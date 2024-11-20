import pandas as pd
import re
from typing import List, Dict, Tuple


# sections
FIRST_SECTION = "FIRST SECTION"

NO_EQUATION_ERROR = "NO_EQUATION_ERROR"
FACT_NOT_REPORTED = "FACT_NOT_REPORTED"
FACT_CALCULATED = "FACT_CALCULATED"

# sum types
SUM_TOTAL = "SUM_TOTAL"
EQUATION_TOTAL = "EQUATION_TOTAL"

## income statement
GrossProfit = 'Gross profit'
OperatingIncome = 'Operating income'
EBT = 'EBT'
NetIncome = 'Net income'
NetIncome_with_unusal_items_1 = 'Net income including unusal items 1'
NetIncome_with_unusal_items_2 = 'Net income including unusal items 2'
NetIncome_with_unusal_items_3 = 'Net income including unusal items 3'
NetIncome_with_unusal_items_4 = 'Net income including unusal items 4'
TotalRevenue= 'Total revenue'
TotalOperatingExpense = 'Total operating expense'
TotalCostAndExpenses = 'C&E'
MinorityInterest = 'Minority Interest'


## Balance sheet
# Fact const
# Assets
CashAndCashEquivalent = "Cash And Cash Equivalen"
RestrictedCash = "Restricted Cash"
Goodwill = "Goodwill"
AccountsReceivable = "Accounts Receivable"
IntangibleAssets = "Intangible Assets"
OtherAssetsCurrent = "Other Assets Current"
CurrentAssets = "Current Assets"
OtherAssetsNoncurrent = "Other Assets Noncurrent"
NonCurrentAssets = "Non Current Assets"
OtherAssets = "Other Assets"
TotalAssets = "Total Assets"

#Liabilities
AccountsPayable = "Accounts Payable"
PropertyPlantAndEquipment = "Property Plant And Equipment"
ShortTermDebtCurrent = "Current portion of Short Term Debt"
LongTermDebtCurrent = "Current portion of Long Term Debt"
ShortTermDebt = "Short Term Debt"
LongTermDebt = "Long Term Debt"
DeferredTaxLiabilityNonCurrent = "Deferred Tax Liability Non Current"
LiabilitiesCurrent = "Current Liabilities"
OtherLiabilitiesNoncurrent = "Other Liabilities Non current"
NonLiabilitiesCurrent = "Non Current Liabilities"
OtherLiabilities = "Other Liabilities"
TotalLiabilities = "Total Liabilities"

RetainedEarnings = "Retained Earnings"

# equity
StockholdersEquity = "Stockholders Equity"
TotalEquity = "Total Equity"
TotalLiabilitiesAndEquity = "Total Liabilities And Equity"


