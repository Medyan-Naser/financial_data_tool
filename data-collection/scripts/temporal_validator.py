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


@dataclass 
class TemporalValidationResult:
    """Full result of temporal validation for a candidate."""
    fact_name: str
    total_comparisons: int
    matched_comparisons: int
    matches: List[TemporalMatch]
    score: float            # Temporal confidence score
    
    @property
    def match_ratio(self) -> float:
        if self.total_comparisons == 0:
            return 0.0
        return self.matched_comparisons / self.total_comparisons


class TemporalValidator:
    """
    Cross-year validation engine.
    
    Compares candidate row values against previously parsed historical
    statements to boost confidence when overlapping years match.
    
    The 10% tolerance accounts for:
    - Restatements
    - Rounding differences across filings
    - Unit/scale corrections between years
    
    Scoring:
    - Each matched year adds +10 to temporal_score
    - A bonus of +15 if ALL overlapping years match
    - Zero-to-zero comparisons are skipped (not informative)
    - If one value is zero and the other isn't, it's a strong negative signal
    """

    # Scoring constants
    PER_YEAR_MATCH_BONUS = 10.0
    ALL_YEARS_MATCH_BONUS = 15.0
    MISMATCH_PENALTY = -20.0
    ZERO_VS_NONZERO_PENALTY = -30.0

    def __init__(self, historical_statements: Dict[str, pd.DataFrame],
                 tolerance: float = 0.10):
        """
        Args:
            historical_statements: Dict of {filing_year: mapped_df} from 
                previously parsed filings for the same company.
                Each mapped_df has standardized fact names as index.
            tolerance: Maximum allowed percentage difference (0.10 = 10%)
        """
        self.historical_statements = historical_statements or {}
        self.tolerance = tolerance

    def validate_candidate(self, fact_name: str, row_data: pd.Series) -> TemporalValidationResult:
        """
        Validate a candidate's row data against historical statements.
        
        Args:
            fact_name: The standardized fact name (e.g., "Total revenue")
            row_data: Series with column names as date/period keys
        
        Returns:
            TemporalValidationResult with score and match details
        """
        result = TemporalValidationResult(
            fact_name=fact_name,
            total_comparisons=0,
            matched_comparisons=0,
            matches=[],
            score=0.0,
        )

        if not self.historical_statements:
            return result

        current_columns = row_data.index.tolist()

        for hist_year, hist_df in self.historical_statements.items():
            # Check if this fact exists in historical data
            if fact_name not in hist_df.index:
                continue

            hist_row = hist_df.loc[fact_name]

            # Find overlapping columns (years that exist in both)
            common_cols = [col for col in current_columns if col in hist_row.index]
            if not common_cols:
                continue

            for col in common_cols:
                curr_val = row_data[col]
                hist_val = hist_row[col]

                # Skip NaN comparisons
                if pd.isna(curr_val) or pd.isna(hist_val):
                    continue

                result.total_comparisons += 1

                # Skip zero==zero (not informative)
                if curr_val == 0 and hist_val == 0:
                    continue

                # Historical value is 0 -> fact wasn't mapped in the older filing.
                # This is NOT a mismatch; just no data to compare. Skip.
                if hist_val == 0:
                    continue

                # Current value is 0 but historical is non-zero: we might be
                # matching the wrong row. Mild penalty.
                if curr_val == 0:
                    match = TemporalMatch(
                        year_column=str(col),
                        hist_filing_year=str(hist_year),
                        current_value=float(curr_val),
                        historical_value=float(hist_val),
                        pct_difference=1.0,
                        matched=False,
                    )
                    result.matches.append(match)
                    result.score += self.ZERO_VS_NONZERO_PENALTY
                    logger.debug(
                        f"  Temporal MISMATCH (current zero, hist nonzero): {fact_name} {col}: "
                        f"current={curr_val:,.0f} vs hist({hist_year})={hist_val:,.0f}"
                    )
                    continue

                # Calculate percentage difference
                avg = (abs(curr_val) + abs(hist_val)) / 2
                diff = abs(curr_val - hist_val)
                pct_diff = diff / avg if avg != 0 else 0

                is_match = pct_diff <= self.tolerance

                match = TemporalMatch(
                    year_column=str(col),
                    hist_filing_year=str(hist_year),
                    current_value=float(curr_val),
                    historical_value=float(hist_val),
                    pct_difference=pct_diff,
                    matched=is_match,
                )
                result.matches.append(match)

                if is_match:
                    result.matched_comparisons += 1
                    result.score += self.PER_YEAR_MATCH_BONUS
                    logger.debug(
                        f"  Temporal MATCH: {fact_name} {col}: "
                        f"current={curr_val:,.0f} vs hist({hist_year})={hist_val:,.0f} "
                        f"(diff={pct_diff*100:.1f}%)"
                    )
                else:
                    result.score += self.MISMATCH_PENALTY
                    logger.debug(
                        f"  Temporal MISMATCH: {fact_name} {col}: "
                        f"current={curr_val:,.0f} vs hist({hist_year})={hist_val:,.0f} "
                        f"(diff={pct_diff*100:.1f}%)"
                    )

        # Bonus if ALL comparisons matched
        if result.total_comparisons > 0 and result.matched_comparisons == result.total_comparisons:
            result.score += self.ALL_YEARS_MATCH_BONUS

        return result

