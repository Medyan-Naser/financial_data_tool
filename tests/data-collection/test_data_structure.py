data_structure = {
    'income_statement': [
        ['us-gaap_Revenues', 'Total revenues'],
        ['us-gaap_CostOfRevenue', 'Total costs and expenses']
    ],
    'balance_sheet': [
        ['us-gaap_GainLossOnDispositionOfAssets', 'Gain on dispositions, net'],
        ['us-gaap_OtherNoncashIncomeExpense', 'Other charges and credits, net']
    ]
}

def find_index_of_revenues(data):
    for sublist in data:
        if 'us-gaap_Revenues' in sublist:
            print(sublist)
            return data.index(sublist)
    return None

# Find the index of 'us-gaap_Revenues' in the income_statement list
index = find_index_of_revenues(data_structure['income_statement'])
#  index = next((i for i, sublist in enumerate(data_structure['income_statement']) if 'us-gaap_Revenues' in sublist), None)

print("Index of 'us-gaap_Revenues':", index)
# Find the index of ['us-gaap_Revenues', 'Total revenues'] in the income_statement list
# index = data_structure['income_statement'].index(['us-gaap_Revenues', 'Total revenues'])
index = data_structure['income_statement'].index('us-gaap_Revenues')
print("Index of ['us-gaap_Revenues', 'Total revenues']:", index)

