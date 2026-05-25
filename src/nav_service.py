"""
src/nav_service.py
------------------
Live NAV fetcher using the free MFAPI (https://api.mfapi.in).
- No API key required
- Updated 6x daily by AMFI
- Falls back gracefully to static metadata if the API is unreachable
"""

import requests
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

# MFAPI base URL
MFAPI_BASE = "https://api.mfapi.in/mf"

# Mapping from internal fund_id → MFAPI scheme code (Direct Growth plans)
MFAPI_SCHEME_CODES = {
    "sbi_bluechip":     119598,   # SBI Large Cap Fund - Direct Plan - Growth
    "parag_parikh_flexi": 122639, # Parag Parikh Flexi Cap Fund - Direct Plan - Growth
    "hdfc_top100":      119018,   # HDFC Large Cap Fund - Growth Option - Direct Plan
    "icici_prudential": 120586,   # ICICI Prudential Large Cap Fund - Direct Plan - Growth
    "mirae_asset":      118825,   # Mirae Asset Large Cap Fund - Direct Plan - Growth
}

# In-memory NAV cache: {fund_id: {"nav": str, "date": str, "change": str, "change_positive": bool}}
_nav_cache: dict = {}


def fetch_latest_nav(fund_id: str, timeout: int = 4) -> Optional[dict]:
    """
    Fetches the latest NAV for a fund from MFAPI.
    Returns a dict with keys: nav, date, change, change_positive
    Returns None on failure (caller should use static fallback).
    """
    if fund_id not in MFAPI_SCHEME_CODES:
        logger.warning(f"No MFAPI scheme code configured for fund_id: {fund_id}")
        return None

    scheme_code = MFAPI_SCHEME_CODES[fund_id]

    # Return from cache if already fetched this session
    if fund_id in _nav_cache:
        logger.info(f"Returning cached NAV for {fund_id}")
        return _nav_cache[fund_id]

    try:
        # Fetch latest NAV
        url = f"{MFAPI_BASE}/{scheme_code}/latest"
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()

        if data.get("status") != "SUCCESS" or not data.get("data"):
            logger.warning(f"MFAPI returned non-success for {fund_id}: {data}")
            return None

        latest = data["data"][0]
        nav_val = float(latest["nav"])
        nav_date = latest["date"]  # format: "DD-MM-YYYY"

        # Fetch previous NAV to compute daily change
        history_url = f"{MFAPI_BASE}/{scheme_code}"
        hist_resp = requests.get(history_url, timeout=timeout, params={"startDate": "", "endDate": ""})
        hist_resp.raise_for_status()
        hist_data = hist_resp.json()

        change_str = "N/A"
        change_positive = True
        if hist_data.get("data") and len(hist_data["data"]) >= 2:
            prev_nav = float(hist_data["data"][1]["nav"])
            change_pct = ((nav_val - prev_nav) / prev_nav) * 100
            sign = "+" if change_pct >= 0 else ""
            change_str = f"{sign}{change_pct:.2f}% (1D)"
            change_positive = change_pct >= 0

        result = {
            "nav": f"₹ {nav_val:,.2f}",
            "date": nav_date,
            "change": change_str,
            "change_positive": change_positive,
        }

        _nav_cache[fund_id] = result
        logger.info(f"Fetched live NAV for {fund_id}: {result['nav']} on {nav_date}")
        return result

    except requests.exceptions.Timeout:
        logger.warning(f"MFAPI timeout for {fund_id} (scheme {scheme_code})")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"MFAPI request error for {fund_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching NAV for {fund_id}: {e}")
        return None


def get_live_nav(fund_id: str, static_nav: str, static_change: str, static_change_positive: bool) -> dict:
    """
    Returns live NAV data merged with static fallback.
    Always returns a complete dict with nav, change, change_positive, date, is_live.
    """
    live = fetch_latest_nav(fund_id)
    if live:
        return {**live, "is_live": True}
    else:
        return {
            "nav": static_nav,
            "change": static_change,
            "change_positive": static_change_positive,
            "date": "Static",
            "is_live": False,
        }


def clear_nav_cache():
    """Clears the in-memory NAV cache (useful for manual refresh)."""
    global _nav_cache
    _nav_cache = {}
    logger.info("NAV cache cleared.")
