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


def _parse_form4_xml(xml_text: str, filing_date: str) -> List[Dict]:
    """Parse a Form 4 XML document → list of transaction dicts."""
    soup = BeautifulSoup(xml_text, "lxml-xml")
    transactions: List[Dict] = []

    owner = soup.find("reportingOwner")
    if not owner:
        return []

    owner_name = owner_cik = ""
    role_parts: List[str] = []

    owner_id = owner.find("reportingOwnerId")
    if owner_id:
        name_tag = owner_id.find("rptOwnerName")
        owner_name = name_tag.text.strip() if name_tag else ""
        cik_tag = owner_id.find("rptOwnerCik")
        owner_cik = cik_tag.text.strip() if cik_tag else ""

    rel = owner.find("reportingOwnerRelationship")
    if rel:
        def _is1(tag):
            t = rel.find(tag)
            return t is not None and (t.text or "").strip() == "1"

        if _is1("isDirector"):
            role_parts.append("Director")
        if _is1("isOfficer"):
            title_tag = rel.find("officerTitle")
            title = title_tag.text.strip() if title_tag else ""
            role_parts.append(f"Officer ({title})" if title else "Officer")
        if _is1("isTenPercentOwner"):
            role_parts.append("10% Owner")

    role_str = ", ".join(role_parts) if role_parts else "Insider"
    period_tag = soup.find("periodOfReport")
    period = period_tag.text.strip() if period_tag else filing_date

    def _parse_txn(txn_el, is_derivative: bool) -> Optional[Dict]:
        security = _xml_val(txn_el, "securityTitle") or "Common Stock"
        txn_date = _xml_val(txn_el, "transactionDate") or period

        coding = txn_el.find("transactionCoding")
        txn_code = ""
        if coding:
            ct = coding.find("transactionCode")
            txn_code = ct.text.strip() if ct else ""

        amounts = txn_el.find("transactionAmounts")
        shares = price = None
        acquired_disposed = ""
        if amounts:
            shares = _safe_float(_xml_val(amounts, "transactionShares"))
            price = _safe_float(_xml_val(amounts, "transactionPricePerShare"))
            acquired_disposed = _xml_val(amounts, "transactionAcquiredDisposedCode") or ""

        post = txn_el.find("postTransactionAmounts")
        shares_after = (
            _safe_float(_xml_val(post, "sharesOwnedFollowingTransaction")) if post else None
        )

        txn_type = _normalize_txn_type(txn_code, acquired_disposed)
        total_value = (
            round(shares * price, 2)
            if shares is not None and price is not None and price > 0
            else None
        )

        return {
            "insider_name": owner_name,
            "insider_cik": owner_cik,
            "insider_role": role_str,
            "security_title": security,
            "transaction_type": txn_type,
            "transaction_code": txn_code,
            "shares": shares,
            "price_per_share": price,
            "total_value": total_value,
            "acquired_disposed": acquired_disposed,
            "transaction_date": txn_date,
            "filing_date": filing_date,
            "shares_after_transaction": shares_after,
            "is_derivative": is_derivative,
        }

    ndt = soup.find("nonDerivativeTable")
    if ndt:
        for txn in ndt.find_all("nonDerivativeTransaction"):
            parsed = _parse_txn(txn, False)
            if parsed:
                transactions.append(parsed)

    dt = soup.find("derivativeTable")
    if dt:
        for txn in dt.find_all("derivativeTransaction"):
            parsed = _parse_txn(txn, True)
            if parsed:
                transactions.append(parsed)

    return transactions


def _fetch_form4_xml(cik: str, accession_number: str, primary_doc: str) -> Optional[str]:
    """Fetch raw Form 4 XML text from EDGAR."""
    acc_clean = accession_number.replace("-", "")
    cik_int = str(int(cik))
    doc_filename = primary_doc.split("/")[-1] if "/" in primary_doc else primary_doc
    url = f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{acc_clean}/{doc_filename}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        return resp.text
    except Exception as exc:
        logger.warning("Failed to fetch Form 4 %s: %s", accession_number, exc)
        return None


