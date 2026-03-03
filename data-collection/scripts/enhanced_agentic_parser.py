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

    # ═══════════════════════════════════════════════════════════════════════════
    # CROSS-YEAR NUMERICAL VALIDATION
    # ═══════════════════════════════════════════════════════════════════════════

    def _validate_cross_year(
        self,
        row_idx: str,
        row_data: pd.Series,
        fact_name: str,
    ) -> List[CrossYearMatch]:
        """
        Validate a row's values against historical statements.
        
        Returns list of CrossYearMatch for overlapping years.
        Excludes zero values (not informative).
        Reports if match was perfect (0% diff) or within tolerance.
        """
        matches = []
        
        if not self.historical_statements:
            return matches
        
        current_columns = list(row_data.index)
        
        for hist_year, hist_df in self.historical_statements.items():
            if fact_name not in hist_df.index:
                continue
            
            hist_row = hist_df.loc[fact_name]
            
            # Find overlapping columns
            for col in current_columns:
                if col not in hist_row.index:
                    continue
                
                curr_val = row_data[col]
                hist_val = hist_row[col]
                
                # Skip NaN
                if pd.isna(curr_val) or pd.isna(hist_val):
                    continue
                
                curr_val = float(curr_val)
                hist_val = float(hist_val)
                
                # Skip zero values (not informative)
                if curr_val == 0 or hist_val == 0:
                    continue
                
                # Calculate percentage difference
                avg = (abs(curr_val) + abs(hist_val)) / 2
                pct_diff = abs(curr_val - hist_val) / avg if avg != 0 else 1.0
                
                is_match = pct_diff <= self.cross_year_tolerance
                is_perfect = pct_diff == 0.0  # Exact match
                
                matches.append(CrossYearMatch(
                    year_column=str(col),
                    historical_filing=str(hist_year),
                    current_value=curr_val,
                    historical_value=hist_val,
                    pct_difference=pct_diff,
                    is_match=is_match,
                    is_perfect_match=is_perfect,
                ))
        
        return matches

    def _find_best_cross_year_match(
        self,
        row_idx: str,
        row_data: pd.Series,
    ) -> Optional[Tuple[str, List[CrossYearMatch]]]:
        """
        Find which standardized item best matches this row based on cross-year data.
        
        Returns (best_fact_name, matches) or None if no good match.
        """
        best_fact = None
        best_matches = []
        best_score = 0
        
        for fact_name in self.target_items:
            matches = self._validate_cross_year(row_idx, row_data, fact_name)
            if not matches:
                continue
            
            # Score: perfect matches = 3, regular matches = 1
            score = sum(3 if m.is_perfect_match else (1 if m.is_match else -1) for m in matches)
            
            if score > best_score:
                best_score = score
                best_fact = fact_name
                best_matches = matches
        
        if best_score > 0:
            return (best_fact, best_matches)
        return None

    # ═══════════════════════════════════════════════════════════════════════════
    # SUM ROW DETECTION
    # ═══════════════════════════════════════════════════════════════════════════

    def _detect_sum_rows(
        self,
        og_df: pd.DataFrame,
        rows_that_are_sum: List[str],
        rows_text: Dict[str, str],
    ) -> Dict[str, Dict]:
        """Detect which rows are sum/total rows."""
        sum_info = {}
        
        sum_keywords = [
            r'(?i)^total\s+', r'(?i)^net\s+', r'(?i)\btotal$',
            r'(?i)^gross\s+profit', r'(?i)^operating\s+income',
            r'(?i)^income\s+before', r'(?i)^current\s+assets',
            r'(?i)^current\s+liabilities', r'(?i)^stockholders',
        ]
        
        first_col = og_df.columns[0] if len(og_df.columns) > 0 else None
        row_list = list(og_df.index)
        
        for idx in og_df.index:
            is_sum = False
            sum_type = None
            component_rows = []
            computed_sum = 0.0
            actual_value = 0.0
            
            if first_col:
                actual_value = float(og_df.loc[idx, first_col]) if not pd.isna(og_df.loc[idx, first_col]) else 0.0
            
            # Check HTML-based sum detection
            if idx in rows_that_are_sum:
                is_sum = True
                sum_type = "html_marker"
            
            # Check label keywords
            human_label = rows_text.get(idx, "")
            for pattern in sum_keywords:
                if re.search(pattern, human_label):
                    is_sum = True
                    sum_type = sum_type or "keyword_label"
                    break
            
            # Check GAAP tag for sum indicators
            gaap_lower = idx.lower()
            if any(kw in gaap_lower for kw in ['total', 'gross', 'netincome', 'netcash']):
                is_sum = True
                sum_type = sum_type or "gaap_tag"
            
            # Try to find component rows (rows above that sum to this value)
            if is_sum and actual_value != 0 and first_col:
                try:
                    pos = row_list.index(idx)
                    if pos > 0:
                        lookback = min(pos, 15)
                        rows_above = row_list[pos - lookback:pos]
                        
                        # Get values for rows above
                        above_vals = {}
                        for r in rows_above:
                            val = og_df.loc[r, first_col]
                            if not pd.isna(val) and val != 0:
                                above_vals[r] = float(val)
                        
                        # Try to find subset that sums to actual_value
                        if above_vals:
                            total_above = sum(above_vals.values())
                            if abs(total_above - actual_value) / max(abs(actual_value), 1) < 0.05:
                                component_rows = list(above_vals.keys())
                                computed_sum = total_above
                except ValueError:
                    pass
            
            if is_sum:
                sum_info[idx] = {
                    "is_sum": True,
                    "sum_type": sum_type,
                    "label": human_label,
                    "component_rows": component_rows,
                    "computed_sum": computed_sum,
                    "actual_value": actual_value,
                }
        
        return sum_info

    # ═══════════════════════════════════════════════════════════════════════════
    # CONFUSABLE GROUP DETECTION
    # ═══════════════════════════════════════════════════════════════════════════

    def _identify_confusable_groups(
        self,
        og_df: pd.DataFrame,
        rows_text: Dict[str, str],
    ) -> List[ConfusableGroup]:
        """
        Group rows that could be confused with each other based on keywords.
        """
        groups = []
        assigned_rows = set()
        
        for group_def in self.confusable_groups:
            group_type = group_def['group_type']
            keywords = group_def['keywords']
            exclude_keywords = group_def.get('exclude_keywords', [])
            target_items = group_def['target_items']
            
            matching_rows = []
            
            for idx in og_df.index:
                if idx in assigned_rows:
                    continue
                
                # Check GAAP tag and human label
                search_text = (idx + " " + rows_text.get(idx, "")).lower()
                
                # Check if any keyword matches
                has_keyword = any(kw.lower() in search_text for kw in keywords)
                
                # Check if any exclude keyword matches
                has_exclude = any(kw.lower() in search_text for kw in exclude_keywords) if exclude_keywords else False
                
                if has_keyword and not has_exclude:
                    matching_rows.append(idx)
            
            if matching_rows:
                groups.append(ConfusableGroup(
                    group_id=f"{self.statement_type}_{group_type}",
                    group_type=group_type,
                    target_items=target_items,
                    rows=matching_rows,
                    reason=f"Rows containing keywords: {keywords}",
                ))
                assigned_rows.update(matching_rows)
        
        # Create a group for remaining unassigned rows
        remaining_rows = [idx for idx in og_df.index if idx not in assigned_rows]
        if remaining_rows:
            groups.append(ConfusableGroup(
                group_id=f"{self.statement_type}_other",
                group_type="other",
                target_items=self.target_items,
                rows=remaining_rows,
                reason="Rows not matching any specific keyword group",
            ))
        
        return groups

    # ═══════════════════════════════════════════════════════════════════════════
    # BATCH LLM MAPPING
    # ═══════════════════════════════════════════════════════════════════════════

    def _build_batch_prompt(
        self,
        group: ConfusableGroup,
        og_df: pd.DataFrame,
        rows_text: Dict[str, str],
        sum_info: Dict[str, Dict],
        numerical_contexts: Dict[str, RowNumericalContext],
    ) -> str:
        """Build prompt for batch mapping a confusable group."""
        lines = [
            f"## Confusable Group: {group.group_type}",
            f"**Reason for grouping**: {group.reason}",
            "",
            "## Target Items to Map To (pick the BEST match for each row):",
        ]
        
        for item in group.target_items:
            lines.append(f"  - {item}")
        
        lines.append("")
        lines.append("## Rows to Map:")
        
        first_col = og_df.columns[0] if len(og_df.columns) > 0 else None
        
        for row_idx in group.rows:
            human_label = rows_text.get(row_idx, "")
            is_sum = row_idx in sum_info
            
            lines.append(f"\n### Row: `{row_idx}`")
            lines.append(f"  - **Human Label**: \"{human_label}\"")
            
            # Add values
            if first_col and row_idx in og_df.index:
                val = og_df.loc[row_idx, first_col]
                if pd.notna(val) and val != 0:
                    lines.append(f"  - **Value**: {float(val):,.0f}")
            
            # Add sum row info
            if is_sum:
                si = sum_info[row_idx]
                lines.append(f"  - **[SUM ROW]** Type: {si['sum_type']}")
                if si.get('component_rows'):
                    lines.append(f"  - Components: {si['component_rows'][:5]}")
                    lines.append(f"  - Computed Sum: {si['computed_sum']:,.0f}")
            
            # Add cross-year validation info
            ctx = numerical_contexts.get(row_idx)
            if ctx and ctx.cross_year_matches:
                lines.append("  - **Cross-Year Validation**:")
                for match in ctx.cross_year_matches[:3]:
                    status = "✓ PERFECT MATCH" if match.is_perfect_match else (
                        f"✓ MATCH ({match.pct_difference*100:.1f}% diff)" if match.is_match else 
                        f"✗ MISMATCH ({match.pct_difference*100:.1f}% diff)"
                    )
                    lines.append(f"    - {match.year_column}: current={match.current_value:,.0f} vs historical={match.historical_value:,.0f} → {status}")
        
        lines.append("")
        lines.append("## Instructions:")
        lines.append("1. Map each row to the BEST matching target item.")
        lines.append("2. If a row has a PERFECT cross-year match, strongly prefer that mapping.")
        lines.append("3. SUM rows should map to 'Total' type items.")
        lines.append("4. Each target item should be mapped AT MOST once.")
        lines.append("5. Return 'null' for mapped_to if no good match exists.")
        
        return "\n".join(lines)

    def _map_batch(
        self,
        group: ConfusableGroup,
        og_df: pd.DataFrame,
        rows_text: Dict[str, str],
        sum_info: Dict[str, Dict],
        numerical_contexts: Dict[str, RowNumericalContext],
    ) -> BatchMappingResult:
        """Map a batch of confusable rows using LLM."""
        
        prompt = self._build_batch_prompt(group, og_df, rows_text, sum_info, numerical_contexts)
        
        response = self._invoke_llm(
            BATCH_MAPPER_SYSTEM_PROMPT, 
            prompt, 
            agent_name=f"BatchMapper:{group.group_type}"
        )
        
        parsed = self._parse_json_response(response)
        
        result = BatchMappingResult(
            group_id=group.group_id,
            mappings={},
            confidence={},
            reasoning={},
            unmapped_rows=[],
        )
        
        if parsed and "mappings" in parsed:
            mapped_items = set()
            
            # Build lookup dict for flexible matching
            og_index_map = {str(idx): idx for idx in og_df.index}
            og_index_lower_map = {str(idx).lower(): idx for idx in og_df.index}
            group_rows_set = set(group.rows)
            
            # Debug: Log what LLM returned
            logger.debug(f"[BatchMapper] LLM returned {len(parsed['mappings'])} mappings")
            for i, m in enumerate(parsed["mappings"][:3]):
                logger.debug(f"[BatchMapper]   Raw mapping {i}: row_idx='{m.get('row_idx')}' -> '{m.get('mapped_to')}'")
            logger.debug(f"[BatchMapper] Group has rows: {group.rows[:3]}...")
            
            for m in parsed["mappings"]:
                row_idx = str(m.get("row_idx", "")).strip()
                mapped_to = m.get("mapped_to")
                confidence = float(m.get("confidence", 0.0))
                reasoning = m.get("reasoning", "")
                
                # Skip null/empty mappings
                if not row_idx or not mapped_to or mapped_to.lower() == 'null':
                    continue
                
                # Flexible row_idx matching
                actual_row_idx = None
                
                # 1. Exact match
                if row_idx in og_index_map:
                    actual_row_idx = og_index_map[row_idx]
                # 2. Case-insensitive match
                elif row_idx.lower() in og_index_lower_map:
                    actual_row_idx = og_index_lower_map[row_idx.lower()]
                # 3. Partial match (LLM might return truncated or modified version)
                else:
                    for idx in group.rows:
                        idx_str = str(idx)
                        if row_idx in idx_str or idx_str in row_idx:
                            actual_row_idx = idx
                            break
                        # Also try without namespace prefix
                        if '_' in idx_str:
                            tag_part = idx_str.split('_', 1)[-1]
                            if row_idx.lower() == tag_part.lower() or tag_part.lower() in row_idx.lower():
                                actual_row_idx = idx
                                break
                
                if not actual_row_idx:
                    logger.debug(f"[BatchMapper] Could not match row_idx '{row_idx}' to any row in group")
                    continue
                
                # Flexible mapped_to matching
                actual_mapped_to = None
                if mapped_to in self.target_items:
                    actual_mapped_to = mapped_to
                else:
                    # Case-insensitive match
                    mapped_to_lower = mapped_to.lower()
                    for target in self.target_items:
                        if target.lower() == mapped_to_lower:
                            actual_mapped_to = target
                            break
                    # Partial match
                    if not actual_mapped_to:
                        for target in self.target_items:
                            if mapped_to_lower in target.lower() or target.lower() in mapped_to_lower:
                                actual_mapped_to = target
                                break
                
                if not actual_mapped_to:
                    logger.debug(f"[BatchMapper] Could not match mapped_to '{mapped_to}' to any target item")
                    continue
                
                if actual_mapped_to not in mapped_items:
                    result.mappings[actual_row_idx] = actual_mapped_to
                    result.confidence[actual_row_idx] = confidence
                    result.reasoning[actual_row_idx] = reasoning
                    mapped_items.add(actual_mapped_to)
                    logger.debug(f"[BatchMapper] Mapped: {actual_row_idx} -> {actual_mapped_to}")
                else:
                    result.unmapped_rows.append(actual_row_idx)
            
            logger.info(f"[BatchMapper] Group '{group.group_type}': {len(result.mappings)} mappings from {len(parsed['mappings'])} LLM responses")
        else:
            logger.warning(f"[BatchMapper] No valid mappings in response for group '{group.group_type}'")
            result.unmapped_rows = group.rows.copy()
        
        return result

    # ═══════════════════════════════════════════════════════════════════════════
    # VERIFICATION AGENT
    # ═══════════════════════════════════════════════════════════════════════════

    def _build_verification_prompt(
        self,
        mappings: Dict[str, str],
        og_df: pd.DataFrame,
        rows_text: Dict[str, str],
        sum_info: Dict[str, Dict],
        numerical_contexts: Dict[str, RowNumericalContext],
        previous_feedback: Optional[str] = None,
    ) -> str:
        """Build prompt for verification agent."""
        lines = [
            f"## Statement Type: {self.statement_type}",
            "",
            "## Current Mappings:",
        ]
        
        first_col = og_df.columns[0] if len(og_df.columns) > 0 else None
        
        for row_idx, mapped_to in sorted(mappings.items(), key=lambda x: x[1]):
            value = ""
            if first_col and row_idx in og_df.index:
                val = og_df.loc[row_idx, first_col]
                if pd.notna(val):
                    value = f" (value: {float(val):,.0f})"
            
            lines.append(f"  - `{row_idx}` → **{mapped_to}**{value}")
        
        # Add unmapped rows
        unmapped = [idx for idx in og_df.index if idx not in mappings]
        if unmapped:
            lines.append("")
            lines.append("## Unmapped Rows:")
            for idx in unmapped[:20]:
                label = rows_text.get(idx, "")
                value = ""
                if first_col:
                    val = og_df.loc[idx, first_col]
                    if pd.notna(val) and val != 0:
                        value = f" (value: {float(val):,.0f})"
                lines.append(f"  - `{idx}` ({label}){value}")
        
        # Add cross-year validation summary
        lines.append("")
        lines.append("## Cross-Year Validation Summary:")
        for row_idx, mapped_to in mappings.items():
            ctx = numerical_contexts.get(row_idx)
            if ctx and ctx.cross_year_matches:
                perfect = any(m.is_perfect_match for m in ctx.cross_year_matches)
                matched = any(m.is_match for m in ctx.cross_year_matches)
                if perfect:
                    lines.append(f"  - {row_idx} → {mapped_to}: ✓ PERFECT cross-year match")
                elif matched:
                    lines.append(f"  - {row_idx} → {mapped_to}: ✓ Cross-year match within 10%")
                else:
                    lines.append(f"  - {row_idx} → {mapped_to}: ⚠ No cross-year validation")
        
        if previous_feedback:
            lines.append("")
            lines.append("## Previous Feedback (from earlier iteration):")
            lines.append(previous_feedback)
        
        lines.append("")
        lines.append("## Verify the mappings. Check for:")
        lines.append("1. Accounting equation violations")
        lines.append("2. Mismatched cross-year validations")
        lines.append("3. Missing critical items")
        lines.append("4. Economic nonsense (negative revenue, etc.)")
        
        return "\n".join(lines)

    def _verify_mappings(
        self,
        mappings: Dict[str, str],
        og_df: pd.DataFrame,
        rows_text: Dict[str, str],
        sum_info: Dict[str, Dict],
        numerical_contexts: Dict[str, RowNumericalContext],
        previous_feedback: Optional[str] = None,
    ) -> VerificationResult:
        """Run verification agent on current mappings."""
        
        prompt = self._build_verification_prompt(
            mappings, og_df, rows_text, sum_info, 
            numerical_contexts, previous_feedback
        )
        
        response = self._invoke_llm(
            VERIFIER_SYSTEM_PROMPT, 
            prompt, 
            agent_name="Verifier"
        )
        
        parsed = self._parse_json_response(response)
        
        if parsed:
            return VerificationResult(
                is_valid=parsed.get("is_valid", True),
                issues=parsed.get("issues", []),
                suggestions=parsed.get("suggestions", []),
                confidence=float(parsed.get("confidence", 0.5)),
                reasoning=parsed.get("reasoning", ""),
            )
        
        return VerificationResult(
            is_valid=True,
            issues=[],
            suggestions=[],
            confidence=0.5,
            reasoning="Verification failed to parse",
        )

    def _apply_verification_suggestions(
        self,
        mappings: Dict[str, str],
        verification: VerificationResult,
    ) -> Dict[str, str]:
        """Apply verification suggestions to mappings."""
        new_mappings = mappings.copy()
        
        for suggestion in verification.suggestions:
            row_idx = suggestion.get("row_idx")
            suggested = suggestion.get("suggested_mapping")
            
            if row_idx and suggested and suggested in self.target_items:
                # Check if suggested item is not already mapped
                if suggested not in new_mappings.values():
                    new_mappings[row_idx] = suggested
                    logger.info(f"[Verifier] Applied fix: {row_idx} -> {suggested}")
        
        return new_mappings

    # ═══════════════════════════════════════════════════════════════════════════
    # MAIN PARSING METHOD
    # ═══════════════════════════════════════════════════════════════════════════

    def parse(
        self,
        og_df: pd.DataFrame,
        rows_text: Dict[str, str],
        rows_that_are_sum: List[str],
    ) -> EnhancedParseResult:
        """
        Parse the financial statement using enhanced agentic approach.
        
        Workflow:
        1. Detect sum rows
        2. Build numerical context (cross-year validation for each row)
        3. Identify confusable groups
        4. Batch LLM mapping for each group
        5. Verification loop (max 3 iterations)
        6. Build final mapped DataFrame
        """
        logger.info(f"[EnhancedParser] Starting {self.statement_type} ({len(og_df)} rows, "
                   f"{len(self.historical_statements)} historical statements)")
        
        # Step 1: Detect sum rows
        sum_info = self._detect_sum_rows(og_df, rows_that_are_sum, rows_text)
        logger.info(f"[EnhancedParser] Detected {len(sum_info)} sum rows")
        
        # Step 2: Build numerical context with cross-year validation
        numerical_contexts = {}
        cross_year_hints = {}  # row_idx -> suggested fact based on cross-year
        
        for idx in og_df.index:
            row_data = og_df.loc[idx]
            
            # Find best cross-year match
            best_match = self._find_best_cross_year_match(idx, row_data)
            
            ctx = RowNumericalContext(
                row_idx=idx,
                values={str(col): float(row_data[col]) for col in row_data.index if pd.notna(row_data[col])},
                cross_year_matches=best_match[1] if best_match else [],
                is_sum_row=idx in sum_info,
                sum_components=sum_info.get(idx, {}).get('component_rows', []),
                sum_computed=sum_info.get(idx, {}).get('computed_sum', 0.0),
                sum_difference_pct=0.0,
            )
            numerical_contexts[idx] = ctx
            
            if best_match and best_match[1]:
                has_perfect = any(m.is_perfect_match for m in best_match[1])
                has_match = any(m.is_match for m in best_match[1])
                if has_perfect or has_match:
                    cross_year_hints[idx] = best_match[0]
                    logger.info(f"[EnhancedParser] Cross-year hint: {idx} -> {best_match[0]} "
                               f"({'PERFECT' if has_perfect else 'within 10%'})")
        
        # Step 3: Identify confusable groups
        groups = self._identify_confusable_groups(og_df, rows_text)
        logger.info(f"[EnhancedParser] Identified {len(groups)} confusable groups: "
                   f"{[g.group_type for g in groups]}")
        
        # Step 4: Batch LLM mapping for each group
        all_mappings = {}
        all_confidence = {}
        all_reasoning = {}
        
        for group in groups:
            logger.info(f"[EnhancedParser] Mapping group '{group.group_type}' ({len(group.rows)} rows)")
            
            batch_result = self._map_batch(
                group, og_df, rows_text, sum_info, numerical_contexts
            )
            
            all_mappings.update(batch_result.mappings)
            all_confidence.update(batch_result.confidence)
            all_reasoning.update(batch_result.reasoning)
        
        logger.info(f"[EnhancedParser] Initial mapping: {len(all_mappings)} rows mapped")
        
        # Apply cross-year hints for unmapped rows with strong validation
        for row_idx, fact in cross_year_hints.items():
            if row_idx not in all_mappings and fact not in all_mappings.values():
                all_mappings[row_idx] = fact
                all_confidence[row_idx] = 0.9
                all_reasoning[row_idx] = "Cross-year numerical validation match"
                logger.info(f"[EnhancedParser] Applied cross-year hint: {row_idx} -> {fact}")
        
        # Step 5: Verification loop
        verification_history = []
        previous_feedback = None
        
        for iteration in range(self.max_verification_iterations):
            logger.info(f"[EnhancedParser] Verification iteration {iteration + 1}/{self.max_verification_iterations}")
            
            verification = self._verify_mappings(
                all_mappings, og_df, rows_text, sum_info, 
                numerical_contexts, previous_feedback
            )
            verification_history.append(verification)
            
            logger.info(f"[EnhancedParser] Verification result: valid={verification.is_valid}, "
                       f"issues={len(verification.issues)}, confidence={verification.confidence:.2f}")
            
            if verification.is_valid or not verification.suggestions:
                logger.info(f"[EnhancedParser] Verification passed or no suggestions, stopping loop")
                break
            
            # Apply suggestions
            new_mappings = self._apply_verification_suggestions(all_mappings, verification)
            
            if new_mappings == all_mappings:
                logger.info(f"[EnhancedParser] No changes from suggestions, stopping loop")
                break
            
            all_mappings = new_mappings
            previous_feedback = f"Issues: {verification.issues}\nApplied fixes for iteration {iteration + 1}"
        
        # Step 6: Build final mapped DataFrame
        mapped_df = pd.DataFrame(0.0, index=self.target_items, columns=og_df.columns)
        mappings_list = []
        
        for row_idx, mapped_to in all_mappings.items():
            if mapped_to in mapped_df.index and row_idx in og_df.index:
                mapped_df.loc[mapped_to] = og_df.loc[row_idx]
                
                ctx = numerical_contexts.get(row_idx)
                
                mappings_list.append(EnhancedMappingResult(
                    row_idx=row_idx,
                    mapped_to=mapped_to,
                    confidence=all_confidence.get(row_idx, 0.5),
                    reasoning=all_reasoning.get(row_idx, ""),
                    is_sum_row=row_idx in sum_info,
                    cross_year_validated=ctx.has_strong_cross_year_match if ctx else False,
                    cross_year_perfect_match=ctx.has_perfect_match if ctx else False,
                    mapped_via="batch_llm",
                    numerical_context=ctx,
                ))
        
        unmapped = [idx for idx in og_df.index if idx not in all_mappings]
        
        stats = {
            "total_rows": len(og_df),
            "mapped_rows": len(all_mappings),
            "unmapped_rows": len(unmapped),
            "match_percentage": (len(all_mappings) / len(og_df) * 100) if len(og_df) > 0 else 0,
            "cross_year_validated": sum(1 for m in mappings_list if m.cross_year_validated),
            "perfect_matches": sum(1 for m in mappings_list if m.cross_year_perfect_match),
            "verification_iterations": len(verification_history),
            "final_verification_valid": verification_history[-1].is_valid if verification_history else True,
            "confusable_groups_processed": len(groups),
        }
        
        logger.info(f"[EnhancedParser] Complete: {stats['mapped_rows']}/{stats['total_rows']} mapped "
                   f"({stats['match_percentage']:.1f}%), {stats['cross_year_validated']} cross-year validated, "
                   f"{stats['perfect_matches']} perfect matches")
        
        return EnhancedParseResult(
            mapped_df=mapped_df,
            mappings=mappings_list,
            unmapped_rows=unmapped,
            verification_iterations=len(verification_history),
            verification_history=verification_history,
            statistics=stats,
        )


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTION
# ═══════════════════════════════════════════════════════════════════════════════

def check_ollama_for_enhanced_parser(base_url: str = "http://localhost:11434") -> bool:
    """Check if Ollama is available for enhanced parsing."""
    try:
        import requests
        response = requests.get(f"{base_url}/api/tags", timeout=5)
        return response.status_code == 200
    except Exception:
        return False
