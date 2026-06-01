import streamlit as st
import pandas as pd
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

from src.ui_helpers import inject_css, render_top_navigation, render_sidebar
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
            ARTHAAI WORKSPACE &nbsp;/&nbsp; HOLDINGS & OVERLAP ANALYZER
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
left_panel, right_panel = st.columns([1.0, 1.0], gap="large")

with left_panel:
    st.markdown("<span style='font-size:0.85rem; font-weight:600; color:#8A99AD;'>PORTFOLIO ALLOCATION BREAKDOWN</span>", unsafe_allow_html=True)
    st.markdown("<div style='margin-bottom:1rem;'></div>", unsafe_allow_html=True)
    
    try:
        # Donut Chart
        df = pd.DataFrame(scheme["holdings"], columns=["Company", "Sector", "Allocation"])
        df["AllocNum"] = df["Allocation"].str.replace("%", "").astype(float)
        
        chart = alt.Chart(df).mark_arc(innerRadius=65, outerRadius=110, stroke=config.STITCH_DESIGN["bg_color"], strokeWidth=2).encode(
            theta=alt.Theta(field="AllocNum", type="quantitative"),
            color=alt.Color(
                field="Company", 
                type="nominal", 
                scale=alt.Scale(range=[config.STITCH_DESIGN["primary_color"], config.STITCH_DESIGN["success_color"], "#3B82F6", "#F59E0B", "#EC4899"]),
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
                alt.Tooltip(field="Company", type="nominal"),
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

    # Detailed holdings table below chart
    st.markdown("<div style='margin-top:2rem;'></div>", unsafe_allow_html=True)
    st.markdown("<span style='font-size:0.85rem; font-weight:600; color:#8A99AD;'>DETAILED PORTFOLIO HOLDINGS LIST</span>", unsafe_allow_html=True)
    st.markdown("<div style='margin-bottom:0.8rem;'></div>", unsafe_allow_html=True)

    rows = ""
    for i, (company, sector, alloc) in enumerate(scheme["holdings"]):
        rows += f"""
        <tr>
            <td style="color:var(--text-muted-color); padding:0.5rem 0.8rem; border-bottom:1px solid var(--border-color);">{i+1}</td>
            <td style="color:var(--text-highlight-color); font-weight:600; padding:0.5rem 0.8rem; border-bottom:1px solid var(--border-color);">{company}</td>
            <td style="color:var(--text-color); padding:0.5rem 0.8rem; border-bottom:1px solid var(--border-color);">{sector}</td>
            <td style="color:var(--primary-color); padding:0.5rem 0.8rem; border-bottom:1px solid var(--border-color); font-weight:700; text-align:right;">{alloc}</td>
        </tr>
        """

    st.markdown(
        f"""
        <table class="holdings-table" style="width:100%; border-collapse:collapse; background:var(--card-bg-color); border:1px solid var(--border-color); border-radius:6px; overflow:hidden; font-size:0.85rem; margin-bottom:1.5rem;">
            <thead>
                <tr style="border-bottom:1px solid var(--border-color); text-align:left; background:var(--bg-color);">
                    <th style="padding:0.6rem 0.8rem; color:var(--text-muted-color); font-weight:700; width:50px;">#</th>
                    <th style="padding:0.6rem 0.8rem; color:var(--text-muted-color); font-weight:700;">Company</th>
                    <th style="padding:0.6rem 0.8rem; color:var(--text-muted-color); font-weight:700;">Sector</th>
                    <th style="padding:0.6rem 0.8rem; color:var(--text-muted-color); font-weight:700; text-align:right; width:100px;">Allocation</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>
        """,
        unsafe_allow_html=True
    )

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
    
    st.markdown("<span style='font-size:0.8rem; font-weight:600; color:#8A99AD;'>OVERLAPPING STOCKS</span>", unsafe_allow_html=True)
    st.markdown("<div style='margin-bottom:0.5rem;'></div>", unsafe_allow_html=True)
    
    if common_data:
        common_data = sorted(common_data, key=lambda x: x["shared_val"], reverse=True)
        rows_overlap = ""
        for item in common_data:
            rows_overlap += f"""
            <tr>
                <td style="color:var(--text-highlight-color); font-weight:600; padding:0.6rem 0.8rem; border-bottom:1px solid var(--border-color);">{item['Company']}</td>
                <td style="color:var(--text-muted-color); padding:0.6rem 0.8rem; border-bottom:1px solid var(--border-color);">{item['Sector']}</td>
                <td style="color:var(--text-highlight-color); text-align:right; padding:0.6rem 0.8rem; border-bottom:1px solid var(--border-color);">{item['Allocation A']}</td>
                <td style="color:var(--text-highlight-color); text-align:right; padding:0.6rem 0.8rem; border-bottom:1px solid var(--border-color);">{item['Allocation B']}</td>
                <td style="color:var(--primary-color); text-align:right; font-weight:700; padding:0.6rem 0.8rem; border-bottom:1px solid var(--border-color);">{item['Shared Overlap']}</td>
            </tr>
            """
            
        st.markdown(
            textwrap.dedent(f"""
            <table style="width:100%; border-collapse:collapse; background:var(--card-bg-color); border:1px solid var(--border-color); border-radius:6px; overflow:hidden; font-size:0.85rem; margin-bottom:1.5rem;">
                <thead>
                    <tr style="border-bottom:1px solid var(--border-color); text-align:left; background:var(--bg-color);">
                        <th style="padding:0.75rem 1rem; color:var(--text-muted-color); font-weight:700;">Company</th>
                        <th style="padding:0.75rem 1rem; color:var(--text-muted-color); font-weight:700;">Sector</th>
                        <th style="padding:0.75rem 1rem; color:var(--text-muted-color); font-weight:700; text-align:right;">{scheme['name']}</th>
                        <th style="padding:0.75rem 1rem; color:var(--text-muted-color); font-weight:700; text-align:right;">{comp_scheme['name']}</th>
                        <th style="padding:0.75rem 1rem; color:var(--primary-color); font-weight:700; text-align:right;">Shared Overlap</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_overlap}
                </tbody>
            </table>
            """),
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            "<div style=\"background:var(--card-bg-color); border:1px solid var(--border-color); border-radius:6px; padding:1.5rem; text-align:center; color:var(--text-muted-color); font-size:0.85rem; margin-bottom:1.5rem;\">"
            "🟢 No overlapping holdings found in these two funds. Excellent diversification!"
            "</div>",
            unsafe_allow_html=True
        )
        
    # Unique portfolio drivers
    st.markdown("<span style='font-size:0.8rem; font-weight:600; color:#8A99AD;'>UNIQUE PORTFOLIO DRIVERS</span>", unsafe_allow_html=True)
    st.markdown("<div style='margin-bottom:0.8rem;'></div>", unsafe_allow_html=True)
    
    col_unique_a, col_unique_b = st.columns(2)
    
    with col_unique_a:
        st.markdown(f"<span style='font-size:0.75rem; font-weight:700; color:var(--text-muted-color); text-transform:uppercase;'>Unique to {scheme['name']}</span>", unsafe_allow_html=True)
        st.markdown("<div style='margin-bottom:0.4rem;'></div>", unsafe_allow_html=True)
        unique_a_keys = [c for c in holdings_a.keys() if c not in common_companies]
        if unique_a_keys:
            unique_a_keys = sorted(unique_a_keys, key=lambda x: holdings_a[x]['alloc'], reverse=True)
            list_items = ""
            for u in unique_a_keys:
                orig_name = holdings_a[u]['original_name']
                list_items += f"<li style='margin-bottom:0.4rem; font-size:0.85rem; color:var(--text-highlight-color);'><span style='font-weight:600;'>{orig_name}</span> <span style='color:var(--text-muted-color);'>({holdings_a[u]['alloc']:.2f}%)</span></li>"
            st.markdown(f"<ul style='list-style-type:square; padding-left:1.2rem;'>{list_items}</ul>", unsafe_allow_html=True)
        else:
            st.markdown("<div style='color:var(--text-muted-color); font-size:0.8rem;'>No unique holdings.</div>", unsafe_allow_html=True)
            
    with col_unique_b:
        st.markdown(f"<span style='font-size:0.75rem; font-weight:700; color:var(--text-muted-color); text-transform:uppercase;'>Unique to {comp_scheme['name']}</span>", unsafe_allow_html=True)
        st.markdown("<div style='margin-bottom:0.4rem;'></div>", unsafe_allow_html=True)
        unique_b_keys = [c for c in holdings_b.keys() if c not in common_companies]
        if unique_b_keys:
            unique_b_keys = sorted(unique_b_keys, key=lambda x: holdings_b[x]['alloc'], reverse=True)
            list_items = ""
            for u in unique_b_keys:
                orig_name = holdings_b[u]['original_name']
                list_items += f"<li style='margin-bottom:0.4rem; font-size:0.85rem; color:var(--text-highlight-color);'><span style='font-weight:600;'>{orig_name}</span> <span style='color:var(--text-muted-color);'>({holdings_b[u]['alloc']:.2f}%)</span></li>"
            st.markdown(f"<ul style='list-style-type:square; padding-left:1.2rem;'>{list_items}</ul>", unsafe_allow_html=True)
        else:
            st.markdown("<div style='color:var(--text-muted-color); font-size:0.8rem;'>No unique holdings.</div>", unsafe_allow_html=True)
