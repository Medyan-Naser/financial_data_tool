"""
TEMPORAL VALIDATOR - Cross-Year 10% Rule Validation

Implements the "10% Rule" for cross-year validation:
- If Year X value from a 2023 filing matches Year X value from a 2022 filing
  within a 10% margin (to account for restatements), the confidence score
  for that row match increases.

This handles the common case where SEC filings overlap years:
- A 2023 10-K filing contains 2023, 2022, 2021 data
- A 2022 10-K filing contains 2022, 2021, 2020 data
- The 2022 values should match (within restatement tolerance)

Usage:
    from temporal_validator import TemporalValidator
    validator = TemporalValidator(historical_statements, tolerance=0.10)
    score = validator.validate_candidate(candidate, row_data, current_columns)
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class TemporalMatch:
    """Result of a single year-to-year comparison."""
    year_column: str        # The column/period being compared
    hist_filing_year: str   # Which historical filing it came from
    current_value: float
    historical_value: float
    pct_difference: float   # Absolute percentage difference
    matched: bool           # Whether within tolerance



