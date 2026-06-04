import streamlit as st

# Set page config for wide layout
st.set_page_config(
    page_title="ArthaAI - News Feed",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded"
)

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.ui_helpers import inject_css, render_top_navigation, render_ticker_bar, render_sidebar, fetch_google_news_cached, render_floating_chatbot
from src.fund_metadata import FUND_DATA

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
            ARTHAAI WORKSPACE &nbsp;/&nbsp; RECENT GOOGLE NEWS FEED
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

st.markdown("<span style='font-size:0.85rem; font-weight:600; color:#8A99AD;'>RECENT GOOGLE NEWS ARTICLES FEED</span>", unsafe_allow_html=True)
st.markdown("<div style='margin-bottom:1rem;'></div>", unsafe_allow_html=True)

with st.spinner("Fetching latest news from Google News..."):
    articles = fetch_google_news_cached(selected_key)

if articles:
    st.markdown("<div style='margin-bottom:0.5rem;'></div>", unsafe_allow_html=True)
    
    # We display them in a clean two-column grid or single clean list
    news_col1, news_col2 = st.columns(2, gap="medium")
    
    for idx, art in enumerate(articles):
        date_str = art["date"]
        try:
            parts = date_str.split(" ")
            if len(parts) >= 4:
                date_str = f"{parts[1]} {parts[2]} {parts[3]}"
        except:
            pass
            
        news_card = f"""
        <div style="background:var(--card-bg-color); border:1px solid var(--border-color); border-radius:6px; padding:0.8rem 1rem; margin-bottom:0.8rem; height: 110px; display: flex; flex-direction: column; justify-content: space-between;">
            <div style="display:flex; justify-content:space-between; align-items:baseline; margin-bottom:6px;">
                <span style="font-size:0.7rem; font-weight:700; color:var(--primary-color); text-transform:uppercase; letter-spacing:0.05em;">{art['source']}</span>
                <span style="font-size:0.65rem; color:var(--outline-color);">{date_str}</span>
            </div>
            <a class="news-link" href="{art['link']}" target="_blank" style="font-size:0.9rem; font-weight:600; line-height:1.45; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;">
                {art['title']}
            </a>
        </div>
        """
        
        # Distribute news cards evenly across two columns
        if idx % 2 == 0:
            with news_col1:
                st.markdown(news_card, unsafe_allow_html=True)
        else:
            with news_col2:
                st.markdown(news_card, unsafe_allow_html=True)
else:
    st.markdown(
        "<div style='color:#8A99AD; font-size:0.85rem; padding:1.5rem; text-align:center;'>⚠️ No recent news articles found for this fund house.</div>",
        unsafe_allow_html=True
    )

# Render the floating chatbot
render_floating_chatbot(selected_key)

