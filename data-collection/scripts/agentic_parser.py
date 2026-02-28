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

