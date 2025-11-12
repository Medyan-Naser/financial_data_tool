#!/usr/bin/env python3
"""
Test that the --statement filter in main.py works correctly.
"""

import sys
from main import get_financial_statements

def test_income_only():
    """Test that only income statement is fetched when filter='income'."""
    print("Testing --statement income filter...")
    
    results = get_financial_statements(
        ticker='AAPL',
        num_years=1,
        quarterly=False,
        statement_filter='income'
    )
    
    # Should have income statements
    assert len(results['income_statements']) > 0, "❌ No income statements!"
    
    # Should NOT have balance sheets or cash flows
    assert len(results['balance_sheets']) == 0, "❌ Balance sheets should be empty!"
    assert len(results['cash_flows']) == 0, "❌ Cash flows should be empty!"
    
    print(f"✅ PASSED: Got {len(results['income_statements'])} income statement(s), 0 balance, 0 cash flow")
    return True


def test_balance_only():
    """Test that only balance sheet is fetched when filter='balance'."""
    print("\nTesting --statement balance filter...")
    
    results = get_financial_statements(
        ticker='AAPL',
        num_years=1,
        quarterly=False,
        statement_filter='balance'
    )
    
    # Should have balance sheets
    assert len(results['balance_sheets']) > 0, "❌ No balance sheets!"
    
    # Should NOT have income or cash flows
    assert len(results['income_statements']) == 0, "❌ Income statements should be empty!"
    assert len(results['cash_flows']) == 0, "❌ Cash flows should be empty!"
    
    print(f"✅ PASSED: Got {len(results['balance_sheets'])} balance sheet(s), 0 income, 0 cash flow")
    return True


def test_cashflow_only():
    """Test that only cash flow is fetched when filter='cashflow'."""
    print("\nTesting --statement cashflow filter...")
    
    results = get_financial_statements(
        ticker='AAPL',
        num_years=1,
        quarterly=False,
        statement_filter='cashflow'
    )
    
    # Should have cash flows
    assert len(results['cash_flows']) > 0, "❌ No cash flows!"
    
    # Should NOT have income or balance
    assert len(results['income_statements']) == 0, "❌ Income statements should be empty!"
    assert len(results['balance_sheets']) == 0, "❌ Balance sheets should be empty!"
    
    print(f"✅ PASSED: Got {len(results['cash_flows'])} cash flow(s), 0 income, 0 balance")
    return True


def test_all():
    """Test that all statements are fetched when filter='all'."""
    print("\nTesting --statement all filter...")
    
    results = get_financial_statements(
        ticker='AAPL',
        num_years=1,
        quarterly=False,
        statement_filter='all'
    )
    
    # Should have all three
    assert len(results['income_statements']) > 0, "❌ No income statements!"
    assert len(results['balance_sheets']) > 0, "❌ No balance sheets!"
    assert len(results['cash_flows']) > 0, "❌ No cash flows!"
    
    print(f"✅ PASSED: Got {len(results['income_statements'])} income, {len(results['balance_sheets'])} balance, {len(results['cash_flows'])} cash flow")
    return True


if __name__ == "__main__":
    print("="*80)
    print("STATEMENT FILTER TEST")
    print("="*80)
    
    all_passed = True
    
    try:
        test_income_only()
    except Exception as e:
        print(f"❌ Income test failed: {e}")
        all_passed = False
    
    try:
        test_balance_only()
    except Exception as e:
        print(f"❌ Balance test failed: {e}")
        all_passed = False
    
    try:
        test_cashflow_only()
    except Exception as e:
        print(f"❌ Cashflow test failed: {e}")
        all_passed = False
    
    try:
        test_all()
    except Exception as e:
        print(f"❌ All test failed: {e}")
        all_passed = False
    
    print("\n" + "="*80)
    if all_passed:
        print("✅ ALL TESTS PASSED!")
        print("The --statement filter is working correctly.")
    else:
        print("❌ SOME TESTS FAILED")
    print("="*80)
    
    sys.exit(0 if all_passed else 1)
