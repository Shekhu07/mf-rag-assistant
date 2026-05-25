import streamlit as st
import markdown
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup paths and imports
sys.path.append(str(Path(__file__).resolve().parent))
from src.query_engine import query_fund
import src.config as config

# Import mutual fund scheme details
from src.fund_metadata import FUND_DATA

# --- PAGE SETUP ---
st.set_page_config(
    page_title="Dhan - Mutual Funds",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- HIGH FIDELITY DHAN WEB STYLE CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');
    
    /* Global Overrides */
    .stApp {
        background-color: #080A0C !important;
        color: #BAC7D5 !important;
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    /* Top Navigation bar */
    .dhan-nav {
        background-color: #0E1217;
        padding: 0.8rem 2rem;
        border-bottom: 1px solid #1C232E;
        display: flex;
        align-items: center;
        margin: -6rem -5rem 2rem -5rem;
    }
    
    .dhan-logo {
        color: #E2FF3B;
        font-family: 'Outfit', sans-serif;
        font-weight: 800;
        font-size: 1.6rem;
        margin-right: 2rem;
        letter-spacing: -0.5px;
    }
    
    /* Typography */
    .scheme-title {
        font-family: 'Outfit', sans-serif;
        font-weight: 700;
        font-size: 1.8rem;
        color: #FFFFFF;
        margin-bottom: 0.2rem;
    }
    
    .scheme-badge {
        background-color: #17211B;
        color: #10B981;
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
        color: #8A99AD;
        margin-bottom: 1.5rem;
    }
    
    /* NAV Section */
    .nav-box {
        margin-bottom: 2rem;
    }
    
    .nav-label {
        font-size: 0.85rem;
        color: #8A99AD;
        font-weight: 500;
        margin-bottom: 0.1rem;
    }
    
    .nav-val {
        font-size: 2.2rem;
        color: #FFFFFF;
        font-weight: 800;
        font-family: 'Outfit', sans-serif;
        display: inline-block;
        margin-right: 0.8rem;
    }
    
    .nav-change-pos {
        color: #10B981;
        font-weight: 700;
        font-size: 1rem;
        display: inline-block;
    }

    .nav-change-neg {
        color: #EF4444;
        font-weight: 700;
        font-size: 1rem;
        display: inline-block;
    }
    
    /* Cards and Containers */
    .dhan-box {
        background-color: #0E1217;
        border: 1px solid #1C232E;
        border-radius: 8px;
        padding: 1.2rem;
        margin-bottom: 1.5rem;
    }
    
    .dhan-box-header {
        font-family: 'Outfit', sans-serif;
        font-weight: 600;
        color: #FFFFFF;
        font-size: 1.05rem;
        margin-bottom: 1rem;
        border-bottom: 1px solid #1C232E;
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
        color: #8A99AD;
    }
    
    .metric-value {
        color: #FFFFFF;
        font-weight: 600;
    }

    /* Returns Dashboard Card */
    .return-card {
        text-align: center;
        padding: 0.8rem;
        background-color: #131A22;
        border: 1px solid #1C2635;
        border-radius: 6px;
    }
    
    .return-num {
        color: #10B981;
        font-size: 1.4rem;
        font-weight: 700;
        font-family: 'Outfit', sans-serif;
    }
    
    /* Holdings Table */
    .holdings-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.85rem;
    }
    .holdings-table th {
        text-align: left;
        color: #8A99AD;
        font-weight: 600;
        border-bottom: 1px solid #1C232E;
        padding: 8px 4px;
        text-transform: uppercase;
        font-size: 0.72rem;
    }
    .holdings-table td {
        padding: 10px 4px;
        border-bottom: 1px dashed #1C232E;
        color: #E2E8F0;
    }
    
    /* Riskometer Card */
    .riskometer-box {
        border-left: 4px solid #EF4444;
        background-color: #1A1215;
        border-radius: 6px;
        padding: 0.8rem;
        font-size: 0.85rem;
        color: #F87171;
    }
    
    /* Order Transaction Box (Right Sidebar Style) */
    .order-box {
        background-color: #0E1217;
        border: 1px solid #1C232E;
        border-radius: 8px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    }
    
    .btn-dhan-green {
        background-color: #E2FF3B !important;
        color: #080A0C !important;
        font-weight: 700 !important;
        font-family: 'Outfit', sans-serif !important;
        border-radius: 6px !important;
        border: none !important;
        width: 100%;
        padding: 10px !important;
        font-size: 1rem !important;
        text-align: center;
        cursor: pointer;
        display: block;
        margin-top: 1rem;
        transition: opacity 0.2s;
    }
    .btn-dhan-green:hover {
        opacity: 0.9;
    }
    
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
        max-width: 82%;
        padding: 0.8rem 1rem;
        font-size: 0.88rem;
        line-height: 1.5;
        position: relative;
    }
    
    .chat-bubble-new-user {
        background: linear-gradient(135deg, #1C2431, #131A24);
        border: 1px solid #2B3A4F;
        color: #EBF1F7;
        border-radius: 16px 16px 4px 16px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    }
    
    .chat-bubble-new-analyst {
        background: linear-gradient(135deg, #0F131C, #090B10);
        border: 1px solid #1C2433;
        color: #C5D2E0;
        border-radius: 16px 16px 16px 4px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
        border-left: 3px solid #E2FF3B;
    }
    
    .chat-avatar-user {
        width: 32px;
        height: 32px;
        background: linear-gradient(135deg, #2B3A4F, #1C2431);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.95rem;
        margin-left: 10px;
        border: 1px solid #3E516D;
        box-shadow: 0 2px 5px rgba(0,0,0,0.3);
    }
    
    .chat-avatar-analyst {
        width: 32px;
        height: 32px;
        background: linear-gradient(135deg, #1A221E, #0E1311);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.95rem;
        margin-right: 10px;
        color: #10B981;
        border: 1px solid rgba(16, 185, 129, 0.3);
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
        background-color: #0E1217;
        border: 1px solid #1C232E;
        border-radius: 20px;
        padding: 4px 10px;
        font-size: 0.7rem;
        color: #8A99AD;
        font-weight: 600;
        transition: all 0.2s;
    }
    
    .chat-source-chip:hover {
        background-color: #161D26;
        border-color: #E2FF3B;
        color: #FFFFFF;
    }
    
    .chat-source-item {
        font-size: 0.76rem;
        background-color: #080A0C;
        border: 1px solid #1C232E;
        border-radius: 6px;
        padding: 8px 12px;
        margin-top: 5px;
    }
    
    /* Chat bubble markdown tables */
    .chat-bubble-new-analyst table {
        width: 100%;
        border-collapse: collapse;
        margin: 0.6rem 0 0.4rem 0;
        font-size: 0.82rem;
    }
    .chat-bubble-new-analyst th {
        background-color: #131A22;
        color: #E2FF3B;
        text-align: left;
        padding: 7px 10px;
        font-weight: 700;
        font-size: 0.72rem;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        border-bottom: 2px solid #2B3A4F;
    }
    .chat-bubble-new-analyst td {
        padding: 7px 10px;
        border-bottom: 1px solid #1C2433;
        color: #C5D2E0;
    }
    .chat-bubble-new-analyst tr:last-child td {
        border-bottom: none;
    }
    .chat-bubble-new-analyst tr:nth-child(even) td {
        background-color: rgba(30, 40, 55, 0.4);
    }
    .chat-bubble-new-analyst strong {
        color: #E2FF3B;
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
        color: #8A99AD;
        font-weight: 600;
        font-size: 0.9rem;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: #FFFFFF;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        color: #E2FF3B;
        border-bottom: 2px solid #E2FF3B;
    }
</style>
""", unsafe_allow_html=True)

# --- TOP NAVIGATION BAR ---
st.markdown(
    """
    <div class="dhan-nav">
        <div class="dhan-logo">⚡ dhan</div>
        <div style="color:#FFFFFF; font-size:0.9rem; font-weight:600; margin-right:1.5rem;">Markets</div>
        <div style="color:#E2FF3B; font-size:0.9rem; font-weight:600; margin-right:1.5rem; border-bottom: 2px solid #E2FF3B; padding-bottom:12px; margin-bottom:-12px;">Mutual Funds</div>
        <div style="color:#8A99AD; font-size:0.9rem; font-weight:500; margin-right:1.5rem;">Portfolio</div>
        <div style="color:#8A99AD; font-size:0.9rem; font-weight:500; margin-right:1.5rem;">Orders</div>
    </div>
    """,
    unsafe_allow_html=True
)

# --- SIDEBAR FOR SCHEME SWITCHER ---
with st.sidebar:
    st.markdown("<h3 style='font-family:Outfit; color:white; font-size:1.15rem; margin-bottom:1rem;'>⚡ Schemes Switcher</h3>", unsafe_allow_html=True)
    fund_keys = list(FUND_DATA.keys())
    selected_key = st.selectbox(
        "Choose Mutual Fund Scheme:",
        options=fund_keys,
        format_func=lambda k: FUND_DATA[k]["name"],
        label_visibility="visible"
    )
    st.divider()
    st.markdown(
        """
        <div style="font-size:0.75rem; color:#8A99AD; line-height:1.4;">
        <b>RAG Security Isolation</b>: Access parameters for this session are restricted to this scheme's documents inside the database.
        </div>
        """,
        unsafe_allow_html=True
    )

# Get selected scheme facts
scheme = FUND_DATA[selected_key]

# --- DASHBOARD HEADER ---
st.markdown(
    """
    <div style="margin-bottom: 2rem; margin-top: 1rem;">
        <h1 style="font-family: 'Outfit', sans-serif; font-weight: 800; color: #FFFFFF; font-size: 2.2rem; margin-bottom: 0.2rem; letter-spacing: -0.5px; line-height: 1.2;">
            ⚡ Dhan
        </h1>
        <p style="font-size: 0.95rem; color: #8A99AD; margin: 0;">
            Real-time layout-aware RAG analysis & portfolio insights powered by Gemini 2.5 Flash
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

# --- TWO-COLUMN LAYOUT ---
left_col, right_col = st.columns([1.6, 1.0], gap="large")

# ==================== LEFT COLUMN: SCHEME ANALYSIS ====================
with left_col:
    # 1. Scheme Header
    st.markdown(f'<div class="scheme-title">{scheme["name"]}</div>', unsafe_allow_html=True)
    st.markdown(
        f'<span class="scheme-badge">DIRECT</span><span class="scheme-badge">GROWTH</span><span style="color:#8A99AD; font-size:0.85rem;">{scheme["category"]}</span>',
        unsafe_allow_html=True
    )
    st.markdown("<div style='margin-bottom:1.5rem;'></div>", unsafe_allow_html=True)
    
    # 2. NAV & Daily Change
    change_class = "nav-change-pos" if scheme["change_positive"] else "nav-change-neg"
    st.markdown(
        f"""
        <div class="nav-box">
            <div class="nav-label">NET ASSET VALUE (NAV)</div>
            <div class="nav-val">{scheme["nav"]}</div>
            <div class="{change_class}">{scheme["change"]}</div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # 3. Dhan Scheme Tabs
    tab_overview, tab_holdings, tab_parameters = st.tabs(["Overview & Returns", "Holdings Portfolio", "Scheme Information"])
    
    with tab_overview:
        st.markdown("<div style='margin-bottom:1rem;'></div>", unsafe_allow_html=True)
        # Returns grid
        st.markdown("<span style='font-size:0.8rem; font-weight:600; color:#8A99AD;'>HISTORICAL PERFORMANCE (CAGR)</span>", unsafe_allow_html=True)
        r_col1, r_col2, r_col3 = st.columns(3)
        with r_col1:
            st.markdown(f'<div class="return-card"><div class="nav-label">1Y RETURN</div><div class="return-num">{scheme["return_1y"]}</div></div>', unsafe_allow_html=True)
        with r_col2:
            st.markdown(f'<div class="return-card"><div class="nav-label">3Y RETURN</div><div class="return-num">{scheme["return_3y"]}</div></div>', unsafe_allow_html=True)
        with r_col3:
            st.markdown(f'<div class="return-card"><div class="nav-label">5Y RETURN</div><div class="return-num">{scheme["return_5y"]}</div></div>', unsafe_allow_html=True)
        
        st.markdown("<div style='margin-bottom:1.5rem;'></div>", unsafe_allow_html=True)
        
        # Investment Objective & Riskometer
        st.markdown("<span style='font-size:0.8rem; font-weight:600; color:#8A99AD;'>RISK PROFILE & SUMMARY</span>", unsafe_allow_html=True)
        risk_col1, risk_col2 = st.columns([1.5, 1.0])
        with risk_col1:
            st.markdown(
                f"""
                <div style="font-size:0.88rem; color:#BAC7D5; line-height:1.5; padding: 0.5rem 0;">
                <b>Description:</b> {scheme['desc']}
                </div>
                """,
                unsafe_allow_html=True
            )
        with risk_col2:
            st.markdown(
                f"""
                <div class="riskometer-box">
                    <div style="font-size:0.75rem; font-weight:600; text-transform:uppercase; margin-bottom:2px;">Riskometer</div>
                    <div style="font-size:1.05rem; font-weight:700;">● {scheme['riskometer']}</div>
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
            chart = alt.Chart(df).mark_arc(innerRadius=65, outerRadius=110, stroke="#080A0C", strokeWidth=2).encode(
                theta=alt.Theta(field="AllocNum", type="quantitative"),
                color=alt.Color(
                    field="Company", 
                    type="nominal", 
                    scale=alt.Scale(range=["#E2FF3B", "#10B981", "#3B82F6", "#F59E0B", "#EC4899"]),
                    legend=alt.Legend(
                        title=None,
                        orient="right",
                        labelColor="#BAC7D5",
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

    with tab_parameters:
        st.markdown("<div style='margin-bottom:1rem;'></div>", unsafe_allow_html=True)
        st.markdown("<span style='font-size:0.8rem; font-weight:600; color:#8A99AD;'>FUND SPECS</span>", unsafe_allow_html=True)
        
        # Grid of key facts
        st.markdown(
            f"""
            <div class="dhan-box">
                <div class="metric-row"><span class="metric-label">Fund Manager</span><span class="metric-value">{scheme['manager']}</span></div>
                <div class="metric-row"><span class="metric-label">Total Assets Under Management (AUM)</span><span class="metric-value">{scheme['aum']}</span></div>
                <div class="metric-row"><span class="metric-label">Expense Ratio (Direct Plan)</span><span class="metric-value" style="color:#E2FF3B;">{scheme['expense_ratio']}</span></div>
                <div class="metric-row"><span class="metric-label">Minimum SIP Amount</span><span class="metric-value">{scheme['min_sip']}</span></div>
                <div class="metric-row"><span class="metric-label">Lock-in Period</span><span class="metric-value">Nil</span></div>
            </div>
            """,
            unsafe_allow_html=True
        )


# ==================== RIGHT COLUMN: BUY CARD & AI CHAT ====================
with right_col:
    # 1. Transaction Order Card (Dhan Panel Style)
    st.markdown(
        f"""
        <div class="order-box">
            <div style="display:flex; justify-content:space-between; margin-bottom:1.2rem; border-bottom:1px solid #1C232E; padding-bottom:0.5rem;">
                <span style="color:#FFFFFF; font-weight:700; font-size:1.1rem; font-family:Outfit;">Invest in Scheme</span>
                <span style="color:#10B981; font-weight:600; font-size:0.82rem; background-color:#14221A; padding:2px 8px; border-radius:4px;">Direct Plan</span>
            </div>
            <div style="font-size:0.82rem; color:#8A99AD; margin-bottom:0.5rem;">INVESTMENT TYPE</div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # We use Streamlit tabs inside the card to toggle between SIP and Lumpsum
    order_tabs = st.tabs(["SIP (Monthly)", "Lumpsum (One-time)"])
    with order_tabs[0]:
        st.number_input("Monthly SIP Amount", min_value=100, value=5000, step=500, key="sip_amount")
        st.selectbox("SIP Date (Monthly)", options=[1, 5, 10, 15, 25], index=1)
        st.markdown(f"<div style='font-size:0.75rem; color:#8A99AD;'>Minimum SIP amount for this scheme: {scheme['min_sip']}</div>", unsafe_allow_html=True)
    with order_tabs[1]:
        st.number_input("One-time Lumpsum Amount", min_value=500, value=10000, step=1000, key="lump_amount")
        st.markdown("<div style='font-size:0.75rem; color:#8A99AD;'>Typically processed within 1 working day.</div>", unsafe_allow_html=True)
        
    st.markdown(
        """
        <button class="btn-dhan-green" onclick="alert('SIP transaction initiated!')">⚡ Start SIP</button>
        """,
        unsafe_allow_html=True
    )
    
    st.markdown("<div style='margin-bottom:2rem;'></div>", unsafe_allow_html=True)

    # 2. Dhan RAG Chat Analyst
    col_header, col_clear = st.columns([2.2, 1.0])
    with col_header:
        st.markdown("<h3 style='font-family:Outfit; color:#E2FF3B; font-weight:700; font-size:1.35rem; margin:0;'>⚡ Dhan AI Analyst</h3>", unsafe_allow_html=True)
    with col_clear:
        if st.button("🗑️ Clear Chat", use_container_width=True, key=f"clear_{selected_key}"):
            chat_key = f"dhan_chat_{selected_key}"
            if chat_key in st.session_state:
                del st.session_state[chat_key]
            st.rerun()

    st.markdown(
        f"<div style='font-size:0.88rem; color:#8A99AD; margin-bottom:1rem;'>Ask questions about <b>{scheme['name']}</b>:</div>",
        unsafe_allow_html=True
    )
    
    # Session state Chat History for this fund
    chat_key = f"dhan_chat_{selected_key}"
    if chat_key not in st.session_state:
        st.session_state[chat_key] = [
            {
                "role": "analyst",
                "content": f"Hi! I have parsed the official factsheet for **{scheme['name']}**. Ask me about portfolio composition, foreign holdings, risk metrics, or asset details. I am isolated to this fund."
            }
        ]
        
    # Render chat history with Dhan bubbles
    for chat in st.session_state[chat_key]:
        if chat["role"] == "user":
            st.markdown(
                f"""
                <div class="chat-row-user">
                    <div class="chat-bubble-new chat-bubble-new-user">
                        <div style="font-size:0.7rem; color:#8A99AD; font-weight:600; margin-bottom:4px;">YOU</div>
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
                        <div style="font-size:0.7rem; color:#E2FF3B; font-weight:700; margin-bottom:4px; font-family:Outfit;">⚡ DHAN RAG ANALYST</div>
                        <div>{html_content}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
            # Render sources inside collapsible expander (hidden by default)
            if "sources" in chat and chat["sources"]:
                with st.expander("🔍 View Reference Passages", expanded=False):
                    for idx, (src_name, score, snippet) in enumerate(chat["sources"]):
                        st.markdown(
                            f"""
                            <div class="chat-source-item" style="margin-top: 5px;">
                                <span style="color:#10B981; font-weight:700; font-size:0.75rem;">SRC {idx+1}: {src_name}</span> &nbsp;|&nbsp; 
                                <span style="color:#8A99AD; font-size:0.7rem;">Distance: {score:.3f}</span>
                                <div style="color:#BAC7D5; font-size:0.8rem; font-style:italic; margin-top:2px;">"{snippet}..."</div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

    # Quick Suggestions (only if the chat has just 1 welcome message)
    if len(st.session_state[chat_key]) == 1:
        st.markdown("<div style='margin-bottom: 0.8rem;'></div>", unsafe_allow_html=True)
        col_s1, col_s2, col_s3 = st.columns(3)
        with col_s1:
            if st.button("📊 Top Holdings", use_container_width=True, key=f"sug_holdings_{selected_key}"):
                st.session_state[chat_key].append({"role": "user", "content": "What are the top 5 holdings in this scheme?"})
                # Serve instantly from local metadata — no API call needed
                rows = "\n".join(
                    [f"| {i+1} | {company} | {sector} | **{alloc}** |" for i, (company, sector, alloc) in enumerate(scheme["holdings"])]
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
            if st.button("📈 Returns Info", use_container_width=True, key=f"sug_perf_{selected_key}"):
                st.session_state[chat_key].append({"role": "user", "content": "Tell me about the CAGR returns."})
                # Serve instantly from local metadata — no API call needed
                ans = (
                    f"Here is the historical CAGR performance for **{scheme['name']}**:\n\n"
                    f"| Period | CAGR Return |\n"
                    f"|--------|------------|\n"
                    f"| 1 Year | **{scheme['return_1y']}** |\n"
                    f"| 3 Years | **{scheme['return_3y']}** |\n"
                    f"| 5 Years | **{scheme['return_5y']}** |\n\n"
                    f"*Risk Profile: {scheme['riskometer']}*"
                )
                st.session_state[chat_key].append({"role": "analyst", "content": ans, "sources": []})
                st.rerun()
        with col_s3:
            if st.button("💼 Expense Specs", use_container_width=True, key=f"sug_expense_{selected_key}"):
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
        
        # Run QA
        with st.spinner("Analyzing context..."):
            ans, docs = query_fund(q_input, selected_key, st.session_state[chat_key][:-1])
            
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
