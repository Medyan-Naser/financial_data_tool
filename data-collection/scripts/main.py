from Company import Company
from Filling import Filling

from merging_statements import *

c = Company(ticker="AAPL")

print(c.ten_k_fillings.iloc[0])
f = Filling(ticker="AAPL", cik=c.cik, acc_num_unfiltered=c.ten_k_fillings.iloc[0], company_facts=c.company_facts)
# print(f.taxonomy)
print(f.company_facts_DF)
t = f.process_one_statement("income_statement")

# # df, labels_dict, taxonomy = f.get_company_facts_DF()

# print(t.df)
# print(t.sections_dict)
print("#######################")
merged_df = t.df
for i in range(1, c.ten_k_fillings.size +1):
    f = Filling(ticker="AAPL", cik=c.cik, acc_num_unfiltered=c.ten_k_fillings.iloc[i], company_facts=c.company_facts)
    t = f.process_one_statement("income_statement")
    merged_df = merge_dfs(merged_df, t.df)

    print(merged_df)