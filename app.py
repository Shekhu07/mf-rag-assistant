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
from src.nav_service import get_live_nav, clear_nav_cache, fetch_nav_history

# --- PAGE SETUP ---
st.set_page_config(
    page_title="Dhan - Mutual Funds",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
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
    
    /* Fund Summary Card */
    .fund-summary-card {
        background: linear-gradient(135deg, #0E1217, #0A0E14);
        border: 1px solid #1C232E;
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
        border-bottom: 1px solid #151D28;
        font-size: 0.84rem;
    }
    .fund-summary-row:last-child { border-bottom: none; }
    .fund-summary-label { color: #8A99AD; font-weight: 500; }
    .fund-summary-value { color: #FFFFFF; font-weight: 600; text-align: right; }
    
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
    /* SaaS-Style Sidebar Navigation Switcher */
    [data-testid="stSidebar"] {
        background-color: #080A0C !important;
        border-right: 1px solid #1C232E !important;
    }
    
    [data-testid="stSidebar"] .stButton > button {
        background-color: transparent !important;
        color: #8A99AD !important;
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
        background-color: #121820 !important;
        color: #FFFFFF !important;
    }
    
    .active-nav-item {
        background-color: #121820;
        border-left: 3.5px solid #E2FF3B;
        color: #E2FF3B;
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
        color: #FFFFFF;
        font-weight: 600;
        margin-left: 8px;
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

# Initialize session state for selected scheme
if "selected_scheme" not in st.session_state:
    st.session_state["selected_scheme"] = "sbi_bluechip"
selected_key = st.session_state["selected_scheme"]

# --- PARALLEL NAV PRE-FETCHING ---
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

# --- SIDEBAR: SAAS NAVIGATION LIST ---
with st.sidebar:
    st.markdown("<h2 style='font-family:Outfit; color:white; font-size:1.3rem; margin-top:0.5rem; margin-bottom:1rem;'>⚡ dhan mutual funds</h2>", unsafe_allow_html=True)
    st.markdown("<span style='font-size:0.7rem; font-weight:700; color:#8A99AD; letter-spacing:0.08em; display:block; margin-bottom:0.8rem;'>SCHEMES WORKSPACE</span>", unsafe_allow_html=True)
    
    short_names = {
        "sbi_bluechip": "SBI Bluechip",
        "parag_parikh_flexi": "Parag Parikh Cap",
        "hdfc_top100": "HDFC Top 100",
        "icici_prudential": "ICICI Pru Bluechip",
        "mirae_asset": "Mirae Asset Large"
    }

    for key, item in FUND_DATA.items():
        nav_info = all_nav_data[key]
        is_active = (key == selected_key)
        name_display = short_names.get(key, item["name"])
        
        if is_active:
            # Active item rendered as highlighted box
            change_val = nav_info["change"].split(" ")[0]
            change_color = "#10B981" if nav_info["change_positive"] else "#EF4444"
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
        st.rerun()
        
    st.markdown(
        """
        <div style="font-size:0.72rem; color:#8A99AD; line-height:1.45; margin-top:0.8rem;">
        <b>RAG Security Isolation</b>: Access parameters for this session are restricted to this scheme's documents inside the database.
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
        f'<span style="background:#0D2B1A; color:#10B981; font-size:0.65rem; font-weight:700; '
        f'padding:2px 7px; border-radius:4px; border:1px solid rgba(16,185,129,0.3); '
        f'margin-left:8px; vertical-align:middle;">&#9679; LIVE · {nav_date}</span>'
    ) if is_live else (
        f'<span style="background:#1A1512; color:#F59E0B; font-size:0.65rem; font-weight:700; '
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
    tab_overview, tab_holdings, tab_sip = st.tabs(["Overview & Returns", "Holdings Portfolio", "💰 SIP Calculator"])
    
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
                    "background:#E2FF3B; color:#080A0C; font-weight:700;"
                    if is_active else
                    "background:#0E1217; color:#8A99AD; font-weight:500;"
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
            df_hist = fetch_nav_history(selected_key, period=selected_period)

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
                        labelColor="#8A99AD",
                        labelFontSize=10,
                        gridColor="#1C232E",
                        domainColor="#1C232E",
                        tickColor="#1C232E",
                    ),
                    title=None,
                ),
                y=alt.Y(
                    "nav:Q",
                    scale=alt.Scale(zero=False),
                    axis=alt.Axis(
                        labelColor="#8A99AD",
                        labelFontSize=10,
                        gridColor="#1C232E",
                        domainColor="#1C232E",
                        tickColor="#1C232E",
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
            ret_color = "#10B981" if period_ret >= 0 else "#EF4444"
            sign = "+" if period_ret >= 0 else ""
            st.markdown(
                f"""
                <div style="display:flex; gap:1rem; margin-top:-0.5rem; margin-bottom:1rem;">
                    <div style="flex:1; background:#0E1217; border:1px solid #1C232E; border-radius:6px; padding:0.6rem 0.8rem; text-align:center;">
                        <div style="font-size:0.65rem; color:#8A99AD; font-weight:600;">PERIOD RETURN</div>
                        <div style="font-size:1rem; font-weight:700; color:{ret_color};">{sign}{period_ret:.1f}%</div>
                    </div>
                    <div style="flex:1; background:#0E1217; border:1px solid #1C232E; border-radius:6px; padding:0.6rem 0.8rem; text-align:center;">
                        <div style="font-size:0.65rem; color:#8A99AD; font-weight:600;">{selected_period} HIGH</div>
                        <div style="font-size:1rem; font-weight:700; color:#FFFFFF">₹{period_high:,.2f}</div>
                    </div>
                    <div style="flex:1; background:#0E1217; border:1px solid #1C232E; border-radius:6px; padding:0.6rem 0.8rem; text-align:center;">
                        <div style="font-size:0.65rem; color:#8A99AD; font-weight:600;">{selected_period} LOW</div>
                        <div style="font-size:1rem; font-weight:700; color:#FFFFFF">₹{period_low:,.2f}</div>
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
                <div style="flex:1; background:#0E1217; border:1px solid #1C232E; border-radius:6px; padding:0.8rem 1rem; text-align:center;">
                    <div style="font-size:0.65rem; color:#8A99AD; font-weight:600; text-transform:uppercase; margin-bottom:2px;">Total Invested</div>
                    <div style="font-size:1.15rem; font-weight:700; color:#FFFFFF;">{invested_str}</div>
                </div>
                <div style="flex:1; background:#0E1217; border:1px solid #1C232E; border-radius:6px; padding:0.8rem 1rem; text-align:center;">
                    <div style="font-size:0.65rem; color:#8A99AD; font-weight:600; text-transform:uppercase; margin-bottom:2px;">Est. Returns</div>
                    <div style="font-size:1.15rem; font-weight:700; color:#10B981;">{wealth_str}</div>
                </div>
                <div style="flex:1; background:#0E1217; border:1px solid #1C232E; border-radius:6px; padding:0.8rem 1rem; text-align:center;">
                    <div style="font-size:0.65rem; color:#8A99AD; font-weight:600; text-transform:uppercase; margin-bottom:2px;">Total Value</div>
                    <div style="font-size:1.15rem; font-weight:700; color:#E2FF3B;">{total_str}</div>
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
            x=alt.X("Year:Q", scale=alt.Scale(domain=[1, years]), axis=alt.Axis(tickCount=int(years), format="d", labelColor="#8A99AD", gridColor="#1C232E", domainColor="#1C232E", title="Years")),
            y=alt.Y("Amount:Q", axis=alt.Axis(format="~s", labelColor="#8A99AD", gridColor="#1C232E", domainColor="#1C232E", title="Amount (₹)")),
            color=alt.Color("Type:N", scale=alt.Scale(domain=["Invested Amount", "Future Value"], range=["#4F5E71", "#E2FF3B"]), legend=alt.Legend(title=None, orient="bottom", labelColor="#BAC7D5", labelFontSize=11)),
        ).properties(
            height=200
        ).configure(
            background="transparent"
        ).configure_view(
            strokeWidth=0
        )

        st.altair_chart(growth_chart, use_container_width=True)


# ==================== RIGHT COLUMN: FUND SUMMARY + AI CHAT ====================
with right_col:
    # 1. Fund Summary Card (replaces non-functional SIP card)
    change_indicator = f'<span style="color:{"#10B981" if display_change_positive else "#EF4444"}">{display_change}</span>'
    risk_color = "#EF4444" if "Very High" in scheme["riskometer"] else "#F59E0B" if "High" in scheme["riskometer"] else "#10B981"
    st.markdown(
        f"""
        <div class="fund-summary-card">
            <div style="font-size:0.7rem; font-weight:700; color:#8A99AD; letter-spacing:0.08em; margin-bottom:0.8rem;">FUND SNAPSHOT</div>
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
                <span class="fund-summary-value" style="color:#E2FF3B;">{scheme['expense_ratio']}</span>
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