class DataFrameWithStringListTracking:
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

    def compute_master_list(self):
        print(" master list")
        for string_index in self.df.index.tolist():
            if 'CostsAndExpenses' in string_index or 'LossesAndExpenses' in string_index:
                continue
            # Get the target row as a Series
            target_row = self.df.loc[string_index]
            # Get the index of the string_index
            idx = self.df.index.get_loc(string_index)
            start_idx = idx - 1
            if idx == 0:
                continue
            # Iterate from the row above the target row to the top
            current_sum = 0
            current_sum = self.df.iloc[start_idx].copy()
            # print(string_index)
            # print(target_row)
            # print(current_sum)
            if (current_sum.values == target_row.values).all(): #  current_sum.equals(target_row):
                self.set_master_list(string_index, self.df.index[start_idx])
            for end_idx in range(start_idx -1 , -1, -1):
                current_sum += self.df.iloc[end_idx]
                # print(current_sum)
                # print(current_sum.values == target_row.values)
                # print(start_idx, end_idx)
                # print(self.df.index.tolist()[end_idx: start_idx + 1])
                if self.df.index[end_idx] in self.rows_that_are_sum:
                    break
                if (current_sum.values == target_row.values).all():
                    self.set_master_list(string_index, self.df.index.tolist()[end_idx: start_idx + 1])

    def check_if_master_in_list(self, fact, fact_list):
        master = self.variable_in_list(fact)
        if master is not None and master in fact_list:
            return True
        return False
        
    def compute_master_list2(self):
        print(" master list")
        # for string_index in self.rows_that_are_sum:
        self.master_list_dict = {}
        print(self.df)
        for string_index in self.df.index.tolist():
            # Get the target row as a Series
            if string_index not in self.df.index.tolist():
                # del self.master_list_dict[string_index]
                v = self.master_list_dict.pop(string_index, None)
                string_index = self.facts_name_dict[string_index]

            if string_index in self.special_master_dict:
                continue

            target_row = self.df.loc[string_index]
            # Get the index of the string_index
            print(string_index)
            idx = self.df.index.get_loc(string_index)
            start_idx = idx - 1
            if idx == 0:
                continue
            current_sum = 0
            current_sum = self.df.iloc[start_idx].copy()
            if (current_sum.values == target_row.values).all(): 
                # NOTE: This mean the row is repeated twice
                # 1) it can be different things but equal, usually samll values, like 1000
                # 2) it can be same thing repeated twice
                # self.set_master_list(string_index, [self.df.index[start_idx]])
                pass
            for end_idx in range(start_idx -1 , -1, -1):
                # print(self.df.index[end_idx])
                if not self.check_if_master_in_list(self.df.index[end_idx], self.df.index[end_idx: idx]): 
                    current_sum += self.df.iloc[end_idx]
                if self.df.index[end_idx] in self.rows_that_are_sum:# and not (string_index == 'Stockholders Equity' or string_index == 'Total Liabilities'  or string_index == 'Total Assets'):
                    break
                # print(current_sum.values)
                # print(target_row.values)
                
                if (current_sum.values == target_row.values).all():
                    # NOTE: getting the len_slaves_list is TIME expensive, specially this function get called every row
                    slaves_list = self.df.index.tolist()[end_idx: start_idx + 1]
                    sliced_df = self.df.loc[slaves_list]
                    slaves_list = sliced_df.loc[~(sliced_df == 0).all(axis=1)]
                    len_slaves_list = len(slaves_list)
                    if len_slaves_list > 1: #and len(self.df.index.tolist()[end_idx: start_idx + 1]) > 1:
                        self.set_master_list(string_index, self.df.index.tolist()[end_idx: start_idx + 1])
                        break
        self.master_list_dict = self.master_list_dict | self.special_master_dict

    def get_master_list(self, idx) -> list:
        """
        Get the list of strings for the specified row.
        
        :param idx: String index or integer index.
        :return: List of strings associated with the row.
        """
        if isinstance(idx, int):
            idx = self.df.index[idx]
        return self.master_list_dict.get(idx, None)
    
    def get_master(self, fact):
        if isinstance(fact, int):
            fact = self.df.index[fact]
        return self.variable_in_list(fact)

    def set_master_list(self, idx, value: list, append=False):
        """
        Set the list of strings for the specified row.
        
        :param idx: String index or integer index.
        :param value: List of strings to set.
        """
        if isinstance(idx, int):
            idx = self.df.index[idx]
        if append:
            if idx not in self.master_list_dict:
                self.master_list_dict[idx] = []
            self.master_list_dict[idx].append(value)
        else:
            self.master_list_dict[idx] = value

    def get_integer_index(self, master_idx) -> int:
        """
        Get the integer index for the given string index.
        
        :param string_idx: The string index.
        :return: The integer index.
        """
        return self.df.index.get_loc(master_idx)

    def get_string_index(self, int_idx) -> str:
        """
        Get the string index for the given integer index.
        
        :param int_idx: The integer index.
        :return: The string index.
        """
        return self.df.index[int_idx]

    def variable_in_list(self, variable: str) -> str:
        """
        Check if the variable is in any list and return the string index if found.
        
        :param variable: The variable to check.
        :return: The string index if the variable is in any list, None otherwise.
        """
        for master_idx, master_list in self.master_list_dict.items():
            if variable in master_list:
                return master_idx
        return None
    

    """
    
        For mapping
    """
    
    def get_section(self, fact : str):
        for section, facts in self.sections_dict.items():
            if fact in facts:
                return section
        return None
    
    def get_start_end(self, fact : str):
        for section, indexes in self.sections_indxs.items():
            if section == fact:
                return indexes['start'], indexes['end']
        return None, None

    def _get_patterns(self) -> Tuple[Dict[str, str], Dict[str, str]]:
        """
        Defines regex patterns for human-readable strings and us_gaap strings.

        :return: Two dictionaries with patterns for human-readable strings and us_gaap strings.
        """
        human_patterns = {
            CurrentAssets: r'\bCurrent\s+Assets?\b',
            NonCurrentAssets: r'\b(?:Noncurrent\s+Assets?)\b',
            LiabilitiesCurrent: r'\b(?:Liabilities\s+Current|Current\s+Liabilities)\b',
            NonLiabilitiesCurrent: r'\b(?:Noncurrent\s+Liabilities|Liabilities\s+Noncurrent)\b',
            StockholdersEquity: r'\b(?:Stockholders?\s+Equity|Equity)\b',
            TotalEquity: r'\b(?:Total?\s+Equity|Equity)\b',
            TotalLiabilitiesAndEquity: r'\b(?:Liabilities\s+and\s+Stockholders?\s+Equity|Equity\s+and\s+Liabilities)\b',
            TotalAssets: r'\b(?:Total\s+Assets)\b',
            TotalLiabilities: r'\b(?:Total\s+Liabilities|Liabilities)\b'
        }

        gaap_patterns = {
            'us-gaap_CurrentAssets': r'\b(?:us-gaap_CurrentAssets)\b',
            'us-gaap_NoncurrentAssets': r'\b(?:us-gaap_NoncurrentAssets)\b',
            'us-gaap_LiabilitiesCurrent': r'\b(?:us-gaap_LiabilitiesCurrent|us-gaap_CurrentLiabilities)\b',
            'us-gaap_NoncurrentLiabilities': r'\b(?:us-gaap_NoncurrentLiabilities|us-gaap_LiabilitiesNonCurrent)\b',
            'us-gaap_StockholdersEquity': r'\b(?:us-gaap_StockholdersEquity|us-gaap_Equity)\b',
            'us-gaap_TotalEquity': r'\b(?:us-gaap_TotalEquity|us-gaap_Equity)\b',
            'us-gaap_LiabilitiesAndStockholdersEquity': r'\b(?:us-gaap_LiabilitiesAndStockholdersEquity|us-gaap_EquityAndLiabilities)\b',
            'us-gaap_TotalAssets': r'\b(?:us-gaap_TotalAssets)\b',
            'us-gaap_TotalLiabilities': r'\b(?:us-gaap_TotalLiabilities|us-gaap_Liabilities)\b'
        }

        return human_patterns, gaap_patterns

    def _match_score(self, string: str, pattern) -> int:
        """
        Scores a string based on how closely it matches a set of patterns.

        :param string: The string to be matched.
        :param patterns: Dictionary of patterns to match against.
        :return: An integer score out of 10 based on pattern match quality.
        """
        score = 0
        # Normalize the string and pattern for comparison
        normalized_string = string.lower()
        normalized_pattern = pattern.lower()
        
        # Criteria 1: Presence of All Words
        pattern_words = normalized_pattern.split()
        matched_words = sum(1 for word in pattern_words if word in normalized_string)
        score += min(4, matched_words)  # Max 4 points

        # Criteria 2: Correct Order of Words
        if all(word in normalized_string for word in pattern_words):
            word_positions = [normalized_string.find(word) for word in pattern_words]
            if word_positions == sorted(word_positions):  # All words are in order
                score += 2
            elif sorted(word_positions)[:len(word_positions) - 1] == word_positions[:-1]:
                score += 1  # Most words are in order

        # Criteria 3: Minimal Gaps Between Words
        words_in_string = normalized_string.split()
        gap_count = len(words_in_string) - len(pattern_words)
        if gap_count == 0:
            score += 2  # No gaps
        elif gap_count <= 2:
            score += 1  # Minimal gaps

        # Criteria 4: Exact Match with Pattern
        if re.fullmatch(pattern, string, re.IGNORECASE):
            score += 2

        return min(score, 10)  # Ensure score does not exceed 10

    def _get_matching_facts(self, fact_name: str) -> list:
        """
        Retrieves all candidates for the given fact (e.g., "Total Assets") by matching fact_name with regex.
        
        :param fact_name: The fact to search for in the DataFrame.
        :return: A list of tuples containing the fact's string index and value.
        """
        matching_facts = []
        human_patterns, gaap_patterns = self._get_patterns()
        gaap_pattern = gaap_patterns.get(fact_name, "")
        for index in self.df.index:
            
            if re.match(gaap_pattern, index):  # Assuming _get_fact_pattern generates a regex pattern
                value = self.df.loc[index]
                matching_facts.append((index, value))
        return matching_facts

    def _find_best_balance_match(self, total_assets_list: list[pd.Series], total_liabilities_equity_list: list[pd.Series]) -> int:
        """
        Finds the best matching pair from 'Total Assets' and 'Total Liabilities and Equity' lists
        that are equal and have the highest value.

        :param total_assets_list: List of (index, value) for Total Assets.
        :param total_liabilities_equity_list: List of (index, value) for Total Liabilities and Equity.
        :return: A score based on equality and maximum value.
        """
        best_score = pd.Series(0)
        for asset_index, asset_value in total_assets_list:
            for equity_index, equity_value in total_liabilities_equity_list:
                if all(asset_value == equity_value):
                    score = asset_value  # Reward higher values
                    print(score, best_score)
                    if score.sum() > best_score.sum():
                        best_score = score
                        self.found_total_assets = [asset_index, equity_index]
        return best_score

    def _evaluate_mf(self, gaap_string: str, human_string: str, mf_fact: str, is_balance_sheet: bool = False) -> int:
        """
        Evaluates an mf object by scoring it based on various criteria and additional
        balance sheet checks if applicable.

        :param gaap_string: The us-gaap fact string.
        :param human_string: The corresponding human-readable string.
        :param mf_fact: The constant fact being evaluated.
        :param is_balance_sheet: Whether the data belongs to a balance sheet.
        :return: A score based on pattern matching and mf equation truth value.
        """
        human_patterns, gaap_patterns = self._get_patterns()
        human_pattern = human_patterns.get(mf_fact, "")
        gaap_pattern = gaap_patterns.get(mf_fact, "")
        
        # Base scores for pattern matching
        human_score = self._match_score(human_string, human_pattern)
        gaap_score = self._match_score(gaap_string, gaap_pattern)
        total_score = human_score + gaap_score

        # Additional condition for balance sheet
        if  self.found_total_assets is not None and is_balance_sheet and mf_fact in [TotalAssets, TotalLiabilitiesAndEquity]:
            total_assets_list = self._get_matching_facts(TotalAssets)
            total_liabilities_equity_list = self._get_matching_facts(TotalLiabilitiesAndEquity)
            
            # Look for matching values
            best_match_score = self._find_best_balance_match(total_assets_list, total_liabilities_equity_list)
            # if best_match_score.sum() > 0:
            #     total_score += 10  # Add match score based on equality and highest value
            print(gaap_string)
            print(human_string)
        if self.found_total_assets:
            for total_asset_equity in self.found_total_assets:
                if total_asset_equity == gaap_string:
                    total_score += 10

        return total_score

    def _rank_shared_mfs(self, is_balance_sheet: bool = False):
        """
        Ranks mf objects that appear in more than one data_fact based on pattern matching and mf equation criteria.
        """
        # Track appearances of each mf object across different data_facts
        mf_occurrences = {}
        # Collect all mfs and group them by their facts
        for data_fact, mf_list in self.facts_mfs.items():
            for mf in mf_list:
                if mf.equation:
                    if mf.fact not in mf_occurrences:
                        mf_occurrences[mf.fact] = []
                    mf_occurrences[mf.fact].append(data_fact)

        # Iterate over mf_occurrences to handle cases where an mf appears in multiple data_facts
        for mf_fact, occurrences in mf_occurrences.items():
            if len(occurrences) > 1:  # Only rank if mf is in multiple lists
                scores = []
                best_score = 0
                best_data_fact = None
                for data_fact in occurrences:
                    human_string = self.rows_text.get(data_fact, "")
                    score = self._evaluate_mf(data_fact, human_string, mf_fact, is_balance_sheet)
                    scores.append((data_fact, mf, score))
                    if score > best_score:
                        best_score = score
                        best_data_fact = data_fact
                if best_data_fact:
                    for data_fact in occurrences:
                        if data_fact == best_data_fact:
                            pass
                        else:
                            try:
                                self.facts_mfs[data_fact].remove(mf)
                            except Exception as e:
                                print(e)
    
        
    def parse_facts_mfs(self, is_balance_sheet: bool = True):
        """
        Parses and ranks all mf objects within facts_mfs based on multiple criteria, including pattern matching.
        """
        # First, rank shared mfs to handle conflicts between data_facts
        self._rank_shared_mfs()
        # TODO also account for 'reu' rows
        # acount for the master_list 

        # Rank individual mfs within each data_fact list
        for data_fact, mf_list in self.facts_mfs.items():
            if not mf_list:
                continue
            # Get the human-readable string for this data_fact
            human_string = self.rows_text.get(data_fact, "")
            # Rank mf objects by evaluating their scores
            ranked_mfs = []
            for mf in mf_list:
                score = self._evaluate_mf(data_fact, human_string, mf.fact, is_balance_sheet)
                if mf.equation:
                    score += 1  # Additional score if mf.equation is True
                ranked_mfs.append((mf, score))
            # Sort mf objects by their score in descending order
            ranked_mfs.sort(key=lambda x: x[1], reverse=True)
            # Update facts_mfs with the ranked list








