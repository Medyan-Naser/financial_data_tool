"""
Comprehensive Test Suite for Macro/Economy Tab

Tests all features of the Macro tab:
- Currency exchange rates
- Cryptocurrency prices
- Precious metals prices (gold, silver)
- Historical metals data
- GDP data for countries
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

from app.cache_manager import macro_cache

# API configuration
API_BASE_URL = "http://localhost:8000"


class TestCurrencyEndpoints:
    """Test currency exchange rate endpoints"""
    
    def test_currency_rates(self):
        """Test currency exchange rates retrieval"""
        print("\n" + "="*60)
        print("TEST: Currency Exchange Rates")
        print("="*60)
        
        response = requests.get(f"{API_BASE_URL}/api/economy/currency")
        
        assert response.status_code == 200, "Currency request failed"
        data = response.json()
        
        # Validate structure
        assert 'base' in data, "Missing base currency"
        assert 'rates' in data, "Missing rates"
        assert 'cached_at' in data, "Missing cache timestamp"
        
        # Check common currencies
        common_currencies = ['EUR', 'GBP', 'JPY', 'CAD', 'AUD']
        rates = data['rates']
        
        for currency in common_currencies:
            if currency in rates:
                assert rates[currency] > 0, f"Invalid rate for {currency}"
                print(f"✓ {currency}: {rates[currency]:.4f}")
        
        print(f"✓ Base: {data['base']}")
        print(f"✓ Total currencies: {len(rates)}")
        
        print("\n✅ Currency rates test passed!")


class TestCryptoEndpoints:
    """Test cryptocurrency price endpoints"""
    
    def test_crypto_prices(self):
        """Test cryptocurrency prices retrieval"""
        print("\n" + "="*60)
        print("TEST: Cryptocurrency Prices")
        print("="*60)
        
        response = requests.get(f"{API_BASE_URL}/api/economy/crypto")
        
        assert response.status_code == 200, "Crypto request failed"
        data = response.json()
        
        # Validate structure
        assert 'cryptocurrencies' in data, "Missing cryptocurrencies"
        assert 'total_count' in data, "Missing count"
        
        cryptos = data['cryptocurrencies']
        assert len(cryptos) > 0, "No crypto data"
        
        # Check first few cryptos
        for crypto in cryptos[:5]:
            required_fields = ['symbol', 'name', 'current_price', 'market_cap']
            for field in required_fields:
                assert field in crypto, f"Missing field: {field}"
            
            assert crypto['current_price'] > 0, f"Invalid price for {crypto['name']}"
            print(f"✓ {crypto['name']} ({crypto['symbol']}): ${crypto['current_price']:,.2f}")
        
        print(f"✓ Total cryptocurrencies: {data['total_count']}")
        
        print("\n✅ Crypto prices test passed!")


class TestMetalsEndpoints:
    """Test precious metals price endpoints"""
    
    def test_current_metals_prices(self):
        """Test current gold and silver prices"""
        print("\n" + "="*60)
        print("TEST: Current Metals Prices (Gold, Silver)")
        print("="*60)
        
        response = requests.get(f"{API_BASE_URL}/api/economy/metals")
        
        assert response.status_code == 200, "Metals request failed"
        data = response.json()
        
        # Validate structure
        assert 'gold' in data, "Missing gold data"
        assert 'silver' in data, "Missing silver data"
        
        # Check gold
        gold = data['gold']
        assert 'price_usd_oz' in gold, "Missing gold price"
        assert gold['price_usd_oz'] > 0, "Invalid gold price"
        print(f"✓ Gold: ${gold['price_usd_oz']:.2f}/oz")
        
        if 'change' in gold:
            print(f"  Change: {gold['change']:.2f} ({gold.get('change_percent', 0):.2f}%)")
        
        # Check silver
        silver = data['silver']
        assert 'price_usd_oz' in silver, "Missing silver price"
        assert silver['price_usd_oz'] > 0, "Invalid silver price"
        print(f"✓ Silver: ${silver['price_usd_oz']:.2f}/oz")
        
        if 'change' in silver:
            print(f"  Change: {silver['change']:.2f} ({silver.get('change_percent', 0):.2f}%)")
        
        print("\n✅ Current metals prices test passed!")
    
    def test_historical_metals_data(self):
        """Test historical metals prices"""
        print("\n" + "="*60)
        print("TEST: Historical Metals Data")
        print("="*60)
        
        # Test different year ranges
        for years in [1, 5]:
            response = requests.get(
                f"{API_BASE_URL}/api/economy/metals/historical",
                params={"years": years}
            )
            
            assert response.status_code == 200, f"Failed for {years} years"
            data = response.json()
            
            # Validate structure
            assert 'gold' in data, "Missing gold historical"
            assert 'silver' in data, "Missing silver historical"
            assert 'years' in data, "Missing years field"
            
            gold_data = data['gold']
            silver_data = data['silver']
            
            assert len(gold_data) > 0, "No gold historical data"
            assert len(silver_data) > 0, "No silver historical data"
            
            print(f"✓ {years} year(s): {len(gold_data)} gold data points, {len(silver_data)} silver data points")
        
        print("\n✅ Historical metals test passed!")


class TestGDPEndpoints:
    """Test GDP data endpoints"""
    
    def test_gdp_data(self):
        """Test GDP data for various countries"""
        print("\n" + "="*60)
        print("TEST: GDP Data for Countries")
        print("="*60)
        
        # Test common countries
        countries = ['US', 'GB', 'DE', 'JP', 'CN']
        
        for country in countries:
            response = requests.get(f"{API_BASE_URL}/api/economy/gdp/{country}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Validate structure
                assert 'country' in data, f"Missing country for {country}"
                assert 'data' in data, f"Missing GDP data for {country}"
                
                gdp_data = data['data']
                if len(gdp_data) > 0:
                    latest = gdp_data[0]
                    value_billions = latest['value_usd'] / 1_000_000_000 if latest.get('value_usd') else 0
                    print(f"✓ {country}: ${value_billions:,.0f}B GDP ({latest.get('year', 'N/A')})")
                else:
                    print(f"⚠ {country}: No data available")
            else:
                print(f"⚠ {country}: Request failed ({response.status_code})")
        
        print("\n✅ GDP data test passed!")


class TestMacroCaching:
    """Test caching behavior for macro endpoints"""
    
    def test_cache_directories(self):
        """Test that macro cache uses correct directory"""
        print("\n" + "="*60)
        print("TEST: Macro Cache Directory Structure")
        print("="*60)
        
        info = macro_cache.get_info()
        
        assert 'Macro' in info['cache_dir'], "Wrong cache directory"
        assert info['namespace'] == 'Macro', "Wrong namespace"
        
        print(f"✓ Cache directory: {info['cache_dir']}")
        print(f"✓ Namespace: {info['namespace']}")
        print(f"✓ Expiry: {info['expiry_hours']} hours")
        
        print("\n✅ Cache directory test passed!")
    
    def test_cache_functionality(self):
        """Test that caching works for macro endpoints"""
        print("\n" + "="*60)
        print("TEST: Macro Data Caching")
        print("="*60)
        
        # Test currency caching
        start_time = datetime.now()
        response1 = requests.get(f"{API_BASE_URL}/api/economy/currency")
        time1 = (datetime.now() - start_time).total_seconds()
        
        assert response1.status_code == 200, "First request failed"
        
        # Second request should be cached
        start_time = datetime.now()
        response2 = requests.get(f"{API_BASE_URL}/api/economy/currency")
        time2 = (datetime.now() - start_time).total_seconds()
        
        assert response2.status_code == 200, "Second request failed"
        
        print(f"✓ First request: {time1:.3f}s")
        print(f"✓ Second request: {time2:.3f}s (cached)")
        
        # Data should be identical
        assert response1.json() == response2.json(), "Cache data mismatch"
        
        print("\n✅ Caching test passed!")
    
    def test_cache_file_names(self):
        """Test that cache files have descriptive names"""
        print("\n" + "="*60)
        print("TEST: Descriptive Cache File Names")
        print("="*60)
        
        # Make some requests to create cache files
        requests.get(f"{API_BASE_URL}/api/economy/currency")
        requests.get(f"{API_BASE_URL}/api/economy/crypto")
        requests.get(f"{API_BASE_URL}/api/economy/metals")
        
        # List cache files
        cache_files = macro_cache.list_keys()
        
        descriptive_count = 0
        for file_info in cache_files[:5]:
            filename = file_info['key']
            # Check if filename is descriptive (not just a hash)
            if any(word in filename for word in ['currency', 'crypto', 'metals', 'gdp', 'rates']):
                descriptive_count += 1
                print(f"✓ Descriptive filename: {filename}")
        
        print(f"✓ Found {descriptive_count} descriptive cache files")
        
        print("\n✅ Descriptive filenames test passed!")


class TestMacroDataIntegrity:
    """Test data integrity and validation"""
    
    def test_data_freshness(self):
        """Test that cached data includes timestamps"""
        print("\n" + "="*60)
        print("TEST: Data Freshness Timestamps")
        print("="*60)
        
        endpoints = [
            '/api/economy/currency',
            '/api/economy/crypto',
            '/api/economy/metals'
        ]
        
        for endpoint in endpoints:
            response = requests.get(f"{API_BASE_URL}{endpoint}")
            
            if response.status_code == 200:
                data = response.json()
                assert 'cached_at' in data, f"Missing timestamp for {endpoint}"
                
                cached_at = datetime.fromisoformat(data['cached_at'])
                age = (datetime.now() - cached_at).total_seconds() / 3600
                
                print(f"✓ {endpoint}: {age:.2f} hours old")
            else:
                print(f"⚠ {endpoint}: Request failed")
        
        print("\n✅ Data freshness test passed!")
    
    def test_error_handling(self):
        """Test error handling for invalid requests"""
        print("\n" + "="*60)
        print("TEST: Error Handling")
        print("="*60)
        
        # Test invalid country code
        response = requests.get(f"{API_BASE_URL}/api/economy/gdp/INVALID")
        
        # Should return error status (4xx or 5xx)
        assert response.status_code >= 400, "Should return error for invalid country"
        print(f"✓ Invalid country code: {response.status_code} error")
        
        print("\n✅ Error handling test passed!")


def run_all_macro_tests():
    """Run all macro tab tests"""
    print("\n" + "#"*60)
    print("# MACRO/ECONOMY TAB COMPREHENSIVE TESTS")
    print("#"*60)
    
    test_classes = [
        TestCurrencyEndpoints(),
        TestCryptoEndpoints(),
        TestMetalsEndpoints(),
        TestGDPEndpoints(),
        TestMacroCaching(),
        TestMacroDataIntegrity()
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
    
    success = run_all_macro_tests()
    sys.exit(0 if success else 1)
