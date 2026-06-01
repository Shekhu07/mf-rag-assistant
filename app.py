import streamlit as st
import markdown
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).resolve().parent / ".env")

# Setup paths and imports
sys.path.append(str(Path(__file__).resolve().parent))
from src.query_engine import query_fund
import src.config as config

# Import mutual fund scheme details
from src.fund_metadata import FUND_DATA
from src.nav_service import get_live_nav, clear_nav_cache, fetch_nav_history
from src.news_service import fetch_google_news, analyze_sentiment_with_llm

# --- PAGE SETUP ---
st.set_page_config(
    page_title="ArthaAI - Mutual Funds",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CACHED DATA WRAPPERS TO OPTIMIZE PERFORMANCE & PREVENT RATE LIMITS ---
@st.cache_data(ttl=300)
def get_all_nav_data_cached():
    from concurrent.futures import ThreadPoolExecutor
    all_nav_data = {}
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {
            key: executor.submit(
                get_live_nav,
                key,
                item["nav"],
                item["change"],
                item["change_positive"]
            )
            for key, item in FUND_DATA.items()
        }
        all_nav_data = {key: fut.result() for key, fut in futures.items()}
    return all_nav_data

@st.cache_data(ttl=300)
def fetch_nav_history_cached(fund_id: str, period: str):
    return fetch_nav_history(fund_id, period)

@st.cache_data(ttl=1800)
def fetch_google_news_cached(fund_id: str):
    return fetch_google_news(fund_id)

@st.cache_data(ttl=1800)
def analyze_sentiment_cached(articles, fund_name, api_key):
    return analyze_sentiment_with_llm(articles, fund_name, api_key)# --- HIGH FIDELITY DHAN WEB STYLE CSS WITH STITCH DESIGN TOKENS ---
st.markdown(f"""
<style>
    :root {{
        --primary-color: {config.STITCH_DESIGN["primary_color"]};
        --bg-color: {config.STITCH_DESIGN["bg_color"]};
        --card-bg-color: {config.STITCH_DESIGN["card_bg_color"]};
        --border-color: {config.STITCH_DESIGN["border_color"]};
        --text-color: {config.STITCH_DESIGN["text_color"]};
        --text-highlight-color: {config.STITCH_DESIGN["text_highlight_color"]};
        --text-muted-color: {config.STITCH_DESIGN["text_muted_color"]};
        --success-color: {config.STITCH_DESIGN["success_color"]};
        --danger-color: {config.STITCH_DESIGN["danger_color"]};
        --font-header: {config.STITCH_DESIGN["font_header"]};
        --font-body: {config.STITCH_DESIGN["font_body"]};
    }}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');
    
    /* Global Overrides */
    .stApp {
        background-color: var(--bg-color) !important;
        color: var(--text-color) !important;
        font-family: var(--font-body);
    }
    
    /* Make default header transparent and allow click-through to nav bar links */
    header[data-testid="stHeader"], [data-testid="stHeader"] {
        background: transparent !important;
        background-color: transparent !important;
        pointer-events: none !important;
        border: none !important;
        box-shadow: none !important;
    }
    
    /* Hide Deploy and Main Menu buttons specifically to prevent hiding collapse control */
    [data-testid="stAppDeployButton"] {
        display: none !important;
    }
    [data-testid="stMainMenu"] {
        display: none !important;
    }
    
    /* Style and ensure the sidebar collapse toggle button is fully visible and clickable */
    [data-testid="stSidebarCollapseButton"], [data-testid="collapsedControl"] {
        pointer-events: auto !important;
        background-color: var(--card-bg-color) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 6px !important;
        color: var(--primary-color) !important;
        display: flex !important;
        z-index: 1000000 !important;
        margin-top: 10px !important;
        margin-left: 12px !important;
    }
    
    [data-testid="stSidebarCollapseButton"]:hover {
        background-color: rgba(255, 255, 255, 0.05) !important;
        color: var(--text-highlight-color) !important;
        border-color: var(--primary-color) !important;
    }
    
    [data-testid="stDecoration"] {
        display: none !important;
    }
    
    /* Reset top padding to sit the custom header naturally at the top */
    .block-container {
        padding-top: 0rem !important;
    }
    
    /* Top Navigation bar */
    .dhan-nav {
        background-color: var(--card-bg-color);
        padding: 0.8rem 2rem;
        border-bottom: 1px solid var(--border-color);
        display: flex;
        align-items: center;
        margin: 0rem -5rem 2rem -5rem;
    }
    
    .dhan-logo {
        color: var(--primary-color);
        font-family: var(--font-header);
        font-weight: 800;
        font-size: 1.6rem;
        margin-right: 2rem;
        margin-left: 2.8rem; /* Leaves room for the sidebar collapse button */
        letter-spacing: -0.5px;
    }
    
    /* Typography */
    .scheme-title {
        font-family: var(--font-header);
        font-weight: 700;
        font-size: 1.8rem;
        color: var(--text-highlight-color);
        margin-bottom: 0.2rem;
    }
    
    .scheme-badge {
        background-color: rgba(16, 185, 129, 0.1);
        color: var(--success-color);
        font-size: 0.72rem;
        font-weight: 700;
        padding: 3px 8px;
        border-radius: 4px;
        border: 1px solid rgba(16, 185, 129, 0.2);
        display: inline-block;
        margin-right: 0.5rem;
    }
    
    .scheme-cat {
        font-size: 0.88rem;
        color: var(--text-muted-color);
        margin-bottom: 1.5rem;
    }
    
    /* NAV Section */
    .nav-box {
        margin-bottom: 2rem;
    }
    
    .nav-label {
        font-size: 0.85rem;
        color: var(--text-muted-color);
        font-weight: 500;
        margin-bottom: 0.1rem;
    }
    
    .nav-val {
        font-size: 2.2rem;
        color: var(--text-highlight-color);
        font-weight: 800;
        font-family: var(--font-header);
        display: inline-block;
        margin-right: 0.8rem;
    }
    
    .nav-change-pos {
        color: var(--success-color);
        font-weight: 700;
        font-size: 1rem;
        display: inline-block;
    }
 
    .nav-change-neg {
        color: var(--danger-color);
        font-weight: 700;
        font-size: 1rem;
        display: inline-block;
    }
    
    /* Cards and Containers */
    .dhan-box {
        background-color: var(--card-bg-color);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 1.2rem;
        margin-bottom: 1.5rem;
    }
    
    .dhan-box-header {
        font-family: var(--font-header);
        font-weight: 600;
        color: var(--text-highlight-color);
        font-size: 1.05rem;
        margin-bottom: 1rem;
        border-bottom: 1px solid var(--border-color);
        padding-bottom: 0.5rem;
    }
    
    /* Metrics Inside Cards */
    .metric-row {
        display: flex;
        justify-content: space-between;
        margin-bottom: 0.8rem;
        font-size: 0.88rem;
    }
    
    .metric-label {
        color: var(--text-muted-color);
    }
    
    .metric-value {
        color: var(--text-highlight-color);
        font-weight: 600;
    }
 
    /* Returns Dashboard Card */
    .return-card {
        text-align: center;
        padding: 0.8rem;
        background-color: var(--card-bg-color);
        border: 1px solid var(--border-color);
        border-radius: 6px;
    }
    
    .return-num {
        color: var(--success-color);
        font-size: 1.4rem;
        font-weight: 700;
        font-family: var(--font-header);
    }
    
    /* Holdings Table */
    .holdings-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.85rem;
    }
    .holdings-table th {
        text-align: left;
        color: var(--text-muted-color);
        font-weight: 600;
        border-bottom: 1px solid var(--border-color);
        padding: 8px 4px;
        text-transform: uppercase;
        font-size: 0.72rem;
    }
    .holdings-table td {
        padding: 10px 4px;
        border-bottom: 1px dashed var(--border-color);
        color: var(--text-color);
    }
    
    /* Riskometer Card */
    .riskometer-box {
        border-left: 4px solid var(--danger-color);
        background-color: rgba(239, 68, 68, 0.1);
        border-radius: 6px;
        padding: 0.8rem;
        font-size: 0.85rem;
        color: var(--danger-color);
    }
    
    /* Fund Summary Card */
    .fund-summary-card {
        background: linear-gradient(135deg, var(--card-bg-color), var(--bg-color));
        border: 1px solid var(--border-color);
        border-radius: 10px;
        padding: 1.2rem;
        margin-bottom: 1.4rem;
        box-shadow: 0 4px 24px rgba(0,0,0,0.4);
    }
    .fund-summary-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.55rem 0;
        border-bottom: 1px solid var(--border-color);
        font-size: 0.84rem;
    }
    .fund-summary-row:last-child { border-bottom: none; }
    .fund-summary-label { color: var(--text-muted-color); font-weight: 500; }
    .fund-summary-value { color: var(--text-highlight-color); font-weight: 600; text-align: right; }
    
    /* Dhan RAG Chat Analyst Container & Bubbles */
    .chat-row-user {
        display: flex;
        justify-content: flex-end;
        align-items: flex-start;
        margin-bottom: 1.2rem;
        width: 100%;
    }
    
    .chat-row-analyst {
        display: flex;
        justify-content: flex-start;
        align-items: flex-start;
        margin-bottom: 1.2rem;
        width: 100%;
    }
    
    .chat-bubble-new {
        max-width: 86%;
        padding: 0.9rem 1.15rem;
        font-size: 0.88rem;
        line-height: 1.55;
        position: relative;
        font-family: var(--font-body);
    }
    
    .chat-bubble-new-user {
        background: rgba(255, 255, 255, 0.05) !important;
        backdrop-filter: blur(8px) !important;
        -webkit-backdrop-filter: blur(8px) !important;
        border: 1px solid var(--border-color) !important;
        color: var(--text-highlight-color) !important;
        border-radius: 16px 16px 0px 16px !important;
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.25) !important;
    }
    
    .chat-bubble-new-analyst {
        background: var(--card-bg-color) !important;
        backdrop-filter: blur(8px) !important;
        -webkit-backdrop-filter: blur(8px) !important;
        border: 1px solid var(--border-color) !important;
        color: var(--text-color) !important;
        border-radius: 16px 16px 16px 0px !important;
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3) !important;
        border-left: 3px solid var(--primary-color) !important;
    }
 
    /* Style markdown tables inside the analyst bubbles */
    .chat-bubble-new-analyst table {
        width: 100% !important;
        border-collapse: collapse !important;
        margin: 0.8rem 0 !important;
        font-size: 0.8rem !important;
    }
    .chat-bubble-new-analyst th {
        background-color: var(--bg-color) !important;
        color: var(--text-muted-color) !important;
        padding: 6px 10px !important;
        text-align: left !important;
        font-weight: 700 !important;
        border-bottom: 1px solid var(--border-color) !important;
    }
    .chat-bubble-new-analyst td {
        padding: 6px 10px !important;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05) !important;
        color: var(--text-highlight-color) !important;
    }
    .chat-bubble-new-analyst tr:last-child td {
        border-bottom: none !important;
    }
 
    /* Copy/Helpful actions inside chatbot response */
    .chat-bubble-footer {
        display: flex;
        gap: 12px;
        margin-top: 8px;
        padding-top: 6px;
        border-top: 1px solid rgba(255, 255, 255, 0.05);
        font-size: 0.65rem;
        color: var(--text-muted-color);
        font-weight: 500;
    }
    .chat-bubble-footer span {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        cursor: pointer;
        transition: color 0.2s;
    }
    .chat-bubble-footer span:hover {
        color: var(--primary-color);
    }
    
    .chat-avatar-user {
        width: 32px;
        height: 32px;
        background: linear-gradient(135deg, var(--card-bg-color), var(--bg-color));
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.95rem;
        margin-left: 10px;
        border: 1px solid var(--border-color);
        box-shadow: 0 2px 5px rgba(0,0,0,0.3);
    }
    
    .chat-avatar-analyst {
        width: 32px;
        height: 32px;
        background: linear-gradient(135deg, var(--card-bg-color), var(--bg-color));
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.95rem;
        margin-right: 10px;
        color: var(--primary-color);
        border: 1px solid rgba(226, 255, 59, 0.3);
        box-shadow: 0 2px 5px rgba(0,0,0,0.3);
    }
    
    .chat-source-chip-container {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
        margin-top: -0.6rem;
        margin-bottom: 1.2rem;
        padding-left: 42px;
    }
    
    .chat-source-chip {
        display: inline-flex;
        align-items: center;
        background-color: var(--card-bg-color);
        border: 1px solid var(--border-color);
        border-radius: 20px;
        padding: 4px 10px;
        font-size: 0.7rem;
        color: var(--text-muted-color);
        font-weight: 600;
        transition: all 0.2s;
    }
    
    .chat-source-chip:hover {
        background-color: rgba(255, 255, 255, 0.05);
        border-color: var(--primary-color);
        color: var(--text-highlight-color);
    }
    
    .chat-source-item {
        font-size: 0.76rem;
        background-color: var(--bg-color);
        border: 1px solid var(--border-color);
        border-radius: 6px;
        padding: 8px 12px;
        margin-top: 5px;
    }
    
    /* Glowing focus outline inside stChatInput textarea */
    div[data-testid="column"] .stChatInput textarea {
        background-color: var(--card-bg-color) !important;
        border: 1px solid var(--border-color) !important;
        color: var(--text-highlight-color) !important;
        border-radius: 8px !important;
        transition: all 0.3s ease !important;
    }
    div[data-testid="column"] .stChatInput textarea:focus {
        border-color: var(--primary-color) !important;
        box-shadow: 0 0 10px rgba(226, 255, 59, 0.2) !important;
    }
    
    /* Streamlit tabs styling override */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: transparent;
        border: none;
        color: var(--text-muted-color);
        font-weight: 600;
        font-size: 0.9rem;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: var(--text-highlight-color);
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        color: var(--primary-color);
        border-bottom: 2px solid var(--primary-color);
    }
    /* SaaS-Style Sidebar Navigation Switcher */
    [data-testid="stSidebar"] {
        background-color: var(--bg-color) !important;
        border-right: 1px solid var(--border-color) !important;
    }
    
    [data-testid="stSidebar"] .stButton > button {
        background-color: transparent !important;
        color: var(--text-muted-color) !important;
        border: none !important;
        text-align: left !important;
        justify-content: flex-start !important;
        padding: 0.6rem 0.8rem !important;
        width: 100% !important;
        border-radius: 6px !important;
        font-size: 0.85rem !important;
        font-weight: 500 !important;
        transition: all 0.2s ease-in-out !important;
        box-shadow: none !important;
    }
    
    [data-testid="stSidebar"] .stButton > button:hover {
        background-color: rgba(255, 255, 255, 0.05) !important;
        color: var(--text-highlight-color) !important;
    }
    
    .active-nav-item {
        background-color: rgba(255, 255, 255, 0.05);
        border-left: 3.5px solid var(--primary-color);
        color: var(--primary-color);
        padding: 0.6rem 0.8rem;
        border-radius: 0 6px 6px 0;
        font-size: 0.85rem;
        font-weight: 700;
        margin-bottom: 4px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        letter-spacing: 0.02em;
    }
    
    .active-nav-nav {
        font-size: 0.8rem;
        color: var(--text-highlight-color);
        font-weight: 600;
        margin-left: 8px;
    }
    
    /* News Feed Styling */
    a.news-link {
        color: var(--text-highlight-color) !important;
        text-decoration: none !important;
        transition: color 0.15s ease-in-out !important;
    }
    a.news-link:hover {
        color: var(--primary-color) !important;
    }
    
    /* Download Button override */
    div.stDownloadButton > button {
        background-color: var(--card-bg-color) !important;
        color: var(--text-color) !important;
        border: 1px solid var(--border-color) !important;
        font-weight: 600 !important;
        border-radius: 6px !important;
        transition: all 0.2s ease-in-out !important;
        box-shadow: none !important;
    }
    div.stDownloadButton > button:hover {
        border-color: var(--primary-color) !important;
        color: var(--primary-color) !important;
        background-color: rgba(255, 255, 255, 0.05) !important;
    }
</style>
""", unsafe_allow_html=True)

# Convert logo to base64 for raw HTML rendering in navigation bar
import base64
def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode("utf-8")
    except Exception:
        return ""

logo_base64 = get_base64_image("assets/logo.png")
if logo_base64:
    logo_html = f'<img src="data:image/png;base64,{logo_base64}" width="28" height="28" style="border-radius: 4px; object-fit: contain;" />'
else:
    logo_html = '<span style="font-size:1.2rem; margin-right:4px;">⚡</span>'

# --- TOP NAVIGATION BAR ---
st.markdown(
    f"""
    <div class="dhan-nav">
        <div class="dhan-logo" style="display: flex; align-items: center; gap: 8px;">
            {logo_html}
            <span>ArthaAI</span>
        </div>
        <div style="color:var(--text-highlight-color); font-size:0.9rem; font-weight:600; margin-right:1.5rem; margin-top:2px;">Markets</div>
        <div style="color:var(--primary-color); font-size:0.9rem; font-weight:600; margin-right:1.5rem; border-bottom: 2px solid var(--primary-color); padding-bottom:12px; margin-bottom:-12px; margin-top:2px;">Mutual Funds</div>
        <div style="color:var(--text-muted-color); font-size:0.9rem; font-weight:500; margin-right:1.5rem; margin-top:2px;">Portfolio</div>
        <div style="color:var(--text-muted-color); font-size:0.9rem; font-weight:500; margin-right:1.5rem; margin-top:2px;">Orders</div>
    </div>
    """,
    unsafe_allow_html=True
)

# Initialize session state for selected scheme
if "selected_scheme" not in st.session_state:
    st.session_state["selected_scheme"] = "parag_parikh_flexi"
selected_key = st.session_state["selected_scheme"]

# --- PARALLEL NAV PRE-FETCHING ---
all_nav_data = get_all_nav_data_cached()


# --- SIDEBAR: SAAS NAVIGATION LIST ---
with st.sidebar:
    col_logo, col_title = st.columns([1, 3.5])
    with col_logo:
        if os.path.exists("assets/logo.png"):
            st.image("assets/logo.png", width=42)
        else:
            st.markdown("<h2 style='margin:0; padding:0; line-height:1; font-size:1.8rem;'>⚡</h2>", unsafe_allow_html=True)
    with col_title:
        st.markdown("<h2 style='font-family:Outfit; color:white; font-size:1.45rem; margin-top:0.25rem; margin-bottom:0; line-height:1;'>ArthaAI</h2>", unsafe_allow_html=True)
    st.markdown("<div style='margin-bottom: 1.2rem;'></div>", unsafe_allow_html=True)
    st.markdown("<span style='font-size:0.7rem; font-weight:700; color:#8A99AD; letter-spacing:0.08em; display:block; margin-bottom:0.8rem;'>SCHEMES WORKSPACE</span>", unsafe_allow_html=True)
    
    short_names = {
        "parag_parikh_flexi": "PP Flexi Cap",
        "pp_tax_saver": "PP Tax Saver ELSS",
        "pp_conservative": "PP Cons Hybrid",
        "pp_liquid": "PP Liquid Fund",
        "pp_dynamic": "PP Dynamic Alloc"
    }

    for key, item in FUND_DATA.items():
        nav_info = all_nav_data[key]
        is_active = (key == selected_key)
        name_display = short_names.get(key, item["name"])
        
        if is_active:
            # Active item rendered as highlighted box
            change_val = nav_info["change"].split(" ")[0]
            change_color = config.STITCH_DESIGN["success_color"] if nav_info["change_positive"] else config.STITCH_DESIGN["danger_color"]
            st.markdown(
                f"""
                <div class="active-nav-item">
                    <span>📁 {name_display}</span>
                    <span class="active-nav-nav">{nav_info["nav"]} <span style="color:{change_color}; font-size:0.75rem;">({change_val})</span></span>
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            # Inactive item rendered as flat button
            btn_label = f"📁 {name_display}"
            if st.button(btn_label, key=f"sidebar_btn_{key}", use_container_width=True):
                st.session_state["selected_scheme"] = key
                st.rerun()

    st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)
    st.divider()
    
    # Utilities in sidebar
    if st.button("🔄 Refresh Live NAV", key="sidebar_refresh", use_container_width=True):
        clear_nav_cache()
        st.cache_data.clear()
        st.rerun()
        
    st.markdown(
        """
        <div style="font-size:0.68rem; color:#5A697D; line-height:1.45; margin-top:0.8rem; border-top:1px solid #1C232E; padding-top:0.8rem;">
            <b>RAG Isolation Mode</b>: Database queries are isolated strictly to this scheme's documents.
            <div style="margin-top: 6px;"></div>
            <b>Disclaimer</b>: Mutual Fund investments are subject to market risks. Read all scheme-related documents carefully. AI insights and sentiment analysis are for informational purposes only and do not constitute financial advice. NAV data is sourced live from public feeds (MFAPI). This platform is an independent educational tool and is not affiliated, associated, authorized, endorsed by, or in any way officially connected with Dhan (Moneylicious Securities Pvt. Ltd.) or any of its subsidiaries.
        </div>
        """,
        unsafe_allow_html=True
    )

# Get selected scheme facts
scheme = FUND_DATA[selected_key]

# --- FETCH LIVE NAV FROM MFAPI (Retrieved from pre-fetched pool) ---
live_nav_data = all_nav_data[selected_key]
display_nav = live_nav_data["nav"]
display_change = live_nav_data["change"]
display_change_positive = live_nav_data["change_positive"]
nav_date = live_nav_data["date"]
is_live = live_nav_data["is_live"]

# --- WORKSPACE STATUS BAR ---
st.markdown(
    """
    <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid var(--border-color); padding-bottom:0.8rem; margin-bottom:1.5rem; margin-top:0.5rem;">
        <div style="font-size:0.7rem; font-weight:700; color:var(--text-muted-color); letter-spacing:0.12em; text-transform:uppercase;">
            ARTHAAI WORKSPACE &nbsp;/&nbsp; SCHEME RESEARCH & ANALYSIS
        </div>
        <div style="display:flex; align-items:center; gap:6px;">
            <span style="display:inline-block; width:6px; height:6px; background-color:var(--success-color); border-radius:50%; box-shadow:0 0 8px var(--success-color);"></span>
            <span style="font-size:0.65rem; font-weight:700; color:var(--success-color); letter-spacing:0.05em; text-transform:uppercase;">RAG SECURED CORE</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# --- TWO-COLUMN LAYOUT ---
left_col, right_col = st.columns([1.65, 1.0], gap="large")

# ==================== LEFT COLUMN: SCHEME ANALYSIS ====================
with left_col:
    # 1. Scheme Header
    st.markdown(f'<div class="scheme-title">{scheme["name"]}</div>', unsafe_allow_html=True)
    st.markdown(
        f'<span class="scheme-badge">DIRECT</span><span class="scheme-badge">GROWTH</span><span style="color:#8A99AD; font-size:0.85rem;">{scheme["category"]}</span>',
        unsafe_allow_html=True
    )
    st.markdown("<div style='margin-bottom:1.5rem;'></div>", unsafe_allow_html=True)
    
    # 2. NAV & Daily Change (Live from MFAPI)
    change_class = "nav-change-pos" if display_change_positive else "nav-change-neg"
    live_badge = (
        f'<span style="background:rgba(16,185,129,0.1); color:var(--success-color); font-size:0.65rem; font-weight:700; '
        f'padding:2px 7px; border-radius:4px; border:1px solid rgba(16,185,129,0.3); '
        f'margin-left:8px; vertical-align:middle;">&#9679; LIVE · {nav_date}</span>'
    ) if is_live else (
        f'<span style="background:rgba(245,158,11,0.1); color:var(--primary-color); font-size:0.65rem; font-weight:700; '
        f'padding:2px 7px; border-radius:4px; border:1px solid rgba(245,158,11,0.3); '
        f'margin-left:8px; vertical-align:middle;">&#9679; STATIC · Refresh to go live</span>'
    )
    st.markdown(
        f"""
        <div class="nav-box">
            <div class="nav-label">NET ASSET VALUE (NAV) {live_badge}</div>
            <div class="nav-val">{display_nav}</div>
            <div class="{change_class}">{display_change}</div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # 3. Dhan Scheme Tabs
    tab_overview, tab_holdings, tab_sip, tab_news, tab_overlap = st.tabs(["Overview & Returns", "Holdings Portfolio", "💰 SIP Calculator", "📰 News & Sentiment", "⚖️ Compare & Overlap"])
    
    with tab_overview:
        import pandas as pd
        import altair as alt

        st.markdown("<div style='margin-bottom:1rem;'></div>", unsafe_allow_html=True)

        # --- CAGR Return Cards ---
        st.markdown("<span style='font-size:0.8rem; font-weight:600; color:#8A99AD;'>HISTORICAL PERFORMANCE (CAGR)</span>", unsafe_allow_html=True)
        r_col1, r_col2, r_col3 = st.columns(3)
        with r_col1:
            st.markdown(f'<div class="return-card"><div class="nav-label">1Y RETURN</div><div class="return-num">{scheme["return_1y"]}</div></div>', unsafe_allow_html=True)
        with r_col2:
            st.markdown(f'<div class="return-card"><div class="nav-label">3Y RETURN</div><div class="return-num">{scheme["return_3y"]}</div></div>', unsafe_allow_html=True)
        with r_col3:
            st.markdown(f'<div class="return-card"><div class="nav-label">5Y RETURN</div><div class="return-num">{scheme["return_5y"]}</div></div>', unsafe_allow_html=True)

        st.markdown("<div style='margin-bottom:1.2rem;'></div>", unsafe_allow_html=True)

        # --- NAV HISTORY LINE CHART ---
        st.markdown("<span style='font-size:0.8rem; font-weight:600; color:#8A99AD;'>NAV PRICE HISTORY (LIVE · MFAPI)</span>", unsafe_allow_html=True)

        # Period selector using segmented control style
        period_key = f"nav_period_{selected_key}"
        if period_key not in st.session_state:
            st.session_state[period_key] = "1Y"

        period_cols = st.columns(6)
        period_labels = ["1M", "6M", "1Y", "3Y", "5Y", "All"]
        for i, period_label in enumerate(period_labels):
            with period_cols[i]:
                is_active = st.session_state[period_key] == period_label
                btn_style = (
                    f"background:{config.STITCH_DESIGN['primary_color']}; color:{config.STITCH_DESIGN['bg_color']}; font-weight:700;"
                    if is_active else
                    f"background:{config.STITCH_DESIGN['card_bg_color']}; color:{config.STITCH_DESIGN['text_muted_color']}; font-weight:500;"
                )
                if st.button(
                    period_label,
                    key=f"period_{selected_key}_{period_label}",
                    use_container_width=True,
                ):
                    st.session_state[period_key] = period_label
                    st.rerun()

        # Fetch and render chart
        selected_period = st.session_state[period_key]
        with st.spinner(f"Loading {selected_period} NAV history..."):
            df_hist = fetch_nav_history_cached(selected_key, period=selected_period)

        if df_hist is not None and len(df_hist) > 1:
            # Compute % change from period start for a normalised view in tooltip
            start_nav = df_hist["nav"].iloc[0]
            df_hist["pct_change"] = ((df_hist["nav"] - start_nav) / start_nav * 100).round(2)
            df_hist["date_str"] = df_hist["date"].dt.strftime("%d %b %Y")
            is_positive = df_hist["nav"].iloc[-1] >= df_hist["nav"].iloc[0]
            line_color = "#10B981" if is_positive else "#EF4444"
            area_color_start = "rgba(16,185,129,0.25)" if is_positive else "rgba(239,68,68,0.25)"

            # Base chart — no hover, no tooltip
            base = alt.Chart(df_hist).encode(
                x=alt.X(
                    "date:T",
                    axis=alt.Axis(
                        format="%b '%y",
                        labelColor=config.STITCH_DESIGN["text_muted_color"],
                        labelFontSize=10,
                        gridColor=config.STITCH_DESIGN["border_color"],
                        domainColor=config.STITCH_DESIGN["border_color"],
                        tickColor=config.STITCH_DESIGN["border_color"],
                    ),
                    title=None,
                ),
                y=alt.Y(
                    "nav:Q",
                    scale=alt.Scale(zero=False),
                    axis=alt.Axis(
                        labelColor=config.STITCH_DESIGN["text_muted_color"],
                        labelFontSize=10,
                        gridColor=config.STITCH_DESIGN["border_color"],
                        domainColor=config.STITCH_DESIGN["border_color"],
                        tickColor=config.STITCH_DESIGN["border_color"],
                        format=".0f",
                    ),
                    title=None,
                ),
            )

            # Gradient area fill — tooltip disabled
            area = base.mark_area(
                line={"color": line_color, "strokeWidth": 2},
                color=alt.Gradient(
                    gradient="linear",
                    stops=[
                        alt.GradientStop(color=area_color_start, offset=0),
                        alt.GradientStop(color="rgba(8,10,12,0.0)", offset=1),
                    ],
                    x1=1, x2=1, y1=1, y2=0,
                ),
                interpolate="monotone",
                tooltip=None,
            )

            chart = area.properties(
                height=220,
            ).configure(
                background="transparent",
            ).configure_view(
                strokeWidth=0,
            )

            st.altair_chart(chart, use_container_width=True)

            # Mini stats below chart
            period_start = df_hist["nav"].iloc[0]
            period_end = df_hist["nav"].iloc[-1]
            period_high = df_hist["nav"].max()
            period_low = df_hist["nav"].min()
            period_ret = ((period_end - period_start) / period_start) * 100
            ret_color = config.STITCH_DESIGN["success_color"] if period_ret >= 0 else config.STITCH_DESIGN["danger_color"]
            sign = "+" if period_ret >= 0 else ""
            st.markdown(
                f"""
                <div style="display:flex; gap:1rem; margin-top:-0.5rem; margin-bottom:1rem;">
                    <div style="flex:1; background:var(--card-bg-color); border:1px solid var(--border-color); border-radius:6px; padding:0.6rem 0.8rem; text-align:center;">
                        <div style="font-size:0.65rem; color:var(--text-muted-color); font-weight:600;">PERIOD RETURN</div>
                        <div style="font-size:1rem; font-weight:700; color:{ret_color};">{sign}{period_ret:.1f}%</div>
                    </div>
                    <div style="flex:1; background:var(--card-bg-color); border:1px solid var(--border-color); border-radius:6px; padding:0.6rem 0.8rem; text-align:center;">
                        <div style="font-size:0.65rem; color:var(--text-muted-color); font-weight:600;">{selected_period} HIGH</div>
                        <div style="font-size:1rem; font-weight:700; color:var(--text-highlight-color)">₹{period_high:,.2f}</div>
                    </div>
                    <div style="flex:1; background:var(--card-bg-color); border:1px solid var(--border-color); border-radius:6px; padding:0.6rem 0.8rem; text-align:center;">
                        <div style="font-size:0.65rem; color:var(--text-muted-color); font-weight:600;">{selected_period} LOW</div>
                        <div style="font-size:1rem; font-weight:700; color:var(--text-highlight-color)">₹{period_low:,.2f}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                "<div style='color:#8A99AD; font-size:0.85rem; padding:1rem; text-align:center;'>⚠️ Could not load chart data. Check your internet connection.</div>",
                unsafe_allow_html=True,
            )

        st.markdown("<div style='margin-bottom:0.5rem;'></div>", unsafe_allow_html=True)

        # --- Fund Description ---
        st.markdown("<span style='font-size:0.8rem; font-weight:600; color:#8A99AD;'>FUND DESCRIPTION</span>", unsafe_allow_html=True)
        st.markdown(
            f"""
            <div style="font-size:0.88rem; color:#BAC7D5; line-height:1.5; padding: 0.5rem 0;">
            {scheme['desc']}
            </div>
            """,
            unsafe_allow_html=True
        )
    with tab_holdings:
        st.markdown("<div style='margin-bottom:1.5rem;'></div>", unsafe_allow_html=True)
        st.markdown("<span style='font-size:0.85rem; font-weight:600; color:#8A99AD;'>PORTFOLIO ALLOCATION BREAKDOWN</span>", unsafe_allow_html=True)
        st.markdown("<div style='margin-bottom:1rem;'></div>", unsafe_allow_html=True)
        
        import pandas as pd
        import altair as alt
        
        try:
            # Prepare data
            df = pd.DataFrame(scheme["holdings"], columns=["Company", "Sector", "Allocation"])
            df["AllocNum"] = df["Allocation"].str.replace("%", "").astype(float)
            
            # Standalone Donut Chart with larger radii and right-aligned legend
            chart = alt.Chart(df).mark_arc(innerRadius=65, outerRadius=110, stroke=config.STITCH_DESIGN["bg_color"], strokeWidth=2).encode(
                theta=alt.Theta(field="AllocNum", type="quantitative"),
                color=alt.Color(
                    field="Company", 
                    type="nominal", 
                    scale=alt.Scale(range=[config.STITCH_DESIGN["primary_color"], config.STITCH_DESIGN["success_color"], "#3B82F6", "#F59E0B", "#EC4899"]),
                    legend=alt.Legend(
                        title=None,
                        orient="right",
                        labelColor=config.STITCH_DESIGN["text_color"],
                        labelFontSize=11,
                        labelFontWeight=500,
                        symbolSize=100,
                        rowPadding=6
                    )
                ),
                tooltip=[
                    alt.Tooltip(field="Company", type="nominal"),
                    alt.Tooltip(field="Sector", type="nominal"),
                    alt.Tooltip(field="Allocation", type="nominal")
                ]
            ).properties(
                width=450,
                height=280
            ).configure(
                background="transparent"
            ).configure_view(
                strokeWidth=0
            )
            
            st.altair_chart(chart, use_container_width=True)
        except Exception as chart_err:
            st.error(f"Error rendering chart: {chart_err}")

    with tab_sip:
        import pandas as pd
        import altair as alt

        st.markdown("<div style='margin-bottom:1rem;'></div>", unsafe_allow_html=True)
        st.markdown("<span style='font-size:0.8rem; font-weight:600; color:#8A99AD;'>SIP CALCULATOR (COMPOUND INTEREST DETAILED GROWTH)</span>", unsafe_allow_html=True)
        st.markdown("<div style='margin-bottom:1rem;'></div>", unsafe_allow_html=True)

        sip_col1, sip_col2 = st.columns([1.2, 1.0])
        with sip_col1:
            monthly_investment = st.slider(
                "Monthly Investment (₹)",
                min_value=500,
                max_value=200000,
                value=10000,
                step=500,
                format="₹%d",
                key=f"sip_amt_{selected_key}"
            )
            years = st.slider(
                "Investment Period (Years)",
                min_value=1,
                max_value=30,
                value=10,
                step=1,
                format="%d years",
                key=f"sip_years_{selected_key}"
            )
        with sip_col2:
            cagr_option = st.radio(
                "Expected Return Rate (CAGR)",
                options=[
                    f"3-Year CAGR ({scheme['return_3y']})",
                    f"5-Year CAGR ({scheme['return_5y']})",
                    f"1-Year CAGR ({scheme['return_1y']})",
                    "Custom Return Rate"
                ],
                key=f"sip_cagr_opt_{selected_key}"
            )
            if cagr_option == "Custom Return Rate":
                annual_rate = st.slider(
                    "Custom Return Rate (%)",
                    min_value=1.0,
                    max_value=30.0,
                    value=15.0,
                    step=0.5,
                    format="%.1f%%",
                    key=f"sip_custom_rate_{selected_key}"
                )
            elif "3-Year" in cagr_option:
                annual_rate = float(scheme["return_3y"].replace("%", ""))
            elif "5-Year" in cagr_option:
                annual_rate = float(scheme["return_5y"].replace("%", ""))
            else:
                annual_rate = float(scheme["return_1y"].replace("%", ""))

        # Calculate Projected Corpus
        # Formula: M = P * ((1 + i)^n - 1) / i * (1 + i)
        i = (annual_rate / 100) / 12
        n = years * 12
        total_invested = monthly_investment * n
        if i == 0:
            future_value = total_invested
        else:
            future_value = monthly_investment * (((1 + i)**n - 1) / i) * (1 + i)
        
        wealth_gained = max(0.0, future_value - total_invested)

        # Metric cards
        invested_str = f"₹{total_invested:,.0f}"
        wealth_str = f"₹{wealth_gained:,.0f}"
        total_str = f"₹{future_value:,.0f}"

        st.markdown(
            f"""
            <div style="display:flex; gap:1rem; margin-top:1rem; margin-bottom:1.5rem;">
                <div style="flex:1; background:var(--card-bg-color); border:1px solid var(--border-color); border-radius:6px; padding:0.8rem 1rem; text-align:center;">
                    <div style="font-size:0.65rem; color:var(--text-muted-color); font-weight:600; text-transform:uppercase; margin-bottom:2px;">Total Invested</div>
                    <div style="font-size:1.15rem; font-weight:700; color:var(--text-highlight-color);">{invested_str}</div>
                </div>
                <div style="flex:1; background:var(--card-bg-color); border:1px solid var(--border-color); border-radius:6px; padding:0.8rem 1rem; text-align:center;">
                    <div style="font-size:0.65rem; color:var(--text-muted-color); font-weight:600; text-transform:uppercase; margin-bottom:2px;">Est. Returns</div>
                    <div style="font-size:1.15rem; font-weight:700; color:var(--success-color);">{wealth_str}</div>
                </div>
                <div style="flex:1; background:var(--card-bg-color); border:1px solid var(--border-color); border-radius:6px; padding:0.8rem 1rem; text-align:center;">
                    <div style="font-size:0.65rem; color:var(--text-muted-color); font-weight:600; text-transform:uppercase; margin-bottom:2px;">Total Value</div>
                    <div style="font-size:1.15rem; font-weight:700; color:var(--primary-color);">{total_str}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Generate year-by-year trajectory
        chart_data = []
        for yr in range(1, int(years) + 1):
            m = yr * 12
            inv = monthly_investment * m
            if i == 0:
                fv = inv
            else:
                fv = monthly_investment * (((1 + i)**m - 1) / i) * (1 + i)
            chart_data.append({"Year": yr, "Amount": inv, "Type": "Invested Amount"})
            chart_data.append({"Year": yr, "Amount": round(fv), "Type": "Future Value"})

        df_chart = pd.DataFrame(chart_data)

        # Growth line chart (clean, static, no hover pop-ups, matches NAV chart)
        growth_chart = alt.Chart(df_chart).mark_line(strokeWidth=3, strokeCap="round", interpolate="monotone", tooltip=None).encode(
            x=alt.X("Year:Q", scale=alt.Scale(domain=[1, years]), axis=alt.Axis(tickCount=int(years), format="d", labelColor=config.STITCH_DESIGN["text_muted_color"], gridColor=config.STITCH_DESIGN["border_color"], domainColor=config.STITCH_DESIGN["border_color"], title="Years")),
            y=alt.Y("Amount:Q", axis=alt.Axis(format="~s", labelColor=config.STITCH_DESIGN["text_muted_color"], gridColor=config.STITCH_DESIGN["border_color"], domainColor=config.STITCH_DESIGN["border_color"], title="Amount (₹)")),
            color=alt.Color("Type:N", scale=alt.Scale(domain=["Invested Amount", "Future Value"], range=["#4F5E71", config.STITCH_DESIGN["primary_color"]]), legend=alt.Legend(title=None, orient="bottom", labelColor=config.STITCH_DESIGN["text_color"], labelFontSize=11)),
        ).properties(
            height=200
        ).configure(
            background="transparent"
        ).configure_view(
            strokeWidth=0
        )

        st.altair_chart(growth_chart, use_container_width=True)

    with tab_news:
        st.markdown("<div style='margin-bottom:1rem;'></div>", unsafe_allow_html=True)
        st.markdown("<span style='font-size:0.8rem; font-weight:600; color:#8A99AD;'>NEWS SENTIMENT ANALYSIS & TRANSACTION TRACKER</span>", unsafe_allow_html=True)
        st.markdown("<div style='margin-bottom:1rem;'></div>", unsafe_allow_html=True)

        with st.spinner("Fetching latest news from Google News..."):
            articles = fetch_google_news_cached(selected_key)

        if articles:
            # Analyze sentiment and buys/sells using Gemini
            with st.spinner("Analyzing news sentiment and buys/sells with Gemini..."):
                api_key = os.environ.get("GEMINI_API_KEY", "")
                analysis_report = analyze_sentiment_cached(articles, scheme["name"], api_key)
            
            # Show LLM Analysis Report
            st.markdown(analysis_report)
            
            # Show raw headlines below
            st.markdown("<div style='margin-bottom:1.8rem; border-bottom:1px solid #1C232E; padding-bottom:1rem;'></div>", unsafe_allow_html=True)
            st.markdown("<span style='font-size:0.8rem; font-weight:600; color:#8A99AD;'>RECENT GOOGLE NEWS ARTICLES FEED</span>", unsafe_allow_html=True)
            st.markdown("<div style='margin-bottom:1rem;'></div>", unsafe_allow_html=True)
            
            for art in articles:
                date_str = art["date"]
                try:
                    parts = date_str.split(" ")
                    if len(parts) >= 4:
                        date_str = f"{parts[1]} {parts[2]} {parts[3]}"
                except:
                    pass
                    
                st.markdown(
                    f"""
                    <div style="background:#0E1217; border:1px solid #1C232E; border-radius:6px; padding:0.8rem 1rem; margin-bottom:0.8rem;">
                        <div style="display:flex; justify-content:space-between; align-items:baseline; margin-bottom:6px;">
                            <span style="font-size:0.7rem; font-weight:700; color:#E2FF3B; text-transform:uppercase; letter-spacing:0.05em;">{art['source']}</span>
                            <span style="font-size:0.65rem; color:#8A99AD;">{date_str}</span>
                        </div>
                        <a class="news-link" href="{art['link']}" target="_blank" style="font-size:0.9rem; font-weight:600; line-height:1.45;">
                            {art['title']}
                        </a>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        else:
            st.markdown(
                "<div style='color:#8A99AD; font-size:0.85rem; padding:1.5rem; text-align:center;'>⚠️ No recent news articles found for this fund house.</div>",
                unsafe_allow_html=True
            )

    with tab_overlap:
        st.markdown("<div style='margin-bottom:1rem;'></div>", unsafe_allow_html=True)
        st.markdown("<span style='font-size:0.8rem; font-weight:600; color:#8A99AD;'>MUTUAL FUND SCHEME COMPARE & OVERLAP ANALYZER</span>", unsafe_allow_html=True)
        st.markdown("<div style='margin-bottom:1rem;'></div>", unsafe_allow_html=True)

        comp_options = [k for k in FUND_DATA.keys() if k != selected_key]
        comparison_key = st.selectbox(
            "Select Mutual Fund to compare overlap with:",
            options=comp_options,
            format_func=lambda x: FUND_DATA[x]["name"],
            key=f"overlap_compare_{selected_key}"
        )
        
        comp_scheme = FUND_DATA[comparison_key]
        
        # --- SIDE-BY-SIDE SPECIFICATIONS COMPARISON ---
        st.markdown("<span style='font-size:0.8rem; font-weight:600; color:#8A99AD;'>KEY SCHEME SPECIFICATIONS COMPARISON</span>", unsafe_allow_html=True)
        st.markdown("<div style='margin-bottom:0.5rem;'></div>", unsafe_allow_html=True)
        
        # Color coding variables
        r_color_a = config.STITCH_DESIGN["danger_color"] if "Very High" in scheme["riskometer"] else config.STITCH_DESIGN.get("warning_color", "#F59E0B")
        r_color_b = config.STITCH_DESIGN["danger_color"] if "Very High" in comp_scheme["riskometer"] else config.STITCH_DESIGN.get("warning_color", "#F59E0B")
        
        import textwrap
        st.markdown(
            textwrap.dedent(f"""
            <table style="width:100%; border-collapse:collapse; background:var(--card-bg-color); border:1px solid var(--border-color); border-radius:6px; overflow:hidden; font-size:0.85rem; margin-bottom:1.5rem;">
                <thead>
                    <tr style="border-bottom:1px solid var(--border-color); text-align:left; background:var(--bg-color);">
                        <th style="padding:0.6rem 0.8rem; color:var(--text-muted-color); font-weight:700;">Metric</th>
                        <th style="padding:0.6rem 0.8rem; color:var(--text-highlight-color); font-weight:700;">{scheme['name']}</th>
                        <th style="padding:0.6rem 0.8rem; color:var(--text-highlight-color); font-weight:700;">{comp_scheme['name']}</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td style="color:var(--text-muted-color); padding:0.5rem 0.8rem; border-bottom:1px solid var(--border-color);">Category</td>
                        <td style="color:var(--text-highlight-color); padding:0.5rem 0.8rem; border-bottom:1px solid var(--border-color); font-weight:500;">{scheme['category']}</td>
                        <td style="color:var(--text-highlight-color); padding:0.5rem 0.8rem; border-bottom:1px solid var(--border-color); font-weight:500;">{comp_scheme['category']}</td>
                    </tr>
                    <tr>
                        <td style="color:var(--text-muted-color); padding:0.5rem 0.8rem; border-bottom:1px solid var(--border-color);">AUM (Size)</td>
                        <td style="color:var(--text-highlight-color); padding:0.5rem 0.8rem; border-bottom:1px solid var(--border-color); font-weight:600;">{scheme['aum']}</td>
                        <td style="color:var(--text-highlight-color); padding:0.5rem 0.8rem; border-bottom:1px solid var(--border-color); font-weight:600;">{comp_scheme['aum']}</td>
                    </tr>
                    <tr>
                        <td style="color:var(--text-muted-color); padding:0.5rem 0.8rem; border-bottom:1px solid var(--border-color);">Expense Ratio</td>
                        <td style="color:var(--primary-color); padding:0.5rem 0.8rem; border-bottom:1px solid var(--border-color); font-weight:700;">{scheme['expense_ratio']}</td>
                        <td style="color:var(--primary-color); padding:0.5rem 0.8rem; border-bottom:1px solid var(--border-color); font-weight:700;">{comp_scheme['expense_ratio']}</td>
                    </tr>
                    <tr>
                        <td style="color:var(--text-muted-color); padding:0.5rem 0.8rem; border-bottom:1px solid var(--border-color);">1Y Return (CAGR)</td>
                        <td style="color:var(--success-color); padding:0.5rem 0.8rem; border-bottom:1px solid var(--border-color); font-weight:700;">{scheme['return_1y']}</td>
                        <td style="color:var(--success-color); padding:0.5rem 0.8rem; border-bottom:1px solid var(--border-color); font-weight:700;">{comp_scheme['return_1y']}</td>
                    </tr>
                    <tr>
                        <td style="color:var(--text-muted-color); padding:0.5rem 0.8rem; border-bottom:1px solid var(--border-color);">3Y Return (CAGR)</td>
                        <td style="color:var(--success-color); padding:0.5rem 0.8rem; border-bottom:1px solid var(--border-color); font-weight:700;">{scheme['return_3y']}</td>
                        <td style="color:var(--success-color); padding:0.5rem 0.8rem; border-bottom:1px solid var(--border-color); font-weight:700;">{comp_scheme['return_3y']}</td>
                    </tr>
                    <tr>
                        <td style="color:var(--text-muted-color); padding:0.5rem 0.8rem; border-bottom:1px solid var(--border-color);">5Y Return (CAGR)</td>
                        <td style="color:var(--success-color); padding:0.5rem 0.8rem; border-bottom:1px solid var(--border-color); font-weight:700;">{scheme['return_5y']}</td>
                        <td style="color:var(--success-color); padding:0.5rem 0.8rem; border-bottom:1px solid var(--border-color); font-weight:700;">{comp_scheme['return_5y']}</td>
                    </tr>
                    <tr>
                        <td style="color:var(--text-muted-color); padding:0.5rem 0.8rem; border-bottom:1px solid var(--border-color);">Riskometer</td>
                        <td style="color:{r_color_a}; padding:0.5rem 0.8rem; border-bottom:1px solid var(--border-color); font-weight:600;">{scheme['riskometer']}</td>
                        <td style="color:{r_color_b}; padding:0.5rem 0.8rem; border-bottom:1px solid var(--border-color); font-weight:600;">{comp_scheme['riskometer']}</td>
                    </tr>
                    <tr>
                        <td style="color:var(--text-muted-color); padding:0.5rem 0.8rem;">Fund Manager</td>
                        <td style="color:var(--text-highlight-color); padding:0.5rem 0.8rem;">{scheme['manager']}</td>
                        <td style="color:var(--text-highlight-color); padding:0.5rem 0.8rem;">{comp_scheme['manager']}</td>
                    </tr>
                </tbody>
            </table>
            """),
            unsafe_allow_html=True
        )

        # Parse holdings into dictionary of {normalized_company_name: {original_name, sector, alloc}}
        def parse_holdings(holdings_list):
            h_dict = {}
            for company, sector, alloc_str in holdings_list:
                try:
                    alloc_val = float(alloc_str.replace("%", "").strip())
                    
                    # Normalize company name for matching:
                    # 1. Lowercase
                    # 2. Strip special characters
                    # 3. Strip common corporate suffixes
                    import re
                    norm = company.lower().strip()
                    norm = norm.replace("£", "").strip()
                    norm = re.sub(r'\b(ltd|limited|corp|corporation|inc|co)\b\.?', '', norm)
                    norm = re.sub(r'\s+', ' ', norm).strip()
                    
                    h_dict[norm] = {"original_name": company, "sector": sector, "alloc": alloc_val}
                except ValueError:
                    pass
            return h_dict
            
        holdings_a = parse_holdings(scheme["holdings"])
        holdings_b = parse_holdings(comp_scheme["holdings"])
        
        # Calculate overlap using Morningstar / standard mutual fund overlap formula:
        # Overlap = sum(min(alloc_A(c), alloc_B(c)))
        common_companies = set(holdings_a.keys()).intersection(set(holdings_b.keys()))
        overlap_pct = 0.0
        common_data = []
        for company in common_companies:
            alloc_a = holdings_a[company]["alloc"]
            alloc_b = holdings_b[company]["alloc"]
            shared = min(alloc_a, alloc_b)
            overlap_pct += shared
            common_data.append({
                "Company": holdings_a[company]["original_name"],
                "Sector": holdings_a[company]["sector"],
                "Allocation A": f"{alloc_a:.2f}%",
                "Allocation B": f"{alloc_b:.2f}%",
                "Shared Overlap": f"{shared:.2f}%",
                "shared_val": shared
            })
            
        overlap_pct = round(overlap_pct, 2)
        
        # Classify diversification strength
        if overlap_pct < 20.0:
            status = "Low Overlap (Excellent Diversification)"
            status_color = config.STITCH_DESIGN["success_color"]
            bg_accent = "rgba(16, 185, 129, 0.1)"
        elif overlap_pct <= 50.0:
            status = "Moderate Overlap (Average Diversification)"
            status_color = config.STITCH_DESIGN["primary_color"]
            bg_accent = "rgba(226, 255, 59, 0.1)"
        else:
            status = "High Overlap (Poor Diversification Redundancy)"
            status_color = config.STITCH_DESIGN["danger_color"]
            bg_accent = "rgba(239, 68, 68, 0.1)"
            
        # Renders the Overlap KPI card
        st.markdown(
            textwrap.dedent(f"""
            <div style="background:var(--card-bg-color); border:1px solid var(--border-color); border-radius:8px; padding:1.5rem; margin-bottom:1.5rem; border-left: 4px solid {status_color};">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <div style="font-size:0.75rem; font-weight:700; color:var(--text-muted-color); text-transform:uppercase; letter-spacing:0.08em; margin-bottom:0.4rem;">
                            PORTFOLIO OVERLAP PERCENTAGE
                        </div>
                        <div style="font-size:2.2rem; font-weight:800; color:{status_color};">
                            {overlap_pct:.2f}%
                        </div>
                    </div>
                    <div style="text-align:right;">
                        <span style="font-size:0.7rem; font-weight:700; background:{bg_accent}; color:{status_color}; padding:0.4rem 0.8rem; border-radius:4px; border:1px solid {status_color}33;">
                            {status}
                        </span>
                    </div>
                </div>
            </div>
            """),
            unsafe_allow_html=True
        )
        
        # Shared Holdings Table
        st.markdown("<span style='font-size:0.8rem; font-weight:600; color:#8A99AD;'>OVERLAPPING STOCKS</span>", unsafe_allow_html=True)
        st.markdown("<div style='margin-bottom:0.5rem;'></div>", unsafe_allow_html=True)
        
        if common_data:
            common_data = sorted(common_data, key=lambda x: x["shared_val"], reverse=True)
            rows = ""
            for item in common_data:
                rows += f"""
                <tr>
                    <td style="color:var(--text-highlight-color); font-weight:600; padding:0.6rem 0.8rem; border-bottom:1px solid var(--border-color);">{item['Company']}</td>
                    <td style="color:var(--text-muted-color); padding:0.6rem 0.8rem; border-bottom:1px solid var(--border-color);">{item['Sector']}</td>
                    <td style="color:var(--text-highlight-color); text-align:right; padding:0.6rem 0.8rem; border-bottom:1px solid var(--border-color);">{item['Allocation A']}</td>
                    <td style="color:var(--text-highlight-color); text-align:right; padding:0.6rem 0.8rem; border-bottom:1px solid var(--border-color);">{item['Allocation B']}</td>
                    <td style="color:var(--primary-color); text-align:right; font-weight:700; padding:0.6rem 0.8rem; border-bottom:1px solid var(--border-color);">{item['Shared Overlap']}</td>
                </tr>
                """
                
            st.markdown(
                textwrap.dedent(f"""
                <table style="width:100%; border-collapse:collapse; background:var(--card-bg-color); border:1px solid var(--border-color); border-radius:6px; overflow:hidden; font-size:0.85rem; margin-bottom:1.5rem;">
                    <thead>
                        <tr style="border-bottom:1px solid var(--border-color); text-align:left; background:var(--bg-color);">
                            <th style="padding:0.75rem 1rem; color:var(--text-muted-color); font-weight:700;">Company</th>
                            <th style="padding:0.75rem 1rem; color:var(--text-muted-color); font-weight:700;">Sector</th>
                            <th style="padding:0.75rem 1rem; color:var(--text-muted-color); font-weight:700; text-align:right;">{scheme['name']}</th>
                            <th style="padding:0.75rem 1rem; color:var(--text-muted-color); font-weight:700; text-align:right;">{comp_scheme['name']}</th>
                            <th style="padding:0.75rem 1rem; color:var(--primary-color); font-weight:700; text-align:right;">Shared Overlap</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows}
                    </tbody>
                </table>
                """),
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                "<div style=\"background:var(--card-bg-color); border:1px solid var(--border-color); border-radius:6px; padding:1.5rem; text-align:center; color:var(--text-muted-color); font-size:0.85rem; margin-bottom:1.5rem;\">"
                "🟢 No overlapping holdings found in these two funds. Excellent diversification!"
                "</div>",
                unsafe_allow_html=True
            )
            
        # Unique portfolio drivers
        st.markdown("<span style='font-size:0.8rem; font-weight:600; color:#8A99AD;'>UNIQUE PORTFOLIO DRIVERS</span>", unsafe_allow_html=True)
        st.markdown("<div style='margin-bottom:0.8rem;'></div>", unsafe_allow_html=True)
        
        col_unique_a, col_unique_b = st.columns(2)
        
        with col_unique_a:
            st.markdown(f"<span style='font-size:0.75rem; font-weight:700; color:var(--text-muted-color); text-transform:uppercase;'>Unique to {scheme['name']}</span>", unsafe_allow_html=True)
            st.markdown("<div style='margin-bottom:0.4rem;'></div>", unsafe_allow_html=True)
            unique_a_keys = [c for c in holdings_a.keys() if c not in common_companies]
            if unique_a_keys:
                unique_a_keys = sorted(unique_a_keys, key=lambda x: holdings_a[x]['alloc'], reverse=True)
                list_items = ""
                for u in unique_a_keys:
                    orig_name = holdings_a[u]['original_name']
                    list_items += f"<li style='margin-bottom:0.4rem; font-size:0.85rem; color:var(--text-highlight-color);'><span style='font-weight:600;'>{orig_name}</span> <span style='color:var(--text-muted-color);'>({holdings_a[u]['alloc']:.2f}%)</span></li>"
                st.markdown(f"<ul style='list-style-type:square; padding-left:1.2rem;'>{list_items}</ul>", unsafe_allow_html=True)
            else:
                st.markdown("<div style='color:var(--text-muted-color); font-size:0.8rem;'>No unique holdings.</div>", unsafe_allow_html=True)
                
        with col_unique_b:
            st.markdown(f"<span style='font-size:0.75rem; font-weight:700; color:var(--text-muted-color); text-transform:uppercase;'>Unique to {comp_scheme['name']}</span>", unsafe_allow_html=True)
            st.markdown("<div style='margin-bottom:0.4rem;'></div>", unsafe_allow_html=True)
            unique_b_keys = [c for c in holdings_b.keys() if c not in common_companies]
            if unique_b_keys:
                unique_b_keys = sorted(unique_b_keys, key=lambda x: holdings_b[x]['alloc'], reverse=True)
                list_items = ""
                for u in unique_b_keys:
                    orig_name = holdings_b[u]['original_name']
                    list_items += f"<li style='margin-bottom:0.4rem; font-size:0.85rem; color:var(--text-highlight-color);'><span style='font-weight:600;'>{orig_name}</span> <span style='color:var(--text-muted-color);'>({holdings_b[u]['alloc']:.2f}%)</span></li>"
                st.markdown(f"<ul style='list-style-type:square; padding-left:1.2rem;'>{list_items}</ul>", unsafe_allow_html=True)
            else:
                st.markdown("<div style='color:var(--text-muted-color); font-size:0.8rem;'>No unique holdings.</div>", unsafe_allow_html=True)


# ==================== RIGHT COLUMN: FUND SUMMARY + AI CHAT ====================
with right_col:
    # 1. Fund Summary Card (replaces non-functional SIP card)
    change_indicator = f'<span style="color:{config.STITCH_DESIGN["success_color"] if display_change_positive else config.STITCH_DESIGN["danger_color"]}">{display_change}</span>'
    risk_color = config.STITCH_DESIGN["danger_color"] if "Very High" in scheme["riskometer"] else config.STITCH_DESIGN.get("warning_color", "#F59E0B") if "High" in scheme["riskometer"] else config.STITCH_DESIGN["success_color"]
    st.markdown(
        f"""
        <div class="fund-summary-card">
            <div style="font-size:0.7rem; font-weight:700; color:var(--text-muted-color); letter-spacing:0.08em; margin-bottom:0.8rem;">FUND SNAPSHOT</div>
            <div class="fund-summary-row">
                <span class="fund-summary-label">Current NAV</span>
                <span class="fund-summary-value">{display_nav} &nbsp;{change_indicator}</span>
            </div>
            <div class="fund-summary-row">
                <span class="fund-summary-label">AUM</span>
                <span class="fund-summary-value">{scheme['aum']}</span>
            </div>
            <div class="fund-summary-row">
                <span class="fund-summary-label">Expense Ratio</span>
                <span class="fund-summary-value" style="color:var(--primary-color);">{scheme['expense_ratio']}</span>
            </div>
            <div class="fund-summary-row">
                <span class="fund-summary-label">Min SIP</span>
                <span class="fund-summary-value">{scheme['min_sip']}</span>
            </div>
            <div class="fund-summary-row">
                <span class="fund-summary-label">Fund Manager</span>
                <span class="fund-summary-value">{scheme['manager']}</span>
            </div>
            <div class="fund-summary-row">
                <span class="fund-summary-label">Risk</span>
                <span class="fund-summary-value" style="color:{risk_color};">{scheme['riskometer']}</span>
            </div>
            <div class="fund-summary-row">
                <span class="fund-summary-label">Category</span>
                <span class="fund-summary-value">{scheme['category']}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # 1b. PDF Factsheet Downloader
    pdf_path = f"data/{selected_key}/true.pdf"
    pdf_bytes = b""
    if os.path.exists(pdf_path):
        try:
            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()
        except Exception:
            pdf_bytes = b""

    if pdf_bytes:
        download_name = f"{selected_key}_factsheet.pdf"
        st.download_button(
            label="📄 Download Factsheet PDF",
            data=pdf_bytes,
            file_name=download_name,
            mime="application/pdf",
            use_container_width=True,
            key=f"dl_pdf_{selected_key}"
        )
    else:
        # Fallback to public factsheet pages
        factsheet_urls = {
            "parag_parikh_flexi": "https://amc.ppfas.com/schemes/ppfas-flexi-cap-fund/",
            "pp_tax_saver": "https://amc.ppfas.com/schemes/parag-parikh-tax-saver-fund/",
            "pp_conservative": "https://amc.ppfas.com/schemes/parag-parikh-conservative-hybrid-fund/",
            "pp_liquid": "https://amc.ppfas.com/schemes/parag-parikh-liquid-fund/",
            "pp_dynamic": "https://amc.ppfas.com/schemes/parag-parikh-dynamic-asset-allocation-fund/"
        }
        url = factsheet_urls.get(selected_key)
        if url:
            st.markdown(
                f"""
                <a href="{url}" target="_blank" style="text-decoration:none;">
                    <button style="width:100%; padding:0.6rem; background-color:rgba(28,36,49,0.5); border:1px solid #E2FF3B; border-radius:4px; color:#E2FF3B; cursor:pointer; font-weight:bold;">
                        📄 View Public Factsheet Website
                    </button>
                </a>
                """,
                unsafe_allow_html=True
            )
    st.markdown("<div style='margin-bottom: 1.2rem;'></div>", unsafe_allow_html=True)

    # 2. ArthaAI RAG Chat Analyst
    col_header, col_clear = st.columns([2.2, 1.0])
    with col_header:
        st.markdown(
            """
            <div style='display:flex; align-items:center; gap:8px;'>
                <span style='display:inline-block; width:8px; height:8px; background-color:var(--primary-color); border-radius:50%; box-shadow:0 0 8px var(--primary-color);'></span>
                <h3 style='font-family:var(--font-header); color:var(--text-highlight-color); font-weight:700; font-size:1.35rem; margin:0;'>ArthaAI Analyst</h3>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col_clear:
        if st.button("🗑️ Clear Chat", use_container_width=True, key=f"clear_{selected_key}"):
            chat_key = f"artha_chat_{selected_key}"
            if chat_key in st.session_state:
                del st.session_state[chat_key]
            st.rerun()

    st.markdown(
        f"<div style='font-size:0.82rem; color:var(--text-muted-color); margin-bottom:1rem;'>Grounded context isolated to <b>{scheme['name']}</b>:</div>",
        unsafe_allow_html=True
    )
    
    # Session state Chat History for this fund
    chat_key = f"artha_chat_{selected_key}"
    if chat_key not in st.session_state:
        st.session_state[chat_key] = [
            {
                "role": "analyst",
                "content": f"Hi! I have parsed the official factsheet for **{scheme['name']}**. Ask me about portfolio composition, foreign holdings, risk metrics, or asset details. I am isolated to this fund."
            }
        ]
        
    # Render chat history with Dhan bubbles inside a fixed-height scrollable container
    chat_viewport = st.container(height=520)
    with chat_viewport:
        for chat in st.session_state[chat_key]:
            if chat["role"] == "user":
                st.markdown(
                    f"""
                    <div class="chat-row-user">
                        <div class="chat-bubble-new chat-bubble-new-user">
                            <div style="font-size:0.7rem; color:var(--text-muted-color); font-weight:600; margin-bottom:4px;">YOU</div>
                            <div>{chat['content']}</div>
                        </div>
                        <div class="chat-avatar-user">👤</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            else:
                # Parse markdown content to rich HTML
                html_content = markdown.markdown(chat['content'], extensions=['tables', 'nl2br'])
                st.markdown(
                    f"""
                    <div class="chat-row-analyst">
                        <div class="chat-avatar-analyst">⚡</div>
                        <div class="chat-bubble-new chat-bubble-new-analyst">
                            <div style="font-size:0.7rem; color:var(--primary-color); font-weight:700; margin-bottom:6px; font-family:var(--font-header); display:flex; justify-content:space-between; align-items:center;">
                                <span>⚡ ARTHAAI SECURED RAG</span>
                                <span style="color:var(--text-muted-color); font-weight:500; font-size:0.6rem; background:rgba(28,35,46,0.5); padding:2px 6px; border-radius:4px;">Grounded</span>
                            </div>
                            <div>{html_content}</div>
                            <div class="chat-bubble-footer">
                                <span>📋 Copy</span>
                                <span>👍 Helpful</span>
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                # Render sources inside collapsible expander (hidden by default)
                if "sources" in chat and chat["sources"]:
                    with st.expander("🔍 View Reference Passages", expanded=False):
                        for idx, (src_name, score, snippet) in enumerate(chat["sources"]):
                            # Convert L2 distance score to user-friendly similarity match percentage
                            match_pct = max(0, min(100, int((1.0 - (score / 2.0)) * 100.0)))
                            st.markdown(
                                f"""
                                <div class="chat-source-item" style="margin-top: 5px;">
                                    <span style="color:var(--success-color); font-weight:700; font-size:0.75rem;">SRC {idx+1}: {src_name}</span> &nbsp;|&nbsp; 
                                    <span style="color:var(--text-muted-color); font-size:0.7rem;">Match Score: {match_pct}%</span>
                                    <div style="color:var(--text-color); font-size:0.8rem; font-style:italic; margin-top:2px;">"{snippet}..."</div>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )

        # Quick Suggestions (only if the chat has just 1 welcome message)
        if len(st.session_state[chat_key]) == 1:
            st.markdown(
                """
                <div style='margin-top: 1.2rem; margin-bottom: 0.6rem;'>
                    <span style='font-size:0.7rem; color:#8A99AD; font-weight:700; letter-spacing:0.06em;'>QUICK QUESTIONS</span>
                </div>
                """,
                unsafe_allow_html=True
            )
            col_s1, col_s2, col_s3 = st.columns(3)
            with col_s1:
                if st.button("📊 Holdings", use_container_width=True, key=f"sug_holdings_{selected_key}"):
                    st.session_state[chat_key].append({"role": "user", "content": "What are the top 5 holdings in this scheme?"})
                    # Serve instantly from local metadata — no API call needed
                    rows = "\n".join(
                        [f"| {i+1} | {company} | {sector} | **{alloc}** |" for i, (company, sector, alloc) in enumerate(scheme["holdings"][:5])]
                    )
                    ans = (
                        f"Here are the top holdings for **{scheme['name']}** from the latest factsheet:\n\n"
                        f"| # | Company | Sector | Allocation |\n"
                        f"|---|---------|--------|-----------|\n"
                        f"{rows}"
                    )
                    st.session_state[chat_key].append({"role": "analyst", "content": ans, "sources": []})
                    st.rerun()
            with col_s2:
                if st.button("📈 Returns", use_container_width=True, key=f"sug_perf_{selected_key}"):
                    st.session_state[chat_key].append({"role": "user", "content": "Tell me about the NAV and CAGR returns."})
                    # Live NAV + static CAGR — instant, no API call needed
                    nav_source = f"MFAPI · {nav_date}" if is_live else "Static"
                    ans = (
                        f"Here is the performance snapshot for **{scheme['name']}**:\n\n"
                        f"| Metric | Value | Source |\n"
                        f"|--------|-------|--------|\n"
                        f"| **Current NAV** | **{display_nav}** | {nav_source} |\n"
                        f"| Daily Change | {display_change} | {nav_source} |\n"
                        f"| 1-Year CAGR | **{scheme['return_1y']}** | Factsheet |\n"
                        f"| 3-Year CAGR | **{scheme['return_3y']}** | Factsheet |\n"
                        f"| 5-Year CAGR | **{scheme['return_5y']}** | Factsheet |\n\n"
                        f"*Risk Profile: {scheme['riskometer']}*"
                    )
                    st.session_state[chat_key].append({"role": "analyst", "content": ans, "sources": []})
                    st.rerun()
            with col_s3:
                if st.button("💼 Expenses", use_container_width=True, key=f"sug_expense_{selected_key}"):
                    st.session_state[chat_key].append({"role": "user", "content": "What is the expense ratio and fees?"})
                    # Serve instantly from local metadata — no API call needed
                    ans = (
                        f"Here are the fee and expense specifications for **{scheme['name']}**:\n\n"
                        f"| Spec | Details |\n"
                        f"|------|---------|\n"
                        f"| Expense Ratio (Direct Plan) | **{scheme['expense_ratio']}** |\n"
                        f"| Minimum SIP Amount | **{scheme['min_sip']}** |\n"
                        f"| Exit Load | **Nil (most Direct plans)** |\n"
                        f"| Lock-in Period | **None** |\n"
                        f"| Risk Profile | **{scheme['riskometer']}** |\n\n"
                        f"*AUM: {scheme['aum']} | Fund Manager: {scheme['manager']}*"
                    )
                    st.session_state[chat_key].append({"role": "analyst", "content": ans, "sources": []})
                    st.rerun()

    # Chat Input
    if q_input := st.chat_input(f"Query {selected_key.replace('_', ' ').upper()} factsheet..."):
        # Append User Msg
        st.session_state[chat_key].append({"role": "user", "content": q_input})
        
        # Render the user message immediately so it appears on screen inside the container while the spinner runs
        with chat_viewport:
            st.markdown(
                f"""
                <div class="chat-row-user">
                    <div class="chat-bubble-new chat-bubble-new-user">
                        <div style="font-size:0.7rem; color:#8A99AD; font-weight:600; margin-bottom:4px;">YOU</div>
                        <div>{q_input}</div>
                    </div>
                    <div class="chat-avatar-user">👤</div>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            # Run QA
            with st.spinner("Analyzing context..."):
                extra_ctx = None
                
                # Dynamic check: Only perform news sentiment analysis if query relates to news, sentiment, or recent changes
                news_keywords = ["news", "sentiment", "recent", "buy", "sell", "holding changes", "article", "headline", "bought", "sold", "active", "transaction", "latest news"]
                is_news_query = any(k in q_input.lower() for k in news_keywords)
                
                if is_news_query:
                    api_key = os.environ.get("GEMINI_API_KEY")
                    if api_key:
                        news_report_key = f"news_report_{selected_key}"
                        # Check session state cache first
                        if news_report_key in st.session_state:
                            extra_ctx = st.session_state[news_report_key]
                        else:
                            try:
                                articles = fetch_google_news_cached(selected_key)
                                if articles:
                                    analysis_report = analyze_sentiment_cached(articles, scheme["name"], api_key)
                                    if analysis_report:
                                        st.session_state[news_report_key] = analysis_report
                                        extra_ctx = analysis_report
                            except Exception as e:
                                import logging
                                logging.getLogger(__name__).warning(f"Failed to fetch news context for chat: {e}")
    
                ans, docs = query_fund(q_input, selected_key, st.session_state[chat_key][:-1], extra_context=extra_ctx)
                
                # Format sources
                sources_list = []
                if docs:
                    for doc, score in docs:
                        snippet = doc.page_content[:250].replace('\n', ' ')
                        sources_list.append((doc.metadata.get('source', 'Unknown'), score, snippet))
                
                # Append Analyst Msg
                st.session_state[chat_key].append({
                    "role": "analyst",
                    "content": ans,
                    "sources": sources_list
                })
                st.rerun()
