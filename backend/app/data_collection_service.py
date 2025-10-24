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
        
    def get_cache_path(self, ticker: str) -> Path:
        """Get the cache file path for a ticker."""
        return self.cache_dir / f"{ticker.upper()}_statements.json"
    
    def is_cached(self, ticker: str) -> bool:
        """Check if ticker data is cached."""
        cache_path = self.get_cache_path(ticker)
        return cache_path.exists()
    
    def load_cached_data(self, ticker: str) -> Optional[Dict]:
        """Load cached data for a ticker."""
        cache_path = self.get_cache_path(ticker)
        
        if not cache_path.exists():
            return None
            
        try:
            with open(cache_path, 'r') as f:
                data = json.load(f)
            logger.info(f"Loaded cached data for {ticker}")
            return data
        except Exception as e:
            logger.error(f"Error loading cached data for {ticker}: {e}")
            return None
    
    def save_to_cache(self, ticker: str, data: Dict) -> bool:
        """Save data to cache."""
        cache_path = self.get_cache_path(ticker)
        
        try:
            # Add metadata
            data['cached_at'] = datetime.now().isoformat()
            data['ticker'] = ticker.upper()
            
            with open(cache_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Saved data to cache for {ticker}")
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
        force_refresh: bool = False
    ) -> AsyncGenerator[str, None]:
        """
        Collect financial data with progress updates.
        
        Yields progress updates as Server-Sent Events (SSE) format.
        """
        ticker = ticker.upper()
        
        # Check cache first
        if not force_refresh and self.is_cached(ticker):
            yield f"data: {json.dumps({'status': 'cached', 'message': 'Loading from cache...', 'progress': 100})}\n\n"
            cached_data = self.load_cached_data(ticker)
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
            # Build command
            cmd = [
                sys.executable,
                str(self.collection_script),
                "--ticker", ticker,
                "--years", str(years)
            ]
            
            # Run subprocess and capture output
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.collection_script.parent)
            )
            
            # Track progress
            current_progress = 15
            progress_per_year = 70 / years  # 70% of progress bar for data collection
            
            # Read output line by line
            line_count = 0
            async for line in process.stdout:
                line_text = line.decode().strip()
                line_count += 1
                
                # Update progress based on output
                if "Processing filing" in line_text or "Processing Income Statement" in line_text:
                    current_progress = min(80, current_progress + progress_per_year / 3)
                    yield f"data: {json.dumps({'status': 'collecting', 'message': line_text, 'progress': int(current_progress)})}\n\n"
                    await asyncio.sleep(0.05)
                
                # Log every 10th line
                if line_count % 10 == 0:
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
            financial_data = await self._load_collected_data(ticker)
            
            if not financial_data:
                yield f"data: {json.dumps({'status': 'error', 'message': 'No data was collected. Ticker may not exist.'})}\n\n"
                return
            
            yield f"data: {json.dumps({'status': 'saving', 'message': 'Saving to cache...', 'progress': 95})}\n\n"
            await asyncio.sleep(0.2)
            
            # Save to cache
            self.save_to_cache(ticker, financial_data)
            
            yield f"data: {json.dumps({'status': 'complete', 'message': 'Data collection complete!', 'progress': 100, 'data': financial_data})}\n\n"
            
        except Exception as e:
            error_msg = f"Unexpected error during collection: {str(e)}"
            logger.error(error_msg)
            yield f"data: {json.dumps({'status': 'error', 'message': error_msg})}\n\n"
    
    async def _load_collected_data(self, ticker: str) -> Optional[Dict]:
        """Load data from the old financials directory and format it."""
        old_financials_dir = BASE_DIR / "api" / "financials"
        
        statements_data = {
            "income_statement": None,
            "balance_sheet": None,
            "cash_flow": None
        }
        
        statement_types = [
            ("income_statement", "income_statement"),
            ("balance_sheet", "balance_sheet"),
            ("cash_flow", "cash_flow_statement")  # Note: file might be cash_flow_statement
        ]
        
        has_data = False
        
        for stmt_key, file_pattern in statement_types:
            # Try multiple file patterns
            patterns = [
                f"{ticker}_{file_pattern}.csv",
                f"{ticker}_{stmt_key}.csv",
                f"{ticker}_{file_pattern}_custom.csv",
                f"{ticker}_{stmt_key}_custom.csv"
            ]
            
            for pattern in patterns:
                file_path = old_financials_dir / pattern
                
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
                            "file_source": pattern
                        }
                        
                        has_data = True
                        logger.info(f"Loaded {stmt_key} for {ticker} from {pattern}")
                        break
                        
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
        
        return {
            "ticker": ticker.upper(),
            "statements": statements_data,
            "collection_date": datetime.now().isoformat()
        }


# Global service instance
data_collection_service = DataCollectionService()
