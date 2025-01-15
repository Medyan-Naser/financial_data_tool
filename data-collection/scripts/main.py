from Company import Company
from Filling import Filling

c = Company(ticker="AAPL")

print(c.ten_k_fillings.iloc[0])
f = Filling(ticker="AAPL", cik=c.cik, accession_number=c.ten_k_fillings.iloc[0], company_facts=c.company_facts)

# t = f.get_statement_soup("income_statement")

df, labels_dict, taxonomy = f.get_company_facts_DF()

print(taxonomy)

print("#######################")

# print(labels_dict)
print(df)
# print(c.company_all_filings)