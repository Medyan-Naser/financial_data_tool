from edgar_functions import *
from headers import headers
from edgar import *
from equations import *
from tabnine_map import *
import pandas as pd
import numpy as np
import sys
import os
from helpers import *

# used to check what section the item belong to
constants_facts = ['Total revenue', 'Gross profit', 'Operating income',  'EBT', 'Net income', "Current Assets", "Non Current Assets", "Total Assets", "Current Liabilities", "Non Current Liabilities", "Total Liabilities",  "Stockholders Equity",  "Total Equity", "Total Liabilities And Equity"] # 'Total non-operating income (expense)', 'Total operating expense', 'C&E',, 'Net income including unusal items 1', 'Net income including unusal items 2', 'Earnings Per Share Basic']

# Do not create _new for this tiem
no_repetation = ['Total revenue', 'Total operating expense', 'C&E', 'Net income', 'Earnings Per Share Basic', 'Earnings Per Share Diluted', 'Weighted Average Number Of Shares Outstanding Basic', 'Weighted Average Number Of Diluted Shares Outstanding', "Current Assets", "Total Assets", "Current Liabilities", "Total Liabilities", "Total Liabilities And Equity"]

# verified by equation:
equation_facts = ['Operating income',  'EBT', 'Net income including unusal items 1', 'Net income' ]

# sub bouandy facts
facts_sub = {NonLiabilitiesCurrent : TotalLiabilities, NonCurrentAssets : TotalAssets, TotalLiabilities : NonLiabilitiesCurrent, TotalAssets : NonCurrentAssets}

income_names = ['Gross profit', 'Operating income',  'EBT', 'Net income']
ICOME_FACT = "ICOME_FACT"

def find_matching_indices(df, target_index, columns):
    # Ensure target_index is in the DataFrame
    if target_index not in df.index:
        return []
    # Get the values of the target row for the specified columns
    target_values = df.loc[target_index, columns]
    # Find other rows that share the same values in the specified columns
    matching_indices = []
    for index in df.index:
        if index == target_index:
            continue
        if (df.loc[index, columns] == target_values).all():
            matching_indices.append(index)
    return matching_indices

def find_bounding_fact(fact, facts_list):
    """ Find the nearest bounding fact below the given fact. """
    if isinstance(fact, str):
        try:
            index = facts_list.index(fact)
        except ValueError:
            return None  # Fact not found
    else:
        index = fact
    for i in range(index+1, len(facts_list)):
        if facts_list[i] in constants_facts:
            if facts_list[i] in income_names:
                return ICOME_FACT
            return facts_list[i]
    return None

