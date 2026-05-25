import os
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
VECTOR_STORE_DIR = BASE_DIR / "vector_store"

# Embedding configuration
EMBEDDING_MODEL = "models/gemini-embedding-2"

# Generative model configuration
GENERATION_MODEL = "gemini-2.5-flash"
GENERATION_TEMPERATURE = 0.2

# Vector database configuration
COLLECTION_NAME = "mutual_fund_docs"

# Chunking configuration
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# Strict fund isolation rules
MAX_FUNDS = 5
