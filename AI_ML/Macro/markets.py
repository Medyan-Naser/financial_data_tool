import pandas as pd
import plotly.graph_objects as go
import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path for cached_yfinance
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Use cached yfinance to avoid rate limiting
try:
    import cached_yfinance as yf
except ImportError:
    import yfinance as yf
    print("Warning: Using direct yfinance - caching not available")

# Map of indicators to yfinance tickers - Comprehensive coverage of key markets
TICKERS = [
    # Equity Indices
    ("S&P 500", "^GSPC"),
    ("NASDAQ", "^IXIC"),
    ("Dow Jones", "^DJI"),
    ("Russell 2000", "^RUT"),
    
    # Volatility
    ("VIX (Volatility)", "^VIX"),
    
    # Precious Metals
    ("Gold (XAUUSD)", "XAUUSD=X"),
    ("Silver (XAGUSD)", "XAGUSD=X"),
    ("Platinum", "PL=F"),
    ("Palladium", "PA=F"),
    
    # Energy
    ("Crude Oil (WTI)", "CL=F"),
    ("Brent Oil", "BZ=F"),
    ("Natural Gas", "NG=F"),
    ("Heating Oil", "HO=F"),
    
    # Industrial Metals
    ("Copper", "HG=F"),
    ("Aluminum", "ALI=F"),
    
    # Cryptocurrencies
    ("Bitcoin", "BTC-USD"),
    ("Ethereum", "ETH-USD"),
    ("Solana", "SOL-USD"),
    
    # Currencies
    ("Dollar Index (DXY)", "DX-Y.NYB"),
    ("EUR/USD", "EURUSD=X"),
    ("GBP/USD", "GBPUSD=X"),
    ("JPY/USD", "JPY=X"),
    
    # Bonds
    ("US 10Y Treasury", "^TNX"),
    ("US 2Y Treasury", "^IRX"),
]


def pct(a, b):
    try:
        if b is None or b == 0:
            return None
        return round((a / b - 1) * 100, 2)
    except Exception:
        return None


def compute_changes(hist: pd.DataFrame) -> dict:
    if hist is None or hist.empty:
        return {"Price": None, "Day": None, "Weekly": None, "Monthly": None, "YTD": None, "YoY": None}

    close = hist["Close"].dropna()
    if close.empty:
        return {"Price": None, "Day": None, "Weekly": None, "Monthly": None, "YTD": None, "YoY": None}

    last_date = close.index[-1]
    last = float(close.iloc[-1])

    # Previous day
    prev = float(close.iloc[-2]) if len(close) > 1 else None

    # Weekly (approx 5 trading days)
    prev_week = float(close.iloc[-6]) if len(close) > 6 else None

    # Monthly (approx 21 trading days)
    prev_month = float(close.iloc[-22]) if len(close) > 22 else None

    # YTD: first trading day of current year
    start_year = datetime(last_date.year, 1, 1)
    ytd_series = close[close.index >= start_year]
    first_ytd = float(ytd_series.iloc[0]) if len(ytd_series) > 0 else None

    # YoY: roughly 252 trading days ago
    prev_year = float(close.iloc[-253]) if len(close) > 253 else None

    return {
        "Price": round(last, 2),
        "Day": pct(last, prev),
        "Weekly": pct(last, prev_week),
        "Monthly": pct(last, prev_month),
        "YTD": pct(last, first_ytd),
        "YoY": pct(last, prev_year),
    }


def build_markets_df():
    end = datetime.utcnow()
    start = end - timedelta(days=600)  # enough history for YoY

    rows = []
    for name, ticker in TICKERS:
        try:
            hist = yf.download(ticker, start=start, end=end, progress=False, auto_adjust=False)
            metrics = compute_changes(hist)
            rows.append({"Instrument": name, **metrics})
        except Exception:
            rows.append({"Instrument": name, "Price": None, "Day": None, "Weekly": None, "Monthly": None, "YTD": None, "YoY": None})

    df = pd.DataFrame(rows, columns=["Instrument", "Price", "Day", "Weekly", "Monthly", "YTD", "YoY"])
    return df


# Module-level cache
_markets_df = None
_markets_json = None


def get_markets_data():
    """Get or build markets dataframe (with caching)."""
    global _markets_df, _markets_json
    
    if _markets_df is None:
        _markets_df = build_markets_df()
        _markets_json = _markets_df.to_dict(orient="records")
    
    return _markets_df, _markets_json


def get_markets_table():
    """Get markets data as a Plotly table."""
    markets_df, _ = get_markets_data()
    
    # Enhanced table with better styling
    table = go.Figure(
        data=[
            go.Table(
                header=dict(
                    values=list(markets_df.columns),
                    fill_color="#1e3a8a",
                    font=dict(color="white", size=13, family="Arial"),
                    align="left",
                    height=35
                ),
                cells=dict(
                    values=[markets_df[col] for col in markets_df.columns],
                    fill_color=[["#f8fafc", "#ffffff"] * (len(markets_df) // 2 + 1)],
                    font=dict(color="#1e293b", size=12, family="Arial"),
                    align="left",
                    height=30
                ),
            )
        ]
    )
    table.update_layout(
        title=dict(
            text="📊 Market Indicators Dashboard",
            font=dict(size=18, color="#1e293b", family="Arial")
        ),
        margin=dict(l=10, r=10, t=50, b=10)
    )
    return table


# Get markets JSON data for API endpoint
def get_markets_json():
    """Get markets data as JSON."""
    _, json_data = get_markets_data()
    return json_data
