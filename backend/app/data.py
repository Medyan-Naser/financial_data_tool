from fastapi import APIRouter
import pandas as pd
import os
from fastapi.responses import JSONResponse


router = APIRouter()

# Get the absolute path to the current directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "financial_data.csv")

@router.get("/data")
async def get_financial_data():
    # Load the data from the CSV file into a DataFrame
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
