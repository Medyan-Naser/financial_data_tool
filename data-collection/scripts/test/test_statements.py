#!/usr/bin/env python3
"""Test Balance Sheet and Cash Flow processing"""

from Company import Company
from Filling import Filling

def test_statements(ticker='AAPL'):
    print(f'\n{"="*80}')
    print(f'Testing {ticker}')
    print("="*80)
    
    company = Company(ticker=ticker)
    filing = Filling(
        ticker=ticker,
        cik=company.cik,
        acc_num_unfiltered=company.ten_k_fillings.iloc[0],
        company_facts=company.company_facts
    )
    
    # Test Balance Sheet
    print('\n=== BALANCE SHEET ===')
    try:
        filing.process_one_statement('balance_sheet')
        bs = filing.balance_sheet.get_mapped_df()
        if bs is not None:
            non_zero = bs[(bs != 0).any(axis=1)]
            print(f'✅ Mapped: {len(non_zero)} out of {len(bs)} items')
            print('\nFirst 10 mapped items:')
            for idx in non_zero.index[:10]:
                val = non_zero.loc[idx].values[0]
                print(f'  - {idx}: ${val:,.0f}')
        else:
            print('❌ Failed to create mapped DataFrame')
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()
    
    # Test Cash Flow
    print('\n=== CASH FLOW ===')
    try:
        filing.process_one_statement('cash_flow_statement')
        cf = filing.cash_flow.get_mapped_df()
        if cf is not None:
            non_zero = cf[(cf != 0).any(axis=1)]
            print(f'✅ Mapped: {len(non_zero)} out of {len(cf)} items')
            print('\nFirst 10 mapped items:')
            for idx in non_zero.index[:10]:
                val = non_zero.loc[idx].values[0]
                print(f'  - {idx}: ${val:,.0f}')
        else:
            print('❌ Failed to create mapped DataFrame')
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_statements('AAPL')
    test_statements('GOOGL')
