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

