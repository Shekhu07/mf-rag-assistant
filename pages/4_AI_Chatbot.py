import streamlit as st
import os
import markdown

# Set page config for wide layout
st.set_page_config(
    page_title="ArthaAI - AI Chatbot",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

from src.ui_helpers import inject_css, render_top_navigation, render_ticker_bar, render_sidebar, get_all_nav_data_cached, query_fund_api, fetch_google_news_cached
from src.fund_metadata import FUND_DATA
import src.config as config

# 1. Inject CSS, ticker bar, terminal navigation
inject_css()
render_ticker_bar()
render_top_navigation()

# 2. Render sidebar and retrieve currently active scheme selection
selected_key = render_sidebar()
scheme = FUND_DATA[selected_key]

# Pre-fetch NAV metrics for snapshot card
all_nav_data = get_all_nav_data_cached()
live_nav_data = all_nav_data[selected_key]
display_nav = live_nav_data["nav"]
display_change = live_nav_data["change"]
display_change_positive = live_nav_data["change_positive"]
nav_date = live_nav_data["date"]
is_live = live_nav_data["is_live"]

# --- WORKSPACE STATUS BAR ---
st.markdown(
    """
    <div class="workspace-bar">
        <div class="workspace-bar-label">
            ARTHAAI WORKSPACE &nbsp;/&nbsp; RAG ANALYST CHAT
        </div>
        <div class="workspace-bar-status">
            <span class="status-dot"></span>
            <span class="status-label">RAG SECURED CORE</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# Header Section
st.markdown(f'<span class="scheme-category-badge">{scheme["category"]}</span><span class="scheme-type-label">Direct Growth</span>', unsafe_allow_html=True)
st.markdown(f'<div class="scheme-title">{scheme["name"]}</div>', unsafe_allow_html=True)
st.markdown("<div style='margin-bottom:1.5rem;'></div>", unsafe_allow_html=True)

# Grid Layout
left_panel, right_panel = st.columns([1.0, 1.65], gap="large")

with left_panel:
    # 1. Fund Summary Snapshot Card
    change_indicator = f'<span style="color:{config.STITCH_DESIGN["success_color"] if display_change_positive else config.STITCH_DESIGN["danger_color"]}">{display_change}</span>'
    risk_color = config.STITCH_DESIGN["danger_color"] if "Very High" in scheme["riskometer"] else config.STITCH_DESIGN.get("warning_color", "#F59E0B") if "High" in scheme["riskometer"] else config.STITCH_DESIGN["success_color"]
    
    st.markdown(
        f"""
        <div class="fund-summary-card">
            <div style="font-size:0.7rem; font-weight:700; color:var(--text-muted-color); letter-spacing:0.08em; margin-bottom:0.8rem;">ACTIVE FUND SNAPSHOT</div>
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

    # PDF Factsheet Downloader
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
            key=f"dl_pdf_page_{selected_key}"
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

with right_panel:
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
        if st.button("🗑️ Clear Chat", use_container_width=True, key=f"clear_page_{selected_key}"):
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
                "content": f"Welcome to ArthaAI RAG Assistant! Ask me factual questions about this fund (e.g. expense ratios, exit loads, SIP minimums, riskometer, benchmark, lock-in). Facts-only. No investment advice."
            }
        ]
        
    # Render chat history with bubbles inside a scrollable container
    chat_viewport = st.container(height=380 if len(st.session_state[chat_key]) == 1 else 500)
    with chat_viewport:
        if len(st.session_state[chat_key]) == 1:
            st.markdown(
                f"""
                <div style="padding: 10px; font-family: var(--font-body);">
                    <div style="font-size: 0.95rem; font-weight: 500; color: var(--text-highlight-color); margin-bottom: 8px;">
                        Welcome to ArthaAI RAG Assistant! Ask me factual questions about this fund (e.g., expense ratios, exit loads, SIP minimums, lock-in, riskometer/benchmark, capital-gains statements).
                    </div>
                    <div style="font-size: 0.8rem; font-weight: 700; color: var(--danger-color); margin-bottom: 12px; letter-spacing: 0.02em;">
                        ⚠️ Facts-only. No investment advice.
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            st.markdown("<span style='font-size: 0.72rem; font-weight: 700; color: var(--outline-color); margin-left: 10px; display: inline-block; margin-bottom: 8px;'>EXAMPLE QUESTIONS:</span>", unsafe_allow_html=True)
            col_s1, col_s2, col_s3 = st.columns(3)
            sug_query = None
            with col_s1:
                if st.button("What is the expense ratio?", key=f"sug_exp_p_{selected_key}", use_container_width=True):
                    sug_query = "What is the expense ratio of this fund?"
            with col_s2:
                if st.button("What is the exit load?", key=f"sug_exit_p_{selected_key}", use_container_width=True):
                    sug_query = "What are the exit load details?"
            with col_s3:
                if st.button("What is the lock-in period?", key=f"sug_lock_p_{selected_key}", use_container_width=True):
                    sug_query = "What is the lock-in period of this fund?"
                    
            if sug_query:
                st.session_state[chat_key].append({"role": "user", "content": sug_query})
                with st.spinner("⚡ Analyzing with RAG..."):
                    ans, sources = query_fund_api(sug_query, selected_key, st.session_state[chat_key][:-1])
                    st.session_state[chat_key].append({
                        "role": "analyst",
                        "content": ans,
                        "sources": sources
                    })
                st.rerun()
        else:
            for chat in st.session_state[chat_key][1:]:
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
                    if "sources" in chat and chat["sources"]:
                        with st.expander("🔍 View Reference Passages", expanded=False):
                            for idx, (src_name, score, snippet) in enumerate(chat["sources"]):
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

    # Chat Input
    if q_input := st.chat_input(f"Query {selected_key.replace('_', ' ').upper()} factsheet..."):
        st.session_state[chat_key].append({"role": "user", "content": q_input})
        
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
            
            with st.spinner("Analyzing context..."):
                extra_ctx = None
                news_keywords = ["news", "recent", "buy", "sell", "holding changes", "article", "headline", "bought", "sold", "active", "transaction", "latest news"]
                is_news_query = any(k in q_input.lower() for k in news_keywords)
                
                if is_news_query:
                    news_report_key = f"news_report_{selected_key}"
                    if news_report_key in st.session_state:
                        extra_ctx = st.session_state[news_report_key]
                    else:
                        try:
                            articles = fetch_google_news_cached(selected_key)
                            if articles:
                                headlines_text = "\n".join([f"- {a['title']} (Source: {a['source']})" for a in articles[:5]])
                                analysis_report = f"Recent News Headlines for {scheme['name']}:\n{headlines_text}"
                                st.session_state[news_report_key] = analysis_report
                                extra_ctx = analysis_report
                        except Exception as e:
                            import logging
                            logging.getLogger(__name__).warning(f"Failed to fetch news context for chat: {e}")
    
                ans, sources_list = query_fund_api(q_input, selected_key, st.session_state[chat_key][:-1], extra_context=extra_ctx)
                
                st.session_state[chat_key].append({
                    "role": "analyst",
                    "content": ans,
                    "sources": sources_list
                })
                st.rerun()

    st.markdown(
        """
        <div style="text-align: center; font-size: 0.72rem; color: var(--outline-color); font-weight: 600; margin-top: 8px;">
            Facts-only. No investment advice.
        </div>
        """,
        unsafe_allow_html=True
    )
