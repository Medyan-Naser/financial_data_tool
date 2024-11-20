import pandas as pd
from itertools import combinations, product

def rearrange_facts(df):
    print(df)
    print("===")
    # Identify rows with duplicates (rows that contain ":")
    duplicated_rows = df[df.index.str.contains(":")]
    print(duplicated_rows)
    # Extract the base facts (main facts) without the colon part
    # base_facts = duplicated_rows.index.str.split(":").str[-1].str.rsplit("_", 1).str[0]
    base_facts = duplicated_rows.index.str.split(":").str[-1].str.rsplit("_", 1).str[0]
    print(base_facts)
    # Create an empty DataFrame to store the rearranged rows
    rearranged_df = pd.DataFrame(columns=df.columns)
    for base_fact in base_facts.unique():
        # Find the index of the main fact in the original DataFrame
        if base_fact in df.index:
            main_fact_index = df.index.get_loc(base_fact)
            # Identify the duplicate rows that correspond to the current main fact
            duplicates_to_insert = duplicated_rows[duplicated_rows.index.str.endswith(base_fact) | duplicated_rows.index.str.contains(f"{base_fact}_")]
            # Sum the values of the duplicate rows
            sum_of_duplicates = duplicates_to_insert.sum()
            # Get the values of the main fact
            main_fact_values = df.loc[base_fact]
            # Check if the sum of duplicates equals the main fact values
            if sum_of_duplicates.equals(main_fact_values):
                # Insert the duplicate rows above the main fact
                rearranged_df = pd.concat([rearranged_df, df.iloc[:main_fact_index]])
                rearranged_df = pd.concat([rearranged_df, duplicates_to_insert])
                rearranged_df = pd.concat([rearranged_df, df.iloc[[main_fact_index]]])
                # Drop the duplicate rows from the original DataFrame
                df = df.drop(duplicates_to_insert.index)
                # Update the remaining part of the DataFrame
                df = df.iloc[main_fact_index+1:]
    # Append any remaining rows in the DataFrame
    rearranged_df = pd.concat([rearranged_df, df])

    print(rearranged_df)
    print("==")
    return rearranged_df

def rearrange_facts2(df):
    # Identify rows with duplicates (rows that contain ":")
    duplicated_rows = df[df.index.str.contains(":")]
    # Extract the base facts (main facts) without the colon part
    base_facts = duplicated_rows.index.str.split(":").str[-1]
    # Create an empty DataFrame to store the rearranged rows
    rearranged_df = pd.DataFrame(columns=df.columns)
    for base_fact in base_facts.unique():
        # Find the index of the main fact in the original DataFrame
        if base_fact in df.index:
            main_fact_index = df.index.get_loc(base_fact)
            # Insert the duplicate rows above the main fact
            duplicates_to_insert = duplicated_rows[duplicated_rows.index.str.endswith(base_fact)]
            # Append rows before the main fact
            rearranged_df = pd.concat([rearranged_df, df.iloc[:main_fact_index]])
            # Append the duplicate rows
            rearranged_df = pd.concat([rearranged_df, duplicates_to_insert])
            # Append the main fact
            rearranged_df = pd.concat([rearranged_df, df.iloc[[main_fact_index]]])
            # Drop the duplicate rows from the original DataFrame
            df = df.drop(duplicates_to_insert.index)
            # Update the remaining part of the DataFrame
            df = df.iloc[main_fact_index+1:]
    # Append any remaining rows in the DataFrame
    rearranged_df = pd.concat([rearranged_df, df])

    return rearranged_df

