"""
Test the stock price backend endpoint
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_historical(symbol="AAPL"):
    """Test historical prices endpoint"""
    url = f"{BASE_URL}/api/stock-price/historical/{symbol}"
    params = {'period': '1y'}
    
    print(f"Testing historical prices for {symbol}...")
    print(f"URL: {url}")
    
    try:
        response = requests.get(url, params=params, timeout=30)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Success!")
            print(f"  Data points: {data.get('data_points')}")
            print(f"  Date range: {data.get('start_date')} to {data.get('end_date')}")
            print(f"  Currency: {data.get('currency')}")
            print(f"  Sample prices (first 5): {data.get('close', [])[:5]}")
            return data
        else:
            print(f"✗ Error: {response.text}")
            return None
    except Exception as e:
        print(f"✗ Connection error: {e}")
        print("Make sure the backend server is running: cd backend && uvicorn app.main:app --reload")
        return None

def test_quote(symbol="AAPL"):
    """Test real-time quote endpoint"""
    url = f"{BASE_URL}/api/stock-price/quote/{symbol}"
    
    print(f"\nTesting real-time quote for {symbol}...")
    print(f"URL: {url}")
    
    try:
        response = requests.get(url, timeout=30)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Current Price: ${data.get('current')}")
            print(f"  Change: ${data.get('change')} ({data.get('change_percent')}%)")
            print(f"  Open: ${data.get('open')}")
            print(f"  High: ${data.get('high')}")
            print(f"  Low: ${data.get('low')}")
            return data
        else:
            print(f"✗ Error: {response.text}")
            return None
    except Exception as e:
        print(f"✗ Connection error: {e}")
        return None

def test_combined(symbol="AAPL"):
    """Test combined endpoint"""
    url = f"{BASE_URL}/api/stock-price/combined/{symbol}"
    params = {'period': '6mo'}
    
    print(f"\nTesting combined data for {symbol}...")
    print(f"URL: {url}")
    
    try:
        response = requests.get(url, params=params, timeout=30)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Success!")
            print(f"  Historical data points: {data['historical'].get('data_points')}")
            print(f"  Current price: ${data['quote'].get('current')}")
            return data
        else:
            print(f"✗ Error: {response.text}")
            return None
    except Exception as e:
        print(f"✗ Connection error: {e}")
        return None

if __name__ == "__main__":
    print("=" * 60)
    print("TESTING STOCK PRICE API ENDPOINTS")
    print("=" * 60)
    
    test_historical("AAPL")
    test_quote("AAPL")
    test_combined("AAPL")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)
