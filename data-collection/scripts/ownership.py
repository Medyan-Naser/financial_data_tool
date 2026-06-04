"""
Company Ownership Data Collection Module

Fetches and aggregates ownership data for a company from SEC EDGAR:
1. Institutional Ownership — aggregated from Form 13F filings (who holds this stock)
2. Insider Ownership — derived from Form 3/4/5 filings
3. Large Shareholders (>5%) — from Schedule 13D/13G filings

Data Sources:
- SEC EDGAR API for company submissions
- Form 13F data sets from SEC for institutional holdings
- Insider transaction data for insider ownership estimates

Caching:
- File-based JSON cache in .api_cache/ownership/
- Default TTL: 24 hours
"""

import os
import json
import time
import logging
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any
from collections import defaultdict

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# ── Config ──────────────────────────────────────────────────────
HEADERS = {"User-Agent": "financial-data-tool@example.com"}
CACHE_TTL_HOURS = int(os.environ.get("OWNERSHIP_CACHE_TTL_HOURS", 24))

_SCRIPT_DIR = Path(__file__).parent
_PROJECT_ROOT = _SCRIPT_DIR.parent.parent
OWNERSHIP_CACHE_DIR = _PROJECT_ROOT / ".api_cache" / "ownership"
OWNERSHIP_CACHE_DIR.mkdir(parents=True, exist_ok=True)


# ══════════════════════════════════════════════════════════════════
# CACHE HELPERS
# ══════════════════════════════════════════════════════════════════

def _cache_path(key: str) -> Path:
    safe = re.sub(r"[^a-zA-Z0-9_\-]", "_", key)
    return OWNERSHIP_CACHE_DIR / f"{safe}.json"


def _read_cache(path: Path) -> Optional[Dict]:
    if not path.exists():
        return None
    try:
        with open(path) as f:
            data = json.load(f)
        cached_at = data.get("_cached_at")
        if not cached_at:
            return None
        age = datetime.now() - datetime.fromisoformat(cached_at)
        if age > timedelta(hours=CACHE_TTL_HOURS):
            logger.debug("Cache expired for %s", path.name)
            return None
        return data
    except Exception as exc:
        logger.warning("Cache read failed for %s: %s", path, exc)
        return None


def _write_cache(path: Path, data: Dict) -> None:
    try:
        data["_cached_at"] = datetime.now().isoformat()
        with open(path, "w") as f:
            json.dump(data, f)
    except Exception as exc:
        logger.warning("Cache write failed for %s: %s", path, exc)


# ══════════════════════════════════════════════════════════════════
# EDGAR HELPERS
# ══════════════════════════════════════════════════════════════════

def _get_cik_from_ticker(ticker: str) -> str:
    """Resolve ticker → 10-digit zero-padded CIK."""
    cache_path = _cache_path(f"cik_{ticker.upper()}")
    cached = _read_cache(cache_path)
    if cached:
        return cached["cik"]

    resp = requests.get(
        "https://www.sec.gov/files/company_tickers.json",
        headers=HEADERS,
        timeout=10,
    )
    resp.raise_for_status()
    ticker_norm = ticker.upper().replace(".", "-")
    for company in resp.json().values():
        if company["ticker"] == ticker_norm:
            cik = str(company["cik_str"]).zfill(10)
            _write_cache(cache_path, {"cik": cik})
            return cik
    raise ValueError(f"Ticker '{ticker}' not found in SEC database")


def _get_company_info(cik: str) -> Dict:
    """Get company name and other basic info from EDGAR."""
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    return {
        "name": data.get("name", ""),
        "cik": cik,
        "sic": data.get("sic", ""),
        "sicDescription": data.get("sicDescription", ""),
        "tickers": data.get("tickers", []),
        "exchanges": data.get("exchanges", []),
    }


def _safe_float(s) -> Optional[float]:
    if s is None:
        return None
    try:
        return float(str(s).replace(",", "").strip())
    except (ValueError, TypeError):
        return None

