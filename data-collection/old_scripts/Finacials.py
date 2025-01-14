import os
import pandas as pd
import numpy as np  # make sure to add
import requests
from bs4 import BeautifulSoup
import logging  # make sure to add
import calendar  # make sure to add
from headers import headers  # change to your own headers file or add variable in code
import sys
import random



class IncomeStatement:

    
# TODO ass a master attr to the df rows or maybe create a dict
# only assign the constant variables to variables that do not have a master

    def __init__(self, og_income_statement: pd.DataFrame, combined_statment: pd.DataFrame, rows_that_are_sum: list, rows_text: dict, cal_facts: dict):
        og_income_statement = rearrange_facts(og_income_statement)
        # og_income_statement = og_income_statement.round(2)
        self.og_income_statement = DataFrameWithStringListTracking(og_income_statement, rows_that_are_sum, rows_text, cal_facts)
        self.og_income_statement.compute_master_list2()
        print(self.og_income_statement.master_list_dict)
        self.income_statement = None
        self.combined_statment = combined_statment

    def find_fact_matching_combined_statement(self,df1_fact, df2, df2_fact_included):
        df2_fact_included_index = df2.index.get_loc(df2_fact_included)
        for df2_fact in df2.index.tolist()[:df2_fact_included_index+1]:
            if self.combined_statment is not None:
                if check_if_index_value_match(self.combined_statment, df2, df1_fact, df2_fact, strict_compare=True):
                    return df2_fact
        return False

    def map_income3(self):
        income_names = ['OperatingIncome', 'ProfitLoss', 'NetIncomeLoss', 'IncomeLossFromContinuingOperations', 'ComprehensiveIncomeNet', 'IncomeLoss', 'IncomeFromContinuingOperation']
        income_statment_map2 = [
        # include the other revenues that add total revenue on top of total revenue
        MapFact(fact=TotalRevenue, possible_names=['Revenue', 'Sales', 'Income'], highest=True),
        MapFact(fact='COGS', possible_names=['CostOfGoodsAndServicesSold', 'CostOfGoodsSold', 'CostOfGoods', 'CostOfRevenue', 'CostOfSale'], highest=True),
        MapFact(fact=GrossProfit, possible_names=['GrossProfit'],equation=IncomeStatement.gross_profit_eq),
        # SG&A could be multiple lines
        MapFact(fact='SG&A', possible_names=['SellingGeneralAndAdministrative', 'SellingAndMarketing', 'GeneralAndAdministrative'], highest=True),
        MapFact(fact='R&D', possible_names=['ResearchAndDevelopment'], highest=True),
        MapFact(fact='Amoritization', possible_names=['Amortization'], highest=True),
        MapFact(fact='Depreciation', possible_names=['Depreciation'], highest=True),
        MapFact(fact='Other operating expenses', possible_names=['OtherOperatingIncomeExpense']),
        MapFact(fact='Total operating expense', possible_names=['OperatingExpenses'], equation=IncomeStatement.total_operating_expense_eq), #  equation="sum of everythin agter Gross profit",
        MapFact(fact='C&E', possible_names=['CostsAndExpenses', 'LossesAndExpenses'], equation=IncomeStatement.costs_and_expenses_eq),
        MapFact(fact=OperatingIncome, possible_names=['OperatingIncome', 'IncomeLossFromContinuingOperations', 'ProfitLoss'], equation=IncomeStatement.operating_income_eq), # equation="Gross profit - Total operating expense", 
        MapFact(fact='Interest expense', possible_names=['InterestExpense'], strict_compare=True),
        MapFact(fact='Interest and investment income', possible_names=['InvestmentIncomeInterest', 'InterestAndOtherIncome'], strict_compare=True),
        MapFact(fact='Cureency Exchange', possible_names=[]),
        # MapFact(fact='Merger & Restructuring Charges', possible_names=['Restructuring']),
        MapFact(fact='Other non-operating income (expense)', possible_names=['OtherNonoperatingIncomeExpense']),
        MapFact(fact='Total non-operating income (expense)', possible_names=['NonoperatingIncomeExpense', 'Nonoperating'], equation=IncomeStatement.total_non_operating_expense_eq),
        MapFact(fact=EBT, possible_names=income_names, equation=IncomeStatement.EBT_eq),
        # put other rows under this and calculate EBT again with these unusual items
        # Merger & Restructuring Charges, Gain (Loss) On Sale Of Investments, Gain (Loss) On Sale Of Assets, Asset Writedown, Other Unusual Items
        MapFact(fact='Income tax expense', possible_names=['IncomeTaxExpense']),
        MapFact(fact=NetIncome, possible_names=income_names, equation=IncomeStatement.net_income_eq), #  equation="EBT - Income tac expense",
        MapFact(fact=MinorityInterest, possible_names=['AttributableToNoncontrollinterest', 'AttributableToNoncontrollingInterest']),
        # MapFact(fact='Net income without extra unusal items', possible_names=['ProfitLoss', 'NetIncomeLoss', 'IncomeLossFromContinuingOperations', 'ComprehensiveIncomeNet']),
        MapFact(fact='Earnings Per Share Basic', possible_names=['EarningsPerShareBasic']),
        MapFact(fact='Earnings Per Share Diluted', possible_names=['EarningsPerShareDiluted']),
        MapFact(fact='Weighted Average Number Of Shares Outstanding Basic', possible_names=['WeightedAverageNumberOfSharesOutstandingBasic']),
        MapFact(fact='Weighted Average Number Of Diluted Shares Outstanding', possible_names=['WeightedAverageNumberOfDilutedSharesOutstanding']),
        # MapFact(fact='C&E', possible_names=['CostsAndExpenses']),
        # MapFact(fact='Minority Interest', possible_names=['AttributableToNoncontrollinterest'])
    ]
        def check_for_net_income(df: DataFrameWithStringListTracking, data_fact):
            # TODO : every time a new income is foud, rename to make new income the lowest and in order
            # base_var = NetIncome
            for ni_w in [NetIncome_with_unusal_items_1, NetIncome_with_unusal_items_2, NetIncome_with_unusal_items_3, NetIncome_with_unusal_items_4]:
                if ni_w not in df.df.index.tolist():
                    break
            if NetIncome not in df.df.index.tolist():
                if IncomeStatement.net_income_eq(df, data_fact, compare_to=df_og.df.loc[data_fact], add_missing_rows=True, change_sign=True, strict_compare=True):
                    index_map = {data_fact: NetIncome}
                    df = rename_df_index(df, index_map)
                    # index_map = {data_fact: NetIncome}
                    # # Update the index
                    # df.df.rename(index=index_map, inplace=True)
                    # # TODO: this is wrong becz NetIncome keep changing
                    # df.facts_name_dict[data_fact] = ni_w
                    return True
            elif IncomeStatement.net_income_inc_unusual_eq(df, NetIncome, data_fact ,compare_to=df_og.df.loc[data_fact], strict_compare=True):
                index_map = {NetIncome: ni_w, data_fact: NetIncome}
                df = rename_df_index(df, index_map)
                # # Update the index
                # df.df.rename(index=index_map, inplace=True)
                # # TODO: this is wrong becz NetIncome keep changing
                # df.facts_name_dict[data_fact] = ni_w
                return True
            return False
        
        # TODO: deal with repeated data_facts which will show with ":" in thier name.
        # they can either be repeated and miss up the equation or they can added wihch will equal the main data_fact without the ":"

        df_og = self.og_income_statement
        df = 0
        df = self.og_income_statement
        # Dictionary to keep track of mappings and if they have been defined
        DATA_ADDED = False
        first_sum_is_revenue = False
        last_mf_found = 0
        last_mf_found_with_equation = 0
        last_total_of_something = None
        income_statment_current_milestone = None
        net_income_subfacts = []
        found_net_income_subfacts = False
        # TODO update df.facts_name_dict for every rename
        for data_fact_index, data_fact in enumerate(df_og.df.index.tolist()):
            df.compute_master_list2()
            print(df.master_list_dict)
            print(f'====={data_fact}')
            print(df.df)
            data_fact_mfs = []
            mf_found = False
            DATA_ADDED = False
            if ":" in data_fact:
                continue
            cases = ['s1', 's2', 's3', 's4', 's5', 's6', 'd']
            for c in cases:
                match c:
                    case 's1': # check for minority interest
                            if ('AttributableToNoncontrollingInterest' in data_fact or 'AttributableToNoncontrollingEntity' in data_fact) and not 'IncludingPortionAttributableToNoncontrollingInterest' in data_fact:
                                # minority interest, the other variable should be net income
                                # other variable could be before or after data_fact
                                df_index = df.df.index.get_loc(data_fact)
                                new_MI = MinorityInterest
                                while new_MI in df.df.index.tolist():
                                    new_MI += '_2' 
                                index_map = {data_fact:new_MI}
                                df = rename_df_index(df, index_map)
                                DATA_ADDED = True
                                if not (NetIncome in df.df.index[df_index - 1] or  EBT in df.df.index[df_index - 1] or OperatingIncome in df.df.index[df_index - 1]):
                                    maybe_net_income = df.df.index[df_index - 1]
                                    # Swapping the values and index
                                    print(df.df)
                                    df.df.iloc[[df_index, df_index - 1]] = df.df.iloc[[df_index - 1, df_index]].values
                                    df.df.index.values[[df_index, df_index - 1]] = df.df.index.values[[df_index - 1, df_index]]
                                    if check_for_net_income(df, maybe_net_income):
                                        last_mf_found_with_equation = NetIncome
                                    print(df.df)
                                    DATA_ADDED = True
                    case 's2': # check rows thar are class reu
                        if data_fact in df_og.rows_that_are_sum and TotalRevenue not in df.df.index.tolist():
                            # if total revenue is not defined the first sum is total revenue
                            # TODO compare with combined_statement to find total revennue
                            print(df.master_list_dict)
                            total_revenue = self.find_fact_matching_combined_statement(TotalRevenue, df.df, data_fact)
                            if total_revenue == data_fact:
                                index_map = {data_fact:TotalRevenue}
                                df = rename_df_index(df, index_map)
                                DATA_ADDED = True
                                last_mf_found_with_equation = TotalRevenue
                            else:
                                if total_revenue:
                                    if (total_revenue != data_fact and (df.df.loc[total_revenue] == df.df.loc[data_fact]).all()):
                                        total_revenue = data_fact
                                    index_map = {data_fact:TotalRevenue}
                                    df = rename_df_index(df, index_map)
                                    income_statment_map2[0].match = total_revenue
                                    DATA_ADDED = True
                                    last_mf_found_with_equation = TotalRevenue
                                # if first_sum_is_revenue:
                                index_map = {data_fact:TotalRevenue}
                                df = rename_df_index(df, index_map)
                                income_statment_map2[0].match = data_fact
                                DATA_ADDED = True
                                last_mf_found_with_equation = TotalRevenue
                        if data_fact in df_og.rows_that_are_sum and NetIncome in df.df.index.tolist():
                            # if total revenue is not defined the first sum is total revenue
                            # TODO compare with combined_statement to find total revennue
                            if check_for_net_income(df, data_fact):
                                last_mf_found_with_equation = NetIncome
                                DATA_ADDED = True                     
                        last_match_reached = False
                        for index in range(len(income_statment_map2)):
                            mf = income_statment_map2[index]
                            # do not start before reaching last match
                            if mf.fact == last_mf_found_with_equation or last_mf_found_with_equation == 0:
                                last_match_reached = True
                            if not last_match_reached:
                                continue
                            if mf_found:
                                break
                            if mf.match is not None:
                                continue
                            for possible_name in mf.possible_names:
                                print(possible_name, data_fact)
                                if mf.strict_compare:
                                    data_fact_filtered = data_fact.split("_")[-1]
                                    if possible_name == data_fact_filtered:
                                        mf.matches.append(data_fact)
                                        data_fact_mfs.append(mf)
                                        mf_found = True
                                        break # ensure that you append it once
                                else:
                                    if possible_name in data_fact:
                                        mf.matches.append(data_fact)
                                        data_fact_mfs.append(mf)
                                        mf_found = True
                                        break # ensure that the order of the restriction matte
                        # renmae only if there is any matches
                        if data_fact_mfs:
                            mf = data_fact_mfs[0]
                            #     # TODO make calc if needed fot total expense
                            print(f"====={mf.fact}")
                            if mf.equation:
                                try:
                                    satisfy_equation = mf.call_eq(df, data_fact, compare_to=df_og.df.loc[data_fact], change_sign=True)
                                except:
                                    satisfy_equation = False
                                if satisfy_equation:
                                    # TODO change index name instead of asigning a new row
                                    index_map = {data_fact: mf.fact}
                                    df = rename_df_index(df, index_map)
                                    # df.df.rename(index=index_map, inplace=True)
                                    mf.match = data_fact
                                    # df.facts_name_dict[data_fact] = mf.fact
                                    last_mf_found_with_equation = mf.fact
                                    DATA_ADDED= True
                            elif TotalRevenue not in df.df.index.tolist():
                                if (df.df.iloc[data_fact_index] == df.df.iloc[data_fact_index + 1]).all():
                                    continue
                                if self.combined_statment is not None and not first_sum_is_revenue:
                                    total_revenue = self.find_fact_matching_combined_statement(TotalRevenue, df.df, data_fact)
                                    if total_revenue == data_fact:
                                        index_map = {data_fact: TotalRevenue}
                                        # Update the index
                                        df = rename_df_index(df, index_map)
                                        # df.df.rename(index=index_map, inplace=True)
                                        # mf.match = data_fact
                                        income_statment_map2[0].match = data_fact
                                        # df.facts_name_dict[data_fact] = TotalRevenue
                                        DATA_ADDED = True
                                        last_mf_found_with_equation = TotalRevenue
                                        continue
                                    else:
                                        if total_revenue and ":" not in total_revenue:
                                            index_map = {total_revenue: TotalRevenue}
                                            # Update the index
                                            df = rename_df_index(df, index_map)
                                            # df.df.rename(index=index_map, inplace=True)
                                            # mf.match = data_fact
                                            income_statment_map2[0].match = total_revenue
                                            # df.facts_name_dict[total_revenue] = TotalRevenue
                                            DATA_ADDED = True
                                            last_mf_found_with_equation = TotalRevenue
                                # check if the first sum COGS or Gross profit
                                try: # sometimes there is no rows_that_are_sum
                                    for possible_name in ['CostOfGoodsAndServicesSold', 'CostOfGoodsSold', 'CostOfGoods', 'CostOfRevenue', 'CostOfSale', 'GrossProfit']:
                                        # data_fact_filtered = data_fact.split("_")[-1]
                                        # TODO: usinf mf , wehere I only have the mf.fact
                                        # Get the subset of the DataFrame from the start to the given index
                                        position = df.df.index.get_loc(df.rows_that_are_sum[0])
                                        subset_df = df.df.iloc[:position+1]
                                        # Check if all values in the subset are positive
                                        all_values_positive = (subset_df >= 0).all().all()
                                        if possible_name in df.rows_that_are_sum[0] and not all_values_positive:
                                            if mf.match is None:
                                                index_map = {data_fact: mf.fact}
                                                df = rename_df_index(df, index_map)
                                                # df.df.rename(index=index_map, inplace=True)
                                                mf.match = data_fact
                                                # df.facts_name_dict[data_fact] = mf.fact
                                                DATA_ADDED = True
                                    for possible_name in ['Revenue', 'Sales']:
                                        print(df.rows_that_are_sum)
                                        # TODO the second sum could be total revenue
                                        # TODO i require all entries to be positive but this migh not alwyas be the case
                                        # how to check if ht esum if gross profit of total revenue
                                        if (df.df.loc[:df.rows_that_are_sum[0]] >= 0).all().all() and possible_name in df.rows_that_are_sum[0] and (combine_variables(df, 0, df.df.index.get_loc(df.rows_that_are_sum[0])) == df.df.loc[df.rows_that_are_sum[0]]).all():
                                            first_sum_is_revenue = True
                                            break
                                        if (df.df.loc[:df.rows_that_are_sum[0]] >= 0).all().all() and possible_name in df.rows_that_are_sum[0] and ("total revenue" in df.rows_text[df.rows_that_are_sum[0]].lower() or "revenue" == df.rows_text[df.rows_that_are_sum[0]].lower()): # (combine_variables(df, 0, df.df.index.get_loc(df.rows_that_are_sum[0])) == df.df.loc[df.rows_that_are_sum[0]]).all():
                                            first_sum_is_revenue = True
                                            break
                                    # first row could be a sum of class "reu" but it will reach here because Ttoal revenue does not have eqaution
                                    if first_sum_is_revenue and df.rows_that_are_sum[0] != data_fact:
                                        continue
                                except Exception as e:
                                    pass
                                if mf.fact == TotalRevenue and ":" not in data_fact:# and df_og.variable_in_list(data_fact) == None:
                                    index_map = {data_fact: TotalRevenue}
                                    # Update the index
                                    df = rename_df_index(df, index_map)
                                    # df.df.rename(index=index_map, inplace=True)
                                    # mf.match = data_fact
                                    income_statment_map2[0].match = data_fact
                                    # df.facts_name_dict[data_fact] = TotalRevenue
                                    DATA_ADDED = True
                                    last_mf_found_with_equation = TotalRevenue
                
                            # elif df_og.variable_in_list(data_fact):
                            #         continue
                            elif mf.match is None:
                                index_map = {data_fact: mf.fact}
                                df = rename_df_index(df, index_map)
                                # df.df.rename(index=index_map, inplace=True)
                                mf.match = data_fact
                                # df.facts_name_dict[data_fact] = mf.fact
                                DATA_ADDED = True
                                last_mf_found_with_equation = mf.fact # used to be TotalRevenue for some reason
                        if NetIncome in df.df.index.tolist() and not DATA_ADDED:
                            check_new_net_income = False
                            for possible_income_name in income_names:
                                if possible_income_name in data_fact:
                                    check_new_net_income = True
                                    break
                            if check_new_net_income:
                                # TODO : every time a new income is foud, rename to make new income the lowest and in order
                                base_var = NetIncome
                                for ni_w in [NetIncome_with_unusal_items_1, NetIncome_with_unusal_items_2, NetIncome_with_unusal_items_3, NetIncome_with_unusal_items_4]:
                                    if ni_w not in df.df.index.tolist():
                                        break
                                print(df.df)
                                if IncomeStatement.net_income_inc_unusual_eq(df, base_var, data_fact ,compare_to=df_og.df.loc[data_fact], strict_compare=True):
                                    index_map = {base_var: ni_w, data_fact: NetIncome}
                                    # Update the index
                                    df = rename_df_index(df, index_map)
                                    # df.df.rename(index=index_map, inplace=True)
                                    # mf.match = data_fact
                                    last_mf_found_with_equation = NetIncome
                                    # TODO: this is wrong becz NetIncome keep changing
                                    # df.facts_name_dict[data_fact] = ni_w
                                    DATA_ADDED = True
                if DATA_ADDED:
                    break
        self.income_statement = df





