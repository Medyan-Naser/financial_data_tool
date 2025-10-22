from Company import Company
from Filling import Filling
from FinancialStatement import *
from merging_statements import *

c = Company(ticker="AAPL")

print(c.ten_k_fillings.iloc[0])
f = Filling(ticker="AAPL", cik=c.cik, acc_num_unfiltered=c.ten_k_fillings.iloc[0], company_facts=c.company_facts)
# print(f.taxonomy)
print(f.company_facts_DF)
f.process_one_statement("income_statement")
f.income_statement.create_zeroed_df_from_map()
# # df, labels_dict, taxonomy = f.get_company_facts_DF()

print(f.income_statement.og_df)
print(f.income_statement.mapped_df)
f.income_statement.map_facts()
print(f.income_statement.mapped_df)

# print(t.sections_dict)
print("#######################")
merged_df = f.income_statement.og_df
# for i in range(1, c.ten_k_fillings.size +1):
#     f = Filling(ticker="AAPL", cik=c.cik, acc_num_unfiltered=c.ten_k_fillings.iloc[i], company_facts=c.company_facts)
#     f.process_one_statement("income_statement")
#     merged_df = merge_dfs(merged_df, f.income_statement.og_df)


#     print(merged_df)