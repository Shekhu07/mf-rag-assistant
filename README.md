---
title: Artha AI
emoji: ⚡
colorFrom: indigo
colorTo: yellow
sdk: streamlit
sdk_version: 1.30.0
app_file: app.py
pinned: false
---

# ⚡ ArthaAI MF RAG Assistant

A **production-grade Mutual Fund Research Assistant** built with Streamlit, LangChain, Qdrant, and Gemini 2.5 Flash. Analyze factsheets, compare returns, check expense ratios, and ask deep questions about any mutual fund — all in a sleek, premium dark UI.

![Python](https://img.shields.io/badge/Python-3.9+-blue?logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.x-red?logo=streamlit)
![LangChain](https://img.shields.io/badge/LangChain-0.x-green)
![Qdrant](https://img.shields.io/badge/Qdrant-Vector_Store-blue?logo=qdrant)
![Gemini](https://img.shields.io/badge/Google_Gemini-2.5_Flash-orange?logo=google)

---

## 🧠 Features

- **Hybrid Search (Dense + BM25)** — Combines dense semantic vector embeddings with sparse BM25 keyword matching using Reciprocal Rank Fusion (RRF) to retrieve precise financial numbers and tickers.
- **Dual-Layer Semantic Cache** — Short-circuits identical queries in under **1.5ms** (4400x speedup!) via exact case-insensitive string matching, and falls back to cosine-similarity vector comparisons to avoid redundant LLM and embedding API calls.
- **Intent-Based Routing Gateway** — Fast-tracks greetings/pleasantries and simple financial metric lookups directly to static text and offline fallbacks, reducing rate limits and network calls.
- **RAG-Powered Q&A** — Ask deep questions about a mutual fund's factsheet using Retrieval-Augmented Generation.
- **Fund Isolation** — Each query is strictly isolated to the selected fund's documents in Qdrant.
- **Real-time NAV Integration** — Retrieves live NAV metrics dynamically from MFAPI endpoints.
- **Rate-Limit Resilience** — Automatic fallback to high-fidelity local metadata when Gemini API quota is exceeded.
- **Premium Dark UI** — Dark, premium interface with markdown tables, animated chat bubbles, and a collapsible sources panel.
- **5 Funds Supported** out of the box:
  - SBI Bluechip Fund Direct Growth
  - Parag Parikh Flexi Cap Fund Direct Growth
  - HDFC Top 100 Fund Direct Growth
  - ICICI Prudential Bluechip Fund Direct Growth
  - Mirae Asset Large Cap Fund Direct Growth

---

## 🗂️ Project Structure

```
mf-rag-assistant/
├── app.py                  # Streamlit UI — main entry point
├── Dockerfile              # Production Docker build configuration
├── .dockerignore           # Exclusions for Docker build context
├── requirements.txt        # Python dependencies
├── .env.template           # Template for environment variables
├── deploy/
│   ├── docker-compose.yml  # Orchestrates Streamlit, Qdrant & Nginx containers
│   └── nginx_streamlit.conf # Nginx reverse proxy configuration
├── src/
│   ├── config.py           # Paths, model names, chunking config
│   ├── ingest.py           # PDF ingestion → Qdrant Vector DB pipeline
│   ├── query_engine.py     # RAG retrieval + Gemini generation + RRF + Routing
│   ├── semantic_cache.py   # Vector and exact-string semantic cache module
│   ├── fund_metadata.py    # Local fund metadata (NAV, returns, etc.)
│   └── utils.py            # PDF text extraction helpers
└── data/
    └── <fund_name>/
        ├── factsheet.pdf           # Official fund factsheet
        └── returns_and_expenses.txt # Supplementary data
```

---

## ⚙️ Setup & Installation

### 1. Clone the repository
```bash
git clone https://github.com/<your-username>/mf-rag-assistant.git
cd mf-rag-assistant
```

### 2. Create and activate a virtual environment
```bash
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up your API key
```bash
cp .env.template .env
# Edit .env and add your Gemini API key:
# GEMINI_API_KEY=your_key_here
```
Get a free key at [Google AI Studio](https://aistudio.google.com/app/apikey).

### 5. Add your fund factsheets
Place PDF factsheets in `data/<fund_id>/factsheet.pdf`. The supported fund IDs are:
- `sbi_bluechip`
- `parag_parikh_flexi`
- `hdfc_top100`
- `icici_prudential`
- `mirae_asset`

### 6. Ingest documents into Qdrant Vector Store
```bash
python3 src/ingest.py
```
This processes all PDFs and text files, chunks them, generates 3072-dimensional embeddings, and stores them in the Qdrant vector database (automatically falling back to local file storage `vector_store/qdrant_local/` if no server is running).

### 7. Run the app
```bash
python3 -m streamlit run app.py
```
Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## 🐳 Production Deployment (Docker + Nginx)

For production deployment or to test a local containerized setup, a turnkey multi-container orchestration is available. Nginx acts as a WebSocket-optimized reverse proxy routing traffic to the Streamlit app.

### 1. Requirements
Ensure you have **Docker Desktop** installed and running on your system.

### 2. Run with Docker Compose
From the project root directory, run the following command to spin up the Streamlit container and Nginx proxy (this automatically reads your `.env` file from the root folder):
```bash
docker compose --env-file .env -f deploy/docker-compose.yml up --build
```

### 3. Access the Dashboard
Once the services start up, open your browser and navigate to:
👉 **`http://localhost`** (standard port 80).

*Note: If port 80 is already in use by another application on your system, you can edit [deploy/docker-compose.yml](file:///Users/abhishekspillai/mf-rag-assistant/deploy/docker-compose.yml) and change `"80:80"` to `"8080:80"`, then access the app at `http://localhost:8080`.*

### 4. Stopping the Services
To stop and clean up the containers, press `Ctrl + C` in the logs terminal and run:
```bash
docker compose -f deploy/docker-compose.yml down
```

---

## 🔐 Environment Variables

| Variable | Description |
|----------|-------------|
| `GEMINI_API_KEY` | Your Google Gemini API key (required) |
| `QDRANT_HOST` | Host address of Qdrant vector database (defaults to `localhost` or SQLite fallback) |

> ⚠️ **Never commit your `.env` file.** It is excluded by `.gitignore`.

---

## 🚀 Adding a New Fund

1. Create a folder: `data/<new_fund_id>/`
2. Add `factsheet.pdf` (the official factsheet PDF)
3. Optionally add `returns_and_expenses.txt` with structured return/fee data
4. Add the fund's metadata to `src/fund_metadata.py` under `FUND_DATA`
5. Re-run `python3 src/ingest.py` to index the new fund

---

## 📄 License

MIT License — free to use and modify.
