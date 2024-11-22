import pandas as pd
from pandas.api.extensions import ExtensionDtype, register_extension_dtype
from helpers import *
from itertools import combinations, product
import copy
import numpy as np
import re
import Finacials

income_statement_milestones = [GrossProfit, OperatingIncome, EBT, NetIncome]

def base_eq(df: DataFrameWithStringListTracking, end_index_s: str, compute=False, compare_to=None, add_missing_rows=False, change_sign=False, strict_compare=True):
    pass
## NOTE when writing function it seems you pass by pointer and you can change inside df 
# 
def gross_profit_eq_old(df: DataFrameWithStringListTracking, compute=False, compare_to=None):
    start_pos = df.df.index.get_loc('Total revenue')
    end_pos = df.df.index.get_loc('Gross profit')
    # computed_expense = df.iloc[start_pos + 1:end_pos].sum()
    gross_profit = combine_variables(df, start_pos+1, end_pos, base_var='Total revenue', subtract=True)
    # print(gross_profit)
    if compute:
        return gross_profit
    if compare_to is not None:
        return compare_to.equals(gross_profit)
        return  df.loc[compare_to, df.columns[-1]] == gross_profit[-1]
    return df.loc['Gross profit', df.columns[-1]] == gross_profit[-1]

def gross_profit_eq(df: DataFrameWithStringListTracking, end_index_s: str, compute=False, compare_to=None, add_missing_rows=False, change_sign=False, strict_compare=True):
    df_temp = 0
    df_temp = copy.deepcopy(df)
    start_pos = df.df.index.get_loc('Total revenue')
    end_pos = df.df.index.get_loc(end_index_s)
    
    if compare_to is not None and change_sign:
        # sjould be operating income at this point
        if end_pos - start_pos > 3:
            return False
        if find_combinations_with_logging(df_temp, start_pos, end_pos, compare_to, change_sign=True, strict_compare=strict_compare, check_for_total=True):
            df.df =df_temp.df
            return True
        else:
            return False
    if df_temp.df.iloc[start_pos+1].sum() > 0:
        for row_index, row in df_temp.df.iloc[start_pos+1:end_pos].iterrows():
            for col in df_temp.df.columns:
                df_temp.df.at[row_index, col] = -row[col]
    gross_profit = combine_variables(df_temp, start_pos+1, end_pos, base_var='Total revenue')
    print(gross_profit, compare_to)
    print(df.master_list_dict)
    if change_sign or add_missing_rows:
        df.df = df_temp.df
    if compute:
        # find_combinations_with_logging(df, start_pos, end_pos, compare_to, change_sign=True)
        return gross_profit
    if compare_to is not None:
        # print(compare_to.equals(gross_profit))
        return compare_to.equals(gross_profit)

def total_operating_expense_eq(df: DataFrameWithStringListTracking, end_index_s: str, compute=False, compare_to=None, add_missing_rows=False, change_sign=False, strict_compare=True):
    df_temp = 0
    df_temp = copy.deepcopy(df)
    compare_to_c = 0
    compare_to_c = copy.deepcopy(compare_to)
    print(df_temp.df, "====1")
    # Find the positions of the start and end index names
    if GrossProfit in df_temp.df.index.tolist():
        start_pos = df_temp.df.index.get_loc(GrossProfit)
    else:
        # TODO: do i need to check this or just call C&E.
        start_pos = df_temp.df.index.get_loc(TotalRevenue)
    end_pos = df_temp.df.index.get_loc(end_index_s) # or 'Operating income'
    if compare_to is not None and change_sign:
        if find_combinations_with_logging(df_temp, start_pos+1, end_pos, compare_to_c, change_sign=True, change_base_sign=True, strict_compare=strict_compare):
            df.df =df_temp.df
            return True
        else:
            return False
    print(df_temp.df, "====3")
    computed_expense = combine_variables(df_temp, start_pos+1, end_pos)
    if add_missing_rows or change_sign:
        df.df = df_temp.df
    if compute:
        # print("====total operating")
        # print(df.df)
        # print(compare_to)
        # print(computed_expense)
        return computed_expense
    if compare_to is not None:
        print("====total operating")
        print(df.df)
        print(compare_to)
        print(computed_expense)
        return compare_to.equals(computed_expense)
        return df.loc[compare_to, df.columns[-1]] == computed_expense[-1]
    # print(df.loc['Total operating expense', df.columns[-1]] == computed_expense[-1])
    return df.loc['Total operating expense', df.columns[-1]] == computed_expense[-1]

