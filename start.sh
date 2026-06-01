#!/bin/bash

# Start FastAPI backend in the background on port 8000
echo "Starting decoupled FastAPI RAG backend on port 8000..."
uvicorn src.api:app --host 127.0.0.1 --port 8000 &

# Start Streamlit frontend in the foreground on port 8501
echo "Starting Streamlit frontend on port 8501..."
streamlit run app.py \
    --server.port=8501 \
    --server.address=0.0.0.0 \
    --browser.gatherUsageStats=false
