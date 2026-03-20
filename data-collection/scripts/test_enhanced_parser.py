#!/usr/bin/env python3
"""
Test Enhanced Agentic Parser with Multiple Companies over 5 Years

This script tests the enhanced parsing system with:
1. Batch LLM queries for related/confusable items
2. Cross-year numerical validation (10% tolerance)
3. Verification agent with feedback loop (max 3 iterations)

Usage:
    python test_enhanced_parser.py
    python test_enhanced_parser.py --companies AAPL MSFT GOOGL
    python test_enhanced_parser.py --years 3 --statement income
"""

import argparse
import sys
import os
import json
import time
from datetime import datetime
from typing import Dict, List, Optional
import pandas as pd
import logging

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

# Set USE_MATCHING to enhanced for this test
os.environ['USE_MATCHING'] = 'enhanced'

from Company import Company
from Filling import Filling
from enhanced_agentic_parser import EnhancedAgenticParser, check_ollama_for_enhanced_parser


# ═══════════════════════════════════════════════════════════════════════════════
# TEST CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

DEFAULT_TEST_COMPANIES = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META']
DEFAULT_TEST_YEARS = 5


# ═══════════════════════════════════════════════════════════════════════════════
# TEST RESULT TRACKING
# ═══════════════════════════════════════════════════════════════════════════════

class TestResult:
    """Track results for a single company/statement test."""
    
    def __init__(self, ticker: str, statement_type: str, filing_date: str):
        self.ticker = ticker
        self.statement_type = statement_type
        self.filing_date = filing_date
        self.total_rows = 0
        self.mapped_rows = 0
        self.cross_year_validated = 0
        self.perfect_matches = 0
        self.verification_iterations = 0
        self.verification_passed = False
        self.parse_time_seconds = 0.0
        self.errors = []
        
    @property
    def match_percentage(self) -> float:
        if self.total_rows == 0:
            return 0.0
        return (self.mapped_rows / self.total_rows) * 100
    
    def to_dict(self) -> dict:
        return {
            'ticker': self.ticker,
            'statement_type': self.statement_type,
            'filing_date': self.filing_date,
            'total_rows': self.total_rows,
            'mapped_rows': self.mapped_rows,
            'match_percentage': round(self.match_percentage, 1),
            'cross_year_validated': self.cross_year_validated,
            'perfect_matches': self.perfect_matches,
            'verification_iterations': self.verification_iterations,
            'verification_passed': self.verification_passed,
            'parse_time_seconds': round(self.parse_time_seconds, 2),
            'errors': self.errors,
        }

