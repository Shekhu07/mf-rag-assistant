import os
import sys
import logging
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.vectorstores import Chroma
from langchain_core.messages import SystemMessage, HumanMessage

# Load environment variables
load_dotenv()

# Setup paths and imports
sys.path.append(str(Path(__file__).resolve().parent))
import config

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Module-level singletons — initialized once, reused on every query
_vector_store_cache: Optional[Chroma] = None
_llm_cache = None

def get_vector_store() -> Chroma:
    """Loads and returns the local Chroma DB (cached at module level)."""
    global _vector_store_cache
    if _vector_store_cache is not None:
        return _vector_store_cache

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set.")

    embeddings = GoogleGenerativeAIEmbeddings(
        model=config.EMBEDDING_MODEL,
        google_api_key=api_key
    )

    if not config.VECTOR_STORE_DIR.exists() or not list(config.VECTOR_STORE_DIR.glob("*")):
        logger.info(f"Vector store not found or empty at {config.VECTOR_STORE_DIR}. Attempting auto-ingestion...")
        try:
            from ingest import ingest_documents
            ingest_documents()
        except Exception as e:
            logger.error(f"Auto-ingestion failed: {e}")
            raise FileNotFoundError(
                f"Vector store not found at {config.VECTOR_STORE_DIR} and auto-ingestion failed: {e}. "
                "Please run the ingestion script 'src/ingest.py' manually."
            )

    db = Chroma(
        persist_directory=str(config.VECTOR_STORE_DIR),
        embedding_function=embeddings,
        collection_name=config.COLLECTION_NAME
    )
    _vector_store_cache = db
    logger.info("ChromaDB vector store initialized and cached.")
    return _vector_store_cache

def get_llm(api_key: str):
    """Returns the LLM client (cached at module level)."""
    global _llm_cache
    if _llm_cache is None:
        _llm_cache = ChatGoogleGenerativeAI(
            model=config.GENERATION_MODEL,
            temperature=config.GENERATION_TEMPERATURE,
            google_api_key=api_key
        )
        logger.info("LLM client initialized and cached.")
    return _llm_cache

def format_chat_history(chat_history: list) -> str:
    """Formats chat history from a list of dicts to a readable string."""
    formatted = []
    for msg in chat_history:
        role = "User" if msg["role"] == "user" else "Assistant"
        formatted.append(f"{role}: {msg['content']}")
    return "\n".join(formatted)

