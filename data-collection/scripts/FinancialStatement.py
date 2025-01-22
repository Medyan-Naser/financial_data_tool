import pandas as pd
import re
from typing import List, Dict, Tuple
from constants import *
from statement_maps import *



class FinancialStatement():

    def __init__(self, og_df: pd.DataFrame, rows_that_are_sum: list, rows_text: dict, cal_facts: dict, sections_dict={}):
        """
        Initialize the DataFrame and the master list tracking dictionary.
        """
        self.og_df = og_df
        self.mapped_df = None
        self.rows_that_are_sum = rows_that_are_sum
        self.rows_text = rows_text #####
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
    IncomeStatementMap = IncomeStatementMap()

    def create_zeroed_df_from_map(self):
        # Extract row labels from the MapFact attributes in IncomeStatementMap
        map_facts = vars(self.IncomeStatementMap)
        print("=====map facts=======")
        print(map_facts)
        # row_labels = [getattr(map_facts[key], 'fact') for key in map_facts]
        row_labels = [getattr(fact, 'fact') for fact in map_facts.values() if isinstance(fact, MapFact)]
        print("=====row_labels=======")
        print(row_labels)
        # Get column headers from the input DataFrame (dates)
        column_labels = self.og_df.columns
        
        # Create a new DataFrame with row labels and column headers, initially filled with zeros
        zeroed_df = pd.DataFrame(0, index=row_labels, columns=column_labels)
        
        self.mapped_df = zeroed_df

    def map_facts(self):
        # Extract all the facts and patterns from the IncomeStatementMap
        map_facts = vars(self.IncomeStatementMap)
        
        # Iterate through each row in the original dataframe
        for idx, row in self.og_df.iterrows():
            found_match = False
            print(f"Checking row '{idx}'...")

            # Extract the human string from rows_text using the row index
            human_string = self.rows_text.get(idx, "")
            print(f"Human string for {idx}: {human_string}")
            
            # Iterate over each MapFact
            for fact_name, map_fact in map_facts.items():
                if found_match:
                    break
                if isinstance(map_fact, MapFact):
                    # Check if any of the GAAP patterns match the row index (for GAAP)
                    for pattern in map_fact.gaap_pattern:
                        if re.search(pattern, idx):
                            # If a GAAP pattern matches, copy the row to the mapped_df under the corresponding fact row
                            fact_row = map_fact.fact
                            self.mapped_df.loc[fact_row] = row
                            print(f"GAAP match found for '{idx}' with pattern '{pattern}'. Mapped to fact '{fact_row}'")
                            found_match = True
                            break
                    
                    # Check if any of the human patterns match the human string
                    print(map_fact.fact)
                    for pattern in map_fact.human_pattern:
                        if re.search(pattern, human_string):
                            # If a human pattern matches, copy the row to the mapped_df under the corresponding fact row
                            fact_row = map_fact.fact
                            self.mapped_df.loc[fact_row] = row
                            print(f"Human match found for '{idx}' with pattern '{pattern}'. Mapped to fact '{fact_row}'")
                            found_match = True
                            break
        
    

class BalanceSheet(FinancialStatement):
    pass

class CashFlow(FinancialStatement):
    pass