# Project Instructions: Mutual Fund RAG Assistant

- Stack: Python 3.11+, Qdrant (Local-First), LangChain, Gemini API (text-embedding-004)
- Core Rule: We are isolating 5 mutual funds. Every piece of ingested text must be tagged with a strict metadata key: {"fund_id": "<fund_name>"}.
- Security: Never hardcode the Gemini API key. Always pull it via os.environ.get("GEMINI_API_KEY").
