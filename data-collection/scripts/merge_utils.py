#!/usr/bin/env python3
"""
Utilities for merging financial statements across multiple years.

This module handles the complexities of combining financial data when:
- Different years have different line items
- Companies change their reporting structure
- There are data quality issues or variations
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


def merge_statements_by_year(statements: List[Dict], statement_type: str) -> Optional[pd.DataFrame]:
    """
    Merge multiple years of financial statements into a single DataFrame.
    
    Strategy:
    1. Union of all line items across years (handles different reporting)
    2. Fill missing values with 0 (some items not reported every year)
    3. Sort columns by date (most recent first)
    4. Preserve data integrity (no sign changes during merge)
    
    Args:
        statements: List of dicts with 'date' and 'mapped' DataFrame
        statement_type: 'income', 'balance', or 'cashflow'
    
    Returns:
        Merged DataFrame with all years, or None if no valid data
    """
    if not statements:
        logger.warning(f"No {statement_type} statements to merge")
        return None
    
    # Filter out None dataframes
    valid_statements = [(s['date'], s['mapped']) for s in statements 
                        if s.get('mapped') is not None and not s['mapped'].empty]
    
    if not valid_statements:
        logger.warning(f"No valid {statement_type} statements after filtering")
        return None
    
    if len(valid_statements) == 1:
        # Single year - return as is but format nicely
        date, df = valid_statements[0]
        return df
    
    # Multiple years - need to merge
    logger.info(f"Merging {len(valid_statements)} years of {statement_type} data")
    
    # Strategy 1: Create a union of all row indices (line items)
    all_rows = set()
    for date, df in valid_statements:
        all_rows.update(df.index.tolist())
    
    logger.info(f"Total unique line items across all years: {len(all_rows)}")
    
    # Strategy 2: Build merged DataFrame year by year
    merged_data = {}
    row_order = []  # Preserve order from most recent year
    
    for date, df in valid_statements:
        # Use the date column names from the original DataFrame
        for col in df.columns:
            if col not in merged_data:
                merged_data[col] = {}
        
        # Add this year's data
        for row_name in df.index:
            if row_name not in row_order:
                row_order.append(row_name)
            
            for col in df.columns:
                merged_data[col][row_name] = df.loc[row_name, col]
    
    # Strategy 3: Create final DataFrame with proper alignment
    result = pd.DataFrame(merged_data, index=row_order)
    
    # Strategy 4: Fill missing values with 0 (items not reported in some years)
    result = result.fillna(0)
    
    # Strategy 5: Sort columns by date (most recent first)
    result = result.sort_index(axis=1, ascending=False)
    
    # Strategy 6: Keep only non-zero rows (at least one year has data)
    non_zero_mask = (result != 0).any(axis=1)
    result = result[non_zero_mask]
    
    logger.info(f"Merged {statement_type}: {len(result)} rows, {len(result.columns)} years")
    
    return result


def validate_sign_consistency(df: pd.DataFrame, statement_type: str) -> pd.DataFrame:
    """
    Validate and fix sign inconsistencies in financial statements.
    
    Rules based on old_scripts analysis:
    
    INCOME STATEMENT:
    - Revenue: Always positive
    - COGS: Can be positive or negative (depends on company)
    - Expenses (SG&A, R&D): Can be positive or negative
    - Net Income: Can be positive (profit) or negative (loss)
    - DO NOT flip signs - preserve as reported
    
    BALANCE SHEET:
    - Assets: Always positive
    - Liabilities: Always positive  
    - Equity: Can be negative (accumulated deficit)
    - DO NOT flip signs - preserve as reported
    
    CASH FLOW:
    - Cash inflows: Positive
    - Cash outflows: Negative (or positive if reported that way)
    - Net changes: Can be positive or negative
    - DO NOT flip signs - preserve as reported
    
    Key Insight from old_scripts:
    - Sign changes were only done when equations don't balance
    - We preserve signs AS REPORTED by the company
    - Companies are responsible for their own sign conventions
    
    Args:
        df: Financial statement DataFrame
        statement_type: 'income', 'balance', or 'cashflow'
    
    Returns:
        DataFrame with validated signs (unchanged unless clear error)
    """
    # Based on old_scripts, we DO NOT change signs during merging
    # Signs are only changed when validating equations (not implemented here)
    # Preserve company's reporting as-is
    
    logger.info(f"Sign validation for {statement_type}: Preserving as-reported values")
    
    return df


def detect_reporting_changes(statements: List[Dict], statement_type: str) -> Dict:
    """
    Detect when companies change their reporting structure between years.
    
    Returns:
        Dictionary with:
        - 'added_items': Line items added in later years
        - 'removed_items': Line items removed in later years
        - 'renamed_items': Potential renamed items (similar values)
    """
    if len(statements) < 2:
        return {'added_items': [], 'removed_items': [], 'renamed_items': []}
    
    valid_statements = [(s['date'], s['mapped']) for s in statements 
                        if s.get('mapped') is not None]
    
    if len(valid_statements) < 2:
        return {'added_items': [], 'removed_items': [], 'renamed_items': []}
    
    # Compare first year to last year
    first_date, first_df = valid_statements[0]
    last_date, last_df = valid_statements[-1]
    
    first_items = set(first_df.index)
    last_items = set(last_df.index)
    
    added = list(first_items - last_items)
    removed = list(last_items - first_items)
    
    logger.info(f"Reporting changes detected: {len(added)} added, {len(removed)} removed")
    
    return {
        'added_items': added,
        'removed_items': removed,
        'renamed_items': []  # Would need fuzzy matching to detect
    }


def format_merged_output(df: pd.DataFrame, ticker: str, statement_type: str) -> str:
    """
    Format merged DataFrame for display.
    
    Args:
        df: Merged financial statement
        ticker: Stock ticker
        statement_type: Type of statement
    
    Returns:
        Formatted string for console output
    """
    if df is None or df.empty:
        return f"No {statement_type} data available"
    
    # Get date range
    dates = sorted(df.columns, reverse=True)
    date_range = f"{dates[0]} to {dates[-1]}" if len(dates) > 1 else str(dates[0])
    
    title = f"{ticker} - {statement_type.title()} Statement - {date_range}"
    separator = "=" * 80
    
    output = f"\n{separator}\n"
    output += f"{title:^80}\n"
    output += f"{separator}\n"
    output += df.to_string()
    output += f"\n{separator}\n"
    
    return output


def merge_all_statements(results: Dict) -> Dict:
    """
    Merge all statement types for multiple years.
    
    Args:
        results: Dictionary from get_financial_statements()
    
    Returns:
        Dictionary with merged statements:
        {
            'income_merged': DataFrame,
            'balance_merged': DataFrame,
            'cashflow_merged': DataFrame,
            'metadata': original metadata
        }
    """
    merged = {
        'ticker': results['ticker'],
        'cik': results['cik'],
        'metadata': results['metadata']
    }
    
    # Merge each statement type
    merged['income_merged'] = merge_statements_by_year(
        results['income_statements'], 'Income Statement'
    )
    
    merged['balance_merged'] = merge_statements_by_year(
        results['balance_sheets'], 'Balance Sheet'
    )
    
    merged['cashflow_merged'] = merge_statements_by_year(
        results['cash_flows'], 'Cash Flow'
    )
    
    # Detect reporting changes
    for stmt_type, stmt_list in [
        ('Income', results['income_statements']),
        ('Balance', results['balance_sheets']),
        ('Cash Flow', results['cash_flows'])
    ]:
        changes = detect_reporting_changes(stmt_list, stmt_type)
        if changes['added_items'] or changes['removed_items']:
            logger.info(f"{stmt_type} reporting changes: {changes}")
    
    return merged
