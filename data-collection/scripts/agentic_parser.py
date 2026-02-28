"""
FULLY AGENTIC LLM PARSER - Financial Statement Mapping via LLM

This module provides a fully agentic approach to parsing financial statements.
Instead of regex patterns and rules, the LLM decides how to map each row
to standardized financial statement items.

Key Design Principles:
1. LLM decides all mappings - no regex or rule-based matching
2. Sum row hints provided to LLM (computed by code, not LLM)
3. All calculations done by code - LLM doesn't do math
4. Post-mapping validation using accounting equations

Usage:
    from agentic_parser import AgenticParser
    parser = AgenticParser(statement_type='income_statement')
    result = parser.parse(og_df, rows_text, rows_that_are_sum)
"""

import json
import logging
import os
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import re

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
        logger.warning("langchain/ollama not available for agentic parser")


@dataclass
class AgenticMappingResult:
    """Result of agentic LLM mapping for a single row."""
    row_idx: str
    mapped_to: Optional[str]
    confidence: float
    reasoning: str
    is_sum_row: bool
    value_info: str


@dataclass
class ValidationResult:
    """Result of equation validation."""
    equation_name: str
    is_valid: bool
    expected: float
    actual: float
    difference: float
    tolerance_pct: float
    message: str


@dataclass
class AgenticParseResult:
    """Complete result of agentic parsing."""
    mapped_df: pd.DataFrame
    mappings: List[AgenticMappingResult]
    unmapped_rows: List[str]
    validation_results: List[ValidationResult]
    statistics: Dict


# ═══════════════════════════════════════════════════════════════════════════════
# STANDARDIZED FINANCIAL ITEMS (what we want to map to)
# ═══════════════════════════════════════════════════════════════════════════════

INCOME_STATEMENT_ITEMS = [
    "Total revenue",
    "COGS",
    "Gross profit",
    "R&D",
    "SG&A",
    "General and administrative",
    "Sales and marketing",
    "Amoritization & Depreciation",
    "Other operating expenses",
    "Total operating expense",
    "Operating income",
    "Interest expense",
    "Interest and investment income",
    "Nonoperating income expense",
    "Income before tax",
    "Income Tax Expense",
    "Net income",
    "Earnings Per Share Basic",
    "Earnings Per Share Diluted",
    "Weighted Average Number Of Shares Outstanding Basic",
    "Weighted Average Number Of Shares Outstanding Diluted",
]

BALANCE_SHEET_ITEMS = [
    "Cash And Cash Equivalen",
    "Marketable Securities Current",
    "Accounts Receivable",
    "Inventory",
    "Other Current Assets",
    "Current Assets",
    "Marketable Securities Noncurrent",
    "Property Plant And Equipment",
    "Goodwill",
    "Intangible Assets",
    "Deferred Income Tax Assets",
    "Other Noncurrent Assets",
    "Operating Lease Right of Use Asset",
    "Noncurrent Assets",
    "Total Assets",
    "Accounts Payable",
    "Accrued Liabilities",
    "Other Current Liabilities",
    "Deferred Revenue",
    "Commercial Paper",
    "Short Term Debt Current",
    "Current Liabilities",
    "Long Term Debt",
    "Operating Lease Liability Noncurrent",
    "Deferred Tax Liabilities Noncurrent",
    "Other Noncurrent Liabilities",
    "Noncurrent Liabilities",
    "Total Liabilities",
    "Retained Earnings",
    "Accumulated Other Comprehensive Income",
    "Common Stock",
    "Additional Paid-In Capital",
    "Treasury Stock",
    "Stockholders Equity",
    "Total Liabilities And Equity",
]

CASH_FLOW_ITEMS = [
    "Net income (CF)",
    "Depreciation and amortization (CF)",
    "Stock-based compensation",
    "Deferred income taxes",
    "Other noncash items",
    "Change in accounts receivable",
    "Change in inventory",
    "Change in accounts payable",
    "Change in other operating assets",
    "Change in other operating liabilities",
    "Change in other working capital",
    "Net cash from operating activities",
    "Purchase of marketable securities",
    "Proceeds from marketable securities",
    "Capital expenditures",
    "Acquisitions",
    "Other investing activities",
    "Net cash from investing activities",
    "Tax withholding for share-based compensation",
    "Dividends paid",
    "Stock repurchases",
    "Proceeds from debt issuance",
    "Debt repayment",
    "Commercial paper net change",
    "Proceeds from issuance of common stock",
    "Other financing activities",
    "Net cash from financing activities",
    "Effect of exchange rate on cash",
    "Net change in cash",
    "Cash at beginning of period",
    "Interest paid",
    "Income taxes paid",
]


