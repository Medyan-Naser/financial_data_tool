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


# ═══════════════════════════════════════════════════════════════════════════════
# TEST FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def test_single_statement(
    og_df: pd.DataFrame,
    rows_text: Dict[str, str],
    rows_that_are_sum: List[str],
    statement_type: str,
    historical_statements: Dict[str, pd.DataFrame],
    ticker: str,
    filing_date: str,
) -> TestResult:
    """Test the enhanced parser on a single statement."""
    
    result = TestResult(ticker, statement_type, filing_date)
    result.total_rows = len(og_df)
    
    try:
        parser = EnhancedAgenticParser(
            statement_type=statement_type,
            historical_statements=historical_statements,
            max_verification_iterations=3,
            cross_year_tolerance=0.10,
        )
        
        start_time = time.time()
        parse_result = parser.parse(
            og_df=og_df,
            rows_text=rows_text,
            rows_that_are_sum=rows_that_are_sum,
        )
        result.parse_time_seconds = time.time() - start_time
        
        # Extract statistics
        result.mapped_rows = parse_result.statistics['mapped_rows']
        result.cross_year_validated = parse_result.statistics.get('cross_year_validated', 0)
        result.perfect_matches = parse_result.statistics.get('perfect_matches', 0)
        result.verification_iterations = parse_result.verification_iterations
        result.verification_passed = parse_result.statistics.get('final_verification_valid', True)
        
        logger.info(
            f"[{ticker}] {statement_type} {filing_date}: "
            f"{result.mapped_rows}/{result.total_rows} mapped ({result.match_percentage:.1f}%), "
            f"{result.cross_year_validated} cross-year, {result.perfect_matches} perfect, "
            f"{result.verification_iterations} iterations, {result.parse_time_seconds:.1f}s"
        )
        
    except Exception as e:
        result.errors.append(str(e))
        logger.error(f"[{ticker}] {statement_type} {filing_date}: ERROR - {e}")
    
    return result


def test_company(
    ticker: str,
    num_years: int = 5,
    statement_filter: str = 'all',
    test_suite: Optional[TestSuite] = None,
) -> Dict[str, List[TestResult]]:
    """Test enhanced parser for a single company over multiple years."""
    
    logger.info(f"\n{'='*60}")
    logger.info(f"Testing {ticker} for {num_years} years")
    logger.info(f"{'='*60}")
    
    results_by_type = {
        'income_statement': [],
        'balance_sheet': [],
        'cash_flow_statement': [],
    }
    
    try:
        # Initialize company
        company = Company(ticker=ticker)
        logger.info(f"Company CIK: {company.cik}")
        
        # Get annual filings
        filings = company.ten_k_fillings
        filings = filings.iloc[:num_years]
        logger.info(f"Found {len(filings)} 10-K filings")
        
        # Accumulate historical statements
        historical_income = {}
        historical_balance = {}
        historical_cashflow = {}
        
        for idx, (report_date, accession_num) in enumerate(filings.items()):
            logger.info(f"\nProcessing filing {idx + 1}/{len(filings)}: {report_date}")
            
            try:
                filing = Filling(
                    ticker=ticker,
                    cik=company.cik,
                    acc_num_unfiltered=accession_num,
                    company_facts=company.company_facts,
                    quarterly=False
                )
                
                # Test income statement
                if statement_filter in ['income', 'all']:
                    filing.process_one_statement("income_statement", historical_statements=historical_income)
                    if filing.income_statement and filing.income_statement.og_df is not None:
                        result = test_single_statement(
                            og_df=filing.income_statement.og_df,
                            rows_text=filing.income_statement.rows_text,
                            rows_that_are_sum=filing.income_statement.rows_that_are_sum,
                            statement_type='income_statement',
                            historical_statements=historical_income,
                            ticker=ticker,
                            filing_date=str(report_date),
                        )
                        results_by_type['income_statement'].append(result)
                        if test_suite:
                            test_suite.add_result(result)
                        
                        # Add to historical
                        if filing.income_statement.mapped_df is not None:
                            historical_income[str(report_date)] = filing.income_statement.mapped_df.copy()
                
                # Test balance sheet
                if statement_filter in ['balance', 'all']:
                    filing.process_one_statement("balance_sheet", historical_statements=historical_balance)
                    if filing.balance_sheet and filing.balance_sheet.og_df is not None:
                        result = test_single_statement(
                            og_df=filing.balance_sheet.og_df,
                            rows_text=filing.balance_sheet.rows_text,
                            rows_that_are_sum=filing.balance_sheet.rows_that_are_sum,
                            statement_type='balance_sheet',
                            historical_statements=historical_balance,
                            ticker=ticker,
                            filing_date=str(report_date),
                        )
                        results_by_type['balance_sheet'].append(result)
                        if test_suite:
                            test_suite.add_result(result)
                        
                        if filing.balance_sheet.mapped_df is not None:
                            historical_balance[str(report_date)] = filing.balance_sheet.mapped_df.copy()
                
                # Test cash flow
                if statement_filter in ['cashflow', 'all']:
                    filing.process_one_statement("cash_flow_statement", historical_statements=historical_cashflow)
                    if filing.cash_flow and filing.cash_flow.og_df is not None:
                        result = test_single_statement(
                            og_df=filing.cash_flow.og_df,
                            rows_text=filing.cash_flow.rows_text,
                            rows_that_are_sum=filing.cash_flow.rows_that_are_sum,
                            statement_type='cash_flow_statement',
                            historical_statements=historical_cashflow,
                            ticker=ticker,
                            filing_date=str(report_date),
                        )
                        results_by_type['cash_flow_statement'].append(result)
                        if test_suite:
                            test_suite.add_result(result)
                        
                        if filing.cash_flow.mapped_df is not None:
                            historical_cashflow[str(report_date)] = filing.cash_flow.mapped_df.copy()
                
            except Exception as e:
                logger.error(f"Error processing filing {accession_num}: {e}")
                continue
        
    except Exception as e:
        logger.error(f"Error testing {ticker}: {e}")
    
    return results_by_type

