# pyrefly: ignore [missing-import]
import streamlit as st
import pandas as pd
# pyrefly: ignore [missing-import]
import altair as alt
import textwrap
import re

# Set page config for wide layout
st.set_page_config(
    page_title="ArthaAI - Holdings & Overlap",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

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
            ARTHAAI WORKSPACE &nbsp;/&nbsp; HOLDINGS & OVERLAP ANALYZER
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
left_panel, right_panel = st.columns([1.0, 1.0], gap="large")

with left_panel:
    st.markdown("<span style='font-size:0.85rem; font-weight:600; color:#8A99AD;'>PORTFOLIO ALLOCATION BREAKDOWN</span>", unsafe_allow_html=True)
    st.markdown("<div style='margin-bottom:1rem;'></div>", unsafe_allow_html=True)
    
    try:
        # Donut Chart
        df = pd.DataFrame(scheme["holdings"], columns=["Company", "Sector", "Allocation"])
        df["AllocNum"] = df["Allocation"].str.replace("%", "").astype(float)
        
        # Aggregate by Sector
        sector_df = df.groupby("Sector", as_index=False)["AllocNum"].sum()
        sector_df = sector_df.sort_values(by="AllocNum", ascending=False)
        sector_df["Allocation"] = sector_df["AllocNum"].apply(lambda x: f"{x:.2f}%")

        if sector_df.empty:
            st.info("No holdings data available for this fund.")
        else:
            chart = alt.Chart(sector_df).mark_arc(innerRadius=65, outerRadius=110, stroke=config.STITCH_DESIGN["bg_color"], strokeWidth=2).encode(
                theta=alt.Theta(field="AllocNum", type="quantitative"),
                color=alt.Color(
                    field="Sector",
                    type="nominal",
                    sort=alt.EncodingSortField(field="AllocNum", op="sum", order="descending"),
                    scale=alt.Scale(range=[config.STITCH_DESIGN["primary_color"], config.STITCH_DESIGN["success_color"], "#3B82F6", "#F59E0B", "#EC4899", "#8B5CF6", "#10B981", "#EF4444", "#F97316", "#06B6D4"]),
                    legend=alt.Legend(
                        title=None,
                        orient="right",
                        labelColor=config.STITCH_DESIGN["text_color"],
                        labelFontSize=11,
                        labelFontWeight=500,
                        symbolSize=100,
                        rowPadding=6
                    )
                ),
                tooltip=[
                    alt.Tooltip(field="Sector", type="nominal"),
                    alt.Tooltip(field="Allocation", type="nominal")
                ]
            ).properties(
                height=280
            ).configure(
                background="transparent"
            ).configure_view(
                strokeWidth=0
            )

            st.altair_chart(chart, use_container_width=True)
    except Exception as chart_err:
        st.error(f"Error rendering chart: {chart_err}")


with right_panel:
    st.markdown("<span style='font-size:0.85rem; font-weight:600; color:#8A99AD;'>MUTUAL FUND SCHEME COMPARE & OVERLAP ANALYZER</span>", unsafe_allow_html=True)
    st.markdown("<div style='margin-bottom:1rem;'></div>", unsafe_allow_html=True)

    comp_options = [k for k in FUND_DATA.keys() if k != selected_key]
    comparison_key = st.selectbox(
        "Select Mutual Fund to compare overlap with:",
        options=comp_options,
        format_func=lambda x: FUND_DATA[x]["name"],
        key=f"overlap_compare_page_{selected_key}"
    )
    
    comp_scheme = FUND_DATA[comparison_key]
    st.markdown("<div style='margin-bottom:1rem;'></div>", unsafe_allow_html=True)
    
    # --- SIDE-BY-SIDE SPECIFICATIONS COMPARISON ---
    st.markdown("<span style='font-size:0.8rem; font-weight:600; color:#8A99AD;'>KEY SCHEME SPECIFICATIONS COMPARISON</span>", unsafe_allow_html=True)
    st.markdown("<div style='margin-bottom:0.5rem;'></div>", unsafe_allow_html=True)
    
    r_color_a = config.STITCH_DESIGN["danger_color"] if "Very High" in scheme["riskometer"] else config.STITCH_DESIGN.get("warning_color", "#F59E0B")
    r_color_b = config.STITCH_DESIGN["danger_color"] if "Very High" in comp_scheme["riskometer"] else config.STITCH_DESIGN.get("warning_color", "#F59E0B")
    
    st.markdown(
        textwrap.dedent(f"""
        <table style="width:100%; border-collapse:collapse; background:var(--card-bg-color); border:1px solid var(--border-color); border-radius:6px; overflow:hidden; font-size:0.85rem; margin-bottom:1.5rem;">
            <thead>
                <tr style="border-bottom:1px solid var(--border-color); text-align:left; background:var(--bg-color);">
                    <th style="padding:0.6rem 0.8rem; color:var(--text-muted-color); font-weight:700;">Metric</th>
                    <th style="padding:0.6rem 0.8rem; color:var(--text-highlight-color); font-weight:700;">{scheme['name']}</th>
                    <th style="padding:0.6rem 0.8rem; color:var(--text-highlight-color); font-weight:700;">{comp_scheme['name']}</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td style="color:var(--text-muted-color); padding:0.5rem 0.8rem; border-bottom:1px solid var(--border-color);">Category</td>
                    <td style="color:var(--text-highlight-color); padding:0.5rem 0.8rem; border-bottom:1px solid var(--border-color); font-weight:500;">{scheme['category']}</td>
                    <td style="color:var(--text-highlight-color); padding:0.5rem 0.8rem; border-bottom:1px solid var(--border-color); font-weight:500;">{comp_scheme['category']}</td>
                </tr>
                <tr>
                    <td style="color:var(--text-muted-color); padding:0.5rem 0.8rem; border-bottom:1px solid var(--border-color);">AUM (Size)</td>
                    <td style="color:var(--text-highlight-color); padding:0.5rem 0.8rem; border-bottom:1px solid var(--border-color); font-weight:600;">{scheme['aum']}</td>
                    <td style="color:var(--text-highlight-color); padding:0.5rem 0.8rem; border-bottom:1px solid var(--border-color); font-weight:600;">{comp_scheme['aum']}</td>
                </tr>
                <tr>
                    <td style="color:var(--text-muted-color); padding:0.5rem 0.8rem; border-bottom:1px solid var(--border-color);">Expense Ratio</td>
                    <td style="color:var(--primary-color); padding:0.5rem 0.8rem; border-bottom:1px solid var(--border-color); font-weight:700;">{scheme['expense_ratio']}</td>
                    <td style="color:var(--primary-color); padding:0.5rem 0.8rem; border-bottom:1px solid var(--border-color); font-weight:700;">{comp_scheme['expense_ratio']}</td>
                </tr>
                <tr>
                    <td style="color:var(--text-muted-color); padding:0.5rem 0.8rem; border-bottom:1px solid var(--border-color);">1Y Return (CAGR)</td>
                    <td style="color:var(--success-color); padding:0.5rem 0.8rem; border-bottom:1px solid var(--border-color); font-weight:700;">{scheme['return_1y']}</td>
                    <td style="color:var(--success-color); padding:0.5rem 0.8rem; border-bottom:1px solid var(--border-color); font-weight:700;">{comp_scheme['return_1y']}</td>
                </tr>
                <tr>
                    <td style="color:var(--text-muted-color); padding:0.5rem 0.8rem; border-bottom:1px solid var(--border-color);">3Y Return (CAGR)</td>
                    <td style="color:var(--success-color); padding:0.5rem 0.8rem; border-bottom:1px solid var(--border-color); font-weight:700;">{scheme['return_3y']}</td>
                    <td style="color:var(--success-color); padding:0.5rem 0.8rem; border-bottom:1px solid var(--border-color); font-weight:700;">{comp_scheme['return_3y']}</td>
                </tr>
                <tr>
                    <td style="color:var(--text-muted-color); padding:0.5rem 0.8rem; border-bottom:1px solid var(--border-color);">5Y Return (CAGR)</td>
                    <td style="color:var(--success-color); padding:0.5rem 0.8rem; border-bottom:1px solid var(--border-color); font-weight:700;">{scheme['return_5y']}</td>
                    <td style="color:var(--success-color); padding:0.5rem 0.8rem; border-bottom:1px solid var(--border-color); font-weight:700;">{comp_scheme['return_5y']}</td>
                </tr>
                <tr>
                    <td style="color:var(--text-muted-color); padding:0.5rem 0.8rem; border-bottom:1px solid var(--border-color);">Riskometer</td>
                    <td style="color:{r_color_a}; padding:0.5rem 0.8rem; border-bottom:1px solid var(--border-color); font-weight:600;">{scheme['riskometer']}</td>
                    <td style="color:{r_color_b}; padding:0.5rem 0.8rem; border-bottom:1px solid var(--border-color); font-weight:600;">{comp_scheme['riskometer']}</td>
                </tr>
                <tr>
                    <td style="color:var(--text-muted-color); padding:0.5rem 0.8rem;">Fund Manager</td>
                    <td style="color:var(--text-highlight-color); padding:0.5rem 0.8rem;">{scheme['manager']}</td>
                    <td style="color:var(--text-highlight-color); padding:0.5rem 0.8rem;">{comp_scheme['manager']}</td>
                </tr>
            </tbody>
        </table>
        """),
        unsafe_allow_html=True
    )

    def parse_holdings(holdings_list):
        h_dict = {}
        for company, sector, alloc_str in holdings_list:
            try:
                alloc_val = float(alloc_str.replace("%", "").strip())
                norm = company.lower().strip()
                norm = norm.replace("£", "").strip()
                norm = re.sub(r'\b(ltd|limited|corp|corporation|inc|co)\b\.?', '', norm)
                norm = re.sub(r'\s+', ' ', norm).strip()
                h_dict[norm] = {"original_name": company, "sector": sector, "alloc": alloc_val}
            except ValueError:
                pass
        return h_dict
        
    holdings_a = parse_holdings(scheme["holdings"])
    holdings_b = parse_holdings(comp_scheme["holdings"])
    
    # Overlap Formula: Sum(min(alloc_A, alloc_B))
    common_companies = set(holdings_a.keys()).intersection(set(holdings_b.keys()))
    overlap_pct = 0.0
    common_data = []
    for company in common_companies:
        alloc_a = holdings_a[company]["alloc"]
        alloc_b = holdings_b[company]["alloc"]
        shared = min(alloc_a, alloc_b)
        overlap_pct += shared
        common_data.append({
            "Company": holdings_a[company]["original_name"],
            "Sector": holdings_a[company]["sector"],
            "Allocation A": f"{alloc_a:.2f}%",
            "Allocation B": f"{alloc_b:.2f}%",
            "Shared Overlap": f"{shared:.2f}%",
            "shared_val": shared
        })
        
    overlap_pct = round(overlap_pct, 2)
    
    if overlap_pct < 20.0:
        status = "Low Overlap (Excellent Diversification)"
        status_color = config.STITCH_DESIGN["success_color"]
        bg_accent = "rgba(16, 185, 129, 0.1)"
    elif overlap_pct <= 50.0:
        status = "Moderate Overlap (Average Diversification)"
        status_color = config.STITCH_DESIGN["primary_color"]
        bg_accent = "rgba(226, 255, 59, 0.1)"
    else:
        status = "High Overlap (Poor Diversification Redundancy)"
        status_color = config.STITCH_DESIGN["danger_color"]
        bg_accent = "rgba(239, 68, 68, 0.1)"
        
    st.markdown(
        textwrap.dedent(f"""
        <div style="background:var(--card-bg-color); border:1px solid var(--border-color); border-radius:8px; padding:1.5rem; margin-bottom:1.5rem; border-left: 4px solid {status_color};">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <div style="font-size:0.75rem; font-weight:700; color:var(--text-muted-color); text-transform:uppercase; letter-spacing:0.08em; margin-bottom:0.4rem;">
                        PORTFOLIO OVERLAP PERCENTAGE
                    </div>
                    <div style="font-size:2.2rem; font-weight:800; color:{status_color};">
                        {overlap_pct:.2f}%
                    </div>
                </div>
                <div style="text-align:right;">
                    <span style="font-size:0.7rem; font-weight:700; background:{bg_accent}; color:{status_color}; padding:0.4rem 0.8rem; border-radius:4px; border:1px solid {status_color}33;">
                        {status}
                    </span>
                </div>
            </div>
        </div>
        """),
        unsafe_allow_html=True
    )
    

    
# Render the floating chatbot
render_floating_chatbot(selected_key)
