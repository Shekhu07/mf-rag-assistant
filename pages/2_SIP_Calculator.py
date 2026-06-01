import streamlit as st
import pandas as pd
import altair as alt

# Set page config for wide layout
st.set_page_config(
    page_title="ArthaAI - SIP Calculator",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

from src.ui_helpers import inject_css, render_top_navigation, render_ticker_bar, render_sidebar, render_floating_chatbot
from src.fund_metadata import FUND_DATA
import src.config as config

# 1. Inject CSS, ticker bar, terminal navigation
inject_css()
render_ticker_bar()
render_top_navigation()

# 2. Render sidebar and retrieve currently active scheme selection
selected_key = render_sidebar()
scheme = FUND_DATA[selected_key]

# --- WORKSPACE STATUS BAR ---
st.markdown(
    """
    <div class="workspace-bar">
        <div class="workspace-bar-label">
            ARTHAAI WORKSPACE &nbsp;/&nbsp; SIP GROWTH CALCULATOR
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
left_panel, right_panel = st.columns([1.1, 1.0], gap="large")

with left_panel:
    st.markdown("<span style='font-size:0.85rem; font-weight:600; color:#8A99AD;'>INVESTMENT SPECIFICATIONS</span>", unsafe_allow_html=True)
    st.markdown("<div style='margin-bottom:1rem;'></div>", unsafe_allow_html=True)

    monthly_investment = st.slider(
        "Monthly Investment (₹)",
        min_value=500,
        max_value=200000,
        value=10000,
        step=500,
        format="₹%d",
        key=f"sip_amt_page_{selected_key}"
    )
    
    years = st.slider(
        "Investment Period (Years)",
        min_value=1,
        max_value=30,
        value=10,
        step=1,
        format="%d years",
        key=f"sip_years_page_{selected_key}"
    )

    cagr_option = st.radio(
        "Expected Return Rate (CAGR)",
        options=[
            f"3-Year CAGR ({scheme['return_3y']})",
            f"5-Year CAGR ({scheme['return_5y']})",
            f"1-Year CAGR ({scheme['return_1y']})",
            "Custom Return Rate"
        ],
        key=f"sip_cagr_opt_page_{selected_key}"
    )
    
    if cagr_option == "Custom Return Rate":
        annual_rate = st.slider(
            "Custom Return Rate (%)",
            min_value=1.0,
            max_value=30.0,
            value=15.0,
            step=0.5,
            format="%.1f%%",
            key=f"sip_custom_rate_page_{selected_key}"
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

with right_panel:
    st.markdown("<span style='font-size:0.85rem; font-weight:600; color:#8A99AD;'>PROJECTED CORPUS DETAILS</span>", unsafe_allow_html=True)
    
    invested_str = f"₹{total_invested:,.0f}"
    wealth_str = f"₹{wealth_gained:,.0f}"
    total_str = f"₹{future_value:,.0f}"

    st.markdown(
        f"""
        <div style="display:flex; gap:1rem; margin-top:1rem; margin-bottom:1.5rem;">
            <div style="flex:1; background:var(--card-bg-color); border:1px solid var(--border-color); border-radius:6px; padding:0.8rem 1rem; text-align:center;">
                <div style="font-size:0.65rem; color:var(--text-muted-color); font-weight:600; text-transform:uppercase; margin-bottom:2px;">Total Invested</div>
                <div style="font-size:1.1rem; font-weight:700; color:var(--text-highlight-color);">{invested_str}</div>
            </div>
            <div style="flex:1; background:var(--card-bg-color); border:1px solid var(--border-color); border-radius:6px; padding:0.8rem 1rem; text-align:center;">
                <div style="font-size:0.65rem; color:var(--text-muted-color); font-weight:600; text-transform:uppercase; margin-bottom:2px;">Est. Returns</div>
                <div style="font-size:1.1rem; font-weight:700; color:var(--success-color);">{wealth_str}</div>
            </div>
            <div style="flex:1; background:var(--card-bg-color); border:1px solid var(--border-color); border-radius:6px; padding:0.8rem 1rem; text-align:center;">
                <div style="font-size:0.65rem; color:var(--text-muted-color); font-weight:600; text-transform:uppercase; margin-bottom:2px;">Total Value</div>
                <div style="font-size:1.1rem; font-weight:700; color:var(--primary-color);">{total_str}</div>
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

    # Growth line chart (clean, static, no hover pop-ups)
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

# Render the floating chatbot
render_floating_chatbot(selected_key)
