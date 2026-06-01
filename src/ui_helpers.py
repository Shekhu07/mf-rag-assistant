import streamlit as st
import os
import sys
import base64
from pathlib import Path
from dotenv import load_dotenv

# Setup paths and imports
sys.path.append(str(Path(__file__).resolve().parent.parent))
from src.fund_metadata import FUND_DATA
from src.nav_service import get_live_nav, clear_nav_cache, fetch_nav_history
from src.news_service import fetch_google_news
import src.config as config

# Load environment variables
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# --- CACHED DATA WRAPPERS ---
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

def query_fund_api(query: str, fund_id: str, chat_history: list, extra_context: str = None) -> tuple[str, list]:
    """Queries the decoupled FastAPI RAG service on port 8000, with local direct fallback."""
    import requests
    api_url = os.environ.get("RAG_API_URL", "http://127.0.0.1:8000/query")
    try:
        payload = {
            "query": query,
            "fund_id": fund_id,
            "chat_history": chat_history,
            "extra_context": extra_context
        }
        resp = requests.post(api_url, json=payload, timeout=45)
        resp.raise_for_status()
        data = resp.json()
        ans = data["answer"]
        sources = [(src["source"], src["score"], src["snippet"]) for src in data.get("sources", [])]
        return ans, sources
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"FastAPI RAG service query failed: {e}. Falling back to local direct execution.")
        try:
            from src.query_engine import query_fund
            ans, docs = query_fund(query, fund_id, chat_history, extra_context=extra_context)
            sources = []
            if docs:
                for doc, score in docs:
                    snippet = doc.page_content[:250].replace('\n', ' ')
                    sources.append((doc.metadata.get('source', 'Unknown'), score, snippet))
            return ans, sources
        except Exception as fallback_err:
            logging.getLogger(__name__).error(f"Fallback local RAG query failed: {fallback_err}")
            return f"Error: Unable to connect to RAG server or run fallback. {e}", []

# --- UI INJECTION HELPERS ---
def inject_css():
    """Injects root styling variables and reads the style.css file."""
    # Load Stitch design system tokens dynamically on every page load
    design = config.load_stitch_design()
    
    # 1. Inject root variables
    st.markdown(f"""
    <style>
        :root {{
            --primary-color: {design["primary_color"]};
            --bg-color: {design["bg_color"]};
            --card-bg-color: {design["card_bg_color"]};
            --border-color: {design["border_color"]};
            --text-color: {design["text_color"]};
            --text-highlight-color: {design["text_highlight_color"]};
            --text-muted-color: {design["text_muted_color"]};
            --success-color: {design["success_color"]};
            --danger-color: {design["danger_color"]};
            --warning-color: {design["warning_color"]};
            --font-header: {design["font_header"]};
            --font-body: {design["font_body"]};
            --font-mono: {design["font_mono"]};
            --border-radius-sm: {design["border_radius_sm"]};
            --border-radius-md: {design["border_radius_md"]};
            --border-radius-lg: {design["border_radius_lg"]};
            --spacing-unit: {design["spacing_unit"]};
            --card-shadow: {design["card_shadow"]};
        }}
    </style>
    """, unsafe_allow_html=True)

    
    # 2. Inject static style.css content
    css_path = Path(__file__).resolve().parent.parent / "assets" / "style.css"
    if css_path.exists():
        with open(css_path, "r") as f:
            css_content = f.read()
            st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)

def render_top_navigation():
    """Renders the custom top navigation bar with base64 logo."""
    # Convert logo to base64
    logo_base64 = ""
    logo_path = Path(__file__).resolve().parent.parent / "assets" / "logo.png"
    if logo_path.exists():
        try:
            with open(logo_path, "rb") as img_file:
                logo_base64 = base64.b64encode(img_file.read()).decode("utf-8")
        except Exception:
            pass
            
    if logo_base64:
        logo_html = f'<img src="data:image/png;base64,{logo_base64}" width="28" height="28" style="border-radius: 4px; object-fit: contain;" />'
    else:
        logo_html = '<span style="font-size:1.2rem; margin-right:4px;">⚡</span>'
        
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

def render_sidebar():
    """Renders the mutual fund scheme selector sidebar."""
    if "selected_scheme" not in st.session_state:
        st.session_state["selected_scheme"] = "parag_parikh_flexi"
    selected_key = st.session_state["selected_scheme"]
    
    with st.sidebar:
        st.markdown(
            f"""
            <div style="padding: 1.5rem 0.5rem 0.5rem 0.5rem; text-align: left; border-bottom: 1px solid var(--border-color); margin-bottom: 1.2rem;">
                <div style="font-family: var(--font-header); font-weight: 800; font-size: 1.15rem; color: var(--text-highlight-color); display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">
                    📊 ArthaAI Terminal
                </div>
                <div style="font-size: 0.68rem; font-weight: 600; color: var(--text-muted-color); letter-spacing: 0.05em; text-transform: uppercase;">
                    Scheme Research Dashboard
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Display 5 schemes as stylized buttons
        st.markdown("<span style='font-size:0.75rem; font-weight:700; color:#8A99AD; letter-spacing:0.08em; text-transform:uppercase; padding-left:0.8rem; display:block; margin-bottom:0.6rem;'>SELECT MUTUAL FUND</span>", unsafe_allow_html=True)
        
        short_names = {
            "parag_parikh_flexi": "Flexi Cap Fund",
            "pp_tax_saver": "ELSS Tax Saver",
            "pp_conservative": "Conservative Hybrid",
            "pp_liquid": "Liquid Fund",
            "pp_dynamic": "Dynamic Asset Allocation"
        }
        
        for key, item in FUND_DATA.items():
            name_display = short_names.get(key, item["name"])
            if key == selected_key:
                st.markdown(
                    f"""
                    <div class="active-nav-item">
                        <span>📁 {name_display}</span>
                        <span class="active-nav-nav">ACTIVE</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            else:
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
                <b>Disclaimer</b>: Mutual Fund investments are subject to market risks. Read all scheme-related documents carefully. AI insights and Google News feed are for informational purposes only and do not constitute financial advice. NAV data is sourced live from public feeds (MFAPI). This platform is an independent educational tool and is not affiliated, associated, authorized, endorsed by, or in any way officially connected with Dhan (Moneylicious Securities Pvt. Ltd.) or any of its subsidiaries.
            </div>
            """,
            unsafe_allow_html=True
        )
    return selected_key
