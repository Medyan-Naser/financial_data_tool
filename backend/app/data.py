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
BASE_DIR = os.path.abspath(os.path.join(BASE_DIR, "../api/financials"))

STATEMENT_TYPES = ["income_statement", "balance_sheet", "cash_flow"]


def get_available_tickers() -> List[str]:
    """Get all unique tickers from the financials directory."""
    tickers = set()
    for file in glob.glob(os.path.join(BASE_DIR, "*.csv")):
        filename = os.path.basename(file)
        # Extract ticker from filename (e.g., AAPL_income_statement.csv -> AAPL)
        match = re.match(r"^(.+?)_(income_statement|balance_sheet|cash_flow)", filename)
        if match:
            tickers.add(match.group(1))
    return sorted(list(tickers))


def load_statement(ticker: str, statement_type: str) -> Optional[Dict]:
    """Load a specific financial statement for a ticker."""
    # Try different file patterns (with and without _custom suffix)
    patterns = [
        f"{ticker}_{statement_type}.csv",
        f"{ticker}_{statement_type}_custom.csv"
    ]
    
    for pattern in patterns:
        file_path = os.path.join(BASE_DIR, pattern)
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
async def get_financial_data(ticker: str):
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
        statement_data = load_statement(ticker_upper, statement_type)
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
async def get_specific_statement(ticker: str, statement_type: str):
    """Get a specific financial statement for a ticker."""
    ticker_upper = ticker.upper()
    
    if statement_type not in STATEMENT_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid statement type. Must be one of: {', '.join(STATEMENT_TYPES)}")
    
    statement_data = load_statement(ticker_upper, statement_type)
    if not statement_data:
        raise HTTPException(status_code=404, detail=f"{statement_type} for {ticker_upper} not found.")
    
    return JSONResponse({
        "ticker": ticker_upper,
        "statement_type": statement_type,
        **statement_data
    })
