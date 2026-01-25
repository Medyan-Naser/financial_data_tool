"""
Detailed cache inspection
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.api_cache import api_cache
import json

print("=" * 60)
print("DETAILED CACHE INSPECTION")
print("=" * 60)

# Get AAPL cache
cached_data = api_cache.get('stock_price', symbol='AAPL', period='1y')

if cached_data:
    print("\n✓ AAPL (1y) found in cache!")
    print("\nCache structure:")
    print(json.dumps({
        'keys': list(cached_data.keys()),
        'symbol': cached_data.get('symbol'),
        'fetched_at': cached_data.get('fetched_at'),
        'has_historical': 'historical' in cached_data,
        'has_quote': 'quote' in cached_data
    }, indent=2))
    
    if 'historical' in cached_data:
        hist = cached_data['historical']
        print("\nHistorical data structure:")
        print(json.dumps({
            'keys': list(hist.keys()) if isinstance(hist, dict) else 'not a dict',
            'data_points': hist.get('data_points') if isinstance(hist, dict) else None,
            'symbol': hist.get('symbol') if isinstance(hist, dict) else None
        }, indent=2))
    
    if 'quote' in cached_data:
        quote = cached_data['quote']
        print("\nQuote data:")
        print(json.dumps(quote, indent=2))

else:
    print("\n✗ AAPL (1y) NOT in cache")

print("\n" + "=" * 60)

# Now test if a fresh request would use cache
print("\nSimulating endpoint behavior:")
print("-" * 60)

# This is what the endpoint does
symbol = 'AAPL'
period = '1y'

cached = api_cache.get('stock_price', symbol=symbol, period=period)
if cached:
    print(f"✓ Cache HIT for {symbol} ({period})")
    print(f"  Would return cached data immediately")
    print(f"  No API call would be made!")
else:
    print(f"✗ Cache MISS for {symbol} ({period})")
    print(f"  Would call yfinance API")
    print(f"  May hit rate limit")

print("=" * 60)
