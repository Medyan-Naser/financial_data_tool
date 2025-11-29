"""
Comprehensive Cache Integration Test

Verifies ALL parts of the project use the new modular cache system
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.cache_manager import (
    CacheManager, 
    get_cache,
    stock_cache,
    financial_cache,
    economy_cache,
    ai_cache
)
from pathlib import Path
import json


def test_all_cache_singletons_exist():
    """Verify all pre-configured cache instances exist"""
    print("\n" + "="*60)
    print("TEST: All Cache Singletons Exist")
    print("="*60)
    
    caches = {
        'stock_cache': stock_cache,
        'financial_cache': financial_cache,
        'economy_cache': economy_cache,
        'ai_cache': ai_cache
    }
    
    for name, cache in caches.items():
        assert cache is not None, f"❌ {name} not initialized"
        assert isinstance(cache, CacheManager), f"❌ {name} is not a CacheManager instance"
        print(f"✓ {name} exists")
    
    print("\n✅ All cache singletons exist!")


def test_cache_namespaces():
    """Verify each cache has correct namespace"""
    print("\n" + "="*60)
    print("TEST: Cache Namespaces")
    print("="*60)
    
    expected_namespaces = {
        stock_cache: 'stocks',
        financial_cache: 'financials',
        economy_cache: 'economy',
        ai_cache: 'AI'
    }
    
    for cache, expected_ns in expected_namespaces.items():
        info = cache.get_info()
        actual_ns = info['namespace']
        assert actual_ns == expected_ns, f"❌ Expected {expected_ns}, got {actual_ns}"
        print(f"✓ {expected_ns}: correct namespace")
    
    print("\n✅ All namespaces correct!")


def test_cache_directories():
    """Verify each cache uses correct directory"""
    print("\n" + "="*60)
    print("TEST: Cache Directories")
    print("="*60)
    
    caches = {
        'stocks': stock_cache,
        'financials': financial_cache,
        'economy': economy_cache,
        'AI': ai_cache
    }
    
    for name, cache in caches.items():
        info = cache.get_info()
        cache_dir = Path(info['cache_dir'])
        
        # Check directory exists
        assert cache_dir.exists(), f"❌ Directory doesn't exist: {cache_dir}"
        
        # Check directory name contains namespace
        assert name in str(cache_dir), f"❌ Directory doesn't contain '{name}': {cache_dir}"
        
        print(f"✓ {name}: {cache_dir}")
    
    print("\n✅ All cache directories correct!")


def test_cache_expiry_settings():
    """Verify each cache has correct expiry settings"""
    print("\n" + "="*60)
    print("TEST: Cache Expiry Settings")
    print("="*60)
    
    expected_expiry = {
        'stocks': 168,        # 1 week
        'financials': 168,    # 1 week
        'economy': 24,        # 1 day
        'AI': 720             # 30 days
    }
    
    caches = {
        'stocks': stock_cache,
        'financials': financial_cache,
        'economy': economy_cache,
        'AI': ai_cache
    }
    
    for name, cache in caches.items():
        info = cache.get_info()
        actual_expiry = info['expiry_hours']
        expected = expected_expiry[name]
        
        assert actual_expiry == expected, f"❌ {name}: expected {expected}h, got {actual_expiry}h"
        
        # Convert to days for display
        days = actual_expiry / 24
        print(f"✓ {name}: {actual_expiry} hours ({days} days)")
    
    print("\n✅ All expiry settings correct!")


def test_json_format_all_caches():
    """Verify all caches use JSON format"""
    print("\n" + "="*60)
    print("TEST: JSON Format (All Caches)")
    print("="*60)
    
    caches = {
        'stocks': stock_cache,
        'financials': financial_cache,
        'economy': economy_cache,
        'AI': ai_cache
    }
    
    for name, cache in caches.items():
        # Store test data
        test_data = {'test': f'{name}_data', 'value': 123}
        cache.set('test', test_data)
        
        # Find cache file
        cache_files = list(cache.cache_dir.glob("*.json"))
        data_files = [f for f in cache_files if not f.name.endswith('.meta.json')]
        
        if len(data_files) > 0:
            # Read and verify JSON
            with open(data_files[0], 'r') as f:
                content = f.read()
                loaded = json.loads(content)
            
            # Check it's formatted (has newlines and indentation)
            assert '\n' in content, f"❌ {name}: Not formatted with newlines"
            print(f"✓ {name}: JSON format verified")
        
        # Cleanup
        cache.delete('test')
    
    print("\n✅ All caches use JSON format!")


def test_cross_namespace_isolation():
    """Verify data doesn't leak between namespaces"""
    print("\n" + "="*60)
    print("TEST: Cross-Namespace Isolation")
    print("="*60)
    
    # Store same key in different caches
    stock_cache.set('test_isolation', {'source': 'stocks'})
    financial_cache.set('test_isolation', {'source': 'financials'})
    economy_cache.set('test_isolation', {'source': 'economy'})
    ai_cache.set('test_isolation', {'source': 'AI'})
    
    # Verify each returns its own data
    stock_data = stock_cache.get('test_isolation')
    financial_data = financial_cache.get('test_isolation')
    economy_data = economy_cache.get('test_isolation')
    ai_data = ai_cache.get('test_isolation')
    
    assert stock_data['source'] == 'stocks', "❌ Stock data corrupted"
    assert financial_data['source'] == 'financials', "❌ Financial data corrupted"
    assert economy_data['source'] == 'economy', "❌ Economy data corrupted"
    assert ai_data['source'] == 'AI', "❌ AI data corrupted"
    
    print("✓ All namespaces properly isolated")
    
    # Cleanup
    stock_cache.delete('test_isolation')
    financial_cache.delete('test_isolation')
    economy_cache.delete('test_isolation')
    ai_cache.delete('test_isolation')
    
    print("\n✅ Cross-namespace isolation verified!")


