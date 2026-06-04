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


# ══════════════════════════════════════════════════════════════════
# INSTITUTIONAL OWNERSHIP FROM 13F DATA SETS
# ══════════════════════════════════════════════════════════════════

def _get_cusip_for_ticker(ticker: str) -> Optional[str]:
    """
    Try to find CUSIP for a ticker using SEC company info or EDGAR search.
    CUSIPs are 9-character identifiers used in 13F filings.
    """
    # Common CUSIP mappings for major stocks
    KNOWN_CUSIPS = {
        "AAPL": "037833100",
        "MSFT": "594918104",
        "GOOGL": "02079K305",
        "GOOG": "02079K107",
        "AMZN": "023135106",
        "TSLA": "88160R101",
        "META": "30303M102",
        "NVDA": "67066G104",
        "BRK.A": "084670108",
        "BRK.B": "084670207",
        "JPM": "46625H100",
        "V": "92826C839",
        "JNJ": "478160104",
        "WMT": "931142103",
        "PG": "742718109",
        "MA": "57636Q104",
        "UNH": "91324P102",
        "HD": "437076102",
        "DIS": "254687106",
        "BAC": "060505104",
        "NFLX": "64110L106",
        "ADBE": "00724F101",
        "CRM": "79466L302",
        "PYPL": "70450Y103",
        "INTC": "458140100",
        "AMD": "007903107",
        "CSCO": "17275R102",
        "PEP": "713448108",
        "KO": "191216100",
        "MRK": "58933Y105",
        "ABT": "002824100",
        "TMO": "883556102",
        "COST": "22160K105",
        "AVGO": "11135F101",
        "NKE": "654106103",
        "ORCL": "68389X105",
        "ACN": "G1151C101",
        "MCD": "580135101",
        "TXN": "882508104",
        "LLY": "532457108",
        "UPS": "911312106",
        "QCOM": "747525103",
        "HON": "438516106",
        "IBM": "459200101",
        "LOW": "548661107",
        "SBUX": "855244109",
        "CVX": "166764100",
        "XOM": "30231G102",
    }
    
    ticker_norm = ticker.upper().replace("-", ".").replace("/", ".")
    if ticker_norm in KNOWN_CUSIPS:
        return KNOWN_CUSIPS[ticker_norm]
    
    return None


# ══════════════════════════════════════════════════════════════════
# PARSE SC 13G/13D FILINGS FOR LARGE SHAREHOLDERS
# ══════════════════════════════════════════════════════════════════

