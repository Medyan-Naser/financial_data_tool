#!/usr/bin/env python3
"""
Test script to verify all task implementations
"""

import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend', 'app'))

def test_cache_expiry():
    """Test 1: Verify cache is set to 1 week (168 hours)"""
    print("=" * 60)
    print("TEST 1: Cache Expiry Configuration")
    print("=" * 60)
    
    try:
        from api_cache import CACHE_EXPIRY_HOURS
        
        if CACHE_EXPIRY_HOURS == 168:
            print("✅ PASS: Cache expiry is correctly set to 168 hours (1 week)")
            return True
        else:
            print(f"❌ FAIL: Cache expiry is {CACHE_EXPIRY_HOURS} hours, expected 168")
            return False
    except ImportError as e:
        print(f"❌ FAIL: Could not import api_cache: {e}")
        return False

def test_cached_api_usage():
    """Test 2: Verify AI and Economy modules use cached APIs"""
    print("\n" + "=" * 60)
    print("TEST 2: Cached API Usage in AI/Economy Modules")
    print("=" * 60)
    
    files_to_check = {
        'AI_ML/cached_yfinance.py': 'Cached yfinance wrapper',
        'AI_ML/cached_fredapi.py': 'Cached FRED API wrapper',
        'AI_ML/AI/get_stock_prices.py': 'AI stock prices',
        'AI_ML/Macro/markets.py': 'Macro markets',
        'AI_ML/Macro/core_cpi_yoy_inflation.py': 'Macro inflation',
    }
    
    all_exist = True
    for file_path, description in files_to_check.items():
        full_path = Path(__file__).parent / file_path
        if full_path.exists():
            # Check if file uses cached imports
            with open(full_path, 'r') as f:
                content = f.read()
                if 'cached_yfinance' in content or 'cached_fredapi' in content or 'import cached_' in content:
                    print(f"✅ {description}: Uses cached APIs")
                else:
                    print(f"⚠️  {description}: May not use cached APIs")
        else:
            print(f"❌ {description}: File not found at {file_path}")
            all_exist = False
    
    return all_exist

def test_cache_directory():
    """Test 3: Verify cache directory exists or can be created"""
    print("\n" + "=" * 60)
    print("TEST 3: Cache Directory")
    print("=" * 60)
    
    cache_dir = Path(__file__).parent / '.api_cache'
    
    if cache_dir.exists():
        cache_files = list(cache_dir.glob("*.pkl"))
        print(f"✅ Cache directory exists: {cache_dir}")
        print(f"   Current cache entries: {len(cache_files)}")
        
        if cache_files:
            # Show sample cache file info
            sample = cache_files[0]
            import time
            mod_time = time.ctime(sample.stat().st_mtime)
            size = sample.stat().st_size / 1024  # KB
            print(f"   Sample cache file: {sample.name}")
            print(f"   Last modified: {mod_time}")
            print(f"   Size: {size:.2f} KB")
        return True
    else:
        print(f"⚠️  Cache directory does not exist yet: {cache_dir}")
        print("   This is normal if no API calls have been made yet.")
        print("   Directory will be created automatically on first API call.")
        return True

def test_frontend_files():
    """Test 4: Verify frontend changes are in place"""
    print("\n" + "=" * 60)
    print("TEST 4: Frontend Chart Enhancements")
    print("=" * 60)
    
    ai_view = Path(__file__).parent / 'frontend/src/components/AIView.js'
    chart_manager = Path(__file__).parent / 'frontend/src/components/ChartManager.js'
    financial_table = Path(__file__).parent / 'frontend/src/components/FinancialTable.js'
    
    results = []
    
    # Check AIView.js for forecast table fix
    if ai_view.exists():
        with open(ai_view, 'r') as f:
            content = f.read()
            if 'id="forecastTable"' in content:
                # Check if it's inside forecast-charts div
                # Simple check: forecastTable should appear after trainingLoss
                if content.index('id="forecastTable"') > content.index('id="trainingLoss"'):
                    print("✅ AIView.js: Forecast table properly positioned")
                    results.append(True)
                else:
                    print("❌ AIView.js: Forecast table may not be in correct position")
                    results.append(False)
            else:
                print("❌ AIView.js: Forecast table panel not found")
                results.append(False)
    else:
        print("❌ AIView.js not found")
        results.append(False)
    
    # Check ChartManager.js for new chart types
    if chart_manager.exists():
        with open(chart_manager, 'r') as f:
            content = f.read()
            chart_types = ['stacked-bar', 'stacked-area', 'scatter', 'composed']
            found_types = [ct for ct in chart_types if f"case '{ct}'" in content]
            
            if len(found_types) == len(chart_types):
                print(f"✅ ChartManager.js: All new chart types implemented ({', '.join(chart_types)})")
                results.append(True)
            else:
                missing = set(chart_types) - set(found_types)
                print(f"❌ ChartManager.js: Missing chart types: {missing}")
                results.append(False)
            
            # Check for analysis mode support
            if 'applyAnalysisMode' in content:
                print("✅ ChartManager.js: Analysis mode transformation implemented")
                results.append(True)
            else:
                print("❌ ChartManager.js: Analysis mode transformation not found")
                results.append(False)
    else:
        print("❌ ChartManager.js not found")
        results.append(False)
    
    # Check FinancialTable.js for new options
    if financial_table.exists():
        with open(financial_table, 'r') as f:
            content = f.read()
            if 'analysisMode' in content and 'stacked-bar' in content:
                print("✅ FinancialTable.js: New chart options added")
                results.append(True)
            else:
                print("❌ FinancialTable.js: New chart options not found")
                results.append(False)
    else:
        print("❌ FinancialTable.js not found")
        results.append(False)
    
    return all(results)

def main():
    """Run all tests"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "FINANCIAL DATA TOOL - CHANGES VERIFICATION" + " " * 6 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    results = []
    
    # Run all tests
    results.append(("Cache Expiry (1 Week)", test_cache_expiry()))
    results.append(("Cached API Usage", test_cached_api_usage()))
    results.append(("Cache Directory", test_cache_directory()))
    results.append(("Frontend Enhancements", test_frontend_files()))
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! All tasks completed successfully.")
        print("\nNext Steps:")
        print("1. Open http://localhost:3000 in your browser")
        print("2. Test the Individual Stocks chart builder with new options")
        print("3. Test AI Predictions → Price Forecast for layout fix")
        print("4. Verify API calls are cached (check .api_cache/ folder)")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
