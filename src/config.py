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

# Google Stitch UI Design Tokens (Material Design 3 Terminal)
DEFAULT_STITCH_DESIGN = {
    "primary_color": "#adc6ff",
    "on_primary": "#002e6a",
    "bg_color": "#0b1326",
    "card_bg_color": "#171f33",
    "surface_container_low": "#131b2e",
    "surface_lowest": "#060e20",
    "surface_high": "#222a3d",
    "surface_highest": "#2d3449",
    "surface_bright": "#31394d",
    "border_color": "#424754",
    "text_color": "#dae2fd",
    "text_highlight_color": "#dae2fd",
    "text_muted_color": "#c2c6d6",
    "outline_color": "#8c909f",
    "success_color": "#4edea3",
    "secondary_container": "#00a572",
    "danger_color": "#ffb4ab",
    "error_container": "#93000a",
    "warning_color": "#ffb3ad",
    "font_header": "'Outfit', sans-serif",
    "font_body": "'Outfit', sans-serif",
    "font_mono": "'JetBrains Mono', monospace",
    "border_radius_sm": "2px",
    "border_radius_md": "4px",
    "border_radius_lg": "8px",
    "border_radius_xl": "12px",
    "spacing_unit": "8px",
    "card_shadow": "none"
}

STITCH_DESIGN_PATH = BASE_DIR / "stitch_design.json"

def load_stitch_design():
    import json
    design = DEFAULT_STITCH_DESIGN.copy()
    if STITCH_DESIGN_PATH.exists():
        try:
            with open(STITCH_DESIGN_PATH, "r") as f:
                loaded = json.load(f)
                # Accept all keys from file, not just those in defaults
                design.update(loaded)
        except Exception:
            pass
    return design

STITCH_DESIGN = load_stitch_design()

