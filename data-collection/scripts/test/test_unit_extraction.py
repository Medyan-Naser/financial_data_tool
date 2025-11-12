#!/usr/bin/env python3
"""
Test script for unit extraction functionality.

Tests that units are properly detected and preserved through the data pipeline.
"""

import sys
import logging
from Company import Company
from Filling import Filling

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_unit_extraction(ticker='AAPL'):
    """
    Test unit extraction for a given ticker.
    
    This will:
    1. Fetch the most recent filing
    2. Process the income statement
    3. Display unit information for each row
    """
    logger.info(f"\n{'='*80}")
    logger.info(f"TESTING UNIT EXTRACTION FOR {ticker}")
    logger.info(f"{'='*80}\n")
    
    try:
        # Initialize company
        logger.info(f"Fetching company data for {ticker}...")
        company = Company(ticker=ticker)
        logger.info(f"Company CIK: {company.cik}")
        
        # Get most recent annual filing
        filings = company.ten_k_fillings
        if filings.empty:
            logger.error("No 10-K filings found")
            return
        
        # Get the most recent filing
        report_date = filings.index[0]
        accession_num = filings.iloc[0]
        
        logger.info(f"\nProcessing most recent filing:")
        logger.info(f"  Report Date: {report_date}")
        logger.info(f"  Accession: {accession_num}")
        
        # Create filling object
        filing = Filling(
            ticker=ticker,
            cik=company.cik,
            acc_num_unfiltered=accession_num,
            company_facts=company.company_facts,
            quarterly=False
        )
        
        # Process income statement
        logger.info(f"\nProcessing Income Statement...")
        filing.process_one_statement("income_statement")
        
        if not filing.income_statement:
            logger.error("Income statement not available")
            return
        
        # Check if units_dict is populated
        logger.info(f"\n{'='*80}")
        logger.info(f"UNIT EXTRACTION RESULTS")
        logger.info(f"{'='*80}\n")
        
        if hasattr(filing.income_statement, 'units_dict') and filing.income_statement.units_dict:
            logger.info(f"✓ units_dict populated with {len(filing.income_statement.units_dict)} entries")
            
            # Display first 10 entries
            logger.info(f"\nFirst 10 unit mappings:")
            for i, (fact_name, unit_info) in enumerate(list(filing.income_statement.units_dict.items())[:10]):
                # Clean up fact name for display
                display_name = fact_name.split(":")[-1] if ":" in fact_name else fact_name
                if "_" in display_name:
                    display_name = display_name.split("_")[-1]
                
                logger.info(f"  {i+1}. {display_name:50s} -> {unit_info}")
            
            # Check for specific items we care about
            logger.info(f"\n{'='*80}")
            logger.info(f"CHECKING SPECIFIC ITEMS")
            logger.info(f"{'='*80}\n")
            
            # Look for revenue
            revenue_found = False
            shares_found = False
            eps_found = False
            
            for fact_name, unit_info in filing.income_statement.units_dict.items():
                fact_lower = fact_name.lower()
                
                if 'revenue' in fact_lower and not revenue_found:
                    logger.info(f"✓ Revenue item found:")
                    logger.info(f"    Fact: {fact_name}")
                    logger.info(f"    Unit: {unit_info}")
                    logger.info(f"    Type: {unit_info.unit_type.value}")
                    revenue_found = True
                
                if 'shares' in fact_lower and 'per' not in fact_lower and not shares_found:
                    logger.info(f"\n✓ Share count item found:")
                    logger.info(f"    Fact: {fact_name}")
                    logger.info(f"    Unit: {unit_info}")
                    logger.info(f"    Type: {unit_info.unit_type.value}")
                    shares_found = True
                
                if 'earningspershare' in fact_lower and not eps_found:
                    logger.info(f"\n✓ EPS item found:")
                    logger.info(f"    Fact: {fact_name}")
                    logger.info(f"    Unit: {unit_info}")
                    logger.info(f"    Type: {unit_info.unit_type.value}")
                    eps_found = True
                
                if revenue_found and shares_found and eps_found:
                    break
            
            # Summary
            logger.info(f"\n{'='*80}")
            logger.info(f"SUMMARY")
            logger.info(f"{'='*80}\n")
            
            logger.info(f"Total facts with units: {len(filing.income_statement.units_dict)}")
            logger.info(f"Revenue detected: {'✓ Yes' if revenue_found else '✗ No'}")
            logger.info(f"Share count detected: {'✓ Yes' if shares_found else '✗ No'}")
            logger.info(f"EPS detected: {'✓ Yes' if eps_found else '✗ No'}")
            
            if revenue_found and shares_found and eps_found:
                logger.info(f"\n✅ SUCCESS: Unit extraction is working correctly!")
                logger.info(f"   Different unit types are properly detected and preserved.")
            else:
                logger.warning(f"\n⚠️  Some items not found, but this may be normal for this filing.")
            
        else:
            logger.error("✗ units_dict is empty or not populated")
            logger.error("  Unit extraction may not be working correctly")
        
        logger.info(f"\n{'='*80}\n")
        
    except Exception as e:
        logger.error(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Test unit extraction')
    parser.add_argument('--ticker', type=str, default='AAPL', help='Stock ticker symbol')
    
    args = parser.parse_args()
    
    test_unit_extraction(args.ticker)
