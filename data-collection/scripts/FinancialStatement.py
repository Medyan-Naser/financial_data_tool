import pandas as pd
import re
from typing import List, Dict, Tuple
from constants import *




class FinancialStatement():

    def __init__(self, df: pd.DataFrame, rows_that_are_sum: list, rows_text: dict, cal_facts: dict, sections_dict={}):
        """
        Initialize the DataFrame and the master list tracking dictionary.
        """
        self.df = df
        self.rows_that_are_sum = rows_that_are_sum
        self.rows_text = rows_text #####
        print(df)
        print(rows_that_are_sum)
        self.master_list_dict = {} # {idx: [] for idx in self.df.index}
        self.facts_name_dict = {}
        self.special_master_dict = {}
        print(cal_facts)
        self.cal_facts = cal_facts
        self.unit = None
        self.sections_dict = sections_dict ####
        self.mapped_facts = []

        temp_dict = {}
        for key in sections_dict.keys():
            temp_dict[key] = {'start' : None, 'end' : None}
        self.sections_indxs = {}
        self.facts_mfs = {}
        self.found_total_assets = None

class IncomeStatement(FinancialStatement):
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

class BalanceSheet(FinancialStatement):
    pass

class CashFlow(FinancialStatement):
    pass