# TODO: check for value matches which is higher importance then name match unless its a constant_fact
# usually there is 2 common columns, so you can have two facts with the same numbers for teh common column but not the new one
# total expenxe could be the same as another value if there is only one itme in the sum
# TODO: numbers are someitmes reported twoce intentially in differnecnt secetion, but the code match it to the first instance
# TODO: make sure you keep track of rows order, do not mix them
def merge_statements3(df1, df2):
    def check_if_order_maintaned(fact1, fact2, fact_map):
        fact1_index = merged_index.index(fact1)
        mapped_fact = fact_map.get(fact2, fact2)
        fact2_index = merged_index.index(mapped_fact)
        print(fact1, fact2, fact1_index, fact2_index)
        if fact2_index < fact1_index:
            return True
        return False

    # Merge the indexes of both dataframes
    merged_index = list(df1.index)  # Start with df1's index
    # Map to keep track of which facts have been processed and renamed
    fact_map = {}
    last_index_match = 0
    df2_facts = df2.index.tolist()
    df1_matches = []
    total_rev_found = False
    for df2_fact_index, df2_fact in enumerate(df2_facts):
        if TotalRevenue == df2_fact:
            total_rev_found = True
        print("===1++", df2_fact)
        # If the fact is present in df1
        df1_match = None
        df2_match = False
        check_row_order = True
        check_if_row_is_first = False
        if df2_fact == TotalRevenue:
            check_row_order = False
        elif df2_fact_index == 0:
            check_if_row_is_first = True
        for df1_fact in df1.index:
            if check_if_index_value_match(df1, df2, df1_fact, df2_fact, strict_compare=True):
                if df1_fact not in df1_matches:
                    df1_match = df1_fact
                    df1_matches.append(df1_match)
                    break
        # if df2_fact in df1.index:
        if df1_match:
            if check_row_order:
                if check_if_row_is_first:
                    if merged_index.index(df1_match) == 0:
                        last_index_match = merged_index.index(df1_match) + 1
                        fact_map[df2_fact] = df1_match
                        df2_match = True
                elif check_if_order_maintaned(df1_match, df2_facts[df2_fact_index-1], fact_map):
                    last_index_match = merged_index.index(df1_match) + 1
                    fact_map[df2_fact] = df1_match
                    df2_match = True
            else:
                last_index_match = merged_index.index(df1_match) + 1
                fact_map[df2_fact] = df1_match
                df2_match = True
        # NOTE: if for example operating income become EBT, and operating income is going to match with EBT
        # EBT then will have to stay EBT?
        # keep track of row
        if df2_match:
            continue
        if df2_fact in no_repetation and df2_fact in merged_index:
            if check_row_order:
                if check_if_row_is_first:
                    if merged_index.index(df1_match) == 0:
                        last_index_match = merged_index.index(df1_match) + 1
                        fact_map[df2_fact] = df1_match
                        df2_match = True
                if check_if_order_maintaned(df2_fact, df2_facts[df2_fact_index-1], fact_map):
                    last_index_match = merged_index.index(df2_fact) + 1
                    fact_map[df2_fact] = df2_fact
                    df2_match = True
            else: 
                last_index_match = merged_index.index(df2_fact) + 1
                fact_map[df2_fact] = df2_fact
                df2_match = True
        if df2_match:
            continue
        if df2_fact in equation_facts:
            df2_f_index = equation_facts.index(df2_fact)
            for i in range(df2_f_index, len(equation_facts)):
                if equation_facts[i] in merged_index:
                    if check_if_order_maintaned(equation_facts[i], df2_facts[df2_fact_index-1], fact_map):
                        last_index_match = merged_index.index(equation_facts[i]) + 1
                        fact_map[df2_fact] = equation_facts[i]
                        df2_match = True
                        break
        if df2_match:
            continue
        # ELSE
        df1_bounding = find_bounding_fact(df2_fact, df1.index.tolist())
        df2_bounding = find_bounding_fact(df2_fact, df2.index.tolist())
        if df2_bounding == df1_bounding and df2_bounding is not None:
            if check_row_order: 
                if check_if_order_maintaned(df2_fact, df2_facts[df2_fact_index-1], fact_map):
                    last_index_match = merged_index.index(df2_fact) + 1
                    df2_match = True
            else:
                last_index_match = merged_index.index(df2_fact) + 1
                df2_match = True
        if df2_match:
            continue
        # TODO fix if common name and maintanined order
        if df2_fact in merged_index:
            if check_if_order_maintaned(df2_fact, df2_facts[df2_fact_index-1], fact_map):
                last_index_match = merged_index.index(df2_fact) + 1
                df2_match = True
        if df2_match:
            continue
        df2_fact_new = df2_fact
        while df2_fact_new in merged_index:
            df2_fact_new += "_new"
        fact_map[df2_fact] = df2_fact_new
        merged_index.insert(last_index_match, df2_fact_new)
        last_index_match += 1
    # Create the merged DataFrame
    merged_columns = sorted(set(df1.columns).union(df2.columns), reverse=True)
    merged_df = pd.DataFrame(index=merged_index, columns=merged_columns).fillna(0)
    # Fill the merged DataFrame with data from df1
    for fact in df1.index:
        merged_df.loc[fact, df1.columns] = df1.loc[fact]
    # Fill the merged DataFrame with data from df2
    for fact in df2.index:
        mapped_fact = fact_map.get(fact, fact)
        for column in df2.columns:
            if column not in df1.columns:
                merged_df.loc[mapped_fact, column] = df2.loc[fact, column]
    # Remove rows with only zero values
    merged_df = merged_df.loc[~(merged_df == 0).all(axis=1)]
    return merged_df

