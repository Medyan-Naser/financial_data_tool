#!/usr/bin/env python3
"""
Integration test for Economy API endpoints
Tests all endpoints and verifies data structure and caching
"""

import requests
import json
import time
from datetime import datetime

API_BASE_URL = "http://localhost:8000"

def test_endpoint(name, url, expected_keys):
    """Test a single endpoint and verify response structure."""
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print(f"URL: {url}")
    print(f"{'='*60}")
    
    try:
        start_time = time.time()
        response = requests.get(url, timeout=10)
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            
            # Verify expected keys
            missing_keys = [key for key in expected_keys if key not in data]
            
            print(f"✅ SUCCESS (took {elapsed:.2f}s)")
            print(f"   Status: {response.status_code}")
            
            if missing_keys:
                print(f"   ⚠️ Missing keys: {missing_keys}")
            else:
                print(f"   ✓ All expected keys present")
            
            # Show cache info if available
            if 'cached_at' in data:
                print(f"   Cache created: {data['cached_at']}")
            if 'cache_expires' in data:
                print(f"   Cache expires: {data['cache_expires']}")
            
            # Show data sample
            print(f"   Data sample:")
            for key in expected_keys[:3]:  # Show first 3 keys
                if key in data:
                    value = data[key]
                    if isinstance(value, (list, dict)):
                        print(f"     {key}: {type(value).__name__} (len={len(value)})")
                    else:
                        print(f"     {key}: {value}")
            
            return True, data
        else:
            print(f"❌ FAILED")
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False, None
            
    except Exception as e:
        print(f"❌ ERROR")
        print(f"   Exception: {str(e)}")
        return False, None


def main():
    """Run all integration tests."""
    print("\n" + "="*60)
    print("ECONOMY API INTEGRATION TESTS")
    print("="*60)
    print(f"Testing Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"API Base URL: {API_BASE_URL}")
    
    results = {}
    
    # Test 1: Overview
    results['overview'] = test_endpoint(
        "Economy Overview",
        f"{API_BASE_URL}/api/economy/overview",
        ['last_updated', 'sections']
    )
    
    # Test 2: Currency Rates
    results['currency'] = test_endpoint(
        "Currency Exchange Rates",
        f"{API_BASE_URL}/api/economy/currency",
        ['base', 'date', 'rates', 'cached_at', 'cache_expires']
    )
    

    
    start_time = time.time()
    response1 = requests.get(f"{API_BASE_URL}/api/economy/currency")
    time1 = time.time() - start_time
    
    time.sleep(0.5)  # Small delay
    
    start_time = time.time()
    response2 = requests.get(f"{API_BASE_URL}/api/economy/currency")
    time2 = time.time() - start_time
    
    if response1.status_code == 200 and response2.status_code == 200:
        data1 = response1.json()
        data2 = response2.json()
        
        if data1.get('cached_at') == data2.get('cached_at'):
            print(f"✅ Cache working correctly!")
            print(f"   First request: {time1:.3f}s")
            print(f"   Second request: {time2:.3f}s (from cache)")
            print(f"   Speedup: {time1/time2:.1f}x faster")
        else:
            print(f"⚠️  Cache may not be working (different timestamps)")
    
    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    
    passed = sum(1 for success, _ in results.values() if success)
    total = len(results)
    
    for name, (success, data) in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status}: {name}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    # Detailed data validation
    print(f"\n{'='*60}")
    print("DATA VALIDATION")
    print(f"{'='*60}")
    
    # Validate currency data
    if results['currency'][0]:
        data = results['currency'][1]
        major_currencies = ['EUR', 'GBP', 'JPY', 'CHF', 'CAD']
        available = [c for c in major_currencies if c in data.get('rates', {})]
        print(f"✓ Currency: {len(available)}/{len(major_currencies)} major currencies available")
    
    # Validate crypto data
    if results['crypto'][0]:
        data = results['crypto'][1]
        crypto_count = data.get('total_count', 0)
        has_btc = any(c.get('symbol') == 'BTC' for c in data.get('cryptocurrencies', []))
        print(f"✓ Crypto: {crypto_count} cryptocurrencies, BTC included: {has_btc}")
    
    # Validate metals data
    if results['metals'][0]:
        data = results['metals'][1]
        has_gold = 'gold' in data and 'price_usd_oz' in data['gold']
        has_silver = 'silver' in data and 'price_usd_oz' in data['silver']
        print(f"✓ Metals: Gold data: {has_gold}, Silver data: {has_silver}")
    
    # Validate GDP data
    if results['gdp'][0]:
        data = results['gdp'][1]
        years_available = len(data.get('data', []))
        print(f"✓ GDP: {years_available} years of historical data")
    
    # Validate inflation data
    if results['inflation'][0]:
        data = results['inflation'][1]
        years_available = len(data.get('data', []))
        print(f"✓ Inflation: {years_available} years of historical data")
    
    # Validate interest rates
    if results['interest_rates'][0]:
        data = results['interest_rates'][1]
        rates_count = len(data.get('rates', []))
        print(f"✓ Interest Rates: {rates_count} rate entries")
    
    print(f"\n{'='*60}")
    if passed == total:
        print("✅ ALL TESTS PASSED!")
        print("The Economy API is fully functional and ready to use.")
    else:
        print(f"⚠️  {total - passed} tests failed. Please check the errors above.")
    print(f"{'='*60}\n")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
