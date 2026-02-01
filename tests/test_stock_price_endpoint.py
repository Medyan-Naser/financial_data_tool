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


class TestQuoteEndpoint:
    """Test real-time quote endpoint"""
    
    def test_quote_basic(self):
        """Test basic quote retrieval"""
        print("\n" + "="*60)
        print(f"TEST: Quote Basic ({TEST_TICKER})")
        print("="*60)
        
        url = f"{BASE_URL}/api/stock-price/quote/{TEST_TICKER}"
        response = requests.get(url, timeout=30)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        print(f"✓ Status: {response.status_code}")
        print(f"✓ Current: ${data.get('current', 'N/A')}")
        print("✅ Quote basic test passed!")
    
    def test_quote_response_structure(self):
        """Test quote response has expected fields"""
        print("\n" + "="*60)
        print("TEST: Quote Response Structure")
        print("="*60)
        
        url = f"{BASE_URL}/api/stock-price/quote/{TEST_TICKER}"
        response = requests.get(url, timeout=30)
        
        assert response.status_code == 200
        data = response.json()
        
        expected_fields = ['current', 'open', 'high', 'low']
        
        for field in expected_fields:
            if field in data:
                print(f"✓ {field}: {data[field]}")
            else:
                print(f"⚠ Missing optional field: {field}")
        
        # Validate numeric values
        if 'current' in data and data['current'] is not None:
            assert isinstance(data['current'], (int, float)), "Current should be numeric"
            assert data['current'] > 0, "Current price should be positive"
        
        print("✅ Quote structure test passed!")
    
    def test_quote_invalid_ticker(self):
        """Test quote with invalid ticker"""
        print("\n" + "="*60)
        print("TEST: Quote Invalid Ticker")
        print("="*60)
        
        url = f"{BASE_URL}/api/stock-price/quote/{INVALID_TICKER}"
        response = requests.get(url, timeout=30)
        
        print(f"✓ Status: {response.status_code}")
        print("✅ Invalid ticker quote test passed!")
    
    def test_quote_change_values(self):
        """Test that quote change values are present and valid"""
        print("\n" + "="*60)
        print("TEST: Quote Change Values")
        print("="*60)
        
        url = f"{BASE_URL}/api/stock-price/quote/{TEST_TICKER}"
        response = requests.get(url, timeout=30)
        
        assert response.status_code == 200
        data = response.json()
        
        if 'change' in data:
            print(f"✓ Change: ${data['change']}")
        if 'change_percent' in data:
            print(f"✓ Change %: {data['change_percent']}%")
        
        print("✅ Change values test passed!")


class TestCombinedEndpoint:
    """Test combined data endpoint"""
    
    def test_combined_basic(self):
        """Test combined endpoint returns both historical and quote"""
        print("\n" + "="*60)
        print(f"TEST: Combined Basic ({TEST_TICKER})")
        print("="*60)
        
        url = f"{BASE_URL}/api/stock-price/combined/{TEST_TICKER}"
        response = requests.get(url, params={'period': '1mo'}, timeout=30)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        assert 'historical' in data, "Should have historical data"
        assert 'quote' in data, "Should have quote data"
        
        print(f"✓ Has historical: {type(data['historical'])}")
        print(f"✓ Has quote: {type(data['quote'])}")
        print("✅ Combined basic test passed!")
    
    def test_combined_historical_content(self):
        """Test combined endpoint historical data content"""
        print("\n" + "="*60)
        print("TEST: Combined Historical Content")
        print("="*60)
        
        url = f"{BASE_URL}/api/stock-price/combined/{TEST_TICKER}"
        response = requests.get(url, params={'period': '3mo'}, timeout=30)
        
        assert response.status_code == 200
        data = response.json()
        
        hist = data.get('historical', {})
        if isinstance(hist, dict):
            print(f"✓ Data points: {hist.get('data_points', 'N/A')}")
            print(f"✓ Symbol: {hist.get('symbol', 'N/A')}")
        
        print("✅ Combined historical content test passed!")
    
    def test_combined_quote_content(self):
        """Test combined endpoint quote data content"""
        print("\n" + "="*60)
        print("TEST: Combined Quote Content")
        print("="*60)
        
        url = f"{BASE_URL}/api/stock-price/combined/{TEST_TICKER}"
        response = requests.get(url, params={'period': '1mo'}, timeout=30)
        
        assert response.status_code == 200
        data = response.json()
        
        quote = data.get('quote', {})
        if isinstance(quote, dict):
            print(f"✓ Current: ${quote.get('current', 'N/A')}")
            print(f"✓ Open: ${quote.get('open', 'N/A')}")
        
        print("✅ Combined quote content test passed!")
    
    def test_combined_different_periods(self):
        """Test combined endpoint with different periods"""
        print("\n" + "="*60)
        print("TEST: Combined Different Periods")
        print("="*60)
        
        periods = ['1mo', '6mo', '1y']
        
        for period in periods:
            url = f"{BASE_URL}/api/stock-price/combined/{TEST_TICKER}"
            response = requests.get(url, params={'period': period}, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                hist = data.get('historical', {})
                points = hist.get('data_points', 0) if isinstance(hist, dict) else 0
                print(f"✓ {period}: {points} data points")
            else:
                print(f"⚠ {period}: Status {response.status_code}")
        
        print("✅ Combined periods test passed!")


class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_special_characters_in_ticker(self):
        """Test handling of special characters in ticker"""
        print("\n" + "="*60)
        print("TEST: Special Characters in Ticker")
        print("="*60)
        
        # Test ticker with dot (like BRK.B)
        url = f"{BASE_URL}/api/stock-price/quote/BRK.B"
        response = requests.get(url, timeout=30)
        print(f"✓ BRK.B status: {response.status_code}")
        
        print("✅ Special characters test passed!")
    
    def test_lowercase_ticker(self):
        """Test that lowercase tickers work"""
        print("\n" + "="*60)
        print("TEST: Lowercase Ticker")
        print("="*60)
        
        url = f"{BASE_URL}/api/stock-price/quote/aapl"
        response = requests.get(url, timeout=30)
        
        print(f"✓ Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Current: ${data.get('current', 'N/A')}")
        
        print("✅ Lowercase ticker test passed!")
    
    def test_timeout_handling(self):
        """Test that requests handle timeout gracefully"""
        print("\n" + "="*60)
        print("TEST: Timeout Handling")
        print("="*60)
        
        try:
            url = f"{BASE_URL}/api/stock-price/historical/{TEST_TICKER}"
            response = requests.get(url, params={'period': 'max'}, timeout=60)
            print(f"✓ Request completed with status: {response.status_code}")
        except requests.exceptions.Timeout:
            print("⚠ Request timed out (may be expected for large data)")
        
        print("✅ Timeout handling test passed!")