# TODO companies stop reporting or start stuff like totla non curretn assets, 
# so the boundary fact should be more flixible
def merge_statements(df1, df2):
    def check_if_order_maintaned(fact1, fact2, fact_map, check_bounding_fact=False):
        fact1_index = merged_index.index(fact1)
        if "A FIX" in fact2:
            fact2 = df2_facts[df2_facts.index(fact2) - 1]
        print('**************')
        print(df1)
        print(df2)
        print(fact_map)
        print(fact1, fact2)
        for f2 in (fact2, df2_facts[df2_facts.index(fact2) - 1]):
            try:
                mapped_fact = fact_map.get(f2, f2)
                fact2_index = merged_index.index(mapped_fact)
                break
            except Exception as e:
                pass
        

        # mapped_fact = fact_map.get(fact2, fact2)
        # fact2_index = merged_index.index(mapped_fact)
        # print(fact1, fact2, fact1_index, fact2_index)
        # TODO: even if you find a value match, it can be in wrong location, like sub total rev 
        # used to be reported at the end and now at top
        if check_bounding_fact:
            df1_bounding = find_bounding_fact(fact1, df1.index.tolist())
            df2_bounding = find_bounding_fact(fact2, df2.index.tolist())
            if df2_bounding is not None and df1_bounding is not None:
                if df2_bounding == df1_bounding and ((fact1_index - fact2_index) < 10 ):
                    return True
            elif fact2_index < fact1_index and ((fact1_index - fact2_index) < 10 ):
                return True
        elif fact2_index < fact1_index and ((fact1_index - fact2_index) < 10 ):
            return True
        return False

    # Merge the indexes of both dataframes
    merged_index = list(df1.index)  # Start with df1's index
    # Map to keep track of which facts have been processed and renamed
    fact_map = {}
    last_index_match = 0
    df2_facts = df2.index.tolist()
    df1_matches = []
    total_rev_found = False
    for df2_fact_index, df2_fact in enumerate(df2_facts):
        cases = ['s1', 's2', 's3', 's4', 's5', 's6', 's7', 'd']
        df2_match = False
        check_row_order = True
        if df2_fact_index == 0:
            check_row_order = False
        for c in cases:
            match c:
                # if check_if_order_maintaned(df2_fact, df2_facts[df2_fact_index-1], fact_map):
                case 's1': # check for number match
                    # NOTE: number match does not gurantee a name match
                    df1_match = None
                    for df1_fact in df1.index:
                        if check_if_index_value_match(df1, df2, df1_fact, df2_fact, strict_compare=True):
                            # TODO do not alwyas match A FIX to a a row, it could match but be seperate
                            if df1_fact not in df1_matches and "A FIX" not in df1_fact and ("A FIX" not in df2_fact):
                                df1_match = df1_fact
                                df1_matches.append(df1_match)
                                break
                    # if df2_fact in df1.index:
                    if df1_match:
                        if check_row_order:
                            if check_if_order_maintaned(df1_match, df2_fact, fact_map, check_bounding_fact=True):
                                last_index_match = merged_index.index(df1_match) + 1
                                fact_map[df2_fact] = df1_match
                                df2_match = True
                        else:
                            if df1_match == TotalRevenue or  merged_index.index(df1_match) == 0:
                                last_index_match = merged_index.index(df1_match) + 1
                                fact_map[df2_fact] = df1_match
                                df2_match = True
                case 's2': # combine "A FIX"
                    if "A FIX" in df2_fact:
                        for f in df1.index.tolist():
                            if "A FIX" in f:
                                df1_bounding = find_bounding_fact(f, df1.index.tolist())
                                df2_bounding = find_bounding_fact(df2_fact, df2.index.tolist())
                                # for fix in df1.index[df2_]
                                if df2_bounding == df1_bounding and df2_bounding is not None:
                                    # if check_if_order_maintaned(df2_fact, df2_facts[df2_fact_index-1], fact_map):
                                    last_index_match = merged_index.index(df2_fact) + 1
                                    fact_map[df2_fact] = f
                                    df2_match = True
                case 's3':
                    if df2_fact in no_repetation and df2_fact in merged_index:
                        if check_row_order:
                            if check_if_order_maintaned(df2_fact, df2_facts[df2_fact_index-1], fact_map):
                                last_index_match = merged_index.index(df2_fact) + 1
                                fact_map[df2_fact] = df2_fact
                                df2_match = True
                        else: 
                            if df2_fact == TotalRevenue or  merged_index.index(df2_fact) == 0:
                                last_index_match = merged_index.index(df2_fact) + 1
                                fact_map[df2_fact] = df2_fact
                                df2_match = True
                case 's4':
        # NOTE: if for example operating income become EBT, and operating income is going to match with EBT
        # EBT then will have to stay EBT?
        # keep track of row
                    if df2_fact in equation_facts:
                        df2_f_index = equation_facts.index(df2_fact)
                        for i in range(df2_f_index, len(equation_facts)):
                            if equation_facts[i] in merged_index:
                                if check_if_order_maintaned(equation_facts[i], df2_facts[df2_fact_index-1], fact_map):
                                    last_index_match = merged_index.index(equation_facts[i]) + 1
                                    fact_map[df2_fact] = equation_facts[i]
                                    df2_match = True
                                    break
                case 's5':
                    # if df2_fact in df1.index.tolist():
                    df1_bounding = find_bounding_fact(df2_fact, df1.index.tolist())
                    df2_bounding = find_bounding_fact(df2_fact, df2.index.tolist())
                    if df2_bounding == df1_bounding and df2_bounding is not None:
                        if check_row_order: 
                            if check_if_order_maintaned(df2_fact, df2_facts[df2_fact_index-1], fact_map):
                                last_index_match = merged_index.index(df2_fact) + 1
                                df2_match = True
                        else:
                            if df2_fact == TotalRevenue or  merged_index.index(df2_fact) == 0:
                                last_index_match = merged_index.index(df2_fact) + 1
                                df2_match = True
                case 's6':
                    if df2_fact in merged_index:
                        if check_row_order: 
                            if check_if_order_maintaned(df2_fact, df2_fact, fact_map, check_bounding_fact=True):
                                last_index_match = merged_index.index(df2_fact) + 1
                                df2_match = True
                        else:
                            if df2_fact == TotalRevenue or  merged_index.index(df2_fact) == 0:
                                last_index_match = merged_index.index(df2_fact) + 1
                                df2_match = True
                case 's7':
                    # if df2_fact in df1.index.tolist():
                    df1_bounding = find_bounding_fact(df2_fact, df1.index.tolist())
                    df2_bounding = find_bounding_fact(df2_fact, df2.index.tolist())
                    if df1_bounding is not None and df2_bounding is not None:
                        if df2_bounding not in df1.index.tolist():
                            if df2_bounding in facts_sub:
                                df2_bounding = facts_sub[df2_bounding]
                        if df1_bounding not in df2.index.tolist():
                            if df2_bounding in facts_sub:
                                df2_bounding = facts_sub[df2_bounding]
                        
                        if df2_bounding == df1_bounding:
                            if check_row_order: 
                                if check_if_order_maintaned(df2_fact, df2_facts[df2_fact_index-1], fact_map):
                                    last_index_match = merged_index.index(df2_fact) + 1
                                    df2_match = True
                            else:
                                if df2_fact == TotalRevenue or  merged_index.index(df2_fact) == 0:
                                    last_index_match = merged_index.index(df2_fact) + 1
                                    df2_match = True
                case _: # default
                    # TODO fix if common name and maintanined order
                    df2_fact_new = df2_fact
                    while df2_fact_new in merged_index:
                        df2_fact_new += "_new"
                    fact_map[df2_fact] = df2_fact_new
                    merged_index.insert(last_index_match, df2_fact_new)
                    last_index_match += 1
            if df2_match:
                break
    # Create the merged DataFrame
    merged_columns = sorted(set(df1.columns).union(df2.columns), reverse=True)
    merged_df = pd.DataFrame(index=merged_index, columns=merged_columns).fillna(0)
    # Fill the merged DataFrame with data from df1
    # print(merged_df)
    for fact in df1.index:
        merged_df.loc[fact, df1.columns] = df1.loc[fact]
    # Fill the merged DataFrame with data from df2
    # print(merged_df)
    for fact in df2.index:
        mapped_fact = fact_map.get(fact, fact)
        for column in df2.columns:
            if column not in df1.columns:
                merged_df.loc[mapped_fact, column] = df2.loc[fact, column]
    # print(merged_df)
    # Remove rows with only zero values
    merged_df = merged_df.loc[~(merged_df == 0).all(axis=1)]
    return merged_df