# ══════════════════════════════════════════════════════════════════
# PUBLIC: FORM 4 — INSIDER TRANSACTIONS
# ══════════════════════════════════════════════════════════════════

# How many years back to collect Form 4 filings for the full MAX cache
_FORM4_MAX_YEARS = 10


def _fetch_form4_all(ticker: str) -> Dict:
    """
    Fetch Form 4 filings for a ticker going back _FORM4_MAX_YEARS years.
    Results are saved in the MAX cache (key: {ticker}_ALL).
    This is the "collect once, filter locally" function — never called directly
    by users; always goes through fetch_form4_transactions().
    """
    ticker = ticker.upper()
    max_cutoff = (datetime.now() - timedelta(days=_FORM4_MAX_YEARS * 365)).strftime("%Y-%m-%d")
    logger.info("Fetching Form 4 MAX data for %s (last %d years, cutoff %s)", ticker, _FORM4_MAX_YEARS, max_cutoff)

    cik = _get_cik_from_ticker(ticker)
    subs = _get_submissions(cik)
    filings = subs.get("filings", {}).get("recent", {})
    company_name = subs.get("name", ticker)

    forms = filings.get("form", [])
    accessions = filings.get("accessionNumber", [])
    filing_dates = filings.get("filingDate", [])
    primary_docs = filings.get("primaryDocument", [])

    # Filter by form type AND date — only fetch XMLs within the year window
    form4_filings = [
        {
            "accessionNumber": accessions[i],
            "filingDate": filing_dates[i],
            "primaryDocument": primary_docs[i] if i < len(primary_docs) else "",
        }
        for i, form in enumerate(forms)
        if form in ("4", "4/A")
        and i < len(accessions)
        and filing_dates[i] >= max_cutoff
    ]

    all_transactions: List[Dict] = []
    parse_errors = 0

    try:
        for idx, filing in enumerate(form4_filings):
            if _stop_fetch.is_set():
                logger.info("Fetch of %s stopped early at filing %d/%d", ticker, idx, len(form4_filings))
                break
            if not filing["primaryDocument"] or not filing["accessionNumber"]:
                continue
            xml_text = _fetch_form4_xml(cik, filing["accessionNumber"], filing["primaryDocument"])
            if xml_text:
                txns = _parse_form4_xml(xml_text, filing["filingDate"])
                all_transactions.extend(txns)
            else:
                parse_errors += 1

            # Respect SEC rate limit (~5 req/s burst, 10/s sustained)
            if idx % 5 == 4:
                time.sleep(0.2)
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt: stopping Form 4 fetch for %s, collected %d txns so far", ticker, len(all_transactions))

    all_transactions.sort(key=lambda x: x.get("transaction_date") or "", reverse=True)

    return {
        "ticker": ticker,
        "cik": cik,
        "company_name": company_name,
        "transactions": all_transactions,           # ALL transactions, unfiltered
        "total_filings_parsed": len(form4_filings),
        "parse_errors": parse_errors,
        "fetched_at": datetime.now().isoformat(),
    }


