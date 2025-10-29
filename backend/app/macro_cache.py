"""
Caching utility for macro economic data endpoints.
Caches valid, non-empty responses to avoid API overload.
"""
import json
import os
import time
from typing import Optional, Dict, Any
from pathlib import Path

# Cache directory
CACHE_DIR = Path(__file__).parent.parent.parent / ".api_cache" / "macro"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Cache expiration time in seconds (1 hour for most data, 1 day for slow-changing data)
CACHE_EXPIRY = {
    "commodities": 3600,  # 1 hour
    "currencies": 3600,   # 1 hour
    "inflation": 86400,   # 24 hours
    "debt-to-gdp": 86400 * 7,  # 7 days
    "dollar-index": 3600,  # 1 hour
    "velocity": 86400 * 7,  # 7 days
    "unemployment": 86400,  # 24 hours
    "real-estate": 86400,  # 24 hours
    "bonds": 3600,  # 1 hour
    "yield-curve": 3600,  # 1 hour
    "markets": 1800,  # 30 minutes
    "gdp-growth": 86400 * 7,  # 7 days
    "consumer-sentiment": 86400,  # 24 hours
    "pmi": 86400,  # 24 hours
    "retail-sales": 86400,  # 24 hours
    "gold-silver": 3600,  # 1 hour
    "crypto": 1800,  # 30 minutes
}

def get_cache_file(endpoint: str) -> Path:
    """Get cache file path for an endpoint."""
    return CACHE_DIR / f"{endpoint}.json"

def is_valid_data(data: Any) -> bool:
    """
    Check if data is valid and non-empty.
    Returns False for None, empty dicts, or data with empty chart data.
    """
    if data is None:
        return False
    
    if isinstance(data, dict):
        # Check if dict is empty
        if not data:
            return False
        
        # Check if it has a 'chart' key with valid data
        if 'chart' in data:
            chart = data['chart']
            if chart is None:
                return False
            if isinstance(chart, dict):
                # Check if chart has data array
                if 'data' in chart:
                    if not chart['data'] or len(chart['data']) == 0:
                        return False
        
        # For nested structures (like commodities, bonds)
        for key, value in data.items():
            if isinstance(value, dict):
                if 'chart' in value:
                    chart = value['chart']
                    if chart is None:
                        return False
                    if isinstance(chart, dict) and 'data' in chart:
                        if not chart['data'] or len(chart['data']) == 0:
                            return False
    
    return True

def get_cached_data(endpoint: str) -> Optional[Dict[str, Any]]:
    """
    Get cached data for an endpoint if it exists and hasn't expired.
    Only returns valid, non-empty data.
    """
    cache_file = get_cache_file(endpoint)
    
    if not cache_file.exists():
        return None
    
    try:
        with open(cache_file, 'r') as f:
            cache_data = json.load(f)
        
        # Check expiration
        cache_time = cache_data.get('timestamp', 0)
        expiry = CACHE_EXPIRY.get(endpoint, 3600)
        
        if time.time() - cache_time > expiry:
            # Cache expired
            return None
        
        # Validate data
        data = cache_data.get('data')
        if not is_valid_data(data):
            # Invalid or empty data, don't return it
            return None
        
        return data
    
    except (json.JSONDecodeError, KeyError, Exception) as e:
        print(f"Error reading cache for {endpoint}: {e}")
        return None

def set_cached_data(endpoint: str, data: Any) -> bool:
    """
    Cache data for an endpoint. Only caches valid, non-empty data.
    Returns True if data was cached, False otherwise.
    """
    # Don't cache invalid or empty data
    if not is_valid_data(data):
        print(f"Not caching invalid/empty data for {endpoint}")
        return False
    
    cache_file = get_cache_file(endpoint)
    
    try:
        cache_data = {
            'timestamp': time.time(),
            'data': data
        }
        
        with open(cache_file, 'w') as f:
            json.dump(cache_data, f)
        
        print(f"Cached data for {endpoint}")
        return True
    
    except Exception as e:
        print(f"Error caching data for {endpoint}: {e}")
        return False

def clear_cache(endpoint: Optional[str] = None):
    """Clear cache for a specific endpoint or all endpoints."""
    if endpoint:
        cache_file = get_cache_file(endpoint)
        if cache_file.exists():
            cache_file.unlink()
    else:
        # Clear all cache files
        for cache_file in CACHE_DIR.glob("*.json"):
            cache_file.unlink()
