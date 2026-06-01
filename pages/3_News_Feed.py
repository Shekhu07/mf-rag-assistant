import streamlit as st

# Set page config for wide layout
st.set_page_config(
    page_title="ArthaAI - News Feed",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded"
)

from src.ui_helpers import inject_css, render_top_navigation, render_sidebar, fetch_google_news_cached
from src.fund_metadata import FUND_DATA

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
            ARTHAAI WORKSPACE &nbsp;/&nbsp; RECENT GOOGLE NEWS FEED
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
        <div style="background:#0E1217; border:1px solid #1C232E; border-radius:6px; padding:0.8rem 1rem; margin-bottom:0.8rem; height: 110px; display: flex; flex-direction: column; justify-content: space-between;">
            <div style="display:flex; justify-content:space-between; align-items:baseline; margin-bottom:6px;">
                <span style="font-size:0.7rem; font-weight:700; color:#E2FF3B; text-transform:uppercase; letter-spacing:0.05em;">{art['source']}</span>
                <span style="font-size:0.65rem; color:#8A99AD;">{date_str}</span>
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