def fetch_form4_transactions(
    ticker: str,
    years: int = 5,
    force_refresh: bool = False,
) -> Dict:
    """
    Fetch Form 4 insider transactions for a company.

    Strategy (mirrors stock_price.py):
      1. Check if the full MAX cache ({ticker}_ALL) exists.
      2. If not (or force_refresh), call _fetch_form4_all() and cache ALL filings.
      3. Filter the cached full dataset by `years` (how many years back to return).

    This means the first call is slow (fetches everything), but subsequent calls
    for any year range are instant cache hits with local filtering.

    Args:
        ticker: Stock ticker symbol (e.g., "AAPL")
        years: How many years back to return transactions for (filters local cache)
        force_refresh: Re-fetch from EDGAR and overwrite the full cache

    Returns:
        dict with keys: ticker, cik, company_name, transactions,
                        total_filings_parsed, parse_errors,
                        requested_years, cutoff_date, from_cache, fetched_at
    """
    ticker = ticker.upper()
    years = max(1, years)

    # ── Full-data (MAX) cache — keyed as {TICKER}_ALL ──────────────────────
    all_cache_path = _cache_path(INSIDER_CACHE_DIR, f"{ticker}_ALL")

    if not force_refresh:
        full_cached = _read_cache(all_cache_path)
    else:
        full_cached = None

    if full_cached is None:
        full_cached = _fetch_form4_all(ticker)
        _write_cache(all_cache_path, full_cached)
        logger.info("Cached Form 4 MAX data for %s (%d txns)", ticker, len(full_cached["transactions"]))
    else:
        logger.info("Cache hit for insider %s (full data, filtering to %d years)", ticker, years)

    # ── Filter by requested year range ─────────────────────────────────────
    cutoff = (datetime.now() - timedelta(days=years * 365)).strftime("%Y-%m-%d")
    all_txns = full_cached.get("transactions", [])
    filtered = [
        t for t in all_txns
        if (t.get("transaction_date") or t.get("filing_date") or "9999-12-31") >= cutoff
    ]

    return {
        **full_cached,
        "transactions": filtered,
        "requested_years": years,
        "cutoff_date": cutoff,
        "total_cached_transactions": len(all_txns),
        "from_cache": True,
    }


# ══════════════════════════════════════════════════════════════════
# FORM 13F PARSING
# ══════════════════════════════════════════════════════════════════

