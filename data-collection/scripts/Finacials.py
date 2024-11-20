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



class Cell:
    def __init__(self):
        pass

class Row:
    def __init__(self):
        pass

class Table:
    def __init__(self):
        pass

class Inocme_statment:
    """ 
    Revenue
    COGS
    Gross profit = Revenue - COGS
    Gross margin = Gross profit / Revenue
    SG&A
    R&D
    Depreciation & amoritization (could be seperate entries)
    Total operating expense = SG&A + R&D + Depreciation & amoritization
    Operating income = Gross profit - Total operating expense
    Operating margin = Operating income / Revenue
    Interest expense
    Interest and investment income
    Other non-operating income (expense)
    Eearning Before Taxes = operating income =(-?) sum of Interset expenses + other non-operating expense
    Income tax expense
    Net income = Erning from continuing operatoins = EBT - income tax expense
    Earnings Per Share Basic And Diluted
    Earnings Per Share Basic
    Earnings Per Share Diluted	
    Weighted Average Number Of Shares Outstanding Basic
    Weighted Average Number Of Diluted Shares Outstanding
    """
    income_statment_map =   {'revenue': ['first',['Revenue', 'Sales']],
                             'Gross profit': ['below revenue', ['GrossProfit']],
                             'COGS': ['below revenue', ['CostOfGoodsAndServicesSold', 'COGS']],
                             'SG&A': ['below revenue', ['SellingGeneralAndAdministrative']]
                            }            # ['revenue', 'COGS', 'gross_profit', 'SG&A']

    def __init__(self, data):
        self.data = data
        self.mapped_data_facts = {}

    def map_data(self, df, data, map):
        temp_mapped_data_facts = {}
        for map_fact, fact_restrictions in map.items():
            temp_mapped_data_facts[map_fact] = None
            data_fact_matches = []
            for data_fact in data.index.tolist():
                for restir in fact_restrictions[1]:
                    if restir in data_fact:
                        data_fact_matches.append(data_fact)
                        temp_mapped_data_facts[map_fact] = data_fact
                        df = df.rename(index={data_fact: map_fact})
                        break # fix
        return df

                

class Balance_sheet:
    """ 
    Total assets = Total liabilties + Equity
    Current assets:
        cash and equibalents
        short term investment
        accounts receivable
        inventory
        prepaid expense
        deferred tas assets current
        other current assets
    total current assets
    Non-current assets:
        Gross property plant and equipment
        Lonh term investment
        Goodwill
        Other intangibles
        Deferred tax assets long term
        other long term assets
    Total assets = current assets + non-current assets

    Current liabilities:
        accounts payable
        accrued expenses
        short term debt
        current porion of long term debt
        other current liabilites
    total current liabilities
    Non-current liabilities:
        Long term debt
        capital leases
        deferred tax liability
        other non current liabilities
    Total liabilities

    Equity:
        total prefered equity

        common stock
        additional pain in capital
        retained earnings
        treasury stock
        comprehinsive inocme and other
        Total common equity
    Total equity = total prefered equity + total common equity
    """
    def __init__(self):
        pass