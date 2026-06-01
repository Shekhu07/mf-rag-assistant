"""
src/news_service.py
------------------
Fetches Google News RSS feed for mutual funds and runs sentiment analysis and transaction tracking.
"""

import requests
import xml.etree.ElementTree as ET
import urllib.parse
import logging
from typing import List, Dict, Optional
from langchain_core.messages import SystemMessage, HumanMessage

logger = logging.getLogger(__name__)

NEWS_QUERIES = {
    "parag_parikh_flexi": '("Parag Parikh Mutual Fund" OR "PPFAS" OR "Parag Parikh Flexi") AND (bought OR sold OR portfolio OR holdings OR stock OR exit OR entry OR buy OR sell)',
    "pp_tax_saver": '("Parag Parikh Tax Saver" OR "PPFAS ELSS" OR "Parag Parikh ELSS") AND (bought OR sold OR portfolio OR holdings OR stock OR exit OR entry OR buy OR sell)',
    "pp_conservative": '("Parag Parikh Conservative" OR "PPFAS Conservative" OR "Parag Parikh Hybrid") AND (bought OR sold OR portfolio OR holdings OR stock OR exit OR entry OR buy OR sell)',
    "pp_liquid": '("Parag Parikh Liquid" OR "PPFAS Liquid") AND (bought OR sold OR portfolio OR holdings OR stock OR exit OR entry OR buy OR sell)',
    "pp_dynamic": '("Parag Parikh Dynamic" OR "PPFAS Dynamic" OR "Parag Parikh Asset Allocation") AND (bought OR sold OR portfolio OR holdings OR stock OR exit OR entry OR buy OR sell)'
}

def fetch_google_news(fund_id: str, max_results: int = 6) -> List[Dict]:
    """
    Fetches the latest Google News articles for a specific mutual fund.
    """
    query = NEWS_QUERIES.get(
        fund_id, 
        f'"{fund_id} Mutual Fund" AND (bought OR sold OR portfolio OR buy OR sell)'
    )
    encoded_query = urllib.parse.quote(query)
    url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-IN&gl=IN&ceid=IN:en"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        resp = requests.get(url, headers=headers, timeout=6)
        resp.raise_for_status()
        
        root = ET.fromstring(resp.content)
        articles = []
        for item in root.findall(".//item")[:max_results]:
            title = item.find("title").text
            link = item.find("link").text
            pub_date = item.find("pubDate").text
            source = item.find("source").text if item.find("source") is not None else "Google News"
            
            # Simple title cleaning (strip the source tag at the end, e.g. "- Mint")
            cleaned_title = title
            if " - " in title:
                parts = title.rsplit(" - ", 1)
                cleaned_title = parts[0]
                if not source or source == "Google News":
                    source = parts[1]

            articles.append({
                "title": cleaned_title,
                "link": link,
                "date": pub_date,
                "source": source
            })
        logger.info(f"Fetched {len(articles)} news articles for {fund_id}")
        return articles
    except Exception as e:
        logger.error(f"Error fetching Google News for {fund_id}: {e}")
        return []

def analyze_sentiment_with_llm(articles: List[Dict], fund_name: str, api_key: str) -> str:
    """
    Invokes Gemini to analyze news sentiment and portfolio transaction details.
    """
    if not articles:
        return "No recent news articles found to perform sentiment analysis."
        
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        import src.config as config
        
        llm = ChatGoogleGenerativeAI(
            model=config.GENERATION_MODEL,
            temperature=0.1,  # low temperature for stable fact extraction
            google_api_key=api_key,
            max_retries=0
        )
        
        bullet_list = ""
        for idx, art in enumerate(articles):
            bullet_list += f"[{idx+1}] Title: {art['title']} (Source: {art['source']}, Date: {art['date']})\n"
            
        system_prompt = (
            "You are a Senior Portfolio Analyst at ArthaAI. Your goal is to analyze financial news headlines "
            "concerning a fund house and synthesize their portfolio actions (specifically what they are buying and selling)."
        )
        
        user_prompt = f"""
Analyze the recent news headlines for **{fund_name}**:

{bullet_list}

Please output a structured report with:
1. **OVERALL SENTIMENT**: Bullet list/heading with a single sentence (e.g. Bullish, Neutral, or Bearish) and short rationale.
2. **PORTFOLIO TRANSACTIONS (BUYS & SELLS)**: 
   - Identify what stocks they have bought, sold, entered, or exited based on these headlines. 
   - Present this as a bulleted list with clear tags like **[BUY/ENTRY]** or **[SELL/EXIT]**.
   - If a headline does not state buys/sells, do not invent them. If no transactions are detected, write "No specific buys/sells reported in these headlines."
3. **EXECUTIVE SUMMARY**: A concise, 2-3 sentence synthesis of the news trend.

Format your response in clean, professional markdown, suitable for a high-fidelity investment terminal. Use bold font for stock names. Do not use generic greetings.
"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        resp = llm.invoke(messages)
        return resp.content
        
    except Exception as e:
        logger.error(f"Error during sentiment LLM analysis: {e}")
        return "⚠️ *Sentiment Analysis is temporarily unavailable (API Limit reached). Showing raw headlines below.*"
