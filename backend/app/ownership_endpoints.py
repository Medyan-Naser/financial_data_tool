"""
Company Ownership API Endpoints

Provides endpoints for fetching company ownership data:
- Who owns a company (institutional vs insider vs retail)
- Top institutional holders
- Insider holdings
- Historical ownership trends

Endpoints:
  GET /api/ownership/{ticker}         — Current ownership breakdown
  GET /api/ownership/{ticker}/history — Historical ownership data
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

# ── Import data-collection module ────────────────────────────────
_DC_PATH = Path(__file__).parent.parent.parent / "data-collection" / "scripts"
if str(_DC_PATH) not in sys.path:
    sys.path.insert(0, str(_DC_PATH))

try:
    from ownership import fetch_company_ownership, fetch_ownership_history
    _DC_AVAILABLE = True
except ImportError as _err:
    logger.error("Could not import ownership from data-collection: %s", _err)
    _DC_AVAILABLE = False

# ── Backend cache layer ──────────────────────────────────────────
ownership_cache = CacheManager(namespace="ownership", expiry_hours=24)


def _dc_check():
    if not _DC_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Ownership data collection module unavailable. Check server logs.",
        )


# ══════════════════════════════════════════════════════════════════
# OWNERSHIP ENDPOINTS
# ══════════════════════════════════════════════════════════════════

@router.get("/api/ownership/{ticker}")
async def get_company_ownership(
    ticker: str,
    force_refresh: bool = Query(default=False),
):
    """
    Get current ownership breakdown for a company.
    
    Returns:
    - Institutional ownership percentage and top holders
    - Insider ownership percentage and top insiders
    - Retail/Other ownership percentage
    - Shares outstanding (when available)
    
    Data sources:
    - Form 13F filings for institutional ownership
    - Form 3/4/5 filings for insider ownership
    """
    _dc_check()
    ticker = ticker.upper()
    cache_key = f"ownership_{ticker}"
    
    if not force_refresh:
        cached = ownership_cache.get(cache_key)
        if cached:
            return JSONResponse({**cached, "from_cache": True})
    
    try:
        result = fetch_company_ownership(ticker, force_refresh=force_refresh)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        logger.error("Error fetching ownership for %s: %s", ticker, exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching ownership data: {exc}")
    
    ownership_cache.set(cache_key, result)
    return JSONResponse({**result, "from_cache": False})


@router.get("/api/ownership/{ticker}/history")
async def get_ownership_history(
    ticker: str,
    quarters: int = Query(default=8, ge=1, le=20),
    force_refresh: bool = Query(default=False),
):
    """
    Get historical ownership data over multiple quarters.
    
    Returns time-series of ownership percentages for charting.
    """
    _dc_check()
    ticker = ticker.upper()
    cache_key = f"ownership_history_{ticker}_{quarters}"
    
    if not force_refresh:
        cached = ownership_cache.get(cache_key)
        if cached:
            return JSONResponse({**cached, "from_cache": True})
    
    try:
        result = fetch_ownership_history(ticker, num_quarters=quarters, force_refresh=force_refresh)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        logger.error("Error fetching ownership history for %s: %s", ticker, exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching ownership history: {exc}")
    
    ownership_cache.set(cache_key, result)
    return JSONResponse({**result, "from_cache": False})
