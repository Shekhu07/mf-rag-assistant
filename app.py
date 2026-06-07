# pyrefly: ignore [missing-import]
import streamlit as st
import pandas as pd
# pyrefly: ignore [missing-import]
import altair as alt
from collections import defaultdict

# Set page config for wide layout
st.set_page_config(
    page_title="ArthaAI - Scheme Overview",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent))

import markdown as md_lib
from src.ui_helpers import inject_css, render_top_navigation, render_ticker_bar, render_sidebar, get_nav_data_cached, prefetch_other_funds, fetch_nav_history_cached, query_fund_api, fetch_google_news_cached
from src.fund_metadata import FUND_DATA
import src.config as config

# 1. Inject CSS, ticker bar, terminal navigation, and sidebar
inject_css()
render_ticker_bar()
render_top_navigation()
selected_key = render_sidebar()
scheme = FUND_DATA[selected_key]

# --- WORKSPACE STATUS BAR ---
st.markdown(
    """
    <div class="workspace-bar">
        <div class="workspace-bar-label">
            ARTHAAI WORKSPACE &nbsp;/&nbsp; SCHEME RESEARCH & OVERVIEW
        </div>
        <div class="workspace-bar-status">
            <span class="status-dot"></span>
            <span class="status-label">RAG SECURED CORE</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# Initialize view state
if "active_view" not in st.session_state:
    st.session_state["active_view"] = "overview"

# ============================================================
# CONDITIONAL VIEW SWITCHING: CHATBOT VS OVERVIEW
# ============================================================
if st.session_state["active_view"] == "chatbot":
    # ============================================================
    # HERO SECTION: RAG CHATBOT (Front & Center)
    # ============================================================

    chat_key = f"main_chat_{selected_key}"
    if chat_key not in st.session_state:
        st.session_state[chat_key] = [
            {
                "role": "analyst",
                "content": f"Welcome to ArthaAI RAG Assistant! Ask me factual questions about this fund (e.g. expense ratios, exit loads, SIP minimums, riskometer, benchmark, lock-in). Facts-only. No investment advice."
            }
        ]

    st.markdown(
        f"""
        <div style="background: linear-gradient(135deg, rgba(173, 198, 255, 0.08), rgba(78, 222, 163, 0.04));
            border: 1px solid rgba(173, 198, 255, 0.15); border-radius: 16px; overflow: hidden; margin-bottom: 1.5rem;">
            <div style="padding: 18px 24px; border-bottom: 1px solid rgba(255,255,255,0.08);
                background: rgba(173, 198, 255, 0.06); display:flex; align-items:center; justify-content:space-between;">
                <div style="display:flex; align-items:center; gap:12px;">
                    <div style="width:36px; height:36px; background:var(--primary-color); border-radius:8px; display:flex; align-items:center; justify-content:center; font-size:18px; color:var(--on-primary); font-weight:800;">⚡</div>
                    <div>
                        <div style="font-weight:700; color:var(--text-highlight-color); font-size:16px; font-family:var(--font-body);">ArthaAI RAG Assistant</div>
                        <div style="font-size:11px; color:var(--outline-color); font-family:var(--font-body);">
                            Grounded on: <strong style="color:var(--primary-color);">{scheme['name']}</strong> &nbsp;·&nbsp; RAG Isolation Active
                        </div>
                    </div>
                </div>
                <div style="display:flex; align-items:center; gap:6px;">
                    <span style="display:inline-block; width:8px; height:8px; background-color:var(--success-color); border-radius:50%; box-shadow:0 0 10px var(--success-color);"></span>
                    <span style="font-size:11px; font-weight:700; color:var(--success-color); letter-spacing:0.05em;">LIVE</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Chat messages viewport
    chat_viewport = st.container(height=260 if len(st.session_state[chat_key]) == 1 else 320)
    with chat_viewport:
        if len(st.session_state[chat_key]) == 1:
            st.markdown(
                f"""
                <div style="padding: 10px; font-family: var(--font-body);">
                    <div style="font-size: 0.9rem; font-weight: 500; color: var(--text-highlight-color); margin-bottom: 8px;">
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
                if st.button("What is the expense ratio?", key=f"sug_exp_{selected_key}", use_container_width=True):
                    sug_query = "What is the expense ratio of this fund?"
            with col_s2:
                if st.button("What is the exit load?", key=f"sug_exit_{selected_key}", use_container_width=True):
                    sug_query = "What are the exit load details?"
            with col_s3:
                if st.button("What is the lock-in period?", key=f"sug_lock_{selected_key}", use_container_width=True):
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
                        f"""<div class="float-chat-row-user"><div class="float-chat-bubble float-chat-bubble-user">{chat['content']}</div></div>""",
                        unsafe_allow_html=True
                    )
                else:
                    html_content = md_lib.markdown(chat['content'], extensions=['tables', 'nl2br'])
                    st.markdown(
                        f"""<div class="float-chat-row-analyst"><div class="float-chat-bubble float-chat-bubble-analyst">{html_content}</div></div>""",
                        unsafe_allow_html=True
                    )

    # Chat input form
    with st.form(key=f"main_chat_form_{selected_key}", clear_on_submit=True):
        chat_col_in, chat_col_btn = st.columns([6, 1])
        with chat_col_in:
            chat_input = st.text_input(
                "Ask ArthaAI...",
                placeholder="Ask factual questions (e.g. What is the minimum SIP? Exit load?)...",
                label_visibility="collapsed",
                key=f"main_chat_input_{selected_key}"
            )
        with chat_col_btn:
            chat_submitted = st.form_submit_button("Ask ➔", use_container_width=True)

    if chat_submitted and chat_input:
        st.session_state[chat_key].append({"role": "user", "content": chat_input})
        with st.spinner("⚡ Analyzing with RAG..."):
            ans, sources = query_fund_api(chat_input, selected_key, st.session_state[chat_key][:-1])
            st.session_state[chat_key].append({
                "role": "analyst",
                "content": ans,
                "sources": sources
            })
        st.rerun()

    st.markdown(
        """
        <div style="text-align: center; font-size: 0.72rem; color: var(--outline-color); font-weight: 600; margin-top: -8px; margin-bottom: 8px;">
            Facts-only. No investment advice.
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("<div style='margin-bottom:1rem;'></div>", unsafe_allow_html=True)
    st.divider()

elif st.session_state["active_view"] == "overview":
    # --- SCHEME HEADER ---
    st.markdown(f'<span class="scheme-category-badge">{scheme["category"]}</span><span class="scheme-type-label">Direct Growth</span>', unsafe_allow_html=True)
    st.markdown(f'<div class="scheme-title">{scheme["name"]}</div>', unsafe_allow_html=True)

    # Fetch NAV metrics for the selected fund
    live_nav_data = get_nav_data_cached(selected_key)
    
    # Prefetch other funds in the background so they load instantly when clicked
    prefetch_other_funds(selected_key)
    display_nav = live_nav_data["nav"]
    display_change = live_nav_data["change"]
    display_change_positive = live_nav_data["change_positive"]
    nav_date = live_nav_data["date"]
    is_live = live_nav_data["is_live"]

    change_color = "var(--success-color)" if display_change_positive else "var(--danger-color)"
    change_arrow = "▲" if display_change_positive else "▼"
    live_badge = (
        f'<span style="background:rgba(78,222,163,0.1); color:var(--success-color); font-size:10px; font-weight:700; '
        f'padding:2px 8px; border-radius:4px; border:1px solid rgba(78,222,163,0.2); margin-left:12px;">● LIVE · {nav_date}</span>'
    ) if is_live else (
        f'<span style="background:rgba(255,193,7,0.1); color:#ffc107; font-size:10px; font-weight:700; '
        f'padding:2px 8px; border-radius:4px; border:1px solid rgba(255,193,7,0.2); margin-left:12px;">● Data as of {nav_date} — live fetch unavailable</span>'
    )

    st.markdown(
        f"""
        <div class="nav-section">
            <div class="nav-metric">
                <span class="nav-metric-label">NAV</span>
                <span class="nav-metric-value">{display_nav} <span class="nav-change-inline" style="color:{change_color};">{change_arrow}{display_change}</span></span>
            </div>
            <div class="nav-divider"></div>
            <div class="nav-metric">
                <span class="nav-metric-label">AUM</span>
                <span class="nav-metric-value">{scheme['aum']}</span>
            </div>
            <div class="nav-divider"></div>
            <div class="nav-metric">
                <span class="nav-metric-label">EXPENSE RATIO</span>
                <span class="nav-metric-value">{scheme['expense_ratio']}</span>
            </div>
            {live_badge}
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("<div style='margin-bottom:1.5rem;'></div>", unsafe_allow_html=True)

    # --- CAGR RETURN CARDS (Terminal Display-lg Style) ---
    st.markdown("<span style='font-size:0.8rem; font-weight:600; color:var(--outline-color);'>HISTORICAL PERFORMANCE (CAGR)</span>", unsafe_allow_html=True)
    st.markdown("<div style='margin-bottom:0.5rem;'></div>", unsafe_allow_html=True)

    def get_performance_badge(return_str: str, default_compare: str):
        try:
            val = float(return_str.replace('%', '').strip())
            if val >= 15.0:
                return "OUTPERFORMING", "badge-outperforming", "trending_up", "return-card-value-green", default_compare
            elif val >= 8.0:
                return "STABLE", "badge-stable", "timeline", "return-card-value-default", default_compare
            else:
                return "LAGGING", "badge-lagging", "trending_down", "return-card-value-danger", "Underperforming"
        except Exception:
            return "STABLE", "badge-stable", "timeline", "return-card-value-default", default_compare

    r1_badge, r1_class, r1_icon, r1_val_class, r1_comp = get_performance_badge(scheme["return_1y"], "vs Category Avg")
    r3_badge, r3_class, r3_icon, r3_val_class, r3_comp = get_performance_badge(scheme["return_3y"], "Annualized CAGR")
    r5_badge, r5_class, r5_icon, r5_val_class, r5_comp = get_performance_badge(scheme["return_5y"], "Long-Term Growth")

    returns = [
        ("1Y RETURN", scheme["return_1y"], r1_icon, r1_badge, r1_class, r1_comp, r1_val_class),
        ("3Y RETURN", scheme["return_3y"], r3_icon, r3_badge, r3_class, r3_comp, r3_val_class),
        ("5Y RETURN", scheme["return_5y"], r5_icon, r5_badge, r5_class, r5_comp, r5_val_class),
    ]

    r_col1, r_col2, r_col3 = st.columns(3)
    for i, (label, value, icon, badge_text, badge_class, compare_text, val_class) in enumerate(returns):
        col = [r_col1, r_col2, r_col3][i]
        with col:
            st.markdown(
                f"""
                <div class="return-card-terminal">
                    <div class="return-card-label">{label}</div>
                    <div class="return-card-value {val_class}">{value}</div>
                    <div class="return-card-status">
                        <span class="performance-badge {badge_class}">{badge_text}</span>
                        <span class="return-card-compare">{compare_text}</span>
                    </div>
                    <span class="material-symbols-outlined return-card-bg-icon">{icon}</span>
                </div>
                """,
                unsafe_allow_html=True
            )

    st.markdown("<div style='margin-bottom:1.5rem;'></div>", unsafe_allow_html=True)

    # --- LATEST NEWS EXPANDER ---
    with st.expander("📰 Latest News & Updates"):
        with st.spinner("Fetching latest news..."):
            news_items = fetch_google_news_cached(selected_key)
            if news_items:
                for item in news_items[:3]:
                    st.markdown(f"**[{item['title']}]({item['link']})**")
                    st.caption(f"{item.get('source', '')} • {item.get('date', '')}")
            else:
                st.info("No recent news found for this fund.")

    st.markdown("<div style='margin-bottom:1.5rem;'></div>", unsafe_allow_html=True)

    # --- NAV PRICE HISTORY CHART ---
    period_key = f"nav_period_{selected_key}"
    if period_key not in st.session_state:
        st.session_state[period_key] = "1Y"

    # Chart container
    st.markdown("""
        <style>
        /* Target the chart container specifically */
        div[data-testid="stVerticalBlock"] > div:has(> div > div > .chart-header) {
            background-color: var(--card-bg-color);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 20px 24px;
            margin-bottom: 1.5rem;
        }
        </style>
    """, unsafe_allow_html=True)

    with st.container():
        st.markdown(
            """
            <div class="chart-header">
                <div class="chart-title">
                    <span class="material-symbols-outlined chart-title-icon">show_chart</span>
                    NAV Price History
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        period_cols = st.columns(6)
        period_labels = ["1M", "6M", "1Y", "3Y", "5Y", "All"]
        for i, period_label in enumerate(period_labels):
            with period_cols[i]:
                is_active = st.session_state[period_key] == period_label
                if st.button(
                    period_label,
                    key=f"period_{selected_key}_{period_label}",
                    use_container_width=True,
                    type="primary" if is_active else "secondary",
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
            line_color = config.STITCH_DESIGN["success_color"] if is_positive else config.STITCH_DESIGN["danger_color"]
            area_color_start = "rgba(78,222,163,0.25)" if is_positive else "rgba(255,180,171,0.25)"

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
                tooltip=[
                    alt.Tooltip("date_str:N", title="Date"),
                    alt.Tooltip("nav:Q", title="NAV (₹)", format=".2f"),
                    alt.Tooltip("pct_change:Q", title="Change (%)", format=".2f")
                ]
            )

            area = base.mark_area(
                line={"color": line_color, "strokeWidth": 2},
                color=alt.Gradient(
                    gradient="linear",
                    stops=[
                        alt.GradientStop(color=area_color_start, offset=0),
                        alt.GradientStop(color="rgba(11,19,38,0.0)", offset=1),
                    ],
                    x1=1, x2=1, y1=1, y2=0,
                ),
                interpolate="monotone"
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
                <div class="mini-stats-row">
                    <div class="mini-stat-card">
                        <div class="mini-stat-label">PERIOD RETURN</div>
                        <div class="mini-stat-value" style="color:{ret_color};">{sign}{period_ret:.1f}%</div>
                    </div>
                    <div class="mini-stat-card">
                        <div class="mini-stat-label">{selected_period} HIGH</div>
                        <div class="mini-stat-value" style="color:var(--text-highlight-color)">₹{period_high:,.2f}</div>
                    </div>
                    <div class="mini-stat-card">
                        <div class="mini-stat-label">{selected_period} LOW</div>
                        <div class="mini-stat-value" style="color:var(--text-highlight-color)">₹{period_low:,.2f}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                "<div style='color:var(--outline-color); font-size:0.85rem; padding:1rem; text-align:center;'>⚠️ Could not load chart data. Check your internet connection.</div>",
                unsafe_allow_html=True,
            )

    # --- BENTO GRID: Sector Allocation + Risk Metrics ---
    bento_left, bento_right = st.columns([1.4, 1.0], gap="large")

    with bento_left:
        # Sector Allocation
        sector_map = defaultdict(float)
        for _, sector, alloc_str in scheme["holdings"]:
            try:
                alloc_val = float(alloc_str.replace("%", "").strip())
                sector_map[sector] += alloc_val
            except ValueError:
                pass

        sorted_sectors = sorted(sector_map.items(), key=lambda x: x[1], reverse=True)[:6]
        max_alloc = max(sorted_sectors[0][1], 1.0) if sorted_sectors else 1.0
        bar_colors = ["sector-bar-primary", "sector-bar-secondary", "sector-bar-primary", "sector-bar-outline", "sector-bar-warning", "sector-bar-outline"]

        st.markdown(
            """
            <div class="sector-card">
                <div class="sector-card-header">
                    <span class="sector-card-title">Sector Allocation</span>
                    <span style="font-size:11px; color:var(--outline-color);">Top 6 Sectors</span>
                </div>
            """,
            unsafe_allow_html=True
        )

        for i, (sector_name, alloc) in enumerate(sorted_sectors):
            bar_class = bar_colors[i % len(bar_colors)]
            st.markdown(
                f"""
                <div class="sector-row">
                    <div class="sector-row-label">
                        <span>{sector_name}</span>
                        <span>{alloc:.1f}%</span>
                    </div>
                    <div class="sector-bar-track">
                        <div class="sector-bar-fill {bar_class}" style="width:{alloc / max_alloc * 100:.1f}%;"></div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        st.markdown("</div>", unsafe_allow_html=True)

    with bento_right:
        # Risk Metrics Cards
        st.markdown(
            f"""
            <div class="stat-card" style="margin-bottom:16px;">
                <span class="stat-card-label">RISKOMETER</span>
                <span class="stat-card-value" style="color:var(--warning-color);">{scheme['riskometer']}</span>
                <span class="stat-card-note">SEBI Risk Classification</span>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            f"""
            <div class="stat-card" style="margin-bottom:16px;">
                <span class="stat-card-label">FUND MANAGER</span>
                <span class="stat-card-value">{scheme['manager']}</span>
                <span class="stat-card-note-success">✓ Active Management</span>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            f"""
            <div class="stat-card">
                <span class="stat-card-label">MINIMUM SIP</span>
                <span class="stat-card-value" style="color:var(--success-color);">{scheme['min_sip']}</span>
                <span class="stat-card-note">Per Month</span>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("<div style='margin-bottom:1.5rem;'></div>", unsafe_allow_html=True)

    # --- TERMINAL INSIGHTS CARD ---
    st.markdown(
        f"""
        <div class="insights-card">
            <div>
                <div class="insights-title">Terminal Insights</div>
                <div class="insights-text">
                    {scheme['desc']}<br/>
                    <span style="color:var(--text-highlight-color); font-weight:600;">Use the RAG chatbot above</span> to query deeper analysis on portfolio risk, sector concentration, and historical returns.
                </div>
            </div>
            <span class="material-symbols-outlined insights-icon">psychology</span>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("<div style='margin-bottom:2rem;'></div>", unsafe_allow_html=True)