def costs_and_expenses_eq(df: DataFrameWithStringListTracking, end_index_s: str, compute=False, compare_to=None, add_missing_rows=False, change_sign=False, strict_compare=True):
    calculate_gp =False
    df_temp = 0
    df_temp = copy.deepcopy(df)
    compare_to_c = 0
    compare_to_c = copy.deepcopy(compare_to)
    # Find the positions of the start and end index names
    start_pos = df_temp.df.index.get_loc('Total revenue')
    if GrossProfit in df_temp.df.index.tolist():
        # TODO: this will error becz C&E include COGS
        start_pos = df_temp.df.index.get_loc(GrossProfit)
    else:
        calculate_gp = True
    end_pos = df_temp.df.index.get_loc(end_index_s) 
    if compare_to is not None and change_sign:
        # if compare_to.sum() > 0:
        #     compare_to_c *= -1
        #     df_temp.df.loc[end_index_s] = compare_to_c
        if find_combinations_with_logging(df_temp, start_pos+1, end_pos, compare_to_c, change_sign=True, change_base_sign=True, strict_compare=strict_compare):
            df.df =df_temp.df
            return True
        else:
            return False
    if add_missing_rows:
        df.df = df_temp.df

def total_of_something(df: DataFrameWithStringListTracking, start_index_s: str, end_index_s: str, compare_to=None, add_missing_rows=False, change_sign=False, strict_compare=True, change_base_sing=True):
    df_temp = 0
    df_temp = copy.deepcopy(df)
    compare_to_c = 0
    compare_to_c = copy.deepcopy(compare_to)
    # Find the positions of the start and end index names
    if isinstance(start_index_s, int):
        start_index_s = df.df.index[start_index_s]
    start_pos = df_temp.df.index.get_loc(start_index_s)
    end_pos = df_temp.df.index.get_loc(end_index_s)
    if compare_to is not None and change_sign:
        if find_combinations_with_logging(df_temp, start_pos+1, end_pos, compare_to_c, change_sign=True, change_base_sign=change_base_sing, strict_compare=strict_compare):
            df.df =df_temp.df
            return True
    return False

def total_non_operating_expense_eq(df: DataFrameWithStringListTracking, end_index_s: str, compute=False, compare_to=None, add_missing_rows=False, change_sign=False, strict_compare=True):
    df_temp = 0
    df_temp = copy.deepcopy(df)
    compare_to_c = 0
    compare_to_c = copy.deepcopy(compare_to)
    # Find the positions of the start and end index names
    # start_pos = df.df.index.get_loc('Operating income')
    end_pos = df_temp.df.index.get_loc(end_index_s)
    if OperatingIncome in df_temp.df.index.tolist(): 
        start_pos = df_temp.df.index.get_loc(OperatingIncome)
    else:
        operating_income = IncomeStatement.operating_income_eq(df_temp, end_index_s, compute=True, change_sign=change_sign)
        df_temp = add_row_to_df(df_temp, operating_income, OperatingIncome, end_index_s, insert_after=False)
        start_pos = df_temp.df.index.get_loc(OperatingIncome)

    if compare_to is not None and change_sign:
        print(start_pos, end_pos)
        if find_combinations_with_logging(df_temp, start_pos+1, end_pos, compare_to_c, change_sign=True, change_base_sign=True, strict_compare=strict_compare):
            df.df = df_temp.df
            return True
        else:
            return False
    computed_expense = combine_variables(df_temp, start_pos+1, end_pos) #, check_master=False)
    if add_missing_rows:
        df.df = df_temp.df
    if compute:
        return computed_expense
    if compare_to is not None:
        # print(df, computed_expense)
        return compare_to.equals(computed_expense)
        return df.loc[compare_to, df.columns[-1]] == computed_expense[-1]
    # print(df.loc['Total non-operating income (expense)', df.columns[-1]] == computed_expense[-1])
    return df.loc['Total non-operating income (expense)', df.columns[-1]] == computed_expense[-1]

