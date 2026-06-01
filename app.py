import streamlit as st
import pandas as pd
import altair as alt

# Set page config for wide layout
st.set_page_config(
    page_title="ArthaAI - Scheme Overview",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

from src.ui_helpers import inject_css, render_top_navigation, render_sidebar, get_all_nav_data_cached, fetch_nav_history_cached
from src.fund_metadata import FUND_DATA
import src.config as config

# 1. Inject Dhan-Style CSS & render top navigation
inject_css()
render_top_navigation()

# 2. Render sidebar and retrieve currently active scheme selection
selected_key = render_sidebar()
scheme = FUND_DATA[selected_key]

# --- WORKSPACE STATUS BAR ---
st.markdown(
    """
    <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid var(--border-color); padding-bottom:0.8rem; margin-bottom:1.5rem; margin-top:0.5rem;">
        <div style="font-size:0.7rem; font-weight:700; color:var(--text-muted-color); letter-spacing:0.12em; text-transform:uppercase;">
            ARTHAAI WORKSPACE &nbsp;/&nbsp; SCHEME RESEARCH & OVERVIEW
        </div>
        <div style="display:flex; align-items:center; gap:6px;">
            <span style="display:inline-block; width:6px; height:6px; background-color:var(--success-color); border-radius:50%; box-shadow:0 0 8px var(--success-color);"></span>
            <span style="font-size:0.65rem; font-weight:700; color:var(--success-color); letter-spacing:0.05em; text-transform:uppercase;">RAG SECURED CORE</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# Fetch NAV metrics pool
all_nav_data = get_all_nav_data_cached()
live_nav_data = all_nav_data[selected_key]
display_nav = live_nav_data["nav"]
display_change = live_nav_data["change"]
display_change_positive = live_nav_data["change_positive"]
nav_date = live_nav_data["date"]
is_live = live_nav_data["is_live"]

# Scheme details block
st.markdown(f'<div class="scheme-title">{scheme["name"]}</div>', unsafe_allow_html=True)
st.markdown(
    f'<span class="scheme-badge">DIRECT</span><span class="scheme-badge">GROWTH</span><span style="color:#8A99AD; font-size:0.85rem;">{scheme["category"]}</span>',
    unsafe_allow_html=True
)
st.markdown("<div style='margin-bottom:1.5rem;'></div>", unsafe_allow_html=True)

# NAV box layout
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

st.divider()

# CAGR Return Cards
st.markdown("<span style='font-size:0.8rem; font-weight:600; color:#8A99AD;'>HISTORICAL PERFORMANCE Snapshot (CAGR)</span>", unsafe_allow_html=True)
st.markdown("<div style='margin-bottom:0.5rem;'></div>", unsafe_allow_html=True)
r_col1, r_col2, r_col3 = st.columns(3)
with r_col1:
    st.markdown(f'<div class="return-card"><div class="nav-label">1Y RETURN</div><div class="return-num">{scheme["return_1y"]}</div></div>', unsafe_allow_html=True)
with r_col2:
    st.markdown(f'<div class="return-card"><div class="nav-label">3Y RETURN</div><div class="return-num">{scheme["return_3y"]}</div></div>', unsafe_allow_html=True)
with r_col3:
    st.markdown(f'<div class="return-card"><div class="nav-label">5Y RETURN</div><div class="return-num">{scheme["return_5y"]}</div></div>', unsafe_allow_html=True)

st.markdown("<div style='margin-bottom:1.5rem;'></div>", unsafe_allow_html=True)

# Period selector
period_key = f"nav_period_{selected_key}"
if period_key not in st.session_state:
    st.session_state[period_key] = "1Y"

st.markdown("<span style='font-size:0.8rem; font-weight:600; color:#8A99AD;'>NAV PRICE HISTORY (LIVE · MFAPI)</span>", unsafe_allow_html=True)
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

# Fetch & Render Chart
selected_period = st.session_state[period_key]
with st.spinner(f"Loading {selected_period} NAV history..."):
    df_hist = fetch_nav_history_cached(selected_key, period=selected_period)

if df_hist is not None and len(df_hist) > 1:
    start_nav = df_hist["nav"].iloc[0]
    df_hist["pct_change"] = ((df_hist["nav"] - start_nav) / start_nav * 100).round(2)
    df_hist["date_str"] = df_hist["date"].dt.strftime("%d %b %Y")
    is_positive = df_hist["nav"].iloc[-1] >= df_hist["nav"].iloc[0]
    line_color = "#10B981" if is_positive else "#EF4444"
    area_color_start = "rgba(16,185,129,0.25)" if is_positive else "rgba(239,68,68,0.25)"

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

    # Mini stats
    period_start = df_hist["nav"].iloc[0]
    period_end = df_hist["nav"].iloc[-1]
    period_high = df_hist["nav"].max()
    period_low = df_hist["nav"].min()
    period_ret = ((period_end - period_start) / period_start) * 100
    ret_color = config.STITCH_DESIGN["success_color"] if period_ret >= 0 else config.STITCH_DESIGN["danger_color"]
    sign = "+" if period_ret >= 0 else ""
    st.markdown(
        f"""
        <div style="display:flex; gap:1rem; margin-top:-0.5rem; margin-bottom:1.5rem;">
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

# Fund Description
st.markdown("<span style='font-size:0.8rem; font-weight:600; color:#8A99AD;'>FUND DESCRIPTION</span>", unsafe_allow_html=True)
st.markdown(
    f"""
    <div style="font-size:0.88rem; color:#BAC7D5; line-height:1.5; padding: 0.5rem 0; margin-bottom:1.5rem;">
    {scheme['desc']}
    </div>
    """,
    unsafe_allow_html=True
)
