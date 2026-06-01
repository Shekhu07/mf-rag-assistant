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

from src.ui_helpers import inject_css, render_top_navigation, render_sidebar, get_all_nav_data_cached, query_fund_api, fetch_google_news_cached
from src.fund_metadata import FUND_DATA
import src.config as config

# 1. Inject Dhan-Style CSS & render top navigation
inject_css()
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
    <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid var(--border-color); padding-bottom:0.8rem; margin-bottom:1.5rem; margin-top:0.5rem;">
        <div style="font-size:0.7rem; font-weight:700; color:var(--text-muted-color); letter-spacing:0.12em; text-transform:uppercase;">
            ARTHAAI WORKSPACE &nbsp;/&nbsp; RAG ANALYST CHAT
        </div>
        <div style="display:flex; align-items:center; gap:6px;">
            <span style="display:inline-block; width:6px; height:6px; background-color:var(--success-color); border-radius:50%; box-shadow:0 0 8px var(--success-color);"></span>
            <span style="font-size:0.65rem; font-weight:700; color:var(--success-color); letter-spacing:0.05em; text-transform:uppercase;">RAG SECURED CORE</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# Header Section
st.markdown(f'<div class="scheme-title">{scheme["name"]}</div>', unsafe_allow_html=True)
st.markdown(
    f'<span class="scheme-badge">DIRECT</span><span class="scheme-badge">GROWTH</span><span style="color:#8A99AD; font-size:0.85rem;">{scheme["category"]}</span>',
    unsafe_allow_html=True
)
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
                "content": f"Hi! I have parsed the official factsheet for **{scheme['name']}**. Ask me about portfolio composition, foreign holdings, risk metrics, or asset details. I am isolated to this fund."
            }
        ]
        
    # Render chat history with bubbles inside a scrollable container
    chat_viewport = st.container(height=500)
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

    # Quick Suggestions (only if chat has just 1 welcome message)
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
            if st.button("📊 Holdings", use_container_width=True, key=f"sug_holdings_page_{selected_key}"):
                st.session_state[chat_key].append({"role": "user", "content": "What are the top 5 holdings in this scheme?"})
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
            if st.button("📈 Returns", use_container_width=True, key=f"sug_perf_page_{selected_key}"):
                st.session_state[chat_key].append({"role": "user", "content": "Tell me about the NAV and CAGR returns."})
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
            if st.button("💼 Expenses", use_container_width=True, key=f"sug_expense_page_{selected_key}"):
                st.session_state[chat_key].append({"role": "user", "content": "What is the expense ratio and fees?"})
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
