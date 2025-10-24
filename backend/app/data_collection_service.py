"""
Data Collection Service with Caching and Progress Tracking

This service manages the collection of financial statement data from SEC Edgar,
including caching, progress tracking, and file management.
"""

import os
import sys
import json
import subprocess
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, AsyncGenerator
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Paths
BASE_DIR = Path(__file__).parent.parent
CACHE_DIR = BASE_DIR / "api" / "cached_statements"
DATA_COLLECTION_SCRIPT = BASE_DIR.parent / "data-collection" / "scripts" / "main.py"

# Ensure cache directory exists
CACHE_DIR.mkdir(parents=True, exist_ok=True)


class DataCollectionService:
    """Service for collecting and caching financial statement data."""
    
    def __init__(self):
        self.cache_dir = CACHE_DIR
        self.collection_script = DATA_COLLECTION_SCRIPT
        
    def get_cache_path(self, ticker: str, quarterly: bool = False) -> Path:
        """Get the cache file path for a ticker."""
        suffix = "_quarterly" if quarterly else ""
        return self.cache_dir / f"{ticker.upper()}{suffix}_statements.json"
    
    def is_cached(self, ticker: str, quarterly: bool = False) -> bool:
        """Check if ticker data is cached."""
        cache_path = self.get_cache_path(ticker, quarterly)
        return cache_path.exists()
    
    def load_from_cache(self, ticker: str, quarterly: bool = False) -> Optional[Dict]:
        """Load cached data for a ticker."""
        cache_path = self.get_cache_path(ticker, quarterly)
        if not cache_path.exists():
            return None
        
        try:
            with open(cache_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading cache for {ticker}: {e}")
            return None
    
    def save_to_cache(self, ticker: str, data: Dict, quarterly: bool = False) -> bool:
        """Save data to cache."""
        cache_path = self.get_cache_path(ticker, quarterly)
        
        try:
            # Add metadata
            data['cached_at'] = datetime.now().isoformat()
            data['ticker'] = ticker.upper()
            
            with open(cache_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            period_label = "quarterly" if quarterly else "annual"
            logger.info(f"Saved {period_label} data to cache for {ticker}")
            return True
        except Exception as e:
            logger.error(f"Error saving to cache for {ticker}: {e}")
            return False
    
    def delete_cache(self, ticker: str) -> bool:
        """Delete cached data for a ticker."""
        cache_path = self.get_cache_path(ticker)
        
        try:
            if cache_path.exists():
                cache_path.unlink()
                logger.info(f"Deleted cache for {ticker}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting cache for {ticker}: {e}")
            return False
    
    async def collect_data_with_progress(
        self, 
        ticker: str, 
        years: int = 15,
        force_refresh: bool = False,
        cleanup_csv: bool = True,
        quarterly: bool = False
    ) -> AsyncGenerator[str, None]:
        """
        Collect financial data with progress updates.
        
        Yields progress updates as Server-Sent Events (SSE) format.
        """
        ticker = ticker.upper()
        
        # Check cache first
        if not force_refresh and self.is_cached(ticker, quarterly):
            yield f"data: {json.dumps({'status': 'cached', 'message': 'Loading from cache...', 'progress': 100})}\n\n"
            cached_data = self.load_from_cache(ticker, quarterly)
            if cached_data:
                yield f"data: {json.dumps({'status': 'complete', 'data': cached_data})}\n\n"
                return
        
        # Start collection
        yield f"data: {json.dumps({'status': 'starting', 'message': f'Starting data collection for {ticker}...', 'progress': 5})}\n\n"
        await asyncio.sleep(0.1)
        
        # Check if script exists
        if not self.collection_script.exists():
            error_msg = f"Data collection script not found at {self.collection_script}"
            logger.error(error_msg)
            yield f"data: {json.dumps({'status': 'error', 'message': error_msg})}\n\n"
            return
        
        # Run the data collection script
        yield f"data: {json.dumps({'status': 'collecting', 'message': f'Fetching {years} years of data from SEC Edgar...', 'progress': 10})}\n\n"
        await asyncio.sleep(0.1)
        
        try:
            # Build command with output directory
            output_dir = self.collection_script.parent / "output"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            cmd = [
                sys.executable,
                str(self.collection_script),
                "--ticker", ticker,
                "--years", str(years),
                "--output", str(output_dir)
            ]
            
            if quarterly:
                cmd.append("--quarterly")
            
            # Run subprocess and capture output
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.collection_script.parent)
            )
            
            # Track progress
            current_progress = 15
            years_processed = 0
            import re
            # Match "Processing filing X/Y: date" pattern
            filing_pattern = re.compile(r'Processing filing (\d+)/(\d+): (.+)')
            
            # Read output line by line
            line_count = 0
            async for line in process.stdout:
                line_text = line.decode().strip()
                line_count += 1
                
                # Update progress based on "Processing filing" messages
                filing_match = filing_pattern.search(line_text)
                if filing_match:
                    current_filing = int(filing_match.group(1))
                    total_filings = int(filing_match.group(2))
                    filing_date = filing_match.group(3)
                    
                    # Calculate progress: 15% to 80% based on filing number
                    current_progress = 15 + int((current_filing / total_filings) * 65)
                    
                    yield f"data: {json.dumps({'status': 'collecting', 'message': f'Processing filing {current_filing}/{total_filings}: {filing_date}', 'progress': current_progress})}\n\n"
                    await asyncio.sleep(0.05)
                elif "Processing Income Statement" in line_text:
                    yield f"data: {json.dumps({'status': 'collecting', 'message': 'Processing Income Statement...', 'progress': current_progress})}\n\n"
                    await asyncio.sleep(0.02)
                elif "Processing Balance Sheet" in line_text:
                    yield f"data: {json.dumps({'status': 'collecting', 'message': 'Processing Balance Sheet...', 'progress': current_progress})}\n\n"
                    await asyncio.sleep(0.02)
                elif "Processing Cash Flow" in line_text:
                    yield f"data: {json.dumps({'status': 'collecting', 'message': 'Processing Cash Flow...', 'progress': current_progress})}\n\n"
                    await asyncio.sleep(0.02)
                
                # Log important lines
                if line_count % 5 == 0 or any(kw in line_text.lower() for kw in ['error', 'warning', 'saved', 'complete']):
                    logger.info(f"[{ticker}] {line_text}")
            
            # Wait for process to complete
            await process.wait()
            
            if process.returncode != 0:
                stderr = await process.stderr.read()
                error_msg = stderr.decode().strip()
                logger.error(f"Data collection failed for {ticker}: {error_msg}")
                yield f"data: {json.dumps({'status': 'error', 'message': f'Collection failed: {error_msg}'})}\n\n"
                return
            
            yield f"data: {json.dumps({'status': 'processing', 'message': 'Processing and formatting data...', 'progress': 85})}\n\n"
            await asyncio.sleep(0.5)
            
            # Load the collected data from the old financials directory
            # and convert it to our cache format
            financial_data = await self._load_collected_data(ticker, quarterly)
            
            if not financial_data:
                yield f"data: {json.dumps({'status': 'error', 'message': 'No data was collected. Ticker may not exist.'})}\n\n"
                return
            
            yield f"data: {json.dumps({'status': 'saving', 'message': 'Saving to cache...', 'progress': 95})}\n\n"
            await asyncio.sleep(0.2)
            
            # Save to cache
            self.save_to_cache(ticker, financial_data, quarterly)
            
            # Optionally clean up CSV files after successful caching
            if cleanup_csv:
                ticker_output_dir = BASE_DIR.parent / "data-collection" / "scripts" / "output" / ticker.upper()
                if ticker_output_dir.exists():
                    try:
                        import shutil
                        shutil.rmtree(ticker_output_dir)
                        logger.info(f"Cleaned up CSV files for {ticker} at {ticker_output_dir}")
                    except Exception as e:
                        logger.warning(f"Could not clean up CSV files for {ticker}: {e}")
            
            yield f"data: {json.dumps({'status': 'complete', 'message': 'Data collection complete!', 'progress': 100, 'data': financial_data})}\n\n"
            
        except Exception as e:
            error_msg = f"Unexpected error during collection: {str(e)}"
            logger.error(error_msg)
            yield f"data: {json.dumps({'status': 'error', 'message': error_msg})}\n\n"
    
    async def _load_collected_data(self, ticker: str, quarterly: bool = False) -> Optional[Dict]:
        """Load data from the data collection output directory and format it."""
        # The output structure is: output/{TICKER}/{statement}_{annual|quarterly}.csv
        ticker_output_dir = BASE_DIR.parent / "data-collection" / "scripts" / "output" / ticker.upper()
        
        if not ticker_output_dir.exists():
            logger.warning(f"No output directory found for {ticker} at: {ticker_output_dir}")
            return None
        
        period_suffix = "quarterly" if quarterly else "annual"
        logger.info(f"Loading {period_suffix} collected data for {ticker} from: {ticker_output_dir}")
        
        statements_data = {
            "income_statement": None,
            "balance_sheet": None,
            "cash_flow": None
        }
        
        statement_types = [
            ("income_statement", "income_statement"),
            ("balance_sheet", "balance_sheet"),
            ("cash_flow", "cash_flow")
        ]
        
        has_data = False
        
        for stmt_key, file_base in statement_types:
            # Look for files matching the pattern: {statement}_*_{annual|quarterly}.csv
            # e.g., income_statement_2024-12-31_annual.csv or income_statement_2024-09-30_quarterly.csv
            import glob
            pattern = str(ticker_output_dir / f"{file_base}_*_{period_suffix}.csv")
            matching_files = glob.glob(pattern)
            
            if matching_files:
                # We have multiple files (one per year), merge them
                all_dfs = []
                for file_path in sorted(matching_files):
                    try:
                        import pandas as pd
                        df = pd.read_csv(file_path, index_col=0)
                        all_dfs.append(df)
                    except Exception as e:
                        logger.error(f"Error loading {file_path}: {e}")
                
                if all_dfs:
                    # Merge all DataFrames horizontally (combine columns/years)
                    merged_df = pd.concat(all_dfs, axis=1)
                    
                    # Remove duplicate columns (keep first occurrence of each date)
                    # This happens because each filing contains multiple comparative years
                    merged_df = merged_df.loc[:, ~merged_df.columns.duplicated(keep='first')]
                    
                    # Sort columns by date (most recent first)
                    try:
                        sorted_cols = sorted(merged_df.columns, key=lambda x: pd.to_datetime(x), reverse=True)
                        merged_df = merged_df[sorted_cols]
                    except:
                        pass  # If dates can't be parsed, keep original order
                    
                    # Format data
                    columns = merged_df.columns.tolist()
                    row_names = merged_df.index.tolist()
                    data = merged_df.values.tolist()
                    
                    statements_data[stmt_key] = {
                        "available": True,
                        "columns": columns,
                        "row_names": row_names,
                        "data": data,
                        "file_source": f"{len(matching_files)} files merged"
                    }
                    
                    has_data = True
                    logger.info(f"Loaded {stmt_key} for {ticker} from {len(matching_files)} files")
            else:
                # Try old single-file pattern
                file_path = ticker_output_dir / f"{file_base}_annual.csv"
                
                if file_path.exists():
                    try:
                        import pandas as pd
                        df = pd.read_csv(file_path)
                        
                        # Format data
                        columns = df.columns[1:].tolist()
                        row_names = df.iloc[:, 0].tolist()
                        data = df.iloc[:, 1:].values.tolist()
                        
                        statements_data[stmt_key] = {
                            "available": True,
                            "columns": columns,
                            "row_names": row_names,
                            "data": data,
                            "file_source": str(file_path)
                        }
                        
                        has_data = True
                        logger.info(f"Loaded {stmt_key} for {ticker} from {file_path}")
                        
                    except Exception as e:
                        logger.error(f"Error loading {file_path}: {e}")
        
        # Fill in missing statements with empty data
        for stmt_key in statements_data:
            if statements_data[stmt_key] is None:
                statements_data[stmt_key] = {
                    "available": False,
                    "columns": [],
                    "row_names": [],
                    "data": []
                }
        
        if not has_data:
            return None
        
        # Detect period coverage by checking column headers
        period_type = "quarterly" if quarterly else "annual"
        
        return {
            "ticker": ticker.upper(),
            "currency": "USD",  # Default to USD for US companies (SEC EDGAR)
            "period_type": period_type,
            "statements": statements_data,
            "collection_date": datetime.now().isoformat()
        }


# Global service instance
data_collection_service = DataCollectionService()
