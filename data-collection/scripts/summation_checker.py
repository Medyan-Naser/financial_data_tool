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

    def _check_xml_calc(self, row_idx: str, row_data: pd.Series,
                        actual_value: float) -> Optional[SumCheckResult]:
        """Check using XML calculation linkbase."""
        if not self.cal_facts:
            return None

        # Extract the fact name from the row index
        fact_name = row_idx
        if '_' in row_idx:
            fact_name = row_idx.split('_', 1)[-1]

        # Look for this fact in cal_facts
        children = None
        for parent_fact, child_list in self.cal_facts.items():
            parent_clean = parent_fact
            if '_' in parent_fact:
                parent_clean = parent_fact.split('_', 1)[-1]
            if parent_clean.lower() == fact_name.lower():
                children = child_list
                break

        if not children:
            return None

        # Find matching rows in og_df for each child
        component_rows = []
        for child in children:
            child_fact = child.get('fact', '') if isinstance(child, dict) else str(child)
            if '_' in child_fact:
                child_fact = child_fact.split('_', 1)[-1]
            
            # Find row in og_df that matches this child
            for idx in self.og_df.index:
                idx_fact = idx
                if '_' in idx:
                    idx_fact = idx.split('_', 1)[-1]
                if idx_fact.lower() == child_fact.lower():
                    component_rows.append(idx)
                    break

        if not component_rows:
            return None

        # Compute sum from components
        first_col = self.og_df.columns[0]
        computed = sum(
            float(self.og_df.loc[c, first_col]) 
            for c in component_rows 
            if c in self.og_df.index and not pd.isna(self.og_df.loc[c, first_col])
        )

        pct_diff = self._pct_diff(actual_value, computed)

        if pct_diff <= self.tolerance:
            return SumCheckResult(
                row_idx=row_idx, is_sum_row=True, sum_type='xml_calc',
                component_rows=component_rows, computed_sum=computed,
                actual_value=actual_value, tolerance_used=self.tolerance,
                pct_difference=pct_diff, confidence=0.95,
            )

        # Try with absolute values (sign convention differences)
        computed_abs = sum(
            abs(float(self.og_df.loc[c, first_col]))
            for c in component_rows
            if c in self.og_df.index and not pd.isna(self.og_df.loc[c, first_col])
        )
        pct_diff_abs = self._pct_diff(abs(actual_value), computed_abs)

        if pct_diff_abs <= self.tolerance:
            return SumCheckResult(
                row_idx=row_idx, is_sum_row=True, sum_type='xml_calc',
                component_rows=component_rows, computed_sum=computed_abs,
                actual_value=actual_value, tolerance_used=self.tolerance,
                pct_difference=pct_diff_abs, confidence=0.90,
            )

        return None

    def _check_numeric_sum(self, row_idx: str, row_data: pd.Series,
                           actual_value: float) -> Optional[SumCheckResult]:
        """
        Check if this row is a sum of rows above it.
        
        Strategy: Look at contiguous blocks of rows above this one.
        Financial statements have a structure where totals follow
        their components.
        """
        row_list = list(self.og_df.index)
        try:
            current_pos = row_list.index(row_idx)
        except ValueError:
            return None

        if current_pos == 0:
            return None

        # Get rows above (up to 20 rows)
        lookback = min(current_pos, 20)
        rows_above = row_list[current_pos - lookback:current_pos]

        first_col = self.og_df.columns[0]
        
        # Get values for rows above
        above_values = {}
        for r in rows_above:
            val = self.og_df.loc[r, first_col]
            if not pd.isna(val) and val != 0:
                above_values[r] = float(val)

        if not above_values:
            return None

        # Try: sum of ALL rows above (within lookback)
        # Try contiguous subsets starting from just above
        best_result = None
        best_confidence = 0.0

        for start in range(len(rows_above)):
            subset_rows = rows_above[start:]
            subset_vals = [above_values[r] for r in subset_rows if r in above_values]
            
            if not subset_vals:
                continue

            # Try positive sum
            computed = sum(subset_vals)
            pct_diff = self._pct_diff(actual_value, computed)
            if pct_diff <= self.tolerance:
                conf = 0.8 if len(subset_vals) >= 2 else 0.5
                if conf > best_confidence:
                    best_confidence = conf
                    best_result = SumCheckResult(
                        row_idx=row_idx, is_sum_row=True, sum_type='exact',
                        component_rows=[r for r in subset_rows if r in above_values],
                        computed_sum=computed, actual_value=actual_value,
                        tolerance_used=self.tolerance, pct_difference=pct_diff,
                        confidence=conf,
                    )

            # Try negative sum (actual might be negative of sum)
            pct_diff_neg = self._pct_diff(actual_value, -computed)
            if pct_diff_neg <= self.tolerance:
                conf = 0.75 if len(subset_vals) >= 2 else 0.45
                if conf > best_confidence:
                    best_confidence = conf
                    best_result = SumCheckResult(
                        row_idx=row_idx, is_sum_row=True, sum_type='exact',
                        component_rows=[r for r in subset_rows if r in above_values],
                        computed_sum=-computed, actual_value=actual_value,
                        tolerance_used=self.tolerance, pct_difference=pct_diff_neg,
                        confidence=conf,
                    )

            # Try absolute sum
            computed_abs = sum(abs(v) for v in subset_vals)
            pct_diff_abs = self._pct_diff(abs(actual_value), computed_abs)
            if pct_diff_abs <= self.tolerance:
                conf = 0.7 if len(subset_vals) >= 2 else 0.4
                if conf > best_confidence:
                    best_confidence = conf
                    best_result = SumCheckResult(
                        row_idx=row_idx, is_sum_row=True, sum_type='absolute',
                        component_rows=[r for r in subset_rows if r in above_values],
                        computed_sum=computed_abs, actual_value=actual_value,
                        tolerance_used=self.tolerance, pct_difference=pct_diff_abs,
                        confidence=conf,
                    )

        return best_result
