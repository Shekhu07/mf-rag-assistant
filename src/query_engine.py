import os
import sys
import logging
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document
from langchain_core.messages import SystemMessage, HumanMessage

# Load environment variables
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# Setup paths and imports
sys.path.append(str(Path(__file__).resolve().parent))
import config
from semantic_cache import check_semantic_cache, add_to_semantic_cache

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Diagnostics: Log environment keys containing key/token/gemini to trace name mismatches
key_diagnostics = [k for k in os.environ.keys() if 'key' in k.lower() or 'token' in k.lower() or 'gemini' in k.lower()]
logger.info(f"Loaded key-related environment variables: {key_diagnostics}")

# Module-level singletons — initialized once, reused on every query
_vector_store_cache: Optional[QdrantVectorStore] = None
_vector_store_api_key: Optional[str] = None
_llm_cache = None
_bm25_retriever_cache: dict = {}

def get_vector_store() -> QdrantVectorStore:
    """Loads and returns the local Qdrant DB (cached at module level)."""
    global _vector_store_cache, _vector_store_api_key
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set.")

    if _vector_store_cache is not None and _vector_store_api_key == api_key:
        return _vector_store_cache

    if _vector_store_cache is not None and _vector_store_api_key != api_key:
        logger.info("API key change detected. Invaliding cached Qdrant vector store.")
        _vector_store_cache = None

    embeddings = GoogleGenerativeAIEmbeddings(
        model=config.EMBEDDING_MODEL,
        google_api_key=api_key
    )

    qdrant_host = os.environ.get("QDRANT_HOST", "localhost")
    qdrant_api_key = os.environ.get("QDRANT_API_KEY")
    client = None

    if qdrant_host != "localhost":
        try:
            url = qdrant_host if (qdrant_host.startswith("http://") or qdrant_host.startswith("https://")) else f"http://{qdrant_host}:6333"
            client = QdrantClient(url=url, api_key=qdrant_api_key, timeout=30)
            client.get_collections()
        except Exception as e:
            logger.warning(f"Failed to connect to Qdrant at {qdrant_host}: {e}. Falling back to local database.")
            client = None

    if client is None:
        try:
            client = QdrantClient(url="http://localhost:6333", timeout=2)
            client.get_collections()
        except Exception:
            db_path = config.VECTOR_STORE_DIR / "qdrant_local"
            # If database folder doesn't exist, we must trigger ingestion
            if not db_path.exists() or not list(db_path.glob("*")):
                logger.info(f"Local Qdrant DB not found at {db_path}. Attempting auto-ingestion...")
                try:
                    from ingest import ingest_documents
                    ingest_documents()
                except Exception as e:
                    logger.error(f"Auto-ingestion failed: {e}")
                    raise FileNotFoundError(f"Local Qdrant DB auto-ingestion failed: {e}")
            client = QdrantClient(path=str(db_path))

    # If the collection doesn't exist, trigger ingestion
    if not client.collection_exists(config.COLLECTION_NAME):
        logger.info(f"Qdrant collection '{config.COLLECTION_NAME}' does not exist. Ingesting documents...")
        try:
            from ingest import ingest_documents
            ingest_documents()
        except Exception as e:
            logger.error(f"Auto-ingestion failed: {e}")
            raise FileNotFoundError(f"Qdrant collection auto-ingestion failed: {e}")

    db = QdrantVectorStore(
        client=client,
        collection_name=config.COLLECTION_NAME,
        embedding=embeddings
    )
    _vector_store_cache = db
    _vector_store_api_key = api_key
    logger.info("Qdrant vector store client initialized and cached.")
    return _vector_store_cache


