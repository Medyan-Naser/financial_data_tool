"""
SUMMATION CHECKER - Sum-Check Utility for Financial Statement Hierarchy

Before final selection, this module checks if a candidate row is the sum 
of a subset of rows above it. This is critical for identifying "Total" rows
like Total Revenue, Total Operating Expenses, Total Assets, etc.

Rules:
1. If Candidate_Row ≈ Sum(other_rows) within tolerance, flag as "Total" type
2. If Candidate_Row ≈ Sum(abs(other_rows)), also flag (accounts for sign conventions)
3. For each row, try both positive and negative since sums can be reported 
   as positive but component rows are negative (e.g., expenses)
4. If multiple regex matches exist for a "Total" concept, prioritize the one 
   that actually functions as a sum

Usage:
    from summation_checker import SummationChecker
    checker = SummationChecker(og_df, rows_that_are_sum, cal_facts)
    result = checker.check_row(row_idx, row_data)
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from itertools import combinations

logger = logging.getLogger(__name__)


@dataclass
class SumCheckResult:
    """Result of a summation check for a single row."""
    row_idx: str
    is_sum_row: bool
    sum_type: str  # 'exact', 'absolute', 'partial', 'xml_calc', 'none'
    component_rows: List[str]  # Row indices that sum to this row
    computed_sum: float
    actual_value: float
    tolerance_used: float
    pct_difference: float
    confidence: float  # 0.0 to 1.0

    def __repr__(self):
        if self.is_sum_row:
            return (f"SumCheckResult(row={self.row_idx}, type={self.sum_type}, "
                    f"components={len(self.component_rows)}, conf={self.confidence:.2f})")
        return f"SumCheckResult(row={self.row_idx}, is_sum=False)"


class SummationChecker:
    """
    Checks if rows in a financial statement are sums of other rows.
    
    Uses multiple strategies:
    1. XML calculation linkbase (cal_facts) - most authoritative
    2. HTML class markers (rows_that_are_sum from SEC HTML)
    3. Numerical verification - brute force sum checking
    
    Scoring:
    - XML calc confirmed sum: +25 to summation_score
    - HTML class marker + numeric match: +20
    - Numeric sum match (exact): +15
    - Numeric sum match (absolute values): +10
    - Partial sum match (subset): +5
    """

    # Scoring constants
    XML_CALC_BONUS = 25.0
    HTML_MARKER_BONUS = 20.0
    EXACT_SUM_BONUS = 15.0
    ABS_SUM_BONUS = 10.0
    PARTIAL_SUM_BONUS = 5.0
    IS_TOTAL_BONUS = 20.0  # Bonus for candidates whose fact is a "Total" type

    # Total-type fact patterns
    TOTAL_FACT_KEYWORDS = {
        'total', 'net cash', 'gross profit', 'operating income',
        'stockholders equity', 'current assets', 'current liabilities',
        'noncurrent assets', 'noncurrent liabilities',
    }

    def __init__(self, og_df: pd.DataFrame,
                 rows_that_are_sum: List[str],
                 cal_facts: Optional[Dict] = None,
                 tolerance: float = 0.02):
        """
        Args:
            og_df: Original DataFrame from filing (rows = facts, cols = periods)
            rows_that_are_sum: List of row indices marked as sum rows in HTML
            cal_facts: Calculation relationships from _cal.xml
            tolerance: Tolerance for sum matching (default 2% for rounding)
        """
        self.og_df = og_df
        self.rows_that_are_sum = set(rows_that_are_sum or [])
        self.cal_facts = cal_facts or {}
        self.tolerance = tolerance
        
        # Pre-compute row values for first non-zero column for fast checking
        self._row_values = {}
        if og_df is not None and not og_df.empty:
            first_col = og_df.columns[0] if len(og_df.columns) > 0 else None
            if first_col is not None:
                for idx in og_df.index:
                    val = og_df.loc[idx, first_col]
                    if not pd.isna(val):
                        self._row_values[idx] = float(val)

    def check_row(self, row_idx: str, row_data: Optional[pd.Series] = None) -> SumCheckResult:
        """
        Check if a row is a summation of other rows.
        
        Tries strategies in order of authority:
        1. XML calculation linkbase
        2. HTML class markers + numeric verification
        3. Numerical brute-force (rows above this one)
        
        Args:
            row_idx: Index of the row to check
            row_data: Optional row data (if not in og_df)
        
        Returns:
            SumCheckResult
        """
        if row_data is None and row_idx in self.og_df.index:
            row_data = self.og_df.loc[row_idx]

        default = SumCheckResult(
            row_idx=row_idx, is_sum_row=False, sum_type='none',
            component_rows=[], computed_sum=0.0,
            actual_value=0.0, tolerance_used=self.tolerance,
            pct_difference=1.0, confidence=0.0,
        )

        if row_data is None:
            return default

        # Get actual value (use first non-zero column)
        actual_value = 0.0
        for val in row_data:
            if not pd.isna(val) and val != 0:
                actual_value = float(val)
                break

        if actual_value == 0:
            return default

        default.actual_value = actual_value

        # Strategy 1: XML calculation linkbase
        xml_result = self._check_xml_calc(row_idx, row_data, actual_value)
        if xml_result and xml_result.is_sum_row:
            return xml_result

        # Strategy 2: HTML class markers
        if row_idx in self.rows_that_are_sum:
            numeric_result = self._check_numeric_sum(row_idx, row_data, actual_value)
            if numeric_result and numeric_result.is_sum_row:
                numeric_result.confidence = min(1.0, numeric_result.confidence + 0.2)
                return numeric_result
            # Even if numeric check fails, HTML marker is meaningful
            return SumCheckResult(
                row_idx=row_idx, is_sum_row=True, sum_type='html_marker',
                component_rows=[], computed_sum=0.0,
                actual_value=actual_value, tolerance_used=self.tolerance,
                pct_difference=0.0, confidence=0.5,
            )

        # Strategy 3: Numerical brute-force
        numeric_result = self._check_numeric_sum(row_idx, row_data, actual_value)
        if numeric_result and numeric_result.is_sum_row:
            return numeric_result

        return default
