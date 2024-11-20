import pandas as pd
from pandas.api.extensions import ExtensionDtype, register_extension_dtype
from helpers import *
from itertools import combinations, product
import copy
import numpy as np
import re


# swithc to combine_variable
# TODO if i miss like operating income the next one will call to all equations

# TODO: create a function that check if values are equal, which can be used in other files too
# have easy compare pecially for equations where 2/3 right is enough, check if the 2/3 are also reported in anther row fix it
keep_value_unchanged = ['us-gaap_EarningsPerShareDiluted', 'us-gaap_EarningsPerShareBasic', 'us-gaap_WeightedAverageNumberOfSharesOutstandingBasic', 'us-gaap_WeightedAverageNumberOfDilutedSharesOutstanding']

lulu_sic = [
    "0001257343",
    "0000723371",
    "0001664038",
    "0001396118",
    "0001599738",
    "0001951051",
    "0000053180",
    "0001696558",
    "0001425115",
    "0001922097",
    "0000094845",
    "0000848372",
    "0001444275",
    "0001397187",
    "0001897532",
    "0000848373",
    "0001902794",
    "0001916331",
    "0001013749",
    "0000902793",
    "0001041868",
    "0001192907",
    "0000095574",
    "0001257333",
    "0001689258",
    "0001257335",
    "0001257334",
    "0001127242",
    "0000002741",
    "0001653909",
    "0001988894",
    "0000852166",
    "0000793029",
    "0000100979",
    "0001666054",
    "0000887538",
    "0000865886",
    "0000744041",
    "0001106652",
    "0001549941",
    "0001139683",
    "0000916802",
    "0001690511",
    "0001862733",
    "0000795363",
    "0001060822",
    "0000106311",
    "0000844143",
    "0001368294",
    "0001462109",
    "0000848371",
    "0001649527",
    "0001050797",
    "0001345122",
    "0001982661",
    "0000778169",
    "0001496819",
    "0001877787",
    "0000943184",
    "0000058839",
    "0001846576",
    "0000821002",
    "0000837912",
    "0001513403",
    "0000039917",
    "0001052274",
    "0001061894",
    "0001751454"
]


statement_keys_map = {
    "balance_sheet": [
        "balance sheet",
        "balance sheets",
        "statement of financial position",
        "consolidated balance sheets",
        "consolidated balance sheet",
        "consolidated financial position",
        "consolidated balance sheets - southern",
        "consolidated statements of financial position",
        "consolidated statement of financial position",
        "consolidated statements of financial condition",
        "combined and consolidated balance sheet",
        "condensed consolidated balance sheets",
        "consolidated balance sheets, as of december 31",
        "dow consolidated balance sheets",
        "consolidated balance sheets (unaudited)",
    ],
    "income_statement": [
        "income statement",
        "income statements",
        "statement of earnings (loss)",
        "statements of consolidated income",
        "statements of operations",
        "consolidated statements of operations",
        "consolidated statement of operations",
        "consolidated statements of earnings",
        "consolidated statement of earnings",
        "consolidated statements of income",
        "consolidated statement of income",
        "consolidated statement of comprehensive income",
        "combined and consolidated statement of income",
        "consolidated income statements",
        "consolidated income statement",
        "condensed consolidated statements of earnings",
        "consolidated results of operations",
        "consolidated statements of income (loss)",
        "consolidated statements of income - southern",
        "consolidated statements of operations and comprehensive income",
        "consolidated statements of comprehensive income",
        "Consolidated and Combined Statements of Income",
        "Consolidated Statements of Net Earnings",
        "Consolidated Statements of Net Earnings (Loss)",
    ],
    "cash_flow_statement": [
        "cash flows statement",
        "cash flows statements",
        "statement of cash flows",
        "statements of consolidated cash flows",
        "consolidated statements of cash flows",
        "consolidated statement of cash flows",
        "consolidated statement of cash flow",
        "consolidated cash flows statements",
        "consolidated cash flow statements",
        "condensed consolidated statements of cash flows",
        "consolidated statements of cash flows (unaudited)",
        "consolidated statements of cash flows - southern",
    ],
}

income_statment_map =   {'total revenue': ['first',['Revenue', 'Sales']],
                         'COGS': ['below revenue', ['CostOfGoodsAndServicesSold', 'CostOfGoodsSold', 'CostOfGoods', 'CostOfRevenue', 'COGS']],
                        'Gross profit': ['equation', ['GrossProfit']],
                        'SG&A': ['below revenue', ['SellingGeneralAndAdministrative']],
                        'R&D': ['below revenue', ['ResearchAndDevelopment']],
                        'amoritization': ['below revenue', ['Amortization']],
                        'Depreciation': ['below revenue', ['Depreciation']],
                        'Total operating expense': ['below revenue', ['OperatingExpenses']],
                        'Operating income': ['equation', ['OperatingIncome']],
                        'Interest expense': ['' ,[]],
                        'Interest and investment income': ['', []],
                        'Other non-operating income (expense)': ['', []],
                        'EBT': ['', ['IncomeLossFromContinuingOperations']],
                        'Income tax expense': ['', ['IncomeTaxExpense']],
                        'Net income': ['',['ProfitLoss', 'NetIncomeLoss']],
                        'Earnings Per Share Basic': ['', ['EarningsPerShareBasic']],
                        'Earnings Per Share Diluted': ['', ['EarningsPerShareDiluted']],
                        'Weighted Average Number Of Shares Outstanding Basic': ['', ['WeightedAverageNumberOfSharesOutstandingBasic']],
                        'Weighted Average Number Of Diluted Shares Outstanding': ['', ['WeightedAverageNumberOfDilutedSharesOutstanding']]
                        }            # ['revenue', 'COGS', 'gross_profit', 'SG&A']

balance_sheet_map = {
                    'Total assets': ['', ['Assets']],
                    'Current assets': ['', ['AssetsCurrent']],
                    'Non-current assets': ['', []],
                    'Current liabilities': ['', ['LiabilitiesCurrent']],
                    'Non-current liabilities': ['', []],
                    'Total liabilities': ['', []],
                    'Total equity': ['', ['StockholdersEquity']],
                    'common stock': ['', ['CommonStock']],
                    'treasury stock': ['', ['TreasuryStock']],
                    'Short term debt': ['', ['DebtCurrent',  'ShorTermDebt', 'OperatingLeaseLiabilityCurrent']],
                    'Long term debt': ['', ['DebtNoncurrent', 'LongTermDebt', 'OperatingLeaseLiabilityNoncurrent']],
                    '': ['', []],
                    '': ['', []],
                    '': ['', []],
                    '': ['', []],
                    '': ['', []],
                    '': ['', []],
                    '': ['', []],
                }

do_strict_compare = ['Total equity']

NO_EQUATION_ERROR = "NO_EQUATION_ERROR"
FACT_NOT_REPORTED = "FACT_NOT_REPORTED"
FACT_CALCULATED = "FACT_CALCULATED"

# sum types
SUM_TOTAL = "SUM_TOTAL"
EQUATION_TOTAL = "EQUATION_TOTAL"


