"""
Extract unit information from FinancialStatement objects.

This module provides utilities to extract unit information for display
in the final output (JSON/CSV).
"""

import logging
from typing import Dict, List, Optional
from unit_handler import UnitNormalizer, UnitInfo

logger = logging.getLogger(__name__)


def extract_units_from_statements(statements: List[Dict], statement_type: str) -> Dict[str, str]:
    """
    Extract unit information from a list of financial statements.
    
    Strategy:
    1. Look at the most recent statement (first in list)
    2. Extract units from units_dict if available
    3. Infer from row names if units_dict not available
    4. Return mapping of row_name -> unit_display_string
    
    Args:
        statements: List of dicts with 'date', 'original', 'mapped' DataFrames,
                   and potentially statement_object
        statement_type: 'income_statement', 'balance_sheet', or 'cash_flow'
    
    Returns:
        Dict mapping standardized row names to unit display strings
        e.g., {'Total revenue': 'USD (millions)', 'Shares outstanding': 'shares (thousands)'}
    """
    if not statements:
        logger.warning(f"No {statement_type} statements to extract units from")
        return {}
    
    units_map = {}
    
    # Get the most recent statement
    recent_stmt = statements[0]
    
    # Try to get statement object (if available from the collection process)
    stmt_obj = recent_stmt.get('statement_object')
    
    if stmt_obj and hasattr(stmt_obj, 'units_dict') and stmt_obj.units_dict:
        logger.info(f"Extracting units from {statement_type} units_dict")
        
        # Map original fact names to mapped row names
        mapped_df = recent_stmt.get('mapped')
        if mapped_df is not None:
            # For each row in the mapped dataframe
            for row_name in mapped_df.index:
                # Try to find corresponding unit info
                # This requires reverse mapping from standardized name to original fact
                # For now, use a simple heuristic
                
                # Check if this is a known type
                unit_str = infer_unit_from_row_name(row_name, statement_type)
                units_map[row_name] = unit_str
        
        # Also extract directly from units_dict
        for fact_name, unit_info in stmt_obj.units_dict.items():
            display_str = UnitNormalizer.format_unit_for_display(unit_info)
            # Store with fact name (will be overridden by mapped name if available)
            units_map[fact_name] = display_str
    else:
        logger.info(f"No units_dict available, inferring units from row names for {statement_type}")
        
        # Fallback: infer from mapped dataframe row names
        mapped_df = recent_stmt.get('mapped')
        if mapped_df is not None:
            for row_name in mapped_df.index:
                unit_str = infer_unit_from_row_name(row_name, statement_type)
                units_map[row_name] = unit_str
    
    logger.info(f"Extracted {len(units_map)} unit mappings for {statement_type}")
    return units_map


def infer_unit_from_row_name(row_name: str, statement_type: str) -> str:
    """
    Infer unit type from standardized row name.
    
    This is a fallback when we don't have explicit unit information.
    
    Args:
        row_name: Standardized row name (e.g., "Total revenue", "Earnings Per Share Diluted")
        statement_type: Type of statement
    
    Returns:
        Unit display string
    """
    row_lower = row_name.lower()
    
    # Per-share items
    if any(keyword in row_lower for keyword in ['per share', 'eps', 'earnings per share']):
        return 'USD per share'
    
    # Share counts
    if any(keyword in row_lower for keyword in [
        'shares outstanding', 'number of shares', 'weighted average',
        'shares issued', 'treasury stock'
    ]):
        return 'shares'
    
    # Ratios and percentages
    if any(keyword in row_lower for keyword in [
        'ratio', 'margin', 'percentage', 'rate', 'return on'
    ]):
        return 'ratio'
    
    # Default to currency for most items
    if statement_type in ['income_statement', 'cash_flow']:
        return 'USD'
    elif statement_type == 'balance_sheet':
        return 'USD'
    
    return 'USD'


def add_units_to_statement_data(statement_data: Dict, units_map: Dict[str, str]) -> Dict:
    """
    Add unit information to statement data structure.
    
    Args:
        statement_data: Statement data dict with 'row_names', 'data', 'columns'
        units_map: Dict mapping row names to unit strings
    
    Returns:
        Enhanced statement data with 'units' field
    """
    if not statement_data or not statement_data.get('available'):
        return statement_data
    
    row_names = statement_data.get('row_names', [])
    
    # Create units list matching row_names order
    units_list = []
    for row_name in row_names:
        unit_str = units_map.get(row_name, 'USD')  # Default to USD
        units_list.append(unit_str)
    
    # Add to statement data
    statement_data['units'] = units_list
    
    logger.debug(f"Added {len(units_list)} units to statement data")
    return statement_data