"""
Panada DataFrame helpers fucntion
"""
def check_if_index_value_match(df1, df2, df1_fact, df2_fact, strict_compare=False):
    common_columns = list(set(df1.columns).intersection(df2.columns))
    if not common_columns and not strict_compare:
        return True
    common_value = False
    combined_value = 0
    
    for column in common_columns:
        test1 = df1.loc[df1_fact, column]
        test2 = df2.loc[df2_fact, column]
        # print(test1, test2)
        if strict_compare:
            if (df1.loc[df1_fact, column]) == (df2.loc[df2_fact, column]) or df1.loc[df1_fact, column] == 0:
                common_value = True
                combined_value += int(df1.loc[df1_fact, column])
            else:
                return False
        else:
            if (df1.loc[df1_fact, column]) == (df2.loc[df2_fact, column]):
                common_value = True
    if strict_compare and combined_value == 0:
        return False
    return common_value

def check_if_index_value_in_df(df1, df2, df2_fact, duplicate=False):
    common_value = False

    for df1_fact in df1.index.tolist():
        common_value = check_if_index_value_match(df1, df2, df1_fact, df2_fact, strict_compare=True)
        # print(f"{common_value} {df1_fact}")
        if common_value:
            if duplicate:
                stripped_df2 = df2_fact[:df2_fact.find("-DATE-")]
                # print("stripped_duplicate")
                # print(stripped_df2)
                # stripped_df2_old = df2_fact[df2_fact.find("-OLD-"):]
                #df1_fact could be duplicate ceck OLD
                index = df1_fact.find("-DATE-")
                if index != -1:
                    stripped_df1 = df1_fact[:index]
                else:
                    stripped_df1 = ""
                if stripped_df2 != df1_fact or stripped_df1 == stripped_df2:
                    return df1_fact
            else:
                return df1_fact
    return False