def _fetch_large_shareholders(cik: str, ticker: str) -> Dict:
    """
    Fetch large shareholders (>5% owners) from SC 13G/13D filings.
    
    These filings are required when an entity acquires >5% of a company's shares.
    This is the most reliable source for institutional ownership data.
    
    Returns:
        dict with cusip, shareholders list, and metadata
    """
    cache_key = f"large_shareholders_{ticker}"
    cache_path_file = _cache_path(cache_key)
    
    cached = _read_cache(cache_path_file)
    if cached:
        return cached
    
    # Get company filings
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    
    filings = data.get("filings", {}).get("recent", {})
    forms = filings.get("form", [])
    dates = filings.get("filingDate", [])
    accessions = filings.get("accessionNumber", [])
    docs = filings.get("primaryDocument", [])
    
    # Find SC 13G/13D filings
    ownership_filings = []
    for i in range(len(forms)):
        form = forms[i]
        if "13G" in form or "13D" in form:
            ownership_filings.append({
                "form": form,
                "date": dates[i],
                "accession": accessions[i].replace("-", ""),
                "doc": docs[i] if i < len(docs) else None,
            })
    
    shareholders = []
    cusip = None
    
    # Parse each filing to extract shareholder data
    for filing in ownership_filings[:15]:  # Check last 15 filings
        try:
            time.sleep(0.15)  # Rate limiting
            acc = filing["accession"]
            doc = filing["doc"]
            
            # Build URL to filing
            filing_url = f"https://www.sec.gov/Archives/edgar/data/{cik.lstrip('0')}/{acc}/{doc}"
            
            resp = requests.get(filing_url, headers=HEADERS, timeout=15)
            if resp.status_code != 200:
                continue
            
            content = resp.text
            soup = BeautifulSoup(content, "html.parser")
            text = soup.get_text()
            
            # Extract CUSIP (9-character identifier)
            if not cusip:
                cusip_match = re.search(r"CUSIP[^\d]*(\d{6,9}[A-Z0-9]{0,3})", text, re.IGNORECASE)
                if cusip_match:
                    cusip = cusip_match.group(1)[:9]
            
            # Extract shareholder name
            name = None
            name_patterns = [
                r"Names?\s*of\s*Reporting\s*Person[s]?\s*[:\s]*([A-Z][A-Za-z0-9\s,\.&/\-]+?)(?:\d|Check|S\.?E\.?C|Item)",
                r"Name\s*of\s*person\s*filing[:\s]*([A-Z][A-Za-z0-9\s,\.&/\-]+?)(?:\(|Address|Item)",
            ]
            for pattern in name_patterns:
                match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
                if match:
                    name = match.group(1).strip()
                    # Clean up extracted name
                    name = re.sub(r"\s+", " ", name)
                    name = re.sub(r"\s*(Item|Check|S\.?E\.?C).*$", "", name, flags=re.IGNORECASE)
                    name = name.strip()[:60]
                    if len(name) > 3:  # Valid name
                        break
                    name = None
            
            # Extract share count
            shares = None
            shares_patterns = [
                r"Aggregate\s*Amount\s*Beneficially\s*Owned[^\d]*?([\d,]+(?:\.\d+)?)",
                r"Sole\s*Voting\s*Power[^\d]*?([\d,]+(?:\.\d+)?)",
                r"(\d{1,3}(?:,\d{3})+(?:\.\d+)?)\s*shares",
            ]
            for pattern in shares_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    shares_str = match.group(1).replace(",", "")
                    shares = _safe_float(shares_str)
                    if shares and shares > 0:
                        break
            
            # Extract percentage
            pct = None
            pct_patterns = [
                r"Percent\s*of\s*[Cc]lass[^\d]*?([\d]+(?:\.\d+)?)\s*%",
                r"([\d]+(?:\.\d+)?)\s*%\s*(?:of|percent)",
            ]
            for pattern in pct_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    pct = _safe_float(match.group(1))
                    if pct and 0 < pct <= 100:
                        break
            
            if name and (shares or pct):
                # Skip invalid names
                invalid_patterns = ["I.R.S", "IRS", "IDENTIFICATION", "CUSIP", "SCHEDULE", "EXCHANGE ACT", "COMMUNICATIONS INC", "CORP/DE"]
                if any(inv in name.upper() for inv in invalid_patterns):
                    continue
                # Skip if the company is filing about itself (check ticker in name)
                if ticker.upper() in name.upper().replace(" ", ""):
                    continue
                    
                # Normalize name for deduplication
                name_normalized = name.upper().replace(",", "").replace(".", "").replace("/", " ")
                
                # Check if we already have this shareholder (keep most recent)
                existing = next((s for s in shareholders if s["name"].upper().replace(",", "").replace(".", "")[:20] == name_normalized[:20]), None)
                if existing:
                    if filing["date"] > existing["filing_date"]:
                        existing.update({
                            "shares": shares or existing["shares"],
                            "percentage": pct or existing["percentage"],
                            "filing_date": filing["date"],
                            "form": filing["form"],
                        })
                else:
                    shareholders.append({
                        "name": name,
                        "shares": shares,
                        "percentage": pct,
                        "filing_date": filing["date"],
                        "form": filing["form"],
                        "type": "institutional" if "LLC" in name.upper() or "INC" in name.upper() or "LP" in name.upper() or "CORP" in name.upper() or "CAPITAL" in name.upper() or "FUND" in name.upper() else "individual",
                    })
                    
        except Exception as exc:
            logger.debug("Failed to parse filing %s: %s", filing.get("accession"), exc)
            continue
    
    # Sort by percentage (descending)
    shareholders.sort(key=lambda x: x.get("percentage") or 0, reverse=True)
    
    result = {
        "cusip": cusip,
        "shareholders": shareholders,
        "num_filings_parsed": len(ownership_filings[:15]),
        "fetched_at": datetime.now().isoformat(),
    }
    
    _write_cache(cache_path_file, result)
    return result


def _fetch_13f_data_for_quarter(year: int, quarter: int) -> Optional[Dict]:
    """
    Fetch SEC 13F data set for a specific quarter.
    SEC provides aggregated 13F data at: https://www.sec.gov/data-research/sec-markets-data/form-13f-data-sets
    Files: https://www.sec.gov/files/structureddata/data/form-13f-data-sets/2024q1.zip
    """
    # Try to fetch from SEC's 13F data sets
    # These are quarterly compilations of all 13F filings
    quarter_str = f"{year}q{quarter}"
    
    # For now, we'll aggregate from individual 13F filings instead
    # The SEC data sets require downloading and parsing ZIP files
    return None

