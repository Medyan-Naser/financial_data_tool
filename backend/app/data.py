from fastapi import APIRouter
import pandas as pd
import os
from fastapi.responses import JSONResponse


router = APIRouter()

# Get the absolute path to the current directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Combine the path with '../data/financials'
BASE_DIR = os.path.abspath(os.path.join(BASE_DIR, "../api/financials"))



@router.get("/api/financials/{ticker}")
async def get_financial_data(ticker: str):
    # Load the data from the CSV file into a DataFrame
    DATA_FILE = os.path.join(BASE_DIR, f"{ticker}_balance_sheet.csv")
    df = pd.read_csv(DATA_FILE)
    
    # Extract years (columns) and financial items (rows)
    years = df.columns[1:].tolist()  # Assuming the first column is the index (financial items)
    financial_items = df.iloc[:, 0].tolist()  # First column is the index with financial items
    
    # Convert data (matrix form, rows: financial items, columns: years)
    data = df.iloc[:, 1:].values.tolist()  # Remove the first column (years)

    return JSONResponse({
        "columns": years,  # years (x-axis)
        "index": financial_items,  # financial items (labels for y-axis)
        "data": data  # numerical data for charting
    })
