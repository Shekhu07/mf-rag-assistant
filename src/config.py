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

# Google Stitch UI Design Tokens — ArthaAI Pro Terminal v2.5
DEFAULT_STITCH_DESIGN = {
    "primary_color": "#3b82f6",
    "on_primary": "#ffffff",
    "bg_color": "#0b1120",
    "card_bg_color": "#0f172a",
    "surface_container_low": "#0f172a",
    "surface_lowest": "#060d1c",
    "surface_high": "#1e293b",
    "surface_highest": "#243040",
    "surface_bright": "#2d3a4f",
    "border_color": "rgba(255,255,255,0.1)",
    "text_color": "#f8fafc",
    "text_highlight_color": "#ffffff",
    "text_muted_color": "#94a3b8",
    "outline_color": "#64748b",
    "success_color": "#4edea3",
    "secondary_container": "#065f46",
    "danger_color": "#f87171",
    "error_container": "#7f1d1d",
    "warning_color": "#fbbf24",
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

