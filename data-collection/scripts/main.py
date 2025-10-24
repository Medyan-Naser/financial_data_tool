#!/usr/bin/env python3
"""
Financial Data Collection Tool

This script fetches and structures financial statements from SEC EDGAR database.
It handles the complexity of different company formats and row labels.

Usage:
    python main.py --ticker AAPL
    python main.py --ticker AAPL --years 3 --statement income
    python main.py --ticker AAPL --output data/
"""

import argparse
import sys
import pandas as pd
from typing import Optional
import logging

from Company import Company
from Filling import Filling
from FinancialStatement import IncomeStatement, BalanceSheet, CashFlow
from healpers import save_dataframe_to_csv
from merge_utils import merge_all_statements, format_merged_output
from pattern_logger import get_pattern_logger

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_financial_statements(ticker: str, num_years: int = 1, quarterly: bool = False, enable_pattern_logging: bool = True):
    """
    Fetch and process financial statements for a given ticker.
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'MSFT')
        num_years: Number of years of data to fetch
        quarterly: If True, fetch quarterly data (10-Q), otherwise annual (10-K)
        enable_pattern_logging: If True, log pattern matching statistics
    
    Returns:
        dict: Dictionary containing processed financial statements
    """
    logger.info(f"Fetching financial data for {ticker}...")
    
    # Initialize pattern logger if enabled
    pattern_logger = get_pattern_logger() if enable_pattern_logging else None
    
    try:
        # Initialize company
        company = Company(ticker=ticker)
        logger.info(f"Company CIK: {company.cik}")
        
        # Get the appropriate filings
        filings = company.ten_q_fillings if quarterly else company.ten_k_fillings
        logger.info(f"Found {len(filings)} filings")
        
        # Limit to requested number of years
        filings = filings.iloc[:num_years]
        
        results = {
            'ticker': ticker,
            'cik': company.cik,
            'income_statements': [],
            'balance_sheets': [],
            'cash_flows': [],
            'metadata': []
        }
        
        # Process each filing
        for idx, (report_date, accession_num) in enumerate(filings.items()):
            logger.info(f"\nProcessing filing {idx + 1}/{len(filings)}: {report_date}")
            logger.info(f"Accession number: {accession_num}")
            
            try:
                # Create filing object
                filing = Filling(
                    ticker=ticker,
                    cik=company.cik,
                    acc_num_unfiltered=accession_num,
                    company_facts=company.company_facts,
                    quarterly=quarterly
                )
                
                # Process income statement
                logger.info("Processing Income Statement...")
                filing.process_one_statement("income_statement")
                if filing.income_statement:
                    mapped_df = filing.income_statement.get_mapped_df()
                    results['income_statements'].append({
                        'date': report_date,
                        'original': filing.income_statement.og_df,
                        'mapped': mapped_df
                    })
                    
                    # Log pattern matching
                    if pattern_logger:
                        pattern_logger.log_statement(
                            ticker=ticker,
                            cik=company.cik,
                            statement_type='income_statement',
                            fiscal_year=str(report_date),
                            original_df=filing.income_statement.og_df,
                            mapped_df=mapped_df,
                            statement_object=filing.income_statement
                        )
                
                # Process balance sheet
                logger.info("Processing Balance Sheet...")
                filing.process_one_statement("balance_sheet")
                if filing.balance_sheet:
                    mapped_df = filing.balance_sheet.get_mapped_df()
                    results['balance_sheets'].append({
                        'date': report_date,
                        'original': filing.balance_sheet.og_df,
                        'mapped': mapped_df
                    })
                    
                    # Log pattern matching
                    if pattern_logger:
                        pattern_logger.log_statement(
                            ticker=ticker,
                            cik=company.cik,
                            statement_type='balance_sheet',
                            fiscal_year=str(report_date),
                            original_df=filing.balance_sheet.og_df,
                            mapped_df=mapped_df,
                            statement_object=filing.balance_sheet
                        )
                
                # Process cash flow
                logger.info("Processing Cash Flow...")
                filing.process_one_statement("cash_flow_statement")
                if filing.cash_flow:
                    mapped_df = filing.cash_flow.get_mapped_df()
                    results['cash_flows'].append({
                        'date': report_date,
                        'original': filing.cash_flow.og_df,
                        'mapped': mapped_df
                    })
                    
                    # Log pattern matching
                    if pattern_logger:
                        pattern_logger.log_statement(
                            ticker=ticker,
                            cik=company.cik,
                            statement_type='cash_flow_statement',
                            fiscal_year=str(report_date),
                            original_df=filing.cash_flow.og_df,
                            mapped_df=mapped_df,
                            statement_object=filing.cash_flow
                        )
                
                # Store metadata
                results['metadata'].append({
                    'date': report_date,
                    'accession': accession_num,
                    'taxonomy': filing.taxonomy
                })
                
            except Exception as e:
                logger.error(f"Error processing filing {accession_num}: {e}")
                continue
        
        logger.info(f"\nSuccessfully processed {len(results['income_statements'])} statements")
        return results
        
    except Exception as e:
        logger.error(f"Error fetching data for {ticker}: {e}")
        raise


