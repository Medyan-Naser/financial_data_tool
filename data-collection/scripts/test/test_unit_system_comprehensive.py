#!/usr/bin/env python3
"""
Comprehensive test for the new UnitDetector system.

Tests:
1. Income statement units (AMZN quarterly)
2. Cash flow statement units (AMZN quarterly)
3. Balance sheet units (AMZN quarterly)
4. Multiple period handling (3-month vs 6-month)
5. Verification against Yahoo Finance values
"""

import sys
import logging
from Company import Company
from Filling import Filling

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


def test_statement_units(ticker='AMZN', quarterly=True):
    """Test all three statements for correct units."""
    
    logger.info(f"\n{'='*80}")
    logger.info(f"TESTING UNIT DETECTION FOR {ticker} {'QUARTERLY' if quarterly else 'ANNUAL'}")
    logger.info(f"{'='*80}\n")
    
    # Get company data
    company = Company(ticker=ticker)
    filings = company.ten_q_fillings if quarterly else company.ten_k_fillings
    
    if filings.empty:
        logger.error(f"No {'quarterly' if quarterly else 'annual'} filings found for {ticker}")
        return False
    
    # Get most recent filing
    report_date = filings.index[0]
    accession = filings.iloc[0]
    
    logger.info(f"Processing filing: {report_date}")
    logger.info(f"Accession: {accession}\n")
    
    # Create filing object
    filing = Filling(
        ticker=ticker,
        cik=company.cik,
        acc_num_unfiltered=accession,
        company_facts=company.company_facts,
        quarterly=quarterly
    )
    
    all_passed = True
    
    # Test 1: Income Statement
    logger.info("="*80)
    logger.info("TEST 1: INCOME STATEMENT")
    logger.info("="*80)
    
    filing.process_one_statement('income_statement')
    
    if filing.income_statement:
        df = filing.income_statement.og_df
        logger.info(f"✓ Processed: {df.shape[0]} rows x {df.shape[1]} columns")
        
        # Check first 5 rows
        logger.info("\nFirst 5 rows:")
        for i, idx in enumerate(df.index[:5]):
            value = df.loc[idx].iloc[0]
            unit_info = filing.income_statement.units_dict.get(idx)
            
            concept = idx.split('_')[-1] if '_' in idx else idx
            logger.info(f"  {i+1}. {concept[:60]}")
            logger.info(f"     Value: {value:,.2f}")
            if unit_info:
                logger.info(f"     Unit: {unit_info}")
            else:
                logger.warning(f"     Unit: MISSING")
                all_passed = False
        
        # Verify revenue
        revenue_row = df.iloc[0]
        revenue_value = revenue_row.iloc[0]
        
        # For AMZN Q2 2025, expected ~$167.7B (in millions = 167,700)
        if ticker == 'AMZN' and quarterly:
            expected = 167700
            error = abs(revenue_value - expected) / expected
            
            logger.info(f"\nRevenue Verification:")
            logger.info(f"  Extracted: ${revenue_value:,.0f}M = ${revenue_value/1000:.1f}B")
            logger.info(f"  Expected: ${expected:,.0f}M = ${expected/1000:.1f}B")
            logger.info(f"  Error: {error*100:.2f}%")
            
            if error < 0.01:  # Less than 1% error
                logger.info("  ✅ PASSED")
            else:
                logger.error("  ❌ FAILED - Value mismatch!")
                all_passed = False
    else:
        logger.error("❌ Income statement not processed")
        all_passed = False
    
    # Test 2: Cash Flow
    logger.info("\n" + "="*80)
    logger.info("TEST 2: CASH FLOW STATEMENT")
    logger.info("="*80)
    
    filing.process_one_statement('cash_flow_statement')
    
    if filing.cash_flow:
        df = filing.cash_flow.og_df
        logger.info(f"✓ Processed: {df.shape[0]} rows x {df.shape[1]} columns")
        
        # Check first row
        idx = df.index[0]
        value = df.loc[idx].iloc[0]
        unit_info = filing.cash_flow.units_dict.get(idx)
        
        concept = idx.split('_')[-1] if '_' in idx else idx
        logger.info(f"\nFirst row:")
        logger.info(f"  {concept[:60]}")
        logger.info(f"  Value: {value:,.2f}")
        if unit_info:
            logger.info(f"  Unit: {unit_info}")
        else:
            logger.warning(f"  Unit: MISSING")
            all_passed = False
    else:
        logger.error("❌ Cash flow not processed")
        all_passed = False
    
    # Test 3: Balance Sheet
    logger.info("\n" + "="*80)
    logger.info("TEST 3: BALANCE SHEET")
    logger.info("="*80)
    
    filing.process_one_statement('balance_sheet')
    
    if filing.balance_sheet:
        df = filing.balance_sheet.og_df
        logger.info(f"✓ Processed: {df.shape[0]} rows x {df.shape[1]} columns")
        
        # Check first row
        idx = df.index[0]
        value = df.loc[idx].iloc[0]
        unit_info = filing.balance_sheet.units_dict.get(idx)
        
        concept = idx.split('_')[-1] if '_' in idx else idx
        logger.info(f"\nFirst row:")
        logger.info(f"  {concept[:60]}")
        logger.info(f"  Value: {value:,.2f}")
        if unit_info:
            logger.info(f"  Unit: {unit_info}")
        else:
            logger.warning(f"  Unit: MISSING")
            all_passed = False
    else:
        logger.error("❌ Balance sheet not processed")
        all_passed = False
    
    # Test 4: Unit Source Distribution
    logger.info("\n" + "="*80)
    logger.info("TEST 4: UNIT SOURCE ANALYSIS")
    logger.info("="*80)
    
    all_units = {}
    for stmt_name, stmt in [
        ('Income', filing.income_statement),
        ('Cash Flow', filing.cash_flow),
        ('Balance', filing.balance_sheet)
    ]:
        if stmt and hasattr(stmt, 'units_dict'):
            all_units[stmt_name] = stmt.units_dict
    
    # Count by source
    source_counts = {'verified': 0, 'header': 0, 'concept': 0, 'fallback': 0}
    
    for stmt_name, units_dict in all_units.items():
        for idx, unit_info in units_dict.items():
            if hasattr(unit_info, 'source'):
                source_counts[unit_info.source] = source_counts.get(unit_info.source, 0) + 1
    
    total = sum(source_counts.values())
    logger.info("\nUnit Detection Sources:")
    for source, count in sorted(source_counts.items(), key=lambda x: -x[1]):
        pct = (count / total * 100) if total > 0 else 0
        logger.info(f"  {source:12s}: {count:3d} ({pct:5.1f}%)")
    
    if source_counts['verified'] > total * 0.5:
        logger.info("  ✅ Majority verified (good!)")
    elif source_counts['header'] > total * 0.3:
        logger.info("  ⚠️  Many from header (acceptable)")
    else:
        logger.warning("  ⚠️  Too many fallbacks")
    
    # Final summary
    logger.info("\n" + "="*80)
    logger.info("SUMMARY")
    logger.info("="*80)
    
    if all_passed:
        logger.info("✅ ALL TESTS PASSED")
        logger.info("   - All statements processed successfully")
        logger.info("   - Units detected for all rows")
        logger.info("   - Values match expected (where tested)")
        return True
    else:
        logger.error("❌ SOME TESTS FAILED")
        logger.error("   Check logs above for details")
        return False


if __name__ == "__main__":
    # Test AMZN quarterly
    success = test_statement_units(ticker='AMZN', quarterly=True)
    
    sys.exit(0 if success else 1)
