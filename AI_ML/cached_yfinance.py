"""
Cached Yahoo Finance Wrapper

This module provides a caching wrapper for yfinance to avoid rate limiting.
All yfinance calls should use this module instead of direct yfinance imports.
"""

import sys
import os
import yfinance as yf
from typing import Optional, Union
import pandas as pd

# Add backend to path for cache utility
backend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backend', 'app')
sys.path.insert(0, backend_path)

try:
    from api_cache import api_cache
except ImportError:
    # Fallback if cache module not available
    print("Warning: API cache module not available, using direct yfinance calls")
    api_cache = None


class CachedTicker:
    """Wrapper for yfinance Ticker with caching"""
    
    def __init__(self, ticker: str):
        self.ticker = ticker
        self._yf_ticker = yf.Ticker(ticker)
    
    def history(self, period: str = "1mo", interval: str = "1d", **kwargs) -> pd.DataFrame:
        """
        Get historical market data with caching
        
        Args:
            period: Time period (e.g., '1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', 'max')
            interval: Data interval (e.g., '1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h', '1d', '5d', '1wk', '1mo', '3mo')
            **kwargs: Additional arguments
        
        Returns:
            DataFrame with historical data
        """
        if api_cache is None:
            return self._yf_ticker.history(period=period, interval=interval, **kwargs)
        
        # Create cache params
        cache_params = {
            'ticker': self.ticker,
            'period': period,
            'interval': interval,
            'method': 'history',
            **kwargs
        }
        
        # Try cache first
        cached_data = api_cache.get('yfinance', **cache_params)
        if cached_data is not None:
            return cached_data
        
        # Cache miss - fetch from yfinance
        data = self._yf_ticker.history(period=period, interval=interval, **kwargs)
        
        # Cache valid responses only
        if not data.empty:
            api_cache.set(data, 'yfinance', **cache_params)
        
        return data
    
    def info(self) -> dict:
        """Get ticker info (not cached due to frequent changes)"""
        return self._yf_ticker.info
    
    @property
    def financials(self):
        """Get financials (not cached)"""
        return self._yf_ticker.financials
    
    @property
    def quarterly_financials(self):
        """Get quarterly financials (not cached)"""
        return self._yf_ticker.quarterly_financials


def download(tickers: Union[str, list], 
             start: Optional[str] = None,
             end: Optional[str] = None,
             period: str = "1mo",
             interval: str = "1d",
             progress: bool = True,
             auto_adjust: bool = True,
             **kwargs) -> pd.DataFrame:
    """
    Cached version of yf.download()
    
    Args:
        tickers: Ticker symbol(s)
        start: Start date (YYYY-MM-DD)
        end: End date (YYYY-MM-DD)
        period: Time period
        interval: Data interval
        progress: Show progress bar
        auto_adjust: Adjust OHLC data
        **kwargs: Additional arguments
    
    Returns:
        DataFrame with market data
    """
    if api_cache is None:
        return yf.download(tickers, start=start, end=end, period=period, 
                          interval=interval, progress=progress, 
                          auto_adjust=auto_adjust, **kwargs)
    
    # Create cache params
    cache_params = {
        'tickers': tickers if isinstance(tickers, str) else ','.join(tickers),
        'start': start,
        'end': end,
        'period': period,
        'interval': interval,
        'auto_adjust': auto_adjust,
        'method': 'download',
        **kwargs
    }
    
    # Try cache first
    cached_data = api_cache.get('yfinance', **cache_params)
    if cached_data is not None:
        return cached_data
    
    # Cache miss - fetch from yfinance
    data = yf.download(tickers, start=start, end=end, period=period,
                      interval=interval, progress=progress,
                      auto_adjust=auto_adjust, **kwargs)
    
    # Cache valid responses only
    if not data.empty:
        api_cache.set(data, 'yfinance', **cache_params)
    
    return data


def Ticker(ticker: str) -> CachedTicker:
    """
    Create a cached Ticker object
    
    Args:
        ticker: Ticker symbol
    
    Returns:
        CachedTicker instance
    """
    return CachedTicker(ticker)


# Cleanup expired cache on import
if api_cache is not None:
    api_cache.clear_expired()