def merge_statements2(df1, df2):
    # TODO: companies change location of reported items, like from opearting income expesne to EBT expense.
    merged_facts = df1.index.tolist()
    df1_facts = df1.index.tolist()
    df2_facts = df2.index.tolist()
    last_index_match = 0
    for df2_index in range(len(df2_facts)):
        df2_fact = df2_facts[df2_index]
        if df2_fact in df1_facts:
            df1_bounding = find_bounding_fact(df2_fact, df1_facts)
            df2_bounding = find_bounding_fact(df2_fact, df2_facts)
            print(df1_bounding, df2_bounding)
            if df2_bounding == df1_bounding: # some variable can move location
                last_index_match =  merged_facts.index(df2_fact) +1
                continue
            else:
                df2_fact_new = df2_fact
                while df2_fact_new in df1_facts:
                    df2_fact_new += "_new"
                df2_facts[df2_index] = df2_fact_new
                index_map = {df2_fact: df2_fact_new}
                df2.rename(index=index_map, inplace=True)
                merged_facts.insert(last_index_match, df2_fact_new)
                last_index_match += 1
                continue
        merged_facts.insert(last_index_match, df2_fact)
        last_index_match += 1
    # # Combine columns from both DataFrames
    combined_columns = list(set(df1.columns) | set(df2.columns))
    # Sort the combined columns
    ordered_columns = sorted(combined_columns, reverse=True)
    merged_df = pd.DataFrame(index=merged_facts, columns=ordered_columns, dtype=float)
    merged_df = merged_df.fillna(0)
    
    for df1_fact in df1_facts:
        for column in df1.columns:
            merged_df.loc[df1_fact, column] = df1.loc[df1_fact, column]
    for df2_fact in df2_facts:
        data_fact_added = False
        df1_match = check_if_index_value_in_df(df1, df2, df2_fact)
        print(df1_match)
        # df2_fact_matches = find_matching_indices(df2, df2_fact, columns)
        if df1_match:
            df1_bounding = find_bounding_fact(df1_match, df1_facts)
            df2_bounding = find_bounding_fact(df2_fact, df2_facts)
            if df2_bounding == df1_bounding: # some variable can move location
                last_index_match =  merged_facts.index(df1_match) + 1
                for column in df2.columns:
                    if column not in df1.columns:
                        merged_df.loc[df1_match, column] = df2.loc[df2_fact, column]
                        data_fact_added = True
            else:
                df2_fact_new = df2_fact
                if df2_fact not in no_repetation:
                    while df2_fact_new in merged_df.index.tolist():
                        df2_fact_new += "_new"
                df2_index = df2_facts.index(df2_fact)
                df2_facts[df2_index] = df2_fact_new
                index_map = {df2_fact: df2_fact_new}
                df2.rename(index=index_map, inplace=True)
                merged_facts.insert(last_index_match, df2_fact_new)
                merged_df = merged_df.reindex(index=merged_facts, fill_value=0)
                last_index_match += 1
                for column in df2.columns:
                    if column not in df1.columns:
                        merged_df.loc[df1_match, column] = df2.loc[df2_fact_new, column]
                data_fact_added = True
        if not data_fact_added:
            df2_fact_new = df2_fact
            if df2_fact not in no_repetation:
                while df2_fact_new in merged_df.index.tolist():
                    df2_fact_new += "_new"
                merged_facts.insert(last_index_match, df2_fact_new)
                merged_df = merged_df.reindex(index=merged_facts, fill_value=0)
                last_index_match += 1
            else:
                last_index_match =  merged_facts.index(df2_fact) + 1
            for column in df2.columns:
                if df2.loc[df2_fact, column] != 0 and column not in df1.columns:
                    merged_df.loc[df2_fact_new, column] =  df2.loc[df2_fact, column]
    merged_df = merged_df.loc[~(merged_df == 0).all(axis=1)]
    return merged_df


