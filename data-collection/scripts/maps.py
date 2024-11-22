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
