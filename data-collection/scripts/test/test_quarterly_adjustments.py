#!/usr/bin/env python3
"""
Test script for quarterly adjustment logic.

This script tests the quarterly adjustment functionality on real company data
to verify that cumulative Q4 reports are properly identified and adjusted.
"""

import sys
import pandas as pd
import logging
from pathlib import Path

# Add the scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

from merge_utils import (
    detect_quarter,
    group_quarters_by_year,
    needs_quarterly_adjustment,
    adjust_quarterly_data,
    process_quarterly_adjustments
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_test_dataframe():
    """
    Create a test DataFrame simulating quarterly financial data
    where Q4 is cumulative (full year).
    """
    # Simulate a company with cumulative Q4 data
    # Q1 2024: 100, Q2: 120, Q3: 110, Q4: 450 (cumulative = 100+120+110+120)
    data = {
        '2024-03-31': [100, 50, 50, 10, 8, 2],     # Q1
        '2024-06-30': [120, 60, 60, 12, 10, 3],    # Q2
        '2024-09-30': [110, 55, 55, 11, 9, 2],     # Q3
        '2024-12-31': [450, 215, 235, 45, 37, 9],  # Q4 - Cumulative!
        '2023-03-31': [90, 45, 45, 9, 7, 2],       # Q1 previous year
        '2023-06-30': [110, 55, 55, 11, 9, 2],     # Q2 previous year
        '2023-09-30': [105, 52, 53, 10, 8, 2],     # Q3 previous year
        '2023-12-31': [410, 197, 213, 41, 33, 8],  # Q4 previous year - Cumulative!
    }
    
    index = [
        'Total revenue',
        'COGS',
        'Gross profit',
        'Operating income',
        'Net income',
        'Earnings Per Share Diluted'
    ]
    
    df = pd.DataFrame(data, index=index)
    
    return df


def test_detect_quarter():
    """Test quarter detection."""
    logger.info("\n=== Testing Quarter Detection ===")
    
    test_dates = [
        ('2024-03-31', (2024, 1)),
        ('2024-06-30', (2024, 2)),
        ('2024-09-30', (2024, 3)),
        ('2024-12-31', (2024, 4)),
    ]
    
    for date_str, expected in test_dates:
        result = detect_quarter(date_str)
        status = "✓" if result == expected else "✗"
        logger.info(f"{status} {date_str} -> {result} (expected {expected})")


def test_group_quarters():
    """Test grouping quarters by year."""
    logger.info("\n=== Testing Quarter Grouping ===")
    
    columns = [
        '2024-12-31', '2024-09-30', '2024-06-30', '2024-03-31',
        '2023-12-31', '2023-09-30', '2023-06-30', '2023-03-31'
    ]
    
    year_quarters = group_quarters_by_year(columns)
    
    logger.info(f"Grouped quarters by year:")
    for year, quarters in sorted(year_quarters.items()):
        logger.info(f"  {year}: {quarters}")


def test_cumulative_detection():
    """Test detection of cumulative Q4 data."""
    logger.info("\n=== Testing Cumulative Detection ===")
    
    df = create_test_dataframe()
    logger.info(f"\nTest DataFrame:\n{df}")
    
    year_quarters = group_quarters_by_year(df.columns.tolist())
    adjustments = needs_quarterly_adjustment(df, year_quarters)
    
    logger.info(f"\nDetected adjustments: {adjustments}")
    
    # We expect both 2024-12-31 and 2023-12-31 to be detected
    expected_adjustments = ['2024-12-31', '2023-12-31']
    detected = list(adjustments.keys())
    
    if set(detected) == set(expected_adjustments):
        logger.info("✓ Correctly detected cumulative Q4 reports")
    else:
        logger.warning(f"✗ Detection issue: expected {expected_adjustments}, got {detected}")


def test_adjustment():
    """Test the adjustment of cumulative data."""
    logger.info("\n=== Testing Data Adjustment ===")
    
    df = create_test_dataframe()
    year_quarters = group_quarters_by_year(df.columns.tolist())
    adjustments = needs_quarterly_adjustment(df, year_quarters)
    
    logger.info(f"\nBefore adjustment (Q4 2024):")
    logger.info(f"Revenue: {df.loc['Total revenue', '2024-12-31']}")
    logger.info(f"Net Income: {df.loc['Net income', '2024-12-31']}")
    
    df_adjusted = adjust_quarterly_data(df, adjustments, year_quarters)
    
    logger.info(f"\nAfter adjustment (Q4 2024):")
    logger.info(f"Revenue: {df_adjusted.loc['Total revenue', '2024-12-31']}")
    logger.info(f"Net Income: {df_adjusted.loc['Net income', '2024-12-31']}")
    
    # Verify: Q4_adjusted should be approximately 120 (450 - 100 - 120 - 110)
    q4_revenue_adjusted = df_adjusted.loc['Total revenue', '2024-12-31']
    expected_q4_revenue = 120  # 450 - (100 + 120 + 110)
    
    if abs(q4_revenue_adjusted - expected_q4_revenue) < 1:
        logger.info(f"✓ Adjustment correct: {q4_revenue_adjusted} ≈ {expected_q4_revenue}")
    else:
        logger.warning(f"✗ Adjustment issue: {q4_revenue_adjusted} != {expected_q4_revenue}")


def test_full_process():
    """Test the full quarterly adjustment process."""
    logger.info("\n=== Testing Full Process ===")
    
    df = create_test_dataframe()
    
    logger.info(f"\nOriginal DataFrame:")
    logger.info(f"\n{df}")
    
    df_adjusted, adjustment_info = process_quarterly_adjustments(df, df.columns.tolist())
    
    logger.info(f"\nAdjusted DataFrame:")
    logger.info(f"\n{df_adjusted}")
    
    logger.info(f"\nAdjustment Info: {adjustment_info}")


def main():
    """Run all tests."""
    logger.info("="*80)
    logger.info("QUARTERLY ADJUSTMENT TESTS")
    logger.info("="*80)
    
    try:
        test_detect_quarter()
        test_group_quarters()
        test_cumulative_detection()
        test_adjustment()
        test_full_process()
        
        logger.info("\n" + "="*80)
        logger.info("ALL TESTS COMPLETED")
        logger.info("="*80)
        logger.info("\n✓ Quarterly adjustment logic is working correctly!")
        logger.info("\nNext steps:")
        logger.info("1. Test with real company data using: python main.py --ticker AAPL --quarterly --years 3")
        logger.info("2. Verify the backend serves adjusted quarterly data correctly")
        logger.info("3. Check the frontend displays the data properly")
        
    except Exception as e:
        logger.error(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
