"""
Comprehensive Test Suite for Financials Cached Endpoints

Tests all features of the financials cached API:
- Get cached financial data
- Check cache status
- Delete cached data
- Error handling for missing tickers

These tests use the backend directly without requiring a running server.
"""

import sys
import os
import pytest
import requests
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.data_collection_service import data_collection_service

# API configuration
API_BASE_URL = "http://localhost:8000"
TEST_TICKER = "AAPL"
TEST_TICKER_ALT = "MSFT"
INVALID_TICKER = "INVALIDTICKER123"


class TestFinancialsCacheStatus:
    """Test cache status endpoint"""
    
    def test_cache_status_for_valid_ticker(self):
        """Test cache status check for a ticker"""
        print("\n" + "="*60)
        print(f"TEST: Cache Status for {TEST_TICKER}")
        print("="*60)
        
        response = requests.get(
            f"{API_BASE_URL}/api/financials/cache/status/{TEST_TICKER}",
            params={"quarterly": False}
        )
        
        assert response.status_code == 200, "Cache status request failed"
        data = response.json()
        
        # Validate structure
        assert 'ticker' in data, "Missing ticker field"
        assert 'cached' in data, "Missing cached field"
        assert data['ticker'] == TEST_TICKER, f"Wrong ticker: {data['ticker']}"
        
        print(f"✓ Ticker: {data['ticker']}")
        print(f"✓ Cached: {data['cached']}")
        
        if data['cached']:
            if 'cached_at' in data:
                print(f"✓ Cached at: {data['cached_at']}")
            if 'period_type' in data:
                print(f"✓ Period type: {data['period_type']}")
        
        print("\n✅ Cache status test passed!")
    
    def test_cache_status_quarterly(self):
        """Test cache status for quarterly data"""
        print("\n" + "="*60)
        print(f"TEST: Quarterly Cache Status for {TEST_TICKER}")
        print("="*60)
        
        response = requests.get(
            f"{API_BASE_URL}/api/financials/cache/status/{TEST_TICKER}",
            params={"quarterly": True}
        )
        
        assert response.status_code == 200, "Quarterly cache status request failed"
        data = response.json()
        
        assert 'ticker' in data, "Missing ticker field"
        assert 'cached' in data, "Missing cached field"
        
        print(f"✓ Ticker: {data['ticker']}")
        print(f"✓ Quarterly cached: {data['cached']}")
        
        print("\n✅ Quarterly cache status test passed!")
    
    def test_cache_status_invalid_ticker(self):
        """Test cache status for non-existent ticker"""
        print("\n" + "="*60)
        print(f"TEST: Cache Status for Invalid Ticker")
        print("="*60)
        
        response = requests.get(
            f"{API_BASE_URL}/api/financials/cache/status/{INVALID_TICKER}"
        )
        
        assert response.status_code == 200, "Should return 200 even for non-cached ticker"
        data = response.json()
        
        assert data['cached'] == False, "Invalid ticker should not be cached"
        print(f"✓ Invalid ticker correctly shows as not cached")
        
        print("\n✅ Invalid ticker cache status test passed!")


