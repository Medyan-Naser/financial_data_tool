"""
Master Test Runner for All Tabs

Runs comprehensive tests for:
- Stock Tab
- Macro Tab  
- AI Tab

Usage:
    python tests/test_all_tabs.py

This will run all tests and provide a comprehensive summary.
Tests use caching to avoid API rate limits.
"""

import sys
import os
import time
from datetime import datetime

# Add tests to path
sys.path.insert(0, os.path.dirname(__file__))

# Import all test modules
import test_stock_tab
import test_macro_tab
import test_ai_tab


def print_banner(text):
    """Print a formatted banner"""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70 + "\n")


def run_all_tab_tests():
    """Run all tab tests and provide summary"""
    
    print("\n" + "#"*70)
    print("#" + " "*68 + "#")
    print("#" + "  COMPREHENSIVE TAB TESTS - FINANCIAL DATA TOOL".center(68) + "#")
    print("#" + " "*68 + "#")
    print("#"*70)
    
    print("\n📋 Test Coverage:")
    print("  ✓ Stock Tab - Price data, financials, charts, caching")
    print("  ✓ Macro Tab - Currency, crypto, metals, GDP, caching")
    print("  ✓ AI Tab - LSTM forecasts, volatility, caching")
    
    print("\n⚠️  Prerequisites:")
    print("  • Backend server must be running on http://localhost:8000")
    print("  • Tests use cached data when available to avoid API limits")
    print("  • AI tests may take several minutes on first run")
    
    print("\n⏱  Starting in 3 seconds...")
    time.sleep(3)
    
    results = {}
    start_time = time.time()
    
    # Run Stock Tab Tests
    print_banner("STOCK TAB TESTS")
    try:
        results['stock'] = test_stock_tab.run_all_stock_tests()
    except Exception as e:
        print(f"❌ Stock tests failed with exception: {e}")
        results['stock'] = False
    
    # Run Macro Tab Tests
    print_banner("MACRO TAB TESTS")
    try:
        results['macro'] = test_macro_tab.run_all_macro_tests()
    except Exception as e:
        print(f"❌ Macro tests failed with exception: {e}")
        results['macro'] = False
    
    # Run AI Tab Tests
    print_banner("AI TAB TESTS")
    try:
        results['ai'] = test_ai_tab.run_all_ai_tests()
    except Exception as e:
        print(f"❌ AI tests failed with exception: {e}")
        results['ai'] = False
    
    # Calculate total time
    total_time = time.time() - start_time
    
    # Print Final Summary
    print("\n" + "#"*70)
    print("#" + " "*68 + "#")
    print("#" + "  FINAL SUMMARY".center(68) + "#")
    print("#" + " "*68 + "#")
    print("#"*70)
    
    print("\n📊 Test Results by Tab:")
    print(f"  {'Stock Tab:':<20} {'✅ PASSED' if results['stock'] else '❌ FAILED'}")
    print(f"  {'Macro Tab:':<20} {'✅ PASSED' if results['macro'] else '❌ FAILED'}")
    print(f"  {'AI Tab:':<20} {'✅ PASSED' if results['ai'] else '❌ FAILED'}")
    
    passed_count = sum(1 for r in results.values() if r)
    total_count = len(results)
    
    print(f"\n📈 Overall: {passed_count}/{total_count} test suites passed")
    print(f"⏱  Total execution time: {total_time:.2f} seconds ({total_time/60:.1f} minutes)")
    
    # Cache Summary
    print("\n💾 Cache Summary:")
    try:
        from app.cache_manager import stock_cache, macro_cache, ai_cache
        
        for name, cache in [('Stock', stock_cache), ('Macro', macro_cache), ('AI', ai_cache)]:
            info = cache.get_info()
            print(f"  {name:<10} {info['total_entries']:>4} entries, {info['total_size_mb']:.2f} MB")
    except:
        print("  Unable to retrieve cache information")
    
    # Final verdict
    print("\n" + "="*70)
    if all(results.values()):
        print("  ✅ ALL TESTS PASSED! 🎉")
        print("  Your application is working correctly across all tabs.")
    else:
        print("  ⚠️  SOME TESTS FAILED")
        print("  Check the output above for details.")
    print("="*70 + "\n")
    
    return all(results.values())


if __name__ == "__main__":
    success = run_all_tab_tests()
    sys.exit(0 if success else 1)