# Example DataFrame
data = {
    '2023-12-31': [5710100000, 1751600000, 3958500000, 1466500000, 671000000, 2137500000, 1821000000, 69300000, 1890300000, 162200000, 1728100000, 23500000, 1704600000, 4.79, 4.66, 356.10, 365.80, 1655500000, 4793900000, 1464100000, 916200000, 287500000],
    '2022-12-31': [4358400000, 1497200000, 2861200000, 1216300000, 595100000, 1811400000, 1049800000, 157200000, 1207000000, 140200000, 1066800000, 6200000, 1060600000, 3.02, 2.94, 351.10, 361.00, 1073100000, 3634600000, 1230300000, 723800000, 266900000],
    '2021-12-31': [4478500000, 1368300000, 3110200000, 1178400000, 557300000, 1735700000, 1374500000, 127700000, 1502200000, 120400000, 1381800000, 2500000, 1379300000, 3.98, 3.85, 346.20, 358.40, 1405000000, 3754300000, 1119100000, 724200000, 249200000],
}

index = [
    'us-gaap_RevenueFromContractWithCustomerExcludingAssessedTax', 'us-gaap_CostOfGoodsAndServicesSold', 
    'us-gaap_GrossProfit', 'us-gaap_SellingGeneralAndAdministrativeExpense', 
    'us-gaap_ResearchAndDevelopmentExpense', 'us-gaap_OperatingExpenses', 
    'us-gaap_OperatingIncomeLoss', 'us-gaap_NonoperatingIncomeExpense', 
    'us-gaap_IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments', 
    'us-gaap_IncomeTaxExpenseBenefit', 'us-gaap_ProfitLoss', 
    'us-gaap_NetIncomeLossAttributableToNoncontrollingInterest', 'us-gaap_NetIncomeLoss', 
    'us-gaap_EarningsPerShareBasic', 'us-gaap_EarningsPerShareDiluted', 
    'us-gaap_WeightedAverageNumberOfSharesOutstandingBasic', 
    'us-gaap_WeightedAverageNumberOfDilutedSharesOutstanding', 
    'us-gaap_ComprehensiveIncomeNetOfTax', 
    'Joint venture:Ope:us-gaap_RevenueFromContractWithCustomerExcludingAssessedTax', 
    'Cost of revenue::us-gaap_CostOfGoodsAndServicesSold', 
    'Service:Revenue::us-gaap_RevenueFromContractWithCustomerExcludingAssessedTax_2', 
    'Cost of revenue::us-gaap_CostOfGoodsAndServicesSold_2'
]

df = pd.DataFrame(data, index=index)

# Rearrange the DataFrame
rearranged_df = rearrange_facts(df)
print(rearranged_df)


def find_combinations_with_logging(df, special_facts, preferred_operation):
    def check_if_master_in_list():
        master = df.variable_in_list(df.df.index[pos])
        # if master is not None and master in df.df.index[start_pos:end_pos]:
        #     continue
    def is_combination_valid(base_fact, comb, signs, target):
        base_total = df.loc[base_fact]
        total = base_total + sum(sign * df.loc[fact] for sign, fact in zip(signs, comb))
        return (total == target).all()

    def adjust_signs(base_fact, comb, signs):
        df.loc[base_fact] *= 1  # Base fact keeps its original sign
        for fact, sign in zip(comb, signs):
            df.loc[fact] *= sign

    result = {}

    for special_fact in special_facts:
        target = df.loc[special_fact]
        special_fact_index = df.index.get_loc(special_fact)
        possible_facts = df.index[:special_fact_index]

        found_combination = False

        # Generate initial signs based on the preferred operation
        initial_signs = [1 if preferred_operation == 'add' else -1] * len(possible_facts)

        # Try combinations starting with the closest rows first
        for base_index in range(special_fact_index-1, -1, -1):
            base_fact = possible_facts[base_index]
            print(base_index)
            # print(possible_facts[:base_index])
            print(possible_facts[base_index+1:special_fact_index])
            remaining_facts = possible_facts[base_index+1:special_fact_index]

            if len(remaining_facts) == 0:
                continue

            # for r in range(1, len(remaining_facts) + 1):
                # for comb in combinations(remaining_facts[::-1], r):  # Reverse to start with closest rows
                    # First try with the initial signs based on the preferred operation
            for comb in combinations(remaining_facts, len(remaining_facts)):
                print(f"Trying combination with base: {base_fact} and additional: {comb} with signs: {initial_signs[:len(comb)]}")
                if is_combination_valid(base_fact, comb, initial_signs[:len(comb)], target):
                    print(f"Match found with initial signs for {base_fact} and {comb}")
                    adjust_signs(base_fact, comb, initial_signs[:len(comb)])
                    result[special_fact] = [base_fact] + list(comb)
                    found_combination = True
                    break

                # If the preferred operation did not work, try all possible sign combinations
                for signs in product([1, -1], repeat=len(comb)):
                    print(f"Trying combination with base: {base_fact} and additional: {comb} with signs: {signs}")
                    if is_combination_valid(base_fact, comb, signs, target):
                        print(f"Match found with signs {signs} for {base_fact} and {comb}")
                        adjust_signs(base_fact, comb, signs)
                        result[special_fact] = [base_fact] + list(comb)
                        found_combination = True
                        break
                if found_combination:
                    break
            if found_combination:
                break
            # if found_combination:
            #     break
    
    return result

