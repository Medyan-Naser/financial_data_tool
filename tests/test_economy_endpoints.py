#!/usr/bin/env python3
"""
Test script for Economy tab endpoints.
Tests each endpoint and validates data is not empty or NaN.
"""

import requests
import json
import sys

BASE_URL = "http://localhost:8000"

# List of all endpoints to test
ENDPOINTS = [
    "/api/macro/commodities",
    "/api/macro/currencies",
    "/api/macro/inflation",
    "/api/macro/debt-to-gdp",
    "/api/macro/dollar-index",
    "/api/macro/velocity",
    "/api/macro/unemployment",
    "/api/macro/real-estate",
    "/api/macro/bonds",
    "/api/macro/yield-curve",
    "/api/macro/markets",
    "/api/macro/gdp-growth",
    "/api/macro/consumer-sentiment",
    "/api/macro/pmi",
    "/api/macro/retail-sales",
    "/api/macro/gold-silver",
    "/api/macro/crypto",
]

def validate_plotly_data(data, endpoint_name):
    """Validate Plotly chart data has actual values"""
    if not data:
        return False, "No data returned"
    
    if 'data' not in data:
        return False, "Missing 'data' field in Plotly object"
    
    traces = data['data']
    if not traces or len(traces) == 0:
        return False, "No traces in data"
    
    # Check first trace for actual data
    trace = traces[0]
    
    # Handle table type
    if trace.get('type') == 'table':
        cells = trace.get('cells', {}).get('values', [])
        if not cells or len(cells) == 0:
            return False, "Table has no cell values"
        
        # Check if cells have data
        first_col = cells[0] if cells else []
        if not first_col or len(first_col) == 0:
            return False, "Table cells are empty"
        
        return True, f"Table with {len(cells)} columns and {len(first_col)} rows"
    
    # Handle chart types (line, scatter, etc.)
    if 'y' not in trace:
        return False, "No y-axis data in trace"
    
    y_data = trace['y']
    if not y_data or len(y_data) == 0:
        return False, "Y-axis data is empty"
    
    # Check for all NaN/None values
    valid_values = [v for v in y_data if v is not None and str(v).lower() != 'nan']
    if len(valid_values) == 0:
        return False, "All y-axis values are NaN or None"
    
    return True, f"Chart with {len(y_data)} data points ({len(valid_values)} valid)"


def test_endpoint(endpoint):
    """Test a single endpoint"""
    url = f"{BASE_URL}{endpoint}"
    print(f"\n{'='*60}")
    print(f"Testing: {endpoint}")
    print(f"{'='*60}")
    
    try:
        response = requests.get(url, timeout=30)
        
        # Check HTTP status
        if response.status_code != 200:
            print(f"❌ FAILED: HTTP {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
        
        # Parse JSON
        try:
            data = response.json()
        except json.JSONDecodeError as e:
            print(f"❌ FAILED: Invalid JSON response")
            print(f"   Error: {e}")
            return False
        
        # Validate based on endpoint structure
        if endpoint == "/api/macro/commodities":
            # Has multiple sub-charts
            for category in ['energy', 'metals', 'agricultural', 'livestock', 'industrial', 'index']:
                if category not in data:
                    print(f"❌ Missing category: {category}")
                    return False
                
                valid, msg = validate_plotly_data(data[category].get('chart'), f"{endpoint}/{category}")
                if not valid:
                    print(f"❌ {category}: {msg}")
                    return False
                else:
                    print(f"✅ {category}: {msg}")
            
            return True
        
        elif endpoint == "/api/macro/bonds":
            # Has multiple bond regions
            for region in ['major_10y', 'europe', 'america', 'asia', 'australia', 'africa']:
                if region not in data:
                    print(f"❌ Missing region: {region}")
                    return False
                
                valid, msg = validate_plotly_data(data[region], f"{endpoint}/{region}")
                if not valid:
                    print(f"❌ {region}: {msg}")
                    return False
                else:
                    print(f"✅ {region}: {msg}")
            
            return True
        
        elif endpoint == "/api/macro/crypto":
            # Has bitcoin and ethereum
            for crypto in ['bitcoin', 'ethereum']:
                if crypto not in data:
                    print(f"❌ Missing crypto: {crypto}")
                    return False
                
                valid, msg = validate_plotly_data(data[crypto], f"{endpoint}/{crypto}")
                if not valid:
                    print(f"❌ {crypto}: {msg}")
                    return False
                else:
                    print(f"✅ {crypto}: {msg}")
            
            return True
        
        elif endpoint == "/api/macro/currencies":
            # Has both data and chart
            if 'chart' not in data:
                print(f"❌ Missing 'chart' field")
                return False
            
            valid, msg = validate_plotly_data(data['chart'], endpoint)
            if not valid:
                print(f"❌ Chart: {msg}")
                return False
            else:
                print(f"✅ Chart: {msg}")
            
            return True
        
        elif endpoint == "/api/macro/markets":
            # Has chart (table format)
            if 'chart' not in data:
                print(f"❌ Missing 'chart' field")
                return False
            
            valid, msg = validate_plotly_data(data['chart'], endpoint)
            if not valid:
                print(f"❌ Chart: {msg}")
                return False
            else:
                print(f"✅ Chart: {msg}")
            
            return True
        
        else:
            # Standard format with 'chart' field
            if 'chart' not in data:
                print(f"❌ Missing 'chart' field")
                return False
            
            valid, msg = validate_plotly_data(data['chart'], endpoint)
            if not valid:
                print(f"❌ Chart: {msg}")
                return False
            else:
                print(f"✅ Chart: {msg}")
            
            return True
    
    except requests.exceptions.Timeout:
        print(f"❌ FAILED: Request timeout")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ FAILED: Request error - {e}")
        return False
    except Exception as e:
        print(f"❌ FAILED: Unexpected error - {e}")
        import traceback
        traceback.print_exc()
        return False




if __name__ == "__main__":
    main()