# ═══════════════════════════════════════════════════════════════════════════════
# ACCOUNTING EQUATIONS FOR VALIDATION (done by code, not LLM)
# ═══════════════════════════════════════════════════════════════════════════════

INCOME_STATEMENT_EQUATIONS = [
    {
        "name": "Gross Profit = Revenue - COGS",
        "result": "Gross profit",
        "components": [("Total revenue", 1), ("COGS", -1)],
        "tolerance_pct": 5.0,
    },
    {
        "name": "Operating Income = Gross Profit - OpEx",
        "result": "Operating income",
        "components": [("Gross profit", 1), ("Total operating expense", -1)],
        "tolerance_pct": 10.0,
    },
    {
        "name": "Net Income = Income Before Tax - Tax",
        "result": "Net income",
        "components": [("Income before tax", 1), ("Income Tax Expense", -1)],
        "tolerance_pct": 10.0,
    },
]

BALANCE_SHEET_EQUATIONS = [
    {
        "name": "Total Assets = Current Assets + Noncurrent Assets",
        "result": "Total Assets",
        "components": [("Current Assets", 1), ("Noncurrent Assets", 1)],
        "tolerance_pct": 5.0,
    },
    {
        "name": "Total Liabilities = Current Liabilities + Noncurrent Liabilities",
        "result": "Total Liabilities",
        "components": [("Current Liabilities", 1), ("Noncurrent Liabilities", 1)],
        "tolerance_pct": 5.0,
    },
    {
        "name": "Total Liabilities + Equity = Total Assets",
        "result": "Total Assets",
        "components": [("Total Liabilities", 1), ("Stockholders Equity", 1)],
        "tolerance_pct": 5.0,
    },
    {
        "name": "Total Liabilities And Equity = Total Assets",
        "result": "Total Liabilities And Equity",
        "components": [("Total Assets", 1)],
        "tolerance_pct": 1.0,
    },
]

CASH_FLOW_EQUATIONS = [
    {
        "name": "Net Change in Cash = Operating + Investing + Financing + FX",
        "result": "Net change in cash",
        "components": [
            ("Net cash from operating activities", 1),
            ("Net cash from investing activities", 1),
            ("Net cash from financing activities", 1),
            ("Effect of exchange rate on cash", 1),
        ],
        "tolerance_pct": 10.0,
    },
]


# ═══════════════════════════════════════════════════════════════════════════════
# PROMPTS FOR THE LLM
# ═══════════════════════════════════════════════════════════════════════════════

MAPPER_SYSTEM_PROMPT = """You are a Senior Financial Data Analyst specializing in SEC EDGAR filings.
Your job is to map rows from raw financial statements to standardized financial concepts.

CRITICAL RULES:
1. You receive rows from a financial statement with GAAP taxonomy tags and human-readable labels.
2. Map each row to ONE of the provided standardized items, or NULL if no match.
3. Each standardized item should be mapped AT MOST once - pick the BEST row.
4. SUM rows (marked [SUM]) are typically totals.

COMMON GAAP TAG MAPPINGS (use these!):
- us-gaap_Revenues, us-gaap_RevenueFromContractWithCustomerExcludingAssessedTax, us-gaap_SalesRevenueNet → "Total revenue"
- us-gaap_CostOfGoodsAndServicesSold, us-gaap_CostOfRevenue, us-gaap_CostOfGoodsSold → "COGS"
- us-gaap_GrossProfit → "Gross profit"
- us-gaap_ResearchAndDevelopmentExpense → "R&D"
- us-gaap_SellingGeneralAndAdministrativeExpense → "SG&A"
- us-gaap_OperatingIncomeLoss → "Operating income"
- us-gaap_IncomeLossFromContinuingOperationsBeforeIncomeTaxes* → "Income before tax"
- us-gaap_IncomeTaxExpenseBenefit → "Income Tax Expense"
- us-gaap_NetIncomeLoss → "Net income"
- us-gaap_CashAndCashEquivalentsAtCarryingValue → "Cash And Cash Equivalen"
- us-gaap_AssetsCurrent → "Current Assets"
- us-gaap_Assets → "Total Assets"
- us-gaap_LiabilitiesCurrent → "Current Liabilities"
- us-gaap_Liabilities → "Total Liabilities"
- us-gaap_StockholdersEquity → "Stockholders Equity"

IMPORTANT: In your response, use the EXACT row_idx STRING from the input (like "us-gaap_Revenues"), NOT a numeric index!

You MUST respond with valid JSON only using this EXACT format:
{
    "mappings": [
        {"row_idx": "us-gaap_Revenues", "mapped_to": "Total revenue", "confidence": 0.95, "reasoning": "GAAP Revenue tag"}
    ]
}"""


