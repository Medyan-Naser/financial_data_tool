#!/usr/bin/env python3
"""
Script to regenerate all cached JSON files with properly separated raw/clean data.

This will:
1. Find all existing cached JSON files
2. For each ticker, re-run data collection
3. Replace the old cache with the new properly-separated data
"""

import sys
import os
import json
import subprocess
import shutil
from pathlib import Path
import time


def get_existing_tickers():
    """Get list of all tickers that have cached data."""
    cache_dir = Path(__file__).parent / "backend" / "api" / "cached_statements"
    tickers = set()
    
    for file in cache_dir.glob("*_statements.json"):
        # Skip quarterly and backup files
        if "_quarterly_" in file.name or ".backup" in file.name:
            continue
        
        # Extract ticker (e.g., AAPL_statements.json -> AAPL)
        ticker = file.stem.replace("_statements", "")
        tickers.add(ticker)
    
    return sorted(list(tickers))


def regenerate_cache(ticker, dry_run=False):
    """Regenerate cache for a single ticker."""
    print(f"\n{'='*60}")
    print(f"Processing {ticker}")
    print(f"{'='*60}")
    
    cache_dir = Path(__file__).parent / "backend" / "api" / "cached_statements"
    cache_file = cache_dir / f"{ticker}_statements.json"
    backup_file = cache_dir / f"{ticker}_statements.json.old"
    
    # Check if cache exists and has the bug
    if cache_file.exists():
        with open(cache_file, 'r') as f:
            data = json.load(f)
        
        # Check income statement for the bug
        stmt = data.get('statements', {}).get('income_statement', {})
        clean_rows = len(stmt.get('row_names', []))
        raw_rows = len(stmt.get('raw_row_names', []))
        
        print(f"Current state:")
        print(f"  Clean rows: {clean_rows}")
        print(f"  Raw rows: {raw_rows}")
        
        # If raw_rows is 0 or if clean_rows is suspiciously large, regenerate
        needs_regen = False
        if raw_rows == 0:
            print(f"  ⚠️  No raw data - needs regeneration")
            needs_regen = True
        elif clean_rows > 25:  # Typical clean view has ~17 rows
            print(f"  ⚠️  Clean view has too many rows - may include raw data")
            needs_regen = True
        else:
            print(f"  ✓ Looks good - skipping")
            return True
        
        if not needs_regen:
            return True
    else:
        print(f"  ℹ No existing cache")
        return True
    
    if dry_run:
        print(f"  [DRY RUN] Would regenerate cache for {ticker}")
        return True
    
    # Backup old cache
    if cache_file.exists():
        shutil.copy(cache_file, backup_file)
        print(f"  ✓ Backed up old cache")
    
    # Run data collection
    print(f"  Running data collection...")
    data_collection_script = Path(__file__).parent / "data-collection" / "scripts" / "main.py"
    output_dir = Path(__file__).parent / "data-collection" / "scripts" / "output"
    
    try:
        result = subprocess.run(
            [
                sys.executable,
                str(data_collection_script),
                "--ticker", ticker,
                "--years", "10",
                "--output", str(output_dir)
            ],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode != 0:
            print(f"  ❌ Data collection failed!")
            print(f"  Error: {result.stderr[:200]}")
            return False
        
        print(f"  ✓ Data collected")
        
    except subprocess.TimeoutExpired:
        print(f"  ❌ Timed out!")
        return False
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False
    
    # Create cache from CSV files
    print(f"  Creating JSON cache...")
    sys.path.insert(0, str(Path(__file__).parent / "backend" / "app"))
    from data_collection_service import DataCollectionService
    import asyncio
    
    service = DataCollectionService()
    
    async def load_and_cache():
        data = await service._load_collected_data(ticker, quarterly=False)
        if data:
            service.save_to_cache(ticker, data, quarterly=False)
            return data
        return None
    
    try:
        data = asyncio.run(load_and_cache())
        if not data:
            print(f"  ❌ Failed to create cache")
            return False
        
        # Verify the new cache
        stmt = data.get('statements', {}).get('income_statement', {})
        new_clean_rows = len(stmt.get('row_names', []))
        new_raw_rows = len(stmt.get('raw_row_names', []))
        
        print(f"  ✓ New cache created:")
        print(f"    Clean rows: {new_clean_rows}")
        print(f"    Raw rows: {new_raw_rows}")
        
        # Clean up CSV files
        ticker_output_dir = output_dir / ticker
        if ticker_output_dir.exists():
            shutil.rmtree(ticker_output_dir)
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error creating cache: {e}")
        return False


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Regenerate all cached JSON files')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without doing it')
    parser.add_argument('--ticker', type=str, help='Regenerate only this ticker')
    args = parser.parse_args()
    
    print(f"\n{'='*60}")
    print("Cached JSON Regeneration Tool")
    print(f"{'='*60}")
    
    if args.ticker:
        tickers = [args.ticker.upper()]
    else:
        tickers = get_existing_tickers()
    
    print(f"\nFound {len(tickers)} tickers to process:")
    print(f"  {', '.join(tickers)}")
    
    if args.dry_run:
        print(f"\n⚠️  DRY RUN MODE - No changes will be made\n")
    
    if not args.dry_run:
        confirm = input(f"\nProceed with regeneration? (yes/no): ")
        if confirm.lower() != 'yes':
            print("Cancelled")
            return
    
    success_count = 0
    skip_count = 0
    fail_count = 0
    
    for ticker in tickers:
        try:
            result = regenerate_cache(ticker, dry_run=args.dry_run)
            if result:
                if not args.dry_run:
                    success_count += 1
                else:
                    skip_count += 1
            else:
                fail_count += 1
        except KeyboardInterrupt:
            print(f"\n\nInterrupted by user")
            break
        except Exception as e:
            print(f"\n  ❌ Unexpected error: {e}")
            fail_count += 1
    
    print(f"\n{'='*60}")
    print("Summary:")
    print(f"{'='*60}")
    if args.dry_run:
        print(f"  Would regenerate: {skip_count}")
    else:
        print(f"  Success: {success_count}")
        print(f"  Skipped: {skip_count}")
        print(f"  Failed: {fail_count}")
    print()


if __name__ == "__main__":
    main()