class MapFact:

    def __init__(self, fact, possible_names=[], pattern=[], equation=None, highest=False, strict_compare=False, can_repeat=False) -> None:
        self.fact = fact
        self.equation = equation
        self.possible_names = possible_names
        self.pattern = pattern
        self.highest = highest
        self.strict_compare = strict_compare
        self.index = None
        self.matches = []
        self.match = None
        self.can_repeat = can_repeat
        # a master attr to attach some rows as sum for a specific row, so do not use that row in calc only use the master
        # every row should be potentially a sum of other rows and it will become a master, but master can have masters
        self.master = None

    def call_eq(self, df, end_idx, **override_params):
        if self.equation:
            return self.equation(df, end_idx, **override_params)
        else:
            return NO_EQUATION_ERROR
    
    def compute2(self, data_map):
        if self.equation:
            return self.equation(data_map)
        else:
            return data_map[self.name]

class FactsMap:

    def __init__(self, df) -> None:
        self.df= df
        self.mapped_df = df

    mapfacts = None
    def map_data_highest_match(self):
        for mapfact in mapfacts:
            strict_compare = True if mapfact in do_strict_compare else False
            data_fact_matches = []
            data_facts = self.df.index.to_list()
            for data_fact in data_facts:
                for possible_name in mapfact.possible_names:
                    if strict_compare:
                        data_fact_filtered = data_fact.split("_")[-1]
                        if possible_name == data_fact_filtered:
                            data_fact_matches.append(data_fact)
                            break
                    else:
                        if possible_name in data_fact_filtered:
                            data_fact_matches.append(data_fact)
                            break
            if data_fact_matches:
                bigest_number = 0
                match = data_fact_matches[0]
                for data in data_fact_matches:
                    if abs(self.df.loc[data, self.df.columns[-1]]) > abs(bigest_number):
                        bigest_number = self.df.loc[data, self.df.columns[-1]]
                        match = data
                self.mapped_df = self.df.rename(index={match: mapfact.fact})
                modified_data_facts = [s.replace(match, mapfact.fact) for s in data_facts]
        return modified_data_facts
    
    def map_data_using_equations(self):
        data_facts_highest_match = self.map_data_highest_match()
        for mapfact in mapfacts:
            data_fact_matches = []
            result = eval(mapfact.equation)
            if result:
                pass
            else:
                pass

def get_key_from_value(dictionary, value):
    """
    Check if a specific value exists in a dictionary and return its corresponding key
    Args:
    - dictionary (dict): The dictionary to search.
    - value: The value to search for.
    Returns:
    - str or None: The key corresponding to the value if found, else None.
    """
    for key, val in dictionary.items():
        if val == value:
            return key
    return None

def map_data(df, map= income_statment_map, strict_compare=False):
    temp_mapped_data_facts = {}
    for map_fact, fact_restrictions in map.items():
        if map_fact in do_strict_compare:
            strict_compare = True
        else:
            strict_compare = False
        temp_mapped_data_facts[map_fact] = None
        data_fact_matches = []
        for data_fact in df.index.tolist():
            for restir in fact_restrictions[1]:
                if strict_compare:
                    data_fact_filtered = data_fact.split("_")[-1]
                    if restir == data_fact_filtered:
                        data_fact_matches.append(data_fact)
                        break # ensure that the order of the restriction matter
                else:
                    if restir in data_fact:
                        data_fact_matches.append(data_fact)
                        break # ensure that the order of the restriction matter
        if data_fact_matches:
            bigest_number = 0
            match = data_fact_matches[0]
            for data in data_fact_matches:
                if abs(df.loc[data, df.columns[-1]]) > abs(bigest_number):
                    bigest_number = df.loc[data, df.columns[-1]]
                    match = data
            temp_mapped_data_facts[map_fact] = match
            df = df.rename(index={match: map_fact})
    return df

def compute(df, equation):
    computed_values = {}
    for column in df.columns:
        computed_values[column] = equation(df, column)
    computed_row = pd.Series(computed_values)
    return computed_row

def compare_row(df, compare_row):
    # Compare with each row in the DataFrame
    for index, row in df.iterrows():
        if compare_row.equals(row):
            return row, index
    return None, None

def add_row_to_df(df: DataFrameWithStringListTracking, row, row_title, index_name: str, insert_after = True):
    print(row, index_name)
    while row_title in df.df.index.tolist():
        row_title += '_new'
    insert_position = df.df.index.get_loc(index_name) # after the first row
    if insert_after:
        insert_position += 1
    map_index = df.df.index.tolist()
    map_index.insert(insert_position, row_title)
    df.df = df.df.reindex(index=map_index)
    df.df.loc[row_title] = row
    return df

def check_if_sum_by_col(df, string_index):
        # Ensure the provided index exists in the DataFrame
    if string_index not in df.index:
        raise ValueError(f"Index '{string_index}' not found in the DataFrame.")
    # Iterate over each column
    for col in df.columns:
        target_value = df.loc[string_index, col]
        # Initialize the sum
        current_sum = 0
        # Get the index of the string_index
        idx = df.index.get_loc(string_index)
        # Iterate from the row above the target row to the top
        for i in range(idx - 1, -1, -1):
            current_sum += df.iloc[i][col]
            # Check if the current sum matches the target value
            if current_sum == target_value:
                break
        else:
            # If the loop completes without finding a sum, return False
            return False
    # If all columns satisfy the condition, return True
    return True

# TODO upgrade this to look for stuff that has : and add them
def check_if_sum(df: DataFrameWithStringListTracking, string_index):
    # Ensure the provided index exists in the DataFrame
    if isinstance(string_index, int):
            string_index = df.df.index[string_index]
    if string_index not in df.df.index:
        raise ValueError(f"Index '{string_index}' not found in the DataFrame.")
    # Get the target row as a Series
    target_row = df.df.loc[string_index]
    # Get the index of the string_index
    idx = df.df.index.get_loc(string_index)
    # Iterate from the row above the target row to the top
    # current_sum = 0
    for start_idx in range(idx - 1, -1, -1):
        current_sum = df.df.iloc[start_idx].copy()
        if current_sum.equals(target_row):
            return start_idx, end_idx
        # Sum rows consecutively from start_idx upwards
        for end_idx in range(start_idx - 1, -1, -1):
            current_sum += df.df.iloc[end_idx]
            if current_sum.equals(target_row):
                return start_idx, end_idx
    # If no sum of consecutive rows equals the target row, return False
    return False, False