def check_all_positive_up_to_index(df, str_index):
    try:
        # Get the position of the given string index
        position = df.index.get_loc(str_index)

        # Get the subset of the DataFrame from the start to the given index
        subset_df = df.iloc[:position+1]

        # Check if all values in the subset are positive
        all_values_positive = (subset_df >= 0).all().all()

        return all_values_positive
    except KeyError:
        return f"Index '{str_index}' not found in DataFrame."

# Example usage
data = {
    '2017-12-31': [-2305000, 979000, 373100, 115400],
    '2016-12-31': [2194600, -0, 398100, -443800],
    '2015-12-31': [2484500, 1027700, 443800, -115400]
}

index = ['Total revenue', 'us-gaap_LaborAndRelatedExpense', 'us-gaap_SellingGeneralAndAdministrativeExpense', 'amg_AmortizationandImpairmentsofIntangibleAssets']

df = pd.DataFrame(data, index=index)
print(df)
result = check_all_positive_up_to_index(df, 'us-gaap_SellingGeneralAndAdministrativeExpense')
print(result)

# Example usage
data = {
    '2023-01-01': [93580000, 33038000, 60542000, 12046000, 15713000, 4611000, 10011000, 42381000, 18161000, 346000, 18507000, 6314000, 12193000, 1.49, 1.48, 8177, 8254, 0.00],
    '2022-01-01': [86833000, 27078000, 59755000, 11381000, 15811000, 4677000, 127000, 31996000, 27759000, 61000, 27820000, 5746000, 22074000, 2.66, 2.63, 8299, 8399, 0.00],
    '2021-01-01': [77849000, 20385000, 57464000, 10411000, 15276000, 5013000, 0, 30700000, 26764000, 288000, 27052000, 5189000, 21863000, 2.61, 2.58, 8375, 8470, 0.00]
}
index = [
    'Total revenue', 'COGS', 'Gross profit', 'R&D', 'SG&A',
    'us-gaap_GeneralAndAdministrativeExpense',
    'msft_ImpairmentIntegrationAndRestructuringExpenses',
    'Total operating expense', 'Operating income',
    'us-gaap_NonoperatingIncomeExpense',
    'us-gaap_IncomeLossFromContinuingOperationsBeforeIncomeTaxes',
    'us-gaap_IncomeTaxExpenseBenefit', 'us-gaap_NetIncomeLoss',
    'us-gaap_EarningsPerShareBasic', 'us-gaap_EarningsPerShareDiluted',
    'us-gaap_WeightedAverageNumberOfSharesOutstandingBasic',
    'us-gaap_WeightedAverageNumberOfDilutedSharesOutstanding',
    'us-gaap_CommonStockDividendsPerShareDeclared'
]

df = pd.DataFrame(data, index=index)
special_facts = ['Operating income']
preferred_operation = 'subtract' # 'add' or 'subtract'

result = find_combinations_with_logging(df, special_facts, preferred_operation)
print(result)
print("\nUpdated DataFrame:")
print(df)

