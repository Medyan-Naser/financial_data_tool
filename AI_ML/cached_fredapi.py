"""
Cached FRED API Wrapper

This module provides a caching wrapper for fredapi to avoid rate limiting.
All FRED API calls should use this module instead of direct fredapi imports.
"""

import sys
import os
from typing import Optional, Union
import pandas as pd
from fredapi import Fred as OriginalFred

# Add backend to path for cache utility
backend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backend', 'app')
sys.path.insert(0, backend_path)

try:
    from api_cache import api_cache
except ImportError:
    # Fallback if cache module not available
    print("Warning: API cache module not available, using direct FRED API calls")
    api_cache = None


class Fred(OriginalFred):
    """Cached wrapper for FRED API"""
    
    def __init__(self, api_key: Optional[str] = None, api_key_file: Optional[str] = None):
        """
        Initialize FRED API with caching
        
        Args:
            api_key: FRED API key
            api_key_file: Path to file containing API key
        """
        super().__init__(api_key=api_key, api_key_file=api_key_file)
    
    def get_series(self, series_id: str, 
                   observation_start: Optional[str] = None,
                   observation_end: Optional[str] = None,
                   **kwargs) -> pd.Series:
        """
        Get a data series from FRED with caching
        
        Args:
            series_id: FRED series ID
            observation_start: Start date (YYYY-MM-DD)
            observation_end: End date (YYYY-MM-DD)
            **kwargs: Additional arguments
        
        Returns:
            Series with FRED data
        """
        if api_cache is None:
            return super().get_series(series_id, observation_start=observation_start,
                                     observation_end=observation_end, **kwargs)
        
        # Create cache params
        cache_params = {
            'series_id': series_id,
            'observation_start': observation_start,
            'observation_end': observation_end,
            'method': 'get_series',
            **kwargs
        }
        
        # Try cache first
        cached_data = api_cache.get('fred', **cache_params)
        if cached_data is not None:
            return cached_data
        
        # Cache miss - fetch from FRED
        data = super().get_series(series_id, observation_start=observation_start,
                                 observation_end=observation_end, **kwargs)
        
        # Cache valid responses only
        if data is not None and len(data) > 0:
            api_cache.set(data, 'fred', **cache_params)
        
        return data
    
    def get_series_info(self, series_id: str) -> dict:
        """
        Get series information (not cached due to metadata nature)
        
        Args:
            series_id: FRED series ID
        
        Returns:
            Dictionary with series metadata
        """
        return super().get_series_info(series_id)
    
    def search(self, search_text: str, **kwargs):
        """
        Search FRED (not cached)
        
        Args:
            search_text: Search query
            **kwargs: Additional arguments
        
        Returns:
            Search results
        """
        return super().search(search_text, **kwargs)


# Cleanup expired cache on import
if api_cache is not None:
    api_cache.clear_expired()