def get_llm(api_key: str):
    """Returns the LLM client (cached at module level)."""
    global _llm_cache
    if _llm_cache is not None:
        # Check if the API key has changed to invalidate cache
        current_key = getattr(_llm_cache, "google_api_key", None)
        current_key_val = current_key.get_secret_value() if hasattr(current_key, "get_secret_value") else current_key
        if current_key_val != api_key:
            _llm_cache = None
            logger.info("API key change detected. Invaliding cached LLM client.")

    if _llm_cache is None:
        _llm_cache = ChatGoogleGenerativeAI(
            model=config.GENERATION_MODEL,
            temperature=config.GENERATION_TEMPERATURE,
            google_api_key=api_key,
            max_retries=2
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
        from src.fund_metadata import FUND_DATA
    except ImportError:
        try:
            from fund_metadata import FUND_DATA
        except ImportError as e:
            return f"⚠️ System Error loading fallback database: {e}"

    if fund_id not in FUND_DATA:
        return f"⚠️ Scheme ID '{fund_id}' not found in metadata configuration."
        
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

def check_conversational_intent(query: str) -> Optional[str]:
    """Checks for standard greetings and pleasantries and returns a static response."""
    import string
    # Strip all punctuation and convert to lowercase
    q_clean = query.lower().translate(str.maketrans("", "", string.punctuation)).strip()
    greetings = {"hello", "hi", "hey", "greetings", "good morning", "good afternoon", "good evening", "yo"}
    thanks = {"thank you", "thanks", "thank", "appreciate it", "awesome thank you"}
    
    words = set(q_clean.split())
    if words.intersection(greetings):
        return "Hello! I am ArthaAI, your mutual fund analysis assistant. How can I help you analyze this mutual fund today?"
    if words.intersection(thanks) or any(t in q_clean for t in thanks):
        return "You're welcome! Let me know if you have any other questions about the fund."
    return None

def check_opinionated_intent(query: str) -> Optional[str]:
    """Checks if the user query seeks investment opinions, recommendations, or buy/sell advice."""
    import string
    q_clean = query.lower().translate(str.maketrans("", "", string.punctuation)).strip()
    words = set(q_clean.split())
    
    # Precise indicators of investment opinions (substring search)
    opinionated_phrases = [
        "should i buy", "should i sell", "should i invest", "good to buy", "recommend", "advice",
        "portfolio advice", "investment advice", "buy or sell", "which one to buy", "is it good to buy",
        "should i choose", "give me advice", "should i pull out", "is this fund good", "should i keep",
        "should i hold", "better than", "is it worth", "worth buying", "future performance", "good fund",
        "best fund", "suggest me", "suggest a fund", "would you recommend", "can i invest", "is it safe to invest",
        "will it grow", "buy this", "sell this", "should we buy", "should we sell", "should we invest",
        "in your opinion", "is this a good", "long-term retirement", "for my portfolio", "for retirement",
        "portfolio recommendation", "recommendation on", "financial advice", "buy/sell", "advise me",
        "give advice", "investment suggestions"
    ]
    
    for phrase in opinionated_phrases:
        if phrase in q_clean:
            return "I am a facts-only assistant and do not provide investment advice, portfolio recommendations, or buy/sell opinions. For guidance on mutual fund investing, please refer to the [AMFI Investor Education & Knowledge Center](https://www.amfiindia.com/investor-corner/knowledge-center/)."
            
    # Single-word indicators when used in queries
    opinionated_words = {"recommend", "opinion", "prediction", "forecast", "buy/sell"}
    if words.intersection(opinionated_words):
        return "I am a facts-only assistant and do not provide investment advice, portfolio recommendations, or buy/sell opinions. For guidance on mutual fund investing, please refer to the [AMFI Investor Education & Knowledge Center](https://www.amfiindia.com/investor-corner/knowledge-center/)."
        
    return None

def enforce_single_citation(answer: str, fund_id: str) -> str:
    """Ensures that the answer has exactly one citation link to the official factsheet at the end."""
    if "do not provide investment advice" in answer or "knowledge-center" in answer:
        return answer
        
    if "do not have that information" in answer or "sorry" in answer.lower():
        return answer

    factsheet_urls = {
        "parag_parikh_flexi": "https://amc.ppfas.com/schemes/ppfas-flexi-cap-fund/",
        "pp_tax_saver": "https://amc.ppfas.com/schemes/parag-parikh-tax-saver-fund/",
        "pp_conservative": "https://amc.ppfas.com/schemes/parag-parikh-conservative-hybrid-fund/",
        "pp_liquid": "https://amc.ppfas.com/schemes/parag-parikh-liquid-fund/",
        "pp_dynamic": "https://amc.ppfas.com/schemes/parag-parikh-dynamic-asset-allocation-fund/"
    }
    factsheet_url = factsheet_urls.get(fund_id, "https://amc.ppfas.com/")
    citation_text = f"\n\nOfficial Factsheet Link: [Official Factsheet & Scheme Details]({factsheet_url})"
    
    # Check if a citation link is already present
    if "Official Factsheet & Scheme Details" in answer or factsheet_url in answer:
        return answer
    else:
        return answer.strip() + citation_text

def check_direct_lookup_intent(query: str, fund_id: str) -> Optional[str]:
    """Routes short, direct financial metric queries directly to the local static metadata fallbacks."""
    import string
    # Strip all punctuation and convert to lowercase
    q_clean = query.lower().translate(str.maketrans("", "", string.punctuation)).strip()
    words = q_clean.split()
    
    # If the query is complex (more than 6 words), route to LLM
    if len(words) > 6:
        return None
        
    keywords = {
        "nav", "price", "holding", "holdings", "portfolio", "allocation", "stock", "stocks", "company", "companies",
        "return", "returns", "performance", "cagr", "growth", "yield", "expense", "fee", "fees", "ratio", "charge",
        "manager", "managers", "manage", "managed", "aum", "size", "assets"
    }
    
    phrases = ["net asset value", "expense ratio", "exit load", "fund manager"]
    
    if any(kw in words for kw in keywords) or any(phrase in q_clean for phrase in phrases):
        logger.info(f"Intent Routing: Query '{query}' matches simple lookup intent. Routing directly to local fallback.")
        return get_local_fallback_answer(query, fund_id)
        
    return None

def reformulate_query(query: str, chat_history: list, api_key: str) -> str:
    """
    Passes the chat history and latest user query to Gemini to rewrite
    the query into a standalone query suitable for search retrieval.
    """
    formatted_history = format_chat_history(chat_history)
    
    system_instruction = (
        "You are a professional financial query reformulator.\n"
        "Your task is to rewrite a follow-up User Question into a standalone, self-contained search query for a retrieval system.\n\n"
        "Rules:\n"
        "1. Resolve all relative pronouns (e.g., 'it', 'its', 'they', 'this fund', 'him', 'her') into the concrete mutual fund scheme name from the chat history.\n"
        "2. Always explicitly incorporate the specific mutual fund name (e.g., 'SBI Bluechip Fund Growth') into the reformulated query to ensure accurate embedding generation.\n"
        "3. Keep the query concise, focused entirely on key search terms (ISINs, ratios, managers, holdings), and strip out conversational filler (e.g., 'can you find', 'please tell me').\n"
        "4. Do NOT answer the question. Only output the reformulated query and nothing else.\n\n"
        "Examples:\n"
        "- History: User: What is the NAV of SBI Bluechip? Analyst: The NAV is 85.0. User: What about its expense ratio?\n"
        "  Output: expense ratio of SBI Bluechip Fund Growth\n"
        "- History: User: Who manages Parag Parikh Flexi Cap? Analyst: Rajeev Thakkar. User: Show me their top holdings.\n"
        "  Output: top holdings of Parag Parikh Flexi Cap Fund\n\n"
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
    """
    Returns True if the query likely depends on chat history context 
    (contains pronouns or context-dependent reference terms).
    """
    # Context-dependent tokens indicating reference to previous turns
    relative_tokens = {
        "it", "its", "them", "they", "those", "that", "this", "these",
        "he", "she", "him", "her", "his", "their", "theirs", "himself", "herself",
        "previous", "earlier", "above", "latter", "former", "other", "another", "additional",
        "same", "different", "similar"
    }
    # Clean the query: lowercase and remove basic punctuation
    import string
    cleaned_query = query.lower().translate(str.maketrans("", "", string.punctuation))
    words = set(cleaned_query.split())
    
    # Check for context-dependent phrases
    phrases = ["what about", "how about", "any other", "what is the other"]
    has_phrase = any(phrase in cleaned_query for phrase in phrases)
    
    return has_phrase or not words.isdisjoint(relative_tokens)

def query_fund(query: str, fund_id: str, chat_history: list = None, k: int = 4, extra_context: str = None) -> tuple[str, list]:
    """
    Queries the database using Hybrid Search (Vector + BM25 keyword matching) with RRF,
    checks semantic cache, applies intent-based routing, and generates a response.
    """
    # 1. Check conversational pleasantry intent
    conversational_resp = check_conversational_intent(query)
    if conversational_resp:
        logger.info("Intent Routing: Serving conversational greeting/pleasantry response.")
        return conversational_resp, []

    # 1.5 Check opinionated/portfolio query intent
    opinion_resp = check_opinionated_intent(query)
    if opinion_resp:
        logger.info("Intent Routing: Serving opinionated query refusal response.")
        return opinion_resp, []
        
    # 2. Check direct metric lookup intent
    lookup_resp = check_direct_lookup_intent(query, fund_id)
    if lookup_resp:
        return enforce_single_citation(lookup_resp, fund_id), []

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return "Error: GEMINI_API_KEY is not set in the environment.", []

    try:
        db = get_vector_store()
    except Exception as e:
        logger.error(f"Failed to load vector store: {e}")
        return f"Error loading database: {e}", []

    # 3. Reformulate query if chat history exists and query is relative
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

    # 4. Check Semantic Cache using reformulated/standalone search query
    query_embedding = None
    try:
        import time
        start_cache_time = time.time()
        
        # A. Exact case-insensitive string match check to bypass embedding generation API network latency (< 1ms)
        from semantic_cache import load_semantic_cache
        records = load_semantic_cache()
        q_strip = search_query.strip().lower()
        exact_match = None
        for rec in records:
            if rec.get("fund_id") == fund_id and rec.get("query", "").strip().lower() == q_strip:
                exact_match = rec.get("response")
                break
        
        if exact_match is not None:
            elapsed = (time.time() - start_cache_time) * 1000
            logger.info(f"[INFO] Exact Cache Hit! Served response in {elapsed:.2f}ms.")
            return enforce_single_citation(exact_match, fund_id), []
            
        # B. Fallback to vector semantic similarity cache match
        # Get query embedding using cached embeddings client
        query_embedding = db.embeddings.embed_query(search_query)
        cached_response = check_semantic_cache(search_query, query_embedding, fund_id)
        if cached_response is not None:
            elapsed = (time.time() - start_cache_time) * 1000
            logger.info(f"[INFO] Semantic Cache Hit! Served response in {elapsed:.2f}ms.")
            return enforce_single_citation(cached_response, fund_id), []
    except Exception as e:
        logger.warning(f"Semantic Cache lookup failed: {e}")

    # 5. Perform Hybrid Search (Dense Vector + BM25 Sparse Keyword)
    dense_results = []
    try:
        from qdrant_client.http import models
        qdrant_filter = models.Filter(
            must=[
                models.FieldCondition(
                    key="metadata.fund_id",
                    match=models.MatchValue(value=fund_id)
                )
            ]
        )
        dense_results = db.similarity_search_with_score(
            search_query, 
            k=20, 
            filter=qdrant_filter
        )
    except Exception as e:
        logger.error(f"Vector search failed: {e}")
        return get_local_fallback_answer(query, fund_id), []

    hybrid_results = []
    try:
        global _bm25_retriever_cache
        from qdrant_client.http import models
        
        if fund_id not in _bm25_retriever_cache:
            # Scroll to fetch all chunks of the fund (usually < 150 chunks)
            records, _ = db.client.scroll(
                collection_name=config.COLLECTION_NAME,
                scroll_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="metadata.fund_id",
                            match=models.MatchValue(value=fund_id)
                        )
                    ]
                ),
                limit=1000,
                with_payload=True,
                with_vectors=False
            )
            
            fund_docs = []
            for rec in records:
                payload = rec.payload or {}
                metadata = payload.get("metadata", {})
                page_content = payload.get("page_content", "")
                if page_content:
                    fund_docs.append(Document(page_content=page_content, metadata=metadata))
                    
            if fund_docs:
                retriever = BM25Retriever.from_documents(fund_docs)
                retriever.k = 20
                _bm25_retriever_cache[fund_id] = retriever
            else:
                _bm25_retriever_cache[fund_id] = None

        bm25_retriever = _bm25_retriever_cache.get(fund_id)
        
        if bm25_retriever:
            # Run sparse keyword retriever
            sparse_results = bm25_retriever.invoke(search_query)
            
            # Reciprocal Rank Fusion (RRF)
            rrf_scores = {}
            doc_map = {}
            c = 60
            
            for rank, (doc, score) in enumerate(dense_results):
                content = doc.page_content
                doc_map[content] = (doc, score)
                rrf_scores[content] = rrf_scores.get(content, 0.0) + (1.0 / (c + (rank + 1)))
                
            for rank, doc in enumerate(sparse_results):
                content = doc.page_content
                if content not in doc_map:
                    # Not found in dense, add with default 0.0 score
                    doc_map[content] = (doc, 0.0)
                rrf_scores[content] = rrf_scores.get(content, 0.0) + (1.0 / (c + (rank + 1)))
                
            sorted_contents = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)
            hybrid_results = [doc_map[content] for content in sorted_contents[:k]]
            logger.info(f"Hybrid Search & RRF merged {len(dense_results)} vector and {len(sparse_results)} BM25 results.")
        else:
            logger.warning("No scroll document records found for fund. Using vector-only results.")
            hybrid_results = dense_results[:k]
    except Exception as e:
        logger.error(f"Hybrid search BM25/RRF failed: {e}. Falling back to vector-only results.")
        hybrid_results = dense_results[:k]

    if not hybrid_results:
        return (
            "I am sorry, but I do not have any documentation available for this mutual fund. "
            "Please ensure the data folder contains documents and ingestion has been completed.",
            []
        )

    # 6. Format context block from retrieved hybrid documents
    context_parts = []
    for idx, (doc, score) in enumerate(hybrid_results):
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

    # 7. Create the grounded prompt with chat history context
    history_context = ""
    if formatted_history:
        history_context = f"Conversation History:\n{formatted_history}\n\n"

    factsheet_urls = {
        "parag_parikh_flexi": "https://amc.ppfas.com/schemes/ppfas-flexi-cap-fund/",
        "pp_tax_saver": "https://amc.ppfas.com/schemes/parag-parikh-tax-saver-fund/",
        "pp_conservative": "https://amc.ppfas.com/schemes/parag-parikh-conservative-hybrid-fund/",
        "pp_liquid": "https://amc.ppfas.com/schemes/parag-parikh-liquid-fund/",
        "pp_dynamic": "https://amc.ppfas.com/schemes/parag-parikh-dynamic-asset-allocation-fund/"
    }
    factsheet_url = factsheet_urls.get(fund_id, "https://amc.ppfas.com/")

    system_instruction = (
        "You are a highly precise, objective, and analytical AI Financial Analyst specializing in Indian Mutual Funds.\n"
        f"You are answering a query about the mutual fund scheme: '{fund_id}' using the provided Context (factsheets, live NAV, news, and history).\n\n"
        "Strict Grounding & Behavior Rules:\n"
        "1. Answers factual queries only (e.g., 'Expense ratio of ?', 'ELSS lock-in?', 'Minimum SIP?', 'Exit load?', 'Riskometer/benchmark?', 'How to download capital-gains statement?').\n"
        "2. If the query asks for any opinionated/portfolio questions, recommendations, buy/sell advice, or whether to invest (e.g., 'Should I buy/sell?'), you MUST refuse to answer. Reply exactly with:\n"
        "   'I am a facts-only assistant and do not provide investment advice, portfolio recommendations, or buy/sell opinions. For guidance on mutual fund investing, please refer to the [AMFI Investor Education & Knowledge Center](https://www.amfiindia.com/investor-corner/knowledge-center/).'\n"
        "3. Base factual answers ONLY on details explicitly provided in the Context below. Do not assume or extrapolate.\n"
        "4. If the context does not contain enough information to answer the factual question, respond EXACTLY with:\n"
        "   'I am sorry, but I do not have that information in the provided documentation for this mutual fund.'\n"
        "5. Do not mention or reference the existence of any 'context', 'provided documents', or 'factsheets' in your final response.\n"
        "6. Highlight critical numbers, percentages, and names in bold.\n"
        "7. Format data comparisons in clean markdown tables when helpful.\n"
        "8. At the very end of every factual response, you MUST append exactly one clear citation link in this format:\n"
        f"   'Official Factsheet Link: [Official Factsheet & Scheme Details]({factsheet_url})'\n\n"
        f"{history_context}"
        f"Context:\n{context_text}"
    )

    # 8. Invoke the Gemini generative model
    logger.info(f"Invoking Gemini model '{config.GENERATION_MODEL}' for generation...")
    try:
        llm = get_llm(api_key)
        
        messages = [
            SystemMessage(content=system_instruction),
            HumanMessage(content=query)
        ]
        
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
            return enforce_single_citation(get_local_fallback_answer(query, fund_id), fund_id), hybrid_results
            
        answer = response.content
        logger.info("Generation complete.")

        # Cache successful response
        if answer and query_embedding is not None:
            try:
                add_to_semantic_cache(search_query, query_embedding, answer, fund_id)
            except Exception as e:
                logger.warning(f"Failed to save semantic cache: {e}")

        return enforce_single_citation(answer, fund_id), hybrid_results
    except Exception as e:
        logger.error(f"Error calling Gemini generation: {e}")
        err_str = str(e).lower()
        if "429" in err_str or "quota" in err_str or "exhausted" in err_str:
            return enforce_single_citation(get_local_fallback_answer(query, fund_id), fund_id), hybrid_results
        return f"Error generating response: {e}", hybrid_results


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
