#!/usr/bin/env python3
"""
Test script to verify that cached JSON files have properly separated raw and clean data.

This script:
1. Deletes an existing cached JSON file
2. Runs the data collection to regenerate it
3. Loads the JSON and verifies clean/raw separation
"""

import sys
import os
import json
import subprocess
import shutil
from pathlib import Path
import time


def test_json_cache_separation(ticker="MSFT"):
    """Test that JSON cache has properly separated raw and clean data."""
    
    print(f"\n{'='*80}")
    print(f"Testing JSON Cache Raw/Clean Separation for {ticker}")
    print(f"{'='*80}\n")
    
    # Paths
    backend_dir = Path(__file__).parent / "backend"
    cache_dir = backend_dir / "api" / "cached_statements"
    cache_file = cache_dir / f"{ticker}_statements.json"
    
    # Step 1: Backup and delete existing cache
    print(f"Step 1: Preparing test environment...")
    backup_file = None
    if cache_file.exists():
        backup_file = cache_dir / f"{ticker}_statements.json.backup"
        shutil.copy(cache_file, backup_file)
        cache_file.unlink()
        print(f"  ✓ Backed up and deleted existing cache: {cache_file}")
    else:
        print(f"  ℹ No existing cache file for {ticker}")
    
    # Step 2: Run data collection
    print(f"\nStep 2: Running data collection for {ticker}...")
    data_collection_script = Path(__file__).parent / "data-collection" / "scripts" / "main.py"
    output_dir = Path(__file__).parent / "data-collection" / "scripts" / "output"
    
    try:
        result = subprocess.run(
            [
                sys.executable,
                str(data_collection_script),
                "--ticker", ticker,
                "--years", "1",
                "--output", str(output_dir)
            ],
            capture_output=True,
            text=True,
            timeout=120  # 2 minute timeout
        )
        
        if result.returncode != 0:
            print(f"  ❌ Data collection failed!")
            print(f"  Error: {result.stderr}")
            return False
        
        print(f"  ✓ Data collection completed")
        
    except subprocess.TimeoutExpired:
        print(f"  ❌ Data collection timed out!")
        return False
    except Exception as e:
        print(f"  ❌ Error running data collection: {e}")
        return False
    
    # Step 3: Load the data and create cache using the service
    print(f"\nStep 3: Creating JSON cache from collected CSV files...")
    sys.path.insert(0, str(backend_dir / "app"))
    from data_collection_service import DataCollectionService
    import asyncio
    
    service = DataCollectionService()
    
    # Load the collected data
    async def load_and_cache():
        data = await service._load_collected_data(ticker, quarterly=False)
        if data:
            service.save_to_cache(ticker, data, quarterly=False)
            return data
        return None
    
    try:
        data = asyncio.run(load_and_cache())
        if not data:
            print(f"  ❌ Failed to load collected data")
            return False
        print(f"  ✓ JSON cache created")
    except Exception as e:
        print(f"  ❌ Error creating cache: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 4: Verify the JSON cache structure
    print(f"\nStep 4: Verifying JSON cache structure...")
    
    if not cache_file.exists():
        print(f"  ❌ Cache file was not created: {cache_file}")
        return False
    
    with open(cache_file, 'r') as f:
        cached_data = json.load(f)
    
    # Check income statement
    stmt = cached_data.get('statements', {}).get('income_statement', {})
    
    if not stmt.get('available'):
        print(f"  ❌ Income statement not available in cache")
        return False
    
    clean_rows = stmt.get('row_names', [])
    clean_data = stmt.get('data', [])
    raw_rows = stmt.get('raw_row_names', [])
    raw_data = stmt.get('raw_data', [])
    
    print(f"\n  Clean view:")
    print(f"    Rows: {len(clean_rows)}")
    print(f"    Data shape: {len(clean_data)} x {len(clean_data[0]) if clean_data else 0}")
    print(f"    Sample rows: {clean_rows[:3]}")
    
    print(f"\n  Raw view:")
    print(f"    Rows: {len(raw_rows)}")
    print(f"    Data shape: {len(raw_data)} x {len(raw_data[0]) if raw_data else 0}")
    print(f"    Sample rows: {raw_rows[:3]}")
    
    # Step 5: Run validation tests
    print(f"\n{'='*80}")
    print("RESULTS:")
    print(f"{'='*80}")
    
    success = True
    
    # Test 1: Both views should exist
    if len(clean_rows) > 0 and len(raw_rows) > 0:
        print(f"✓ PASS: Both clean and raw views exist")
    else:
        print(f"❌ FAIL: Missing clean or raw view")
        success = False
    
    # Test 2: They should have different row counts
    if len(clean_rows) != len(raw_rows):
        print(f"✓ PASS: Different row counts ({len(clean_rows)} vs {len(raw_rows)})")
    else:
        print(f"❌ FAIL: Same row count - data may be duplicated")
        success = False
    
    # Test 3: Clean should contain standardized rows
    standardized_rows = ['Total revenue', 'COGS', 'Gross profit', 'Net income']
    clean_has_standardized = [row for row in standardized_rows if row in clean_rows]
    
    if len(clean_has_standardized) >= 2:
        print(f"✓ PASS: Clean view has standardized rows: {clean_has_standardized}")
    else:
        print(f"❌ FAIL: Clean view missing standardized rows")
        success = False
    
    # Test 4: Raw should primarily have different rows than clean
    clean_set = set(clean_rows)
    raw_set = set(raw_rows)
    overlap = clean_set.intersection(raw_set)
    overlap_pct = (len(overlap) / max(len(clean_set), len(raw_set))) * 100
    
    if overlap_pct < 50:  # Less than 50% overlap is good
        print(f"✓ PASS: Minimal overlap between views ({overlap_pct:.1f}%)")
    else:
        print(f"❌ FAIL: Too much overlap between views ({overlap_pct:.1f}%)")
        success = False
    
    # Test 5: Data dimensions should match row counts
    if len(clean_data) == len(clean_rows) and len(raw_data) == len(raw_rows):
        print(f"✓ PASS: Data dimensions match row counts")
    else:
        print(f"❌ FAIL: Data dimensions mismatch")
        success = False
    
    print(f"\n{'='*80}")
    if success:
        print("✅ ALL TESTS PASSED - JSON cache has properly separated data!")
    else:
        print("❌ TESTS FAILED - JSON cache data is still mixed!")
    print(f"{'='*80}\n")
    
    # Step 6: Cleanup and restore backup
    print(f"Step 5: Cleaning up...")
    if backup_file and backup_file.exists():
        # Keep the new cache file, but also keep backup for reference
        print(f"  ℹ Backup saved at: {backup_file}")
        print(f"  ℹ New cache saved at: {cache_file}")
    
    # Clean up output directory
    ticker_output_dir = output_dir / ticker
    if ticker_output_dir.exists():
        shutil.rmtree(ticker_output_dir)
        print(f"  ✓ Cleaned up output directory")
    
    return success


if __name__ == "__main__":
    ticker = sys.argv[1] if len(sys.argv) > 1 else "MSFT"
    success = test_json_cache_separation(ticker)
    sys.exit(0 if success else 1)
