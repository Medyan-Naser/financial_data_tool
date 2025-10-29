# # Dollar Index
# 
# This chart tracks the U.S. dollar index. The Intercontinental Exchange's index is currently calculated by factoring in the exchange rates of six major world currencies, which include the Euro (EUR), Japanese yen (JPY), Canadian dollar (CAD), British pound (GBP), Swedish krona (SEK), and Swiss franc (CHF). 

# Import notebook libraries and dependencies
import os
import requests
import pandas as pd
import numpy as np
import plotly.express as px
import sys
import os

# Add parent directory to path for cached_yfinance
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Use cached yfinance to avoid rate limiting
try:
    import cached_yfinance as yf
except ImportError:
    import yfinance as yf
    print("Warning: Using direct yfinance - caching not available")


# Retrieve data
ticker = "DX-Y.NYB"
try:
    dollar_index = yf.download(f'{ticker}', progress=False, auto_adjust=False)
    # Check if dataframe is valid
    is_empty = len(dollar_index) == 0 if hasattr(dollar_index, '__len__') else True
    
    if is_empty:
        raise ValueError("Empty dataframe")
    
    # Flatten multi-index columns if present
    if isinstance(dollar_index.columns, pd.MultiIndex):
        dollar_index.columns = [col[0] for col in dollar_index.columns]
    
    has_close = "Close" in dollar_index.columns if hasattr(dollar_index, 'columns') else False
    
    if not has_close:
        raise ValueError("Close column missing")
except Exception as e:
    # Fallback to ^DXY if primary ticker fails
    ticker = "^DXY"
    dollar_index = yf.download(f'{ticker}', progress=False, auto_adjust=False)
    # Flatten multi-index columns if present
    if isinstance(dollar_index.columns, pd.MultiIndex):
        dollar_index.columns = [col[0] for col in dollar_index.columns]

def get_dollar_index_vis():
    dollar_index_vis = px.line(data_frame=dollar_index, y="Close", x=dollar_index.index, title='Daily Close Price of U.S. Dollar Index')
    dollar_index_vis.update_xaxes(
        rangeslider_visible=True,
        rangeselector=dict(
            buttons=list([
                dict(count=1, label="1m", step="month", stepmode="backward"),
                dict(count=6, label="6m", step="month", stepmode="backward"),
                dict(count=1, label="YTD", step="year", stepmode="todate"),
                dict(count=1, label="1y", step="year", stepmode="backward"),
                dict(step="all")
            ])
        )
    )
    return(dollar_index_vis)