VALIDATION_FIX_PROMPT = """You are a Financial Data Validator.
The initial mapping has some issues detected by equation validation.

VALIDATION FAILURES:
{validation_failures}

CURRENT MAPPINGS:
{current_mappings}

UNMAPPED ROWS:
{unmapped_rows}

Your task: Review the validation failures and suggest corrections.
- If a row was mapped incorrectly, suggest the correct mapping.
- If a required item is missing, suggest which unmapped row it might be.
- Consider that some items may simply not be present in this statement.

Respond with exactly this JSON format:
{
    "corrections": [
        {
            "row_idx": "some_row",
            "old_mapping": "Wrong Item",
            "new_mapping": "Correct Item",
            "reasoning": "why this correction"
        }
    ],
    "missing_items": [
        {
            "item": "Gross profit",
            "likely_row": "some_unmapped_row or null",
            "confidence": 0.7,
            "reasoning": "why this row"
        }
    ]
}"""


# ═══════════════════════════════════════════════════════════════════════════════
# AGENTIC PARSER CLASS
# ═══════════════════════════════════════════════════════════════════════════════

class AgenticParser:
    """
    Fully agentic LLM-based parser for financial statements.
    
    All mapping decisions are made by the LLM, with code handling:
    - Sum row detection
    - Equation validation
    - Numeric calculations
    """

    def __init__(
        self,
        statement_type: str = "income_statement",
        model_name: str = "llama3.2",
        fallback_model: str = "mistral",
        base_url: str = "http://localhost:11434",
        temperature: float = 0.1,
        timeout: int = 180,
        max_retries: int = 2,
        target_items: Optional[List[str]] = None,
    ):
        """
        Args:
            statement_type: 'income_statement', 'balance_sheet', or 'cash_flow_statement'
            model_name: Primary Ollama model
            fallback_model: Fallback if primary fails
            base_url: Ollama server URL
            temperature: LLM temperature (low = deterministic)
            timeout: Request timeout seconds
            max_retries: Max validation retry attempts
            target_items: Optional list of target items to map to. If None, uses defaults.
        """
        self.statement_type = statement_type
        self.model_name = model_name
        self.fallback_model = fallback_model
        self.base_url = base_url
        self.temperature = temperature
        self.timeout = timeout
        self.max_retries = max_retries
        self._llm_cache = {}
        self.enabled = LANGCHAIN_AVAILABLE

        # Set equations based on statement type
        if statement_type == "income_statement":
            self.equations = INCOME_STATEMENT_EQUATIONS
            default_items = INCOME_STATEMENT_ITEMS
        elif statement_type == "balance_sheet":
            self.equations = BALANCE_SHEET_EQUATIONS
            default_items = BALANCE_SHEET_ITEMS
        elif statement_type == "cash_flow_statement":
            self.equations = CASH_FLOW_EQUATIONS
            default_items = CASH_FLOW_ITEMS
        else:
            raise ValueError(f"Unknown statement type: {statement_type}")
        
        # Use provided target_items or fall back to defaults
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
                    model: Optional[str] = None) -> Optional[str]:
        """Invoke LLM with fallback."""
        if not self.enabled:
            logger.warning("[AgenticParser] LLM not available")
            return None

        model = model or self.model_name

        for attempt_model in [model, self.fallback_model]:
            llm = self._get_llm(attempt_model)
            if llm is None:
                continue
            try:
                logger.info(f"[AgenticParser] Calling model '{attempt_model}'...")
                t0 = time.time()
                messages = [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_prompt),
                ]
                response = llm.invoke(messages)
                duration = time.time() - t0
                content = response.content
                logger.info(
                    f"[AgenticParser] Response from '{attempt_model}' "
                    f"({duration:.1f}s, {len(content)} chars)"
                )
                return content
            except Exception as e:
                logger.warning(f"[AgenticParser] FAILED with '{attempt_model}': {e}")
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
            # Try to extract JSON from the response
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass
            logger.warning(f"Could not parse LLM response as JSON: {response[:300]}")
            return None

    # ═══════════════════════════════════════════════════════════════════════════
    # SUM ROW DETECTION (done by code, not LLM)
    # ═══════════════════════════════════════════════════════════════════════════

    def _detect_sum_rows(
        self,
        og_df: pd.DataFrame,
        rows_that_are_sum: List[str],
        rows_text: Dict[str, str],
    ) -> Dict[str, Dict]:
        """
        Detect which rows are sum/total rows.
        
        Uses multiple signals:
        1. rows_that_are_sum from HTML parsing (class='reu' or 'rou')
        2. Labels containing 'Total', 'Net', etc.
        3. Numeric analysis: row value ≈ sum of rows above until previous total
        
        Returns dict mapping row_idx to sum info.
        """
        sum_info = {}
        
        # Known sum keywords
        sum_keywords = [
            r'(?i)^total\s+',
            r'(?i)^net\s+',
            r'(?i)\btotal$',
            r'(?i)^gross\s+profit',
            r'(?i)^operating\s+income',
            r'(?i)^income\s+before',
        ]
        
        for idx in og_df.index:
            is_sum = False
            sum_type = None
            
            # Check HTML-based sum detection
            if idx in rows_that_are_sum:
                is_sum = True
                sum_type = "html_marker"
            
            # Check label keywords
            human_label = rows_text.get(idx, "")
            for pattern in sum_keywords:
                if re.search(pattern, human_label):
                    is_sum = True
                    sum_type = "keyword_label"
                    break
            
            # Check GAAP tag for sum indicators
            if not is_sum:
                gaap_lower = idx.lower()
                if any(kw in gaap_lower for kw in ['total', 'net', 'gross']):
                    is_sum = True
                    sum_type = "gaap_tag"
            
            if is_sum:
                sum_info[idx] = {
                    "is_sum": True,
                    "sum_type": sum_type,
                    "label": human_label,
                }
        
        return sum_info

    # ═══════════════════════════════════════════════════════════════════════════
    # EQUATION VALIDATION (done by code, not LLM)
    # ═══════════════════════════════════════════════════════════════════════════

    def _validate_equations(
        self,
        mapped_df: pd.DataFrame,
        year_column: str,
    ) -> List[ValidationResult]:
        """
        Validate mapped data against accounting equations.
        
        All calculations done by code - the results inform the LLM.
        """
        results = []
        
        for eq in self.equations:
            eq_name = eq["name"]
            result_item = eq["result"]
            components = eq["components"]
            tolerance = eq["tolerance_pct"]
            
            # Check if we have the result item
            if result_item not in mapped_df.index:
                results.append(ValidationResult(
                    equation_name=eq_name,
                    is_valid=False,
                    expected=0,
                    actual=0,
                    difference=0,
                    tolerance_pct=tolerance,
                    message=f"Missing result item: {result_item}",
                ))
                continue
            
            # Calculate expected value from components
            expected = 0.0
            missing_components = []
            for comp_name, multiplier in components:
                if comp_name not in mapped_df.index:
                    missing_components.append(comp_name)
                    continue
                val = mapped_df.loc[comp_name, year_column]
                if pd.notna(val) and val != 0:
                    expected += float(val) * multiplier
            
            if missing_components:
                # Can't validate if components are missing
                results.append(ValidationResult(
                    equation_name=eq_name,
                    is_valid=False,
                    expected=expected,
                    actual=0,
                    difference=0,
                    tolerance_pct=tolerance,
                    message=f"Missing components: {missing_components}",
                ))
                continue
            
            # Get actual value
            actual = mapped_df.loc[result_item, year_column]
            if pd.isna(actual):
                actual = 0.0
            actual = float(actual)
            
            # Calculate difference
            diff = abs(expected - actual)
            
            # Check tolerance
            base = max(abs(expected), abs(actual), 1)  # Avoid div by zero
            diff_pct = (diff / base) * 100
            is_valid = diff_pct <= tolerance
            
            results.append(ValidationResult(
                equation_name=eq_name,
                is_valid=is_valid,
                expected=expected,
                actual=actual,
                difference=diff,
                tolerance_pct=tolerance,
                message=f"{'✓' if is_valid else '✗'} {eq_name}: expected={expected:,.0f}, actual={actual:,.0f}, diff={diff_pct:.1f}%",
            ))
        
        return results

   