"""
New Unit Detection System - Complete Rewrite

Strategy:
1. Parse table headers for explicit unit declarations
2. Verify with company_facts (filtering by period for quarterly)
3. Use concept-based inference as fallback
4. Store raw values before any multiplication

This replaces the fragmented unit handling across multiple files.
"""

import logging
import math
import pandas as pd
from dataclasses import dataclass
from typing import Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class UnitType(Enum):
    CURRENCY = "currency"
    SHARES = "shares"
    PER_SHARE = "per_share"
    RATIO = "ratio"
    PERCENT = "percent"


@dataclass
class UnitInfo:
    """
    Complete unit information for a financial fact.
    
    IMPORTANT: In our system, values are ALREADY scaled during extraction.
    scale_factor is ALWAYS 1.0 because values are stored in base units (dollars, shares).
    original_scale tracks what scale was applied during extraction.
    """
    unit_type: UnitType
    base_unit: str  # 'USD', 'shares', 'USD/share', etc.
    scale_factor: float = 1.0  # ALWAYS 1 - values already in base units!
    source: str = 'unknown'  # 'header', 'verified', 'concept', 'fallback'
    original_scale: float = 1.0  # What scale was applied (for display/debugging)
    
    def __repr__(self):
        # Show original scale for human readability
        scale_names = {
            1: "",
            1000: " (from thousands)",
            1000000: " (from millions)",
            1000000000: " (from billions)"
        }
        scale_str = scale_names.get(self.original_scale, f" (from x{self.original_scale})")
        return f"{self.base_unit}{scale_str} [{self.source}]"


