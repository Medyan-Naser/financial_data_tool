"""
Test if the cache is working properly for stock price data
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.api_cache import api_cache

# Test cache operations
print("=" * 60)
print("TESTING STOCK PRICE CACHE")
print("=" * 60)

# Test 1: Check if cache directory exists
print(f"\n1. Cache directory: {api_cache.cache_dir}")
print(f"   Exists: {api_cache.cache_dir.exists()}")

# Test 2: Get cache info
info = api_cache.get_cache_info()
print(f"\n2. Cache Info:")
print(f"   Total entries: {info['total_entries']}")
print(f"   Total size: {info.get('total_size_mb', 0):.2f} MB")
print(f"   Expiry hours: {info['expiry_hours']}")

# Test 3: Try to get stock price from cache
print(f"\n3. Testing cache for AAPL (1y period):")
cached_data = api_cache.get('stock_price', symbol='AAPL', period='1y')
if cached_data:
    print(f"   ✓ Found in cache!")
    print(f"   Data points: {cached_data.get('historical', {}).get('data_points', 'N/A')}")
else:
    print(f"   ✗ Not in cache (this is normal if you just started)")

# Test 4: List all cache files
import glob
cache_files = list(api_cache.cache_dir.glob("*.pkl"))
print(f"\n4. Cache Files ({len(cache_files)} total):")
for f in cache_files[:5]:  # Show first 5
    size_mb = f.stat().st_size / (1024 * 1024)
    print(f"   - {f.name} ({size_mb:.2f} MB)")
if len(cache_files) > 5:
    print(f"   ... and {len(cache_files) - 5} more")

# Test 5: Check quote cache
print(f"\n5. Testing quote cache for AAPL:")
quote_cached = api_cache.get('stock_quote', symbol='AAPL')
if quote_cached:
    print(f"   ✓ Found in cache!")
    print(f"   Current price: ${quote_cached.get('current', 'N/A')}")
else:
    print(f"   ✗ Not in cache")

print("\n" + "=" * 60)
print("RECOMMENDATIONS:")
print("=" * 60)

if info['total_entries'] == 0:
    print("⚠️  Cache is empty!")
    print("   This means:")
    print("   - First request will hit the API (and might get rate limited)")
    print("   - Subsequent requests should use cache")
    print("   - Wait a moment and try searching again")
elif cached_data or quote_cached:
    print("✓ Cache is working!")
    print("  Your next request should be instant and won't hit the API.")
else:
    print("⚠️  Cache exists but doesn't have AAPL data")
    print("   Try searching for AAPL, then run this test again.")

print("\n" + "=" * 60)
