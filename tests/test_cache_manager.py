"""
Comprehensive tests for CacheManager

Tests all caching functionality across the project
"""

import sys
import os
import time
import json
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.cache_manager import CacheManager, get_cache, stock_cache, financial_cache, economy_cache, ai_cache


def test_basic_operations():
    """Test basic cache operations"""
    print("\n" + "="*60)
    print("TEST 1: Basic Cache Operations")
    print("="*60)
    
    # Create test cache
    test_cache = CacheManager('test', expiry_hours=1)
    
    # Test SET
    data = {'test': 'data', 'value': 123}
    result = test_cache.set('test_key', data)
    assert result == True, "❌ Failed to set cache"
    print("✓ SET operation works")
    
    # Test GET
    retrieved = test_cache.get('test_key')
    assert retrieved == data, "❌ Retrieved data doesn't match"
    print("✓ GET operation works")
    
    # Test EXISTS
    exists = test_cache.exists('test_key')
    assert exists == True, "❌ Exists check failed"
    print("✓ EXISTS operation works")
    
    # Test non-existent key
    missing = test_cache.get('missing_key')
    assert missing is None, "❌ Should return None for missing key"
    print("✓ Returns None for missing keys")
    
    # Test DELETE
    deleted = test_cache.delete('test_key')
    assert deleted == True, "❌ Failed to delete"
    assert test_cache.get('test_key') is None, "❌ Data still exists after delete"
    print("✓ DELETE operation works")
    
    # Cleanup
    test_cache.clear_all()
    print("\n✅ All basic operations passed!")


def test_cache_with_parameters():
    """Test cache with parameters"""
    print("\n" + "="*60)
    print("TEST 2: Cache with Parameters")
    print("="*60)
    
    test_cache = CacheManager('test_params', expiry_hours=1)
    
    # Store with different parameters
    test_cache.set('stock', {'price': 100}, symbol='AAPL', period='1y')
    test_cache.set('stock', {'price': 200}, symbol='MSFT', period='1y')
    test_cache.set('stock', {'price': 150}, symbol='AAPL', period='6mo')
    
    # Retrieve with specific parameters
    aapl_1y = test_cache.get('stock', symbol='AAPL', period='1y')
    assert aapl_1y['price'] == 100, "❌ Wrong data for AAPL 1y"
    print("✓ AAPL 1y data correct")
    
    msft_1y = test_cache.get('stock', symbol='MSFT', period='1y')
    assert msft_1y['price'] == 200, "❌ Wrong data for MSFT 1y"
    print("✓ MSFT 1y data correct")
    
    aapl_6mo = test_cache.get('stock', symbol='AAPL', period='6mo')
    assert aapl_6mo['price'] == 150, "❌ Wrong data for AAPL 6mo"
    print("✓ AAPL 6mo data correct")
    
    # Cleanup
    test_cache.clear_all()
    print("\n✅ Parameter-based caching works!")


def test_expiration():
    """Test cache expiration"""
    print("\n" + "="*60)
    print("TEST 3: Cache Expiration")
    print("="*60)
    
    # Create cache with 1 second expiry
    test_cache = CacheManager('test_expiry', expiry_hours=0.0003)  # ~1 second
    
    # Store data
    test_cache.set('expire_test', {'data': 'test'})
    
    # Should exist immediately
    data = test_cache.get('expire_test')
    assert data is not None, "❌ Data should exist immediately"
    print("✓ Data exists immediately after caching")
    
    # Wait for expiration
    print("  Waiting 2 seconds for expiration...")
    time.sleep(2)
    
    # Should be expired now
    expired_data = test_cache.get('expire_test')
    assert expired_data is None, "❌ Data should be expired"
    print("✓ Data expired correctly")
    
    # Cleanup
    test_cache.clear_all()
    print("\n✅ Expiration works correctly!")