class UnitDetector:
    """
    Complete unit detection system.
    
    Handles all aspects of unit detection:
    - Table header parsing
    - Company facts verification
    - Concept-based inference
    - Multiple period handling
    """
    
    # Known share-related concepts
    SHARE_CONCEPTS = {
        'WeightedAverageNumberOfSharesOutstandingBasic',
        'WeightedAverageNumberOfDilutedSharesOutstanding',
        'CommonStockSharesOutstanding',
        'CommonStockSharesIssued',
        'SharesOutstanding',
        'SharesIssued',
    }
    
    # Known per-share concepts
    PER_SHARE_CONCEPTS = {
        'EarningsPerShareBasic',
        'EarningsPerShareDiluted',
        'BookValuePerShare',
        'DividendPerShare',
    }
    
    @classmethod
    def parse_table_header(cls, table) -> Tuple[float, float, bool]:
        """
        Parse table header for unit declarations.
        
        IMPORTANT: Extract shares unit FIRST and remove it from text before parsing currency unit.
        This prevents shares unit from being mistakenly used as currency unit.
        
        Returns:
            (currency_scale, shares_scale, has_explicit_units)
        """
        # Get all header text
        headers = table.find_all('th')
        if not headers:
            return 1000, 1, False  # Default: thousands
        
        header_text = ' '.join([h.get_text().lower() for h in headers])
        original_header_text = header_text  # Keep original for logging
        
        # Default values
        currency_scale = 1000  # Default: thousands (most common in US filings)
        shares_scale = 1
        has_explicit_units = False
        
        # STEP 1: Extract shares unit FIRST (and remove from text to avoid confusion)
        shares_text_removed = ""
        if 'shares in billions' in header_text or 'shares in billion' in header_text:
            shares_scale = 1000000000
            # Remove this phrase so it doesn't interfere with currency parsing
            header_text = header_text.replace('shares in billions', '').replace('shares in billion', '')
            shares_text_removed = "shares in billions"
        elif 'shares in millions' in header_text or 'shares in million' in header_text:
            shares_scale = 1000000
            header_text = header_text.replace('shares in millions', '').replace('shares in million', '')
            shares_text_removed = "shares in millions"
        elif 'shares in thousands' in header_text or 'shares in thousand' in header_text:
            shares_scale = 1000
            header_text = header_text.replace('shares in thousands', '').replace('shares in thousand', '')
            shares_text_removed = "shares in thousands"
        
        # STEP 2: Now parse currency unit from the REMAINING text (with shares unit removed)
        # This ensures we don't accidentally parse the shares unit as currency unit
        if 'in billions' in header_text or 'in billion' in header_text:
            currency_scale = 1000000000
            has_explicit_units = True
        elif 'in millions' in header_text or 'in million' in header_text:
            currency_scale = 1000000
            has_explicit_units = True
        elif 'in thousands' in header_text or 'in thousand' in header_text:
            currency_scale = 1000
            has_explicit_units = True
        elif 'in dollars' in header_text or 'in ones' in header_text or 'in dollar' in header_text:
            currency_scale = 1
            has_explicit_units = True
        
        # Note: Currency unit should ALWAYS be present (required by SEC)
        # If we didn't find explicit units, default to thousands
        if not has_explicit_units:
            logger.debug(f"No explicit currency unit found in header, using default (thousands): {original_header_text}")
        
        if has_explicit_units or shares_text_removed:
            scale_names = {1000000000: 'billions', 1000000: 'millions', 1000: 'thousands', 1: 'ones'}
            logger.debug(
                f"Header parsing: currency={scale_names.get(currency_scale, currency_scale)}, "
                f"shares={scale_names.get(shares_scale, shares_scale)}"
                f"{' (shares unit removed: ' + shares_text_removed + ')' if shares_text_removed else ''}"
            )
        
        return currency_scale, shares_scale, has_explicit_units
    
    @classmethod
    def get_company_fact_for_period(cls, company_facts_df, concept: str, 
                                    end_date: str, is_quarterly: bool = False) -> Optional[pd.Series]:
        """
        Get the correct company fact for verification.
        
        For quarterly reports, MUST filter by period length to get 3-month period only!
        This is CRITICAL - quarterly filings contain multiple periods (3-month, 6-month, etc.)
        """
        if company_facts_df is None or company_facts_df.empty:
            return None
        
        # Filter by concept and end date
        filtered = company_facts_df[
            (company_facts_df['fact'] == concept) & 
            (company_facts_df['end'] == end_date)
        ]
        
        if filtered.empty:
            return None
        
        # For quarterly: MUST select 3-month period
        if is_quarterly and len(filtered) > 1 and 'start' in filtered.columns:
            # Calculate period length for each row
            filtered_copy = filtered.copy()
            filtered_copy['period_days'] = (
                pd.to_datetime(filtered_copy['end']) - 
                pd.to_datetime(filtered_copy['start'])
            ).dt.days
            
            # Filter for 85-95 days (3 months = ~90 days)
            quarterly_periods = filtered_copy[
                (filtered_copy['period_days'] >= 85) & 
                (filtered_copy['period_days'] <= 95)
            ]
            
            if not quarterly_periods.empty:
                logger.debug(f"Selected 3-month period for {concept} (from {len(filtered)} options)")
                return quarterly_periods.iloc[0]
            
            # Fallback: use shortest period (likely the quarterly one)
            shortest_idx = filtered_copy['period_days'].idxmin()
            period_days = filtered_copy.loc[shortest_idx, 'period_days']
            logger.warning(f"No 3-month period found for {concept}, using shortest: {period_days} days")
            return filtered_copy.loc[shortest_idx]
        
        return filtered.iloc[0]
    
    @classmethod
    def verify_scale_by_ratio(cls, raw_table_value: float, company_facts_value: float,
                              tolerance: float = 0.10) -> Optional[float]:
        """
        Verify scale by checking if ratio is a clean power of 10.
        
        The ratio between company_facts (always in ones) and table value should be
        a clean power of 10 (1, 1000, 1000000, etc.) with small tolerance for rounding.
        
        Args:
            raw_table_value: Value from HTML table (BEFORE any multiplication)
            company_facts_value: Value from company_facts API (always in ones/dollars)
            tolerance: Acceptable relative error (default 10%)
        
        Returns:
            Scale factor (1, 1000, 1000000, etc.) or None if no clean match
        """
        if raw_table_value == 0 or company_facts_value == 0:
            return None
        
        # Calculate ratio (should be power of 10)
        ratio = abs(company_facts_value) / abs(raw_table_value)
        
        # DEBUG: Log the comparison (use DEBUG level to reduce noise)
        logger.debug(f"[VERIFY] Comparing: table={raw_table_value:,.0f}, facts={company_facts_value:,.0f}, ratio={ratio:,.2f}")
        
        # Test common scale factors
        common_scales = [1000000000, 1000000, 1000, 1]
        
        for scale in common_scales:
            relative_error = abs(ratio - scale) / scale
            if relative_error < tolerance:
                logger.debug(f"Verified scale: {raw_table_value} * {scale} = {company_facts_value} (error: {relative_error*100:.1f}%)")
                return scale
        
        # Check if ratio is ANY power of 10 (even unusual ones like 10000)
        log_ratio = math.log10(ratio)
        if abs(log_ratio - round(log_ratio)) < 0.1:
            suggested_scale = 10 ** round(log_ratio)
            logger.info(f"Unusual scale factor detected: {suggested_scale}")
            return suggested_scale
        
        # No clean match - values don't align
        logger.warning(f"Scale verification failed: ratio={ratio:.2f} is not a clean power of 10")
        return None
    
    @classmethod
    def detect_unit_from_concept(cls, concept: str, human_label: str = "") -> UnitType:
        """
        Infer unit type from GAAP concept name or human label.
        """
        concept_lower = concept.lower()
        label_lower = human_label.lower()
        
        # Check for per-share metrics
        if concept in cls.PER_SHARE_CONCEPTS or 'pershare' in concept_lower:
            return UnitType.PER_SHARE
        if 'per share' in label_lower:
            return UnitType.PER_SHARE
        
        # Check for share counts
        if concept in cls.SHARE_CONCEPTS or 'shares' in concept_lower:
            if 'per' not in concept_lower and 'per' not in label_lower:
                return UnitType.SHARES
        
        # Check for ratios/percentages
        if 'ratio' in concept_lower or 'percentage' in concept_lower or 'percent' in concept_lower:
            return UnitType.RATIO
        if 'ratio' in label_lower or '%' in label_lower:
            return UnitType.RATIO
        
        # Default: currency
        return UnitType.CURRENCY
    
    @classmethod
    def detect_unit_for_row(cls, row_name: str, raw_value: Optional[float], end_date: str,
                           header_currency_scale: float, header_shares_scale: float,
                           company_facts_df, is_quarterly: bool = False,
                           human_label: str = "") -> UnitInfo:
        """
        Detect complete unit information for a single row.
        
        Priority:
        1. Value verification with company_facts (if available)
        2. Table header declaration (explicit units)
        3. Concept-based inference (fallback)
        
        Args:
            row_name: Full fact name (e.g., 'us-gaap_Revenue')
            raw_value: Raw value from HTML (before any multiplication)
            end_date: Period end date
            header_currency_scale: Scale from table header for currency
            header_shares_scale: Scale from table header for shares
            company_facts_df: DataFrame of company facts
            is_quarterly: Whether this is quarterly data
            human_label: Human-readable label for the fact
        
        Returns:
            UnitInfo with complete unit details
        """
        # Extract concept name (remove taxonomy prefix)
        if '_' in row_name:
            concept = row_name.split('_', 1)[1]
        else:
            concept = row_name
        
        # Remove section prefix if present
        if ':' in concept:
            concept = concept.split(':')[-1]
            if '_' in concept:
                concept = concept.split('_', 1)[1]
        
        # Determine unit type from concept
        unit_type = cls.detect_unit_from_concept(concept, human_label)
        
        # Per-share metrics: no scaling
        if unit_type == UnitType.PER_SHARE:
            return UnitInfo(
                unit_type=UnitType.PER_SHARE,
                base_unit='USD/share',
                scale_factor=1.0,
                source='concept',
                original_scale=1.0  # No scaling applied
            )
        
        # Ratios/percentages: no scaling
        if unit_type == UnitType.RATIO:
            return UnitInfo(
                unit_type=UnitType.RATIO,
                base_unit='ratio',
                scale_factor=1.0,
                source='concept',
                original_scale=1.0  # No scaling applied
            )
        
        # Try value verification if we have raw value
        verified_scale = None
        if raw_value is not None and raw_value != 0:
            fact_row = cls.get_company_fact_for_period(
                company_facts_df, concept, end_date, is_quarterly
            )
            
            if fact_row is not None and 'val' in fact_row:
                verified_scale = cls.verify_scale_by_ratio(
                    raw_value, fact_row['val']
                )
        
        # Use verified scale if available
        if verified_scale is not None:
            if unit_type == UnitType.SHARES:
                return UnitInfo(
                    unit_type=UnitType.SHARES,
                    base_unit='shares',
                    scale_factor=1.0,  # Values already scaled!
                    source='verified',
                    original_scale=verified_scale  # Track what was verified
                )
            else:
                return UnitInfo(
                    unit_type=UnitType.CURRENCY,
                    base_unit='USD',
                    scale_factor=1.0,  # Values already scaled!
                    source='verified',
                    original_scale=verified_scale  # Track what was verified
                )
        
        # Fallback: use header scale (assume it was applied in Filling.py)
        if unit_type == UnitType.SHARES:
            return UnitInfo(
                unit_type=UnitType.SHARES,
                base_unit='shares',
                scale_factor=1.0,  # Values already scaled!
                source='header',
                original_scale=header_shares_scale  # Track header scale
            )
        else:
            return UnitInfo(
                unit_type=UnitType.CURRENCY,
                base_unit='USD',
                scale_factor=1.0,  # Values already scaled!
                source='header',
                original_scale=header_currency_scale  # Track header scale
            )
