#!/usr/bin/env python3
"""
Enhanced test script to analyze pattern_log.jsonl and validate regex improvements.
This script:
1. Parses all entries in pattern_log.jsonl
2. Tests if we can find the SPECIFIC items we care about
3. Reports success rate for finding our target metrics
4. Provides detailed statistics on unmatched patterns
5. Identifies which unmatched items should be added to regex
"""

import json
import re
from collections import defaultdict, Counter
from statement_maps import IncomeStatementMap, BalanceSheetMap, CashFlowMap

def load_pattern_log(filepath):
    """Load and parse the JSONL pattern log file."""
    entries = []
    with open(filepath, 'r') as f:
        for line in f:
            if line.strip():
                entries.append(json.loads(line))
    return entries

def get_target_items(stmt_map):
    """Get list of MapFact items we're trying to find."""
    items = []
    for attr_name in dir(stmt_map):
        if attr_name.startswith('_'):
            continue
        attr = getattr(stmt_map, attr_name)
        if hasattr(attr, 'gaap_pattern'):
            items.append((attr_name, attr))
    return items

def test_regex_against_log(entries, statement_maps):
    """Test if we can find the specific items we care about."""
    # Track which items we found and which we didn't
    item_stats = {
        'income_statement': defaultdict(lambda: {'found': 0, 'total_statements': 0, 'found_in': []}),
        'balance_sheet': defaultdict(lambda: {'found': 0, 'total_statements': 0, 'found_in': []}),
        'cash_flow_statement': defaultdict(lambda: {'found': 0, 'total_statements': 0, 'found_in': []})
    }
    
    # Track unmatched raw labels
    unmatched_labels = {
        'income_statement': Counter(),
        'balance_sheet': Counter(),
        'cash_flow_statement': Counter()
    }
    
    # Track human labels that weren't matched
    unmatched_human_labels = {
        'income_statement': Counter(),
        'balance_sheet': Counter(),
        'cash_flow_statement': Counter()
    }
    
    # Count unique statements per type
    statement_counts = defaultdict(set)
    for entry in entries:
        key = (entry['ticker'], entry['fiscal_year'], entry['statement_type'])
        statement_counts[entry['statement_type']].add(key)
    
    # For each statement in the log
    for entry in entries:
        statement_type = entry['statement_type']
        ticker = entry['ticker']
        fiscal_year = entry['fiscal_year']
        
        # Get the appropriate map
        if statement_type == 'income_statement':
            stmt_map = statement_maps['income']
        elif statement_type == 'balance_sheet':
            stmt_map = statement_maps['balance']
        else:
            stmt_map = statement_maps['cash_flow']
        
        # Get all target items for this statement type
        target_items = get_target_items(stmt_map)
        
        # Track which items we found in THIS statement
        found_items_in_statement = set()
        
        # Check each row in the statement
        for row in entry['rows']:
            raw_label = row['raw_label']
            human_label = row.get('human_label')
            
            # Try to match against each target item
            matched_to_any = False
            for item_name, map_fact in target_items:
                if item_name in found_items_in_statement:
                    continue  # Already found this item in this statement
                
                matched = False
                match_type = None
                
                # Check GAAP patterns against raw_label
                for pattern in map_fact.gaap_pattern:
                    try:
                        if re.search(pattern, raw_label, re.IGNORECASE):
                            matched = True
                            match_type = 'gaap'
                            break
                    except Exception as e:
                        pass
                
                if not matched and hasattr(map_fact, 'ifrs_pattern'):
                    # Check IFRS patterns
                    for pattern in map_fact.ifrs_pattern:
                        try:
                            if re.search(pattern, raw_label, re.IGNORECASE):
                                matched = True
                                match_type = 'ifrs'
                                break
                        except Exception as e:
                            pass
                
                # Check human patterns against human_label
                if not matched and human_label and hasattr(map_fact, 'human_pattern'):
                    for pattern in map_fact.human_pattern:
                        try:
                            if re.search(pattern, human_label, re.IGNORECASE):
                                matched = True
                                match_type = 'human'
                                break
                        except Exception as e:
                            pass
                
                if matched:
                    found_items_in_statement.add(item_name)
                    item_stats[statement_type][item_name]['found'] += 1
                    item_stats[statement_type][item_name]['found_in'].append(f"{ticker}_{fiscal_year}")
                    matched_to_any = True
                    break
            
            # Track unmatched labels
            if not matched_to_any:
                unmatched_labels[statement_type][raw_label] += 1
                if human_label:
                    unmatched_human_labels[statement_type][human_label] += 1
        
        # Update total statements count for each item
        for item_name, _ in target_items:
            item_stats[statement_type][item_name]['total_statements'] += 1
    
    return item_stats, statement_counts, unmatched_labels, unmatched_human_labels

