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


# ═══════════════════════════════════════════════════════════════════════════════
# STANDARDIZED ITEMS BY STATEMENT TYPE
# ═══════════════════════════════════════════════════════════════════════════════

INCOME_STATEMENT_ITEMS = [
    "Total revenue", "COGS", "Gross profit", "R&D", "SG&A",
    "General and administrative", "Sales and marketing",
    "Amoritization & Depreciation", "Other operating expenses",
    "Total operating expense", "Operating income", "Interest expense",
    "Interest and investment income", "Nonoperating income expense",
    "Income before tax", "Income Tax Expense", "Net income",
    "Earnings Per Share Basic", "Earnings Per Share Diluted",
    "Weighted Average Number Of Shares Outstanding Basic",
    "Weighted Average Number Of Shares Outstanding Diluted",
]

BALANCE_SHEET_ITEMS = [
    "Cash And Cash Equivalen", "Marketable Securities Current",
    "Accounts Receivable", "Inventory", "Other Current Assets",
    "Current Assets", "Marketable Securities Noncurrent",
    "Property Plant And Equipment", "Goodwill", "Intangible Assets",
    "Deferred Income Tax Assets", "Other Noncurrent Assets",
    "Operating Lease Right of Use Asset", "Noncurrent Assets", "Total Assets",
    "Accounts Payable", "Accrued Liabilities", "Other Current Liabilities",
    "Deferred Revenue", "Commercial Paper", "Short Term Debt Current",
    "Current Liabilities", "Long Term Debt", "Operating Lease Liability Noncurrent",
    "Deferred Tax Liabilities Noncurrent", "Other Noncurrent Liabilities",
    "Noncurrent Liabilities", "Total Liabilities", "Retained Earnings",
    "Accumulated Other Comprehensive Income", "Common Stock",
    "Additional Paid-In Capital", "Treasury Stock", "Stockholders Equity",
    "Total Liabilities And Equity",
]

CASH_FLOW_ITEMS = [
    "Net income (CF)", "Depreciation and amortization (CF)",
    "Stock-based compensation", "Deferred income taxes", "Other noncash items",
    "Change in accounts receivable", "Change in inventory",
    "Change in accounts payable", "Change in other operating assets",
    "Change in other operating liabilities", "Change in other working capital",
    "Net cash from operating activities", "Purchase of marketable securities",
    "Proceeds from marketable securities", "Capital expenditures", "Acquisitions",
    "Other investing activities", "Net cash from investing activities",
    "Tax withholding for share-based compensation", "Dividends paid",
    "Stock repurchases", "Proceeds from debt issuance", "Debt repayment",
    "Commercial paper net change", "Proceeds from issuance of common stock",
    "Other financing activities", "Net cash from financing activities",
    "Effect of exchange rate on cash", "Net change in cash",
    "Cash at beginning of period", "Interest paid", "Income taxes paid",
]


# ═══════════════════════════════════════════════════════════════════════════════
# PROMPTS
# ═══════════════════════════════════════════════════════════════════════════════

BATCH_MAPPER_SYSTEM_PROMPT = """You are a Senior Financial Data Analyst specializing in SEC EDGAR filings.
Your job is to map MULTIPLE related rows from financial statements to standardized concepts AT ONCE.

CRITICAL RULES:
1. You receive a GROUP of related rows that could potentially be confused with each other.
2. Map each row to ONE of the provided standardized items, or "null" if no match.
3. Each standardized item should be mapped AT MOST once - if multiple rows could match, pick the BEST one.
4. Use ALL available context: GAAP tags, human labels, numerical values, cross-year matches, and sum relationships.

**VERY IMPORTANT**: The "row_idx" in your response MUST be the EXACT GAAP tag string shown in the input (like "us-gaap_RevenueFromContractWithCustomerExcludingAssessedTax"), NOT a numeric index or abbreviated form!

NUMERICAL INSIGHTS (critical for decision-making):
- If a row's values MATCH historical data for a specific fact (within 10%), that's STRONG evidence.
- If cross_year_match says "PERFECT", it's almost certainly correct.
- If a row is marked as a SUM row, it should map to a "Total" type item.
- Use the magnitude of numbers: billions typically = revenue-level, millions = expense-level.
- LLMs are bad at math, so I've pre-computed all numerical comparisons for you.

COMMON GAAP TAG MAPPINGS:
- us-gaap_Revenues, us-gaap_RevenueFromContractWithCustomerExcludingAssessedTax → "Total revenue"
- us-gaap_CostOfGoodsAndServicesSold, us-gaap_CostOfRevenue → "COGS"
- us-gaap_GrossProfit → "Gross profit"
- us-gaap_ResearchAndDevelopmentExpense → "R&D"
- us-gaap_SellingGeneralAndAdministrativeExpense → "SG&A"
- us-gaap_OperatingIncomeLoss → "Operating income"
- us-gaap_NetIncomeLoss → "Net income"
- us-gaap_Assets → "Total Assets"
- us-gaap_Liabilities → "Total Liabilities"
- us-gaap_StockholdersEquity → "Stockholders Equity"

You MUST respond with valid JSON only. Use the EXACT row index string from the input:
{
    "mappings": [
        {"row_idx": "us-gaap_RevenueFromContractWithCustomerExcludingAssessedTax", "mapped_to": "Total revenue", "confidence": 0.95, "reasoning": "GAAP Revenue tag"}
    ]
}"""