# TODO everu sum of class 'reu' should be either a total like total expense or like net income
# enhanced_df
def find_combinations_with_logging(enhanced_df: DataFrameWithStringListTracking, start_index, end_index, target, preferred_operation_addition=True, change_sign=False, check_all_comb=False, change_base_sign=False, strict_compare=True, tolerance=0.1, check_for_total=False, must_find_comb=False, check_for_negative=True, facts_weight=None, reu_class=False):
    closest_match = None
    closest_match_differences = None
    closest_default_match = None
    closest_default_match_differences = None
    def check_if_master_in_list(fact, fact_list):
        master = enhanced_df.variable_in_list(fact)
        if master is not None and master in fact_list:
            return True
        return False
    # TODO if you want to add a fix, check also if the valuse of the differnece for [1,1,1...] exist in the df
    # this will catch single rows that are in the wrong place
    def is_combination_valid(base_fact, comb, signs, target, base_fact_sign=1, set_base_difference=False):
        def compare_series(series1, series2):
            """
            is series2 smaller than series1
            """
            if series1 is None:
                return True
            series1_value = series1.abs().sum()
            series2_value = series2.abs().sum()
            if series2_value < series1_value:
                return True
            elif series2_value < series1_value:
                return False
            elif (series2 == 0).sum() > (series1 == 0).sum():
                return True
            else:
                return False
        nonlocal closest_match
        nonlocal closest_match_differences
        nonlocal closest_default_match
        nonlocal closest_default_match_differences
        if base_fact is not None:
            base_total = enhanced_df.df.loc[base_fact] * base_fact_sign
        else:
            base_total = 0
        total = base_total + sum(sign * enhanced_df.df.loc[fact] for sign, fact in zip(signs, comb))
        print(total, target)
        # TODO make it less strict of copmare for rows that are sum
        # Calculate the absolute differences
        differences = (target - total)
        # Find indices where the values are exactly equal
        exact_matches = (differences == 0)
        if set_base_difference:
            closest_match = [base_fact, comb, signs]
            closest_match_differences = differences
            closest_default_match = closest_match
            closest_default_match_differences = differences


        # If two or more values are exact matches, check the remaining value with tolerance
        # TODO make it accept one match if the row is a smu (reu)
        allowed_difference = target * tolerance
        # for diff in allowed_difference:
        #     if diff < 
        # TODO maintaina min allowed_diff
        if exact_matches.sum() == 2 or (exact_matches.sum() == 1 and not strict_compare and (differences.abs() < allowed_difference.abs()).all()) or (not strict_compare and (differences.abs() < allowed_difference.abs()).all()) or must_find_comb:
            # print(allowed_difference, differences)
            # TODO since sum rows call multiple equatoin, this will alwas add a fix to saisfy the first equation 
            if (differences.abs() < allowed_difference.abs()).all() or (not strict_compare and reu_class) or must_find_comb:
                print(len(signs) + (1 if base_fact else 0))
                if (len(signs) + (1 if base_fact else 0)) > 1:
                    if compare_series(closest_match_differences, differences):
                        # if set_base_difference:
                        #     closest_default_match = [base_fact, comb, signs]
                        #     closest_match = closest_default_match
                        #     closest_match_differences = closest_default_match_differences
                        closest_match = [base_fact, comb, signs]
                        closest_match_differences = differences
        # Check if the total is close to the target within the tolerance
        # print(np.isclose(total, target, atol=1e-15))
        return np.isclose(total, target,rtol=1e-10, atol=1e-6).all()
        return (total == target).all()

    def adjust_signs(base_fact, comb, signs, base_fact_sign=1):
        def update_facts(enhanced_df, fact, sign):
            master_list = enhanced_df.get_master_list(fact)
            if master_list:
                for sub_fact in master_list:
                    enhanced_df.df.loc[sub_fact] *= sign
                    # Recursively update sub-facts of the current sub_fact
                    update_facts(enhanced_df, sub_fact, sign)
        # if base_fact is not None:
        #     df.df.loc[base_fact] *= base_fact_sign
         # Base fact keeps its original sign
        # if subtraction is what is needed the sign will be already negative which is correct
        # so flip all the signs to only change the one i added instead of subtracting
        if change_sign:
            if not preferred_operation_addition:
                signs *= -1
            for fact, sign in zip(comb, signs):
                # change slaves values
                enhanced_df.df.loc[fact] *= sign
                update_facts(enhanced_df, fact, sign)
    print("=============", target)
    print(start_index, end_index)
    result = []
    # special_fact_index = df.df.index.get_loc(special_fact)
    possible_facts = enhanced_df.df.index[start_index:end_index]
    all_facts = enhanced_df.df.index.tolist()
    found_combination = False
    # Generate initial signs based on the preferred operation
    initial_signs = [1 if preferred_operation_addition else -1] * len(possible_facts)

    if check_all_comb:
        first_index = end_index -1
    else:
        first_index = start_index
    # Try combinations starting with the closest rows first
    for base_index in range(first_index, max(start_index-1 ,-1), -1):
        print(start_index, end_index, base_index, possible_facts)
        base_fact = all_facts[base_index]
        base_fact_sign = 1
        print(base_index)
        # print(possible_facts[:base_index])
        print(all_facts[base_index+1:end_index])
        if change_base_sign:
            remaining_facts = all_facts[base_index:end_index]
            base_fact = None
        else:
            remaining_facts = all_facts[base_index+1:end_index]

        if len(remaining_facts) == 0:
            continue
        
        print(remaining_facts)
        for fact in remaining_facts:
            # TODO: this part need to be improved either here or where the master is combupted
            master_facts = []
            if check_if_master_in_list(fact, remaining_facts) or (enhanced_df.variable_in_list(fact) == base_fact and base_fact is not None):
                master_facts.append(fact)
                comb_list = list(remaining_facts)
                comb_list.remove(fact)
                remaining_facts = tuple(comb_list)
        print(remaining_facts)
        print(enhanced_df.master_list_dict)
        # for r in range(1, len(remaining_facts) + 1):
            # for comb in combinations(remaining_facts[::-1], r):  # Reverse to start with closest rows
                # First try with the initial signs based on the preferred operation
        MAX_ALL_COMB_NEGATIVE = 4
        for comb in combinations(remaining_facts, len(remaining_facts)):
            # master_facts = []
            # for fact in comb:
            #     # TODO: this part need to be improved either here or where the master is combupted
            #     if check_if_master_in_list(fact, comb) or (df.variable_in_list(fact) == base_fact and base_fact is not None):
            #         master_facts.append(fact)
            #         comb_list = list(comb)
            #         comb_list.remove(fact)
            #         comb = tuple(comb_list)
            signs = initial_signs[:len(comb)]
            # signs = [0 if fact in master_facts else sign for fact, sign in zip(comb, signs)]
            print(f"Trying combination with base: {base_fact} and additional: {comb} with signs: {signs}")
            if is_combination_valid(base_fact, comb, initial_signs[:len(comb)], target, set_base_difference=True):
                print(f"Match found with initial signs for {base_fact} and {comb}")
                result = [base_fact] + list(comb)
                found_combination = True
                break
            # If the preferred operation did not work, try all possible sign combinations
            # Split the facts into those with predefined signs and those without
            # Convert the predefined signs list to a dictionary for easier lookup
            if facts_weight:
                predefined_signs = {item['fact']: float(item['weight']) for item in facts_weight}
            else:
                predefined_signs = {}
            # Create a list to hold the final signs
            signs = [None] * len(comb)  # Initialize with None to indicate positions that need to be filled
            fixed_signs = []
            variable_facts = []
            variable_signs_index = []
            for i, fact in enumerate(comb):
                if fact in predefined_signs:
                    signs[i] = predefined_signs[fact]  # Set the fixed signs in their correct positions
                else:
                    variable_facts.append(fact)
                    variable_signs_index.append(i)
                print(predefined_signs)
            if check_for_negative:
                if check_all_comb:
                    if MAX_ALL_COMB_NEGATIVE == 0:
                        check_for_negative = False
                    MAX_ALL_COMB_NEGATIVE -= 1
                # Generate only the variable sign combinations
                for variable_signs in product([1, -1], repeat=len(variable_facts)):
                    # Combine fixed signs with the current combination of variable signs
                    for i, sign in zip(variable_signs_index, variable_signs):
                        signs[i] = sign
                    # signs = [0 if fact in master_facts else sign for fact, sign in zip(comb, signs)]
                    print(f"Trying combination with base: {base_fact} and additional: {comb} with signs: {signs}")
                    if is_combination_valid(base_fact, comb, signs, target):
                        print(f"Match found with signs {signs} for {base_fact} and {comb}")
                        # signs = [1 if sign == 0 else sign for sign in signs]
                        adjust_signs(base_fact, comb, signs)
                        result = [base_fact] + list(comb)
                        found_combination = True
                        break
                    elif not change_base_sign and change_sign: # if you can not change base sing check if its reported with the wron sign
                        if is_combination_valid(base_fact, comb, signs, target * -1):
                            print(f"Match found with signs {signs} for {base_fact} and {comb}")
                            # signs = [1 if sign == 0 else sign for sign in signs]
                            adjust_signs(base_fact, comb, signs)
                            enhanced_df.df.loc[target.name] *= -1
                            result = [base_fact] + list(comb)
                            found_combination = True
                            break
            if found_combination:
                break
        if found_combination:
            break
        # TODO add an extra row for the adjustmens, so the variable can become a master,
        # otherwise because of the small difference, this variable will fail to be a master
        if not found_combination and not strict_compare:
            if check_for_total:
                if (enhanced_df.df.iloc[start_index] + enhanced_df.df.iloc[end_index -1] == enhanced_df.df.iloc[end_index]).all():
                    total_expense = 'Total income (expense)'
                    while total_expense in enhanced_df.df.index.tolist():
                        total_expense += '_new'
                    enhanced_df = rename_df_index(enhanced_df, enhanced_df.df.index[end_index-1], total_expense)
                    # index_map = {df.df.index[end_index-1]: total_expense}
                    # df.df.rename(index=index_map, inplace=True)
                    found_combination = True
                    result = enhanced_df.df.index[end_index-1]
                elif (enhanced_df.df.iloc[start_index] - enhanced_df.df.iloc[end_index -1] == enhanced_df.df.iloc[end_index]).all():
                    # TODO adjust sign
                    enhanced_df.df.iloc[end_index-1] *= -1
                    total_expense = 'Total income (expense)'
                    while total_expense in enhanced_df.df.index.tolist():
                        total_expense += '_new'
                    enhanced_df = rename_df_index(enhanced_df, enhanced_df.df.index[end_index-1], total_expense)
                    # index_map = {df.df.index[end_index-1]: total_expense}
                    # df.df.rename(index=index_map, inplace=True)
                    found_combination = True
                    result = enhanced_df.df.index[end_index-1]
                elif closest_match is not None and not found_combination:
                    base_fact, comb, signs = closest_match
                    adjust_signs(*closest_match)
                    result = [base_fact] + list(comb)
                    found_combination = True
                    fix = "A FIX"
                    while fix in enhanced_df.df.index.tolist():
                        fix += '_new'
                    # check if the values match another row with [1, -1] if positive move that row to the fix place, 
                    # if negative move that row after end_index
                    fix_match_found = False
                    for data_fact2 in enhanced_df.df.index.tolist():
                        if enhanced_df.df.loc[data_fact2].equals(closest_match_differences) and "A FIX" not in data_fact2:
                            # replace the rows
                            print(enhanced_df.df)
                            enhanced_df.df = enhanced_df.df.drop(data_fact2)
                            enhanced_df = add_row_to_df(enhanced_df, closest_match_differences,  data_fact2, enhanced_df.df.index[end_index-1], insert_after=False)
                            print(enhanced_df.df)
                            fix_match_found = True
                        elif enhanced_df.df.loc[data_fact2].equals(closest_match_differences*-1) and "A FIX" not in data_fact2:
                            # replace the rows
                            print(enhanced_df.df)
                            enhanced_df.df = enhanced_df.df.drop(data_fact2)
                            enhanced_df = add_row_to_df(enhanced_df, closest_match_differences*-1,  data_fact2, enhanced_df.df.index[end_index-1], insert_after=True)
                            print(enhanced_df.df)
                            fix_match_found = True
                        elif enhanced_df.df.loc[data_fact2].equals(closest_default_match_differences) and "A FIX" not in data_fact2:
                            # replace the rows
                            enhanced_df.df = enhanced_df.df.drop(data_fact2)
                            enhanced_df = add_row_to_df(enhanced_df, closest_default_match_differences,  data_fact2, enhanced_df.df.index[end_index-1], insert_after=False)
                            fix_match_found = True
                        elif df.df.loc[data_fact2].equals(closest_default_match_differences*-1) and "A FIX" not in data_fact2:
                            # replace the rows
                            enhanced_df.df = enhanced_df.df.drop(data_fact2)
                            enhanced_df = add_row_to_df(enhanced_df, closest_default_match_differences*-1,  data_fact2, enhanced_df.df.index[end_index-1], insert_after=True)
                            fix_match_found = True
    
                    if not fix_match_found:
                        enhanced_df = add_row_to_df(dfenhanced_df, closest_match_differences, fix, enhanced_df.df.index[end_index], insert_after=False)
            elif closest_match is not None and not found_combination:
                fix_match_found = False
                print(closest_match_differences)
                for data_fact2 in enhanced_df.df.index.tolist():
                    if fix_match_found:
                        break
                    if enhanced_df.df.loc[data_fact2].equals(closest_match_differences) and "A FIX" not in data_fact2:
                        # replace the rows
                        print(enhanced_df.df)
                        enhanced_df.df = enhanced_df.df.drop(data_fact2)
                        enhanced_df = add_row_to_df(enhanced_df, closest_match_differences,  data_fact2, enhanced_df.df.index[end_index-1], insert_after=False)
                        print(df.df)
                        fix_match_found = True
                    elif enhanced_df.df.loc[data_fact2].equals(closest_match_differences*-1) and "A FIX" not in data_fact2:
                        # replace the rows
                        enhanced_df.df = enhanced_df.df.drop(data_fact2)
                        enhanced_df = add_row_to_df(enhanced_df, closest_match_differences*-1,  data_fact2, enhanced_df.df.index[end_index-1], insert_after=True)
                        fix_match_found = True
                    elif enhanced_df.df.loc[data_fact2].equals(closest_default_match_differences) and "A FIX" not in data_fact2:
                        # replace the rows
                        enhanced_df.df = enhanced_df.df.drop(data_fact2)
                        enhanced_df = add_row_to_df(enhanced_df, closest_default_match_differences,  data_fact2, enhanced_df.df.index[end_index-1], insert_after=False)
                        fix_match_found = True
                    elif enhanced_df.df.loc[data_fact2].equals(closest_default_match_differences*-1) and "A FIX" not in data_fact2:
                        # replace the rows
                        enhanced_df.df = enhanced_df.df.drop(data_fact2)
                        enhanced_df = add_row_to_df(df, closest_default_match_differences*-1,  data_fact2, enhanced_df.df.index[end_index-1], insert_after=True)
                        fix_match_found = True
                if fix_match_found :
                    found_combination = True
                    result = [base_fact] + list(comb)
                else:
                    base_fact, comb, signs = closest_match
                    adjust_signs(*closest_match)
                    fix = "A FIX"
                    while fix in enhanced_df.df.index.tolist():
                        fix += '_new'
                    if closest_match_differences.abs().sum() < target.abs().sum() and (end_index - start_index) > 1:
                        enhanced_df = add_row_to_df(enhanced_df, closest_match_differences, fix, enhanced_df.df.index[end_index], insert_after=False)
                        found_combination = True
                        result = [base_fact] + list(comb)

    return result