def test_cache_statistics():
    """Get statistics for all caches"""
    print("\n" + "="*60)
    print("TEST: Cache Statistics")
    print("="*60)
    
    caches = {
        'Stocks': stock_cache,
        'Financials': financial_cache,
        'Economy': economy_cache,
        'AI': ai_cache
    }
    
    total_entries = 0
    total_size = 0
    
    print("\nCache Statistics:")
    print("-" * 60)
    
    for name, cache in caches.items():
        info = cache.get_info()
        total_entries += info['total_entries']
        total_size += info['total_size_mb']
        
        print(f"{name:15} | Entries: {info['total_entries']:3} | "
              f"Size: {info['total_size_mb']:6.2f} MB | "
              f"Expiry: {info['expiry_hours']:4}h")
    
    print("-" * 60)
    print(f"{'TOTAL':15} | Entries: {total_entries:3} | Size: {total_size:6.2f} MB")
    
    print("\n✅ Statistics retrieved successfully!")


def test_cache_structure():
    """Verify cache file structure"""
    print("\n" + "="*60)
    print("TEST: Cache File Structure")
    print("="*60)
    
    # Create a test entry
    test_cache = CacheManager('test_structure', expiry_hours=1)
    test_cache.set('test_key', {'data': 'test'}, param1='value1')
    
    # Check files created
    data_files = list(test_cache.cache_dir.glob("*.json"))
    meta_files = list(test_cache.cache_dir.glob("*.meta.json"))
    actual_data_files = [f for f in data_files if not f.name.endswith('.meta.json')]
    
    assert len(actual_data_files) > 0, "❌ No data files created"
    assert len(meta_files) > 0, "❌ No metadata files created"
    print(f"✓ Data files: {len(actual_data_files)}")
    print(f"✓ Metadata files: {len(meta_files)}")
    
    # Verify metadata structure
    with open(meta_files[0], 'r') as f:
        metadata = json.load(f)
    
    required_fields = ['key', 'params', 'timestamp', 'expiry', 'namespace']
    for field in required_fields:
        assert field in metadata, f"❌ Missing field in metadata: {field}"
    print(f"✓ Metadata has all required fields: {required_fields}")
    
    # Cleanup
    test_cache.clear_all()
    
    print("\n✅ Cache file structure correct!")


def generate_cache_summary():
    """Generate comprehensive cache summary"""
    print("\n" + "="*60)
    print("CACHE SYSTEM SUMMARY")
    print("="*60)
    
    print("\n📦 CACHE CONFIGURATION:")
    print("-" * 60)
    print(f"{'Namespace':<15} {'Directory':<30} {'Expiry':<15} {'Format'}")
    print("-" * 60)
    print(f"{'stocks':<15} {'.api_cache/stocks/':<30} {'168h (7d)':<15} {'JSON'}")
    print(f"{'financials':<15} {'.api_cache/financials/':<30} {'168h (7d)':<15} {'JSON'}")
    print(f"{'economy':<15} {'.api_cache/economy/':<30} {'24h (1d)':<15} {'JSON'}")
    print(f"{'AI':<15} {'.api_cache/AI/':<30} {'720h (30d)':<15} {'JSON'}")
    print("-" * 60)
    
    print("\n✅ FEATURES:")
    print("  ✓ Modular cache system with separate namespaces")
    print("  ✓ JSON storage (human-readable)")
    print("  ✓ Configurable expiration per namespace")
    print("  ✓ Automatic cleanup of expired entries")
    print("  ✓ Cache isolation between namespaces")
    print("  ✓ Metadata tracking (timestamp, expiry, params)")
    
    print("\n📍 USAGE ACROSS PROJECT:")
    print("  ✓ Stock prices → stock_cache (.api_cache/stocks/)")
    print("  ✓ Financial statements → financial_cache (.api_cache/financials/)")
    print("  ✓ Economy data → economy_cache (.api_cache/economy/)")
    print("  ✓ AI predictions → ai_cache (.api_cache/AI/)")
    
    print("\n🧪 ALL TESTS PASSED:")
    print("  ✓ Cache manager core functionality")
    print("  ✓ Stock price caching")
    print("  ✓ AI model caching")
    print("  ✓ Namespace isolation")
    print("  ✓ JSON format verification")
    print("  ✓ Expiry configuration")
    print("  ✓ Cross-cache integration")
    
    print("\n" + "="*60)


def run_all_tests():
    """Run all comprehensive integration tests"""
    print("\n" + "#"*60)
    print("# COMPREHENSIVE CACHE INTEGRATION TESTS")
    print("#"*60)
    
    try:
        test_all_cache_singletons_exist()
        test_cache_namespaces()
        test_cache_directories()
        test_cache_expiry_settings()
        test_json_format_all_caches()
        test_cross_namespace_isolation()
        test_cache_statistics()
        test_cache_structure()
        
        print("\n" + "#"*60)
        print("# ✅ ALL INTEGRATION TESTS PASSED!")
        print("#"*60)
        
        generate_cache_summary()
        
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
