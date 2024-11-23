from fastapi import APIRouter, HTTPException
import pandas as pd
import os
from fastapi.responses import JSONResponse

router = APIRouter()

# Get the absolute path to the current directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.abspath(os.path.join(BASE_DIR, "../api/financials"))


@router.get("/api/financials/{ticker}")
async def get_financial_data(ticker: str):
    # File paths for balance sheet and income statement
    balance_sheet_file = os.path.join(BASE_DIR, f"{ticker}_balance_sheet.csv")
    income_statement_file = os.path.join(BASE_DIR, f"{ticker}_income_statement.csv")

    # Check if files exist and load them
    if not os.path.exists(balance_sheet_file):
        raise HTTPException(status_code=404, detail=f"Balance sheet for {ticker} not found.")
    if not os.path.exists(income_statement_file):
        raise HTTPException(status_code=404, detail=f"Income statement for {ticker} not found.")

    # Load the balance sheet
    balance_sheet_df = pd.read_csv(balance_sheet_file)
    balance_sheet_years = balance_sheet_df.columns[1:].tolist()  # Exclude the first column (index)
    balance_sheet_items = balance_sheet_df.iloc[:, 0].tolist()  # First column as index
    balance_sheet_data = balance_sheet_df.iloc[:, 1:].values.tolist()

    # Load the income statement
    income_statement_df = pd.read_csv(income_statement_file)
    income_statement_years = income_statement_df.columns[1:].tolist()  # Exclude the first column (index)
    income_statement_items = income_statement_df.iloc[:, 0].tolist()  # First column as index
    income_statement_data = income_statement_df.iloc[:, 1:].values.tolist()

    return JSONResponse({
        "balance_sheet": {
            "columns": balance_sheet_years,
            "index": balance_sheet_items,
            "data": balance_sheet_data
        },
        "income_statement": {
            "columns": income_statement_years,
            "index": income_statement_items,
            "data": income_statement_data
        }
    })
