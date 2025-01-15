import pandas as pd
import re
from typing import List, Dict, Tuple



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