def rearrange_facts(df):
    print(df)
    print("===")
    # Identify rows with duplicates (rows that contain ":")
    duplicated_rows = df[df.index.str.contains(":")]
    print(duplicated_rows)
    # Extract the base facts (main facts) without the colon part
    # base_facts = duplicated_rows.index.str.split(":").str[-1].str.rsplit("_", 1).str[0]
    base_facts = duplicated_rows.index.str.split(":").str[-1]
    print(base_facts)
    # Create a copy of df to avoid modifying the original DataFrame during iteration
    df_copy = df.copy()
    # Create an empty DataFrame to store the rearranged rows
    rearranged_df = pd.DataFrame(columns=df.columns)
    for base_fact in base_facts.unique():
        # Find the index of the main fact in the original DataFrame
        if base_fact in df.index:
            main_fact_index = df.index.get_loc(base_fact)
            # Identify the duplicate rows that correspond to the current main fact
            duplicates_to_insert = duplicated_rows[duplicated_rows.index.str.endswith(base_fact)]
            # Sum the values of the duplicate rows
            sum_of_duplicates = duplicates_to_insert.sum()
            # Get the values of the main fact
            main_fact_values = df.loc[base_fact]
            # Check if the sum of duplicates equals the main fact values
            print(sum_of_duplicates)
            print(main_fact_values)
            if (sum_of_duplicates.equals(main_fact_values) and duplicates_to_insert.shape[0] > 1) or duplicates_to_insert.shape[0] > 1:
                # Drop the duplicate rows from their original positions in the DataFrame
                df = df.drop(duplicates_to_insert.index)
                # Iterate through each duplicate row
                print(duplicates_to_insert)
                for dup_index in duplicates_to_insert.index:
                    dup_row = duplicates_to_insert.loc[dup_index]
                    # Prepare a new index for the DataFrame with duplicate row inserted above main_fact_index
                    new_index = df.index.tolist()
                    new_index.insert(main_fact_index, dup_index)
                    # Reindex the DataFrame to include the new index
                    df = df.reindex(index=new_index)
                    # Assign the duplicate row data to the newly inserted row
                    df.loc[dup_index] = dup_row
                    # Increment main_fact_index for the next insertion
                    main_fact_index += 1
    
    # Append any remaining rows in the DataFrame to rearranged_df
    rearranged_df = pd.concat([rearranged_df, df])
                # # Insert the duplicate rows above the main fact
                # rearranged_df = pd.concat([rearranged_df, df_copy.iloc[:main_fact_index]])
                # rearranged_df = pd.concat([rearranged_df, duplicates_to_insert])
                # rearranged_df = pd.concat([rearranged_df, df_copy.iloc[[main_fact_index]]])
                # # Drop the duplicate rows from the original DataFrame
                # df_copy = df_copy.drop(duplicates_to_insert.index)
                # # Update the remaining part of the DataFrame
                # df_copy = pd.concat([df_copy.iloc[main_fact_index+1:]])

    print(rearranged_df)
    print("==")
    return rearranged_df

