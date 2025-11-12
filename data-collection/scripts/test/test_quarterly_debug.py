#!/usr/bin/env python3
"""
Debug script to test quarterly data collection and identify where it gets stuck.
"""

import sys
import logging
import time
from datetime import datetime

# Setup verbose logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(name)s] %(message)s'
)
logger = logging.getLogger(__name__)

def test_quarterly_collection():
    """Test quarterly data collection with detailed logging."""
    
    from Company import Company
    from Filling import Filling
    
    ticker = 'AAPL'
    years = 2  # Test with 2 years = 8 quarterly filings
    
    print("="*80)
    print(f"TESTING QUARTERLY DATA COLLECTION FOR {ticker}")
    print(f"Years: {years} (expected ~{years * 4} filings)")
    print("="*80)
    
    start_time = time.time()
    
    try:
        # Initialize company
        print(f"\n[1] Initializing company {ticker}...")
        company = Company(ticker=ticker)
        print(f"    ✓ Company CIK: {company.cik}")
        print(f"    ✓ Total 10-Q filings available: {len(company.ten_q_fillings)}")
        
        # Get quarterly filings
        filings = company.ten_q_fillings
        num_filings = years * 4
        filings = filings.iloc[:num_filings]
        
        print(f"\n[2] Processing {len(filings)} quarterly filings...")
        print("-"*80)
        
        # Process each filing
        for idx, (report_date, accession_num) in enumerate(filings.items()):
            filing_start = time.time()
            
            print(f"\n[Filing {idx + 1}/{len(filings)}] Date: {report_date}")
            print(f"  Accession: {accession_num}")
            
            try:
                # Create filing object
                print(f"  Creating Filling object...")
                filing = Filling(
                    ticker=ticker,
                    cik=company.cik,
                    acc_num_unfiltered=accession_num,
                    company_facts=company.company_facts,
                    quarterly=True
                )
                print(f"  ✓ Filling created in {time.time() - filing_start:.1f}s")
                
                # Process income statement
                stmt_start = time.time()
                print(f"  Processing Income Statement...")
                sys.stdout.flush()  # Force output
                
                filing.process_one_statement("income_statement")
                
                if filing.income_statement:
                    df = filing.income_statement.og_df
                    print(f"  ✓ Income Statement: {len(df)} rows, {len(df.columns)} columns ({time.time() - stmt_start:.1f}s)")
                else:
                    print(f"  ✗ No Income Statement data")
                
                # Process balance sheet
                stmt_start = time.time()
                print(f"  Processing Balance Sheet...")
                sys.stdout.flush()
                
                filing.process_one_statement("balance_sheet")
                
                if filing.balance_sheet:
                    df = filing.balance_sheet.og_df
                    print(f"  ✓ Balance Sheet: {len(df)} rows, {len(df.columns)} columns ({time.time() - stmt_start:.1f}s)")
                else:
                    print(f"  ✗ No Balance Sheet data")
                
                # Process cash flow
                stmt_start = time.time()
                print(f"  Processing Cash Flow...")
                sys.stdout.flush()
                
                filing.process_one_statement("cash_flow_statement")
                
                if filing.cash_flow:
                    df = filing.cash_flow.og_df
                    print(f"  ✓ Cash Flow: {len(df)} rows, {len(df.columns)} columns ({time.time() - stmt_start:.1f}s)")
                else:
                    print(f"  ✗ No Cash Flow data")
                
                filing_time = time.time() - filing_start
                print(f"  ✓ Filing completed in {filing_time:.1f}s")
                
                # Check for timeout
                if filing_time > 30:
                    print(f"  ⚠️  WARNING: Filing took more than 30 seconds!")
                
            except KeyboardInterrupt:
                print(f"\n  ✗ INTERRUPTED by user")
                raise
            except Exception as e:
                print(f"  ✗ ERROR: {e}")
                import traceback
                traceback.print_exc()
                print(f"  Continuing to next filing...")
                continue
        
        total_time = time.time() - start_time
        print("\n" + "="*80)
        print(f"✓ TEST COMPLETED SUCCESSFULLY")
        print(f"  Total time: {total_time:.1f}s")
        print(f"  Avg per filing: {total_time/len(filings):.1f}s")
        print("="*80)
        
        return True
        
    except KeyboardInterrupt:
        print("\n" + "="*80)
        print("✗ TEST INTERRUPTED BY USER")
        elapsed = time.time() - start_time
        print(f"  Elapsed time: {elapsed:.1f}s")
        print("="*80)
        return False
    except Exception as e:
        print("\n" + "="*80)
        print(f"✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        print("="*80)
        return False


if __name__ == "__main__":
    print("Starting quarterly collection debug test...")
    print("If this hangs, press Ctrl+C to interrupt and see where it got stuck.\n")
    
    success = test_quarterly_collection()
    sys.exit(0 if success else 1)
