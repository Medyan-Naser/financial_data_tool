"""
ENHANCED AGENTIC PARSER - Improved Financial Statement Mapping via LLM

Key Improvements over the original agentic_parser.py:
1. BATCH LLM QUERIES: Groups related/confusable items together for LLM mapping
   (e.g., items with "sales" could be COGS, Net Sales, Revenue - ask LLM to map all at once)
2. CROSS-YEAR NUMERICAL VALIDATION: Uses overlapping years between merged statements
   and new filings to validate mappings with 10% tolerance (excludes zero values)
3. ENHANCED PROMPTS: Includes numerical insights, summation relationships, and groupings
4. VERIFICATION LOOP: Mapper Agent → Verifier Agent feedback loop (max 3 iterations)

Usage:
    from enhanced_agentic_parser import EnhancedAgenticParser
    parser = EnhancedAgenticParser(
        statement_type='income_statement',
        historical_statements={'2022': df_2022, '2023': df_2023}
    )
    result = parser.parse(og_df, rows_text, rows_that_are_sum)
"""

import json
import logging
import os
import re
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Set
from collections import defaultdict
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

# Try importing langchain
try:
    from langchain_ollama import ChatOllama
    from langchain_core.messages import HumanMessage, SystemMessage
    LANGCHAIN_AVAILABLE = True
except ImportError:
    try:
        from langchain_community.chat_models import ChatOllama
        from langchain_core.messages import HumanMessage, SystemMessage
        LANGCHAIN_AVAILABLE = True
    except ImportError:
        LANGCHAIN_AVAILABLE = False
        logger.warning("langchain/ollama not available for enhanced agentic parser")


# ═══════════════════════════════════════════════════════════════════════════════
# DATA CLASSES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class CrossYearMatch:
    """Result of cross-year numerical validation for a single comparison."""
    year_column: str
    historical_filing: str
    current_value: float
    historical_value: float
    pct_difference: float
    is_match: bool
    is_perfect_match: bool  # NEW: Exact match with 0% difference
    
    def __repr__(self):
        status = "PERFECT" if self.is_perfect_match else ("MATCH" if self.is_match else "MISMATCH")
        return f"CrossYearMatch({self.year_column}: {status}, diff={self.pct_difference*100:.1f}%)"


@dataclass
class RowNumericalContext:
    """Numerical context for a single row including cross-year validation."""
    row_idx: str
    values: Dict[str, float]  # year -> value
    cross_year_matches: List[CrossYearMatch]
    is_sum_row: bool
    sum_components: List[str]
    sum_computed: float
    sum_difference_pct: float
    
    @property
    def has_strong_cross_year_match(self) -> bool:
        """True if any cross-year validation matched."""
        return any(m.is_match for m in self.cross_year_matches)
    
    @property
    def has_perfect_match(self) -> bool:
        """True if any cross-year validation was a perfect match."""
        return any(m.is_perfect_match for m in self.cross_year_matches)
    
    @property
    def best_historical_match(self) -> Optional[str]:
        """Returns the fact name this row most likely matches based on cross-year data."""
        # This is populated during validation
        return getattr(self, '_best_historical_match', None)


@dataclass
class ConfusableGroup:
    """A group of rows that could be confused with each other."""
    group_id: str
    group_type: str  # e.g., 'revenue_related', 'expense_related', 'asset_related'
    target_items: List[str]  # Standardized items these could map to
    rows: List[str]  # Row indices in this group
    reason: str  # Why these are grouped together


@dataclass 
class BatchMappingResult:
    """Result from batch LLM mapping of a confusable group."""
    group_id: str
    mappings: Dict[str, str]  # row_idx -> standardized_item
    confidence: Dict[str, float]  # row_idx -> confidence
    reasoning: Dict[str, str]  # row_idx -> reasoning
    unmapped_rows: List[str]
    

@dataclass
class VerificationResult:
    """Result from the verification agent."""
    is_valid: bool
    issues: List[Dict[str, Any]]  # List of issues found
    suggestions: List[Dict[str, Any]]  # Suggested corrections
    confidence: float
    reasoning: str
    

@dataclass
class EnhancedMappingResult:
    """Result for a single row mapping with full context."""
    row_idx: str
    mapped_to: Optional[str]
    confidence: float
    reasoning: str
    is_sum_row: bool
    cross_year_validated: bool
    cross_year_perfect_match: bool
    mapped_via: str  # 'batch_llm', 'cross_year', 'verification_fix', etc.
    numerical_context: Optional[RowNumericalContext]


@dataclass
class EnhancedParseResult:
    """Complete result of enhanced agentic parsing."""
    mapped_df: pd.DataFrame
    mappings: List[EnhancedMappingResult]
    unmapped_rows: List[str]
    verification_iterations: int
    verification_history: List[VerificationResult]
    statistics: Dict


# ═══════════════════════════════════════════════════════════════════════════════
# CONFUSABLE ITEM GROUPS - Items that are commonly confused
# ═══════════════════════════════════════════════════════════════════════════════

