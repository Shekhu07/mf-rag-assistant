# ⚡ ArthaAI MF RAG Assistant

A **production-grade Mutual Fund Research Assistant** built with Streamlit, LangChain, ChromaDB, and Gemini 2.5 Flash. Analyze factsheets, compare returns, check expense ratios, and ask deep questions about any mutual fund — all in a sleek, premium dark UI.

![Python](https://img.shields.io/badge/Python-3.9+-blue?logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.x-red?logo=streamlit)
![LangChain](https://img.shields.io/badge/LangChain-0.x-green)
![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector_Store-purple)
![Gemini](https://img.shields.io/badge/Google_Gemini-2.5_Flash-orange?logo=google)

---

## 🧠 Features

- **RAG-Powered Q&A** — Ask any question about a mutual fund's factsheet using Retrieval-Augmented Generation
- **Fund Isolation** — Each query is strictly scoped to the selected fund's documents in ChromaDB
- **Instant Answers** — Returns Info, Expense Specs, and Top Holdings load instantly from local metadata (no API call)
- **Conversational Memory** — Multi-turn chat with query reformulation for follow-up questions
- **Rate-Limit Resilience** — Automatic fallback to local metadata when Gemini API quota is exceeded
- **Premium Dark UI** — Dark, premium interface with markdown tables, animated chat bubbles, and a collapsible sources panel
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
├── requirements.txt        # Python dependencies
├── .env.template           # Template for environment variables
├── src/
│   ├── config.py           # Paths, model names, chunking config
│   ├── ingest.py           # PDF ingestion → ChromaDB pipeline
│   ├── query_engine.py     # RAG retrieval + Gemini generation
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

### 6. Ingest documents into ChromaDB
```bash
python3 src/ingest.py
```
This processes all PDFs and text files, chunks them, embeds them, and stores them in the local `vector_store/` directory.

### 7. Run the app
```bash
python3 -m streamlit run app.py
```
Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## 🔐 Environment Variables

| Variable | Description |
|----------|-------------|
| `GEMINI_API_KEY` | Your Google Gemini API key (required) |

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
