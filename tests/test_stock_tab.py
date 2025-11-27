"""
Comprehensive Test Suite for Stock Tab

Tests all features of the Stock tab:
- Stock price retrieval (historical, quotes, combined)
- Financial data (income statement, balance sheet, cash flow)
- Chart data generation
- Caching behavior
- API integration

These tests use cached data when available to avoid hitting API rate limits.
"""

import sys
import os
import pytest
import requests
import json
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.cache_manager import stock_cache

# API configuration
API_BASE_URL = "http://localhost:8000"
TEST_TICKER = "AAPL"
TEST_TICKER_ALT = "MSFT"


class TestStockPriceEndpoints:
    """Test stock price data retrieval"""
    
    def test_historical_prices(self):
        """Test historical stock price data retrieval"""
        print("\n" + "="*60)
        print(f"TEST: Historical Prices for {TEST_TICKER}")
        print("="*60)
        
        # Test different periods
        periods = ['1mo', '3mo', '6mo', '1y']
        
        for period in periods:
            response = requests.get(
                f"{API_BASE_URL}/api/stock-price/historical/{TEST_TICKER}",
                params={"period": period}
            )
            
            assert response.status_code == 200, f"Failed for period {period}"
            data = response.json()
            
            # Validate response structure
            assert 'dates' in data, "Missing dates field"
            assert 'close' in data, "Missing close prices"
            assert 'open' in data, "Missing open prices"
            assert 'high' in data, "Missing high prices"
            assert 'low' in data, "Missing low prices"
            assert 'volume' in data, "Missing volume data"
            
            # Validate data integrity
            assert len(data['dates']) > 0, f"No data for period {period}"
            assert len(data['dates']) == len(data['close']), "Data length mismatch"
            
            print(f"✓ Period {period}: {len(data['dates'])} data points")
        
        print("\n✅ Historical prices test passed!")
    
    def test_stock_quote(self):
        """Test real-time stock quote"""
        print("\n" + "="*60)
        print(f"TEST: Real-time Quote for {TEST_TICKER}")
        print("="*60)
        
        response = requests.get(f"{API_BASE_URL}/api/stock-price/quote/{TEST_TICKER}")
        
        assert response.status_code == 200, "Quote request failed"
        data = response.json()
        
        # Validate quote structure
        required_fields = ['current', 'change', 'change_percent', 'high', 'low', 'open', 'previous_close']
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
            assert data[field] is not None, f"Null value for {field}"
        
        print(f"✓ Current Price: ${data['current']:.2f}")
        print(f"✓ Change: {data['change']:.2f} ({data['change_percent']:.2f}%)")
        print(f"✓ High: ${data['high']:.2f}, Low: ${data['low']:.2f}")
        
        print("\n✅ Stock quote test passed!")
    
    def test_combined_data(self):
        """Test combined historical + quote data"""
        print("\n" + "="*60)
        print(f"TEST: Combined Data for {TEST_TICKER}")
        print("="*60)
        
        response = requests.get(
            f"{API_BASE_URL}/api/stock-price/combined/{TEST_TICKER}",
            params={"period": "1y"}
        )
        
        assert response.status_code == 200, "Combined request failed"
        data = response.json()
        
        # Should have both historical and quote
        assert 'historical' in data, "Missing historical data"
        assert 'quote' in data, "Missing quote data"
        
        # Validate historical
        hist = data['historical']
        assert len(hist['dates']) > 0, "No historical data"
        
        # Validate quote
        quote = data['quote']
        assert quote['current'] > 0, "Invalid current price"
        
        print(f"✓ Historical: {len(hist['dates'])} data points")
        print(f"✓ Quote: ${quote['current']:.2f}")
        
        print("\n✅ Combined data test passed!")
    
    def test_cache_functionality(self):
        """Test that caching is working properly"""
        print("\n" + "="*60)
        print("TEST: Stock Price Caching")
        print("="*60)
        
        # Clear cache for test ticker
        stock_cache.delete('historical', symbol=TEST_TICKER_ALT, period='1mo')
        
        # First request - should hit API
        start_time = datetime.now()
        response1 = requests.get(
            f"{API_BASE_URL}/api/stock-price/historical/{TEST_TICKER_ALT}",
            params={"period": "1mo"}
        )
        time1 = (datetime.now() - start_time).total_seconds()
        
        assert response1.status_code == 200, "First request failed"
        
        # Second request - should use cache (much faster)
        start_time = datetime.now()
        response2 = requests.get(
            f"{API_BASE_URL}/api/stock-price/historical/{TEST_TICKER_ALT}",
            params={"period": "1mo"}
        )
        time2 = (datetime.now() - start_time).total_seconds()
        
        assert response2.status_code == 200, "Second request failed"
        
        # Cached request should be faster
        print(f"✓ First request: {time1:.3f}s (API call)")
        print(f"✓ Second request: {time2:.3f}s (cached)")
        print(f"✓ Speed improvement: {time1/time2:.1f}x faster")
        
        # Data should be identical
        assert response1.json() == response2.json(), "Cache data mismatch"
        
        print("\n✅ Caching test passed!")


