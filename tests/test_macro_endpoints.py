#!/usr/bin/env python3
"""
Test script for all macro economic indicator endpoints.
This script tests each endpoint to ensure data loads properly.
"""

import requests
import json
from typing import Dict, Any
import sys

# Base URL for the API
API_BASE_URL = "http://localhost:8000"

# Define all endpoints to test
ENDPOINTS = {
    "Overview": "/api/macro/overview",
    "Commodities": "/api/macro/commodities",
    "Currencies": "/api/macro/currencies",
    "Inflation": "/api/macro/inflation",
    "Debt to GDP": "/api/macro/debt-to-gdp",
    "Dollar Index": "/api/macro/dollar-index",
    "Money Velocity": "/api/macro/velocity",
    "Unemployment": "/api/macro/unemployment",
    "Real Estate": "/api/macro/real-estate",
    "Markets": "/api/macro/markets",
    "Bonds": "/api/macro/bonds",
    "Yield Curve": "/api/macro/yield-curve",
    "GDP Growth": "/api/macro/gdp-growth",
    "Consumer Sentiment": "/api/macro/consumer-sentiment",
    "Manufacturing PMI": "/api/macro/pmi",
    "Retail Sales": "/api/macro/retail-sales",
}

def test_endpoint(name: str, endpoint: str) -> Dict[str, Any]:
    """
    Test a single endpoint and return results.
    
    Args:
        name: Display name for the endpoint
        endpoint: API endpoint path
        
    Returns:
        Dictionary with test results
    """
    url = f"{API_BASE_URL}{endpoint}"
    
    try:
        print(f"Testing {name}... ", end="", flush=True)
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            # Check if response has data
            has_data = False
            data_info = ""
            
            if isinstance(data, dict):
                if 'chart' in data:
                    has_data = True
                    data_info = "Has chart data"
                elif 'data' in data:
                    has_data = True
                    data_info = f"Has data ({len(data.get('data', []))} items)"
                elif 'indicators' in data:
                    has_data = True
                    data_info = f"Has indicators ({len(data.get('indicators', []))} items)"
                else:
                    # Check for nested data structures (like bonds, commodities)
                    data_keys = list(data.keys())
                    if data_keys:
                        has_data = True
                        data_info = f"Has keys: {', '.join(data_keys[:3])}"
            
            if has_data:
                print(f"✅ PASS - {data_info}")
                return {
                    "name": name,
                    "status": "PASS",
                    "message": data_info,
                    "response_code": 200
                }
            else:
                print(f"⚠️  WARN - Empty response")
                return {
                    "name": name,
                    "status": "WARN",
                    "message": "Empty response",
                    "response_code": 200
                }
        else:
            print(f"❌ FAIL - HTTP {response.status_code}")
            error_msg = response.text[:100] if response.text else "No error message"
            return {
                "name": name,
                "status": "FAIL",
                "message": error_msg,
                "response_code": response.status_code
            }
            
    except requests.exceptions.Timeout:
        print(f"❌ FAIL - Timeout")
        return {
            "name": name,
            "status": "FAIL",
            "message": "Request timeout (30s)",
            "response_code": None
        }
    except requests.exceptions.ConnectionError:
        print(f"❌ FAIL - Connection error (server not running?)")
        return {
            "name": name,
            "status": "FAIL",
            "message": "Connection error - is the server running?",
            "response_code": None
        }
    except Exception as e:
        print(f"❌ FAIL - {str(e)[:50]}")
        return {
            "name": name,
            "status": "FAIL",
            "message": str(e)[:100],
            "response_code": None
        }


def main():
    """Run all endpoint tests and print summary."""
    print("=" * 70)
    print("MACRO ECONOMIC INDICATORS - ENDPOINT TESTING")
    print("=" * 70)
    print()
    
    results = []
    
    # Test each endpoint
    for name, endpoint in ENDPOINTS.items():
        result = test_endpoint(name, endpoint)
        results.append(result)
    
    # Print summary
    print()
    print("=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for r in results if r["status"] == "PASS")
    warned = sum(1 for r in results if r["status"] == "WARN")
    failed = sum(1 for r in results if r["status"] == "FAIL")
    total = len(results)
    
    print(f"\nTotal Endpoints: {total}")
    print(f"✅ Passed: {passed}")
    print(f"⚠️  Warnings: {warned}")
    print(f"❌ Failed: {failed}")
    
    # Show failed tests
    if failed > 0:
        print("\n" + "=" * 70)
        print("FAILED TESTS:")
        print("=" * 70)
        for result in results:
            if result["status"] == "FAIL":
                print(f"\n❌ {result['name']}")
                print(f"   Message: {result['message']}")
                if result['response_code']:
                    print(f"   HTTP Code: {result['response_code']}")
    
    # Show warnings
    if warned > 0:
        print("\n" + "=" * 70)
        print("WARNINGS:")
        print("=" * 70)
        for result in results:
            if result["status"] == "WARN":
                print(f"\n⚠️  {result['name']}")
                print(f"   Message: {result['message']}")
    
    print("\n" + "=" * 70)
    
    # Exit code based on results
    if failed > 0:
        print("\n❌ Some tests failed. Please check the server logs.")
        sys.exit(1)
    elif warned > 0:
        print("\n⚠️  All tests passed but some have warnings.")
        sys.exit(0)
    else:
        print("\n✅ All tests passed successfully!")
        sys.exit(0)


if __name__ == "__main__":
    main()
