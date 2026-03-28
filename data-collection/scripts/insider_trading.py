"""
Insider Trading & Investor Tracking — Data Collection Module

Handles:
1. Form 4  — insider transactions per company (fetch_form4_transactions)
2. Form 13F — institutional portfolio holdings (fetch_13f_holdings, fetch_investor_filings)
3. Investor search via EDGAR company search (search_investors)

Caching:
  - File-based JSON cache in output/insider/ and output/investors/
  - Default TTL: 24 hours (configurable via INSIDER_CACHE_TTL_HOURS env var)
  - Cache is checked before every EDGAR request

EDGAR API notes (verified from live data):
  - Form 4 primaryDocument has XSLT prefix (e.g. "xslF345X05/file.xml") → strip it
  - 13F info table is a SEPARATE file from primary_doc.xml (found via filing index)
  - 13F <value> field is in US DOLLARS (verified: shares × price ≈ value)
  - transactionPricePerShare may be <footnoteId> (no price) for $0 awards/RSUs
"""

import os
import json
import time
import logging
import re
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# ── Graceful-stop flag — set this to abort any in-progress EDGAR fetch ──────
# Called automatically by the FastAPI shutdown hook (see insider_endpoints.py).
# Also checked each iteration so Ctrl-C from CLI breaks out immediately.
_stop_fetch = threading.Event()

# ── Config ──────────────────────────────────────────────────────
HEADERS = {"User-Agent": "financial-data-tool@example.com"}
CACHE_TTL_HOURS = int(os.environ.get("INSIDER_CACHE_TTL_HOURS", 24))

_SCRIPT_DIR = Path(__file__).parent
_PROJECT_ROOT = _SCRIPT_DIR.parent.parent  # data-collection/scripts -> project root
INSIDER_CACHE_DIR = _PROJECT_ROOT / ".api_cache" / "insider"
INVESTOR_CACHE_DIR = _PROJECT_ROOT / ".api_cache" / "investors"

INSIDER_CACHE_DIR.mkdir(parents=True, exist_ok=True)
INVESTOR_CACHE_DIR.mkdir(parents=True, exist_ok=True)


# ══════════════════════════════════════════════════════════════════
# FILE-BASED CACHE HELPERS
# ══════════════════════════════════════════════════════════════════

def _cache_path(directory: Path, key: str) -> Path:
    safe = re.sub(r"[^a-zA-Z0-9_\-]", "_", key)
    return directory / f"{safe}.json"


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
# SHARED EDGAR HELPERS
# ══════════════════════════════════════════════════════════════════

def _get_cik_from_ticker(ticker: str) -> str:
    """Resolve ticker → 10-digit zero-padded CIK. Cached in INSIDER_CACHE_DIR."""
    cache_path = _cache_path(INSIDER_CACHE_DIR, f"cik_{ticker.upper()}")
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


def _get_submissions(cik: str) -> dict:
    """
    Fetch all EDGAR submission data for a CIK including paginated older filings.
    Returns the full submissions dict with all filings merged into 'recent'.
    """
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    for old_file in data.get("filings", {}).get("files", []):
        old_url = "https://data.sec.gov/submissions/" + old_file["name"]
        try:
            old_resp = requests.get(old_url, headers=HEADERS, timeout=10)
            old_sub = old_resp.json()
            for col in old_sub:
                if col in data["filings"]["recent"]:
                    data["filings"]["recent"][col] += old_sub[col]
        except Exception as exc:
            logger.warning("Could not load extra filings page %s: %s", old_file["name"], exc)

    return data


def _xml_val(element, tag: str, default=None):
    """
    Extract text from <tag><value>...</value></tag> or plain <tag>...</tag>.
    Returns default when tag is missing or contains only <footnoteId/>.
    """
    if element is None:
        return default
    found = element.find(tag)
    if found is None:
        return default
    value_child = found.find("value")
    if value_child is not None:
        text = (value_child.text or "").strip()
        return text if text else default
    text = (found.text or "").strip()
    return text if text else default


def _safe_float(s) -> Optional[float]:
    if s is None:
        return None
    try:
        return float(str(s).replace(",", "").strip())
    except (ValueError, TypeError):
        return None


# ══════════════════════════════════════════════════════════════════
# FORM 4 PARSING
# ══════════════════════════════════════════════════════════════════

_TXN_CODE_MAP = {
    "P": "Purchase", "S": "Sale", "A": "Award/Grant",
    "D": "Return to Issuer", "F": "Tax Withholding",
    "M": "Option/RSU Exercise", "C": "Conversion", "G": "Gift",
    "J": "Other", "I": "Discretionary", "K": "Equity Conversion",
    "L": "Small Acquisition", "O": "Option Exercise (OTM)",
    "U": "Tender Disposition", "W": "Inheritance",
    "X": "Option Exercise (ITM)", "Z": "Voting Trust",
    "V": "Voluntary", "E": "Expiration", "H": "Expiration (ITM)",
}


def _normalize_txn_type(code: str, acquired_disposed: str) -> str:
    code_up = (code or "").upper()
    if code_up == "P":
        return "Buy"
    if code_up == "S":
        return "Sell"
    base = _TXN_CODE_MAP.get(code_up, f"Other ({code})")
    if acquired_disposed == "A":
        return f"{base} (Acquired)"
    if acquired_disposed == "D":
        return f"{base} (Disposed)"
    return base