def operating_income_eq(df: DataFrameWithStringListTracking, end_index_s: str, compute=False, compare_to=None, add_missing_rows=False, change_sign=False, strict_compare=True):
    df_temp = 0
    df_temp = copy.deepcopy(df)
    end_pos = df_temp.df.index.get_loc(end_index_s)
    print(df_temp.df)
    if 'C&E' in df_temp.df.index.tolist(): #df.df.loc['C&E'].sum() != 0:
        start_pos = df_temp.df.index.get_loc('C&E')
        operating_income = combine_variables(df_temp, start_pos, end_pos, base_var=TotalRevenue)
    elif 'Total operating expense' in df_temp.df.index.tolist():         #df.df.loc['Total operating expense'].sum() == 0:
        # total_operating_expense = IncomeStatement.total_operating_expense_eq(df_temp, end_index_s, compute=True, change_sign=change_sign)
        start_pos = df_temp.df.index.get_loc('Total operating expense')
        operating_income = combine_variables(df_temp, start_pos, end_pos, base_var=GrossProfit if GrossProfit in df_temp.df.index.tolist() else TotalRevenue)
    else: # check if the previous row is the total expense
        pass
    print(df_temp.df)
    if compare_to is not None and change_sign:
        if GrossProfit in df_temp.df.index.tolist():
            start_pos = df_temp.df.index.get_loc(GrossProfit)
        else:
            start_pos = df_temp.df.index.get_loc(TotalRevenue)
        if find_combinations_with_logging(df_temp, start_pos, end_pos, compare_to, change_sign=True, strict_compare=strict_compare, check_for_total=True):
            df.df = df_temp.df
            return True
        else:
            return False
    if add_missing_rows:
        df.df = df_temp.df
    if compute:
        return operating_income
    if compare_to is not None:
        print(compare_to, operating_income)
        # print(compare_to.equals(operating_income))
        return compare_to.equals(operating_income)
        return df.loc[compare_to, df.columns[-1]] == operating_income[-1]
    # print(df.loc['Total operating expense', df.columns[-1]] == operating_income[-1])
    return df.loc['Operating income', df.df.columns[-1]] == operating_income[-1]

def EBT_eq(df: DataFrameWithStringListTracking, end_index_s: str, compute=False, compare_to=None, add_missing_rows=False, change_sign=False, strict_compare=True):
    df_temp = 0
    df_temp = copy.deepcopy(df)
    calc_total_non_oi = False
    # if df.df.loc['Total non-operating income (expense)'].sum() == 0:
    if 'Total non-operating income (expense)' not in df_temp.df.index.tolist():
        calc_total_non_oi = True
    start_pos = df_temp.df.index.get_loc(OperatingIncome)
    end_pos = df_temp.df.index.get_loc(end_index_s)
    print(start_pos, end_pos, (df_temp.df.iloc[start_pos] + df_temp.df.iloc[end_pos -1]))
    if compare_to is not None and change_sign:
        return False
    ebt = combine_variables(df_temp, start_pos, end_pos, base_var=OperatingIncome)
    if calc_total_non_oi:
        total_non_operating_expense = IncomeStatement.total_non_operating_expense_eq(df_temp, end_index_s, compute=True, change_sign=change_sign)
        df_temp = add_row_to_df(df_temp, total_non_operating_expense, 'Total non-operating income (expense)', end_index_s, insert_after=False)
    if add_missing_rows:
        df.df = df_temp.df
    if compute:
        return ebt
    if compare_to is not None:
        return compare_to.equals(ebt)
        return df.loc[compare_to, df.columns[-1]] == ebt[-1]
    # print(df.loc['Total non-operating income (expense)', df.columns[-1]] == ebt[-1])
    return df.loc['EBT', df.columns[-1]] == ebt[-1]