#income_statement
#balance_sheet
#cash_flow_statement
cik = "0000094845"
ticker = "SPB"
statement_types = ["balance_sheet"]
# statement_types_maps = [income_statment_map, balance_sheet_map]
one_company = True
quarterly = False


accn = get_filtered_filings(
    ticker, ten_k=(not quarterly), just_accession_numbers=False, headers=headers
)

# combined_statment = pd.DataFrame()
check_if_statement_exist = False
combined_statments = []
is_base_statement = False
print(accn)
num_files = len(accn["accessionNumber"])

for indx, statement_type in enumerate(statement_types):
    combined_statment = None
    file_path = f'../finanacial_statements/{ticker}_{statement_type}_custom.csv'
    if check_if_statement_exist and os.path.exists(file_path):
        financial_statement = pd.read_csv(f"{file_path}", index_col=0)
        # financial_statement = calc_yoy_growth(financial_statement)
        combined_statments.append(financial_statement)
        continue
    first = True
    for i in range(0, num_files):
        if i == 5:
            pass 
        acc_num_unfiltered = accn["accessionNumber"].iloc[i]
        acc_num_filtered = accn["accessionNumber"].iloc[i].replace("-", "")
        # statement, rows_that_are_sum, rows_text, cal_facts, sections_dict
        financial_statement_struct = process_one_statement(ticker, acc_num_filtered, statement_type, acc_num_unfiltered, quarterly=quarterly)
        if financial_statement_struct is None:
            continue
        # print(rows_text)
        # print(cal_facts)
        if statement_type == "income_statement":
            fs = IncomeStatement(statement, combined_statment, financial_statement_struct.rows_that_are_sum, financial_statement_struct.rows_text, financial_statement_struct.cal_facts)
        else:
            fs = BalanceSheet(financial_statement_struct, combined_statment)
        # statement = process_all_statements_facts(ticker, acc_num)
        print(f"this is the {i}")        
        print(fs)
        if fs is None:
                continue
        if statement_type == "income_statement":
            fs.map_income3()
            statement = fs.income_statement.df
        else:
            fs.map_balance()
            statement = fs.balance_sheet.df
        print(statement)
        # statement = map_data(statement,  map= statement_types_maps[indx]) #  map= balance_sheet_map income_statment_map
        # new_statement = rename_statement(statement, label_dict)
        if first:
            # x=process_one_statement(ticker, acc_num, statement_type)
            # print(x)
            first = False
            combined_statment = statement
            is_base_statement = True
        else:
            
            if statement is None:
                continue
            # print("=======pre merge=====")
            # print(combined_statment)
            # print(statement)
            combined_statment = merge_statements(combined_statment, statement)
            print(combined_statment)
            try:
                combined_statment.to_csv(f"{file_path}", index=True)
            except AttributeError:
                continue
            # combined_statment = combine_dictionaries(combined_statment, statement)
    # combined_statment = calc_yoy_growth(combined_statment)
    print(combined_statment)
    combined_statments.append(combined_statment)
    try:
        combined_statment.to_csv(f"{file_path}", index=True)
    except AttributeError:
        continue
    # with open(f"{ticker}_{acc_num}.txt", "wb") as file:
    #     file.write()
print("++=======")
# try:
#     test = get_roic(combined_statments[0], combined_statments[1])
#     print(test)
#     print("++=======")
# except (AttributeError, KeyError) as e:
#     continue

# TODO: 10-q are filled 3 times a year, for the missing quarter, it will be the 10-k statement - (the sum of the other 3 quarters statement)
