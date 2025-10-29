"""
API Response Caching Utility

This module provides caching functionality for external API calls (Yahoo Finance, FRED)
to avoid rate limiting and improve performance.

Cache Features:
- Only caches valid/successful responses
- 168-hour (1 week) expiration time
- Automatic cleanup of expired entries
- Separate cache storage location
"""

import os
import json
import pickle
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional, Callable
import pandas as pd
import logging

logger = logging.getLogger(__name__)

# Cache directory - create in project root under .cache
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
CACHE_DIR = os.path.join(PROJECT_ROOT, '.api_cache')
CACHE_EXPIRY_HOURS = 168  # 1 week (7 days * 24 hours)


class APICache:
    """Cache manager for API responses"""
    
    def __init__(self, cache_dir: str = CACHE_DIR, expiry_hours: int = CACHE_EXPIRY_HOURS):
        self.cache_dir = Path(cache_dir)
        self.expiry_hours = expiry_hours
        self._ensure_cache_dir()
    
    def _ensure_cache_dir(self):
        """Create cache directory if it doesn't exist"""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Cache directory initialized at: {self.cache_dir}")
    
    def _generate_cache_key(self, api_name: str, **params) -> str:
        """
        Generate a unique cache key based on API name and parameters
        
        Args:
            api_name: Name of the API (e.g., 'yfinance', 'fred')
            **params: Parameters used in the API call
        
        Returns:
            MD5 hash as cache key
        """
        # Sort params to ensure consistent hashing
        sorted_params = json.dumps(params, sort_keys=True)
        key_string = f"{api_name}:{sorted_params}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _get_cache_path(self, cache_key: str) -> Path:
        """Get the file path for a cache key"""
        return self.cache_dir / f"{cache_key}.pkl"
    
    def _is_valid_response(self, data: Any) -> bool:
        """
        Check if the response data is valid and should be cached
        
        Args:
            data: Response data to validate
        
        Returns:
            True if data is valid, False otherwise
        """
        if data is None:
            return False
        
        # For pandas DataFrames, check if not empty
        if isinstance(data, pd.DataFrame):
            return not data.empty
        
        # For pandas Series
        if isinstance(data, pd.Series):
            return len(data) > 0
        
        # For dicts/lists, check if not empty
        if isinstance(data, (dict, list)):
            return len(data) > 0
        
        # For other types, consider valid if not None
        return True
    
    def get(self, api_name: str, **params) -> Optional[Any]:
        """
        Retrieve cached response if available and not expired
        
        Args:
            api_name: Name of the API
            **params: Parameters used in the API call
        
        Returns:
            Cached data if valid, None otherwise
        """
        cache_key = self._generate_cache_key(api_name, **params)
        cache_path = self._get_cache_path(cache_key)
        
        if not cache_path.exists():
            logger.debug(f"Cache miss for {api_name} with params: {params}")
            return None
        
        try:
            with open(cache_path, 'rb') as f:
                cache_entry = pickle.load(f)
            
            # Check expiration
            cached_time = cache_entry.get('timestamp')
            if cached_time:
                expiry_time = cached_time + timedelta(hours=self.expiry_hours)
                if datetime.now() > expiry_time:
                    logger.info(f"Cache expired for {api_name}")
                    cache_path.unlink()  # Delete expired cache
                    return None
            
            logger.info(f"Cache hit for {api_name} with params: {params}")
            return cache_entry.get('data')
        
        except Exception as e:
            logger.error(f"Error reading cache: {e}")
            # Delete corrupted cache file
            if cache_path.exists():
                cache_path.unlink()
            return None
    
    def set(self, data: Any, api_name: str, **params) -> bool:
        """
        Cache a valid response
        
        Args:
            data: Response data to cache
            api_name: Name of the API
            **params: Parameters used in the API call
        
        Returns:
            True if cached successfully, False otherwise
        """
        # Only cache valid responses
        if not self._is_valid_response(data):
            logger.info(f"Skipping cache for invalid response from {api_name}")
            return False
        
        cache_key = self._generate_cache_key(api_name, **params)
        cache_path = self._get_cache_path(cache_key)
        
        try:
            cache_entry = {
                'timestamp': datetime.now(),
                'api_name': api_name,
                'params': params,
                'data': data
            }
            
            with open(cache_path, 'wb') as f:
                pickle.dump(cache_entry, f)
            
            logger.info(f"Cached response for {api_name} with params: {params}")
            return True
        
        except Exception as e:
            logger.error(f"Error writing cache: {e}")
            return False
    
    def clear_expired(self):
        """Remove all expired cache entries"""
        if not self.cache_dir.exists():
            return
        
        expired_count = 0
        for cache_file in self.cache_dir.glob("*.pkl"):
            try:
                with open(cache_file, 'rb') as f:
                    cache_entry = pickle.load(f)
                
                cached_time = cache_entry.get('timestamp')
                if cached_time:
                    expiry_time = cached_time + timedelta(hours=self.expiry_hours)
                    if datetime.now() > expiry_time:
                        cache_file.unlink()
                        expired_count += 1
            except Exception as e:
                logger.error(f"Error checking cache file {cache_file}: {e}")
                # Delete corrupted file
                cache_file.unlink()
                expired_count += 1
        
        if expired_count > 0:
            logger.info(f"Cleared {expired_count} expired cache entries")
    
    def clear_all(self):
        """Remove all cache entries"""
        if not self.cache_dir.exists():
            return
        
        count = 0
        for cache_file in self.cache_dir.glob("*.pkl"):
            cache_file.unlink()
            count += 1
        
        logger.info(f"Cleared all {count} cache entries")
    
    def get_cache_info(self) -> dict:
        """Get information about the cache"""
        if not self.cache_dir.exists():
            return {
                'total_entries': 0,
                'cache_dir': str(self.cache_dir),
                'expiry_hours': self.expiry_hours
            }
        
        cache_files = list(self.cache_dir.glob("*.pkl"))
        total_size = sum(f.stat().st_size for f in cache_files)
        
        return {
            'total_entries': len(cache_files),
            'total_size_mb': total_size / (1024 * 1024),
            'cache_dir': str(self.cache_dir),
            'expiry_hours': self.expiry_hours
        }


def cached_api_call(api_name: str, func: Callable, **params) -> Any:
    """
    Wrapper function to cache API calls
    
    Args:
        api_name: Name of the API (e.g., 'yfinance', 'fred')
        func: Function to call if cache miss
        **params: Parameters to pass to the function
    
    Returns:
        Cached or fresh API response
    
    Example:
        result = cached_api_call('yfinance', yf.download, ticker='AAPL', period='1mo')
    """
    cache = APICache()
    
    # Try to get from cache first
    cached_data = cache.get(api_name, **params)
    if cached_data is not None:
        return cached_data
    
    # Cache miss - call the API
    try:
        result = func(**params)
        
        # Cache the result if valid
        cache.set(result, api_name, **params)
        
        return result
    except Exception as e:
        logger.error(f"API call failed: {e}")
        raise


# Create global cache instance
api_cache = APICache()
