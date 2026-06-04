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
def get_nav_data_cached(fund_id: str):
    item = FUND_DATA[fund_id]
    return get_live_nav(
        fund_id,
        item["nav"],
        item["change"],
        item["change_positive"]
    )

def prefetch_other_funds(selected_key: str):
    """Prefetch the remaining 4 funds in a background thread."""
    import threading
    from streamlit.runtime.scriptrunner import add_script_run_ctx, get_script_run_ctx

    ctx = get_script_run_ctx()

    def _prefetch():
        for key in FUND_DATA.keys():
            if key != selected_key:
                get_nav_data_cached(key)

    thread = threading.Thread(target=_prefetch)
    if ctx:
        add_script_run_ctx(thread, ctx)
    thread.start()

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
    """Renders the terminal-style top navigation bar with working page links."""
    # Initialize view state
    if "active_view" not in st.session_state:
        st.session_state["active_view"] = "overview"

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
        </div>
        """,
        unsafe_allow_html=True
    )

    # Detect current running page for navigation highlighting
    # NOTE: ctx.main_script_path always returns the entrypoint (app.py), even on sub-pages.
    # We must use page_script_hash + pages_manager.get_pages() to find the actual current page.
    from streamlit.runtime.scriptrunner import get_script_run_ctx
    ctx = get_script_run_ctx()
    current_page_script = "app.py"  # fallback
    if ctx:
        try:
            pages = ctx.pages_manager.get_pages()
            current_hash = ctx.page_script_hash
            page_info = pages.get(current_hash)
            if page_info and page_info.get("script_path"):
                current_page_script = Path(page_info["script_path"]).name
        except Exception:
            pass
    is_on_app = (current_page_script == "app.py")

    # Horizontal page navigation using Streamlit buttons
    nav_cols = st.columns([1, 1, 1, 1, 1, 2])

    # 1. Overview Page Button
    with nav_cols[0]:
        is_active_overview = is_on_app and (st.session_state.get("active_view", "overview") == "overview")
        if st.button(
            "📊 Overview",
            key="nav_overview",
            use_container_width=True,
            type="primary" if is_active_overview else "secondary",
        ):
            st.session_state["active_view"] = "overview"
            if not is_on_app:
                st.switch_page("app.py")
            else:
                st.rerun()

    # 2. AI Chatbot Button
    with nav_cols[1]:
        is_active_chatbot = is_on_app and (st.session_state.get("active_view", "overview") == "chatbot")
        if st.button(
            "🤖 AI Chatbot",
            key="nav_chatbot",
            use_container_width=True,
            type="primary" if is_active_chatbot else "secondary",
        ):
            st.session_state["active_view"] = "chatbot"
            if not is_on_app:
                st.switch_page("app.py")
            else:
                st.rerun()

    # 3. Holdings Page Button
    with nav_cols[2]:
        is_active_holdings = (current_page_script == "1_Holdings_&_Overlap.py")
        if st.button(
            "📈 Holdings",
            key="nav_holdings",
            use_container_width=True,
            type="primary" if is_active_holdings else "secondary",
        ):
            st.switch_page("pages/1_Holdings_&_Overlap.py")

    # 4. SIP Calculator Page Button
    with nav_cols[3]:
        is_active_sip = (current_page_script == "2_SIP_Calculator.py")
        if st.button(
            "💰 SIP Calc",
            key="nav_sip",
            use_container_width=True,
            type="primary" if is_active_sip else "secondary",
        ):
            st.switch_page("pages/2_SIP_Calculator.py")

    # 5. News Feed Page Button
    with nav_cols[4]:
        is_active_news = (current_page_script == "3_News_Feed.py")
        if st.button(
            "📰 News",
            key="nav_news",
            use_container_width=True,
            type="primary" if is_active_news else "secondary",
        ):
            st.switch_page("pages/3_News_Feed.py")

    # Style the top nav buttons
    st.markdown("""
    <style>
        /* Top nav buttons - horizontal pill style */
        .stApp > div > div > div > div > div > [data-testid="stHorizontalBlock"]:nth-of-type(1) button,
        .stApp > div > div > div > div > div > [data-testid="stHorizontalBlock"]:nth-of-type(2) button {
            background-color: var(--surface-container-low) !important;
            color: var(--text-muted-color) !important;
            border: 1px solid var(--border-color) !important;
            border-radius: 8px !important;
            font-size: 0.8rem !important;
            font-weight: 600 !important;
            font-family: var(--font-body) !important;
            padding: 0.45rem 0.5rem !important;
            transition: all 0.2s ease !important;
        }
        .stApp > div > div > div > div > div > [data-testid="stHorizontalBlock"]:nth-of-type(1) button:hover,
        .stApp > div > div > div > div > div > [data-testid="stHorizontalBlock"]:nth-of-type(2) button:hover {
            background-color: var(--surface-high) !important;
            color: var(--primary-color) !important;
            border-color: var(--primary-color) !important;
        }
        .stApp > div > div > div > div > div > [data-testid="stHorizontalBlock"]:nth-of-type(1) button p,
        .stApp > div > div > div > div > div > [data-testid="stHorizontalBlock"]:nth-of-type(2) button p {
            font-family: var(--font-body) !important;
            font-size: 0.8rem !important;
            font-weight: 600 !important;
            color: inherit !important;
        }
        /* Top nav active button styling override */
        .stApp > div > div > div > div > div > [data-testid="stHorizontalBlock"] button[data-testid="baseButton-primary"] {
            background-color: var(--primary-color) !important;
            color: var(--bg-color) !important;
            border-color: var(--primary-color) !important;
        }
        .stApp > div > div > div > div > div > [data-testid="stHorizontalBlock"] button[data-testid="baseButton-primary"] p {
            color: var(--bg-color) !important;
        }
    </style>
    """, unsafe_allow_html=True)


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

    # Reset active view to overview when a different scheme is selected
    if "last_selected_scheme" not in st.session_state or st.session_state["last_selected_scheme"] != selected_key:
        st.session_state["active_view"] = "overview"
        st.session_state["last_selected_scheme"] = selected_key

    return selected_key

def render_floating_chatbot(selected_key: str):
    """Renders a floating RAG chatbot widget — FAB button + inline chat panel."""
    import markdown
    import streamlit.components.v1 as components

    if "show_float_chat" not in st.session_state:
        st.session_state["show_float_chat"] = False

    # Hidden Streamlit button that toggles the chat state (clickable by JS)
    col_hide = st.columns([1])[0]
    with col_hide:
        toggled = st.button("🔄 Toggle ArthaAI Chat", key="float_chat_toggle_btn", use_container_width=True)
        if toggled:
            st.session_state["show_float_chat"] = not st.session_state["show_float_chat"]
            st.rerun()

    # Style the toggle button to be visible and attractive (not hidden)
    st.markdown("""
    <style>
        /* Style the toggle chat button as a prominent inline button */
        button[data-testid="baseButton-secondary"] p {
            font-family: var(--font-body) !important;
        }
    </style>
    """, unsafe_allow_html=True)

    # Floating Action Button via components.html (real JS + CSS positioning)
    is_open = st.session_state["show_float_chat"]
    fab_label = "✖ Close" if is_open else "✦ ArthaAI"
    fab_bg = "#ffb4ab" if is_open else "#adc6ff"
    fab_color = "#1a1a2e"

    components.html(
        f"""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@600;700&display=swap');
            body {{ margin: 0; padding: 0; overflow: hidden; background: transparent; }}
            .fab {{
                position: fixed;
                bottom: 28px;
                right: 28px;
                z-index: 999999;
                background: {fab_bg};
                color: {fab_color};
                border: none;
                border-radius: 999px;
                padding: 14px 24px;
                font-size: 13px;
                font-weight: 700;
                font-family: 'Outfit', sans-serif;
                cursor: pointer;
                box-shadow: 0 8px 32px rgba(0,0,0,0.45), 0 0 0 2px rgba(173, 198, 255, 0.1);
                transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
                letter-spacing: 0.03em;
                display: flex;
                align-items: center;
                gap: 8px;
            }}
            .fab:hover {{
                transform: scale(1.06) translateY(-2px);
                box-shadow: 0 14px 44px rgba(173, 198, 255, 0.25);
            }}
            .fab:active {{
                transform: scale(0.98);
            }}
        </style>
        <button class="fab" onclick="
            // Find and click the hidden Streamlit toggle button
            const allButtons = parent.document.querySelectorAll('button');
            for (const btn of allButtons) {{
                const text = (btn.innerText || btn.textContent || '').trim();
                if (text.includes('Toggle ArthaAI Chat')) {{
                    btn.click();
                    break;
                }}
            }}
        ">{fab_label}</button>
        """,
        height=0,
    )

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

        # --- Inline Chat Panel ---
        st.markdown("<div style='margin-top:1.5rem;'></div>", unsafe_allow_html=True)
        st.markdown(
            f"""
            <div style="background: linear-gradient(135deg, rgba(173, 198, 255, 0.06), rgba(78, 222, 163, 0.03));
                border: 1px solid rgba(173, 198, 255, 0.15); border-radius: 16px; overflow: hidden;">
                <div style="padding: 16px 20px; border-bottom: 1px solid rgba(255,255,255,0.08);
                    background: rgba(173, 198, 255, 0.08); display:flex; align-items:center; justify-content:space-between;">
                    <div style="display:flex; align-items:center; gap:10px;">
                        <span style="color:var(--primary-color); font-size:20px;">⚡</span>
                        <div>
                            <div style="font-weight:700; color:var(--text-highlight-color); font-size:15px; font-family:var(--font-body);">ArthaAI RAG Assistant</div>
                            <div style="font-size:10px; color:var(--outline-color); text-transform:uppercase; letter-spacing:0.05em; font-family:var(--font-body);">
                                Grounded: {scheme['name'][:30]}
                            </div>
                        </div>
                    </div>
                    <div style="display:flex; align-items:center; gap:6px;">
                        <span style="display:inline-block; width:6px; height:6px; background-color:var(--success-color); border-radius:50%; box-shadow:0 0 8px var(--success-color);"></span>
                        <span style="font-size:10px; font-weight:700; color:var(--success-color); letter-spacing:0.05em;">ACTIVE</span>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Chat messages viewport
        chat_viewport = st.container(height=350)
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

        # Chat input form
        with st.form(key=f"float_chat_form_{selected_key}", clear_on_submit=True):
            col_in, col_btn = st.columns([5, 1])
            with col_in:
                q_input = st.text_input("Ask AI Terminal...", placeholder="e.g. What are the top holdings?", label_visibility="collapsed", key=f"float_input_{selected_key}")
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


