"""
Quick test to verify economy endpoints are working
"""

import requests

API_BASE = "http://localhost:8000"

def test_economy_endpoints():
    """Test that all economy endpoints work"""
    print("\n" + "="*60)
    print("Testing Economy Endpoints")
    print("="*60)
    
    endpoints = [
        "/api/economy/currency",
        "/api/economy/crypto",
        "/api/economy/metals",
        "/api/economy/metals/historical?years=1",
        "/api/economy/crypto/historical/bitcoin?days=365",
        "/api/economy/gdp/US",
        "/api/economy/interest-rates",
        "/api/economy/inflation/US",
    ]
    
    passed = 0
    failed = 0
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{API_BASE}{endpoint}", timeout=10)
            if response.status_code == 200:
                print(f"✅ {endpoint}")
                passed += 1
            else:
                print(f"❌ {endpoint} - Status: {response.status_code}")
                failed += 1
        except Exception as e:
            print(f"❌ {endpoint} - Error: {str(e)}")
            failed += 1
    
    print("\n" + "="*60)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*60)
    
    return failed == 0

if __name__ == "__main__":
    import sys
    print("\n⚠️  Make sure backend is running on http://localhost:8000")
    import time
    time.sleep(2)
    
    success = test_economy_endpoints()
    sys.exit(0 if success else 1)