def net_income_inc_unusual_eq(df, start_index_s, end_index_s, compute=False, compare_to=None, add_missing_rows=False, change_sign=True, strict_compare=True):
    print(strict_compare)
    df_temp = 0
    df_temp = copy.deepcopy(df)
    start_pos = df_temp.df.index.get_loc(start_index_s)
    end_pos = df_temp.df.index.get_loc(end_index_s)
    if compare_to is not None and change_sign:
        if find_combinations_with_logging(df_temp, start_pos, end_pos, compare_to, change_sign=True, strict_compare=strict_compare):
            df.df = df_temp.df
            return True
        else:
            return False
    print("====net income unusual")
    print(df)
    print(start_index_s, end_index_s)
    print(net_income)
    print(compare_to)

    if compute:
        return net_income
    if compare_to is not None:
        if net_income:
            return True
        return compare_to.equals(net_income)
        return df.loc[compare_to, df.columns[-1]] == net_income[-1]
    # print(df.loc['Total non-operating income (expense)', df.columns[-1]] == ebt[-1])
    return df.loc['Net income without extra unusal items', df.columns[-1]] == net_income[-1]

def net_income_eq(df: DataFrameWithStringListTracking,  end_index_s: str, compute=False, compare_to=None, add_missing_rows=False, change_sign=False, strict_compare=True):
    df_temp = 0
    df_temp = copy.deepcopy(df)
    if 'EBT' not in df_temp.df.index.tolist():
        ebt = IncomeStatement.EBT_eq(df_temp, end_index_s, compute=True, change_sign=change_sign)
        df_temp = add_row_to_df(df_temp, ebt, 'EBT', end_index_s, insert_after=False)
    start_pos = df_temp.df.index.get_loc('EBT')
    end_pos = df_temp.df.index.get_loc(end_index_s)
    # computed_expense = df.iloc[start_pos + 1:end_pos].sum()
    # print(df)

    if compare_to is not None and change_sign:
        if find_combinations_with_logging(df_temp, start_pos, end_pos, compare_to, change_sign=True, strict_compare=strict_compare, check_for_total=True):
            df.df = df_temp.df
            return True
        else:
            return False
    net_income = 0
    net_income = combine_variables(df_temp, start_pos+1, end_pos, base_var='EBT')
    # net_income = df.loc['EBT'] - df.loc['Income tax expense']
    # print(df)
    if add_missing_rows:
        df.df = df_temp.df
    if compute:
        return net_income
    if compare_to is not None:
        return compare_to.equals(net_income)
        return df.loc[compare_to, df.columns[-1]] == net_income[-1]
    # print(df.loc['Total non-operating income (expense)', df.columns[-1]] == ebt[-1])
    return df.loc['Net income', df.columns[-1]] == net_income[-1]


def total_current_assets_eq(df: DataFrameWithStringListTracking, end_index_s: str, compute=False, compare_to=None, add_missing_rows=False, change_sign=False, strict_compare=True, must_find_comb=False, facts_weight=None, reu_class=False):
    df_temp = 0
    df_temp = copy.deepcopy(df)
    compare_to_c = 0
    compare_to_c = copy.deepcopy(compare_to)
    # Find the positions of the start and end index names
    start_pos = 0
    end_pos = df_temp.df.index.get_loc(end_index_s) # or 'Operating income'
    if compare_to is not None and change_sign:
        if find_combinations_with_logging(df_temp, start_pos, end_pos, compare_to_c, change_sign=True, change_base_sign=True, strict_compare=strict_compare, must_find_comb=must_find_comb, check_for_negative=False, facts_weight=facts_weight, reu_class=reu_class):
            df.df =df_temp.df
            return True
        else:
            return False
    computed_expense = combine_variables(df_temp, start_pos, end_pos)
    if add_missing_rows or change_sign:
        df.df = df_temp.df
    if compute:
        return computed_expense
    if compare_to is not None:
        return compare_to.equals(computed_expense)
        return df.loc[compare_to, df.columns[-1]] == computed_expense[-1]
    return df.loc['Total operating expense', df.columns[-1]] == computed_expense[-1]

