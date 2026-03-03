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

