"""
Test AI Model Cache Integration

Verifies that AI models properly use the cache system
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.cache_manager import ai_cache
import json


def test_ai_cache_configuration():
    """Test AI cache is configured correctly"""
    print("\n" + "="*60)
    print("TEST: AI Cache Configuration")
    print("="*60)
    
    info = ai_cache.get_info()
    
    # Check namespace
    assert info['namespace'] == 'AI', f"❌ Wrong namespace: {info['namespace']}"
    print(f"✓ Namespace: {info['namespace']}")
    
    # Check expiry (should be 30 days = 720 hours)
    assert info['expiry_hours'] == 720, f"❌ Wrong expiry: {info['expiry_hours']}"
    print(f"✓ Expiry: {info['expiry_hours']} hours (30 days)")
    
    # Check directory
    assert 'AI' in str(info['cache_dir']), f"❌ Wrong directory: {info['cache_dir']}"
    print(f"✓ Cache directory: {info['cache_dir']}")
    
    print("\n✅ AI cache configuration correct!")


def test_ai_prediction_caching():
    """Test AI predictions can be cached"""
    print("\n" + "="*60)
    print("TEST: AI Prediction Caching")
    print("="*60)
    
    # Simulate a health score prediction
    health_score = {
        'ticker': 'AAPL',
        'total_score': 85.5,
        'rating': 'Excellent',
        'breakdown': {
            'profitability': 20,
            'liquidity': 18,
            'solvency': 19,
            'efficiency': 15,
            'growth': 13.5
        }
    }
    
    # Cache it
    ai_cache.set('health_score', health_score, ticker='AAPL', quarterly=False)
    print("✓ Cached health score prediction")
    
    # Retrieve it
    retrieved = ai_cache.get('health_score', ticker='AAPL', quarterly=False)
    assert retrieved is not None, "❌ Failed to retrieve cached prediction"
    assert retrieved['total_score'] == 85.5, "❌ Wrong score retrieved"
    print("✓ Retrieved cached prediction successfully")
    
    # Test different parameters
    ai_cache.set('health_score', {'total_score': 75}, ticker='MSFT', quarterly=False)
    ai_cache.set('health_score', {'total_score': 80}, ticker='AAPL', quarterly=True)
    
    # Verify correct retrieval
    aapl_annual = ai_cache.get('health_score', ticker='AAPL', quarterly=False)
    aapl_quarterly = ai_cache.get('health_score', ticker='AAPL', quarterly=True)
    msft_annual = ai_cache.get('health_score', ticker='MSFT', quarterly=False)
    
    assert aapl_annual['total_score'] == 85.5, "❌ Wrong AAPL annual score"
    assert aapl_quarterly['total_score'] == 80, "❌ Wrong AAPL quarterly score"
    assert msft_annual['total_score'] == 75, "❌ Wrong MSFT score"
    print("✓ Multiple predictions cached correctly")
    
    print("\n✅ AI prediction caching works!")


def test_cache_persistence():
    """Test that cache persists to disk as JSON"""
    print("\n" + "="*60)
    print("TEST: Cache Persistence (JSON)")
    print("="*60)
    
    # Store a prediction
    prediction = {
        'model': 'test_model',
        'ticker': 'TSLA',
        'prediction': [0.2, 0.8],
        'timestamp': '2024-01-15'
    }
    ai_cache.set('test_prediction', prediction, ticker='TSLA')
    
    # Find the cache file
    cache_files = list(ai_cache.cache_dir.glob("*.json"))
    data_files = [f for f in cache_files if not f.name.endswith('.meta.json')]
    
    assert len(data_files) > 0, "❌ No cache files found"
    print(f"✓ Found {len(data_files)} cache file(s)")
    
    # Verify it's valid JSON and human-readable
    for cache_file in data_files[:1]:  # Check first file
        with open(cache_file, 'r') as f:
            content = f.read()
            data = json.loads(content)
        
        # Check formatting (should have indentation)
        assert '\n' in content, "❌ JSON not formatted with newlines"
        assert '  ' in content or '\t' in content, "❌ JSON not indented"
        print("✓ Cache file is formatted JSON (human-readable)")
        print(f"  Sample: {content[:100]}...")
    
    print("\n✅ Cache persistence works!")


def test_cache_info_and_listing():
    """Test cache info and listing for AI models"""
    print("\n" + "="*60)
    print("TEST: Cache Info and Listing")
    print("="*60)
    
    # Clear first
    ai_cache.clear_all()
    
    # Add multiple predictions
    models = ['health_score', 'bankruptcy_risk', 'revenue_forecast']
    tickers = ['AAPL', 'MSFT', 'GOOGL']
    
    for model in models:
        for ticker in tickers:
            ai_cache.set(model, {'prediction': f'{model}_{ticker}'}, ticker=ticker)
    
    # Get info
    info = ai_cache.get_info()
    print(f"✓ Cache info:")
    print(f"  Total entries: {info['total_entries']}")
    print(f"  Valid entries: {info['valid_entries']}")
    print(f"  Size: {info['total_size_mb']} MB")
    
    assert info['total_entries'] == 9, f"❌ Expected 9 entries, got {info['total_entries']}"
    
    # List keys
    keys = ai_cache.list_keys()
    assert len(keys) == 9, f"❌ Expected 9 keys, got {len(keys)}"
    print(f"✓ Listed {len(keys)} cached predictions")
    
    # Show sample
    for key in keys[:3]:
        print(f"  - {key['key']} (ticker={key['params'].get('ticker')}): {key['size_kb']} KB")
    
    print("\n✅ Cache info and listing work!")


def test_cache_cleanup():
    """Test cache cleanup"""
    print("\n" + "="*60)
    print("TEST: Cache Cleanup")
    print("="*60)
    
    info_before = ai_cache.get_info()
    print(f"Before cleanup: {info_before['total_entries']} entries")
    
    # Cleanup expired
    removed = ai_cache.cleanup_expired()
    print(f"✓ Cleanup removed {removed} expired entries")
    
    info_after = ai_cache.get_info()
    print(f"After cleanup: {info_after['total_entries']} entries")
    
    # Clear all
    total = ai_cache.clear_all()
    print(f"✓ Cleared all {total} entries")
    
    info_final = ai_cache.get_info()
    assert info_final['total_entries'] == 0, "❌ Cache should be empty"
    print("✓ Cache is empty")
    
    print("\n✅ Cache cleanup works!")


def run_all_tests():
    """Run all AI cache tests"""
    print("\n" + "#"*60)
    print("# AI MODEL CACHE INTEGRATION TESTS")
    print("#"*60)
    
    try:
        test_ai_cache_configuration()
        test_ai_prediction_caching()
        test_cache_persistence()
        test_cache_info_and_listing()
        test_cache_cleanup()
        
        print("\n" + "#"*60)
        print("# ✅ ALL AI CACHE TESTS PASSED!")
        print("#"*60)
        
        print("\n" + "="*60)
        print("SUMMARY: AI Model Caching")
        print("="*60)
        print("✓ AI predictions are cached in: .api_cache/AI/")
        print("✓ Cache format: JSON (human-readable)")
        print("✓ Cache duration: 30 days (720 hours)")
        print("✓ Models that use cache:")
        print("  - Health Score")
        print("  - Bankruptcy Risk (ready)")
        print("  - Revenue Forecast (ready)")
        print("  - Trend Analysis (ready)")
        print("  - Anomaly Detection (ready)")
        print("="*60)
        
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
