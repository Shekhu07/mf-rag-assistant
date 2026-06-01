import os
import sys
import shutil
import logging
from pathlib import Path

# Setup paths
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))
sys.path.append(str(BASE_DIR / "src"))

# Import configurations and setup logging
from src import config

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def download_database() -> bool:
    repo_id = os.environ.get("HF_DATASET_REPO")
    token = os.environ.get("HF_TOKEN")
    
    if not repo_id:
        logger.info("HF_DATASET_REPO environment variable not set. Skipping Hugging Face download.")
        return False
        
    local_dir = config.VECTOR_STORE_DIR / "qdrant_local"
    logger.info(f"Attempting to download vector store from Hugging Face Dataset: '{repo_id}'")
    
    try:
        from huggingface_hub import snapshot_download
        
        # Download files directly into the target directory
        snapshot_download(
            repo_id=repo_id,
            repo_type="dataset",
            local_dir=str(local_dir),
            token=token,
            ignore_patterns=[".git*", "README.md"]
        )
        
        # Handle cases where files might be downloaded into a nested qdrant_local folder
        # (e.g., if the user uploaded the whole qdrant_local folder to the dataset repo)
        nested_dir = local_dir / "qdrant_local"
        if nested_dir.exists() and nested_dir.is_dir():
            logger.info("Found nested qdrant_local directory. Re-aligning directory structure...")
            for path in nested_dir.iterdir():
                dest = local_dir / path.name
                if dest.exists():
                    if dest.is_dir():
                        shutil.rmtree(dest)
                    else:
                        dest.unlink()
                shutil.move(str(path), str(dest))
            nested_dir.rmdir()
            
        # Verify that essential database components exist
        meta_json = local_dir / "meta.json"
        collection_dir = local_dir / "collection"
        
        if meta_json.exists() and collection_dir.exists():
            logger.info(f"Successfully downloaded and verified vector store at: {local_dir}")
            return True
        else:
            logger.warning(f"Download completed, but expected database files are missing in {local_dir}")
            return False
            
    except Exception as e:
        logger.error(f"Failed to download vector store from HF Hub: {e}")
        return False

def main():
    # 1. Attempt to download the database from HF Hub
    download_success = download_database()
    
    # 2. Check if a valid database is present locally (whether from download or pre-existing)
    local_db_dir = config.VECTOR_STORE_DIR / "qdrant_local"
    db_exists = (
        local_db_dir.exists() and 
        (local_db_dir / "meta.json").exists() and 
        (local_db_dir / "collection").exists()
    )
    
    # 3. If no database exists, run the auto-ingestion pipeline as fallback
    if not db_exists:
        logger.warning("No local vector database found. Triggering fallback auto-ingestion...")
        try:
            from src.ingest import ingest_documents
            ingest_documents()
            logger.info("Fallback auto-ingestion completed successfully.")
        except Exception as e:
            logger.error(f"Fallback auto-ingestion failed: {e}")
            sys.exit(1)
    else:
        logger.info("Qdrant local database is ready.")

if __name__ == "__main__":
    main()