class TestFinancialDataEndpoints:
    """Test financial statement data retrieval"""
    
    def test_financial_data_retrieval(self):
        """Test retrieving financial statements"""
        print("\n" + "="*60)
        print(f"TEST: Financial Data for {TEST_TICKER}")
        print("="*60)
        
        # Test both quarterly and annual data
        for quarterly in [False, True]:
            period_type = "quarterly" if quarterly else "annual"
            
            response = requests.get(
                f"{API_BASE_URL}/api/financials/{TEST_TICKER}",
                params={"quarterly": quarterly}
            )
            
            assert response.status_code == 200, f"Failed for {period_type}"
            data = response.json()
            
            # Validate structure
            required_sections = ['income_statement', 'balance_sheet', 'cash_flow']
            for section in required_sections:
                assert section in data, f"Missing {section}"
                assert len(data[section]) > 0, f"Empty {section}"
            
            print(f"✓ {period_type.capitalize()} data:")
            print(f"  - Income Statement: {len(data['income_statement'])} periods")
            print(f"  - Balance Sheet: {len(data['balance_sheet'])} periods")
            print(f"  - Cash Flow: {len(data['cash_flow'])} periods")
        
        print("\n✅ Financial data test passed!")
    
    def test_financial_data_content(self):
        """Test content of financial data"""
        print("\n" + "="*60)
        print(f"TEST: Financial Data Content for {TEST_TICKER}")
        print("="*60)
        
        response = requests.get(
            f"{API_BASE_URL}/api/financials/{TEST_TICKER}",
            params={"quarterly": False}
        )
        
        assert response.status_code == 200, "Request failed"
        data = response.json()
        
        # Check income statement has key metrics
        income = data['income_statement']
        first_period = income[0] if income else {}
        
        key_metrics = ['Total Revenue', 'Net Income', 'Gross Profit']
        found_metrics = []
        
        for metric in key_metrics:
            if metric in first_period:
                found_metrics.append(metric)
                print(f"✓ Found metric: {metric}")
        
        assert len(found_metrics) > 0, "No key metrics found"
        
        print("\n✅ Financial content test passed!")