def get_local_fallback_answer(query: str, fund_id: str) -> str:
    """Generates a high-fidelity fallback answer using local metadata."""
    try:
        from fund_metadata import FUND_DATA
    except ImportError:
        return "⚠️ ArthaAI is currently experiencing high demand (Gemini API Rate Limit Exceeded). Please wait a moment and try again."

    if fund_id not in FUND_DATA:
        return "⚠️ ArthaAI is currently experiencing high demand (Gemini API Rate Limit Exceeded). Please wait a moment and try again."
        
    fund = FUND_DATA[fund_id]
    q_lower = query.lower()
    
    # 1. Holdings
    if any(k in q_lower for k in ["holding", "portfolio", "allocation", "stock", "company", "companies"]):
        rows = "\n".join(
            [f"| {i+1} | {company} | {sector} | **{alloc}** |" for i, (company, sector, alloc) in enumerate(fund["holdings"])]
        )
        return (
            f"Here are the holdings for **{fund['name']}** from the latest factsheet:\n\n"
            f"| # | Company | Sector | Allocation |\n"
            f"|---|---------|--------|-----------|\n"
            f"{rows}\n\n"
            f"*(Source: Local Scheme Metadata)*"
        )
        
    # 2. Performance / Returns
    if any(k in q_lower for k in ["return", "performance", "cagr", "growth", "1y", "3y", "5y", "year"]):
        return (
            f"Here is the historical CAGR performance for **{fund['name']}**:\n\n"
            f"| Period | CAGR Return |\n"
            f"|--------|------------|\n"
            f"| 1 Year | **{fund['return_1y']}** |\n"
            f"| 3 Years | **{fund['return_3y']}** |\n"
            f"| 5 Years | **{fund['return_5y']}** |\n\n"
            f"*Risk Profile: {fund['riskometer']}*\n\n"
            f"*(Source: Local Scheme Metadata)*"
        )
        
    # 3. Expense Ratio / Fees
    if any(k in q_lower for k in ["expense", "fee", "ratio", "charge", "exit load", "entry load"]):
        return (
            f"Here are the fee and expense specifications for **{fund['name']}**:\n\n"
            f"| Spec | Details |\n"
            f"|------|---------|\n"
            f"| Expense Ratio (Direct Plan) | **{fund['expense_ratio']}** |\n"
            f"| Minimum SIP Amount | **{fund['min_sip']}** |\n"
            f"| Exit Load | **Nil** |\n"
            f"| Lock-in Period | **None** |\n"
            f"| Risk Profile | **{fund['riskometer']}** |\n\n"
            f"*AUM: {fund['aum']} | Fund Manager: {fund['manager']}*\n\n"
            f"*(Source: Local Scheme Metadata)*"
        )
        
    # 4. Fund Manager
    if "manager" in q_lower or "manage" in q_lower:
        return (
            f"The fund manager for **{fund['name']}** is **{fund['manager']}**.\n\n"
            f"*(Source: Local Scheme Metadata - RAG generation bypassed due to rate limits)*"
        )
        
    # 5. AUM / Size
    if any(k in q_lower for k in ["aum", "size", "assets", "management"]):
        return (
            f"The total Assets Under Management (AUM) for **{fund['name']}** is **{fund['aum']}**.\n\n"
            f"*(Source: Local Scheme Metadata - RAG generation bypassed due to rate limits)*"
        )
        
    # 6. NAV
    if "nav" in q_lower or "asset value" in q_lower:
        return (
            f"The Net Asset Value (NAV) of **{fund['name']}** is **{fund['nav']}** (Change: {fund['change']}).\n\n"
            f"*(Source: Local Scheme Metadata - RAG generation bypassed due to rate limits)*"
        )
        
    # Default fallback message
    return (
        f"**{fund['name']}** Brief Summary:\n"
        f"- **NAV**: {fund['nav']} ({fund['change']})\n"
        f"- **AUM**: {fund['aum']}\n"
        f"- **Expense Ratio**: {fund['expense_ratio']}\n"
        f"- **Fund Manager**: {fund['manager']}\n"
        f"- **Category**: {fund['category']}\n\n"
        f"*(Note: ArthaAI is currently experiencing high demand. General info is served from local scheme metadata)*"
    )

def reformulate_query(query: str, chat_history: list, api_key: str) -> str:
    """
    Passes the chat history and latest user query to Gemini to rewrite
    the query into a standalone query suitable for search retrieval.
    """
    formatted_history = format_chat_history(chat_history)
    
    system_instruction = (
        "You are an assistant designed to reformulate user questions for search retrieval.\n"
        "Given the following Chat History and a follow-up User Question, rewrite the follow-up "
        "question into a standalone, self-contained question that can be searched in a vector "
        "database without needing any previous context. Keep the reformulated query concise, "
        "specific, and focused on key financial terms.\n"
        "Do NOT answer the question. Just output the rewritten standalone question and nothing else.\n\n"
        f"Chat History:\n{formatted_history}"
    )
    
    try:
        llm = get_llm(api_key)
        messages = [
            SystemMessage(content=system_instruction),
            HumanMessage(content=f"User Question: {query}")
        ]
        
        import time
        success = False
        retries = 1
        delay = 1.0
        response = None
        while not success and retries > 0:
            try:
                response = llm.invoke(messages)
                success = True
            except Exception as e:
                err_str = str(e).lower()
                if "429" in err_str or "quota" in err_str or "exhausted" in err_str:
                    logger.warning(f"Gemini API rate limit hit in reformulate_query. Retrying in {delay}s... (Retries left: {retries-1})")
                    time.sleep(delay)
                    delay *= 2
                    retries -= 1
                else:
                    raise e

        if not response:
            logger.warning("Query reformulation failed due to rate limits. Falling back to original query.")
            return query
            
        standalone_query = response.content.strip()
        # Clean up any potential markdown surrounding the response
        standalone_query = standalone_query.replace('"', '').replace("'", "")
        return standalone_query
    except Exception as e:
        logger.error(f"Error reformulating query: {e}")
        # Fallback to original query on failure
        return query

