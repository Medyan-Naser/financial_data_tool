"""
Insider Trading & Investor Tracking API Endpoints

Thin backend layer — all data collection and parsing logic lives in:
  data-collection/scripts/insider_trading.py

This module:
  1. Adds the data-collection scripts to sys.path
  2. Imports fetch_* functions from insider_trading.py
  3. Wraps them in FastAPI endpoints with a backend CacheManager layer

Endpoints:
  GET /api/insider/{ticker}            — Form 4 transactions (non-deriv by default)
  GET /api/investors/search?q=         — EDGAR investor name search
  GET /api/investors/{cik}/filings     — List 13F-HR filing dates
  GET /api/investors/{cik}/holdings    — Latest (or specific) 13F holdings
  GET /api/investors/{cik}/history     — Portfolio % time-series for ChartManager
"""

import sys
import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from .cache_manager import CacheManager

logger = logging.getLogger(__name__)
router = APIRouter()

# ── Import data-collection module (adds scripts/ to sys.path) ────
_DC_PATH = Path(__file__).parent.parent.parent / "data-collection" / "scripts"
if str(_DC_PATH) not in sys.path:
    sys.path.insert(0, str(_DC_PATH))

try:
    from insider_trading import (
        fetch_form4_transactions,
        search_investors as _search_investors,
        fetch_investor_filings,
        fetch_13f_holdings,
        fetch_13f_history,
    )
    _DC_AVAILABLE = True
except ImportError as _err:
    logger.error("Could not import insider_trading from data-collection: %s", _err)
    _DC_AVAILABLE = False

# ── Backend cache layer (fast lookup before hitting data-collection) ──
insider_cache = CacheManager(namespace="insider", expiry_hours=24)
investor_cache = CacheManager(namespace="investors", expiry_hours=24)


def _dc_check():
    if not _DC_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Data collection module unavailable. Check server logs.",
        )


# ══════════════════════════════════════════════════════════════════
# INSIDER TRADING — Form 4
# ══════════════════════════════════════════════════════════════════

@router.get("/api/insider/{ticker}")
async def get_insider_transactions(
    ticker: str,
    years: int = Query(default=10, ge=1, le=20),
    force_refresh: bool = Query(default=False),
):
    """
    Return Form 4 insider transactions for a company ticker.

    Strategy: always fetches and caches the full MAX dataset ({ticker}_ALL),
    then filters locally to the requested `years`. First call is slow;
    subsequent calls for any year range are instant cache hits.

    Args:
        years: How many years back to return (1–20, default 5)
        force_refresh: Re-fetch all filings from EDGAR
    """
    _dc_check()
    ticker = ticker.upper()
    # Backend cache key includes years so different year requests are cached separately
    cache_key = f"insider_{ticker}_{years}y"

    if not force_refresh:
        cached = insider_cache.get(cache_key)
        if cached:
            return JSONResponse({**cached, "from_cache": True})

    try:
        result = fetch_form4_transactions(
            ticker,
            years=years,
            force_refresh=force_refresh,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        logger.error("Error fetching Form 4 for %s: %s", ticker, exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching insider data: {exc}")

    insider_cache.set(cache_key, result)
    return JSONResponse({**result, "from_cache": False})


# ══════════════════════════════════════════════════════════════════
# INVESTOR TRACKING — Form 13F
# ══════════════════════════════════════════════════════════════════

@router.get("/api/investors/search")
async def search_investors_endpoint(q: str = Query(..., min_length=2)):
    """Search EDGAR for institutional investors by name."""
    _dc_check()
    cache_key = f"inv_search_{q.lower().replace(' ', '_')[:60]}"
    cached = investor_cache.get(cache_key)
    if cached:
        return JSONResponse({**cached, "from_cache": True})

    try:
        result = _search_investors(q)
    except Exception as exc:
        logger.error("Investor search error for '%s': %s", q, exc)
        raise HTTPException(status_code=502, detail=f"EDGAR search error: {exc}")

    investor_cache.set(cache_key, result)
    return JSONResponse({**result, "from_cache": False})


@router.get("/api/investors/{cik}/filings")
async def get_investor_filings(cik: str, force_refresh: bool = Query(default=False)):
    """List all 13F-HR filing dates for an investor CIK."""
    _dc_check()
    cik_padded = cik.zfill(10)
    cache_key = f"inv_filings_{cik_padded}"
    if not force_refresh:
        cached = investor_cache.get(cache_key)
        if cached:
            return JSONResponse({**cached, "from_cache": True})

    try:
        result = fetch_investor_filings(cik_padded, force_refresh=force_refresh)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"EDGAR error: {exc}")

    investor_cache.set(cache_key, result)
    return JSONResponse({**result, "from_cache": False})


@router.get("/api/investors/{cik}/holdings")
async def get_investor_holdings(
    cik: str,
    filing_date: Optional[str] = Query(default=None),
    force_refresh: bool = Query(default=False),
):
    """
    Return 13F portfolio holdings for an investor.
    Defaults to the most recent 13F-HR filing.
    Values are in US dollars (verified against live Berkshire data).
    """
    _dc_check()
    cik_padded = cik.zfill(10)
    cache_key = f"inv_holdings_{cik_padded}_{filing_date or 'latest'}"

    if not force_refresh:
        cached = investor_cache.get(cache_key)
        if cached:
            return JSONResponse({**cached, "from_cache": True})

    try:
        result = fetch_13f_holdings(cik_padded, filing_date=filing_date, force_refresh=force_refresh)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        logger.error("Error fetching 13F holdings for CIK %s: %s", cik, exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching holdings: {exc}")

    investor_cache.set(cache_key, result)
    return JSONResponse({**result, "from_cache": False})


@router.get("/api/investors/{cik}/history")
async def get_investor_history(
    cik: str,
    num_filings: int = Query(default=6, ge=1, le=20),
    top_n: int = Query(default=15, ge=3, le=30),
    force_refresh: bool = Query(default=False),
):
    """
    Return portfolio weight time-series for ChartManager.

    Fetches the last `num_filings` 13F filings and tracks how the top-N
    holdings' portfolio percentages changed over time.

    Response shape:
      { investor_name, columns: [date,...], rows: [{name, values:[pct,...]}, ...],
        all_holdings_latest, total_portfolio_value, available_filings }
    """
    _dc_check()
    cik_padded = cik.zfill(10)
    cache_key = f"inv_history_{cik_padded}_{num_filings}_{top_n}"

    if not force_refresh:
        cached = investor_cache.get(cache_key)
        if cached:
            return JSONResponse({**cached, "from_cache": True})

    try:
        result = fetch_13f_history(
            cik_padded,
            num_filings=num_filings,
            top_n=top_n,
            force_refresh=force_refresh,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        logger.error("Error fetching 13F history for CIK %s: %s", cik, exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching history: {exc}")

    investor_cache.set(cache_key, result)
    return JSONResponse({**result, "from_cache": False})
