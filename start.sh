#!/usr/bin/env bash
set -e

# Sync vector store from Hugging Face Dataset or run local fallback ingestion
echo "Syncing/building vector database..."
.venv/bin/python src/download_db.py


# Start Streamlit frontend in the foreground on port 8501
echo "Starting Streamlit frontend on port 8501..."
.venv/bin/streamlit run app.py \
    --server.port=8501 \
    --server.address=0.0.0.0 \
    --browser.gatherUsageStats=false
