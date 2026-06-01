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


