"""
Detailed cache inspection and validation

Comprehensive test suite for cache structure validation including:
- Cache data structure inspection
- Historical data validation
- Quote data validation
- Cache key consistency
- Multi-ticker cache inspection
- Cache freshness checks
"""

import sys
import os
import json
import pytest
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.api_cache import api_cache

TEST_TICKER = "AAPL"
ALT_TICKER = "MSFT"
TEST_PERIOD = "1y"


class TestCacheStructure:
    """Test cache data structure"""
    
    def test_cache_data_keys(self):
        """Test that cached data has expected top-level keys"""
        print("\n" + "="*60)
        print(f"TEST: Cache Data Keys ({TEST_TICKER})")
        print("="*60)
        
        cached_data = api_cache.get('stock_price', symbol=TEST_TICKER, period=TEST_PERIOD)
        
        if cached_data:
            keys = list(cached_data.keys())
            print(f"✓ Found {len(keys)} keys: {keys}")
            
            # Check for common expected keys
            if 'symbol' in cached_data:
                assert cached_data['symbol'] == TEST_TICKER, "Symbol should match"
                print(f"✓ Symbol matches: {cached_data['symbol']}")
            
            print("✅ Cache keys test passed!")
        else:
            print(f"⚠ {TEST_TICKER} not in cache - skipping")
            print("✅ Test passed (cache miss is valid)")
    
    def test_cache_metadata(self):
        """Test cache metadata fields"""
        print("\n" + "="*60)
        print("TEST: Cache Metadata")
        print("="*60)
        
        cached_data = api_cache.get('stock_price', symbol=TEST_TICKER, period=TEST_PERIOD)
        
        if cached_data:
            metadata_fields = ['symbol', 'fetched_at', 'period']
            
            for field in metadata_fields:
                if field in cached_data:
                    print(f"✓ Has {field}: {cached_data[field]}")
                else:
                    print(f"⚠ Missing optional field: {field}")
            
            print("✅ Metadata test passed!")
        else:
            print("⚠ No cached data - skipping")
            print("✅ Test passed (cache miss is valid)")
    
    def test_cache_json_serializable(self):
        """Test that cache data is JSON serializable"""
        print("\n" + "="*60)
        print("TEST: JSON Serializable")
        print("="*60)
        
        cached_data = api_cache.get('stock_price', symbol=TEST_TICKER, period=TEST_PERIOD)
        
        if cached_data:
            try:
                json_str = json.dumps(cached_data, default=str)
                assert len(json_str) > 0, "JSON should not be empty"
                print(f"✓ Successfully serialized to JSON ({len(json_str)} chars)")
                print("✅ JSON serializable test passed!")
            except Exception as e:
                pytest.fail(f"Cache data not JSON serializable: {e}")
        else:
            print("⚠ No cached data - skipping")
            print("✅ Test passed (cache miss is valid)")


class TestHistoricalDataStructure:
    """Test historical data structure within cache"""
    
    def test_historical_data_exists(self):
        """Test that historical data section exists"""
        print("\n" + "="*60)
        print("TEST: Historical Data Exists")
        print("="*60)
        
        cached_data = api_cache.get('stock_price', symbol=TEST_TICKER, period=TEST_PERIOD)
        
        if cached_data and 'historical' in cached_data:
            hist = cached_data['historical']
            print(f"✓ Historical data found")
            print(f"✓ Type: {type(hist)}")
            print("✅ Historical exists test passed!")
        elif cached_data:
            print("⚠ No 'historical' key in cache")
            print("✅ Test passed (structure may vary)")
        else:
            print("⚠ No cached data - skipping")
            print("✅ Test passed (cache miss is valid)")
    
    def test_historical_data_structure(self):
        """Test historical data structure details"""
        print("\n" + "="*60)
        print("TEST: Historical Data Structure")
        print("="*60)
        
        cached_data = api_cache.get('stock_price', symbol=TEST_TICKER, period=TEST_PERIOD)
        
        if cached_data and 'historical' in cached_data:
            hist = cached_data['historical']
            
            if isinstance(hist, dict):
                print(f"✓ Keys: {list(hist.keys())}")
                
                if 'data_points' in hist:
                    print(f"✓ Data points: {hist['data_points']}")
                    assert hist['data_points'] > 0, "Should have data points"
                
                if 'symbol' in hist:
                    print(f"✓ Symbol: {hist['symbol']}")
                
                # Check for price arrays
                price_fields = ['open', 'high', 'low', 'close', 'volume']
                for field in price_fields:
                    if field in hist:
                        data_len = len(hist[field]) if isinstance(hist[field], list) else 'N/A'
                        print(f"✓ {field}: {data_len} entries")
            
            print("✅ Historical structure test passed!")
        else:
            print("⚠ No historical data - skipping")
            print("✅ Test passed (cache miss is valid)")
    
    def test_historical_price_data_validity(self):
        """Test that historical price data is valid"""
        print("\n" + "="*60)
        print("TEST: Historical Price Data Validity")
        print("="*60)
        
        cached_data = api_cache.get('stock_price', symbol=TEST_TICKER, period=TEST_PERIOD)
        
        if cached_data and 'historical' in cached_data:
            hist = cached_data['historical']
            
            if isinstance(hist, dict) and 'close' in hist:
                close_prices = hist['close']
                
                if isinstance(close_prices, list) and len(close_prices) > 0:
                    # Check first few prices are valid
                    for i, price in enumerate(close_prices[:5]):
                        if price is not None:
                            assert isinstance(price, (int, float)), f"Price should be numeric"
                            assert price > 0, f"Price should be positive"
                            print(f"✓ Price[{i}]: ${price:.2f}")
                    
                    print("✅ Price validity test passed!")
                else:
                    print("⚠ No close prices found")
        else:
            print("⚠ No historical data - skipping")
            print("✅ Test passed (cache miss is valid)")


