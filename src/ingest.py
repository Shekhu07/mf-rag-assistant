import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_qdrant import QdrantVectorStore

# Load environment variables (e.g., GEMINI_API_KEY)
load_dotenv()

# Import project configurations and utilities
# Add current directory to path just in case
sys.path.append(str(Path(__file__).resolve().parent))
import config
from utils import extract_text, get_supported_files

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def validate_and_get_funds(data_dir: Path) -> list[str]:
    """
    Scans the data directory, identifies subdirectories as mutual funds,
    and validates that we are isolating at most 5 mutual funds.
    """
    if not data_dir.exists():
        logger.warning(f"Data directory {data_dir} does not exist. Creating it.")
        data_dir.mkdir(parents=True, exist_ok=True)
        return []
    
    # Identify direct subdirectories under data/
    funds = [d.name for d in data_dir.iterdir() if d.is_dir()]
    
    # Log detected funds
    logger.info(f"Detected mutual fund directories: {funds}")
    
    # Enforce strict isolation limit
    if len(funds) > config.MAX_FUNDS:
        raise ValueError(
            f"Error: Exceeded the maximum limit of {config.MAX_FUNDS} mutual funds. "
            f"Found {len(funds)} funds: {funds}. Please clean up the data folder."
        )
        
    return funds

def ingest_documents():
    """Main function to ingest documents into ChromaDB."""
    # 1. Get and validate mutual funds directories
    funds = validate_and_get_funds(config.DATA_DIR)
    if not funds:
        logger.info("No mutual fund folders found in the data directory. Ingestion completed with 0 documents.")
        return

    # 2. Retrieve and validate Gemini API Key
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        logger.error("GEMINI_API_KEY environment variable is not set. Ingestion cannot proceed.")
        sys.exit(1)

    # 3. Process documents folder by folder
    all_chunks = []
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.CHUNK_SIZE,
        chunk_overlap=config.CHUNK_OVERLAP,
        length_function=len
    )

    for fund_id in funds:
        fund_dir = config.DATA_DIR / fund_id
        logger.info(f"Processing mutual fund: '{fund_id}'")
        
        # Get all supported files in this fund's subdirectory
        files = get_supported_files(fund_dir)
        if not files:
            logger.warning(f"No supported files (.txt, .pdf, .docx) found for fund '{fund_id}' in {fund_dir}")
            continue

        for file_path in files:
            logger.info(f"  Extracting text from: '{file_path.name}'")
            text = extract_text(file_path)
            if not text or not text.strip():
                logger.warning(f"  Skipped empty file: '{file_path.name}'")
                continue

            # Split extracted text into chunks
            chunks = text_splitter.split_text(text)
            logger.info(f"  Created {len(chunks)} chunks from '{file_path.name}'")

            # Create LangChain Document objects with strict metadata
            for i, chunk in enumerate(chunks):
                doc = Document(
                    page_content=chunk,
                    metadata={
                        "fund_id": fund_id,
                        "source": file_path.name,
                        "chunk_index": i
                    }
                )
                all_chunks.append(doc)

    if not all_chunks:
        logger.info("No text chunks were generated. Vector store was not updated.")
        return

    logger.info(f"Total chunks generated: {len(all_chunks)}. Committing to ChromaDB...")

    # 4. Initialize embedding model
    embeddings = GoogleGenerativeAIEmbeddings(
        model=config.EMBEDDING_MODEL,
        google_api_key=api_key
    )

    # 5. Populate local Qdrant vector store
    # Ensure vector store directory exists
    config.VECTOR_STORE_DIR.mkdir(parents=True, exist_ok=True)
    
    from qdrant_client import QdrantClient
    from qdrant_client.http import models

    qdrant_host = os.environ.get("QDRANT_HOST", "localhost")
    qdrant_api_key = os.environ.get("QDRANT_API_KEY")
    client = None

    if qdrant_host != "localhost":
        try:
            url = qdrant_host if (qdrant_host.startswith("http://") or qdrant_host.startswith("https://")) else f"http://{qdrant_host}:6333"
            client = QdrantClient(url=url, api_key=qdrant_api_key, timeout=60)
            client.get_collections()
        except Exception as e:
            logger.warning(f"Failed to connect to Qdrant at {qdrant_host}: {e}. Falling back to local database.")
            client = None

    if client is None:
        try:
            client = QdrantClient(url="http://localhost:6333", timeout=2)
            client.get_collections()
        except Exception:
            db_path = config.VECTOR_STORE_DIR / "qdrant_local"
            logger.info(f"Using local file-backed Qdrant DB at {db_path}")
            client = QdrantClient(path=str(db_path))

    # Recreate the collection to clear old data
    logger.info(f"Recreating Qdrant collection '{config.COLLECTION_NAME}'...")
    if client.collection_exists(config.COLLECTION_NAME):
        client.delete_collection(config.COLLECTION_NAME)
        
    client.create_collection(
        collection_name=config.COLLECTION_NAME,
        vectors_config=models.VectorParams(size=3072, distance=models.Distance.COSINE)
    )

    db = QdrantVectorStore(
        client=client,
        collection_name=config.COLLECTION_NAME,
        embedding=embeddings
    )

    # Add documents in batches to respect the 100 RPM Free Tier limit
    import time
    batch_size = 20
    delay_seconds = 15
    total_chunks = len(all_chunks)
    
    for i in range(0, total_chunks, batch_size):
        batch = all_chunks[i:i+batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (total_chunks - 1) // batch_size + 1
        
        success = False
        retry_delay = 30  # Start with 30s wait on quota errors
        
        while not success:
            try:
                logger.info(f"Embedding batch {batch_num}/{total_batches} ({len(batch)} chunks)...")
                db.add_documents(batch)
                success = True
            except Exception as e:
                err_str = str(e).lower()
                if "429" in err_str or "quota" in err_str or "exhausted" in err_str:
                    logger.warning(f"Rate limit hit during batch {batch_num}. Sleeping for {retry_delay}s before retrying...")
                    time.sleep(retry_delay)
                    retry_delay = min(retry_delay + 15, 90)  # Cap backoff at 90s
                else:
                    # Re-raise other unexpected errors
                    raise e
        
        if i + batch_size < total_chunks:
            logger.info(f"Sleeping for {delay_seconds} seconds to respect API rate limits...")
            time.sleep(delay_seconds)

    # Chroma versions >= 0.4.x persist automatically, but let's call persist() if it exists
    if hasattr(db, "persist"):
        db.persist()

    logger.info(f"Successfully ingested all documents into vector store at: {config.VECTOR_STORE_DIR}")

if __name__ == "__main__":
    ingest_documents()
