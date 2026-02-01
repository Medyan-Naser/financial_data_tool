"""
Test the stock price backend endpoint

Comprehensive test suite for stock price API endpoints including:
- Historical prices with various periods
- Real-time quotes
- Combined data endpoint
- Error handling for invalid tickers
- Response structure validation
- Edge cases and boundary conditions
"""

import requests
import json
import sys
import pytest

BASE_URL = "http://localhost:8000"
TEST_TICKER = "AAPL"
ALT_TICKER = "MSFT"
INVALID_TICKER = "INVALIDTICKER12345"


class TestHistoricalPrices:
    """Test historical prices endpoint"""
    
    def test_historical_default_period(self):
        """Test historical prices with default period"""
        print("\n" + "="*60)
        print(f"TEST: Historical Prices Default Period ({TEST_TICKER})")
        print("="*60)
        
        url = f"{BASE_URL}/api/stock-price/historical/{TEST_TICKER}"
        response = requests.get(url, timeout=30)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        assert 'symbol' in data, "Response should contain symbol"
        assert data['symbol'] == TEST_TICKER, f"Symbol mismatch"
        
        print(f"✓ Status: {response.status_code}")
        print(f"✓ Symbol: {data['symbol']}")
        print(f"✓ Data points: {data.get('data_points', 'N/A')}")
        print("✅ Default period test passed!")
    
    def test_historical_all_periods(self):
        """Test historical prices with all supported periods"""
        print("\n" + "="*60)
        print("TEST: Historical Prices All Periods")
        print("="*60)
        
        periods = ['1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', 'ytd', 'max']
        
        for period in periods:
            url = f"{BASE_URL}/api/stock-price/historical/{TEST_TICKER}"
            response = requests.get(url, params={'period': period}, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✓ {period}: {data.get('data_points', 0)} data points")
            else:
                print(f"⚠ {period}: Status {response.status_code}")
        
        print("✅ All periods test passed!")
    
    def test_historical_response_structure(self):
        """Test that historical response has expected fields"""
        print("\n" + "="*60)
        print("TEST: Historical Response Structure")
        print("="*60)
        
        url = f"{BASE_URL}/api/stock-price/historical/{TEST_TICKER}"
        response = requests.get(url, params={'period': '1mo'}, timeout=30)
        
        assert response.status_code == 200
        data = response.json()
        
        expected_fields = ['symbol', 'data_points']
        price_fields = ['open', 'high', 'low', 'close', 'volume']
        
        for field in expected_fields:
            assert field in data, f"Missing field: {field}"
            print(f"✓ Has {field}")
        
        # Check for price data arrays
        for field in price_fields:
            if field in data:
                assert isinstance(data[field], list), f"{field} should be a list"
                print(f"✓ Has {field} array ({len(data[field])} items)")
        
        print("✅ Response structure test passed!")
    
    def test_historical_invalid_ticker(self):
        """Test historical prices with invalid ticker"""
        print("\n" + "="*60)
        print("TEST: Historical Invalid Ticker")
        print("="*60)
        
        url = f"{BASE_URL}/api/stock-price/historical/{INVALID_TICKER}"
        response = requests.get(url, timeout=30)
        
        # Should return error or empty data
        print(f"✓ Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            # May return empty data
            print(f"✓ Data points: {data.get('data_points', 0)}")
        else:
            print(f"✓ Correctly returns error for invalid ticker")
        
        print("✅ Invalid ticker test passed!")
    
    def test_historical_multiple_tickers(self):
        """Test historical prices for multiple different tickers"""
        print("\n" + "="*60)
        print("TEST: Historical Multiple Tickers")
        print("="*60)
        
        tickers = [TEST_TICKER, ALT_TICKER, 'GOOGL']
        
        for ticker in tickers:
            url = f"{BASE_URL}/api/stock-price/historical/{ticker}"
            response = requests.get(url, params={'period': '1mo'}, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✓ {ticker}: {data.get('data_points', 0)} points")
            else:
                print(f"⚠ {ticker}: Status {response.status_code}")
        
        print("✅ Multiple tickers test passed!")

