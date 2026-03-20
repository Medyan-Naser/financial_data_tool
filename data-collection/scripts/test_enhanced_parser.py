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


class TestSuite:
    """Collect and summarize test results."""
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.start_time = datetime.now()
        
    def add_result(self, result: TestResult):
        self.results.append(result)
    
    def get_summary(self) -> dict:
        if not self.results:
            return {'message': 'No results'}
        
        total_tests = len(self.results)
        successful_tests = sum(1 for r in self.results if not r.errors)
        
        total_rows = sum(r.total_rows for r in self.results)
        total_mapped = sum(r.mapped_rows for r in self.results)
        total_cross_year = sum(r.cross_year_validated for r in self.results)
        total_perfect = sum(r.perfect_matches for r in self.results)
        
        avg_match_pct = sum(r.match_percentage for r in self.results) / total_tests
        avg_parse_time = sum(r.parse_time_seconds for r in self.results) / total_tests
        
        by_statement = {}
        for r in self.results:
            if r.statement_type not in by_statement:
                by_statement[r.statement_type] = {'count': 0, 'match_pct_sum': 0}
            by_statement[r.statement_type]['count'] += 1
            by_statement[r.statement_type]['match_pct_sum'] += r.match_percentage
        
        for st in by_statement:
            by_statement[st]['avg_match_pct'] = round(
                by_statement[st]['match_pct_sum'] / by_statement[st]['count'], 1
            )
        
        return {
            'total_tests': total_tests,
            'successful_tests': successful_tests,
            'failed_tests': total_tests - successful_tests,
            'total_rows_processed': total_rows,
            'total_rows_mapped': total_mapped,
            'overall_match_percentage': round(total_mapped / total_rows * 100, 1) if total_rows > 0 else 0,
            'total_cross_year_validated': total_cross_year,
            'total_perfect_matches': total_perfect,
            'avg_match_percentage': round(avg_match_pct, 1),
            'avg_parse_time_seconds': round(avg_parse_time, 2),
            'total_time_seconds': round((datetime.now() - self.start_time).total_seconds(), 1),
            'by_statement_type': by_statement,
        }
    
    def print_summary(self):
        summary = self.get_summary()
        print("\n" + "=" * 80)
        print("ENHANCED PARSER TEST SUMMARY".center(80))
        print("=" * 80)
        
        print(f"\n📊 Overall Results:")
        print(f"   Tests Run: {summary['total_tests']}")
        print(f"   Successful: {summary['successful_tests']}")
        print(f"   Failed: {summary['failed_tests']}")
        
        print(f"\n📈 Mapping Statistics:")
        print(f"   Total Rows Processed: {summary['total_rows_processed']:,}")
        print(f"   Total Rows Mapped: {summary['total_rows_mapped']:,}")
        print(f"   Overall Match Rate: {summary['overall_match_percentage']}%")
        print(f"   Avg Match Rate per Statement: {summary['avg_match_percentage']}%")
        
        print(f"\n🔗 Cross-Year Validation:")
        print(f"   Cross-Year Validated: {summary['total_cross_year_validated']:,}")
        print(f"   Perfect Matches: {summary['total_perfect_matches']:,}")
        
        print(f"\n⏱️  Performance:")
        print(f"   Average Parse Time: {summary['avg_parse_time_seconds']}s")
        print(f"   Total Test Time: {summary['total_time_seconds']}s")
        
        print(f"\n📋 By Statement Type:")
        for st, stats in summary.get('by_statement_type', {}).items():
            print(f"   {st}: {stats['count']} tests, {stats['avg_match_pct']}% avg match")
        
        print("\n" + "=" * 80)
        
        # Print any errors
        errors = [r for r in self.results if r.errors]
        if errors:
            print("\n⚠️  Errors:")
            for r in errors:
                print(f"   {r.ticker} {r.statement_type} {r.filing_date}: {r.errors}")