def test_json_storage():
    """Test that cache uses JSON (human-readable)"""
    print("\n" + "="*60)
    print("TEST 4: JSON Storage Format")
    print("="*60)
    
    test_cache = CacheManager('test_json', expiry_hours=1)
    
    # Store data
    test_data = {
        'symbol': 'AAPL',
        'prices': [100, 101, 102],
        'metadata': {'currency': 'USD'}
    }
    test_cache.set('json_test', test_data)
    
    # Find the cache file
    cache_files = list(test_cache.cache_dir.glob("*.json"))
    data_files = [f for f in cache_files if not f.name.endswith('.meta.json')]
    
    assert len(data_files) > 0, "❌ No cache files found"
    print(f"✓ Found {len(data_files)} cache file(s)")
    
    # Read and verify it's valid JSON
    cache_file = data_files[0]
    with open(cache_file, 'r') as f:
        loaded_data = json.load(f)
    
    assert loaded_data == test_data, "❌ Loaded data doesn't match"
    print("✓ Cache file is valid JSON")
    print("✓ Data is human-readable")
    
    # Cleanup
    test_cache.clear_all()
    print("\n✅ JSON storage works correctly!")


def test_namespace_isolation():
    """Test that different namespaces are isolated"""
    print("\n" + "="*60)
    print("TEST 5: Namespace Isolation")
    print("="*60)
    
    cache1 = CacheManager('namespace1', expiry_hours=1)
    cache2 = CacheManager('namespace2', expiry_hours=1)
    
    # Store in namespace1
    cache1.set('key', {'namespace': 1})
    
    # Should not exist in namespace2
    data = cache2.get('key')
    assert data is None, "❌ Data leaked between namespaces"
    print("✓ Namespaces are isolated")
    
    # Store in namespace2
    cache2.set('key', {'namespace': 2})
    
    # Both should have their own data
    data1 = cache1.get('key')
    data2 = cache2.get('key')
    
    assert data1['namespace'] == 1, "❌ Namespace1 data corrupted"
    assert data2['namespace'] == 2, "❌ Namespace2 data corrupted"
    print("✓ Each namespace maintains its own data")
    
    # Cleanup
    cache1.clear_all()
    cache2.clear_all()
    print("\n✅ Namespace isolation works!")


def test_stock_cache():
    """Test stock price cache"""
    print("\n" + "="*60)
    print("TEST 6: Stock Price Cache")
    print("="*60)
    
    # Test stock_cache singleton
    assert stock_cache is not None, "❌ stock_cache not initialized"
    print("✓ stock_cache singleton exists")
    
    # Test caching historical data
    historical_data = {
        'symbol': 'AAPL',
        'dates': ['2024-01-01', '2024-01-02'],
        'close': [150, 151]
    }
    stock_cache.set('historical', historical_data, symbol='AAPL', period='1y')
    
    retrieved = stock_cache.get('historical', symbol='AAPL', period='1y')
    assert retrieved is not None, "❌ Failed to retrieve cached historical data"
    assert retrieved['symbol'] == 'AAPL', "❌ Wrong historical data"
    print("✓ Historical stock data caches correctly")
    
    # Test caching quote data
    quote_data = {'symbol': 'AAPL', 'current': 150.50}
    stock_cache.set('quote', quote_data, symbol='AAPL')
    
    retrieved_quote = stock_cache.get('quote', symbol='AAPL')
    assert retrieved_quote is not None, "❌ Failed to retrieve cached quote"
    assert retrieved_quote['current'] == 150.50, "❌ Wrong quote data"
    print("✓ Quote data caches correctly")
    
    # Check cache info
    info = stock_cache.get_info()
    print(f"✓ Stock cache info: {info['total_entries']} entries, {info['total_size_mb']} MB")
    
    print("\n✅ Stock cache works correctly!")


