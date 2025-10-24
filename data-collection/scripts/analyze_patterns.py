#!/usr/bin/env python3
"""
Pattern Analysis Tool

Analyzes the pattern log to identify commonly unmapped items and suggest
regex improvements.

Usage:
    python3 analyze_patterns.py
    python3 analyze_patterns.py --statement income_statement
    python3 analyze_patterns.py --report
"""

import argparse
import json
from pattern_logger import get_pattern_logger
from collections import Counter


def main():
    parser = argparse.ArgumentParser(description='Analyze financial statement patterns')
    parser.add_argument('--statement', type=str, choices=['income_statement', 'balance_sheet', 'cash_flow'],
                       help='Filter by statement type')
    parser.add_argument('--report', action='store_true',
                       help='Generate human-readable report')
    parser.add_argument('--top', type=int, default=20,
                       help='Number of top unmapped items to show')
    
    args = parser.parse_args()
    
    logger = get_pattern_logger()
    
    if args.report:
        # Generate human-readable report
        report = logger.generate_human_readable_report('pattern_analysis_report.txt')
        print(report)
        print("\nReport saved to: pattern_analysis_report.txt")
    else:
        # Analyze common patterns
        analysis = logger.analyze_common_patterns(args.statement)
        
        if not analysis:
            print("No pattern data available. Run some statements first.")
            return
        
        print("="*80)
        print(f"PATTERN ANALYSIS - {analysis['statement_type'].upper()}")
        print("="*80)
        print(f"Total statements analyzed: {analysis['total_entries']}")
        print(f"Total unique unmapped items: {analysis['total_unique_unmapped']}")
        print("\n" + "="*80)
        print(f"TOP {args.top} MOST COMMONLY UNMAPPED ITEMS:")
        print("="*80)
        
        for idx, (label, info) in enumerate(analysis['most_common_unmapped'][:args.top], 1):
            print(f"\n{idx}. {label[:70]}")
            print(f"   Frequency: {info['count']} times")
            print(f"   Companies: {', '.join(info['companies'][:5])}")
            if len(info['companies']) > 5:
                print(f"              ...and {len(info['companies']) - 5} more")
            print(f"   US-GAAP: {'Yes' if info['is_us_gaap'] else 'No'}")
            
            # Suggest regex pattern
            if info['is_us_gaap']:
                # Extract the tag name
                if ':' in label:
                    tag = label.split(':')[-1]
                    print(f"   Suggested pattern: r\"(?i)\\b{tag}\\b\"")
            else:
                # Human label - suggest fuzzy pattern
                keywords = label.lower().replace(',', '').split()
                if len(keywords) > 0:
                    pattern = r"(?i)" + ".*".join(keywords[:3])
                    print(f"   Suggested pattern: r\"{pattern}\"")


if __name__ == "__main__":
    main()
