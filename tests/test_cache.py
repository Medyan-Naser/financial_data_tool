"""
Test if the cache is working properly for stock price data

Comprehensive test suite for API cache functionality including:
- Cache directory and info operations
- Cache get/set operations
- Cache expiry behavior
- Cache key generation
- Error handling
"""

import sys
import os
import pytest
import time
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.api_cache import api_cache


class TestCacheDirectory:
    """Test cache directory operations"""
    
    def test_cache_directory_exists(self):
        """Test that cache directory is created"""
        print("\n" + "="*60)
        print("TEST: Cache Directory Exists")
        print("="*60)
        
        assert api_cache.cache_dir.exists(), "Cache directory should exist"
        print(f"✓ Cache directory: {api_cache.cache_dir}")
        print("✅ Cache directory test passed!")
    
    def test_cache_directory_is_writable(self):
        """Test that cache directory is writable"""
        print("\n" + "="*60)
        print("TEST: Cache Directory Writable")
        print("="*60)
        
        test_file = api_cache.cache_dir / ".write_test"
        try:
            test_file.write_text("test")
            assert test_file.exists(), "Should be able to write to cache dir"
            test_file.unlink()  # Clean up
            print("✓ Cache directory is writable")
            print("✅ Write test passed!")
        except Exception as e:
            pytest.fail(f"Cache directory not writable: {e}")