def _find_13f_info_table_url(cik: str, accession_number: str) -> Optional[str]:
    """
    Locate the 13F information table **raw** XML file URL within a filing.

    The filing index contains two flavours of the info table link:
      - xslForm13F_X02/50240.xml  → XSLT-styled (renders as HTML) — SKIP
      - 50240.xml                  → raw XML we want

    Strategy:
      1. Parse index HTML, find rows with "INFORMATION TABLE" text.
         Prefer links whose text ends in .xml (raw) over those ending in .html.
      2. Fallback: any .xml not named primary_doc and not under xsl* path.
      3. Last resort: probe common filenames.
    """
    acc_clean = accession_number.replace("-", "")
    cik_int = str(int(cik))
    base_url = f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{acc_clean}"
    index_url = f"{base_url}/{accession_number}-index.htm"

    def _resolve(href: str) -> str:
        if href.startswith("/"):
            return f"https://www.sec.gov{href}"
        if href.startswith("http"):
            return href
        return f"{base_url}/{href}"

    def _is_raw_xml(href: str) -> bool:
        """True if the href points to raw XML (not an XSLT wrapper)."""
        lower = href.lower()
        if not lower.endswith(".xml"):
            return False
        # Skip XSLT-prefixed paths (e.g. xslForm13F_X02/..., xslF345X05/...)
        parts = href.split("/")
        if len(parts) > 1 and parts[-2].lower().startswith("xsl"):
            return False
        return True

    try:
        resp = requests.get(index_url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # Pass 1: rows with "INFORMATION TABLE" — collect raw .xml links
        info_table_links = []
        for row in soup.find_all("tr"):
            cells = row.find_all("td")
            row_text = " ".join(c.text.upper() for c in cells)
            if "INFORMATION TABLE" in row_text:
                for cell in cells:
                    for link in cell.find_all("a", href=True):
                        href = link["href"]
                        if _is_raw_xml(href):
                            info_table_links.append(_resolve(href))

        if info_table_links:
            return info_table_links[0]

        # Pass 2: any raw .xml not named primary_doc
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if _is_raw_xml(href) and "primary_doc" not in href.lower():
                return _resolve(href)

    except Exception as exc:
        logger.warning("Could not fetch 13F index for %s: %s", accession_number, exc)

    # Last resort: probe known filenames
    for fname in ["informationtable.xml", "infotable.xml", "form13finfotable.xml"]:
        url = f"{base_url}/{fname}"
        try:
            r = requests.head(url, headers=HEADERS, timeout=5)
            if r.status_code == 200:
                return url
        except Exception:
            pass

    return None


def _parse_13f_xml(xml_text: str) -> List[Dict]:
    """Parse 13F information table XML → list of holding dicts."""
    soup = BeautifulSoup(xml_text, "lxml-xml")
    holdings: List[Dict] = []

    for entry in soup.find_all("infoTable"):
        name_tag = entry.find("nameOfIssuer")
        cusip_tag = entry.find("cusip")
        value_tag = entry.find("value")
        title_tag = entry.find("titleOfClass")
        put_call_tag = entry.find("putCall")

        company_name = name_tag.text.strip() if name_tag else ""
        cusip = cusip_tag.text.strip() if cusip_tag else ""
        title = title_tag.text.strip() if title_tag else ""
        put_call = put_call_tag.text.strip() if (put_call_tag and put_call_tag.text) else None
        value = _safe_float(value_tag.text) if value_tag else None  # US dollars

        shr_amt = entry.find("shrsOrPrnAmt")
        shares = shares_type = None
        if shr_amt:
            shr_tag = shr_amt.find("sshPrnamt")
            type_tag = shr_amt.find("sshPrnamtType")
            shares = _safe_float(shr_tag.text) if shr_tag else None
            shares_type = type_tag.text.strip() if type_tag else ""

        holdings.append({
            "company_name": company_name,
            "cusip": cusip,
            "title_of_class": title,
            "value": value,        # dollars
            "shares": shares,
            "shares_type": shares_type,
            "put_call": put_call,
            "portfolio_pct": 0.0,  # filled in by caller
        })

    return holdings


def _aggregate_holdings(holdings: List[Dict]) -> List[Dict]:
    """
    Aggregate duplicate CUSIPs (some investors report multiple managers for same stock).
    Sums value and shares per CUSIP, keeps first company_name.
    """
    agg: Dict[str, Dict] = {}
    for h in holdings:
        key = h["cusip"] or h["company_name"]
        if key not in agg:
            agg[key] = dict(h)
        else:
            agg[key]["value"] = (agg[key]["value"] or 0) + (h["value"] or 0)
            agg[key]["shares"] = (agg[key]["shares"] or 0) + (h["shares"] or 0)

    result = list(agg.values())
    result.sort(key=lambda h: h.get("value") or 0, reverse=True)
    return result


# ══════════════════════════════════════════════════════════════════
# PUBLIC: INVESTOR SEARCH
# ══════════════════════════════════════════════════════════════════

def search_investors(query: str) -> Dict:
    """
    Search EDGAR for institutional investors by name (those that file 13F-HR).

    Uses the EDGAR company search HTML (tableFile2) because the Atom feed
    returns broken company names (SEC CGI renders Perl internal references).

    Returns:
        dict with keys: query, results (list of {cik, name}), count, fetched_at
    """
    cache_key = f"search_{re.sub(r'[^a-z0-9]', '_', query.lower())}"
    cache_path = _cache_path(INVESTOR_CACHE_DIR, cache_key)

    cached = _read_cache(cache_path)
    if cached:
        return cached

    resp = requests.get(
        "https://www.sec.gov/cgi-bin/browse-edgar",
        params={
            "company": query, "CIK": "", "type": "13F-HR",
            "dateb": "", "owner": "include", "count": "40",
            "search_text": "", "action": "getcompany",
        },
        headers=HEADERS,
        timeout=15,
    )
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    results = []

    table = soup.find("table", class_="tableFile2")
    if table:
        for row in table.find_all("tr"):
            cols = row.find_all("td")
            if len(cols) >= 2:
                cik_text = cols[0].text.strip()
                name_raw = cols[1].text.strip()
                # Strip SIC description if appended (e.g. "NAME INC\nSIC: 6726 ...")
                name = name_raw.split("SIC:")[0].split("\n")[0].strip()
                if cik_text.isdigit() and name:
                    results.append({
                        "cik": cik_text.zfill(10),
                        "name": name,
                    })

    result = {
        "query": query,
        "results": results,
        "count": len(results),
        "fetched_at": datetime.now().isoformat(),
    }
    _write_cache(cache_path, result)
    return result


# ══════════════════════════════════════════════════════════════════
# PUBLIC: 13F FILINGS LIST
# ══════════════════════════════════════════════════════════════════

def fetch_investor_filings(cik: str, force_refresh: bool = False) -> Dict:
    """
    Return all 13F-HR filing dates for an investor CIK.

    Returns:
        dict with keys: cik, investor_name, filings (list), total_filings, fetched_at
    """
    cik_padded = cik.zfill(10)
    cache_path = _cache_path(INVESTOR_CACHE_DIR, f"filings_{cik_padded}")

    if not force_refresh:
        cached = _read_cache(cache_path)
        if cached:
            return cached

    subs = _get_submissions(cik_padded)
    filings = subs.get("filings", {}).get("recent", {})
    investor_name = subs.get("name", f"CIK {cik}")

    forms = filings.get("form", [])
    accessions = filings.get("accessionNumber", [])
    filing_dates = filings.get("filingDate", [])
    report_dates = filings.get("reportDate", [])

    filing_list = [
        {
            "accessionNumber": accessions[i],
            "filingDate": filing_dates[i],
            "reportDate": report_dates[i] if i < len(report_dates) else "",
            "form": form,
        }
        for i, form in enumerate(forms)
        if form in ("13F-HR", "13F-HR/A") and i < len(accessions)
    ]

    result = {
        "cik": cik_padded,
        "investor_name": investor_name,
        "filings": filing_list,
        "total_filings": len(filing_list),
        "fetched_at": datetime.now().isoformat(),
    }
    _write_cache(cache_path, result)
    return result


# ══════════════════════════════════════════════════════════════════
# PUBLIC: 13F HOLDINGS
# ══════════════════════════════════════════════════════════════════

def fetch_13f_holdings(
    cik: str,
    filing_date: Optional[str] = None,
    force_refresh: bool = False,
) -> Dict:
    """
    Fetch and parse 13F-HR holdings for an investor.

    Args:
        cik: Investor EDGAR CIK
        filing_date: Specific YYYY-MM-DD filing date, or None for most recent
        force_refresh: Bypass file cache

    Returns:
        dict with keys: cik, investor_name, filing_date, report_date,
                        holdings (list), total_holdings, total_portfolio_value,
                        available_filings, fetched_at
    """
    cik_padded = cik.zfill(10)
    cache_key = f"holdings_{cik_padded}_{filing_date or 'latest'}"
    cache_path = _cache_path(INVESTOR_CACHE_DIR, cache_key)

    if not force_refresh:
        cached = _read_cache(cache_path)
        if cached:
            logger.info("Cache hit for investor holdings %s", cik_padded)
            return cached

    logger.info("Fetching 13F holdings for CIK %s (date=%s)", cik_padded, filing_date or "latest")

    filings_data = fetch_investor_filings(cik_padded, force_refresh=force_refresh)
    filing_list = filings_data.get("filings", [])
    investor_name = filings_data.get("investor_name", f"CIK {cik}")

    if not filing_list:
        raise ValueError(f"No 13F-HR filings found for CIK {cik}")

    if filing_date:
        target = next((f for f in filing_list if f["filingDate"] == filing_date), None)
        if not target:
            raise ValueError(f"No 13F filing found for date {filing_date}")
    else:
        target = filing_list[0]

    info_url = _find_13f_info_table_url(cik_padded, target["accessionNumber"])

    raw_holdings: List[Dict] = []
    if info_url:
        try:
            resp = requests.get(info_url, headers=HEADERS, timeout=20)
            resp.raise_for_status()
            raw_holdings = _parse_13f_xml(resp.text)
        except Exception as exc:
            logger.error("Failed to fetch 13F info table for CIK %s: %s", cik, exc)
    else:
        logger.warning("Could not find info table URL for CIK %s filing %s", cik, target["accessionNumber"])

    holdings = _aggregate_holdings(raw_holdings)
    total_value = sum(h.get("value") or 0 for h in holdings)

    for h in holdings:
        h["portfolio_pct"] = (
            round((h.get("value") or 0) / total_value * 100, 4) if total_value > 0 else 0.0
        )

    result = {
        "cik": cik_padded,
        "investor_name": investor_name,
        "filing_date": target["filingDate"],
        "report_date": target.get("reportDate", ""),
        "holdings": holdings,
        "total_holdings": len(holdings),
        "total_portfolio_value": total_value,
        "available_filings": [f["filingDate"] for f in filing_list],
        "fetched_at": datetime.now().isoformat(),
    }

    _write_cache(cache_path, result)
    logger.info(
        "13F fetch complete for %s: %d positions, total $%.1fB",
        investor_name, len(holdings), total_value / 1e9,
    )
    return result


# ══════════════════════════════════════════════════════════════════
# PUBLIC: MULTI-FILING HISTORY (for ChartManager time-series)
# ══════════════════════════════════════════════════════════════════

def fetch_13f_history(
    cik: str,
    num_filings: int = 6,
    top_n: int = 15,
    force_refresh: bool = False,
) -> Dict:
    """
    Fetch the last `num_filings` distinct quarterly 13F periods and return
    portfolio weight history for the top-N holdings.

    Handles investors with multiple sub-manager 13F filings per quarter
    (e.g. Berkshire Hathaway) by grouping on reportDate and using the filing
    with the most holdings for each quarter period.

    Args:
        cik: Investor EDGAR CIK
        num_filings: How many distinct quarters to load
        top_n: How many top holdings to track over time
        force_refresh: Bypass file cache

    Returns:
        dict with:
            investor_name, cik,
            columns: [oldest_date, ..., newest_date]  (filing dates)
            rows: [ { name: company_name, values: [pct_oldest, ..., pct_newest] }, ... ]
            all_holdings_latest: full latest holdings list
            available_filings: all filing dates
    """
    cik_padded = cik.zfill(10)
    cache_key = f"history_{cik_padded}_{num_filings}_{top_n}"
    cache_path = _cache_path(INVESTOR_CACHE_DIR, cache_key)

    if not force_refresh:
        cached = _read_cache(cache_path)
        if cached:
            return cached

    filings_data = fetch_investor_filings(cik_padded, force_refresh=force_refresh)
    all_filings = filings_data.get("filings", [])
    investor_name = filings_data.get("investor_name", f"CIK {cik}")

    if not all_filings:
        raise ValueError(f"No 13F filings found for CIK {cik}")

    # Group by reportDate; for each quarter keep all filing accession numbers
    # so we can pick the one with the most holdings
    from collections import defaultdict
    by_period: Dict[str, List[Dict]] = defaultdict(list)
    for f in all_filings:
        period = f.get("reportDate") or f["filingDate"][:7]  # fallback to YYYY-MM
        by_period[period].append(f)

    # Take the N most recent distinct periods
    sorted_periods = sorted(by_period.keys(), reverse=True)[:num_filings]
    sorted_periods.reverse()  # oldest → newest

    # For each period, try each filing and keep the one with most holdings
    per_filing: List[Dict] = []
    for period in sorted_periods:
        candidates = by_period[period]
        best: Optional[Dict] = None
        for filing in candidates:
            try:
                data = fetch_13f_holdings(
                    cik_padded,
                    filing_date=filing["filingDate"],
                    force_refresh=force_refresh,
                )
                if best is None or data["total_holdings"] > best["total_holdings"]:
                    best = data
                time.sleep(0.05)
            except Exception as exc:
                logger.warning("Could not load filing %s: %s", filing["filingDate"], exc)
        if best and best["total_holdings"] > 0:
            per_filing.append(best)

    if not per_filing:
        raise ValueError(f"No holdings data could be loaded for CIK {cik}")

    # Find top-N companies by value in the most recent (largest) filing
    latest = per_filing[-1]
    top_companies = [h["company_name"] for h in latest["holdings"][:top_n]]

    # Build time-series: columns = filing dates, rows = per-company portfolio %
    columns = [f["filing_date"] for f in per_filing]
    rows = []
    for company in top_companies:
        values = []
        for filing_data in per_filing:
            match = next(
                (h for h in filing_data["holdings"] if h["company_name"] == company),
                None,
            )
            values.append(round(match["portfolio_pct"], 4) if match else None)
        rows.append({"name": company, "values": values})

    result = {
        "cik": cik_padded,
        "investor_name": investor_name,
        "columns": columns,
        "rows": rows,
        "all_holdings_latest": latest["holdings"],
        "total_portfolio_value": latest["total_portfolio_value"],
        "latest_filing_date": latest["filing_date"],
        "available_filings": all_filings,
        "fetched_at": datetime.now().isoformat(),
    }

    _write_cache(cache_path, result)
    return result


# ══════════════════════════════════════════════════════════════════
# CLI ENTRY POINT (for manual testing)
# ══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    parser = argparse.ArgumentParser(description="Insider Trading & Investor Data Collection")
    sub = parser.add_subparsers(dest="cmd")

    p_form4 = sub.add_parser("form4", help="Fetch Form 4 insider transactions")
    p_form4.add_argument("ticker")
    p_form4.add_argument("--limit", type=int, default=40)
    p_form4.add_argument("--derivatives", action="store_true")
    p_form4.add_argument("--refresh", action="store_true")

    p_search = sub.add_parser("search", help="Search institutional investors")
    p_search.add_argument("query")

    p_holdings = sub.add_parser("holdings", help="Fetch 13F holdings for a CIK")
    p_holdings.add_argument("cik")
    p_holdings.add_argument("--date", default=None)
    p_holdings.add_argument("--refresh", action="store_true")

    p_history = sub.add_parser("history", help="Fetch portfolio history for a CIK")
    p_history.add_argument("cik")
    p_history.add_argument("--filings", type=int, default=6)
    p_history.add_argument("--top", type=int, default=15)

    args = parser.parse_args()

    if args.cmd == "form4":
        data = fetch_form4_transactions(args.ticker, args.limit, args.derivatives, args.refresh)
        print(f"\n{data['company_name']} ({data['ticker']})")
        print(f"Transactions: {len(data['transactions'])}")
        for t in data["transactions"][:5]:
            print(f"  {t['transaction_date']} | {t['insider_name']} | {t['transaction_type']} | {t['shares']} shares @ ${t['price_per_share']}")
    elif args.cmd == "search":
        data = search_investors(args.query)
        print(f"\nResults for '{args.query}':")
        for r in data["results"][:10]:
            print(f"  {r['name']} (CIK {r['cik']})")
    elif args.cmd == "holdings":
        data = fetch_13f_holdings(args.cik, args.date, args.refresh)
        print(f"\n{data['investor_name']} — {data['filing_date']}")
        print(f"Total portfolio: ${data['total_portfolio_value']:,.0f}")
        for h in data["holdings"][:10]:
            print(f"  {h['company_name']}: {h['portfolio_pct']:.2f}%  ${h['value']:,.0f}")
    elif args.cmd == "history":
        data = fetch_13f_history(args.cik, args.filings, args.top)
        print(f"\n{data['investor_name']} — {len(data['columns'])} filings")
        print("Columns:", data["columns"])
        for row in data["rows"][:5]:
            print(f"  {row['name']}: {row['values']}")
    else:
        parser.print_help()
