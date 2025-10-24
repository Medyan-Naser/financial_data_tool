#!/usr/bin/env python3
"""
Pattern Logger for Financial Statement Mapping Improvement

This module logs unmapped rows and their labels to help improve regex patterns.
The log file serves as a database to analyze what companies report and improve matching.

Log Format:
- Company ticker, CIK, statement type, fiscal year
- Total rows matched vs total rows
- Each row: us-gaap tag, human label, matched status
- Only logs unique combinations (no duplicates)
"""

import os
import json
import hashlib
from datetime import datetime
from typing import Dict, List, Optional
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class PatternLogger:
    """
    Logs financial statement patterns for regex improvement.
    
    Features:
    - Deduplication (only logs unique company/year/statement combos)
    - Structured format (easy to parse for analysis)
    - Match statistics (X/Y rows matched)
    - Both US-GAAP and human labels captured
    """
    
    def __init__(self, log_dir: str = "pattern_logs"):
        """
        Initialize the pattern logger.
        
        Args:
            log_dir: Directory to store log files
        """
        self.log_dir = log_dir
        self.log_file = os.path.join(log_dir, "pattern_log.jsonl")
        self.seen_file = os.path.join(log_dir, "seen_hashes.txt")
        
        # Create log directory if it doesn't exist
        os.makedirs(log_dir, exist_ok=True)
        
        # Load already-seen hashes to avoid duplicates
        self.seen_hashes = self._load_seen_hashes()
    
    def _load_seen_hashes(self) -> set:
        """Load set of already-logged statement hashes."""
        if not os.path.exists(self.seen_file):
            return set()
        
        with open(self.seen_file, 'r') as f:
            return set(line.strip() for line in f)
    
    def _save_hash(self, hash_str: str):
        """Save a hash to the seen file."""
        with open(self.seen_file, 'a') as f:
            f.write(f"{hash_str}\n")
    
    def _generate_hash(self, ticker: str, statement_type: str, fiscal_year: str) -> str:
        """
        Generate unique hash for company/statement/year combination.
        
        Args:
            ticker: Stock ticker
            statement_type: 'income_statement', 'balance_sheet', 'cash_flow'
            fiscal_year: Fiscal year end date (e.g., '2024-09-28')
        
        Returns:
            SHA256 hash string
        """
        key = f"{ticker}|{statement_type}|{fiscal_year}"
        return hashlib.sha256(key.encode()).hexdigest()
    
    def _extract_row_info(self, df: pd.DataFrame) -> List[Dict]:
        """
        Extract row information from DataFrame.
        
        Args:
            df: Original DataFrame from financial statement
        
        Returns:
            List of dicts with row info: {index, us_gaap, human_label}
        """
        rows = []
        for idx, row_name in enumerate(df.index):
            rows.append({
                'row_number': idx + 1,
                'us_gaap': row_name if 'us-gaap' in str(row_name) else None,
                'human_label': row_name if 'us-gaap' not in str(row_name) else None,
                'raw_label': str(row_name)
            })
        return rows
    
    def log_statement(
        self,
        ticker: str,
        cik: str,
        statement_type: str,
        fiscal_year: str,
        original_df: pd.DataFrame,
        mapped_df: Optional[pd.DataFrame],
        taxonomy: str = "us-gaap",
        statement_object: Optional[object] = None
    ) -> bool:
        """
        Log a financial statement for pattern analysis.
        
        Args:
            ticker: Stock ticker (e.g., 'AAPL')
            cik: SEC CIK number
            statement_type: 'income_statement', 'balance_sheet', 'cash_flow'
            fiscal_year: Fiscal year end date (e.g., '2024-09-28')
            original_df: Original DataFrame from SEC filing
            mapped_df: Mapped DataFrame (or None if mapping failed)
            taxonomy: XBRL taxonomy used (default: 'us-gaap')
        
        Returns:
            True if logged, False if already exists (duplicate)
        """
        # Check if already logged
        hash_key = self._generate_hash(ticker, statement_type, fiscal_year)
        if hash_key in self.seen_hashes:
            logger.debug(f"Skipping {ticker} {statement_type} {fiscal_year} - already logged")
            return False
        
        # Extract matched row information from statement object's mapped_facts
        # mapped_facts contains tuples of (original_idx, fact_row, pattern_type, pattern)
        matched_original_rows = set()
        
        if statement_object is not None and hasattr(statement_object, 'mapped_facts'):
            # Extract the original indices that were successfully mapped
            for mapped_fact_tuple in statement_object.mapped_facts:
                if len(mapped_fact_tuple) >= 1:
                    original_idx = mapped_fact_tuple[0]  # First element is original row name
                    matched_original_rows.add(str(original_idx))
            logger.debug(f"Found {len(matched_original_rows)} matched rows from statement object")
        else:
            logger.debug("No statement object or mapped_facts available")
        
        # Extract row information with match status
        row_info = []
        for idx, row_name in enumerate(original_df.index):
            is_matched = str(row_name) in matched_original_rows
            row_info.append({
                'row_number': idx + 1,
                'raw_label': str(row_name),
                'is_us_gaap': 'us-gaap' in str(row_name) or ':' in str(row_name),
                'matched': is_matched
            })
        
        # Calculate match statistics
        total_rows = len(original_df)
        matched_rows = len(matched_original_rows)
        match_percentage = (matched_rows / total_rows * 100) if total_rows > 0 else 0
        
        # Create log entry
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'ticker': ticker,
            'cik': cik,
            'statement_type': statement_type,
            'fiscal_year': fiscal_year,
            'taxonomy': taxonomy,
            'statistics': {
                'total_rows': total_rows,
                'matched_rows': matched_rows,
                'unmapped_rows': total_rows - matched_rows,
                'match_percentage': round(match_percentage, 2),
                'match_ratio': f"{matched_rows}/{total_rows}"
            },
            'rows': row_info,
            'hash': hash_key
        }
        
        # Append to log file (JSONL format - one JSON per line)
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
        
        # Save hash to avoid duplicates
        self._save_hash(hash_key)
        self.seen_hashes.add(hash_key)
        
        logger.info(f"Logged {ticker} {statement_type} {fiscal_year}: {matched_rows}/{total_rows} matched ({match_percentage:.1f}%)")
        
        return True
    
    def generate_human_readable_report(self, output_file: str = None) -> str:
        """
        Generate a human-readable report from the log file.
        
        Args:
            output_file: Optional file path to save report
        
        Returns:
            Report text
        """
        if not os.path.exists(self.log_file):
            return "No log data available."
        
        # Read all log entries
        entries = []
        with open(self.log_file, 'r') as f:
            for line in f:
                entries.append(json.loads(line))
        
        # Generate report
        report_lines = [
            "="*80,
            "FINANCIAL STATEMENT PATTERN LOG REPORT",
            "="*80,
            f"Total statements logged: {len(entries)}",
            f"Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "="*80,
            ""
        ]
        
        # Group by statement type
        by_type = {}
        for entry in entries:
            stmt_type = entry['statement_type']
            if stmt_type not in by_type:
                by_type[stmt_type] = []
            by_type[stmt_type].append(entry)
        
        # Report by statement type
        for stmt_type, stmt_entries in by_type.items():
            report_lines.append(f"\n{'='*80}")
            report_lines.append(f"{stmt_type.upper().replace('_', ' ')}")
            report_lines.append(f"{'='*80}")
            report_lines.append(f"Total filings: {len(stmt_entries)}")
            
            # Calculate average match rate
            avg_match = sum(e['statistics']['match_percentage'] for e in stmt_entries) / len(stmt_entries)
            report_lines.append(f"Average match rate: {avg_match:.1f}%")
            report_lines.append("")
            
            # List each filing
            for entry in stmt_entries:
                report_lines.append(f"  {entry['ticker']} - {entry['fiscal_year']}")
                report_lines.append(f"    Match: {entry['statistics']['match_ratio']} ({entry['statistics']['match_percentage']}%)")
                
                # Show unmapped rows
                unmapped = [r for r in entry['rows'] if not r['matched']]
                if unmapped:
                    report_lines.append(f"    Unmapped rows ({len(unmapped)}):")
                    for row in unmapped[:5]:  # Show first 5
                        report_lines.append(f"      - {row['raw_label'][:70]}")
                    if len(unmapped) > 5:
                        report_lines.append(f"      ... and {len(unmapped) - 5} more")
                report_lines.append("")
        
        report_text = "\n".join(report_lines)
        
        # Save to file if requested
        if output_file:
            with open(output_file, 'w') as f:
                f.write(report_text)
            logger.info(f"Report saved to {output_file}")
        
        return report_text
    
    def analyze_common_patterns(self, statement_type: str = None) -> Dict:
        """
        Analyze log to find commonly unmapped patterns.
        
        Args:
            statement_type: Optional filter by statement type
        
        Returns:
            Dictionary with analysis results
        """
        if not os.path.exists(self.log_file):
            return {}
        
        # Read all log entries
        entries = []
        with open(self.log_file, 'r') as f:
            for line in f:
                entry = json.loads(line)
                if statement_type is None or entry['statement_type'] == statement_type:
                    entries.append(entry)
        
        if not entries:
            return {}
        
        # Find commonly unmapped rows
        unmapped_labels = {}
        for entry in entries:
            for row in entry['rows']:
                if not row['matched']:
                    label = row['raw_label']
                    if label not in unmapped_labels:
                        unmapped_labels[label] = {
                            'count': 0,
                            'companies': set(),
                            'is_us_gaap': row['is_us_gaap']
                        }
                    unmapped_labels[label]['count'] += 1
                    unmapped_labels[label]['companies'].add(entry['ticker'])
        
        # Convert sets to lists for JSON serialization
        for label in unmapped_labels:
            unmapped_labels[label]['companies'] = list(unmapped_labels[label]['companies'])
        
        # Sort by frequency
        sorted_unmapped = sorted(
            unmapped_labels.items(),
            key=lambda x: x[1]['count'],
            reverse=True
        )
        
        return {
            'total_entries': len(entries),
            'statement_type': statement_type or 'all',
            'most_common_unmapped': sorted_unmapped[:20],  # Top 20
            'total_unique_unmapped': len(unmapped_labels)
        }


# Singleton instance
_pattern_logger = None

def get_pattern_logger(log_dir: str = "pattern_logs") -> PatternLogger:
    """Get or create the global pattern logger instance."""
    global _pattern_logger
    if _pattern_logger is None:
        _pattern_logger = PatternLogger(log_dir)
    return _pattern_logger