def total_non_current_assets_eq(df: DataFrameWithStringListTracking, end_index_s: str, compute=False, compare_to=None, add_missing_rows=False, change_sign=False, strict_compare=True, must_find_comb=False, facts_weight=None, reu_class=False):
    df_temp = 0
    df_temp = copy.deepcopy(df)
    compare_to_c = 0
    compare_to_c = copy.deepcopy(compare_to)
    # Find the positions of the start and end index names
    start_pos = df_temp.df.index.get_loc(CurrentAssets) + 1
    end_pos = df_temp.df.index.get_loc(end_index_s)
    if compare_to is not None and change_sign:
        if find_combinations_with_logging(df_temp, start_pos, end_pos, compare_to_c, change_sign=True, change_base_sign=True, strict_compare=strict_compare, must_find_comb=must_find_comb, check_for_negative=False, facts_weight=facts_weight, reu_class=reu_class):
            df.df = df_temp.df
            return True
        else:
            return False
    computed_expense = combine_variables(df_temp, start_pos, end_pos)
    if add_missing_rows or change_sign:
        df.df = df_temp.df
    if compute:
        return computed_expense
    if compare_to is not None:
        return compare_to.equals(computed_expense)
        return df.loc[compare_to, df.columns[-1]] == computed_expense[-1]
    return df.loc['Total operating expense', df.columns[-1]] == computed_expense[-1]

def total_assets_eq(df: DataFrameWithStringListTracking, end_index_s: str, compute=False, compare_to=None, add_missing_rows=False, change_sign=False, strict_compare=True, must_find_comb=False, facts_weight=None, reu_class=False):
    
    # CurrentAssets, PropertyPlantAndEquipment, Goodwill, IntangibleAssets, OtherAssetsNoncurrent, NonCurrentAssets
    
    index_list = df.df.index.tolist()
    if (CurrentAssets not in index_list and NonCurrentAssets not in index_list) and ((PropertyPlantAndEquipment not in index_list and Goodwill not in index_list) or (PropertyPlantAndEquipment not in index_list and IntangibleAssets not in index_list)):
        return False
    df_temp = 0
    df_temp = copy.deepcopy(df)
    compare_to_c = 0
    compare_to_c = copy.deepcopy(compare_to)
    # Find the positions of the start and end index names
    start_pos = 0
    end_pos = df_temp.df.index.get_loc(end_index_s) # or 'Operating income'
    if compare_to is not None and change_sign:
        if find_combinations_with_logging(df_temp, start_pos, end_pos, compare_to_c, change_sign=True, change_base_sign=True, strict_compare=strict_compare, must_find_comb=must_find_comb, check_for_negative=False, facts_weight=facts_weight, reu_class=reu_class):
            df.df =df_temp.df
            return True
        else:
            return False
    computed_expense = combine_variables(df_temp, start_pos, end_pos)
    if add_missing_rows or change_sign:
        df.df = df_temp.df
    if compute:
        return computed_expense
    if compare_to is not None:
        return compare_to.equals(computed_expense)
        return df.loc[compare_to, df.columns[-1]] == computed_expense[-1]
    return df.loc['Total operating expense', df.columns[-1]] == computed_expense[-1]