def combine_variables(df: DataFrameWithStringListTracking, start_pos, end_pos, base_var=None, subtract=False, check_master=True):
    # NOTE do not remove new_var = 0 otherwise you will pass by reference
    new_var = 0
    if base_var is not None:
        new_var += df.df.loc[base_var]
    for pos in range(start_pos, end_pos):
        # TODO skip only if the master is part of the combination
        if check_master:
            master = df.variable_in_list(df.df.index[pos])
            if master is not None and master in df.df.index[start_pos:end_pos]:
                continue
        if subtract:
            if "Income" in df.df.index[pos] and "Expense" in df.df.index[pos]:
                new_var += df.df.iloc[pos]
            else:
                new_var -= df.df.iloc[pos]
        else:
            new_var += df.df.iloc[pos]
    return new_var

def check_for_inverse_sum(df: DataFrameWithStringListTracking, string_index: str):
    index = df.df.index.get_loc(string_index)
    if (df.df.iloc[index + 1] + df.df.iloc[index + 2] == df.df.iloc[index]).all():
        positive1 = all(val >= 0 for val in df.df.iloc[index])
        positive2 = all(val >= 0 for val in df.df.iloc[index + 1])
        positive3 = all(val >= 0 for val in df.df.iloc[index + 2])
        negative1 = all(val <= 0 for val in df.df.iloc[index])
        negative2 = all(val <= 0 for val in df.df.iloc[index + 1])
        negative3 = all(val <= 0 for val in df.df.iloc[index + 2])
        if (positive1 and positive2 and positive3) or (negative1 and negative2 and negative3):
            return True
    return False

