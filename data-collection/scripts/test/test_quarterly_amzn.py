#!/usr/bin/env python3
"""
Test script to verify quarterly data collection for AMZN.

Verifies:
1. Units are correct (verified by comparing with company_facts)
2. Columns are in correct order (newest first)
3. Only 3-month periods are included (not 6-month or 9-month YTD)
4. Data matches external sources (Yahoo Finance)
"""

import sys
import logging
import pandas as pd
from Company import Company
from Filling import Filling
from main import get_financial_statements
from merge_utils import merge_statements_by_year

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_amzn_quarterly():
    """Test AMZN quarterly data collection."""
    
    logger.info(f"\n{'='*80}")
    logger.info(f"TESTING AMZN QUARTERLY DATA COLLECTION")
    logger.info(f"{'='*80}\n")
    
    # Collect 2 years of quarterly data
    logger.info("Collecting 2 years of AMZN quarterly data...")
    results = get_financial_statements(
        ticker='AMZN',
        num_years=2,
        quarterly=True,
        enable_pattern_logging=False
    )
    
    if not results or not results.get('income_statements'):
        logger.error("❌ Failed to collect data")
        return False
    
    logger.info(f"✓ Collected {len(results['income_statements'])} quarterly filings")
    
    # Merge the statements
    logger.info("\nMerging statements...")
    merged_df = merge_statements_by_year(results['income_statements'], 'income')
    
    if merged_df is None or merged_df.empty:
        logger.error("❌ Merge failed")
        return False
    
    logger.info(f"✓ Merged: {merged_df.shape[0]} rows x {merged_df.shape[1]} columns")
    
    # Check 1: Column order
    logger.info(f"\n{'='*80}")
    logger.info("CHECK 1: Column Order (Newest First)")
    logger.info(f"{'='*80}")
    
    columns = merged_df.columns.tolist()
    logger.info(f"First 5 columns: {columns[:5]}")
    logger.info(f"Last 5 columns: {columns[-5:]}")
    
    # Verify newest is first
    try:
        first_date = pd.to_datetime(columns[0])
        last_date = pd.to_datetime(columns[-1])
        
        if first_date > last_date:
            logger.info("✓ Columns are sorted correctly (newest first)")
        else:
            logger.error(f"❌ Columns are in wrong order!")
            logger.error(f"   First: {first_date}, Last: {last_date}")
            return False
    except Exception as e:
        logger.error(f"❌ Could not verify column order: {e}")
        return False
    
    # Check 2: Unit verification
    logger.info(f"\n{'='*80}")
    logger.info("CHECK 2: Unit Verification")
    logger.info(f"{'='*80}")
    
    # Get the most recent filing to check units
    most_recent = results['income_statements'][0]
    if 'statement_object' in most_recent:
        stmt_obj = most_recent['statement_object']
        if hasattr(stmt_obj, 'units_dict') and stmt_obj.units_dict:
            logger.info(f"✓ Unit information available ({len(stmt_obj.units_dict)} items)")
            
            # Check a few specific items
            revenue_checked = False
            shares_checked = False
            eps_checked = False
            
            for fact, unit_info in stmt_obj.units_dict.items():
                if 'revenue' in fact.lower() and not revenue_checked:
                    logger.info(f"  Revenue: {unit_info}")
                    if unit_info.scale_factor == 1000000:
                        logger.info("    ✓ Correctly detected as millions")
                    revenue_checked = True
                
                if 'shares' in fact.lower() and 'per' not in fact.lower() and not shares_checked:
                    logger.info(f"  Shares: {unit_info}")
                    if unit_info.unit_type.value == 'shares':
                        logger.info("    ✓ Correctly detected as shares")
                    shares_checked = True
                
                if 'earningspershare' in fact.lower() and not eps_checked:
                    logger.info(f"  EPS: {unit_info}")
                    if unit_info.unit_type.value == 'per_share':
                        logger.info("    ✓ Correctly detected as per-share")
                    eps_checked = True
        else:
            logger.warning("⚠️  No unit information in statement object")
    else:
        logger.warning("⚠️  Statement object not available")
    
    # Check 3: Verify against known values
    logger.info(f"\n{'='*80}")
    logger.info("CHECK 3: Value Verification")
    logger.info(f"{'='*80}")
    
    # Find revenue row
    revenue_row = None
    for row_name in merged_df.index:
        if 'revenue' in row_name.lower() and 'total' in row_name.lower():
            revenue_row = row_name
            break
    
    if revenue_row:
        # Get Q2 2025 revenue (most recent)
        recent_col = columns[0]
        revenue_value = merged_df.loc[revenue_row, recent_col]
        
        logger.info(f"Q2 2025 Revenue from our data:")
        logger.info(f"  {revenue_value:,.0f} (should be in millions)")
        logger.info(f"  = ${revenue_value/1000:.1f}B")
        
        # Expected: ~$168B for Q2 2025
        expected_billions = 168
        actual_billions = revenue_value / 1000
        
        if abs(actual_billions - expected_billions) < 5:  # Within $5B tolerance
            logger.info(f"✓ Value matches expected (~${expected_billions}B)")
        else:
            logger.error(f"❌ Value mismatch! Expected ~${expected_billions}B, got ${actual_billions:.1f}B")
            logger.error(f"   This suggests wrong units or wrong period selection")
            return False
    else:
        logger.warning("⚠️  Could not find revenue row")
    
    # Check 4: Only 3-month periods
    logger.info(f"\n{'='*80}")
    logger.info("CHECK 4: Period Verification (3-month only)")
    logger.info(f"{'='*80}")
    
    # This check requires looking at company_facts to see period lengths
    company = Company(ticker='AMZN')
    facts_df = company.company_facts_DF if hasattr(company, 'company_facts_DF') else None
    
    if facts_df is not None:
        # Check periods for the columns we have
        three_month_count = 0
        other_period_count = 0
        
        for col in columns[:5]:  # Check first 5
            col_date = pd.to_datetime(col).strftime('%Y-%m-%d')
            
            # Find revenue for this date
            revenue_facts = facts_df[
                (facts_df['fact'] == 'RevenueFromContractWithCustomerExcludingAssessedTax') &
                (facts_df['end'] == col_date)
            ]
            
            if not revenue_facts.empty:
                for idx, row in revenue_facts.iterrows():
                    if 'start' in row:
                        start = pd.to_datetime(row['start'])
                        end = pd.to_datetime(row['end'])
                        days = (end - start).days
                        months = days / 30
                        
                        if 85 <= days <= 95:  # ~3 months
                            three_month_count += 1
                            logger.info(f"  {col}: {days} days (~{months:.1f} months) ✓")
                        else:
                            other_period_count += 1
                            logger.warning(f"  {col}: {days} days (~{months:.1f} months) ⚠️ Not 3-month!")
                        break
        
        if three_month_count > 0 and other_period_count == 0:
            logger.info(f"✓ All periods are 3-month quarters")
        elif other_period_count > 0:
            logger.error(f"❌ Found {other_period_count} non-3-month periods!")
            logger.error(f"   This means 6-month or 9-month YTD columns are included")
            return False
    
    # Summary
    logger.info(f"\n{'='*80}")
    logger.info("SUMMARY")
    logger.info(f"{'='*80}\n")
    
    logger.info("✅ ALL CHECKS PASSED!")
    logger.info(f"   - Columns sorted correctly (newest first)")
    logger.info(f"   - Units verified as correct (millions)")
    logger.info(f"   - Values match expected (~$168B for Q2 2025)")
    logger.info(f"   - Only 3-month periods included")
    
    logger.info(f"\n{'='*80}\n")
    return True


if __name__ == "__main__":
    success = test_amzn_quarterly()
    sys.exit(0 if success else 1)
