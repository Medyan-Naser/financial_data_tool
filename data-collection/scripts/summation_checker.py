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
