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
    "parag_parikh_flexi":   122639, # Parag Parikh Flexi Cap Fund - Direct Plan - Growth
    "pp_tax_saver":         147481, # Parag Parikh ELSS Tax Saver Fund - Direct Plan - Growth
    "pp_conservative":      148958, # Parag Parikh Conservative Hybrid Fund - Direct Plan - Growth
    "pp_liquid":            143269, # Parag Parikh Liquid Fund - Direct Plan - Growth
    "pp_dynamic":           152468, # Parag Parikh Dynamic Asset Allocation Fund - Direct Plan - Growth
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


def fetch_nav_history(fund_id: str, period: str = "1Y", timeout: int = 6) -> Optional[object]:
    """
    Fetches historical NAV data for a fund from MFAPI and returns a
    pandas DataFrame with columns ['date', 'nav'] filtered to the requested period.

    period options: '1M', '6M', '1Y', '3Y', '5Y', 'All'
    Returns None on failure.
    """
    try:
        import pandas as pd
        from datetime import timedelta
    except ImportError:
        logger.error("pandas is required for fetch_nav_history")
        return None

    if fund_id not in MFAPI_SCHEME_CODES:
        return None

    scheme_code = MFAPI_SCHEME_CODES[fund_id]
    cache_key = f"history_{fund_id}"

    # Use session-level cache for history too
    if cache_key in _nav_cache:
        df_all = _nav_cache[cache_key]
    else:
        try:
            url = f"{MFAPI_BASE}/{scheme_code}"
            resp = requests.get(url, timeout=timeout)
            resp.raise_for_status()
            data = resp.json()

            if data.get("status") != "SUCCESS" or not data.get("data"):
                return None

            # MFAPI returns newest first — reverse to oldest first for charting
            records = data["data"]
            df_all = pd.DataFrame(records)
            df_all["date"] = pd.to_datetime(df_all["date"], format="%d-%m-%Y")
            df_all["nav"] = df_all["nav"].astype(float)
            df_all = df_all.sort_values("date").reset_index(drop=True)

            _nav_cache[cache_key] = df_all
            logger.info(f"Fetched {len(df_all)} historical NAV records for {fund_id}")

        except Exception as e:
            logger.error(f"Failed to fetch history for {fund_id}: {e}")
            return None

    # Filter by period
    latest_date = df_all["date"].max()
    period_map = {
        "1M":  latest_date - pd.DateOffset(months=1),
        "6M":  latest_date - pd.DateOffset(months=6),
        "1Y":  latest_date - pd.DateOffset(years=1),
        "3Y":  latest_date - pd.DateOffset(years=3),
        "5Y":  latest_date - pd.DateOffset(years=5),
        "All": df_all["date"].min(),
    }
    start_date = period_map.get(period, period_map["1Y"])
    df_filtered = df_all[df_all["date"] >= start_date].copy()
    return df_filtered


def clear_nav_cache():
    """Clears the in-memory NAV cache (useful for manual refresh)."""
    global _nav_cache
    _nav_cache = {}
    logger.info("NAV cache cleared.")