def total_current_liabilities_eq(df: DataFrameWithStringListTracking, end_index_s: str, compute=False, compare_to=None, add_missing_rows=False, change_sign=False, strict_compare=True, must_find_comb=False, facts_weight=None, reu_class=False):
    df_temp = 0
    df_temp = copy.deepcopy(df)
    compare_to_c = 0
    compare_to_c = copy.deepcopy(compare_to)
    # Find the positions of the start and end index names
    start_pos = df_temp.df.index.get_loc(TotalAssets) +1
    end_pos = df_temp.df.index.get_loc(end_index_s) # or 'Operating income'
    if compare_to is not None and change_sign:
        if find_combinations_with_logging(df_temp, start_pos, end_pos, compare_to_c, change_sign=True, change_base_sign=True, strict_compare=strict_compare, must_find_comb=must_find_comb, check_for_negative=False, facts_weight=facts_weight, reu_class=reu_class):
            df.df =df_temp.df
            return True
        else:
            return False
    computed_expense = combine_variables(df_temp, start_pos, end_pos)
    if add_missing_rows or change_sign:
        df.df = df_temp.df
    if compute:
        return computed_expense
    if compare_to is not None:
        return compare_to.equals(computed_expense)
        return df.loc[compare_to, df.columns[-1]] == computed_expense[-1]
    return df.loc['Total operating expense', df.columns[-1]] == computed_expense[-1]

def total_non_current_liabilities_eq(df: DataFrameWithStringListTracking, end_index_s: str, compute=False, compare_to=None, add_missing_rows=False, change_sign=False, strict_compare=True, must_find_comb=False, facts_weight=None, reu_class=False):
    df_temp = 0
    df_temp = copy.deepcopy(df)
    compare_to_c = 0
    compare_to_c = copy.deepcopy(compare_to)
    # Find the positions of the start and end index names
    start_pos = df_temp.df.index.get_loc(LiabilitiesCurrent) + 1
    end_pos = df_temp.df.index.get_loc(end_index_s) 
    if compare_to is not None and change_sign:
        if find_combinations_with_logging(df_temp, start_pos, end_pos, compare_to_c, change_sign=True, change_base_sign=True, strict_compare=strict_compare, must_find_comb=must_find_comb, check_for_negative=False, facts_weight=facts_weight, reu_class=reu_class):
            df.df =df_temp.df
            return True
        else:
            return False
    computed_expense = combine_variables(df_temp, start_pos, end_pos)
    if add_missing_rows or change_sign:
        df.df = df_temp.df
    if compute:
        return computed_expense
    if compare_to is not None:
        return compare_to.equals(computed_expense)
        return df.loc[compare_to, df.columns[-1]] == computed_expense[-1]
    return df.loc['Total operating expense', df.columns[-1]] == computed_expense[-1]

def total_liabilities_eq(df: DataFrameWithStringListTracking, end_index_s: str, compute=False, compare_to=None, add_missing_rows=False, change_sign=False, strict_compare=True, must_find_comb=False, facts_weight=None, reu_class=False):
    df_temp = 0
    df_temp = copy.deepcopy(df)
    compare_to_c = 0
    compare_to_c = copy.deepcopy(compare_to)
    # Find the positions of the start and end index names
    start_pos = df_temp.df.index.get_loc(TotalAssets) +1
    end_pos = df_temp.df.index.get_loc(end_index_s) # or 'Operating income'
    if compare_to is not None and change_sign:
        if find_combinations_with_logging(df_temp, start_pos, end_pos, compare_to_c, change_sign=True, change_base_sign=True, strict_compare=strict_compare, must_find_comb=must_find_comb, check_for_negative=False, facts_weight=facts_weight, reu_class=reu_class):
            df.df =df_temp.df
            return True
        else:
            return False
    computed_expense = combine_variables(df_temp, start_pos, end_pos)
    if add_missing_rows or change_sign:
        df.df = df_temp.df
    if compute:
        return computed_expense
    if compare_to is not None:
        return compare_to.equals(computed_expense)
        return df.loc[compare_to, df.columns[-1]] == computed_expense[-1]
    return df.loc['Total operating expense', df.columns[-1]] == computed_expense[-1]

