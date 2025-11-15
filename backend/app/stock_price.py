"""
Stock Price API Endpoints

Provides real-time and historical stock price data using:
- yfinance for historical OHLC data (free)
- Finnhub for real-time quotes (free tier)

All responses are cached for 1 week to minimize API calls.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import yfinance as yf
import requests
import pandas as pd
from datetime import datetime, timedelta
import logging
from .api_cache import api_cache

logger = logging.getLogger(__name__)

router = APIRouter()

# Finnhub configuration
FINNHUB_API_KEY = "d4capm9r01qudf6helq0d4capm9r01qudf6helqg"
FINNHUB_BASE_URL = "https://finnhub.io/api/v1"


def get_historical_prices_yfinance(symbol: str, period: str = "1y") -> dict:
    """
    Fetch historical stock prices using yfinance
    
    Args:
        symbol: Stock ticker symbol
        period: Time period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
    
    Returns:
        Dictionary with dates, prices, and metadata
    """
    try:
        logger.info(f"Fetching historical data for {symbol} (period: {period})")
        
        # Download historical data with timeout
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period, timeout=10)
        
        if hist.empty:
            logger.warning(f"No historical data found for {symbol}")
            return None
        
        # Sample data if too many points (for performance)
        max_points = 500
        if len(hist) > max_points:
            # Sample evenly to reduce data points
            step = len(hist) // max_points
            hist = hist.iloc[::step]
            logger.info(f"Sampled data from {len(hist) * step} to {len(hist)} points")
        
        # Convert to format suitable for charts
        data = {
            'symbol': symbol,
            'dates': hist.index.strftime('%Y-%m-%d').tolist(),
            'timestamps': (hist.index.astype(int) // 10**9).tolist(),  # Convert to Unix timestamps
            'open': hist['Open'].round(2).tolist(),
            'high': hist['High'].round(2).tolist(),
            'low': hist['Low'].round(2).tolist(),
            'close': hist['Close'].round(2).tolist(),
            'volume': hist['Volume'].astype(int).tolist(),
            'data_points': len(hist),
            'start_date': hist.index[0].strftime('%Y-%m-%d'),
            'end_date': hist.index[-1].strftime('%Y-%m-%d'),
            'currency': ticker.info.get('currency', 'USD') if hasattr(ticker, 'info') else 'USD'
        }
        
        logger.info(f"Retrieved {data['data_points']} data points for {symbol}")
        return data
        
    except Exception as e:
        logger.error(f"Error fetching historical data for {symbol}: {e}")
        # Check if it's a rate limit error
        error_msg = str(e).lower()
        if 'rate' in error_msg or 'limit' in error_msg or 'too many' in error_msg:
            raise Exception(f"Too Many Requests. Rate limited. Try after a while.")
        raise


def get_realtime_quote_finnhub(symbol: str) -> dict:
    """
    Fetch real-time quote using Finnhub API
    
    Args:
        symbol: Stock ticker symbol
    
    Returns:
        Dictionary with current price data
    """
    try:
        url = f"{FINNHUB_BASE_URL}/quote"
        params = {
            'symbol': symbol,
            'token': FINNHUB_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if not data or data.get('c') == 0:
            logger.warning(f"No real-time quote data for {symbol}")
            return None
        
        return {
            'symbol': symbol,
            'current': round(data.get('c', 0), 2),
            'open': round(data.get('o', 0), 2),
            'high': round(data.get('h', 0), 2),
            'low': round(data.get('l', 0), 2),
            'previous_close': round(data.get('pc', 0), 2),
            'change': round(data.get('d', 0), 2),
            'change_percent': round(data.get('dp', 0), 2),
            'timestamp': int(data.get('t', 0))
        }
        
    except Exception as e:
        logger.error(f"Error fetching real-time quote for {symbol}: {e}")
        return None


@router.get("/api/stock-price/historical/{symbol}")
async def get_historical_prices(
    symbol: str,
    period: str = Query(default="1y", regex="^(1d|5d|1mo|3mo|6mo|1y|2y|5y|10y|ytd|max)$")
):
    """
    Get historical stock prices
    
    Parameters:
    - symbol: Stock ticker symbol (e.g., AAPL)
    - period: Time period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
    
    Returns historical OHLC data with dates and volumes
    """
    try:
        symbol = symbol.upper()
        
        # Check cache first
        cache_key = f"historical_{symbol}_{period}"
        cached_data = api_cache.get('stock_price', symbol=symbol, period=period)
        
        if cached_data:
            logger.info(f"Returning cached historical data for {symbol}")
            return cached_data
        
        # Fetch fresh data
        data = get_historical_prices_yfinance(symbol, period)
        
        if not data:
            raise HTTPException(
                status_code=404,
                detail=f"No historical data found for symbol {symbol}"
            )
        
        # Cache the result
        api_cache.set(data, 'stock_price', symbol=symbol, period=period)
        
        return data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_historical_prices: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/stock-price/quote/{symbol}")
async def get_quote(symbol: str):
    """
    Get real-time stock quote
    
    Parameters:
    - symbol: Stock ticker symbol (e.g., AAPL)
    
    Returns current price, change, and other real-time data
    """
    try:
        symbol = symbol.upper()
        
        # Check cache first (cache for shorter time - 5 minutes for real-time data)
        # For now, using the same cache duration as other APIs
        cached_data = api_cache.get('stock_quote', symbol=symbol)
        
        if cached_data:
            logger.info(f"Returning cached quote for {symbol}")
            return cached_data
        
        # Fetch fresh data
        data = get_realtime_quote_finnhub(symbol)
        
        if not data:
            # Fallback to yfinance if Finnhub fails
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                hist = ticker.history(period="2d")
                
                if not hist.empty:
                    current_price = hist['Close'].iloc[-1]
                    prev_close = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
                    change = current_price - prev_close
                    change_percent = (change / prev_close * 100) if prev_close != 0 else 0
                    
                    data = {
                        'symbol': symbol,
                        'current': round(current_price, 2),
                        'open': round(hist['Open'].iloc[-1], 2),
                        'high': round(hist['High'].iloc[-1], 2),
                        'low': round(hist['Low'].iloc[-1], 2),
                        'previous_close': round(prev_close, 2),
                        'change': round(change, 2),
                        'change_percent': round(change_percent, 2),
                        'timestamp': int(hist.index[-1].timestamp())
                    }
            except Exception as e:
                logger.error(f"Fallback to yfinance also failed: {e}")
        
        if not data:
            raise HTTPException(
                status_code=404,
                detail=f"No quote data found for symbol {symbol}"
            )
        
        # Cache the result
        api_cache.set(data, 'stock_quote', symbol=symbol)
        
        return data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_quote: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/stock-price/combined/{symbol}")
async def get_combined_data(
    symbol: str,
    period: str = Query(default="1y", regex="^(1d|5d|1mo|3mo|6mo|1y|2y|5y|10y|ytd|max)$")
):
    """
    Get both historical and real-time data in one call
    
    Parameters:
    - symbol: Stock ticker symbol (e.g., AAPL)
    - period: Time period for historical data
    
    Returns both historical OHLC data and current quote
    """
    try:
        symbol = symbol.upper()
        
        # Fetch both datasets
        historical = await get_historical_prices(symbol, period)
        quote = await get_quote(symbol)
        
        return {
            'symbol': symbol,
            'historical': historical,
            'quote': quote,
            'fetched_at': datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_combined_data: {e}")
        raise HTTPException(status_code=500, detail=str(e))
