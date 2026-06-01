"""
src/news_service.py
------------------
Fetches Google News RSS feed for mutual funds.
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

# LLM sentiment analysis function removed.
