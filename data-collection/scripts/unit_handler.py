"""
Unit Handling System for Financial Statements

Implements multi-layer unit detection and normalization similar to edgartools.
Handles:
- Currency units (USD, EUR, etc.)
- Share counts
- Per-share metrics (USD/share, EPS)
- Ratios and percentages
- Scale factors (thousands, millions, billions)
"""

import re
import logging
from typing import Optional, Dict, Tuple, List
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class UnitType(Enum):
    """Types of units in financial statements."""
    CURRENCY = "currency"
    SHARES = "shares"
    PER_SHARE = "per_share"
    RATIO = "ratio"
    PERCENTAGE = "percentage"
    PURE_NUMBER = "pure"
    OTHER = "other"


@dataclass
class UnitInfo:
    """
    Complete unit information for a financial fact.
    """
    unit_type: UnitType
    base_unit: str  # e.g., 'USD', 'shares', 'usdPerShare'
    scale_factor: float  # 1, 1000, 1000000, etc.
    original_unit_ref: Optional[str] = None  # Original XBRL unitRef
    decimals: Optional[int] = None  # XBRL decimals attribute
    
    def __repr__(self):
        scale_name = {1: "", 1000: " (thousands)", 1000000: " (millions)", 1000000000: " (billions)"}
        scale_str = scale_name.get(self.scale_factor, f" (x{self.scale_factor})")
        return f"{self.base_unit}{scale_str}"


