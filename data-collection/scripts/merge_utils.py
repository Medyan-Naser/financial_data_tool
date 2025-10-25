#!/usr/bin/env python3
"""
Utilities for merging financial statements across multiple years.

This module handles the complexities of combining financial data when:
- Different years have different line items
- Companies change their reporting structure
- There are data quality issues or variations
- Quarterly reports may contain cumulative year-to-date data
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple
import logging
from datetime import datetime
from dateutil.relativedelta import relativedelta

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
    try:
        # Convert column names to datetime for proper sorting
        datetime_cols = pd.to_datetime(result.columns)
        # Sort in descending order (newest first)
        sorted_indices = datetime_cols.argsort()[::-1]
        result = result.iloc[:, sorted_indices]
        logger.info(f"Sorted columns: {result.columns[:5].tolist()} ... {result.columns[-5:].tolist()}")
    except Exception as e:
        logger.warning(f"Could not sort columns by date: {e}, using default sort")
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


def detect_fiscal_year(date_str: str) -> int:
    """
    Determine the fiscal year for a given date.
    Most companies use calendar year, but some have different fiscal year ends.
    
    Args:
        date_str: Date string in format 'YYYY-MM-DD'
    
    Returns:
        Fiscal year as integer
    """
    date = pd.to_datetime(date_str)
    # For most companies, fiscal year = calendar year
    # If the month is in Q1 (Jan-Mar), it might belong to previous fiscal year for some companies
    # For now, we'll use the calendar year
    return date.year


def detect_quarter(date_str: str) -> Tuple[int, int]:
    """
    Determine the quarter for a given date.
    
    Args:
        date_str: Date string in format 'YYYY-MM-DD'
    
    Returns:
        Tuple of (fiscal_year, quarter_number)
    """
    date = pd.to_datetime(date_str)
    fiscal_year = date.year
    
    # Determine quarter based on month
    month = date.month
    if month <= 3:
        quarter = 1
    elif month <= 6:
        quarter = 2
    elif month <= 9:
        quarter = 3
    else:
        quarter = 4
    
    return fiscal_year, quarter


def group_quarters_by_year(columns: List[str]) -> Dict[int, Dict[int, str]]:
    """
    Group quarterly column dates by fiscal year and quarter.
    
    Args:
        columns: List of date strings in format 'YYYY-MM-DD'
    
    Returns:
        Dictionary: {fiscal_year: {quarter: date_string}}
    """
    year_quarters = {}
    
    for col in columns:
        fiscal_year, quarter = detect_quarter(col)
        
        if fiscal_year not in year_quarters:
            year_quarters[fiscal_year] = {}
        
        year_quarters[fiscal_year][quarter] = col
    
    return year_quarters


def needs_quarterly_adjustment(df: pd.DataFrame, year_quarters: Dict[int, Dict[int, str]]) -> Dict[str, str]:
    """
    Detect which quarterly columns need adjustment (contain cumulative YTD data).
    
    Strategy:
    1. For each fiscal year with 4 quarters, check if Q4 appears to be cumulative
    2. A Q4 is likely cumulative if: Q4 ≈ Q1 + Q2 + Q3 + Q4_actual
    3. Check multiple rows to confirm the pattern
    
    Args:
        df: DataFrame with quarterly data
        year_quarters: Dictionary mapping {fiscal_year: {quarter: date_string}}
    
    Returns:
        Dictionary: {date_to_adjust: 'cumulative'} mapping columns that need adjustment
    """
    adjustments = {}
    
    for fiscal_year, quarters in year_quarters.items():
        # We need at least Q4 to check, and ideally Q1, Q2, Q3 for comparison
        if 4 not in quarters:
            continue
        
        q4_col = quarters[4]
        
        # Get columns for other quarters if available
        available_quarters = [q for q in [1, 2, 3] if q in quarters]
        
        if len(available_quarters) < 2:
            # Not enough data to determine if it's cumulative
            logger.debug(f"Year {fiscal_year}: Not enough quarters to check Q4 (only have {available_quarters})")
            continue
        
        # Check if Q4 looks like cumulative data
        is_cumulative = check_if_cumulative(df, quarters, available_quarters, q4_col)
        
        if is_cumulative:
            adjustments[q4_col] = 'cumulative'
            logger.info(f"Detected cumulative Q4 data for {fiscal_year}: {q4_col}")
    
    return adjustments


def check_if_cumulative(df: pd.DataFrame, quarters: Dict[int, str], 
                        available_quarters: List[int], q4_col: str) -> bool:
    """
    Check if Q4 column contains cumulative year-to-date data.
    
    Logic:
    - If Q4 value is approximately equal to or greater than Q1+Q2+Q3, it's likely cumulative
    - Check multiple rows (at least 3) to confirm the pattern
    - Use revenue, expenses, or other flow items (not balance sheet items)
    
    Args:
        df: DataFrame with quarterly data
        quarters: Dictionary of {quarter: date_string}
        available_quarters: List of available quarter numbers (1, 2, 3)
        q4_col: Q4 column name to check
    
    Returns:
        True if Q4 appears to be cumulative
    """
    # Select rows that are likely to be flow items (income statement or cash flow)
    # These typically include keywords like 'revenue', 'income', 'expense', 'cash'
    flow_rows = []
    
    for idx in df.index:
        idx_lower = str(idx).lower()
        if any(keyword in idx_lower for keyword in ['revenue', 'income', 'expense', 'cogs', 
                                                      'operating', 'cash', 'net', 'sales']):
            # Exclude per-share items as they don't accumulate
            if 'per share' not in idx_lower and 'eps' not in idx_lower and 'shares outstanding' not in idx_lower:
                flow_rows.append(idx)
    
    if len(flow_rows) < 3:
        logger.debug(f"Not enough flow items to check for cumulative pattern")
        return False
    
    # Check the pattern for multiple rows
    cumulative_votes = 0
    total_checks = 0
    
    for row in flow_rows[:10]:  # Check up to 10 rows
        try:
            # Get Q4 value
            q4_val = df.loc[row, q4_col]
            
            # Skip if Q4 is zero or NaN
            if pd.isna(q4_val) or q4_val == 0:
                continue
            
            # Sum available quarters
            sum_qtrs = sum([df.loc[row, quarters[q]] for q in available_quarters 
                           if quarters[q] in df.columns and not pd.isna(df.loc[row, quarters[q]])])
            
            # Check if Q4 is suspiciously close to or greater than the sum of other quarters
            # Allow for some tolerance (Q4 should be roughly equal to full year if cumulative)
            if sum_qtrs > 0:
                ratio = q4_val / sum_qtrs
                
                # If Q4 is 2.5x to 8x the sum of other quarters, it's likely the full year
                # (because Q4 = Q1 + Q2 + Q3 + Q4_actual, so ratio ≈ 4/3 = 1.33 minimum)
                if 1.2 <= ratio <= 8.0:
                    cumulative_votes += 1
                    logger.debug(f"Row '{row}': Q4={q4_val:.0f}, Sum(Q1-Q3)={sum_qtrs:.0f}, Ratio={ratio:.2f} -> Cumulative")
                else:
                    logger.debug(f"Row '{row}': Q4={q4_val:.0f}, Sum(Q1-Q3)={sum_qtrs:.0f}, Ratio={ratio:.2f} -> Not cumulative")
                
                total_checks += 1
        
        except Exception as e:
            logger.debug(f"Error checking row {row}: {e}")
            continue
    
    # If majority of checks suggest cumulative, return True
    if total_checks >= 3:
        is_cumulative = cumulative_votes / total_checks >= 0.5
        logger.info(f"Cumulative check: {cumulative_votes}/{total_checks} rows suggest cumulative = {is_cumulative}")
        return is_cumulative
    
    logger.debug(f"Not enough valid checks ({total_checks}) to determine if cumulative")
    return False


def adjust_quarterly_data(df: pd.DataFrame, adjustments: Dict[str, str], 
                         year_quarters: Dict[int, Dict[int, str]]) -> pd.DataFrame:
    """
    Adjust quarterly data by subtracting Q1+Q2+Q3 from cumulative Q4.
    
    Args:
        df: DataFrame with quarterly data
        adjustments: Dictionary of {date: 'cumulative'} for columns needing adjustment
        year_quarters: Dictionary mapping {fiscal_year: {quarter: date_string}}
    
    Returns:
        Adjusted DataFrame
    """
    df_adjusted = df.copy()
    
    for fiscal_year, quarters in year_quarters.items():
        if 4 not in quarters:
            continue
        
        q4_col = quarters[4]
        
        # Check if this Q4 needs adjustment
        if q4_col not in adjustments:
            continue
        
        logger.info(f"Adjusting Q4 {fiscal_year} ({q4_col}) by subtracting Q1+Q2+Q3")
        
        # Get available quarter columns
        available_quarters = [q for q in [1, 2, 3] if q in quarters and quarters[q] in df.columns]
        
        if not available_quarters:
            logger.warning(f"Cannot adjust Q4 {q4_col}: no other quarters available")
            continue
        
        # Adjust each row
        for row in df.index:
            try:
                # Get Q4 value (which is cumulative)
                q4_cumulative = df.loc[row, q4_col]
                
                # Skip if NaN or zero
                if pd.isna(q4_cumulative) or q4_cumulative == 0:
                    continue
                
                # Sum Q1, Q2, Q3
                sum_q123 = sum([df.loc[row, quarters[q]] for q in available_quarters 
                               if not pd.isna(df.loc[row, quarters[q]])])
                
                # Calculate actual Q4: Q4_actual = Q4_cumulative - (Q1 + Q2 + Q3)
                q4_actual = q4_cumulative - sum_q123
                
                # Update the dataframe
                df_adjusted.loc[row, q4_col] = q4_actual
                
                logger.debug(f"Row '{row}': Q4 adjusted from {q4_cumulative:.0f} to {q4_actual:.0f}")
            
            except Exception as e:
                logger.debug(f"Error adjusting row {row}: {e}")
                continue
        
        logger.info(f"Successfully adjusted Q4 {fiscal_year} ({q4_col})")
    
    return df_adjusted


def process_quarterly_adjustments(df: pd.DataFrame, columns: List[str]) -> Tuple[pd.DataFrame, Dict]:
    """
    Main function to detect and adjust quarterly cumulative data.
    
    This is called as a final step after merging all columns.
    
    Args:
        df: DataFrame with merged quarterly data (columns are dates, rows are line items)
        columns: List of column names (dates)
    
    Returns:
        Tuple of (adjusted_dataframe, adjustment_info_dict)
    """
    logger.info("Starting quarterly adjustment process...")
    
    # Step 1: Group quarters by fiscal year
    year_quarters = group_quarters_by_year(columns)
    logger.info(f"Identified {len(year_quarters)} fiscal years in the data")
    
    # Step 2: Detect which quarters need adjustment
    adjustments = needs_quarterly_adjustment(df, year_quarters)
    
    if not adjustments:
        logger.info("No quarterly adjustments needed")
        return df, {}
    
    logger.info(f"Found {len(adjustments)} columns requiring adjustment: {list(adjustments.keys())}")
    
    # Step 3: Perform adjustments
    df_adjusted = adjust_quarterly_data(df, adjustments, year_quarters)
    
    # Step 4: Prepare info for logging/debugging
    adjustment_info = {
        'adjusted_columns': list(adjustments.keys()),
        'fiscal_years_adjusted': [fy for fy, qs in year_quarters.items() if qs.get(4) in adjustments],
        'adjustment_type': 'cumulative_q4_correction'
    }
    
    logger.info(f"Quarterly adjustment complete. Adjusted {len(adjustments)} columns.")
    
    return df_adjusted, adjustment_info
