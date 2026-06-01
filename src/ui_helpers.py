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
    design = config.load_stitch_design()

    st.markdown(f"""
    <style>
        :root {{
            --primary-color: {design["primary_color"]};
            --on-primary: {design.get("on_primary", "#002e6a")};
            --bg-color: {design["bg_color"]};
            --card-bg-color: {design["card_bg_color"]};
            --surface-container-low: {design.get("surface_container_low", "#131b2e")};
            --surface-lowest: {design.get("surface_lowest", "#060e20")};
            --surface-high: {design.get("surface_high", "#222a3d")};
            --surface-highest: {design.get("surface_highest", "#2d3449")};
            --surface-bright: {design.get("surface_bright", "#31394d")};
            --border-color: {design["border_color"]};
            --text-color: {design["text_color"]};
            --text-highlight-color: {design["text_highlight_color"]};
            --text-muted-color: {design["text_muted_color"]};
            --outline-color: {design.get("outline_color", "#8c909f")};
            --success-color: {design["success_color"]};
            --secondary-container: {design.get("secondary_container", "#00a572")};
            --danger-color: {design["danger_color"]};
            --error-container: {design.get("error_container", "#93000a")};
            --warning-color: {design["warning_color"]};
            --font-header: {design["font_header"]};
            --font-body: {design["font_body"]};
            --font-mono: {design.get("font_mono", "'JetBrains Mono', monospace")};
            --border-radius-sm: {design.get("border_radius_sm", "2px")};
            --border-radius-md: {design.get("border_radius_md", "4px")};
            --border-radius-lg: {design.get("border_radius_lg", "8px")};
            --border-radius-xl: {design.get("border_radius_xl", "12px")};
            --spacing-unit: {design.get("spacing_unit", "8px")};
            --card-shadow: {design.get("card_shadow", "none")};
        }}
    </style>
    """, unsafe_allow_html=True)

    css_path = Path(__file__).resolve().parent.parent / "assets" / "style.css"
    if css_path.exists():
        with open(css_path, "r") as f:
            css_content = f.read()
            st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)

