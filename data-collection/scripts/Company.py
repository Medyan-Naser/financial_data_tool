import os
import pandas as pd
import numpy as np  # make sure to add
import requests
from bs4 import BeautifulSoup
import logging  # make sure to add
import calendar  # make sure to add
from headers import headers  # change to your own headers file or add variable in code
from maps import *


# constants
IN_DOLLARS = 1/1000
IN_THOUSANDS = 1
IN_MILLIONS = 1000

class Company:
    
    def __init__(self) -> None:
        self.headers = headers
        self.ticker = ticker
        self.cik - CIK

    def get_cik_matching_tickers(self):
        ticker = self.ticker.upper().replace(".", "-")
        ticker_json = requests.get(
            "https://www.sec.gov/files/company_tickers.json", headers=self.headers
        ).json()

        for company in ticker_json.values():
            if company["ticker"] == ticker:
                cik = str(company["cik_str"]).zfill(10)
                return cik
        raise ValueError(f"Ticker {ticker} not found in SEC database")
    
    def get_submission_data_for_ticker(self, only_filings_df=False):
        """
        Get the data in json form for a given ticker. For example: 'cik', 'entityType', 'sic', 'sicDescription', 'insiderTransactionForOwnerExists', 'insiderTransactionForIssuerExists', 'name', 'tickers', 'exchanges', 'ein', 'description', 'website', 'investorWebsite', 'category', 'fiscalYearEnd', 'stateOfIncorporation', 'stateOfIncorporationDescription', 'addresses', 'phone', 'flags', 'formerNames', 'filings'
        Args:
            ticker (str): The ticker symbol of the company.
        Returns:
            json: The submissions for the company.
        """
        cik = self.get_cik_matching_tickers()
        headers = self.headers
        url = f"https://data.sec.gov/submissions/CIK{cik}.json"
        print(url)
        company_json = requests.get(url, headers=headers).json()
        for old_file in company_json['filings']['files']:
            old_submission_url = "https://data.sec.gov/submissions/" + old_file['name']
            old_sub = requests.get(old_submission_url, headers=headers).json()
            # download_json("https://data.sec.gov/submissions/" + old_file['name'])
            for column in old_sub:
                company_json['filings']['recent'][column] += old_sub[column]
        if only_filings_df:
            return pd.DataFrame(company_json["filings"]["recent"])
        else:
            return company_json
        
    def get_filtered_filings(self, ten_k=True, just_accession_numbers=False):
        """
        Retrieves either 10-K or 10-Q filings for a given ticker and optionally returns just accession numbers.
        Args:
            ticker (str): Stock ticker symbol.
            ten_k (bool): If True, fetches 10-K filings; otherwise, fetches 10-Q filings.
            just_accession_numbers (bool): If True, returns only accession numbers; otherwise, returns full data.
            headers (dict): Headers for HTTP request.
        Returns:
            DataFrame or Series: DataFrame of filings or Series of accession numbers.
        """
        # Fetch submission data for the given ticker
        company_filings_df = self.get_submission_data_for_ticker(only_filings_df=True)
        # Filter for 10-K or 10-Q forms
        df = company_filings_df[(company_filings_df["form"] == ("10-K" if ten_k else "10-Q")) | (company_filings_df["form"] == ("20-F" if ten_k else "10-Q"))]
        # Return accession numbers if specified
        if just_accession_numbers:
            df = df.set_index("reportDate")
            accession_df = df["accessionNumber"]
            return accession_df
        else:
            return df
        
    def get_facts(self):
        """
        Retrieves company facts for a given ticker.
        Args:
            ticker (str): Stock ticker symbol.
            headers (dict): Headers for HTTP request.
        Returns:
            dict: Company facts in JSON format.
        """
        # Get CIK number matching the ticker
        cik = self.get_cik_matching_ticker()
        # Construct URL for company facts
        url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
        # Fetch and return company facts
        company_facts = requests.get(url, headers=self.headers).json()
        # company_facts = requests.get(url, headers=headers)
        return company_facts
    
    def facts_DF(self):
        """
        Converts company facts into a DataFrame.
        Args:
            ticker (str): Stock ticker symbol.
            headers (dict): Headers for HTTP request.
        Returns:
            tuple: DataFrame of facts and a dictionary of labels.
        """
        # Retrieve facts data
        facts = self.get_facts()
        us_gaap_data = facts["facts"]["us-gaap"]
        df_data = []
        # Process each fact and its details
        for fact, details in us_gaap_data.items():
            for unit in details["units"]:
                for item in details["units"][unit]:
                    row = item.copy()
                    row["fact"] = fact
                    df_data.append(row)
        df = pd.DataFrame(df_data)
        # Convert 'end' and 'start' to datetime
        df["end"] = pd.to_datetime(df["end"])
        df["start"] = pd.to_datetime(df["start"])
        # Drop duplicates and set index
        df = df.drop_duplicates(subset=["fact", "end", "val"])
        # df.set_index("end", inplace=True)
        # df.reset_index(inplace=True)
        # Create a dictionary of labels for facts
        labels_dict = {fact: details["label"] for fact, details in us_gaap_data.items()}
        return df, labels_dict