# Function to move a fact to a new position in DataFrame
def move_fact_to_new_position(df, fact, new_index):
    # TODO account for masters and slaves
    df_reindexed = df.drop(fact)
    top = df_reindexed.iloc[:new_index]
    bottom = df_reindexed.iloc[new_index:]
    df_reordered = pd.concat([top, df.loc[[fact]], bottom])
    return df_reordered

def rename_df_index(df: DataFrameWithStringListTracking, index_map): # string_index: str, new_string_index: str):
    # index_map = {string_index: new_string_index}
    df.df.rename(index=index_map, inplace=True)
    for string_index, new_string_index in index_map.items():
        df.facts_name_dict[string_index] = new_string_index
    return df












"""
Dictionary helper functions
"""

def get_weight_by_key(data_dict, key):
    """
    """
    if data_dict:
        if key in data_dict:
            print(data_dict[key])
            return [float(item['weight']) for item in data_dict[key]]
    return []

def get_facts_by_key(data_dict, key):
    """
    Check if a string is a key and return a list of facts.
    
    Parameters:
    data_dict (dict): The dictionary containing the data.
    key (str): The key to check.
    
    Returns:
    list: A list of facts if the key exists, otherwise an empty list.
    """
    if data_dict:
        if key in data_dict:
            print(data_dict[key])
            print([item['fact'] for item in data_dict[key]])
            return [item['fact'] for item in data_dict[key]]
    return []
    
