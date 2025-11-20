"""
Stock Price API Endpoints

Provides real-time and historical stock price data using:
- yfinance for historical OHLC data (free)
- Finnhub for real-time quotes (free tier)

All responses are cached for 1 week to minimize API calls.
Cache stored in: .api_cache/stocks/ (JSON format)
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import yfinance as yf
import requests
import pandas as pd
from datetime import datetime, timedelta
import logging
from .cache_manager import stock_cache

logger = logging.getLogger(__name__)

router = APIRouter()

# Finnhub configuration
FINNHUB_API_KEY = "d4capm9r01qudf6helq0d4capm9r01qudf6helqg"
FINNHUB_BASE_URL = "https://finnhub.io/api/v1"


def filter_data_by_period(hist: pd.DataFrame, period: str) -> pd.DataFrame:
    """
    Filter historical data by time period
    
    Args:
        hist: Full historical DataFrame
        period: Time period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
    
    Returns:
        Filtered DataFrame
    """
    if period == 'max':
        return hist
    
    # Calculate cutoff date
    end_date = hist.index[-1]
    
    if period == '1d':
        cutoff_date = end_date - timedelta(days=1)
    elif period == '5d':
        cutoff_date = end_date - timedelta(days=5)
    elif period == '1mo':
        cutoff_date = end_date - timedelta(days=30)
    elif period == '3mo':
        cutoff_date = end_date - timedelta(days=90)
    elif period == '6mo':
        cutoff_date = end_date - timedelta(days=180)
    elif period == '1y':
        cutoff_date = end_date - timedelta(days=365)
    elif period == '2y':
        cutoff_date = end_date - timedelta(days=730)
    elif period == '5y':
        cutoff_date = end_date - timedelta(days=1825)
    elif period == '10y':
        cutoff_date = end_date - timedelta(days=3650)
    elif period == 'ytd':
        # Year to date - from Jan 1 of current year
        cutoff_date = datetime(end_date.year, 1, 1)
    else:
        # Default to 1 year
        cutoff_date = end_date - timedelta(days=365)
    
    # Filter data
    filtered_hist = hist[hist.index >= cutoff_date]
    return filtered_hist


def get_max_historical_data(symbol: str) -> pd.DataFrame:
    """
    Fetch MAX historical data for a symbol (used for caching)
    
    Args:
        symbol: Stock ticker symbol
    
    Returns:
        DataFrame with full historical data
    """
    logger.info(f"Fetching MAX historical data for {symbol}")
    ticker = yf.Ticker(symbol)
    hist = ticker.history(period='max', timeout=10)
    
    if hist.empty:
        logger.warning(f"No historical data found for {symbol}")
        return None
    
    return hist


def get_historical_prices_yfinance(symbol: str, period: str = "1y") -> dict:
    """
    Fetch historical stock prices using yfinance.
    Strategy: Fetch MAX data once and filter locally for different periods.
    
    Args:
        symbol: Stock ticker symbol
        period: Time period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
    
    Returns:
        Dictionary with dates, prices, and metadata
    """
    try:
        logger.info(f"Getting historical data for {symbol} (period: {period})")
        
        # Try to get MAX data from cache first
        cached_max_data = stock_cache.get('historical', symbol=symbol, period='max')
        
        if cached_max_data:
            logger.info(f"Found cached MAX data for {symbol}, filtering locally")
            # Reconstruct DataFrame from cached data
            hist = pd.DataFrame({
                'Open': cached_max_data['open'],
                'High': cached_max_data['high'],
                'Low': cached_max_data['low'],
                'Close': cached_max_data['close'],
                'Volume': cached_max_data['volume']
            })
            hist.index = pd.to_datetime(cached_max_data['dates'])
            currency = cached_max_data.get('currency', 'USD')
        else:
            # Fetch MAX data and cache it
            logger.info(f"No cached MAX data found, fetching from API")
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period='max', timeout=10)
            
            if hist.empty:
                logger.warning(f"No historical data found for {symbol}")
                return None
            
            currency = ticker.info.get('currency', 'USD') if hasattr(ticker, 'info') else 'USD'
            
            # Cache the MAX data
            max_data = {
                'symbol': symbol,
                'dates': hist.index.strftime('%Y-%m-%d').tolist(),
                'timestamps': (hist.index.astype(int) // 10**9).tolist(),
                'open': hist['Open'].round(2).tolist(),
                'high': hist['High'].round(2).tolist(),
                'low': hist['Low'].round(2).tolist(),
                'close': hist['Close'].round(2).tolist(),
                'volume': hist['Volume'].astype(int).tolist(),
                'data_points': len(hist),
                'start_date': hist.index[0].strftime('%Y-%m-%d'),
                'end_date': hist.index[-1].strftime('%Y-%m-%d'),
                'currency': currency
            }
            stock_cache.set('historical', max_data, symbol=symbol, period='max')
            logger.info(f"Cached MAX data for {symbol} ({len(hist)} points)")
        
        # Filter data by requested period
        if period != 'max':
            hist = filter_data_by_period(hist, period)
            logger.info(f"Filtered to {period}: {len(hist)} data points")
        
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
            'timestamps': (hist.index.astype(int) // 10**9).tolist(),
            'open': hist['Open'].round(2).tolist(),
            'high': hist['High'].round(2).tolist(),
            'low': hist['Low'].round(2).tolist(),
            'close': hist['Close'].round(2).tolist(),
            'volume': hist['Volume'].astype(int).tolist(),
            'data_points': len(hist),
            'start_date': hist.index[0].strftime('%Y-%m-%d'),
            'end_date': hist.index[-1].strftime('%Y-%m-%d'),
            'currency': currency
        }
        
        logger.info(f"Returning {data['data_points']} data points for {symbol} ({period})")
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
    
    Note: This endpoint now fetches MAX data once and filters locally for better performance.
    The MAX data is cached, so subsequent requests for different periods are served quickly.
    """
    try:
        symbol = symbol.upper()
        
        # Get data (will use cached MAX data if available and filter locally)
        data = get_historical_prices_yfinance(symbol, period)
        
        if not data:
            raise HTTPException(
                status_code=404,
                detail=f"No historical data found for symbol {symbol}"
            )
        
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
        
        # Check cache first
        cached_data = stock_cache.get('quote', symbol=symbol)
        
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
        stock_cache.set('quote', data, symbol=symbol)
        
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