def total_equity_eq(df: DataFrameWithStringListTracking, end_index_s: str, compute=False, compare_to=None, add_missing_rows=False, change_sign=False, strict_compare=True, must_find_comb=False, facts_weight=None, reu_class=False):
    df_temp = 0
    df_temp = copy.deepcopy(df)
    compare_to_c = 0
    compare_to_c = copy.deepcopy(compare_to)
    end_pos = df_temp.df.index.get_loc(end_index_s)
    start_pos = df_temp.df.index.get_loc(TotalLiabilities) + 1
        # or 'Operating income'
    if compare_to is not None and change_sign:
        if find_combinations_with_logging(df_temp, start_pos, end_pos, compare_to_c, change_sign=True, change_base_sign=True, strict_compare=strict_compare, must_find_comb=must_find_comb, check_for_negative=True, facts_weight=facts_weight, reu_class=reu_class):
            df.df =df_temp.df
            return True
        else:
            return False

def total_liabilities_and_equity_eq(df: DataFrameWithStringListTracking, end_index_s: str, compute=False, compare_to=None, add_missing_rows=False, change_sign=False, strict_compare=True, must_find_comb=False, facts_weight=None, reu_class=False):
    df_temp = 0
    df_temp = copy.deepcopy(df)
    compare_to_c = 0
    compare_to_c = copy.deepcopy(compare_to)
    check_equal_total_assets = False

    start_pos = df_temp.df.index.get_loc(TotalAssets) + 1
    end_pos = df_temp.df.index.get_loc(end_index_s)
    if df_temp.df.loc[TotalAssets].equals(df_temp.df.loc[end_index_s]):
        check_equal_total_assets = True
    if check_equal_total_assets: # check if TotalLiabilities was reported
        must_find_comb = True
        if TotalLiabilities not in df_temp.df.index.tolist():
            pass
    if compare_to is not None and change_sign:
        if find_combinations_with_logging(df_temp, start_pos, end_pos, compare_to_c, change_sign=True, change_base_sign=True, strict_compare=strict_compare, must_find_comb=must_find_comb, check_for_negative=False, facts_weight=facts_weight, reu_class=reu_class):
            df.df =df_temp.df
            return True
        else:
            return False
    computed_expense = combine_variables(df_temp, start_pos, end_pos)
    if add_missing_rows or change_sign:
        df.df = df_temp.df
    if compute:
        return computed_expense
    if compare_to is not None:
        return compare_to.equals(computed_expense)
        return df.loc[compare_to, df.columns[-1]] == computed_expense[-1]
    return df.loc['Total operating expense', df.columns[-1]] == computed_expense[-1]

def total_of_something(df: DataFrameWithStringListTracking, start_index_s: str, end_index_s: str, compare_to=None, add_missing_rows=False, change_sign=False, strict_compare=True, change_base_sing=True, check_all_comb=False, must_find_comb=False, facts_weight=None, reu_class=False):
    df_temp = 0
    df_temp = copy.deepcopy(df)
    compare_to_c = 0
    compare_to_c = copy.deepcopy(compare_to)
    # Find the positions of the start and end index names
    if isinstance(start_index_s, int):
        start_index_s = df.df.index[start_index_s]
    start_pos = df_temp.df.index.get_loc(start_index_s)
    end_pos = df_temp.df.index.get_loc(end_index_s)
    if compare_to is not None and change_sign:
        if check_all_comb:
            if find_combinations_with_logging(df_temp, start_pos, end_pos, compare_to_c, change_sign=True, change_base_sign=change_base_sing, strict_compare=strict_compare, check_all_comb=check_all_comb, check_for_negative=True, reu_class=reu_class):
                df.df = df_temp.df
                return True
        else:
            if find_combinations_with_logging(df_temp, start_pos+1, end_pos, compare_to_c, change_sign=True, change_base_sign=change_base_sing, strict_compare=strict_compare, check_for_negative=False, reu_class=reu_class):
                df.df = df_temp.df
                return True
    return False
