# Import notebook libraries and dependencies
import os
import requests
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import sys

# Add parent directory to path for cached APIs
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Use cached yfinance to avoid rate limiting
try:
    import cached_yfinance as yf
except ImportError:
    import yfinance as yf
    print("Warning: Using direct yfinance - caching not available")

# Use cached fredapi to avoid rate limiting
try:
    from cached_fredapi import Fred
except ImportError:
    from fredapi import Fred
    print("Warning: Using direct FRED API - caching not available")

# Set API keys
os.environ["ALPHA_VANTAGE_API_KEY"] = "SX41SKXRRMA9Q01U"
os.environ["FRED_API_KEY"] = "69db3b36e2b3bf578e036a5f42d9b315"

def get_table():
    """
    Get gold and silver metrics including various ratios.
    Returns a Plotly table figure.
    """
    try:
        # Use yfinance to get gold and silver prices
        # GC=F is Gold Futures, SI=F is Silver Futures
        gold_ticker = yf.Ticker("GC=F")
        silver_ticker = yf.Ticker("SI=F")
        
        gold_info = gold_ticker.history(period="1d")
        silver_info = silver_ticker.history(period="1d")
        
        if len(gold_info) == 0 or len(silver_info) == 0:
            # Fallback: use static/cached values
            gold_price = 2000.0
            silver_price = 24.0
        else:
            gold_price = round(gold_info['Close'].iloc[-1], 2)
            silver_price = round(silver_info['Close'].iloc[-1], 2)
        
        # Calculate Gold/Silver Ratio
        goldsilver_ratio = round(gold_price / silver_price, 2) if silver_price > 0 else 0
        
        # Get DJIA
        try:
            djia_ticker = yf.Ticker("^DJI")
            djia_data = djia_ticker.history(period="1d")
            djia = djia_data['Close'].iloc[-1] if len(djia_data) > 0 else 35000
        except:
            djia = 35000  # Fallback value
        
        dowgold_ratio = round(djia / gold_price, 2) if gold_price > 0 else 0
        
        # Initialize FRED
        fred_api_key = os.getenv("FRED_API_KEY")
        fred = Fred(api_key=fred_api_key)
        
        # Retrieve Federal Reserve data - Single Family Home Price
        try:
            re = fred.get_series_latest_release('MSPUS')
            re = pd.DataFrame(re)
            re.columns = ['Single Family Home Price']
            re.index = pd.to_datetime(re.index)
            re.index.name = 'Date'
            last_re_price = re.iloc[-1].values[0]
            re_gold_ratio = round(last_re_price / gold_price, 2) if gold_price > 0 else 0
        except:
            last_re_price = 0
            re_gold_ratio = 0
        
        # Retrieve monetary base data
        try:
            money = fred.get_series_latest_release('BOGMBASE')
            money = pd.DataFrame(money)
            money.columns = ['Monetary Base']
            money.index = pd.to_datetime(money.index)
            money.index.name = 'Date'
            monetary_base_billions = round(money.iloc[-1].values[0] / 1000, 2)
            gold_base_ratio = round(gold_price / monetary_base_billions, 4) if monetary_base_billions > 0 else 0
        except:
            monetary_base_billions = 0
            gold_base_ratio = 0
        
        # Create table
        table = go.Figure(data=[go.Table(
            header=dict(
                values=['Metrics', 'Values'],
                fill_color='paleturquoise',
                align='left',
                font=dict(size=14, color='black')
            ),
            cells=dict(
                values=[
                    ['Gold Spot ($/oz)', 'Silver Spot ($/oz)', 'Gold/Silver Ratio', 
                     'Dow/Gold Ratio', "Real Estate/Gold Ratio", "Gold/Monetary Base Ratio"],
                    [f"${gold_price}", f"${silver_price}", goldsilver_ratio, 
                     dowgold_ratio, re_gold_ratio, gold_base_ratio]
                ],
                fill_color='lavender',
                align='left',
                font=dict(size=12)
            )
        )])
        
        table.update_layout(
            title="Gold & Silver Metrics",
            margin=dict(l=10, r=10, t=40, b=10)
        )
        
        return table
        
    except Exception as e:
        print(f"Error generating gold/silver table: {e}")
        # Return error table
        table = go.Figure(data=[go.Table(
            header=dict(values=['Error'], fill_color='red', align='left'),
            cells=dict(values=[[f"Error loading data: {str(e)}"]], fill_color='lightgray', align='left')
        )])
        return table
