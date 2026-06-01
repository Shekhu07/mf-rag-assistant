import os
import sys
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
from pathlib import Path

# Setup paths and imports
sys.path.append(str(Path(__file__).resolve().parent.parent))
from src.query_engine import query_fund

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="ArthaAI RAG API", version="1.0")

class QueryRequest(BaseModel):
    query: str
    fund_id: str
    chat_history: List[Dict[str, str]] = []
    extra_context: Optional[str] = None

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/query")
def process_query(req: QueryRequest):
    try:
        logger.info(f"Received query request for fund {req.fund_id}: '{req.query}'")
        ans, docs = query_fund(req.query, req.fund_id, req.chat_history, extra_context=req.extra_context)
        
        sources_list = []
        if docs:
            for doc, score in docs:
                snippet = doc.page_content[:250].replace('\n', ' ')
                sources_list.append({
                    "source": doc.metadata.get('source', 'Unknown'),
                    "score": float(score),
                    "snippet": snippet
                })
        
        return {
            "answer": ans,
            "sources": sources_list
        }
    except Exception as e:
        logger.error(f"Error handling API query request: {e}")
        raise HTTPException(status_code=500, detail=str(e))