def test_ai_cache():
    """Test AI model cache"""
    print("\n" + "="*60)
    print("TEST 7: AI Model Cache")
    print("="*60)
    
    assert ai_cache is not None, "❌ ai_cache not initialized"
    print("✓ ai_cache singleton exists")
    
    # Check cache directory
    expected_path = Path('.api_cache/AI')
    assert expected_path.name in str(ai_cache.cache_dir), f"❌ Wrong cache dir: {ai_cache.cache_dir}"
    print(f"✓ AI cache directory: {ai_cache.cache_dir}")
    
    # Test AI model prediction caching
    model_prediction = {
        'model': 'test_model',
        'prediction': [0.1, 0.9],
        'features': ['f1', 'f2']
    }
    ai_cache.set('prediction', model_prediction, model='test_model', ticker='AAPL')
    
    retrieved = ai_cache.get('prediction', model='test_model', ticker='AAPL')
    assert retrieved is not None, "❌ Failed to retrieve AI prediction"
    assert retrieved['prediction'] == [0.1, 0.9], "❌ Wrong prediction data"
    print("✓ AI predictions cache correctly")
    
    # Check expiry time
    info = ai_cache.get_info()
    assert info['expiry_hours'] == 720, "❌ AI cache should have 720 hour expiry"
    print(f"✓ AI cache expiry: {info['expiry_hours']} hours (30 days)")
    
    print("\n✅ AI cache works correctly!")


def test_cleanup_operations():
    """Test cleanup operations"""
    print("\n" + "="*60)
    print("TEST 8: Cleanup Operations")
    print("="*60)
    
    test_cache = CacheManager('test_cleanup', expiry_hours=0.0003)  # 1 second
    
    # Create multiple entries
    for i in range(5):
        test_cache.set(f'key_{i}', {'value': i})
    
    info = test_cache.get_info()
    assert info['total_entries'] == 5, "❌ Should have 5 entries"
    print(f"✓ Created {info['total_entries']} cache entries")
    
    # Wait for expiration
    time.sleep(2)
    
    # Cleanup expired
    removed = test_cache.cleanup_expired()
    assert removed == 5, f"❌ Should have removed 5 entries, removed {removed}"
    print(f"✓ Cleaned up {removed} expired entries")
    
    # Verify all removed
    info = test_cache.get_info()
    assert info['total_entries'] == 0, "❌ Should have 0 entries after cleanup"
    print("✓ All expired entries removed")
    
    print("\n✅ Cleanup operations work!")


def test_cache_info_and_listing():
    """Test cache info and key listing"""
    print("\n" + "="*60)
    print("TEST 9: Cache Info and Listing")
    print("="*60)
    
    test_cache = CacheManager('test_info', expiry_hours=24)
    
    # Create entries
    test_cache.set('key1', {'data': 1}, param='a')
    test_cache.set('key2', {'data': 2}, param='b')
    test_cache.set('key3', {'data': 3}, param='c')
    
    # Get info
    info = test_cache.get_info()
    print(f"✓ Cache info: {json.dumps(info, indent=2)}")
    assert info['total_entries'] == 3, "❌ Should have 3 entries"
    assert info['valid_entries'] == 3, "❌ All should be valid"
    assert info['expired_entries'] == 0, "❌ None should be expired"
    
    # List keys
    keys = test_cache.list_keys()
    assert len(keys) == 3, "❌ Should list 3 keys"
    print(f"✓ Listed {len(keys)} keys")
    
    for key_info in keys:
        print(f"  - {key_info['key']}: {key_info['size_kb']} KB, expired={key_info['expired']}")
    
    # Cleanup
    test_cache.clear_all()
    print("\n✅ Info and listing work!")


def run_all_tests():
    """Run all tests"""
    print("\n" + "#"*60)
    print("# COMPREHENSIVE CACHE MANAGER TESTS")
    print("#"*60)
    
    try:
        test_basic_operations()
        test_cache_with_parameters()
        test_expiration()
        test_json_storage()
        test_namespace_isolation()
        test_stock_cache()
        test_ai_cache()
        test_cleanup_operations()
        test_cache_info_and_listing()
        
        print("\n" + "#"*60)
        print("# ✅ ALL TESTS PASSED!")
        print("#"*60)
        return True
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
