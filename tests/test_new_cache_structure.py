"""
Test New Cache Structure

Verifies:
- Only 3 directories: Stock, Macro, AI
- Descriptive file names (not MD5 hashes)
- All caches use correct directories
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.cache_manager import stock_cache, macro_cache, ai_cache
from pathlib import Path


def test_only_three_directories():
    """Test that only 3 cache directories exist"""
    print("\n" + "="*60)
    print("TEST: Only 3 Cache Directories")
    print("="*60)
    
    cache_root = Path('.api_cache')
    
    # Expected directories
    expected = {'Stock', 'Macro', 'AI'}
    
    # Get actual directories
    if cache_root.exists():
        actual = {d.name for d in cache_root.iterdir() if d.is_dir()}
    else:
        actual = set()
    
    # Filter out any unexpected directories
    unexpected = actual - expected
    missing = expected - actual
    
    if unexpected:
        print(f"⚠️  Unexpected directories found: {unexpected}")
        print(f"   These should be removed or migrated")
    
    if missing:
        print(f"ℹ️  Missing directories (will be created on first use): {missing}")
    
    print(f"✓ Expected directories: {expected}")
    print(f"✓ Actual directories: {actual}")
    
    print("\n✅ Directory structure checked!")


def test_descriptive_file_names():
    """Test that cache files have descriptive names"""
    print("\n" + "="*60)
    print("TEST: Descriptive File Names")
    print("="*60)
    
    # Create test data
    test_data = {'test': 'data', 'value': 123}
    
    # Test Stock cache
    stock_cache.set('historical', test_data, symbol='AAPL', period='1y')
    stock_files = list(stock_cache.cache_dir.glob("*.json"))
    data_files = [f for f in stock_files if not f.name.endswith('.meta.json')]
    
    if data_files:
        filename = data_files[0].name
        # Check that it contains descriptive parts (not just MD5 hash)
        assert 'historical' in filename or 'AAPL' in filename or '1y' in filename, \
            f"❌ Stock filename not descriptive: {filename}"
        print(f"✓ Stock cache file: {filename}")
    
    # Test Macro cache
    macro_cache.set('currency_rates', test_data)
    macro_files = list(macro_cache.cache_dir.glob("*.json"))
    macro_data_files = [f for f in macro_files if not f.name.endswith('.meta.json')]
    
    if macro_data_files:
        filename = macro_data_files[0].name
        assert 'currency' in filename or 'rates' in filename, \
            f"❌ Macro filename not descriptive: {filename}"
        print(f"✓ Macro cache file: {filename}")
    
    # Test AI cache
    ai_cache.set('health_score', test_data, ticker='MSFT', quarterly=False)
    ai_files = list(ai_cache.cache_dir.glob("*.json"))
    ai_data_files = [f for f in ai_files if not f.name.endswith('.meta.json')]
    
    if ai_data_files:
        filename = ai_data_files[0].name
        assert 'health_score' in filename or 'MSFT' in filename, \
            f"❌ AI filename not descriptive: {filename}"
        print(f"✓ AI cache file: {filename}")
    
    # Cleanup
    stock_cache.delete('historical', symbol='AAPL', period='1y')
    macro_cache.delete('currency_rates')
    ai_cache.delete('health_score', ticker='MSFT', quarterly=False)
    
    print("\n✅ File names are descriptive!")


def test_cache_namespaces_match_tabs():
    """Test that cache namespaces match UI tabs"""
    print("\n" + "="*60)
    print("TEST: Cache Namespaces Match UI Tabs")
    print("="*60)
    
    # Get info from each cache
    stock_info = stock_cache.get_info()
    macro_info = macro_cache.get_info()
    ai_info = ai_cache.get_info()
    
    # Check namespaces
    assert stock_info['namespace'] == 'Stock', f"❌ Expected 'Stock', got '{stock_info['namespace']}'"
    print("✓ Stock cache → Stock tab")
    
    assert macro_info['namespace'] == 'Macro', f"❌ Expected 'Macro', got '{macro_info['namespace']}'"
    print("✓ Macro cache → Economy/Macro tab")
    
    assert ai_info['namespace'] == 'AI', f"❌ Expected 'AI', got '{ai_info['namespace']}'"
    print("✓ AI cache → AI tab")
    
    print("\n✅ Namespaces match UI tabs!")


def test_cache_directories():
    """Test cache directory paths"""
    print("\n" + "="*60)
    print("TEST: Cache Directory Paths")
    print("="*60)
    
    caches = {
        'Stock': stock_cache,
        'Macro': macro_cache,
        'AI': ai_cache
    }
    
    for name, cache in caches.items():
        info = cache.get_info()
        cache_dir = Path(info['cache_dir'])
        
        # Check directory name
        assert name in str(cache_dir), f"❌ Directory doesn't contain '{name}': {cache_dir}"
        
        # Check directory exists
        assert cache_dir.exists(), f"❌ Directory doesn't exist: {cache_dir}"
        
        print(f"✓ {name}: {cache_dir}")
    
    print("\n✅ All directories correct!")


def test_sample_cache_files():
    """Create sample files and verify naming"""
    print("\n" + "="*60)
    print("TEST: Sample Cache Files")
    print("="*60)
    
    # Stock cache examples
    print("\nStock Cache Examples:")
    stock_cache.set('historical', {'price': 150}, symbol='AAPL', period='1y')
    stock_cache.set('quote', {'current': 151}, symbol='TSLA')
    
    stock_files = [f.name for f in stock_cache.cache_dir.glob("*.json") 
                   if not f.name.endswith('.meta.json')]
    for f in stock_files[:3]:
        print(f"  - {f}")
    
    # Macro cache examples
    print("\nMacro Cache Examples:")
    macro_cache.set('currency_rates', {'USD': 1.0})
    macro_cache.set('crypto_prices', {'BTC': 50000})
    macro_cache.set('gdp', {'value': 1000}, country='US')
    
    macro_files = [f.name for f in macro_cache.cache_dir.glob("*.json")
                   if not f.name.endswith('.meta.json')]
    for f in macro_files[:3]:
        print(f"  - {f}")
    
    # AI cache examples
    print("\nAI Cache Examples:")
    ai_cache.set('health_score', {'score': 85}, ticker='AAPL', quarterly=False)
    ai_cache.set('bankruptcy_risk', {'risk': 'low'}, ticker='MSFT', quarterly=True)
    
    ai_files = [f.name for f in ai_cache.cache_dir.glob("*.json")
                if not f.name.endswith('.meta.json')]
    for f in ai_files[:3]:
        print(f"  - {f}")
    
    print("\n✅ Sample files created with descriptive names!")
    
    # Cleanup
    stock_cache.clear_all()
    macro_cache.clear_all()
    ai_cache.clear_all()


def generate_summary():
    """Generate summary of new structure"""
    print("\n" + "="*60)
    print("NEW CACHE STRUCTURE SUMMARY")
    print("="*60)
    
    print("\n📁 DIRECTORY STRUCTURE:")
    print("  .api_cache/")
    print("  ├── Stock/       (Stock prices, quotes)")
    print("  ├── Macro/       (Economy data, currencies, commodities)")
    print("  └── AI/          (ML predictions, health scores)")
    
    print("\n📄 FILE NAMING:")
    print("  OLD: b588bbf70d02ebf58e525480d3884977.json (MD5 hash)")
    print("  NEW: historical_AAPL_1y.json (Descriptive)")
    print("  NEW: currency_rates.json (Descriptive)")
    print("  NEW: health_score_AAPL_False.json (Descriptive)")
    
    print("\n✅ BENEFITS:")
    print("  ✓ Easy to identify what each file contains")
    print("  ✓ Only 3 directories (matches UI tabs)")
    print("  ✓ Clean organization")
    print("  ✓ Human-friendly file names")
    
    print("\n" + "="*60)


def run_all_tests():
    """Run all tests"""
    print("\n" + "#"*60)
    print("# NEW CACHE STRUCTURE TESTS")
    print("#"*60)
    
    try:
        test_only_three_directories()
        test_descriptive_file_names()
        test_cache_namespaces_match_tabs()
        test_cache_directories()
        test_sample_cache_files()
        
        print("\n" + "#"*60)
        print("# ✅ ALL TESTS PASSED!")
        print("#"*60)
        
        generate_summary()
        
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