def analyze_unmatched_for_new_patterns(unmatched_labels, unmatched_human_labels):
    """Analyze unmatched patterns to identify candidates for new regex."""
    print("\n" + "="*80)
    print("UNMATCHED PATTERN ANALYSIS")
    print("Identifying high-frequency patterns that should be added")
    print("="*80)
    
    for stmt_type in ['income_statement', 'balance_sheet', 'cash_flow_statement']:
        print(f"\n{'='*80}")
        print(f"{stmt_type.upper().replace('_', ' ')}")
        print("-"*80)
        
        # Show top unmatched GAAP labels
        print("\nTop 30 Unmatched GAAP Labels (raw_label):")
        print(f"{'Count':<8} {'GAAP Label'}")
        print("-"*80)
        for label, count in unmatched_labels[stmt_type].most_common(30):
            print(f"{count:<8} {label}")
        
        # Show top unmatched human labels
        print(f"\nTop 30 Unmatched Human Labels:")
        print(f"{'Count':<8} {'Human Label'}")
        print("-"*80)
        for label, count in unmatched_human_labels[stmt_type].most_common(30):
            if label:  # Only show non-empty
                print(f"{count:<8} {label}")

def print_report(item_stats, statement_counts):
    """Print a detailed report of findings."""
    print("="*80)
    print("ITEM-SPECIFIC MATCHING REPORT")
    print("Showing success rate for finding each target financial metric")
    print("="*80)
    print()
    
    overall_items_found = 0
    overall_items_total = 0
    
    for stmt_type in ['income_statement', 'balance_sheet', 'cash_flow_statement']:
        print(f"\n{'='*80}")
        print(f"{stmt_type.upper().replace('_', ' ')}")
        print(f"Total statements analyzed: {len(statement_counts[stmt_type])}")
        print("-"*80)
        print(f"{'Item':<40} {'Found':<10} {'Total':<10} {'%':<10}")
        print("-"*80)
        
        items = sorted(item_stats[stmt_type].items(), 
                      key=lambda x: x[1]['found'] / max(1, x[1]['total_statements']), 
                      reverse=True)
        
        for item_name, stats in items:
            found = stats['found']
            total = stats['total_statements']
            pct = (found / total * 100) if total > 0 else 0
            
            overall_items_found += found
            overall_items_total += total
            
            status = "✓" if pct >= 75 else "✗"
            print(f"{status} {item_name:<38} {found:<10} {total:<10} {pct:>6.2f}%")
        
        # Calculate average for this statement type
        if items:
            stmt_found = sum(s['found'] for _, s in items)
            stmt_total = sum(s['total_statements'] for _, s in items)
            stmt_pct = (stmt_found / stmt_total * 100) if stmt_total > 0 else 0
            print("-"*80)
            print(f"{'AVERAGE FOR ' + stmt_type.upper():<40} {stmt_found:<10} {stmt_total:<10} {stmt_pct:>6.2f}%")
    
    print("\n" + "="*80)
    overall_pct = (overall_items_found / overall_items_total * 100) if overall_items_total > 0 else 0
    print(f"{'OVERALL AVERAGE':<40} {overall_items_found:<10} {overall_items_total:<10} {overall_pct:>6.2f}%")
    print("="*80)
    
    return overall_pct

def main():
    log_file = '/Users/medyan/Desktop/projects/stock_analysis/financial_data_tool/data-collection/scripts/pattern_logs/pattern_log.jsonl'
    
    print("Loading pattern log...")
    entries = load_pattern_log(log_file)
    print(f"Loaded {len(entries)} entries from pattern log")
    print()
    
    print("Testing regex patterns to find target items...")
    statement_maps = {
        'income': IncomeStatementMap(),
        'balance': BalanceSheetMap(),
        'cash_flow': CashFlowMap()
    }
    
    item_stats, statement_counts, unmatched_labels, unmatched_human_labels = test_regex_against_log(entries, statement_maps)
    print()
    
    match_pct = print_report(item_stats, statement_counts)
    
    # Show unmatched analysis
    analyze_unmatched_for_new_patterns(unmatched_labels, unmatched_human_labels)
    
    print()
    if match_pct >= 75:
        print(f"✓ SUCCESS! Average match rate of {match_pct:.2f}% exceeds 75% threshold!")
        return 0
    else:
        print(f"✗ FAIL: Average match rate of {match_pct:.2f}% is below 75% threshold.")
        print("  Need to improve regex patterns.")
        return 1

if __name__ == '__main__':
    exit(main())
