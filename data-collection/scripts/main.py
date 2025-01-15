from Company import Company
from Filling import Filling

c = Company(ticker="AAPL")

print(c.ten_k_fillings.iloc[0])
f = Filling(ticker="AAPL", cik=c.cik, acc_num_unfiltered=c.ten_k_fillings.iloc[0], company_facts=c.company_facts)
# print(f.taxonomy)
print(f.company_facts_DF)
t = f.process_one_statement("income_statement")

# df, labels_dict, taxonomy = f.get_company_facts_DF()

print(t.df)
print(t.sections_dict)
print("#######################")

# print(labels_dict)
# print(df)
# print(c.company_all_filings)