class UnitNormalizer:
    """
    Multi-layer unit detection and normalization system.
    """
    
    # Currency mappings
    CURRENCY_MAPPINGS = {
        'USD': ['USD', 'US DOLLAR', 'DOLLARS', 'usd', 'US$', 'DOLLAR', 'iso4217:USD', 'U-Monetary'],
        'EUR': ['EUR', 'EURO', 'EUROS', 'eur', '€', 'iso4217:EUR'],
        'GBP': ['GBP', 'POUND', 'POUNDS', 'gbp', '£', 'BRITISH POUND', 'iso4217:GBP'],
        'JPY': ['JPY', 'YEN', 'yen', 'jpy', '¥', 'JAPANESE YEN', 'iso4217:JPY'],
        'CNY': ['CNY', 'YUAN', 'RMB', 'cny', 'iso4217:CNY'],
        'CAD': ['CAD', 'CANADIAN DOLLAR', 'cad', 'iso4217:CAD'],
    }
    
    # Share mappings
    SHARE_MAPPINGS = {
        'shares': ['shares', 'share', 'SHARES', 'SHARE', 'STOCK', 'EQUITY', 'xbrli:shares', 'U-Shares'],
        'shares_unit': ['shares_unit', 'share_unit', 'SHARES_UNIT'],
    }
    
    # Per-share mappings (most specific - checked first)
    PER_SHARE_MAPPINGS = {
        'usdPerShare': ['USD/shares', 'USD per share', 'USD/share', 'usd/shares', 'U-USD-per-shares'],
        'eurPerShare': ['EUR/shares', 'EUR per share', 'EUR/share', 'eur/shares'],
        'usdPerShare_unit': ['USD/shares_unit', 'USD per share unit', 'USD/share_unit'],
    }
    
    # Known share-based concepts (for concept-based inference)
    SHARE_CONCEPTS = [
        'CommonStockSharesOutstanding',
        'CommonStockSharesIssued',
        'WeightedAverageNumberOfSharesOutstandingBasic',
        'WeightedAverageNumberOfSharesOutstandingDiluted',
        'WeightedAverageNumberOfDilutedSharesOutstanding',
        'PreferredStockSharesOutstanding',
        'TreasuryStockShares',
    ]
    
    # Known per-share concepts (for concept-based inference)
    PER_SHARE_CONCEPTS = [
        'EarningsPerShareBasic',
        'EarningsPerShareDiluted',
        'BookValuePerShare',
        'DividendsPerShare',
        'CashDividendsPerShare',
    ]
    
    # Keywords for label-based detection
    SHARE_KEYWORDS = [
        'shares outstanding', 'number of shares', 'share count',
        'weighted average', 'diluted shares', 'basic shares'
    ]
    
    PER_SHARE_KEYWORDS = [
        'per share', 'per common share', 'earnings per share', 'eps',
        'book value per share', 'dividend per share'
    ]
    
    RATIO_KEYWORDS = [
        'ratio', 'margin', 'percentage', 'rate', 'percent', '%',
        'return on', 'yield'
    ]
    
    @classmethod
    def normalize_unit_from_company_facts(cls, unit_str: str) -> Tuple[UnitType, str]:
        """
        Normalize a unit string from company facts API.
        
        Args:
            unit_str: Unit string from company_facts (e.g., 'USD', 'shares', 'USD/shares')
            
        Returns:
            Tuple of (UnitType, normalized_unit_name)
        """
        unit_lower = unit_str.lower().strip()
        
        # Check per-share units FIRST (most specific)
        for normalized, variants in cls.PER_SHARE_MAPPINGS.items():
            if any(variant.lower() in unit_lower for variant in variants):
                return UnitType.PER_SHARE, normalized
        
        # Check currencies
        for normalized, variants in cls.CURRENCY_MAPPINGS.items():
            if any(variant.lower() in unit_lower for variant in variants):
                return UnitType.CURRENCY, normalized
        
        # Check shares
        for normalized, variants in cls.SHARE_MAPPINGS.items():
            if any(variant.lower() in unit_lower for variant in variants):
                return UnitType.SHARES, normalized
        
        # Check if it's a ratio/percentage (pure number)
        if 'pure' in unit_lower or unit_lower == '':
            return UnitType.RATIO, 'pure'
        
        logger.warning(f"Unknown unit: {unit_str}")
        return UnitType.OTHER, unit_str
    
    @classmethod
    def detect_unit_from_concept(cls, fact_name: str, human_label: str) -> Optional[Tuple[UnitType, str]]:
        """
        Detect unit based on GAAP concept name (concept-based inference).
        
        Args:
            fact_name: GAAP fact name (e.g., 'us-gaap_EarningsPerShareBasic')
            human_label: Human-readable label
            
        Returns:
            Tuple of (UnitType, unit_name) or None if not detected
        """
        # Extract concept from fact name (remove prefix)
        concept = fact_name.split('_')[-1] if '_' in fact_name else fact_name
        
        # Check per-share concepts
        if any(psc in concept for psc in cls.PER_SHARE_CONCEPTS):
            return UnitType.PER_SHARE, 'usdPerShare'
        
        # Check share concepts
        if any(sc in concept for sc in cls.SHARE_CONCEPTS):
            return UnitType.SHARES, 'shares'
        
        # Check label for per-share keywords
        label_lower = human_label.lower()
        if any(keyword in label_lower for keyword in cls.PER_SHARE_KEYWORDS):
            return UnitType.PER_SHARE, 'usdPerShare'
        
        # Check label for share keywords
        if any(keyword in label_lower for keyword in cls.SHARE_KEYWORDS):
            return UnitType.SHARES, 'shares'
        
        # Check label for ratio keywords
        if any(keyword in label_lower for keyword in cls.RATIO_KEYWORDS):
            return UnitType.RATIO, 'pure'
        
        return None
    
    @classmethod
    def determine_scale_factor(cls, decimals: Optional[int]) -> float:
        """
        Determine scale factor from XBRL decimals attribute.
        
        Args:
            decimals: XBRL decimals value
            
        Returns:
            Scale factor (1, 1000, 1000000, etc.)
        """
        if decimals is None:
            return 1.0
        
        # Negative decimals indicate scale
        # decimals=-6 means millions, decimals=-3 means thousands
        if decimals <= -9:
            return 1000000000  # Billions
        elif decimals <= -6:
            return 1000000  # Millions
        elif decimals <= -3:
            return 1000  # Thousands
        else:
            return 1.0  # No scaling
    
    @classmethod
    def verify_unit_by_value_comparison(cls, 
                                        table_value: float, 
                                        company_facts_value: float,
                                        tolerance: float = 0.10) -> float:
        """
        Verify unit scale by comparing table value with company_facts value.
        
        This is the OLD approach - comparing actual numbers to detect scale.
        More reliable than trusting unit strings alone.
        
        The ratio between facts_value and table_value should be a clean power of 10
        (1, 10, 100, 1000, 10000, etc.) with small tolerance for rounding.
        
        Args:
            table_value: Value extracted from HTML table (RAW, before any multiplication)
            company_facts_value: Value from company_facts API (always in ones/dollars)
            tolerance: Acceptable deviation from perfect ratio (default 10%)
            
        Returns:
            Scale factor (1, 1000, 1000000, etc.) or None if no clean match
        """
        if table_value == 0 or company_facts_value == 0:
            return None
        
        # Use absolute values for comparison
        table_val = abs(table_value)
        facts_val = abs(company_facts_value)
        
        # Calculate the ratio
        ratio = facts_val / table_val
        
        # Define valid conversion factors (powers of 10)
        # Test from largest to smallest to prefer larger scales
        conversion_factors = [
            (1000000000, "billions"),
            (1000000, "millions"),
            (1000, "thousands"),
            (1, "ones/dollars")
        ]
        
        # Check if ratio is close to any valid factor
        for factor, unit_name in conversion_factors:
            # Calculate relative error
            relative_error = abs(ratio - factor) / factor
            
            if relative_error < tolerance:
                logger.debug(f"Unit verified: table={table_val} * {factor} ({unit_name}) = {facts_val}, error={relative_error*100:.1f}%")
                return factor
        
        # Check if ratio is a power of 10 but not in our list
        import math
        log_ratio = math.log10(ratio)
        if abs(log_ratio - round(log_ratio)) < 0.1:  # Close to integer power of 10
            suggested_factor = 10 ** round(log_ratio)
            logger.warning(f"Unusual scale factor detected: {suggested_factor}")
            return suggested_factor
        
        # No clean match found - values don't align
        logger.warning(f"Unit mismatch: table={table_val}, facts={facts_val}, ratio={ratio:.2f} (not a clean power of 10)")
        return None
    
    @classmethod
    def get_unit_info_from_company_facts(cls, 
                                         company_facts_df, 
                                         fact_name: str, 
                                         end_date: str,
                                         human_label: str = "",
                                         table_value: Optional[float] = None,
                                         is_quarterly: bool = False) -> Optional[UnitInfo]:
        """
        Extract complete unit information from company facts DataFrame.
        
        This is the main entry point for unit detection.
        Uses multi-layer approach:
        1. Try to find fact in company_facts_df (most reliable)
        2. VERIFY scale by comparing actual values (OLD approach - most accurate!)
        3. Fall back to concept-based inference
        
        Args:
            company_facts_df: DataFrame with company facts
            fact_name: GAAP fact name
            end_date: End date for the fact
            human_label: Human-readable label for fallback detection
            table_value: Actual value from HTML table (for verification)
            is_quarterly: If True, prefer 3-month periods (not 6-month YTD)
            
        Returns:
            UnitInfo object or None
        """
        # Extract concept from fact name (remove taxonomy prefix)
        concept = fact_name.split('_')[-1] if '_' in fact_name else fact_name
        
        try:
            # Try to find the fact in company_facts_df
            filtered = company_facts_df[
                (company_facts_df['fact'] == concept) & 
                (company_facts_df['end'] == end_date)
            ]
            
            if not filtered.empty:
                # For quarterly reports, there may be multiple periods with same end date
                # (e.g., 3-month Q2 and 6-month YTD both ending 2025-06-30)
                # We need to pick the right one!
                
                if is_quarterly and len(filtered) > 1 and 'start' in filtered.columns:
                    import pandas as pd
                    # Calculate period length for each row
                    filtered_with_length = filtered.copy()
                    filtered_with_length['period_days'] = (
                        pd.to_datetime(filtered_with_length['end']) - 
                        pd.to_datetime(filtered_with_length['start'])
                    ).dt.days
                    
                    # For quarterly: prefer 85-95 day periods (3 months)
                    # For YTD periods: 180+ days
                    quarterly_rows = filtered_with_length[
                        (filtered_with_length['period_days'] >= 85) & 
                        (filtered_with_length['period_days'] <= 95)
                    ]
                    
                    if not quarterly_rows.empty:
                        # Use the 3-month period
                        filtered = quarterly_rows
                        logger.debug(f"Selected 3-month period from {len(filtered_with_length)} options")
                    else:
                        # Fallback: use shortest period (likely most relevant)
                        shortest_idx = filtered_with_length['period_days'].idxmin()
                        filtered = filtered_with_length.loc[[shortest_idx]]
                        logger.debug(f"No 3-month period found, using shortest: {filtered.iloc[0]['period_days']} days")
                
                row = filtered.iloc[0]
                
                # Get unit from company facts
                if 'unit' in row:
                    unit_str = row['unit']
                else:
                    # Fallback: infer from value magnitude and concept
                    logger.warning(f"No unit column found for {fact_name}")
                    concept_detection = cls.detect_unit_from_concept(fact_name, human_label)
                    if concept_detection:
                        unit_type, base_unit = concept_detection
                        return UnitInfo(
                            unit_type=unit_type,
                            base_unit=base_unit,
                            scale_factor=1.0,
                            original_unit_ref=None
                        )
                    return None
                
                # Normalize the unit
                unit_type, base_unit = cls.normalize_unit_from_company_facts(unit_str)
                
                # VERIFY scale by comparing actual values (OLD method - most reliable!)
                scale_factor = None
                if table_value is not None and 'val' in row:
                    company_facts_value = row['val']
                    scale_factor = cls.verify_unit_by_value_comparison(
                        table_value, 
                        company_facts_value
                    )
                
                # If verification failed, try to infer from unit string
                if scale_factor is None:
                    if 'Million' in unit_str or 'million' in unit_str:
                        scale_factor = 1000000
                        logger.info(f"Using scale from unit string: {unit_str} -> millions")
                    elif 'Thousand' in unit_str or 'thousand' in unit_str:
                        scale_factor = 1000
                        logger.info(f"Using scale from unit string: {unit_str} -> thousands")
                    elif 'Billion' in unit_str or 'billion' in unit_str:
                        scale_factor = 1000000000
                        logger.info(f"Using scale from unit string: {unit_str} -> billions")
                    else:
                        # Check if it's shares (no scale) or ratio (no scale)
                        if unit_type == UnitType.SHARES or unit_type == UnitType.RATIO:
                            scale_factor = 1.0
                        else:
                            # Default: assume no scaling needed
                            scale_factor = 1.0
                            logger.warning(f"Could not verify scale for {fact_name}, defaulting to 1.0")
                
                return UnitInfo(
                    unit_type=unit_type,
                    base_unit=base_unit,
                    scale_factor=scale_factor,
                    original_unit_ref=unit_str,
                    decimals=None
                )
        
        except Exception as e:
            logger.debug(f"Could not get unit from company_facts for {fact_name}: {e}")
        
        # Fallback: concept-based inference
        concept_detection = cls.detect_unit_from_concept(fact_name, human_label)
        if concept_detection:
            unit_type, base_unit = concept_detection
            return UnitInfo(
                unit_type=unit_type,
                base_unit=base_unit,
                scale_factor=1.0,
                original_unit_ref=None
            )
        
        # Last resort: assume currency (most common)
        logger.warning(f"Could not detect unit for {fact_name}, assuming USD")
        return UnitInfo(
            unit_type=UnitType.CURRENCY,
            base_unit='USD',
            scale_factor=1.0,
            original_unit_ref=None
        )
    
    @classmethod
    def format_unit_for_display(cls, unit_info: UnitInfo) -> str:
        """
        Format unit information for display in financial statements.
        
        Args:
            unit_info: UnitInfo object
            
        Returns:
            Human-readable unit string (e.g., "USD (millions)", "shares (thousands)", "USD per share")
        """
        if unit_info.unit_type == UnitType.PER_SHARE:
            return "USD per share"
        elif unit_info.unit_type == UnitType.SHARES:
            if unit_info.scale_factor == 1000:
                return "shares (thousands)"
            elif unit_info.scale_factor == 1000000:
                return "shares (millions)"
            else:
                return "shares"
        elif unit_info.unit_type == UnitType.CURRENCY:
            currency = unit_info.base_unit
            if unit_info.scale_factor == 1000:
                return f"{currency} (thousands)"
            elif unit_info.scale_factor == 1000000:
                return f"{currency} (millions)"
            elif unit_info.scale_factor == 1000000000:
                return f"{currency} (billions)"
            else:
                return currency
        elif unit_info.unit_type == UnitType.RATIO:
            return "ratio"
        elif unit_info.unit_type == UnitType.PERCENTAGE:
            return "%"
        else:
            return str(unit_info.base_unit)
    
    @classmethod
    def are_compatible(cls, unit1: UnitInfo, unit2: UnitInfo) -> bool:
        """
        Check if two units are compatible for calculations.
        
        Args:
            unit1, unit2: UnitInfo objects
            
        Returns:
            True if units can be combined in calculations
        """
        # Same base unit is always compatible
        if unit1.base_unit == unit2.base_unit:
            return True
        
        # Same unit type might be compatible
        if unit1.unit_type == unit2.unit_type:
            if unit1.unit_type == UnitType.CURRENCY:
                # Different currencies are NOT compatible
                return unit1.base_unit == unit2.base_unit
            elif unit1.unit_type == UnitType.SHARES:
                # shares and shares_unit are compatible
                return True
            elif unit1.unit_type == UnitType.PER_SHARE:
                # Per-share units must match exactly
                return unit1.base_unit == unit2.base_unit
        
        return False


def extract_unit_from_company_facts_row(company_facts_df, fact: str, end_date: str) -> Optional[str]:
    """
    Helper function to extract unit from company facts for a specific fact and date.
    
    Returns the actual unit string from the API (e.g., 'USD', 'shares', 'USD/shares')
    """
    try:
        filtered = company_facts_df[
            (company_facts_df['fact'] == fact) & 
            (company_facts_df['end'] == end_date)
        ]
        
        if not filtered.empty:
            # The company_facts_df was built from units dict
            # We need to track which unit each row came from
            # This requires modifying how we build company_facts_DF in Filling.py
            return filtered.iloc[0].get('unit', None)
    except Exception as e:
        logger.debug(f"Could not extract unit for {fact}: {e}")
    
    return None