def rename_df_index(df: DataFrameWithStringListTracking, index_map): # string_index: str, new_string_index: str):
    # index_map = {string_index: new_string_index}
    df.df.rename(index=index_map, inplace=True)
    for string_index, new_string_index in index_map.items():
        df.facts_name_dict[string_index] = new_string_index
    return df
    
def check_cal_eq():
    pass
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
class IncomeStatement:

    income_statement_milestones = [GrossProfit, OperatingIncome, EBT, NetIncome]

    def base_eq(df: DataFrameWithStringListTracking, end_index_s: str, compute=False, compare_to=None, add_missing_rows=False, change_sign=False, strict_compare=True):
        pass
    ## NOTE when writing function it seems you pass by pointer and you can change inside df 
    # example :

    # TODO: rewrite the function to account for that const variable might not be in the df!!
    # if not in df add them at the end after you do calculations
    # TODO: if total revenue is a sum it calls the equation which all depend on total revenue already definied

    # TODO statements can have mistakes, update equation to check for 2/3 pass, and change the other value

    # TODO instead of changeing total operating expense to negative, let operating income equation change it if needed
    # if a sum need to be multiplied by -1, all of its components need to also

    # TODO for equations like opearting income, check if the row before it satisfy the equation, 
    # this can catch total expenses that are not of class 'reu' and statement that has numbers that do not add up
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
        # print(df_temp.df, "====2")
        # if df_temp.df.iloc[start_pos+1].sum() > 0 and change_sign:
        #     for row_index, row in df_temp.df.iloc[start_pos+1:end_pos].iterrows():
        #         for col in df_temp.df.columns:
        #             df_temp.df.at[row_index, col] = -row[col]
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
                # if calculate_gp:
                #     total_revenue_index = df_temp.df.index.get_loc('Total revenue')
                #     total_revenue_next_index = df_temp.df.index[total_revenue_index+1] # + 2 because the last variable is not counted, so this ensure to inlcude the variable after Tptal revenue
                #     t_r_next_index_boundry = df_temp.df.index[total_revenue_index+2]
                #     gross_profit = IncomeStatement.gross_profit_eq(df_temp, t_r_next_index_boundry, compute=True, change_sign=change_sign)
                #     df_temp = add_row_to_df(df_temp, gross_profit, GrossProfit, total_revenue_next_index)
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
            # elif (df_temp.df.iloc[start_pos] + df_temp.df.iloc[end_pos -1] == df_temp.df.iloc[end_pos]).all():
            #     total_expense = 'Total operating expense'
            #     while total_expense in df_temp.df.index.tolist():
            #         total_expense += '_new'
            #     index_map = {df_temp.df.index[end_pos-1]: total_expense}
            #     df_temp.df.rename(index=index_map, inplace=True)
            #     df.df = df_temp.df
            #     return True
            # elif (df_temp.df.iloc[start_pos] - df_temp.df.iloc[end_pos -1] == df_temp.df.iloc[end_pos]).all():
                # total_expense = 'Total operating expense'
                # while total_expense in df_temp.df.index.tolist():
                #     total_expense += '_new'
                # index_map = {df_temp.df.index[end_pos-1]: total_expense}
                # df_temp.df.rename(index=index_map, inplace=True)
                # df_temp.df.iloc[end_pos-1] *= -1
                # df.df = df_temp.df
                # return True
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
            if find_combinations_with_logging(df_temp, start_pos, end_pos, compare_to, change_sign=True, strict_compare=strict_compare, check_for_total=True):
                # if calc_total_non_oi:
                #     total_non_operating_expense = IncomeStatement.total_non_operating_expense_eq(df_temp, end_index_s, compute=True, change_sign=change_sign)
                #     df_temp = add_row_to_df(df_temp, total_non_operating_expense, 'Total non-operating income (expense)', end_index_s, insert_after=False)
                df.df = df_temp.df
                return True
            # elif (df_temp.df.iloc[start_pos] + df_temp.df.iloc[end_pos -1] == df_temp.df.iloc[end_pos]).all():
            #     total_expense = 'Total non-operating income (expense)'
            #     while total_expense in df_temp.df.index.tolist():
            #         total_expense += '_new'
            #     index_map = {df_temp.df.index[end_pos-1]: total_expense}
            #     df_temp.df.rename(index=index_map, inplace=True)
            #     df.df = df_temp.df
            #     return True
            # elif (df_temp.df.iloc[start_pos] - df_temp.df.iloc[end_pos -1] == df_temp.df.iloc[end_pos]).all():
            #     total_expense = 'Total non-operating income (expense)'
            #     while total_expense in df_temp.df.index.tolist():
            #         total_expense += '_new'
            #     index_map = {df_temp.df.index[end_pos-1]: total_expense}
            #     df_temp.df.rename(index=index_map, inplace=True)
            #     df_temp.df.iloc[end_pos-1] *= -1
            #     df.df = df_temp.df
            #     return True
            else:
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
        # for ni_w in [NetIncome_with_unusal_items_1, NetIncome_with_unusal_items_2, NetIncome_with_unusal_items_3, NetIncome_with_unusal_items_4]:
        #     if ni_w not in df.df.index.tolist():
        #         # start_pos = df.df.index.get_loc(ni_w)
        #         # base_variable = ni_w
        #         break
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
        # computed_expense = df.iloc[start_pos + 1:end_pos].sum()
        net_income = 0
        # net_income += df.loc['Net income']
        # for pos in range(start_pos+1, end_pos):
        #     net_income += df.iloc[pos]
        # net_income = combine_variables(df, start_pos+1, end_pos, base_var=start_index_s, subtract=True)
        # net_income = find_combinations_with_logging(df, start_pos, end_pos, preferred_operation_addition=False)
        # net_income 
        # net_income = df.loc['EBT'] - df.loc['Income tax expense']
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
            # elif (df_temp.df.iloc[start_pos] + df_temp.df.iloc[end_pos -1] == df_temp.df.iloc[end_pos]).all():
            #     total_expense = 'Total income (expense)'
            #     while total_expense in df_temp.df.index.tolist():
            #         total_expense += '_new'
            #     index_map = {df_temp.df.index[end_pos-1]: total_expense}
            #     df_temp.df.rename(index=index_map, inplace=True)
            #     df.df = df_temp.df
            #     return True
            # elif (df_temp.df.iloc[start_pos] - df_temp.df.iloc[end_pos -1] == df_temp.df.iloc[end_pos]).all():
            #     total_expense = 'Total income (expense)'
            #     while total_expense in df_temp.df.index.tolist():
            #         total_expense += '_new'
            #     index_map = {df_temp.df.index[end_pos-1]: total_expense}
            #     df_temp.df.rename(index=index_map, inplace=True)
            #     df_temp.df.iloc[end_pos-1] *= -1
            #     df.df = df_temp.df
            #     return True
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
            # if NetIncome in df.df.index.tolist() and not found_net_income_subfacts:
                # TODO this will have unwanted behaviour if the tax interest for example is reported as positive instead of negative
                # then it will assume its a inverse sum where it should be a net income
                # maybe they need to have "ProfitLossAttributableTo" in both rows?!
                # if check_for_inverse_sum(df, NetIncome): 
                #     df_index = df.df.index.get_loc(NetIncome)
                    # net_income_subfacts.append(df.df.index[df_index + 1])
                    # net_income_subfacts.append(df.df.index[df_index + 2])
                    # found_net_income_subfacts = True
                    # last_mf_found = df.df.index[df_index + 2]
                    # df.special_master_dict[NetIncome] = [df.df.index[df_index + 1], df.df.index[df_index + 2]]
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
                    case 's3': # check rows thar are class reu
                        if data_fact in df_og.rows_that_are_sum and NetIncome in df.df.index.tolist():
                            # if total revenue is not defined the first sum is total revenue
                            # TODO compare with combined_statement to find total revennue
                            if check_for_net_income(df, data_fact):
                                last_mf_found_with_equation = NetIncome
                                DATA_ADDED = True
                    case 's4': # check rows thar are class reu
                        if data_fact in df_og.rows_that_are_sum:
                            num_of_equations = 4
                            last_match_reached = False
                            print(last_mf_found_with_equation)
                            for index in range(len(income_statment_map2)):
                                mf = income_statment_map2[index]
                                # do not start before reaching last match
                                if mf.fact == last_mf_found_with_equation or last_mf_found_with_equation == 0:
                                    last_match_reached = True
                                if not last_match_reached:
                                    continue
                                if mf.equation is None:
                                    continue
                                if mf_found:
                                    break
                                if mf.match is not None:
                                    continue
                                # if "Total COGS" in df.df.index.tolist() and (mf.fact == TotalCostAndExpenses or mf.fact == TotalOperatingExpense):
                                #     continue
                                if TotalOperatingExpense in df.df.index.tolist() and mf.fact == TotalCostAndExpenses:
                                    continue
                                num_of_equations -= 1
                                print(f'====={mf.fact}')
                                try:
                                    if  mf.call_eq(df, data_fact, compare_to=df_og.df.loc[data_fact], add_missing_rows=True, change_sign=True, strict_compare=False):
                                        if mf.fact == OperatingIncome and "gross" in df.rows_text[data_fact].lower():
                                            # Change total operating expense to total cogs and operating income into gross progit
                                            if TotalOperatingExpense in df.df.index.tolist():
                                                data_fact_2 = get_key_from_value(df.facts_name_dict, TotalOperatingExpense)
                                                index_map = {data_fact: GrossProfit, TotalOperatingExpense: "Total COGS"}
                                                df.facts_name_dict[data_fact_2] = "Total COGS"
                                            else:
                                                index_map = {data_fact: GrossProfit}
                                            # Update the index
                                            df = rename_df_index(df, index_map)
                                            # df.df.rename(index=index_map, inplace=True)
                                            last_mf_found_with_equation = GrossProfit
                                            # df.facts_name_dict[data_fact] = GrossProfit
                                            DATA_ADDED = True
                                            mf_found = True
                                        elif mf.fact == TotalOperatingExpense and "cost of" in df.rows_text[data_fact].lower():
                                            index_map = {data_fact: 'Total COGS'}
                                            # Update the index
                                            df = rename_df_index(df, index_map)
                                            # df.df.rename(index=index_map, inplace=True)
                                            last_mf_found_with_equation = 'COGS'
                                            # df.facts_name_dict[data_fact] = 'Total COGS'
                                            DATA_ADDED = True
                                            mf_found = True
                                        else:
                                            index_map = {data_fact: mf.fact}
                                            # Update the index
                                            df = rename_df_index(df, index_map)
                                            # df.df.rename(index=index_map, inplace=True)
                                            mf.match = data_fact
                                            last_mf_found_with_equation = mf.fact
                                            # df.facts_name_dict[data_fact] = mf.fact
                                            DATA_ADDED = True
                                            mf_found = True
                                except Exception as e:
                                    print(e)
                                    pass
                                if num_of_equations == 0:
                                    break

                            if not DATA_ADDED:
                                start_idx = last_mf_found_with_equation
                                # if last_mf_found_with_equation != 0 and last_mf_found != 0 :
                                #     if df.df.index.get_loc(last_mf_found) > df.df.index.get_loc(last_mf_found_with_equation):
                                #         start_idx = last_mf_found
                                if IncomeStatement.total_of_something(df, start_idx, data_fact, compare_to=df_og.df.loc[data_fact], add_missing_rows=True, change_sign=True, strict_compare=True):
                                    index_map = {data_fact: f"total: {data_fact}"}
                                    # Update the index
                                    df = rename_df_index(df, index_map)
                                    # df.df.rename(index=index_map, inplace=True)
                                    # mf.match = data_fact
                                    last_total_of_something = f"total: {data_fact}"
                                    last_mf_found = data_fact
                                    # last_mf_found_with_equation = data_fact
                                    df.facts_name_dict[data_fact] = f"total: {data_fact}"
                                    DATA_ADDED = True
                            if not DATA_ADDED:
                                # TODO when two total and some facts between them, sometimes the first total is part of the second sometimes its nots
                                # right now it only check if total one is part of total two, but check for total two for facts after total one found using total_of_something()
                                data_fact_slaves = get_facts_by_key(df.cal_facts, data_fact)
                                print(data_fact_slaves)
                                move_above=True
                                if data_fact_slaves:
                                    print(data_fact_slaves, data_fact)
                                    print("==")
                                    # TODO any missing row from the sum but in equation, move it to inlcude it in the equation
                                    facts_misplaced = compare_variable_lists(data_fact_slaves, df.df.index[df.df.index.get_loc(start_idx):data_fact_index], df.facts_name_dict)
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
                                    if IncomeStatement.total_of_something(df, start_idx, data_fact, compare_to=df_og.df.loc[data_fact], add_missing_rows=True, change_sign=True, strict_compare=True):
                                        index_map = {data_fact: f"total: {data_fact}"}
                                        # Update the index
                                        df = rename_df_index(df, index_map)
                                        last_total_of_something = f"total: {data_fact}"
                                        df.facts_name_dict[data_fact] = f"total: {data_fact}"
                                        DATA_ADDED = True
                                    elif last_total_of_something is not None and not DATA_ADDED:
                                        if IncomeStatement.total_of_something(df, last_total_of_something, data_fact, compare_to=df_og.df.loc[data_fact], add_missing_rows=True, change_sign=True, strict_compare=True):
                                            index_map = {data_fact: f"total: {data_fact}"}
                                            # Update the index
                                            df = rename_df_index(df, index_map)
                                            last_total_of_something = f"total: {data_fact}"
                                            df.facts_name_dict[data_fact] = f"total: {data_fact}"
                                            DATA_ADDED = True
                    case 's5': # check rows thar are NOT reu                        
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

