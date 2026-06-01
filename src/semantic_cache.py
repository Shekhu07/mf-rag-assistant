import json
import logging
from pathlib import Path
from typing import Optional
import numpy as np

logger = logging.getLogger(__name__)

# Locate the cache file inside the vector store directory
CACHE_FILE = Path(__file__).resolve().parent.parent / "vector_store" / "semantic_cache.json"


def compute_cosine_similarity(v1: list, v2: list) -> float:
    """Computes the cosine similarity between two vector lists."""
    arr1 = np.array(v1)
    arr2 = np.array(v2)
    dot_prod = np.dot(arr1, arr2)
    norm1 = np.linalg.norm(arr1)
    norm2 = np.linalg.norm(arr2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return float(dot_prod / (norm1 * norm2))


def load_semantic_cache() -> list:
    """Loads semantic cache records from disk."""
    if not CACHE_FILE.exists():
        return []
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load semantic cache: {e}")
        return []


def save_semantic_cache(records: list):
    """Saves semantic cache records to disk."""
    try:
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to write semantic cache: {e}")


def check_semantic_cache(query: str, query_embedding: list, fund_id: str, threshold: float = 0.96) -> Optional[str]:
    """
    Checks the semantic cache for a similar query for the same fund_id.
    Returns the cached response if a match is found (similarity >= threshold), otherwise None.
    """
    records = load_semantic_cache()
    if not records:
        return None

    best_similarity = -1.0
    best_response = None
    best_query = None

    for rec in records:
        if rec.get("fund_id") == fund_id and "embedding" in rec:
            similarity = compute_cosine_similarity(query_embedding, rec["embedding"])
            if similarity > best_similarity:
                best_similarity = similarity
                best_response = rec.get("response")
                best_query = rec.get("query")

    if best_similarity >= threshold and best_response:
        logger.info(
            f"Semantic Cache HIT! Best match query: '{best_query}' with similarity {best_similarity:.4f} (Threshold: {threshold})"
        )
        return best_response

    return None


def add_to_semantic_cache(query: str, query_embedding: list, response: str, fund_id: str):
    """Adds a new query, its embedding, and the generated response to the semantic cache."""
    records = load_semantic_cache()
    
    # Avoid duplicate cache records for identical queries
    for rec in records:
        if rec.get("fund_id") == fund_id and rec.get("query").strip().lower() == query.strip().lower():
            return
            
    records.append({
        "query": query,
        "embedding": query_embedding,
        "response": response,
        "fund_id": fund_id
    })
    save_semantic_cache(records)
    logger.info(f"Added query to semantic cache for fund '{fund_id}'. Total cache size: {len(records)}.")
