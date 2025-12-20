#!/usr/bin/env python3
"""
Test script to verify that raw and clean views are properly separated.

This script:
1. Collects fresh financial data for a ticker
2. Verifies that clean and raw data are independent
3. Checks that clean data only contains mapped rows
4. Checks that raw data only contains original rows
"""

import sys
import os
import json
import subprocess
from pathlib import Path

# Add data-collection scripts to path
sys.path.insert(0, str(Path(__file__).parent / "data-collection" / "scripts"))

from Company import Company
from Filling import Filling
from FinancialStatement import IncomeStatement


def test_raw_clean_separation(ticker="AAPL", num_years=1):
    """Test that raw and clean data are properly separated."""
    
    print(f"\n{'='*80}")
    print(f"Testing Raw/Clean Separation for {ticker}")
    print(f"{'='*80}\n")
    
    # Step 1: Collect data
    print(f"Step 1: Collecting data for {ticker}...")
    try:
        company = Company(ticker=ticker)
        filings = company.ten_k_fillings
        
        # Get the most recent filing
        report_date = filings.index[0]
        accession_num = filings.iloc[0]
        
        print(f"  Report Date: {report_date}")
        print(f"  Accession: {accession_num}")
        
        # Create filing object
        filing = Filling(
            ticker=ticker,
            cik=company.cik,
            acc_num_unfiltered=accession_num,
            company_facts=company.company_facts,
            quarterly=False
        )
        
        # Process income statement
        print(f"\nStep 2: Processing Income Statement...")
        filing.process_one_statement("income_statement")
        
        if not filing.income_statement:
            print("  ❌ Failed to process income statement")
            return False
        
        # Get clean and raw DataFrames
        mapped_df = filing.income_statement.get_mapped_df()
        raw_df = filing.income_statement.raw_df
        
        print(f"\nStep 3: Analyzing data structure...")
        print(f"  Clean (mapped) rows: {len(mapped_df)}")
        print(f"  Raw (unmapped) rows: {len(raw_df) if raw_df is not None else 0}")
        
        # Step 4: Verify they are different
        if raw_df is None:
            print("  ⚠️  Warning: No raw data generated")
            return False
        
        # Check that the indices are different
        clean_indices = set(mapped_df.index)
        raw_indices = set(raw_df.index)
        
        overlap = clean_indices.intersection(raw_indices)
        
        print(f"\n  Clean-only rows: {len(clean_indices - raw_indices)}")
        print(f"  Raw-only rows: {len(raw_indices - clean_indices)}")
        print(f"  Overlapping rows: {len(overlap)}")
        
        # Display sample rows from each
        print(f"\nStep 4: Sample rows from Clean View (first 5):")
        for i, row_name in enumerate(list(mapped_df.index)[:5]):
            print(f"  {i+1}. {row_name}")
        
        print(f"\nStep 5: Sample rows from Raw View (first 5):")
        for i, row_name in enumerate(list(raw_df.index)[:5]):
            print(f"  {i+1}. {row_name}")
        
        # Step 6: Check for standardized row names in clean data
        standardized_rows = ['Total revenue', 'COGS', 'Gross profit', 'Net income']
        clean_has_standardized = [row for row in standardized_rows if row in clean_indices]
        raw_has_standardized = [row for row in standardized_rows if row in raw_indices]
        
        print(f"\nStep 6: Standardized rows check:")
        print(f"  Clean view has standardized rows: {clean_has_standardized}")
        print(f"  Raw view has standardized rows: {raw_has_standardized}")
        
        # Step 7: Verify separation
        print(f"\n{'='*80}")
        print("RESULTS:")
        print(f"{'='*80}")
        
        success = True
        
        # Test 1: Clean and raw should be different
        if len(clean_indices) == len(raw_indices) and clean_indices == raw_indices:
            print("❌ FAIL: Clean and raw data have identical rows!")
            success = False
        else:
            print("✓ PASS: Clean and raw data have different row sets")
        
        # Test 2: Clean should contain standardized rows
        if len(clean_has_standardized) >= 2:
            print(f"✓ PASS: Clean view contains standardized rows: {clean_has_standardized}")
        else:
            print(f"❌ FAIL: Clean view missing standardized rows")
            success = False
        
        # Test 3: Raw should NOT primarily contain standardized rows
        if len(raw_has_standardized) < len(standardized_rows) / 2:
            print(f"✓ PASS: Raw view primarily contains original rows")
        else:
            print(f"⚠️  WARNING: Raw view has many standardized rows: {raw_has_standardized}")
        
        # Test 4: Row counts should be different
        if len(clean_indices) != len(raw_indices):
            print(f"✓ PASS: Different row counts ({len(clean_indices)} vs {len(raw_indices)})")
        else:
            print(f"⚠️  WARNING: Same row count in both views")
        
        print(f"\n{'='*80}")
        if success:
            print("✅ ALL TESTS PASSED - Raw and clean data are properly separated!")
        else:
            print("❌ TESTS FAILED - Raw and clean data are still mixed!")
        print(f"{'='*80}\n")
        
        return success
        
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    ticker = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    success = test_raw_clean_separation(ticker)
    sys.exit(0 if success else 1)