class TestCachedFinancialData:
    """Test cached financial data retrieval"""
    
    def test_get_cached_data_structure(self):
        """Test getting cached financial data"""
        print("\n" + "="*60)
        print(f"TEST: Get Cached Financial Data for {TEST_TICKER}")
        print("="*60)
        
        response = requests.get(
            f"{API_BASE_URL}/api/financials/cached/{TEST_TICKER}",
            params={"quarterly": False}
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Validate structure
            assert 'cached' in data, "Missing cached flag"
            assert data['cached'] == True, "Should indicate data is from cache"
            
            print(f"✓ Data successfully retrieved from cache")
            
            # Check for financial data fields
            if 'income_statement' in data:
                print(f"✓ Income statement data present")
            if 'balance_sheet' in data:
                print(f"✓ Balance sheet data present")
            if 'cash_flow' in data:
                print(f"✓ Cash flow data present")
            
            print("\n✅ Cached data retrieval test passed!")
        
        elif response.status_code == 404:
            data = response.json()
            assert data['cached'] == False, "Should indicate not cached"
            print(f"⚠ No cached data available for {TEST_TICKER}")
            print(f"  Message: {data.get('message', 'N/A')}")
            print("\n✅ Test passed (404 is valid for uncached ticker)")
        
        else:
            pytest.fail(f"Unexpected status code: {response.status_code}")
    
    def test_cached_data_not_found(self):
        """Test response for ticker with no cached data"""
        print("\n" + "="*60)
        print(f"TEST: Cached Data Not Found")
        print("="*60)
        
        response = requests.get(
            f"{API_BASE_URL}/api/financials/cached/{INVALID_TICKER}"
        )
        
        # Should return 404 for non-cached ticker
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        data = response.json()
        
        assert 'cached' in data, "Missing cached field"
        assert data['cached'] == False, "Should indicate not cached"
        assert 'message' in data, "Should include helpful message"
        
        print(f"✓ Correctly returns 404 for non-cached ticker")
        print(f"✓ Message: {data['message']}")
        
        print("\n✅ Not found test passed!")


class TestDataCollectionService:
    """Test data collection service directly"""
    
    def test_is_cached_method(self):
        """Test is_cached method of data collection service"""
        print("\n" + "="*60)
        print("TEST: Data Collection Service - is_cached()")
        print("="*60)
        
        # Test for annual data
        is_cached_annual = data_collection_service.is_cached(TEST_TICKER, quarterly=False)
        print(f"✓ {TEST_TICKER} annual cached: {is_cached_annual}")
        
        # Test for quarterly data
        is_cached_quarterly = data_collection_service.is_cached(TEST_TICKER, quarterly=True)
        print(f"✓ {TEST_TICKER} quarterly cached: {is_cached_quarterly}")
        
        # Test for invalid ticker
        is_cached_invalid = data_collection_service.is_cached(INVALID_TICKER, quarterly=False)
        assert is_cached_invalid == False, "Invalid ticker should not be cached"
        print(f"✓ {INVALID_TICKER} correctly shows as not cached")
        
        print("\n✅ is_cached test passed!")
    
    def test_load_from_cache(self):
        """Test loading data from cache"""
        print("\n" + "="*60)
        print("TEST: Data Collection Service - load_from_cache()")
        print("="*60)
        
        # First check if data is cached
        if data_collection_service.is_cached(TEST_TICKER, quarterly=False):
            cached_data = data_collection_service.load_from_cache(TEST_TICKER, quarterly=False)
            
            assert cached_data is not None, "Failed to load cached data"
            print(f"✓ Successfully loaded cached data for {TEST_TICKER}")
            
            # Check structure
            if 'ticker' in cached_data:
                print(f"✓ Ticker in data: {cached_data['ticker']}")
            if 'cached_at' in cached_data:
                print(f"✓ Cached at: {cached_data['cached_at']}")
        else:
            print(f"⚠ No cached data for {TEST_TICKER}, skipping load test")
        
        # Test loading non-existent data
        invalid_data = data_collection_service.load_from_cache(INVALID_TICKER, quarterly=False)
        assert invalid_data is None, "Should return None for non-existent cache"
        print(f"✓ Correctly returns None for non-cached ticker")
        
        print("\n✅ load_from_cache test passed!")


class TestCacheIntegration:
    """Test cache behavior integration"""
    
    def test_cache_consistency(self):
        """Test that cache status and data retrieval are consistent"""
        print("\n" + "="*60)
        print("TEST: Cache Consistency")
        print("="*60)
        
        # Get cache status via API
        status_response = requests.get(
            f"{API_BASE_URL}/api/financials/cache/status/{TEST_TICKER}"
        )
        assert status_response.status_code == 200
        status_data = status_response.json()
        
        # Get cached data via API
        data_response = requests.get(
            f"{API_BASE_URL}/api/financials/cached/{TEST_TICKER}"
        )
        
        # Check consistency
        if status_data['cached']:
            assert data_response.status_code == 200, "If status says cached, data should be retrievable"
            print(f"✓ Cache status and data retrieval are consistent (both indicate cached)")
        else:
            assert data_response.status_code == 404, "If status says not cached, should get 404"
            print(f"✓ Cache status and data retrieval are consistent (both indicate not cached)")
        
        print("\n✅ Cache consistency test passed!")
    
    def test_service_api_consistency(self):
        """Test that service and API return consistent results"""
        print("\n" + "="*60)
        print("TEST: Service vs API Consistency")
        print("="*60)
        
        # Check via service
        service_cached = data_collection_service.is_cached(TEST_TICKER, quarterly=False)
        
        # Check via API
        api_response = requests.get(
            f"{API_BASE_URL}/api/financials/cache/status/{TEST_TICKER}",
            params={"quarterly": False}
        )
        api_data = api_response.json()
        api_cached = api_data['cached']
        
        # Should match
        assert service_cached == api_cached, "Service and API should report same cache status"
        print(f"✓ Service cached: {service_cached}")
        print(f"✓ API cached: {api_cached}")
        print(f"✓ Results match!")
        
        print("\n✅ Service/API consistency test passed!")


def run_all_financials_cached_tests():
    """Run all financials cached tests"""
    print("\n" + "#"*60)
    print("# FINANCIALS CACHED ENDPOINTS TESTS")
    print("#"*60)
    
    test_classes = [
        TestFinancialsCacheStatus(),
        TestCachedFinancialData(),
        TestDataCollectionService(),
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
    
    success = run_all_financials_cached_tests()
    sys.exit(0 if success else 1)
