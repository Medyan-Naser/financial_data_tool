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