def is_query_relative(query: str) -> bool:
    """Returns True if the query likely depends on chat history context (contains pronouns/deictic terms)."""
    relative_tokens = {"it", "its", "them", "they", "those", "that", "this", "he", "she", "him", "her", "his", "their", "previous", "earlier", "above", "latter", "former", "other", "why", "how", "what about", "who"}
    # Strip common punctuation and split into words
    cleaned_query = query.lower().replace("?", "").replace(".", "").replace(",", "")
    words = set(cleaned_query.split())
    return not words.isdisjoint(relative_tokens)

def query_fund(query: str, fund_id: str, chat_history: list = None, k: int = 4, extra_context: str = None) -> tuple[str, list]:
    """
    Queries the vector database for a specific mutual fund (enforcing isolation),
    optionally reformulating the query using conversation history,
    constructs a grounded prompt, and generates a response using Gemini 2.5 Flash.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return "Error: GEMINI_API_KEY is not set in the environment.", []

    try:
        db = get_vector_store()
    except Exception as e:
        logger.error(f"Failed to load vector store: {e}")
        return f"Error loading database: {e}", []

    # 1. Reformulate query if chat history exists and query is relative
    search_query = query
    formatted_history = ""
    if chat_history and len(chat_history) > 1:  # >1 to skip the initial static greeting message
        # Exclude the very first greeting message if it is from assistant and static
        history_to_format = chat_history
        if chat_history[0]["role"] == "analyst" and "Hi! I have parsed" in chat_history[0]["content"]:
            history_to_format = chat_history[1:]
            
        if len(history_to_format) > 0:
            formatted_history = format_chat_history(history_to_format)
            # Only reformulate query if it is relative to conversation history
            if is_query_relative(query):
                # Apply a sliding window of the last 6 messages (3 turns of conversation) to prevent context bloat
                history_to_format = history_to_format[-6:]
                logger.info("Reformulating user query based on conversation history...")
                search_query = reformulate_query(query, history_to_format, api_key)
                logger.info(f"Original: '{query}' -> Reformulated: '{search_query}'")
            else:
                logger.info("Query is self-contained. Skipping reformulation step.")

    # 2. Retrieve matching documents strictly isolated by fund_id
    logger.info(f"Retrieving chunks for fund '{fund_id}' with search query: '{search_query}'")
    search_filter = {"fund_id": fund_id}
    
    # We use similarity_search_with_score which returns list of (Document, score)
    # where score is L2 distance (lower is closer/better).
    try:
        results = db.similarity_search_with_score(
            search_query,
            k=k,
            filter=search_filter
        )
    except Exception as e:
        logger.error(f"Error querying vector store: {e}")
        return f"Error executing similarity search: {e}", []

    if not results:
        logger.warning(f"No document chunks found for fund '{fund_id}'.")
        return (
            "I am sorry, but I do not have any documentation available for this mutual fund. "
            "Please ensure the data folder contains documents and ingestion has been completed.",
            []
        )

    # 3. Format context block from retrieved documents
    context_parts = []
    for idx, (doc, score) in enumerate(results):
        context_parts.append(
            f"[Source Document {idx+1}]\n"
            f"Filename: {doc.metadata.get('source', 'Unknown')}\n"
            f"Content: {doc.page_content.strip()}"
        )
    context_text = "\n\n".join(context_parts)

    # Fetch live NAV dynamically from MFAPI and prepend to context
    live_nav_ctx = ""
    try:
        from nav_service import fetch_latest_nav
        nav_data = fetch_latest_nav(fund_id)
        if nav_data:
            nav_val = nav_data.get("nav")
            nav_date = nav_data.get("date")
            nav_change = nav_data.get("change")
            live_nav_ctx = (
                f"[Real-Time Live NAV & Price Data]\n"
                f"As of {nav_date}, the latest Net Asset Value (NAV) of this mutual fund is {nav_val}.\n"
                f"The daily NAV change is {nav_change}.\n\n"
            )
    except Exception as e:
        logger.warning(f"Failed to fetch live NAV context: {e}")

    if live_nav_ctx:
        context_text = live_nav_ctx + context_text

    if extra_context:
        context_text = f"[Additional Recent News & Transactions Context]\n{extra_context}\n\n" + context_text

    # 4. Create the grounded prompt with chat history context
    history_context = ""
    if formatted_history:
        history_context = f"Conversation History:\n{formatted_history}\n\n"

    system_instruction = (
        "You are a highly precise and objective AI financial analyst assistant specializing in mutual fund analysis.\n"
        "You are tasked with answering queries about a specific mutual fund using the provided factsheet, live NAV context, and optional recent news/transaction context.\n"
        "You also have access to the conversation history below to help you answer follow-up queries or maintain context.\n\n"
        "Strict Grounding Rules:\n"
        "1. Answer the question using ONLY the facts, numbers, and statements provided in the Context (including live NAV and recent news/portfolio changes context) below.\n"
        "2. Do NOT use outside knowledge, extrapolate, make assumptions, or speculate.\n"
        "3. If the context does not contain the answer or does not have enough information to answer, you must respond exactly with: "
        "'I am sorry, but I do not have that information in the provided documentation for this mutual fund.'\n"
        "4. Keep your answer factual, precise, concise, and directly derived from the source text.\n\n"
        f"{history_context}"
        f"Context:\n{context_text}"
    )

    # 5. Invoke the Gemini generative model
    logger.info(f"Invoking Gemini model '{config.GENERATION_MODEL}' for generation...")
    try:
        llm = get_llm(api_key)
        
        messages = [
            SystemMessage(content=system_instruction),
            HumanMessage(content=query)
        ]
        
        import time
        success = False
        retries = 1
        delay = 1.0
        response = None
        while not success and retries > 0:
            try:
                response = llm.invoke(messages)
                success = True
            except Exception as e:
                err_str = str(e).lower()
                if "429" in err_str or "quota" in err_str or "exhausted" in err_str:
                    logger.warning(f"Gemini API rate limit hit in query_fund. Retrying in {delay}s... (Retries left: {retries-1})")
                    time.sleep(delay)
                    delay *= 2
                    retries -= 1
                else:
                    raise e

        if not response:
            return get_local_fallback_answer(query, fund_id), results
            
        answer = response.content
        logger.info("Generation complete.")
        return answer, results
    except Exception as e:
        logger.error(f"Error calling Gemini generation: {e}")
        err_str = str(e).lower()
        if "429" in err_str or "quota" in err_str or "exhausted" in err_str:
            return get_local_fallback_answer(query, fund_id), results
        return f"Error generating response: {e}", results

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python src/query_engine.py <query_text> <fund_id>")
        sys.exit(1)
        
    q = sys.argv[1]
    f = sys.argv[2]
    ans, docs = query_fund(q, f)
    print("\n" + "="*60)
    print(f"ANSWER FOR {f.upper()}:")
    print("="*60)
    print(ans)
    print("="*60 + "\n")
