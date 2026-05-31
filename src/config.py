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

# Google Stitch UI Design Tokens
DEFAULT_STITCH_DESIGN = {
    "primary_color": "#E2FF3B",
    "bg_color": "#080A0C",
    "card_bg_color": "#0E1217",
    "border_color": "#1C232E",
    "text_color": "#BAC7D5",
    "text_highlight_color": "#FFFFFF",
    "text_muted_color": "#8A99AD",
    "success_color": "#10B981",
    "danger_color": "#EF4444",
    "font_header": "'Outfit', sans-serif",
    "font_body": "'Plus Jakarta Sans', sans-serif"
}

STITCH_DESIGN_PATH = BASE_DIR / "stitch_design.json"

def load_stitch_design():
    import json
    design = DEFAULT_STITCH_DESIGN.copy()
    if STITCH_DESIGN_PATH.exists():
        try:
            with open(STITCH_DESIGN_PATH, "r") as f:
                loaded = json.load(f)
                for k, v in loaded.items():
                    if k in design:
                        design[k] = v
        except Exception:
            pass
    return design

STITCH_DESIGN = load_stitch_design()