CashAndCashEquivalent = "Cash And Cash Equivalen"
CurrentAssets = "Current Assets"
TotalAssets = "Total Assets"
AccountsReceivable = "Accounts Receivable"
RestrictedCash = "Restricted Cash"
OtherAssetsCurrent = "Other Assets Current"
Goodwill = "Goodwill"
IntangibleAssets = "Intangible Assets"
OtherAssetsNoncurrent = "Other Assets Noncurrent"
NonCurrentAssets = "Non Current Assets"
AccountsPayable = "Accounts Payable"
LiabilitiesCurrent = "Current Liabilities"
NonLiabilitiesCurrent = "Non Current Liabilities"
ShortTermDebtCurrent = "Current portion of Short Term Debt"
LongTermDebtCurrent = "Current portion of Long Term Debt"
ShortTermDebt = "Short Term Debt"
LongTermDebt = "Long Term Debt"
DeferredTaxLiabilityNonCurrent = "Deferred Tax Liability Non Current"
OtherLiabilitiesNoncurrent = "Other Liabilities Non current"
TotalLiabilities = "Total Liabilities"
RetainedEarnings = "Retained Earnings"
StockholdersEquity = "Stockholders Equity"
TotalEquity = "Total Equity"
TotalLiabilitiesAndEquity = "Total Liabilities And Equity"
PropertyPlantAndEquipment = "Property Plant And Equipment"
class BalanceSheet:


    ## NOTE when writing function it seems you pass by pointer and you can change inside df 

    # TODO for equations like opearting income, check if the row before it satisfy the equation, 
    # this can catch total expenses that are not of class 'reu' and statement that has numbers that do not add up

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

    def total_stockholders_equity_eq(df: DataFrameWithStringListTracking, end_index_s: str, compute=False, compare_to=None, add_missing_rows=False, change_sign=False, strict_compare=True, must_find_comb=False, facts_weight=None, reu_class=False):
        df_temp = 0
        df_temp = copy.deepcopy(df)
        compare_to_c = 0
        compare_to_c = copy.deepcopy(compare_to)
        
        # Find the positions of the start and end index names
        if TotalLiabilities not in df_temp.df.index.tolist():
            if 'StockholdersEquity' in end_index_s or 'Equity' in end_index_s:
                # TODO: re assign end_pos to something more reasnoalbe
                ## check the data_fact if its has cal.xml or if it has master_list
                # calculate TotalLiabilities
                
                # check for master list
                print(df_temp.df)
                fact_eq_list = None
                if end_index_s in df.master_list_dict:
                    fact_eq_list = df.master_list_dict[end_index_s]
                if facts_weight and not fact_eq_list:
                        fact_eq_list = [item['fact'] for item in facts_weight]
                        print(fact_eq_list)
                if fact_eq_list:
                    end_pos_TL_s = find_extreme_index_element(fact_eq_list, df_temp.df.index.tolist(),  find_highest=False)
                    print(end_pos_TL_s)
                    end_pos_TL = df_temp.df.index.get_loc(end_pos_TL_s)
                    start_pos = df_temp.df.index.get_loc(TotalAssets) +1
                    def_temp_indexes = df_temp.df.index.tolist()
                    # result = find_combinations_with_logging(df_temp, start_pos, end_pos_TL, compare_to_c, change_sign=True, change_base_sign=True, strict_compare=strict_compare, must_find_comb=must_find_comb, check_for_negative=False, check_all_comb=True)
                    if abs(start_pos - end_pos_TL) > 5 or (LiabilitiesCurrent in def_temp_indexes[start_pos : end_pos_TL] and abs(start_pos - end_pos_TL) > 3) or (LiabilitiesCurrent in def_temp_indexes[start_pos : end_pos_TL] and NonLiabilitiesCurrent in def_temp_indexes[start_pos : end_pos_TL]):
                        total_liabilities = combine_variables(df_temp, start_pos, end_pos_TL)
                        df_temp = add_row_to_df(df_temp, total_liabilities,  TotalLiabilities, end_pos_TL_s, insert_after=False)
                        print(df_temp.df)
                        print(end_pos_TL_s)
        print(df_temp.df)

        end_pos = df_temp.df.index.get_loc(end_index_s)
        start_pos = df_temp.df.index.get_loc(TotalLiabilities) + 1
         # or 'Operating income'
        if compare_to is not None and change_sign:
            if find_combinations_with_logging(df_temp, start_pos, end_pos, compare_to_c, change_sign=True, change_base_sign=True, strict_compare=strict_compare, must_find_comb=must_find_comb, check_for_negative=True, facts_weight=facts_weight, reu_class=reu_class):
                df.df =df_temp.df
                start_pos = df.df.index.get_loc(TotalLiabilities) + 1
                end_pos = df.df.index.get_loc(end_index_s)
                df.special_master_dict[StockholdersEquity] = df.df.index[start_pos: end_pos]
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
        return df.loc['Total operating expense', df.columns[-1]] == computed_expense[-1]

    def total_liabilities_and_equity_eq(df: DataFrameWithStringListTracking, end_index_s: str, compute=False, compare_to=None, add_missing_rows=False, change_sign=False, strict_compare=True, must_find_comb=False, facts_weight=None, reu_class=False):
        df_temp = 0
        df_temp = copy.deepcopy(df)
        compare_to_c = 0
        compare_to_c = copy.deepcopy(compare_to)
        check_equal_total_assets = False
        # Find the positions of the start and end index names
        TotalLiabilities_pos = df_temp.df.index.get_loc(TotalLiabilities)
        # StockholdersEquity_pos = df_temp.df.index.get_loc(TotalEquity)
        # if compare_to is not None and change_sign:
        #     total = df_temp.df.iloc[TotalLiabilities_pos] + df_temp.df.iloc[StockholdersEquity_pos]
        #     return compare_to.equals(total)
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