VERIFIER_SYSTEM_PROMPT = """You are a Senior Financial Auditor who verifies financial statement mappings.
Your job is to review a complete mapping and identify any issues or inconsistencies.

VERIFICATION CHECKS:
1. ACCOUNTING EQUATIONS: Does the mapping satisfy basic accounting identities?
   - Gross Profit = Revenue - COGS
   - Operating Income = Gross Profit - Operating Expenses
   - Total Assets = Current Assets + Noncurrent Assets
   - Total Liabilities + Equity = Total Assets

2. NUMERICAL CONSISTENCY: Do the mapped values make economic sense?
   - Revenue should be positive and typically the largest item
   - COGS should be positive and less than Revenue
   - Net Income can be positive or negative but should be smaller magnitude than Revenue

3. CROSS-YEAR VALIDATION: Were cross-year matches honored?
   - If a row had a PERFECT cross-year match to a fact, it should be mapped to that fact

4. SUM ROWS: Are sum rows mapped to "Total" type items?
   - Rows marked as sums should map to items like "Total revenue", "Total Assets", etc.

5. MISSING CRITICAL ITEMS: Are key items present?
   - Income statement needs: Revenue, COGS, Gross Profit, Operating Income, Net Income
   - Balance sheet needs: Total Assets, Total Liabilities, Stockholders Equity

RESPOND WITH:
{
    "is_valid": true/false,
    "issues": [
        {"type": "equation_violation", "description": "...", "severity": "high/medium/low"}
    ],
    "suggestions": [
        {"row_idx": "...", "current_mapping": "...", "suggested_mapping": "...", "reasoning": "..."}
    ],
    "confidence": 0.85,
    "reasoning": "overall assessment"
}"""


# ═══════════════════════════════════════════════════════════════════════════════
# ENHANCED AGENTIC PARSER CLASS
# ═══════════════════════════════════════════════════════════════════════════════

class EnhancedAgenticParser:
    """
    Enhanced agentic parser with:
    1. Batch LLM queries for related/confusable items
    2. Cross-year numerical validation (10% tolerance, excludes zeros)
    3. Verification agent with feedback loop (max 3 iterations)
    """

    def __init__(
        self,
        statement_type: str = "income_statement",
        historical_statements: Optional[Dict[str, pd.DataFrame]] = None,
        model_name: str = "llama3.2",
        fallback_model: str = "mistral",
        base_url: str = "http://localhost:11434",
        temperature: float = 0.1,
        timeout: int = 60,
        max_verification_iterations: int = 3,
        cross_year_tolerance: float = 0.10,
        target_items: Optional[List[str]] = None,
    ):
        self.statement_type = statement_type
        self.historical_statements = historical_statements or {}
        self.model_name = model_name
        self.fallback_model = fallback_model
        self.base_url = base_url
        self.temperature = temperature
        self.timeout = timeout
        self.max_verification_iterations = max_verification_iterations
        self.cross_year_tolerance = cross_year_tolerance
        self._llm_cache = {}
        self.enabled = LANGCHAIN_AVAILABLE

        # Set target items based on statement type
        if statement_type == "income_statement":
            default_items = INCOME_STATEMENT_ITEMS
            self.confusable_groups = CONFUSABLE_GROUPS.get('income_statement', [])
        elif statement_type == "balance_sheet":
            default_items = BALANCE_SHEET_ITEMS
            self.confusable_groups = CONFUSABLE_GROUPS.get('balance_sheet', [])
        elif statement_type == "cash_flow_statement":
            default_items = CASH_FLOW_ITEMS
            self.confusable_groups = CONFUSABLE_GROUPS.get('cash_flow_statement', [])
        else:
            raise ValueError(f"Unknown statement type: {statement_type}")
        
        self.target_items = target_items if target_items else default_items

    def _get_llm(self, model: str):
        """Get or create a ChatOllama instance."""
        if not LANGCHAIN_AVAILABLE:
            return None
        if model not in self._llm_cache:
            try:
                self._llm_cache[model] = ChatOllama(
                    model=model,
                    base_url=self.base_url,
                    temperature=self.temperature,
                    timeout=self.timeout,
                    format="json",
                )
            except Exception as e:
                logger.error(f"Failed to create LLM for model '{model}': {e}")
                return None
        return self._llm_cache[model]

    def _invoke_llm(self, system_prompt: str, user_prompt: str,
                    model: Optional[str] = None, agent_name: str = "Unknown") -> Optional[str]:
        """Invoke LLM with fallback."""
        if not self.enabled:
            logger.warning(f"[{agent_name}] LLM not available")
            return None

        model = model or self.model_name

        for attempt_model in [model, self.fallback_model]:
            llm = self._get_llm(attempt_model)
            if llm is None:
                continue
            try:
                logger.info(f"[{agent_name}] Calling model '{attempt_model}'...")
                t0 = time.time()
                messages = [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_prompt),
                ]
                response = llm.invoke(messages)
                duration = time.time() - t0
                content = response.content
                logger.info(f"[{agent_name}] Response from '{attempt_model}' ({duration:.1f}s, {len(content)} chars)")
                return content
            except Exception as e:
                logger.warning(f"[{agent_name}] FAILED with '{attempt_model}': {e}")
                if attempt_model == self.fallback_model:
                    return None
        return None

    def _parse_json_response(self, response: str) -> Optional[Dict]:
        """Parse JSON from LLM response."""
        if not response:
            return None
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass
            logger.warning(f"Could not parse JSON: {response[:300]}")
            return None

 