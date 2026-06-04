#!/usr/bin/env bash
set -e

# Cleanup background processes on exit
cleanup() {
    echo "Shutting down services..."
    kill "$UVICORN_PID" 2>/dev/null || true
    wait "$UVICORN_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

# Sync vector store from Hugging Face Dataset or run local fallback ingestion
echo "Syncing/building vector database..."
.venv/bin/python src/download_db.py

# Start FastAPI backend in the background on port 8000
echo "Starting decoupled FastAPI RAG backend on port 8000..."
.venv/bin/uvicorn src.api:app --host 127.0.0.1 --port 8000 &
UVICORN_PID=$!

# Start Streamlit frontend in the foreground on port 8501
echo "Starting Streamlit frontend on port 8501..."
.venv/bin/streamlit run app.py \
    --server.port=8501 \
    --server.address=0.0.0.0 \
    --browser.gatherUsageStats=false
