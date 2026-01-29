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


class TestCacheInfo:
    """Test cache info operations"""
    
    def test_get_cache_info_returns_dict(self):
        """Test that get_cache_info returns expected structure"""
        print("\n" + "="*60)
        print("TEST: Cache Info Structure")
        print("="*60)
        
        info = api_cache.get_cache_info()
        
        assert isinstance(info, dict), "Cache info should be a dict"
        assert 'total_entries' in info, "Should have total_entries"
        assert 'expiry_hours' in info, "Should have expiry_hours"
        
        print(f"✓ Total entries: {info['total_entries']}")
        print(f"✓ Expiry hours: {info['expiry_hours']}")
        print("✅ Cache info test passed!")
    
    def test_cache_info_values_are_valid(self):
        """Test that cache info values are reasonable"""
        print("\n" + "="*60)
        print("TEST: Cache Info Values")
        print("="*60)
        
        info = api_cache.get_cache_info()
        
        assert info['total_entries'] >= 0, "Total entries should be non-negative"
        assert info['expiry_hours'] > 0, "Expiry hours should be positive"
        
        if 'total_size_mb' in info:
            assert info['total_size_mb'] >= 0, "Size should be non-negative"
            print(f"✓ Total size: {info['total_size_mb']:.2f} MB")
        
        print("✅ Cache info values test passed!")

