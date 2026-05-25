import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma

# Load environment variables
load_dotenv()

# Import configurations
sys.path.append(str(Path(__file__).resolve().parent))
import config

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def test_query(query_text: str, fund_id: str = None):
    """Loads the vector store and queries it, optionally filtering by fund_id."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        logger.error("GEMINI_API_KEY environment variable is not set.")
        sys.exit(1)

    if not config.VECTOR_STORE_DIR.exists():
        logger.error(f"Vector store directory {config.VECTOR_STORE_DIR} does not exist. Please run ingest.py first.")
        sys.exit(1)

    logger.info("Initializing embedding model...")
    embeddings = GoogleGenerativeAIEmbeddings(
        model=config.EMBEDDING_MODEL,
        google_api_key=api_key
    )

    logger.info(f"Loading Chroma DB from {config.VECTOR_STORE_DIR}...")
    db = Chroma(
        persist_directory=str(config.VECTOR_STORE_DIR),
        embedding_function=embeddings,
        collection_name=config.COLLECTION_NAME
    )

    search_kwargs = {}
    if fund_id:
        logger.info(f"Searching for '{query_text}' with strict filter: fund_id = '{fund_id}'")
        search_kwargs["filter"] = {"fund_id": fund_id}
    else:
        logger.info(f"Searching for '{query_text}' without filters...")

    # Perform similarity search with scores
    results = db.similarity_search_with_relevance_scores(
        query_text,
        k=4,
        **search_kwargs
    )

    print("\n" + "="*50)
    print(f"QUERY: '{query_text}' | FILTER: fund_id = {fund_id}")
    print("="*50)
    
    if not results:
        print("No documents found.")
    else:
        for idx, (doc, score) in enumerate(results):
            print(f"\nResult #{idx+1} [Relevance Score: {score:.4f}]")
            print(f"Metadata: {doc.metadata}")
            # Truncate content for display
            content = doc.page_content.strip().replace('\n', ' ')
            display_content = content[:200] + "..." if len(content) > 200 else content
            print(f"Content:  {display_content}")
            
    print("="*50 + "\n")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python src/query_test.py <query_text> [fund_id]")
        sys.exit(1)
        
    q = sys.argv[1]
    f = sys.argv[2] if len(sys.argv) > 2 else None
    test_query(q, f)