# TODO ass a master attr to the df rows or maybe create a dict
# only assign the constant variables to variables that do not have a master

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
                    case 's2': # check rows thar are class reu
                        if data_fact in df_og.rows_that_are_sum:
                            num_of_equations = 3
                            data_fact_mfs = find_possible_names(data_fact, last_mf_found_with_equation)
                            # TODO when two total and some facts between them, sometimes the first total is part of the second sometimes its nots
                            # right now it only check if total one is part of total two, but check for total two for facts after total one found using total_of_something()
                           
                            for mf in data_fact_mfs:
                                try:
                                    num_of_equations -= 1
                                    print(mf.fact)
                                    if  mf.call_eq(df, data_fact, compare_to=df_og.df.loc[data_fact], add_missing_rows=True, change_sign=True, strict_compare=False, reu_class=True):
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
                                        break
                                except Exception as e:
                                    print(e)
                                    pass
                            if not DATA_ADDED:
                                start_idx = last_mf_found_with_equation
                                if BalanceSheet.total_of_something(df, start_idx, data_fact, compare_to=df_og.df.loc[data_fact], add_missing_rows=True, change_sign=True, strict_compare=True, reu_class=True):
                                    index_map = {data_fact: f"total: {data_fact}"}
                                    # Update the index
                                    df = rename_df_index(df, index_map)
                                    last_total_of_something = f"total: {data_fact}"
                                    last_mf_found = data_fact
                                    df.facts_name_dict[data_fact] = f"total: {data_fact}"
                                    DATA_ADDED = True
                            if not DATA_ADDED:
                                start_idx = last_mf_found_with_equation
                                if BalanceSheet.total_of_something(df, start_idx, data_fact, compare_to=df_og.df.loc[data_fact], add_missing_rows=True, change_sign=True, strict_compare=True, check_all_comb=True, reu_class=True):
                                    index_map = {data_fact: f"total: {data_fact}"}
                                    # Update the index
                                    df = rename_df_index(df, index_map)
                                    last_total_of_something = f"total: {data_fact}"
                                    last_mf_found = data_fact
                                    df.facts_name_dict[data_fact] = f"total: {data_fact}"
                                    DATA_ADDED = True
                            # if not DATA_ADDED and df.cal_facts:
                                # TODO when two total and some facts between them, sometimes the first total is part of the second sometimes its nots
                                # right now it only check if total one is part of total two, but check for total two for facts after total one found using total_of_something()
                    case 's3': # check rows thar are class reu
                        if data_fact in df_og.rows_that_are_sum:
                            data_fact_mfs =  find_possible_names(data_fact, last_mf_found_with_equation)
                            if data_fact_mfs:
                                if len(data_fact_mfs) > 1:
                                    print(string_rank.index(data_fact_mfs[0].fact) ,string_rank.index(data_fact_mfs[1].fact))
                                    if string_rank.index(data_fact_mfs[0].fact) < string_rank.index(data_fact_mfs[1].fact):
                                        mf = data_fact_mfs[0]
                                    else:
                                        mf = data_fact_mfs[1]
                                else:
                                    mf = data_fact_mfs[0]
                                try:
                                    if data_fact in df.cal_facts:
                                        if  mf.call_eq(df, data_fact, compare_to=df_og.df.loc[data_fact], add_missing_rows=True, change_sign=True, strict_compare=False, must_find_comb=True, reu_class=True, facts_weight=df.cal_facts[data_fact]):
                                            index_map = {data_fact: mf.fact}
                                            # Update the index
                                            df = rename_df_index(df, index_map)
                                            mf.match = data_fact
                                            last_mf_found_with_equation = mf.fact
                                            DATA_ADDED = True
                                            mf_found = True
                                    elif  mf.call_eq(df, data_fact, compare_to=df_og.df.loc[data_fact], add_missing_rows=True, change_sign=True, strict_compare=False, must_find_comb=True, reu_class=True):
                                            index_map = {data_fact: mf.fact}
                                            # Update the index
                                            df = rename_df_index(df, index_map)
                                            mf.match = data_fact
                                            last_mf_found_with_equation = mf.fact
                                            DATA_ADDED = True
                                            mf_found = True
                                except Exception as e:
                                    print(e)
                                    pass
                                if num_of_equations == 0:
                                    break
                    case 's4': # check rows thar are NOT reu                        
                        data_fact_mfs =  find_possible_names(data_fact, last_mf_found_with_equation, check_for_equation=False)
                        # renmae only if there is any matches
                        if data_fact_mfs:
                            if len(data_fact_mfs) > 1 and data_fact_mfs[0].fact in string_rank and data_fact_mfs[1].fact in string_rank:
                                print(string_rank.index(data_fact_mfs[0].fact) ,string_rank.index(data_fact_mfs[1].fact))
                                if string_rank.index(data_fact_mfs[0].fact) < string_rank.index(data_fact_mfs[1].fact):
                                    mf = data_fact_mfs[0]
                                else:
                                    mf = data_fact_mfs[1]
                            else:
                                mf = data_fact_mfs[0]
                            #     # TODO make calc if needed fot total expense
                            print(f"====={mf.fact}")
                            if mf.equation:
                                try:
                                    # TODO, find a wayt o verify if strict_compare need to be set to FALSE
                                    # some equation facts like Total Assets can be reported not as 'reu' and it need "A FIX"
                                    satisfy_equation = mf.call_eq(df, data_fact, compare_to=df_og.df.loc[data_fact], change_sign=True, strict_compare=False, reu_class=False)
                                except:
                                    satisfy_equation = False
                                if satisfy_equation:
                                    # TODO change index name instead of asigning a new row
                                    index_map = {data_fact: mf.fact}
                                    df = rename_df_index(df, index_map)
                                    mf.match = data_fact
                                    last_mf_found_with_equation = mf.fact
                                    DATA_ADDED= True
                            elif mf.match is None:
                                index_map = {data_fact: mf.fact}
                                df = rename_df_index(df, index_map)
                                mf.match = data_fact
                                DATA_ADDED = True
                if DATA_ADDED:
                    break
        self.balance_sheet = df