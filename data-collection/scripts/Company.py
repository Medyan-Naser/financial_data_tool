from headers import *
from constants import *
from healpers import *

import requests
import pandas as pd


## Fucntions not copied 
# facts_DF
# annual_facts
# quarterly_facts


class Company():

    def __init__(self, cik=None, ticker=None, ) -> None:
        if not ticker and not cik:
            raise ValueError(f"Must include the ticker or the CIK")
        if not ticker:
            self.ticker = ticker
        if not cik:
            self.cik = self.cik_matching_ticker()
        else:
            self.cik = cik

        self.company_filings = None
        self.company_all_filings = None
        self.ten_k_fillings = None
        self.ten_q_fillings = None
        self.company_facts = None

    def cik_matching_ticker(self):
        # return ticker
        ticker = self.ticker.upper().replace(".", "-")
        ticker_json = requests.get(
            "https://www.sec.gov/files/company_tickers.json", headers=headers
        ).json()

        for company in ticker_json.values():
            if company["ticker"] == ticker:
                cik = str(company["cik_str"]).zfill(10)
                return cik
        raise ValueError(f"Ticker {ticker} not found in SEC database")

    def get_submission_data_for_ticker(self):
        """
        Get the data in json form for a given ticker. For example: 'cik', 'entityType', 'sic', 'sicDescription', 'insiderTransactionForOwnerExists', 'insiderTransactionForIssuerExists', 'name', 'tickers', 'exchanges', 'ein', 'description', 'website', 'investorWebsite', 'category', 'fiscalYearEnd', 'stateOfIncorporation', 'stateOfIncorporationDescription', 'addresses', 'phone', 'flags', 'formerNames', 'filings'
        Returns:
            json: The submissions for the company.
        """
        cik = self.cik
        headers = headers
        url = f"https://data.sec.gov/submissions/CIK{cik}.json"
        print(url)
        company_json = requests.get(url, headers=headers).json()
        for old_file in company_json['filings']['files']:
            old_submission_url = "https://data.sec.gov/submissions/" + old_file['name']
            print(old_submission_url)
            old_sub = requests.get(old_submission_url, headers=headers).json()
            for column in old_sub:
                company_json['filings']['recent'][column] += old_sub[column]
       
        self.company_filings = pd.DataFrame(company_json["filings"]["recent"])
        self.company_all_filings = company_json

    def get_filtered_filings(self, just_accession_numbers=True):
        """
        Retrieves either 10-K or 10-Q filings for a given ticker and optionally returns just accession numbers.
        Args:
            just_accession_numbers (bool): If True, returns only accession numbers; otherwise, returns full data.
        Returns:
            DataFrame or Series: DataFrame of filings or Series of accession numbers.
        """

        # Filter for 10-K or 10-Q forms
        ten_k = self.company_filings[(self.company_filings["form"] == "10-K") | (self.company_filings["form"] == "20-F") | (self.company_filings["form"] == "40-F")]
        ten_q = self.company_filings[(self.company_filings["form"] == "10-Q")]

        ten_k = ten_k.set_index("reportDate")
        self.ten_k_fillings = ten_k["accessionNumber"]

        ten_q = ten_q.set_index("reportDate")
        self.ten_q_fillings = ten_q["accessionNumber"]
        # Return accession numbers if specified
        # if just_accession_numbers:
        #     df = df.set_index("reportDate")
        #     accession_df = df["accessionNumber"]
        #     return accession_df
        # else:
        #     return df


    def get_facts(self):
        """
        Retrieves company facts for a given ticker.
        Returns:
            dict: Company facts in JSON format.
        """
        # Construct URL for company facts
        url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{self.cik}.json"
        print("facts url :")
        print(url)
        # Fetch and return company facts
        self.company_facts = requests.get(url, headers=headers).json()