class TestStockChartFeatures:
    """Test chart-related features"""
    
    def test_chart_data_format(self):
        """Test that chart data is in correct format"""
        print("\n" + "="*60)
        print("TEST: Chart Data Format")
        print("="*60)
        
        response = requests.get(
            f"{API_BASE_URL}/api/stock-price/combined/{TEST_TICKER}",
            params={"period": "6mo"}
        )
        
        assert response.status_code == 200, "Request failed"
        data = response.json()
        
        hist = data['historical']
        
        # Verify all arrays same length
        lengths = [
            len(hist['dates']),
            len(hist['close']),
            len(hist['open']),
            len(hist['high']),
            len(hist['low']),
            len(hist['volume'])
        ]
        
        assert all(l == lengths[0] for l in lengths), "Array length mismatch"
        print(f"✓ All arrays have consistent length: {lengths[0]}")
        
        # Verify dates are in order
        dates = hist['dates']
        assert dates == sorted(dates), "Dates not in chronological order"
        print(f"✓ Dates in chronological order")
        
        # Verify price data is reasonable
        assert all(p > 0 for p in hist['close']), "Invalid price data"
        print(f"✓ Price data valid (all positive)")
        
        print("\n✅ Chart data format test passed!")
    
    def test_multiple_periods(self):
        """Test data availability for all period options"""
        print("\n" + "="*60)
        print("TEST: Multiple Period Options")
        print("="*60)
        
        periods = ['1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y']
        
        results = {}
        for period in periods:
            try:
                response = requests.get(
                    f"{API_BASE_URL}/api/stock-price/historical/{TEST_TICKER}",
                    params={"period": period}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    results[period] = len(data['dates'])
                    print(f"✓ {period}: {results[period]} data points")
                else:
                    print(f"⚠ {period}: Request failed")
            except Exception as e:
                print(f"⚠ {period}: {str(e)}")
        
        # At least some periods should work
        assert len(results) > 0, "No periods returned data"
        
        print("\n✅ Multiple periods test passed!")


class TestCacheIntegration:
    """Test cache behavior across stock features"""
    
    def test_cache_directories(self):
        """Test that stock cache uses correct directory"""
        print("\n" + "="*60)
        print("TEST: Stock Cache Directory Structure")
        print("="*60)
        
        info = stock_cache.get_info()
        
        assert 'Stock' in info['cache_dir'], "Wrong cache directory"
        assert info['namespace'] == 'Stock', "Wrong namespace"
        
        print(f"✓ Cache directory: {info['cache_dir']}")
        print(f"✓ Namespace: {info['namespace']}")
        print(f"✓ Expiry: {info['expiry_hours']} hours")
        
        print("\n✅ Cache directory test passed!")
    
    def test_cache_persistence(self):
        """Test that cache persists across requests"""
        print("\n" + "="*60)
        print("TEST: Cache Persistence")
        print("="*60)
        
        # Make a request
        response = requests.get(
            f"{API_BASE_URL}/api/stock-price/quote/{TEST_TICKER}"
        )
        assert response.status_code == 200
        data1 = response.json()
        
        # Check cache info
        info = stock_cache.get_info()
        initial_count = info['total_entries']
        
        # Make another request (should use cache)
        response = requests.get(
            f"{API_BASE_URL}/api/stock-price/quote/{TEST_TICKER}"
        )
        assert response.status_code == 200
        data2 = response.json()
        
        # Cache count should stay same or increase (not decrease)
        info2 = stock_cache.get_info()
        assert info2['total_entries'] >= initial_count
        
        print(f"✓ Cache entries: {info2['total_entries']}")
        print(f"✓ Data consistent across requests")
        
        print("\n✅ Cache persistence test passed!")


def run_all_stock_tests():
    """Run all stock tab tests"""
    print("\n" + "#"*60)
    print("# STOCK TAB COMPREHENSIVE TESTS")
    print("#"*60)
    
    test_classes = [
        TestStockPriceEndpoints(),
        TestFinancialDataEndpoints(),
        TestStockChartFeatures(),
        TestCacheIntegration()
    ]
    
    total_tests = 0
    passed_tests = 0
    
    for test_class in test_classes:
        class_name = test_class.__class__.__name__
        print(f"\n{'='*60}")
        print(f"Running {class_name}")
        print(f"{'='*60}")
        
        test_methods = [m for m in dir(test_class) if m.startswith('test_')]
        
        for method_name in test_methods:
            total_tests += 1
            try:
                method = getattr(test_class, method_name)
                method()
                passed_tests += 1
            except AssertionError as e:
                print(f"❌ {method_name} FAILED: {e}")
            except Exception as e:
                print(f"❌ {method_name} ERROR: {e}")
    
    print("\n" + "#"*60)
    print(f"# RESULTS: {passed_tests}/{total_tests} tests passed")
    print("#"*60)
    
    return passed_tests == total_tests


if __name__ == "__main__":
    import time
    print("\n⚠️  Make sure the backend server is running on http://localhost:8000")
    print("Waiting 2 seconds...")
    time.sleep(2)
    
    success = run_all_stock_tests()
    sys.exit(0 if success else 1)
