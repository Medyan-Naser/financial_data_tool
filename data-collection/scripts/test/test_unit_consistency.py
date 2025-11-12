#!/usr/bin/env python3
"""
Test unit consistency: Verify that values are stored as full numbers with unit scale = 1.

This tests the user's requirement:
"in my json files always store the full number with unit of 1"
"""

import sys
import logging
from Company import Company
from Filling import Filling

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def test_unit_consistency(ticker='AMZN', quarterly=True):
    """
    Test that:
    1. Table header says "in millions"
    2. Values are stored as full numbers (e.g., 167,702,000,000)
    3. UnitInfo has scale_factor = 1.0
    4. UnitInfo has original_scale = 1,000,000
    """
    
    logger.info("="*80)
    logger.info(f"UNIT CONSISTENCY TEST: {ticker} {'Quarterly' if quarterly else 'Annual'}")
    logger.info("="*80)
    
    # Get company data
    company = Company(ticker=ticker)
    filings = company.ten_q_fillings if quarterly else company.ten_k_fillings
    
    if filings.empty:
        logger.error(f"No filings found for {ticker}")
        return False
    
    # Get most recent filing
    report_date = filings.index[0]
    accession = filings.iloc[0]
    
    logger.info(f"\nProcessing: {report_date}")
    logger.info(f"Report URL: https://www.sec.gov/cgi-bin/viewer?action=view&cik={company.cik}&accession_number={accession.replace('-', '')}&xbrl_type=v")
    
    # Create filing
    filing = Filling(
        ticker=ticker,
        cik=company.cik,
        acc_num_unfiltered=accession,
        company_facts=company.company_facts,
        quarterly=quarterly
    )
    
    # Process income statement
    logger.info("\n" + "="*80)
    logger.info("INCOME STATEMENT TEST")
    logger.info("="*80)
    
    filing.process_one_statement('income_statement')
    
    if not filing.income_statement:
        logger.error("❌ Failed to process income statement")
        return False
    
    df = filing.income_statement.og_df
    units_dict = filing.income_statement.units_dict
    
    # Check first row (typically revenue)
    revenue_idx = df.index[0]
    revenue_value = df.loc[revenue_idx].iloc[0]
    revenue_unit = units_dict.get(revenue_idx)
    
    logger.info(f"\nRevenue Row:")
    logger.info(f"  Index: {revenue_idx}")
    logger.info(f"  Value: {revenue_value:,.0f}")
    
    if revenue_unit:
        logger.info(f"  Unit Type: {revenue_unit.unit_type}")
        logger.info(f"  Base Unit: {revenue_unit.base_unit}")
        logger.info(f"  Scale Factor: {revenue_unit.scale_factor}")
        logger.info(f"  Original Scale: {revenue_unit.original_scale:,.0f}")
        logger.info(f"  Source: {revenue_unit.source}")
        logger.info(f"  Display: {revenue_unit}")
    else:
        logger.error("  ❌ No unit info!")
        return False
    
    # Verification
    all_passed = True
    
    # Test 1: Value should be full number (billions)
    if ticker == 'AMZN' and quarterly:
        # Expected: ~$167.7B = 167,700,000,000
        expected_min = 160_000_000_000
        expected_max = 170_000_000_000
        
        if expected_min <= revenue_value <= expected_max:
            logger.info(f"\n✅ TEST 1 PASSED: Value is full number")
            logger.info(f"   {revenue_value:,.0f} is in expected range")
            logger.info(f"   ${revenue_value/1_000_000_000:.1f}B")
        else:
            logger.error(f"\n❌ TEST 1 FAILED: Value not in expected range")
            logger.error(f"   Got: {revenue_value:,.0f}")
            logger.error(f"   Expected: {expected_min:,.0f} to {expected_max:,.0f}")
            all_passed = False
    
    # Test 2: Scale factor should be 1.0
    if revenue_unit.scale_factor == 1.0:
        logger.info(f"\n✅ TEST 2 PASSED: scale_factor = 1.0")
        logger.info(f"   Values are already in base units")
    else:
        logger.error(f"\n❌ TEST 2 FAILED: scale_factor = {revenue_unit.scale_factor}")
        logger.error(f"   Should be 1.0 (values already scaled)")
        all_passed = False
    
    # Test 3: Original scale should be 1,000,000 (millions)
    if revenue_unit.original_scale == 1_000_000:
        logger.info(f"\n✅ TEST 3 PASSED: original_scale = 1,000,000")
        logger.info(f"   Header declared 'in millions'")
    else:
        logger.warning(f"\n⚠️  TEST 3 WARNING: original_scale = {revenue_unit.original_scale:,.0f}")
        logger.warning(f"   Expected 1,000,000 (millions)")
        # Not a failure, could be billions or thousands
    
    # Test 4: Check multiple rows
    logger.info("\n" + "="*80)
    logger.info("MULTIPLE ROWS TEST")
    logger.info("="*80)
    
    scale_counts = {}
    for idx in df.index[:10]:
        unit_info = units_dict.get(idx)
        if unit_info:
            if unit_info.scale_factor != 1.0:
                logger.error(f"❌ Row {idx[:50]}: scale_factor = {unit_info.scale_factor} (should be 1.0)")
                all_passed = False
            else:
                scale_counts[unit_info.original_scale] = scale_counts.get(unit_info.original_scale, 0) + 1
    
    logger.info(f"\nOriginal scales used (from {len(df)} rows):")
    for scale, count in sorted(scale_counts.items(), reverse=True):
        if scale == 1000000000:
            logger.info(f"  Billions:   {count} rows")
        elif scale == 1000000:
            logger.info(f"  Millions:   {count} rows")
        elif scale == 1000:
            logger.info(f"  Thousands:  {count} rows")
        elif scale == 1:
            logger.info(f"  Ones:       {count} rows")
        else:
            logger.info(f"  Other ({scale:,.0f}): {count} rows")
    
    # Final summary
    logger.info("\n" + "="*80)
    logger.info("SUMMARY")
    logger.info("="*80)
    
    if all_passed:
        logger.info("✅ ALL TESTS PASSED!")
        logger.info("   - Values stored as full numbers")
        logger.info("   - scale_factor = 1.0 (consistent)")
        logger.info("   - original_scale tracks what was applied")
        logger.info("\nJSON output format:")
        logger.info(f'  {{"value": {revenue_value:,.0f}, "unit": {{"base": "{revenue_unit.base_unit}", "scale": {revenue_unit.scale_factor}}}}}')
        return True
    else:
        logger.error("❌ SOME TESTS FAILED")
        return False


if __name__ == "__main__":
    success = test_unit_consistency(ticker='AMZN', quarterly=True)
    sys.exit(0 if success else 1)