def get_key_by_fact(data_dict, fact):
    """
    Check if a string is a fact for one of the keys and return the key.
    
    Parameters:
    data_dict (dict): The dictionary containing the data.
    fact (str): The fact to check.
    
    Returns:
    str: The key if the fact is found, otherwise an empty string.
    """
    for key, facts in data_dict.items():
        for item in facts:
            if item['fact'] == fact:
                return key
    return None

def get_key_by_fact2(data_dict, fact):
    """
    Check if a string is a fact for one of the keys and return the key.
    
    Parameters:
    data_dict (dict): The dictionary containing the data.
    fact (str): The fact to check.
    
    Returns:
    str: The key if the fact is found, otherwise an empty string.
    """
    for key, facts in data_dict.items():
        if facts == fact:
            return key
    return None








"""
List helper functions
"""

def compare_variable_lists(list1, list2, facts_name_dict, master_list_dict):
    def normalize_fact(fact):
        # Check if the fact has been renamed
        for original, renamed in facts_name_dict.items():
            if fact == renamed:
                return original
        return fact
    def find_key_with_value(value):
        for key, val_list in master_list_dict.items():
            if value in val_list:
                return key
        return None
    
    # Normalize both lists
    normalized_list1 = {normalize_fact(fact) for fact in list1}
    normalized_list2 = {normalize_fact(fact) for fact in list2}
    # Find values in list2 but not in list1
    in_list2_not_in_list1 = [fact for fact in list2 if normalize_fact(fact) not in normalized_list1]
    # Keep track of values in list1 but not in list2
    in_list1_not_in_list2 = [fact for fact in list1 if normalize_fact(fact) not in normalized_list2]
    print("+++++++++ checking for master ++++++")
    tmp_list = in_list1_not_in_list2.copy()
    for fact in in_list1_not_in_list2:
        f_master = find_key_with_value(fact)
        if f_master:
            normal_f_master = normalize_fact(f_master)
            if normal_f_master in normalized_list2:
                tmp_list.remove(fact)
    in_list1_not_in_list2 = tmp_list
    return in_list1_not_in_list2




def find_extreme_index_element(list1, list2, find_highest=False):
    """
    This function returns the element from list2 that has the highest or lowest index in list1.
    
    Parameters:
    list1 (list): The list to search through.
    list2 (list): The list of elements to find in list1.
    find_highest (bool): If True, find the element with the highest index. If False, find the element with the lowest index.
    
    Returns:
    element: The element from list2 that has the highest or lowest index in list1.
    """
    if not list2:
        return None  # Return None if list2 is empty
    
    # Initialize the variables to store the result
    extreme_index = -1 if find_highest else float('inf')
    extreme_element = None
    
    for element in list2:
        if element in list1:
            index = list1.index(element)
            if (find_highest and index > extreme_index) or (not find_highest and index < extreme_index):
                extreme_index = index
                extreme_element = element
    
    return extreme_element



    # def check_if_lists_equal(list1, list2, master_list):
    #     list2_size = len(list2)
    #     list1_size = 0 
    #     for l1 in list1:
    #         if l1 in list2:
    #             list1_size += 1
    #     return list2_size == list1_size