def save_results(results: dict, output_dir: str = "data"):
    """
    Save financial statement results to CSV files.
    
    Args:
        results: Dictionary containing financial statements
        output_dir: Output directory path
    """
    ticker = results['ticker']
    
    # Save income statements
    for item in results['income_statements']:
        if item['mapped'] is not None:
            save_dataframe_to_csv(
                item['mapped'],
                output_dir,
                ticker,
                f"income_statement_{item['date']}",
                "annual"
            )
    
    # Save balance sheets
    for item in results['balance_sheets']:
        if item['mapped'] is not None:
            save_dataframe_to_csv(
                item['mapped'],
                output_dir,
                ticker,
                f"balance_sheet_{item['date']}",
                "annual"
            )
    
    # Save cash flows
    for item in results['cash_flows']:
        if item['mapped'] is not None:
            save_dataframe_to_csv(
                item['mapped'],
                output_dir,
                ticker,
                f"cash_flow_{item['date']}",
                "annual"
            )
    
    logger.info(f"Results saved to {output_dir}/{ticker}/")


def print_statement(df: pd.DataFrame, title: str):
    """
    Print a financial statement in a readable format.
    
    Args:
        df: DataFrame containing the financial statement
        title: Title to display
    """
    print(f"\n{'='*80}")
    print(f"{title:^80}")
    print(f"{'='*80}")
    print(df.to_string())
    print(f"{'='*80}\n")


def main():
    """
    Main entry point for the CLI.
    """
    parser = argparse.ArgumentParser(
        description='Fetch and process financial statements from SEC EDGAR'
    )
    parser.add_argument(
        '--ticker',
        type=str,
        required=True,
        help='Stock ticker symbol (e.g., AAPL, MSFT)'
    )
    parser.add_argument(
        '--years',
        type=int,
        default=1,
        help='Number of years of data to fetch (default: 1)'
    )
    parser.add_argument(
        '--quarterly',
        action='store_true',
        help='Fetch quarterly data (10-Q) instead of annual (10-K)'
    )
    parser.add_argument(
        '--statement',
        type=str,
        choices=['income', 'balance', 'cashflow', 'all'],
        default='all',
        help='Which statement to fetch (default: all)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Output directory for CSV files (if not specified, prints to console)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Fetch data
        results = get_financial_statements(
            ticker=args.ticker,
            num_years=args.years,
            quarterly=args.quarterly
        )
        
        # Display or save results
        if args.output:
            save_results(results, args.output)
        else:
            # Merge multiple years into single tables
            if args.years > 1:
                logger.info(f"\nMerging {args.years} years of data into unified statements...")
                merged = merge_all_statements(results)
                
                # Print merged statements
                if merged['income_merged'] is not None:
                    print(format_merged_output(merged['income_merged'], args.ticker, 'Income'))
                
                if merged['balance_merged'] is not None:
                    print(format_merged_output(merged['balance_merged'], args.ticker, 'Balance Sheet'))
                
                if merged['cashflow_merged'] is not None:
                    print(format_merged_output(merged['cashflow_merged'], args.ticker, 'Cash Flow'))
            else:
                # Single year - print as before
                for item in results['income_statements']:
                    if item['mapped'] is not None:
                        print_statement(
                            item['mapped'],
                            f"{args.ticker} - Income Statement - {item['date']}"
                        )
                    else:
                        print_statement(
                            item['original'],
                            f"{args.ticker} - Income Statement (Original) - {item['date']}"
                        )
                
                # Print balance sheets
                for item in results['balance_sheets']:
                    if item['mapped'] is not None:
                        # Only show non-zero rows
                        non_zero = item['mapped'][(item['mapped'] != 0).any(axis=1)]
                        print_statement(
                            non_zero,
                            f"{args.ticker} - Balance Sheet - {item['date']}"
                        )
                
                # Print cash flows
                for item in results['cash_flows']:
                    if item['mapped'] is not None:
                        # Only show non-zero rows
                        non_zero = item['mapped'][(item['mapped'] != 0).any(axis=1)]
                        print_statement(
                            non_zero,
                            f"{args.ticker} - Cash Flow - {item['date']}"
                        )
        
        logger.info("Processing complete!")
        
    except KeyboardInterrupt:
        logger.info("\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()