CONFUSABLE_GROUPS = {
    'income_statement': [
        {
            'group_type': 'revenue_related',
            'keywords': ['revenue', 'sales', 'net sales', 'total revenue'],
            'target_items': ['Total revenue'],
            'exclude_keywords': ['cost', 'expense', 'cogs'],
        },
        {
            'group_type': 'cost_of_sales',
            'keywords': ['cost', 'cogs', 'cost of revenue', 'cost of sales', 'cost of goods'],
            'target_items': ['COGS'],
            'exclude_keywords': ['operating', 'interest', 'research'],
        },
        {
            'group_type': 'operating_expenses',
            'keywords': ['operating', 'expense', 'r&d', 'research', 'selling', 'general', 'administrative', 'sg&a', 'marketing'],
            'target_items': ['R&D', 'SG&A', 'General and administrative', 'Sales and marketing', 'Total operating expense', 'Other operating expenses'],
            'exclude_keywords': ['interest', 'tax', 'income'],
        },
        {
            'group_type': 'income_items',
            'keywords': ['income', 'profit', 'earnings', 'loss'],
            'target_items': ['Gross profit', 'Operating income', 'Income before tax', 'Net income'],
            'exclude_keywords': ['tax expense', 'per share'],
        },
        {
            'group_type': 'tax_related',
            'keywords': ['tax', 'income tax'],
            'target_items': ['Income Tax Expense'],
            'exclude_keywords': ['before tax', 'deferred'],
        },
        {
            'group_type': 'per_share',
            'keywords': ['per share', 'eps', 'earnings per', 'diluted', 'basic'],
            'target_items': ['Earnings Per Share Basic', 'Earnings Per Share Diluted', 
                           'Weighted Average Number Of Shares Outstanding Basic',
                           'Weighted Average Number Of Shares Outstanding Diluted'],
            'exclude_keywords': [],
        },
    ],
    'balance_sheet': [
        {
            'group_type': 'cash_securities',
            'keywords': ['cash', 'equivalent', 'marketable', 'securities', 'investment'],
            'target_items': ['Cash And Cash Equivalen', 'Marketable Securities Current', 'Marketable Securities Noncurrent'],
            'exclude_keywords': ['flow', 'change'],
        },
        {
            'group_type': 'receivables_inventory',
            'keywords': ['receivable', 'inventory', 'inventories'],
            'target_items': ['Accounts Receivable', 'Inventory'],
            'exclude_keywords': ['payable', 'change'],
        },
        {
            'group_type': 'current_assets',
            'keywords': ['current asset', 'total current', 'other current'],
            'target_items': ['Current Assets', 'Other Current Assets'],
            'exclude_keywords': ['liabilit', 'non-current', 'noncurrent'],
        },
        {
            'group_type': 'fixed_assets',
            'keywords': ['property', 'plant', 'equipment', 'ppe', 'fixed asset'],
            'target_items': ['Property Plant And Equipment'],
            'exclude_keywords': [],
        },
        {
            'group_type': 'intangibles',
            'keywords': ['goodwill', 'intangible', 'amortiz'],
            'target_items': ['Goodwill', 'Intangible Assets'],
            'exclude_keywords': ['expense'],
        },
        {
            'group_type': 'total_assets',
            'keywords': ['total asset', 'assets total'],
            'target_items': ['Total Assets', 'Noncurrent Assets'],
            'exclude_keywords': ['current', 'liabilit'],
        },
        {
            'group_type': 'payables_liabilities',
            'keywords': ['payable', 'accrued', 'liability', 'liabilities'],
            'target_items': ['Accounts Payable', 'Accrued Liabilities', 'Other Current Liabilities', 
                           'Current Liabilities', 'Noncurrent Liabilities', 'Total Liabilities'],
            'exclude_keywords': ['receivable', 'asset'],
        },
        {
            'group_type': 'debt',
            'keywords': ['debt', 'borrowing', 'loan', 'commercial paper', 'note'],
            'target_items': ['Short Term Debt Current', 'Long Term Debt', 'Commercial Paper'],
            'exclude_keywords': [],
        },
        {
            'group_type': 'equity',
            'keywords': ['equity', 'stockholder', 'shareholder', 'retained', 'common stock', 'treasury'],
            'target_items': ['Stockholders Equity', 'Retained Earnings', 'Common Stock', 
                           'Additional Paid-In Capital', 'Treasury Stock', 
                           'Accumulated Other Comprehensive Income'],
            'exclude_keywords': [],
        },
    ],
    'cash_flow_statement': [
        {
            'group_type': 'operating_adjustments',
            'keywords': ['depreciation', 'amortization', 'stock-based', 'compensation', 'deferred'],
            'target_items': ['Depreciation and amortization (CF)', 'Stock-based compensation', 
                           'Deferred income taxes', 'Other noncash items'],
            'exclude_keywords': [],
        },
        {
            'group_type': 'working_capital_changes',
            'keywords': ['change in', 'increase', 'decrease', 'receivable', 'inventory', 'payable'],
            'target_items': ['Change in accounts receivable', 'Change in inventory', 
                           'Change in accounts payable', 'Change in other operating assets',
                           'Change in other operating liabilities', 'Change in other working capital'],
            'exclude_keywords': [],
        },
        {
            'group_type': 'investing_activities',
            'keywords': ['purchase', 'acquisition', 'capital expenditure', 'capex', 'proceeds', 'marketable'],
            'target_items': ['Purchase of marketable securities', 'Proceeds from marketable securities',
                           'Capital expenditures', 'Acquisitions', 'Other investing activities',
                           'Net cash from investing activities'],
            'exclude_keywords': ['operating', 'financing'],
        },
        {
            'group_type': 'financing_activities',
            'keywords': ['dividend', 'repurchase', 'buyback', 'debt', 'issuance', 'stock'],
            'target_items': ['Dividends paid', 'Stock repurchases', 'Proceeds from debt issuance',
                           'Debt repayment', 'Proceeds from issuance of common stock',
                           'Net cash from financing activities'],
            'exclude_keywords': ['operating', 'investing'],
        },
        {
            'group_type': 'cash_totals',
            'keywords': ['net cash', 'cash from', 'total cash', 'net change', 'beginning', 'ending'],
            'target_items': ['Net cash from operating activities', 'Net cash from investing activities',
                           'Net cash from financing activities', 'Net change in cash', 
                           'Cash at beginning of period'],
            'exclude_keywords': [],
        },
    ],
}