class BalanceSheet:


    ## NOTE when writing function it seems you pass by pointer and you can change inside df 


    def __init__(self, og_balance_sheet: pd.DataFrame, combined_statment: pd.DataFrame, rows_that_are_sum: list, rows_text: dict, cal_facts: dict):
        # og_income_statement = rearrange_facts(og_income_statement)
        # og_income_statement = og_income_statement.round(2)
        self.og_balance_sheet = DataFrameWithStringListTracking(og_balance_sheet, rows_that_are_sum, rows_text, cal_facts)
        self.og_balance_sheet.compute_master_list2()
        print(self.og_balance_sheet.master_list_dict)
        self.balance_sheet = None
        self.combined_statment = combined_statment

    def find_fact_matching_combined_statement(self,df1_fact, df2, df2_fact_included):
        df2_fact_included_index = df2.index.get_loc(df2_fact_included)
        for df2_fact in df2.index.tolist()[:df2_fact_included_index+1]:
            if self.combined_statment is not None:
                if check_if_index_value_match(self.combined_statment, df2, df1_fact, df2_fact, strict_compare=True):
                    return df2_fact
        return False

    def map_balance(self):
        string_rank = [TotalLiabilitiesAndEquity, NonLiabilitiesCurrent, LiabilitiesCurrent, NonCurrentAssets, CurrentAssets, StockholdersEquity, TotalEquity, TotalLiabilities, TotalAssets]
        balance_sheet_map = [
        MapFact(fact=CashAndCashEquivalent, possible_names=['CashAndCashEquivalent'], pattern=[r'\bCash(?:And)?Cash(?:And)?Equivalent\b'], highest=True),
        MapFact(fact=AccountsReceivable, possible_names=['AccountsReceivable'], pattern=[r'\bAccounts?Receivable\b'], highest=True),
        MapFact(fact=RestrictedCash, possible_names=['RestrictedCash'], pattern=[r'\bRestrictedCash\b'], highest=True),
        MapFact(fact=OtherAssetsCurrent, possible_names=['OtherAssetsCurrent'], pattern=[r'\bOtherAssets?Current\b'], highest=True),
        MapFact(fact=CurrentAssets, possible_names=['AssetsCurrent', 'CurrentAssets'], pattern=[r'\b(?:AssetsCurrent|CurrentAssets?)\b'], equation=BalanceSheet.total_current_assets_eq),
        MapFact(fact=PropertyPlantAndEquipment, possible_names=['PropertyPlantAndEquipment'], pattern=[r'\bPropertyPlant(?:And)?Equipment\b'], highest=True),
        MapFact(fact=Goodwill, possible_names=['Goodwill'], pattern=[r'\bGoodwill\b'], highest=True),
        MapFact(fact=IntangibleAssets, possible_names=['IntangibleAssets'], pattern=[r'\bIntangibleAssets?\b'], highest=True),
        MapFact(fact=OtherAssetsNoncurrent, possible_names=['OtherAssetsNoncurrent'], pattern=[r'\bOtherAssets?Noncurrent\b'], highest=True),
        MapFact(fact=NonCurrentAssets, possible_names=['NoncurrentAssets', 'AssetsNoncurrent'], pattern=[r'\b(?:Noncurrent|Assets?)Assets?\b'], equation=BalanceSheet.total_non_current_assets_eq),
        MapFact(fact=TotalAssets, possible_names=['Assets'], pattern=[r'\b(?:Total)?Assets\b'], can_repeat=True, equation=BalanceSheet.total_assets_eq),
        MapFact(fact=AccountsPayable, possible_names=['AccountsPayable'], pattern=[r'\bAccounts?Payable\b'], highest=True),
        MapFact(fact=ShortTermDebtCurrent, possible_names=['ShortTermDebt', 'ShortTermBorrowing'], pattern=[r'\bShortTermDebtCurrent\b', r'\bShortTermBorrowingCurrent\b']),
        MapFact(fact=LongTermDebtCurrent, possible_names=['LongTermDebt', 'LongTermDebtCurrent'], pattern=[r'\bLongTermDebtCurrent\b', r'\bLongTermDebt\b']),
        MapFact(fact=LiabilitiesCurrent, possible_names=['LiabilitiesCurrent', 'CurrentLiabilities'], pattern=[r'\bLiabilitiesCurrent\b', r'\bCurrentLiabilities\b'], equation=BalanceSheet.total_current_liabilities_eq),
        MapFact(fact=ShortTermDebt, possible_names=['ShortTermDebt', 'ShortTermBorrowing'], pattern=[r'\bShortTermDebt\b', r'\bShortTermBorrowing\b']),
        MapFact(fact=LongTermDebt, possible_names=['LongTermDebt'], pattern=[r'\bLongTermDebt\b']),
        MapFact(fact=DeferredTaxLiabilityNonCurrent, possible_names=['DeferredIncomeTaxLiabilitie'], pattern=[r'\bDeferred(?:Income)?TaxLiabilit(?:ies|y)\b']),  
        MapFact(fact=OtherLiabilitiesNoncurrent, possible_names=['OtherLiabilitiesNoncurrent'], pattern=[r'\bOtherLiabilities?Noncurrent\b']),
        MapFact(fact=NonLiabilitiesCurrent, possible_names=['NoncurrentLiabilities', 'LiabilitiesNonCurrent'], pattern=[r'\bNoncurrentLiabilities\b', r'\bLiabilities?NonCurrent\b'], equation=BalanceSheet.total_non_current_liabilities_eq),
        MapFact(fact=TotalLiabilities, possible_names=['TotalLiabilities', 'Liabilities'], pattern=[r'\bTotalLiabilities\b', r'\bLiabilities\b'], can_repeat=False, equation=BalanceSheet.total_current_liabilities_eq),
        MapFact(fact=RetainedEarnings, possible_names=['RetainedEarnings'], pattern=[r'\bRetainedEarnings\b']),
        MapFact(fact=StockholdersEquity, possible_names=['StockholdersEquity', 'Equity'], pattern=[r'\bStockholders?Equity\b', r'\bEquity\b'], can_repeat=False, equation=BalanceSheet.total_stockholders_equity_eq),
        MapFact(fact=TotalEquity, possible_names=['StockholdersEquity', 'Equity'], pattern=[r'\bTotal?Equity\b', r'\bEquity\b'], can_repeat=True, equation=BalanceSheet.total_equity_eq),
        MapFact(fact=TotalLiabilitiesAndEquity, possible_names=['LiabilitiesAndStockholdersEquity', 'EquityAndLiabilities'], pattern=[r'\bLiabilitiesAndStockholdersEquity\b', r'\bEquityAndLiabilities\b'], equation=BalanceSheet.total_liabilities_and_equity_eq),
    ]
        def find_possible_names(data_fact, last_mf_found_with_equation, check_for_equation=True):
            last_match_reached = False
            for index in range(len(balance_sheet_map)):
                mf = balance_sheet_map[index]
                # do not start before reaching last match
                if mf.fact == last_mf_found_with_equation or last_mf_found_with_equation == 0:
                    last_match_reached = True
                if not last_match_reached:
                    continue
                if check_for_equation:
                    if mf.equation is None:
                        continue
                if mf.match is not None and not mf.can_repeat:
                    continue
                print(f'====={mf.fact}', last_mf_found_with_equation)
                for possible_name in mf.possible_names:
                    print(possible_name, data_fact)
                    if mf.strict_compare:
                        data_fact_filtered = data_fact.split("_")[-1]
                        if possible_name == data_fact_filtered:
                            mf.matches.append(data_fact)
                            data_fact_mfs.append(mf)
                            mf_found = True
                            break
                for possible_name in mf.possible_names:
                    print(possible_name, data_fact)
                    if possible_name.lower() in data_fact.lower():
                        mf.matches.append(data_fact)
                        data_fact_mfs.append(mf)
                        break
            return data_fact_mfs

        # TODO: deal with repeated data_facts which will show with ":" in thier name.
        # they can either be repeated and miss up the equation or they can added wihch will equal the main data_fact without the ":"

        df_og = self.og_balance_sheet
        df = 0
        df = self.og_balance_sheet
        # Dictionary to keep track of mappings and if they have been defined
        DATA_ADDED = False
        last_mf_found = 0
        last_mf_found_with_equation = 0
        last_total_of_something = None
        # TODO update df.facts_name_dict for every rename
        for data_fact in (df_og.df.index.tolist()):
            df.compute_master_list2()
            print(df.master_list_dict)
            print(f'====={data_fact}')
            print(df.df)
            data_fact_mfs = []
            mf_found = False
            DATA_ADDED = False
            if ":" in data_fact:
                continue
            cases = ['s1', 's2', 's3', 's4', 's5', 's6', 'd']
            # TODO
            # TODO
            # TODO: moving rows around is missing the order of indexes and the loop !!
            for c in cases:
                match c:
                    case 's1': # check rows thar are cal_xml
                        if df.cal_facts:
                            if data_fact in df.cal_facts:
                                data_fact_mfs = find_possible_names(data_fact, last_mf_found_with_equation)
                                data_fact_slaves = get_facts_by_key(df.cal_facts, data_fact)
                                data_fact_slaves_weight = get_weight_by_key(df.cal_facts, data_fact)
                                print(data_fact_slaves)
                                move_above=True

                                # check if the slaves are from different sheets
                                if data_fact_slaves:
                                    none_in_list2 = all(s not in df_og.df.index.tolist() for s in data_fact_slaves)
                                    print(none_in_list2)
                                if not none_in_list2:
                                        
                                    # check for missing slaves
                                    if data_fact_mfs:
                                        if len(data_fact_mfs) > 1:
                                            print(string_rank.index(data_fact_mfs[0].fact) ,string_rank.index(data_fact_mfs[1].fact))
                                            if string_rank.index(data_fact_mfs[0].fact) < string_rank.index(data_fact_mfs[1].fact):
                                                mf = data_fact_mfs[0]
                                            else:
                                                mf = data_fact_mfs[1]
                                        else:
                                            mf = data_fact_mfs[0]
                                    if last_mf_found_with_equation == 0:
                                        start_idx = df.df.index[last_mf_found_with_equation]
                                    else:
                                        start_idx = last_mf_found_with_equation
                                # TODO if you have equation (data_fact_slaves) check if these are the only variables, to catch sums that are itermediate 
                                # befor you pass must_find_comb=True !!!
                                                            # TODO: from self.cal_facts get the signs and use them to for the equation
                                # balance sheet does not change the signs of the equation
                                    print(data_fact_slaves, data_fact)
                                    print("==")
                                    # TODO any missing row from the sum but in equation, move it to inlcude it in the equation
                                    if data_fact_mfs:
                                        if mf.fact == TotalLiabilitiesAndEquity and TotalLiabilities in df.df.index.tolist():
                                            start_idx = TotalAssets
        
                                    data_fact_index = df.df.index.get_loc(data_fact)
                                    facts_misplaced = compare_variable_lists(data_fact_slaves, df.df.index[df.df.index.get_loc(start_idx):data_fact_index], df.facts_name_dict, df.master_list_dict)
                                    print(facts_misplaced)
                                    # Identify rows with duplicates (rows that contain ":")
                                    duplicated_rows = df.df[df.df.index.str.contains(":")]
                                    print(duplicated_rows)
                                    # Extract the base facts (main facts) without the colon part
                                    base_facts = duplicated_rows.index.str.split(":").str[-1]
                                    for f_mis in facts_misplaced:
                                        if f_mis in df.df.index.tolist():
                                            # Remove the misplaced fact from its current position
                                            current_index = df.df.index.get_loc(f_mis)
                                            # Determine the new index based on move_above flag
                                            if move_above:
                                                new_index = data_fact_index
                                                if new_index > current_index:
                                                    new_index -= 1  # Adjust for removal shift
                                                data_fact_index += 1  # Adjust the data_fact_index if we are moving above
                                            else:
                                                new_index = data_fact_index + 1
                                            # Move the misplaced fact to the new position
                                            df.df = move_fact_to_new_position(df.df, f_mis, new_index)
                                            # move dependent facts
                                            if f_mis in base_facts:
                                                # Identify the duplicate rows that correspond to the current main fact
                                                duplicates_to_insert = duplicated_rows[duplicated_rows.index.str.endswith(f_mis)]
                                                for dup_index in duplicates_to_insert.index:
                                                    df.df = move_fact_to_new_position(df.df, dup_index, new_index)
                                    print(df.df)
                                    print("===")
                                    print(df.cal_facts[data_fact])
                                    if data_fact_mfs:
                                        # check for missing slaves
                                        if last_mf_found_with_equation == 0:
                                            start_idx = df.df.index[last_mf_found_with_equation]
                                        else:
                                            start_idx = last_mf_found_with_equation
                                        try:
                                            if mf.call_eq(df, data_fact, compare_to=df_og.df.loc[data_fact], add_missing_rows=True, change_sign=True, strict_compare=False, facts_weight=df.cal_facts[data_fact], reu_class=True):
                                                if mf.can_repeat and mf.match is not None:
                                                    print(df.facts_name_dict, mf.fact)
                                                    old_mf = get_key_by_fact2(df.facts_name_dict, mf.fact)
                                                    if old_mf in df.facts_name_dict:
                                                        del df.facts_name_dict[old_mf]
                                                    index_map = {mf.fact: old_mf, data_fact: mf.fact}
                                                else:
                                                    index_map = {data_fact: mf.fact}
                                                # Update the index
                                                df = rename_df_index(df, index_map)
                                                mf.match = data_fact
                                                last_mf_found_with_equation = mf.fact
                                                DATA_ADDED = True
                                                mf_found = True
                                                # break
                                        except Exception as e:
                                            print(e)
                                            pass                  
                if DATA_ADDED:
                    break
        self.balance_sheet = df