def render_ticker_bar():
    """Renders the scrolling live market ticker bar at the top of the page."""
    ticker_data = [
        ("NIFTY 50", "22,453.30", "+0.45%", "up"),
        ("SENSEX", "73,876.84", "+0.38%", "up"),
        ("BANK NIFTY", "48,115.50", "-0.12%", "down"),
        ("USD/INR", "83.42", "0.00%", "flat"),
    ]

    items_html = ""
    for label, value, change, direction in ticker_data:
        arrow = "▲" if direction == "up" else ("▼" if direction == "down" else "")
        css_class = f"ticker-{direction}"
        items_html += f"""
        <span class="ticker-item">
            <span class="ticker-label">{label}</span>
            <span class="ticker-value">{value}</span>
            <span class="{css_class}">{arrow}{change}</span>
        </span>
        """

    # Duplicate for seamless loop
    full_html = items_html + items_html

    st.markdown(
        f"""
        <div class="ticker-bar">
            <div class="ticker-scroll">{full_html}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

def render_top_navigation():
    """Renders the terminal-style top navigation bar."""
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
        logo_html = '<div class="terminal-logo-icon">A</div>'

    st.markdown(
        f"""
        <div class="terminal-nav">
            <div style="display:flex; align-items:center; gap:10px; margin-left:2.8rem;">
                {logo_html}
                <div>
                    <div class="terminal-logo-text">ArthaAI</div>
                    <div class="terminal-logo-sub">Terminal v2.4</div>
                </div>
            </div>
            <div style="display:flex; align-items:center; margin-left:2rem;">
                <span class="terminal-nav-link terminal-nav-link-active">Mutual Funds</span>
                <span class="terminal-nav-link terminal-nav-link-inactive">Markets</span>
                <span class="terminal-nav-link terminal-nav-link-inactive">Portfolio</span>
            </div>
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
                <div style="font-family: var(--font-header); font-weight: 800; font-size: 1.15rem; color: var(--primary-color); display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">
                    📊 ArthaAI Terminal
                </div>
                <div style="font-size: 0.68rem; font-weight: 600; color: var(--outline-color); letter-spacing: 0.05em; text-transform: uppercase;">
                    Scheme Research Dashboard
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown("<span style='font-size:0.68rem; font-weight:700; color:var(--outline-color); letter-spacing:0.08em; text-transform:uppercase; padding-left:0.8rem; display:block; margin-bottom:0.6rem;'>MUTUAL FUND SCHEMES</span>", unsafe_allow_html=True)

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
                        <span style="font-weight:700;">{name_display}</span>
                        <span class="active-nav-nav">›</span>
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

        if st.button("🔄 Refresh Live NAV", key="sidebar_refresh", use_container_width=True):
            clear_nav_cache()
            st.cache_data.clear()
            st.rerun()

        st.markdown(
            """
            <div style="font-size:0.68rem; color:var(--outline-color); line-height:1.45; margin-top:0.8rem; border-top:1px solid var(--border-color); padding-top:0.8rem;">
                <b>RAG Isolation Mode</b>: Database queries are isolated strictly to this scheme's documents.
                <div style="margin-top: 6px;"></div>
                <b>Disclaimer</b>: Mutual Fund investments are subject to market risks. Read all scheme-related documents carefully. AI insights and Google News feed are for informational purposes only and do not constitute financial advice. NAV data is sourced live from public feeds (MFAPI). This platform is an independent educational tool and is not affiliated, associated, authorized, endorsed by, or in any way officially connected with Dhan (Moneylicious Securities Pvt. Ltd.) or any of its subsidiaries.
            </div>
            """,
            unsafe_allow_html=True
        )
    return selected_key

def render_floating_chatbot(selected_key: str):
    """Renders a floating RAG chatbot widget with glassmorphism styling."""
    import markdown

    if "show_float_chat" not in st.session_state:
        st.session_state["show_float_chat"] = False

    with st.container():
        st.markdown('<div class="floating-btn-anchor"></div>', unsafe_allow_html=True)
        btn_label = "✖ Close" if st.session_state["show_float_chat"] else "✦ ArthaAI Terminal"
        if st.button(btn_label, key="float_chat_toggle_btn"):
            st.session_state["show_float_chat"] = not st.session_state["show_float_chat"]
            st.rerun()

    if st.session_state["show_float_chat"]:
        scheme = FUND_DATA[selected_key]
        chat_key = f"artha_chat_{selected_key}"

        if chat_key not in st.session_state:
            st.session_state[chat_key] = [
                {
                    "role": "analyst",
                    "content": f"Analysis of **{scheme['name']}** loaded. Ask me about portfolio composition, returns, risk metrics, or expenses."
                }
            ]

        with st.container():
            st.markdown('<div class="floating-chat-anchor"></div>', unsafe_allow_html=True)

            st.markdown(
                f"""
                <div class="floating-chat-header">
                    <div style="display:flex; align-items:center; gap:8px;">
                        <span style="color:var(--primary-color); font-size:18px;">⚡</span>
                        <span style="font-weight:700; color:var(--text-highlight-color); font-size:14px;">ArthaAI Assistant</span>
                    </div>
                    <div style="font-size:10px; color:var(--outline-color); text-transform:uppercase; letter-spacing:0.05em;">
                        Grounded: {scheme['name'][:25]}...
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            chat_viewport = st.container(height=260)
            with chat_viewport:
                for chat in st.session_state[chat_key]:
                    if chat["role"] == "user":
                        st.markdown(
                            f"""<div class="float-chat-row-user"><div class="float-chat-bubble float-chat-bubble-user">{chat['content']}</div></div>""",
                            unsafe_allow_html=True
                        )
                    else:
                        html_content = markdown.markdown(chat['content'], extensions=['tables', 'nl2br'])
                        st.markdown(
                            f"""<div class="float-chat-row-analyst"><div class="float-chat-bubble float-chat-bubble-analyst">{html_content}</div></div>""",
                            unsafe_allow_html=True
                        )

            with st.form(key=f"float_chat_form_{selected_key}", clear_on_submit=True):
                col_in, col_btn = st.columns([5, 1])
                with col_in:
                    q_input = st.text_input("Ask AI Terminal...", placeholder="Ask AI Terminal...", label_visibility="collapsed", key=f"float_input_{selected_key}")
                with col_btn:
                    submitted = st.form_submit_button("➔")

            if submitted and q_input:
                st.session_state[chat_key].append({"role": "user", "content": q_input})
                with st.spinner("Analyzing..."):
                    ans, sources = query_fund_api(q_input, selected_key, st.session_state[chat_key][:-1])
                    st.session_state[chat_key].append({
                        "role": "analyst",
                        "content": ans,
                        "sources": sources
                    })
                st.rerun()
