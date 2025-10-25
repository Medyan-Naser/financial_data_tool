from fastapi import APIRouter, HTTPException
import pandas as pd
import os
import glob
import re
from typing import Dict, List, Optional
from fastapi.responses import JSONResponse

router = APIRouter()

# Get the absolute path to the current directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OLD_FINANCIALS_DIR = os.path.abspath(os.path.join(BASE_DIR, "../api/financials"))
CACHED_STATEMENTS_DIR = os.path.abspath(os.path.join(BASE_DIR, "../api/cached_statements"))

STATEMENT_TYPES = ["income_statement", "balance_sheet", "cash_flow"]


def get_available_tickers() -> List[str]:
    """Get all unique tickers from both cached_statements and old financials directory."""
    tickers = set()
    
    # Check cached statements directory (new system)
    if os.path.exists(CACHED_STATEMENTS_DIR):
        for file in glob.glob(os.path.join(CACHED_STATEMENTS_DIR, "*_statements.json")):
            filename = os.path.basename(file)
            # Extract ticker from filename (e.g., AAPL_statements.json -> AAPL)
            match = re.match(r"^(.+?)_statements\.json$", filename)
            if match:
                tickers.add(match.group(1))
    
    # Also check old financials directory for backward compatibility
    if os.path.exists(OLD_FINANCIALS_DIR):
        for file in glob.glob(os.path.join(OLD_FINANCIALS_DIR, "*.csv")):
            filename = os.path.basename(file)
            # Extract ticker from filename (e.g., AAPL_income_statement.csv -> AAPL)
            match = re.match(r"^(.+?)_(income_statement|balance_sheet|cash_flow)", filename)
            if match:
                tickers.add(match.group(1))
    
    return sorted(list(tickers))


def load_statement(ticker: str, statement_type: str, quarterly: bool = False) -> Optional[Dict]:
    """Load a specific financial statement for a ticker from cached statements or old directory."""
    import json
    import sys
    from pathlib import Path
    
    # Determine which cache file to use
    if quarterly:
        cached_file = os.path.join(CACHED_STATEMENTS_DIR, f"{ticker}_quarterly_statements.json")
    else:
        cached_file = os.path.join(CACHED_STATEMENTS_DIR, f"{ticker}_statements.json")
    
    # First, try loading from cached_statements (new system)
    if os.path.exists(cached_file):
        try:
            with open(cached_file, 'r') as f:
                cached_data = json.load(f)
                statements = cached_data.get('statements', {})
                
                if statement_type in statements and statements[statement_type].get('available'):
                    result = {
                        "columns": statements[statement_type]['columns'],
                        "row_names": statements[statement_type]['row_names'],
                        "data": statements[statement_type]['data'],
                        "available": True
                    }
                    
                    # Apply quarterly adjustments for quarterly data on income_statement and cash_flow
                    if quarterly and statement_type in ['income_statement', 'cash_flow']:
                        try:
                            # Import quarterly adjustment logic
                            merge_utils_path = Path(__file__).parent.parent.parent / "data-collection" / "scripts"
                            if str(merge_utils_path) not in sys.path:
                                sys.path.insert(0, str(merge_utils_path))
                            
                            from merge_utils import process_quarterly_adjustments
                            
                            # Convert to DataFrame
                            df = pd.DataFrame(
                                result['data'],
                                columns=result['columns'],
                                index=result['row_names']
                            )
                            
                            # Apply adjustments
                            df_adjusted, adjustment_info = process_quarterly_adjustments(df, df.columns.tolist())
                            
                            # Convert back to dict format
                            result['data'] = df_adjusted.values.tolist()
                            result['columns'] = df_adjusted.columns.tolist()
                            result['row_names'] = df_adjusted.index.tolist()
                            
                            if adjustment_info:
                                print(f"Applied quarterly adjustments to {ticker} {statement_type}: {adjustment_info}")
                        except Exception as e:
                            print(f"Warning: Could not apply quarterly adjustments: {str(e)}")
                    
                    return result
        except Exception as e:
            print(f"Error loading from cache {cached_file}: {str(e)}")
    
    # Fall back to old CSV files
    patterns = [
        f"{ticker}_{statement_type}.csv",
        f"{ticker}_{statement_type}_custom.csv"
    ]
    
    for pattern in patterns:
        file_path = os.path.join(OLD_FINANCIALS_DIR, pattern)
        if os.path.exists(file_path):
            try:
                df = pd.read_csv(file_path)
                # Get columns (dates) - skip first column which is row names
                columns = df.columns[1:].tolist()
                # Get row names (first column)
                row_names = df.iloc[:, 0].tolist()
                # Get data values
                data = df.iloc[:, 1:].values.tolist()
                
                return {
                    "columns": columns,
                    "row_names": row_names,
                    "data": data,
                    "available": True
                }
            except Exception as e:
                print(f"Error loading {file_path}: {str(e)}")
                return None
    
    return None


@router.get("/api/tickers")
async def get_tickers():
    """Get list of all available tickers."""
    try:
        tickers = get_available_tickers()
        return JSONResponse({"tickers": tickers})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/financials/{ticker}")
async def get_financial_data(ticker: str, quarterly: bool = False):
    """Get all financial statements for a ticker."""
    ticker_upper = ticker.upper()
    
    # Check if ticker exists
    available_tickers = get_available_tickers()
    if ticker_upper not in available_tickers:
        raise HTTPException(status_code=404, detail=f"Ticker {ticker_upper} not found.")
    
    # Load each statement type
    response_data = {
        "ticker": ticker_upper,
        "statements": {}
    }
    
    for statement_type in STATEMENT_TYPES:
        statement_data = load_statement(ticker_upper, statement_type, quarterly=quarterly)
        if statement_data:
            response_data["statements"][statement_type] = statement_data
        else:
            response_data["statements"][statement_type] = {
                "available": False,
                "columns": [],
                "row_names": [],
                "data": []
            }
    
    # Check if at least one statement is available
    has_data = any(stmt["available"] for stmt in response_data["statements"].values())
    if not has_data:
        raise HTTPException(status_code=404, detail=f"No financial data found for {ticker_upper}.")
    
    return JSONResponse(response_data)


@router.get("/api/financials/{ticker}/{statement_type}")
async def get_specific_statement(ticker: str, statement_type: str, quarterly: bool = False):
    """Get a specific financial statement for a ticker."""
    ticker_upper = ticker.upper()
    
    if statement_type not in STATEMENT_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid statement type. Must be one of: {', '.join(STATEMENT_TYPES)}")
    
    statement_data = load_statement(ticker_upper, statement_type, quarterly=quarterly)
    if not statement_data:
        raise HTTPException(status_code=404, detail=f"{statement_type} for {ticker_upper} not found.")
    
    return JSONResponse({
        "ticker": ticker_upper,
        "statement_type": statement_type,
        **statement_data
    })