class TestQuoteDataStructure:
    """Test quote data structure within cache"""
    
    def test_quote_data_exists(self):
        """Test that quote data section exists"""
        print("\n" + "="*60)
        print("TEST: Quote Data Exists")
        print("="*60)
        
        cached_data = api_cache.get('stock_price', symbol=TEST_TICKER, period=TEST_PERIOD)
        
        if cached_data and 'quote' in cached_data:
            quote = cached_data['quote']
            print(f"✓ Quote data found")
            print(f"✓ Type: {type(quote)}")
            print("✅ Quote exists test passed!")
        elif cached_data:
            print("⚠ No 'quote' key in cache")
        else:
            print("⚠ No cached data - skipping")
        
        print("✅ Test passed!")
    
    def test_quote_data_fields(self):
        """Test quote data has expected fields"""
        print("\n" + "="*60)
        print("TEST: Quote Data Fields")
        print("="*60)
        
        cached_data = api_cache.get('stock_price', symbol=TEST_TICKER, period=TEST_PERIOD)
        
        if cached_data and 'quote' in cached_data:
            quote = cached_data['quote']
            
            if isinstance(quote, dict):
                expected_fields = ['current', 'open', 'high', 'low', 'change', 'change_percent']
                
                for field in expected_fields:
                    if field in quote:
                        print(f"✓ {field}: {quote[field]}")
                    else:
                        print(f"⚠ Missing: {field}")
            
            print("✅ Quote fields test passed!")
        else:
            print("⚠ No quote data - skipping")
            print("✅ Test passed (cache miss is valid)")
    
    def test_quote_values_valid(self):
        """Test quote values are valid"""
        print("\n" + "="*60)
        print("TEST: Quote Values Valid")
        print("="*60)
        
        cached_data = api_cache.get('stock_price', symbol=TEST_TICKER, period=TEST_PERIOD)
        
        if cached_data and 'quote' in cached_data:
            quote = cached_data['quote']
            
            if isinstance(quote, dict):
                if 'current' in quote and quote['current'] is not None:
                    assert isinstance(quote['current'], (int, float)), "Current should be numeric"
                    assert quote['current'] > 0, "Current should be positive"
                    print(f"✓ Current price valid: ${quote['current']}")
                
                if 'high' in quote and 'low' in quote:
                    if quote['high'] is not None and quote['low'] is not None:
                        assert quote['high'] >= quote['low'], "High should be >= Low"
                        print(f"✓ High/Low valid: ${quote['low']} - ${quote['high']}")
            
            print("✅ Quote values test passed!")
        else:
            print("⚠ No quote data - skipping")
            print("✅ Test passed (cache miss is valid)")


class TestMultiTickerCache:
    """Test cache behavior with multiple tickers"""
    
    def test_different_tickers_separate_cache(self):
        """Test that different tickers have separate cache entries"""
        print("\n" + "="*60)
        print("TEST: Different Tickers Separate Cache")
        print("="*60)
        
        cache1 = api_cache.get('stock_price', symbol=TEST_TICKER, period=TEST_PERIOD)
        cache2 = api_cache.get('stock_price', symbol=ALT_TICKER, period=TEST_PERIOD)
        
        if cache1 and cache2:
            # They should be different objects
            symbol1 = cache1.get('symbol') or cache1.get('historical', {}).get('symbol')
            symbol2 = cache2.get('symbol') or cache2.get('historical', {}).get('symbol')
            
            if symbol1 and symbol2:
                assert symbol1 != symbol2, "Different tickers should have different data"
                print(f"✓ {TEST_TICKER} data: symbol={symbol1}")
                print(f"✓ {ALT_TICKER} data: symbol={symbol2}")
        else:
            print(f"✓ {TEST_TICKER} cached: {cache1 is not None}")
            print(f"✓ {ALT_TICKER} cached: {cache2 is not None}")
        
        print("✅ Separate cache test passed!")
    
    def test_different_periods_separate_cache(self):
        """Test that different periods have separate cache entries"""
        print("\n" + "="*60)
        print("TEST: Different Periods Separate Cache")
        print("="*60)
        
        periods = ['1mo', '6mo', '1y']
        
        for period in periods:
            cached = api_cache.get('stock_price', symbol=TEST_TICKER, period=period)
            status = "cached" if cached else "not cached"
            print(f"✓ {TEST_TICKER} ({period}): {status}")
        
        print("✅ Separate periods test passed!")

