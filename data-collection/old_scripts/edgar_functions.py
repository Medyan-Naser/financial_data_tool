import os
import pandas as pd
import numpy as np  # make sure to add
import requests
from bs4 import BeautifulSoup
import logging  # make sure to add
import calendar  # make sure to add
from headers import headers  # change to your own headers file or add variable in code
import math
import sys
import random
import re
from collections import Counter # for currency check
from cal_xml import fetch_file_content, parse_calculation_arcs
from helpers import DataFrameWithStringListTracking

# TODO for the following keep number as reported: PerShare, PerBasicShare, PerDilutedShare


# constants for thousand def
# IN_DOLLARS = 1/1000
# IN_THOUSANDS = 1
# IN_MILLIONS = 1000

# constants for dollar def
IN_DOLLARS = 1
IN_THOUSANDS = 1000
IN_MILLIONS = 1000000

# taxonimy
GAAP = "us-gaap"
IFRS = "ifrs-full"

# currencies
USD = "USD"
USD_sign = "$"
EUR = "EUR"
EUR_sign = "€"
CNY = "CNY"
CNY_sign = "¥"
# India
INR = "INR"
INR_sign = "₨"

currency_keys = [USD, EUR, CNY, INR]
currency_map = {USD: USD_sign, EUR: EUR_sign, CNY: CNY_sign, INR: INR_sign}


# sections
FIRST_SECTION = "FIRST SECTION"

pd.options.display.float_format = (
    lambda x: "{:,.0f}".format(x) if int(x) == x else "{:,.2f}".format(x)
)

keep_value_unchanged = ['us-gaap_EarningsPerShareDiluted', 'us-gaap_EarningsPerShareBasic', 'us-gaap_WeightedAverageNumberOfSharesOutstandingBasic', 'us-gaap_WeightedAverageNumberOfDilutedSharesOutstanding']

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
        "Consolidated Statements of Financial Position",
    ],
    "income_statement": [
        "income statement",
        "income statements",
        "statement of earnings (loss)",
        "statement of income",
        "statement of comprehensive income",
        "statements of consolidated income",
        "statements of consolidated comprehensive income",
        "statements of operations",
        "consolidated statements of operations",
        "consolidated statement of operations",
        "consolidated statements of earnings",
        "consolidated statement of earnings",
        "consolidated statements of income",
        "consolidated statement of income",
        "combined and consolidated statement of income",
        "consolidated income statements",
        "consolidated income statement",
        "consolidated statement of comprehensive income",
        "condensed consolidated statements of earnings",
        "consolidated results of operations",
        "consolidated statements of income (loss)",
        "consolidated statements of income - southern",
        "consolidated statements of operations and comprehensive income",
        "consolidated statements of comprehensive income",
        "consolidated statements of operations and comprehensive loss",
        "CONSOLIDATED STATEMENTS OF OPERATIONS AND COMPREHENSIVE LOSS",
        "consolidated statements of comprehensive loss",
        "Consolidated Statements of Comprehensive (Loss) Income",
        "Consolidated and Combined Statements of Income",
        "Consolidated Statements of Net Earnings",
        "Consolidated Statements of Net Earnings (Loss)",
        "Consolidated and Combined Statements of (Loss) Income",
        # quaesinable
        "consolidated statements of profit",
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


def companies_matching_sik(sic, headers=headers):
    cik_url_base = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&SIC={sic}&owner=include&match=starts-with&start=0&count=400&hidefilings=0"
    cik_list = []
    session = requests.Session()
    html_file = session.get(cik_url_base, headers=headers)
    if html_file.status_code == 200:
        soup = BeautifulSoup(html_file.text, 'html.parser')
        table = soup.find('table')
        if table:
            rows = table.find_all('tr')
            for row in rows:
                columns = row.find_all('td')
                if len(columns) > 0 and columns[0].text.strip().isdigit():
                    cik = columns[0].text.strip()
                    cik_list.append(cik)
    return cik_list

def cik_matching_ticker(ticker, headers=headers):
    # return ticker
    ticker = ticker.upper().replace(".", "-")
    ticker_json = requests.get(
        "https://www.sec.gov/files/company_tickers.json", headers=headers
    ).json()

    for company in ticker_json.values():
        if company["ticker"] == ticker:
            cik = str(company["cik_str"]).zfill(10)
            return cik
    raise ValueError(f"Ticker {ticker} not found in SEC database")


def get_submission_data_for_ticker(ticker, headers=headers, only_filings_df=False):
    """
    Get the data in json form for a given ticker. For example: 'cik', 'entityType', 'sic', 'sicDescription', 'insiderTransactionForOwnerExists', 'insiderTransactionForIssuerExists', 'name', 'tickers', 'exchanges', 'ein', 'description', 'website', 'investorWebsite', 'category', 'fiscalYearEnd', 'stateOfIncorporation', 'stateOfIncorporationDescription', 'addresses', 'phone', 'flags', 'formerNames', 'filings'

    Args:
        ticker (str): The ticker symbol of the company.

    Returns:
        json: The submissions for the company.
    """
    cik = cik_matching_ticker(ticker)
    headers = headers
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    print(url)
    company_json = requests.get(url, headers=headers).json()
    for old_file in company_json['filings']['files']:
        old_submission_url = "https://data.sec.gov/submissions/" + old_file['name']
        print(old_submission_url)
        old_sub = requests.get(old_submission_url, headers=headers).json()
        # print(old_sub)
        # download_json("https://data.sec.gov/submissions/" + old_file['name'])
        for column in old_sub:
            company_json['filings']['recent'][column] += old_sub[column]
    if only_filings_df:
        print("=============")
        print(company_json['filings']['recent']['accessionNumber'])
        return pd.DataFrame(company_json["filings"]["recent"])
    else:
        return company_json


def get_filtered_filings(
    ticker, ten_k=True, just_accession_numbers=False, headers=None
):
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
    company_filings_df = get_submission_data_for_ticker(
        ticker, only_filings_df=True, headers=headers
    )
    # Filter for 10-K or 10-Q forms
    df = company_filings_df[(company_filings_df["form"] == ("10-K" if ten_k else "10-Q")) | (company_filings_df["form"] == ("20-F" if ten_k else "10-Q")) | (company_filings_df["form"] == ("40-F" if ten_k else "10-Q"))]
    # Return accession numbers if specified
    if just_accession_numbers:
        df = df.set_index("reportDate")
        accession_df = df["accessionNumber"]
        return accession_df
    else:
        return df


def get_facts(ticker, headers=None):
    """
    Retrieves company facts for a given ticker.

    Args:
        ticker (str): Stock ticker symbol.
        headers (dict): Headers for HTTP request.

    Returns:
        dict: Company facts in JSON format.
    """
    # Get CIK number matching the ticker
    cik = cik_matching_ticker(ticker)
    # Construct URL for company facts
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
    print("facts url :")
    print(url)
    # Fetch and return company facts
    company_facts = requests.get(url, headers=headers).json()
    # company_facts = requests.get(url, headers=headers)

    return company_facts


def facts_DF(ticker, headers=None):
    """
    Converts company facts into a DataFrame.

    Args:
        ticker (str): Stock ticker symbol.
        headers (dict): Headers for HTTP request.

    Returns:
        tuple: DataFrame of facts and a dictionary of labels.
    """
    # Retrieve facts data
    facts = get_facts(ticker, headers)
    taxonomy = GAAP
    try:
        us_gaap_data = facts["facts"][GAAP]
    except Exception as e:
        try:
            us_gaap_data = facts["facts"][IFRS]
            taxonomy = IFRS
        except Exception as e:
            return None, None, None
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
    # print(facts)
    # print("++++")
    # print(df)
    # print("++++")
    # print(labels_dict)
    # print("++++")
    # df.to_csv(f"facts_df", index=True)
    # import json
    # with open("facts.txt", "w") as file:
    #     # Write the string to the file
    #     json.dump(facts, file, indent=4)
    return df, labels_dict, taxonomy


def annual_facts(ticker, headers=None):
    """
    Fetches and processes annual (10-K) financial facts for a given ticker.

    Args:
        ticker (str): Stock ticker symbol.
        headers (dict): Headers for HTTP request.

    Returns:
        DataFrame: Transposed pivot table of annual financial facts.
    """
    # Get accession numbers for 10-K filings
    accession_nums = get_filtered_filings(
        ticker, ten_k=True, just_accession_numbers=True, headers=headers
    )
    # Extract and process facts data
    df, label_dict, taxonomy = facts_DF(ticker, headers)
    # Filter data for 10-K filings
    ten_k = df[df["accn"].isin(accession_nums)]
    ten_k = ten_k[ten_k.index.isin(accession_nums.index)]
    # Pivot and format the data
    pivot = ten_k.pivot_table(values="val", columns="fact", index="end")
    pivot.rename(columns=label_dict, inplace=True)
    return pivot.T


def quarterly_facts(ticker, headers=None):
    """
    Fetches and processes quarterly (10-Q) financial facts for a given ticker.

    Args:
        ticker (str): Stock ticker symbol.
        headers (dict): Headers for HTTP request.

    Returns:
        DataFrame: Transposed pivot table of quarterly financial facts.
    """
    # Get accession numbers for 10-Q filings
    accession_nums = get_filtered_filings(
        ticker, ten_k=False, just_accession_numbers=True, headers=headers
    )
    # Extract and process facts data
    df, label_dict, taxonomy = facts_DF(ticker, headers)
    # Filter data for 10-Q filings
    ten_q = df[df["accn"].isin(accession_nums)]
    ten_q = ten_q[ten_q.index.isin(accession_nums.index)].reset_index(drop=False)
    # Remove duplicate entries
    ten_q = ten_q.drop_duplicates(subset=["fact", "end"], keep="last")
    # Pivot and format the data
    pivot = ten_q.pivot_table(values="val", columns="fact", index="end")
    pivot.rename(columns=label_dict, inplace=True)
    return pivot.T


def save_dataframe_to_csv(dataframe, folder_name, ticker, statement_name, frequency):
    """
    Saves a given DataFrame to a CSV file in a specified directory.

    Args:
        dataframe (DataFrame): The DataFrame to be saved.
        folder_name (str): The folder name where the CSV file will be saved.
        ticker (str): Stock ticker symbol.
        statement_name (str): Name of the financial statement.
        frequency (str): Frequency of the financial data (e.g., annual, quarterly).

    Returns:
        None
    """
    # Create directory path
    directory_path = os.path.join(folder_name, ticker)
    os.makedirs(directory_path, exist_ok=True)
    # Construct file path and save DataFrame
    file_path = os.path.join(directory_path, f"{statement_name}_{frequency}.csv")
    dataframe.to_csv(file_path)


def _get_file_name(report):
    """
    Extracts the file name from an XML report tag.

    Args:
        report (Tag): BeautifulSoup tag representing the report.

    Returns:
        str: File name extracted from the tag.
    """
    html_file_name_tag = report.find("HtmlFileName")
    xml_file_name_tag = report.find("XmlFileName")
    # Return the appropriate file name
    if html_file_name_tag:
        return html_file_name_tag.text
    elif xml_file_name_tag:
        return xml_file_name_tag.text
    else:
        return ""


def _is_statement_file(short_name_tag, long_name_tag, file_name):
    """
    Determines if a given file is a financial statement file.

    Args:
        short_name_tag (Tag): BeautifulSoup tag for the short name.
        long_name_tag (Tag): BeautifulSoup tag for the long name.
        file_name (str): Name of the file.

    Returns:
        bool: True if it's a statement file, False otherwise.
    """
    return (
        short_name_tag is not None
        and long_name_tag is not None
        and file_name  # Ensure file_name is not an empty string
        # and "Statement" in long_name_tag.text # check if this is needed
    )


def get_statement_file_names_in_filing_summary(ticker, accession_number, headers=None):
    """
    Retrieves file names of financial statements from a filing summary.

    Args:
        ticker (str): Stock ticker symbol.
        accession_number (str): SEC filing accession number.
        headers (dict): Headers for HTTP request.

    Returns:
        dict: Dictionary mapping statement types to their file names.
    """
    try:
        # Set up request session and get filing summary
        session = requests.Session()
        cik = cik_matching_ticker(ticker)
        base_link = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_number}"
        filing_summary_link = f"{base_link}/FilingSummary.xml"
        filing_summary_response = session.get(
            filing_summary_link, headers=headers
        ).content.decode("utf-8")

        # Parse the filing summary
        filing_summary_soup = BeautifulSoup(filing_summary_response, "lxml-xml")
        statement_file_names_dict = {}
        # Extract file names for statements
        for report in filing_summary_soup.find_all("Report"):
            file_name = _get_file_name(report)
            short_name, long_name = report.find("ShortName"), report.find("LongName")
            if _is_statement_file(short_name, long_name, file_name):
                statement_file_names_dict[short_name.text.lower()] = file_name
        return statement_file_names_dict
    except requests.RequestException as e:
        print(f"An error occurred: {e}")
        return {}


def get_statement_soup(
    ticker, accession_number, statement_name, headers, statement_keys_map
):
    """
    Retrieves the BeautifulSoup object for a specific financial statement.

    Args:
        ticker (str): Stock ticker symbol.
        accession_number (str): SEC filing accession number.
        statement_name (str): has to be 'balance_sheet', 'income_statement', 'cash_flow_statement'
        headers (dict): Headers for HTTP request.
        statement_keys_map (dict): Mapping of statement names to keys.

    Returns:
        BeautifulSoup: Parsed HTML/XML content of the financial statement.

    Raises:
        ValueError: If the statement file name is not found or if there is an error fetching the statement.
    """
    session = requests.Session()
    cik = cik_matching_ticker(ticker)
    base_link = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_number}"
    print(base_link)
    # Get statement file names
    statement_file_name_dict = get_statement_file_names_in_filing_summary(
        ticker, accession_number, headers
    )
    statement_link = None
    # Find the specific statement link
    # print(statement_file_name_dict)
    for possible_key in statement_keys_map.get(statement_name.lower(), []):
        file_name = statement_file_name_dict.get(possible_key.lower())
        file_name_loss = statement_file_name_dict.get((possible_key.lower() + " (loss)"))
        # print(possible_key.lower())
        if file_name:
            statement_link = f"{base_link}/{file_name}"
            print(statement_link)
            break
        elif file_name_loss:
            statement_link = f"{base_link}/{file_name_loss}"
            print(statement_link)
            break

    if not statement_link:
        #ShortNames = statement_file_name_dict.find_all("ShortName")
        # TODO: check again if one of the maps is in one of files R1, R2,...

        statement_link_found = False

        for possible_key in statement_keys_map.get(statement_name.lower(), []):
            for short in statement_file_name_dict:
                # check if the R{num} is less than R10
                if possible_key in short.lower():
                    print(short.lower(), int(re.search(r'R(\d+)', statement_file_name_dict.get(short.lower())).group(1)))
                    if int(re.search(r'R(\d+)', statement_file_name_dict.get(short.lower())).group(1)) < 10:
                        file_name = statement_file_name_dict.get(short.lower())
                        statement_link = f"{base_link}/{file_name}"
                        print(statement_link)
                        statement_link_found = True
                        break
            if statement_link_found:
                break

        # if statement_file_name_dict.get(possible_key.lower()) in file_name:
        #     statement_link = f"{base_link}/{file_name}"
        #     print(statement_link)
        #     break
        # else:
        if not statement_link:
            raise ValueError(f"Could not find statement file name for {statement_name}")
    # Fetch the statement
    try:
        statement_response = session.get(statement_link, headers=headers)
        statement_response.raise_for_status()  # Check for a successful request
        # Parse and return the content
        if statement_link.endswith(".xml"):
            return BeautifulSoup(
                statement_response.content, "lxml-xml", from_encoding="utf-8"
            )
        else:
            return BeautifulSoup(statement_response.content, "lxml")
    except requests.RequestException as e:
        raise ValueError(f"Error fetching the statement: {e}")
    
def get_cal_xml_filename(
    ticker, accession_number, headers
):
    """
    Retrieves the BeautifulSoup object for a specific financial statement.

    Args:
        ticker (str): Stock ticker symbol.
        accession_number (str): SEC filing accession number.
        headers (dict): Headers for HTTP request.

    Returns:
        BeautifulSoup: Parsed HTML/XML content of the financial statement.

    Raises:
        ValueError: If the statement file name is not found or if there is an error fetching the statement.
    """
    session = requests.Session()
    cik = cik_matching_ticker(ticker)
    base_link = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_number}"
    print(base_link)
    # Get statement file names
    statement_link = None
    # Fetch the statement
    try:
        statement_response = session.get(base_link, headers=headers)
        statement_response.raise_for_status()  # Check for a successful request
        # Parse the HTML content
        soup = BeautifulSoup(statement_response.content, 'html.parser')
        # Find all links in the page
        links = soup.find_all('a')
        # Iterate over links and find the one that ends with '_cal.xml'
        for link in links:
            href = link.get('href')
            if href and href.endswith('_cal.xml'):
                statement_link = base_link + '/' + href.split('/')[-1]
                break
        if not statement_link:
            raise ValueError(f"Could not find cal.xml")
        print(statement_link)
        cal_content = fetch_file_content(statement_link)
        all_equations = parse_calculation_arcs(cal_content)
        return all_equations
    except requests.RequestException as e:
        raise ValueError(f"Error fetching the statement: {e}")
    


def get_all_statements_soup(
    ticker, accession_number, headers, statement_keys_map
):
    """
    Retrieves the BeautifulSoup object for a specific financial statement.

    Args:
        ticker (str): Stock ticker symbol.
        accession_number (str): SEC filing accession number.
        statement_name (str): has to be 'balance_sheet', 'income_statement', 'cash_flow_statement'
        headers (dict): Headers for HTTP request.
        statement_keys_map (dict): Mapping of statement names to keys.

    Returns:
        BeautifulSoup: Parsed HTML/XML content of the financial statement.

    Raises:
        ValueError: If the statement file name is not found or if there is an error fetching the statement.
    """
    session = requests.Session()
    cik = cik_matching_ticker(ticker)
    base_link = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_number}"
    print(base_link)
    # Get statement file names
    statement_file_name_dict = get_statement_file_names_in_filing_summary(
        ticker, accession_number, headers
    )

    statement_soups = {}
    statement_names = ["income_statement", "balance_sheet", "cash_flow_statement"]
    for statement_name in statement_names:
        statement_link = None
        # Find the specific statement link
        for possible_key in statement_keys_map.get(statement_name.lower(), []):
            file_name = statement_file_name_dict.get(possible_key.lower())
            if file_name:
                statement_link = f"{base_link}/{file_name}"
                print(statement_link)
                break
        if not statement_link:
            raise ValueError(f"Could not find statement file name for {statement_name}")
        # Fetch the statement
        try:
            statement_response = session.get(statement_link, headers=headers)
            statement_response.raise_for_status()  # Check for a successful request
            # Parse and return the content
            if statement_link.endswith(".xml"):
                statement_soups[statement_name] =  BeautifulSoup(
                    statement_response.content, "lxml-xml", from_encoding="utf-8"
                )
            else:
                statement_soups[statement_name] = BeautifulSoup(statement_response.content, "lxml")
        except requests.RequestException as e:
            raise ValueError(f"Error fetching the statement: {e}")
    return statement_soups

def extract_columns_values_and_dates_from_statement(soup: BeautifulSoup, ticker, accession_number, statement_name, get_duplicates=True, quarterly=False):
    """
    Extracts columns, values, and dates from an HTML soup object representing a financial statement.

    Args:
        soup (BeautifulSoup): The BeautifulSoup object of the HTML document.

    Returns:
        tuple: Tuple containing columns, values_set, and date_time_index.
    """


    def check_units(num1, num2):
        # Define the conversion factors
        # TODO: should it be int or float
        num1 = float(num1)
        num2 = float(num2)
        print( num1, num2)
        conversion_factors = {
            "dollars": 1,
            "thousands": 1000,
            "millions": 1000000,
            "cent": 1/1000
        }
        # Check if the second number represents the same value as the first number
        for unit, factor in conversion_factors.items():
            print("##############")
            print(num1)
            print(num2 * factor)
            if num1 == num2 * factor:
                return factor # * 1/1000 add for thousand def
        # If the second number doesn't represent the same value in any unit
        return False

    columns = []
    values_set = []
    unit_multiplier_set = []
    text_set = {}
    if statement_name == "income_statement":
        date_time_index, header_indices = get_datetime_index_dates_from_statement(soup, quarterly=quarterly)
    else: 
        date_time_index, header_indices = get_datetime_index_dates_from_statement(soup, quarterly=quarterly, check_date_indexes=False)
    print(date_time_index)
    company_facts, ld, taxonomy = facts_DF(ticker, headers)


        # Find all column headers (th) for "3 Months Ended" period
        # column_headers = soup.find_all('th', text='3 Months Ended')
        # row = soup.find_all('tr')
        # # Extract the indices of the column headers for "3 Months Ended" period
        # header_indices = [row.find('th').index(header) for header in column_headers]
    rows_that_are_sum = []
    sections_dict = {}

    for table in soup.find_all("table"):
        unit_multiplier = IN_THOUSANDS
        special_case = False
        # print(table)

        # Check table headers for unit multipliers and special cases
        # TODO: using the get_facts function duoble check that the unit_multiplier is correct
        # The facts will have the right units. 
        # Facts are in dollars, edgar_functions extract the amount in thousands!!!

        # if quarterly:
        #     header_indices = find_three_months_ended_indices(soup)
        # else:
        #     ten_k_header_indices = find_twelve_months_ended_indices(soup)
            # Find all column headers
            # column_headers = soup.find_all('th')
            # # Initialize a variable to store the index location of "3 Months Ended"
            # three_months_index = None
            # # Iterate over the column headers to find the index location of "3 Months Ended"
            # for index, header in enumerate(column_headers):
            #     if "3 Months" in header.text:
            #         three_months_index = index
            #         # print(three_months_index)
            #         break
            # header_indices = [three_months_index-1, three_months_index]
        table_header = table.find("th")
        print("=================1")
        if table_header:
            header_text = table_header.get_text()
            # Determine unit multiplier based on header text
            if "in thousands" in header_text.lower():
                unit_multiplier = IN_THOUSANDS
            elif "in millions" in header_text.lower():
                unit_multiplier = IN_MILLIONS
            else:
                unit_multiplier = IN_DOLLARS
            # Check for special case scenario
            if "unless otherwise specified" in header_text:
                special_case = True
        # Fact check the multipler later
        # 
        # print(company_facts)
        # Process each row of the table
        inside_section = False
        is_row_header = False
        current_section_name = FIRST_SECTION
        print("=================2")
        for row in table.select("tr"):
            onclick_elements = row.select("td.pl a, td.pl.custom a")
            if not onclick_elements:
                continue

            onclick_attr = onclick_elements[0]["onclick"]
            row_title = onclick_attr.split("defref_")[-1].split("',")[0]
            row_text = onclick_elements[0].get_text(strip=True)

            # next_sibling_text_td = onclick_elements[0].find_next_sibling("td", class_="text")
            # next_sibling_text_td = row.select("td.pl + td.text")
            if get_duplicates:
                row_contain_number = row.select("td.num, td.nump")
                if not row_contain_number:
                    print(row_title)

                    if row_title.endswith("Abstract"):
                        current_section_name = onclick_elements[0].get_text(strip=True)
                        if current_section_name:
                            if is_row_header: # previous row is also header
                                row_section_name += ":" + current_section_name
                                current_section_name = row_section_name
                                # Get the text content of the <a> element
                                # if not inside_section:
                                print("=================")
                            else:
                                row_section_name = current_section_name
                            is_row_header = True
                            inside_section = True
                            continue
                        else:
                            continue
                    else:
                        pass
                else:
                    is_row_header = False
                
            print("=================3")
            
            row_class = row.get('class')
            print("row class:" , row_class)
            if row_class == ['reu'] or row_class == ['rou']:
                rows_that_are_sum.append(row_title)
            # TODO 'rh' is the class for row header
            if row_class == ['rh']:
                pass
            if row_title in columns and (not get_duplicates):
                continue
            if row_title in columns and inside_section:
                row_title = row_section_name + ":" + row_title
                while (row_title in columns):
                    # TODO: fix when multiple valuea are the same even when they are inside the section
                    row_title = "D1:" + row_title # str(random.randint(1, 10))
                    # continue
                file_name = "terms_that_share_fact_name.txt"
                with open(file_name, 'a+') as file:
                    # Check if the string_to_append already exists in the file
                    file.seek(0)  # Move the cursor to the beginning of the file
                    if row_title not in file.read():
                        # If the string does not exist, write it to the file
                        file.write(row_title + '\n')
            
            # Add the fact to the corresponding section in the dictionary
            # if row_text.endswith("Abstract"):
            #     current_section_name = FIRST_SECTION
            if current_section_name in sections_dict:
                sections_dict[current_section_name].append(row_title)
            else:
                sections_dict[current_section_name] = [row_title]

            
            column = row_title
            columns.append(column)
            text_set[column] = row_text
            print("=================4")
            # file_name = "balance_sheet_us-gaap_terms.txt"
            # with open(file_name, 'a+') as file:
            #     # Check if the string_to_append already exists in the file
            #     file.seek(0)  # Move the cursor to the beginning of the file
            #     if row_title not in file.read():
            #         # If the string does not exist, write it to the file
            #         file.write(row_title + '\n')

            # Extract column title from 'onclick' attribute
            # title_row = row.select("td.text")[0]
            # if title_row:
            #     print("test")
            #     print(title_row.get_text())
            #     columns.append(title_row.[0].get_text(strip=True))
            # else:
            #     onclick_attr = onclick_elements[0]["onclick"]
            #     column_title = onclick_attr.split("defref_")[-1].split("',")[0]
            #     columns.append(column_title)

            # Initialize values array with NaNs
            length_date_time_index = len(date_time_index)
            values = [0] * length_date_time_index
            values_counter = 0
            print("=================5")
            # Process each cell in the row
            for i, cell in enumerate((row.select("td.text, td.nump, td.num"))):
                print("=================6")
                # if quarterly:
                if i not in header_indices:
                    continue
                # elif ten_k_header_indices:
                #     if i not in ten_k_header_indices:
                #         continue
                if "text" in cell.get("class"):
                    values_counter += 1
                    continue

                # Clean and parse cell value
                a_tag = cell.find('a')
                if a_tag:
                    # sys.exit(f"{cell}----- {cell.get_text()}")
                    value = keep_numbers_and_decimals_only_in_string(
                    a_tag.get_text().replace("$", "")
                    .replace(",", "")
                    .replace("(", "")
                    .replace(")", "")
                    .strip()
                )
                    # sys.exit(f"{cell}----- {cell.get_text()}------{value}")
                else:
                    value = keep_numbers_and_decimals_only_in_string(
                        cell.text.replace("$", "")
                        .replace(",", "")
                        .replace("(", "")
                        .replace(")", "")
                        .strip()
                    )
                print("=================7")
                if value:
                    value = float(value)
                    # print(value)
                    # Adjust value based on special case and cell class
                    # TODO can not get the unit for the stuff that have the same name.
                    # edgar tools knows how to do it!
                    if (row_title not in keep_value_unchanged) : #and ("in dollars" not in onclick_elements[0].get_text(strip=True).lower()) and ("in shares" not in onclick_elements[0].get_text(strip=True).lower()) and ("per share" not in onclick_elements[0].get_text(strip=True).lower()) :
                        index = row_title.find(f"{taxonomy}_")
                        if index != -1: #and i == 0:
                            # Slice the string to get the part after "us-gaap_"
                            fact = row_title[index + len(f"{taxonomy}_"):]
                            print("=================8")
                            # print(fact)
                            # print(accession_number)
                            # print(date_time_index[i])
                            print(date_time_index, values_counter)
                            end_date = str(date_time_index[values_counter])
                            end_date = end_date.split(" ")[0]
                            # print(end_date)
                            criteria = f'fact=="{fact}" and accn=="{accession_number}" and end=="{end_date}"'
                            # print(criteria)
                            try:
                                # filtered_data = company_facts.query(criteria)
                                # filtered_data = company_facts[(company_facts['fact'] == fact) & (company_facts['accn'] == accession_number) & (company_facts['end'] == end_date) ]
                                filtered_data = company_facts[(company_facts['fact'] == fact) & (company_facts['end'] == end_date) ]
                            except Exception as e:
                                pass
                            # print("##############1")
                            # print(filtered_data)
                            #company_facts[(company_facts['fact'] == fact) & (company_facts['accn'] == accession_number) & (company_facts['end'] == end_date) ] #& (company_facts['end'] == end_date)
                            #company_facts.query(f'fact=="{fact}" and accn=="{accession_number}]" and end=="{end_date}"')
                            filtered_value = 0
                            print("=================9")
                            try:
                                filtered_value = filtered_data.iloc[0]['val']
                            except Exception as e:
                                pass
                            # print("##############2")
                            # print(filtered_value)
                            # TODO now i filter through every cell, only filter if the firct cell is 0
                            print("fact and table value")
                            print(filtered_data)
                            print(value)
                            if ":" in row_title: # use same unit as base fact
                                if filtered_value != 0:
                                    if row_title.split(":")[-1] in columns:
                                        index = columns.index(row_title.split(":")[-1])
                                        unit_multiplier = unit_multiplier_set[index]
                            elif filtered_value != 0:
                                fact_unit = check_units(abs(filtered_value), value)
                                print("##############unit")
                                print(fact_unit)
                                if fact_unit:
                                    unit_multiplier = fact_unit

                        print(f"===== {i}")
                        if "nump" in cell.get("class"):
                            values[values_counter] = value * unit_multiplier
                            values_counter += 1
                        else:
                            values[values_counter] = -value * unit_multiplier
                            values_counter += 1
                    else:
                        if "nump" in cell.get("class"):
                            values[values_counter] = value
                            values_counter += 1
                        else:
                            values[values_counter] = -value
                            values_counter += 1
                    # check if the untit multiplier is correct
                else:
                    pass # it is a title row
            values_set.append(values)
            unit_multiplier_set.append(unit_multiplier)
    print("return values")
    print(sections_dict)
    return columns, values_set, date_time_index, rows_that_are_sum, text_set, sections_dict

def extract_columns_from_statement(soup, get_duplicates=True):
    """
    Extracts columns, values, and dates from an HTML soup object representing a financial statement.

    Args:
        soup (BeautifulSoup): The BeautifulSoup object of the HTML document.

    Returns:
        tuple: Tuple containing columns, values_set, and date_time_index.
    """
    columns = []

    for table in soup.find_all("table"):
        unit_multiplier = 1
        special_case = False

        # Check table headers for unit multipliers and special cases
        table_header = table.find("th")
        if table_header:
            header_text = table_header.get_text()
            # Determine unit multiplier based on header text
            if "$ in Thousands" in header_text:
                unit_multiplier = 1
            elif "$ in Millions" in header_text:
                unit_multiplier = 1000
            else:
                unit_multiplier = 0.001
            # Check for special case scenario
            if "unless otherwise specified" in header_text:
                special_case = True

        # Process each row of the table
        inside_section = False
        for row in table.select("tr"):
            onclick_elements = row.select("td.pl a, td.pl.custom a")
            if not onclick_elements:
                continue
            if get_duplicates:
                next_sibling_text_td = row.select("td.text")
                if next_sibling_text_td:
                    # Get the text content of the <a> element
                    row_section_name = onclick_elements[0].get_text(strip=True)
                    if inside_section:
                        pass
                    inside_section = True
                    print("=================")
                    continue
                
            
            onclick_attr = onclick_elements[0]["onclick"]
            row_title = onclick_attr.split("defref_")[-1].split("',")[0]

            if row_title in sum(columns, []) and (not get_duplicates):
                continue
            if row_title in sum(columns, []) and inside_section:
                row_title = row_section_name + ":" + row_title
                if row_title in sum(columns, []):
                    # row_title = row_title + "_2"
                    continue
                file_name = "terms_that_share_fact_name.txt"
                with open(file_name, 'a+') as file:
                    # Check if the string_to_append already exists in the file
                    file.seek(0)  # Move the cursor to the beginning of the file
                    if row_title not in file.read():
                        # If the string does not exist, write it to the file
                        file.write(row_title + '\n')
            
            column = [row_title, onclick_elements[0].get_text(strip=True)]
            columns.append(column)
            
    return columns

def check_for_two_currency(text):
    # Function to extract currency symbols (EUR, USD, €, $) from a text
    # currencies = [EUR, USD, EUR_sign, USD_sign, CNY, CNY_sign]
    # if (EUR in text and USD in text) or (EUR_sign in text and USD_sign in text) or (EUR in text and USD in text) or (EUR_sign in text and USD_sign in text):
    #     return True
    num_of_currencies = 0
    for currency, currency_sign in currency_map.items():
        if currency in text or currency_sign in text:
            num_of_currencies += 1
    if num_of_currencies > 1:
        return True
    return False

def extract_currency(text):
    # Function to extract currency symbols (EUR, USD, €, $) from a text
    currencies = [EUR, USD, EUR_sign, USD_sign, CNY, CNY_sign, INR, INR_sign]
    for currency, currency_sign in currency_map.items():
        if currency in text or currency_sign in text:
            return currency
    return None

def get_most_frequent_currency(currencies):
    # Get the most frequent currency from the list
    currency_count = Counter(currencies)
    most_frequent_currency = currency_count.most_common(1)[0][0]
    return most_frequent_currency

def check_datetime_index_dates_for_currency():
    pass

def get_date_indexes(column_indexes, target):
    target_columns = ["1 Months", "2 Months", "3 Months", "4 Months", "5 Months", "6 Months", "7 Months", "8 Months", "9 Months", "10 Months", "11 Months", "12 Months"]
    start_idx = 0
    end_idx = 0
    max_column_index = column_indexes[target]['index']
    for target_column in target_columns:
        if target_column in column_indexes:
            if column_indexes[target_column]['index'] < max_column_index:
                start_idx += column_indexes[target_column]['colspan']
    # end_idx is not included
    end_idx = start_idx +  column_indexes[target]['colspan']
    return start_idx, end_idx


def get_datetime_index_dates_from_statement(soup: BeautifulSoup, quarterly=False, check_date_indexes=True) -> pd.DatetimeIndex:
    """
    Extracts datetime index dates from the HTML soup object of a financial statement.

    Args:
        soup (BeautifulSoup): The BeautifulSoup object of the HTML document.

    Returns:
        pd.DatetimeIndex: A Pandas DatetimeIndex object containing the extracted dates.
        # TODO comapnies that file 20F might have columns for same date but differnet currency
        # take the currency with the most columns as the base, also check its the same as previous statements
    """
    table_headers = soup.find_all("th", {"class": "th"})
    # Define the target column headers
    target_columns =  ["1 Months", "2 Months", "3 Months", "4 Months", "5 Months", "6 Months", "7 Months", "8 Months", "9 Months", "10 Months", "11 Months", "12 Months"]
    column_indexes = {}
    currencies = []
    header_currency_mapping = {}
    contain_two_currency = False
    for header in soup.find_all("th", {"class": "tl"}):
        if header:
            header_text = header.get_text()
            if not contain_two_currency:
                contain_two_currency = check_for_two_currency(header_text)
    for index, header in enumerate(table_headers):
        header_text = header.text.strip()
        if contain_two_currency:
            header_currency = extract_currency(header_text)
            if header_currency:
                currencies.append(header_currency)
        for target in target_columns:
            if target in header_text:
                column_indexes[target] = {
                    'index': index,
                    'colspan': int(header.get("colspan", 1))  # Default colspan to 1 if not specified
                }

    dates = [str(th.div.string) for th in table_headers if th.div and th.div.string]
    print(dates)
    if contain_two_currency:
        main_currency = get_most_frequent_currency(currencies)
        date_currencies = currencies #[extract_currency(date) for date in dates]
        print(main_currency)
        print(date_currencies)
        # Filter dates and header indexes by the main currency
        dates = [date for date, currency in zip(dates, date_currencies) if currency == main_currency]
        dates = [standardize_date(date).replace(".", "") for date in dates]
        filtered_indexes = [index for index, currency in enumerate(date_currencies) if currency == main_currency]
        print(dates, filtered_indexes)
    
    # print(three_months_index)
    if check_date_indexes:
        if quarterly:
            # dates = dates[three_months_index: three_months_index + three_colspan]
            start_idx, end_idx = get_date_indexes(column_indexes, "3 Months")
        else:
            # dates = dates[three_months_index + three_colspan: three_months_index + three_colspan + twelve_colspan]
            start_idx, end_idx = get_date_indexes(column_indexes, "12 Months")
            print(start_idx, end_idx)
        date_indexes = range(start_idx, end_idx)
        dates = dates[start_idx: end_idx]
    elif contain_two_currency:
        date_indexes = filtered_indexes # range(len(dates))
    else:
        date_indexes =  range(len(dates))
    index_dates = pd.to_datetime(dates)
    print(dates, date_indexes)
    return index_dates, date_indexes

def find_three_months_ended_indices(soup: BeautifulSoup):
    # Parse the HTML table
    date_headers_cosnt = ["3 Months", "6 Months", "9 Months", "12 Months"]
    date_headers_keys = []
    date_headers = {}
    columns_num = 0
    table = soup.find('table')
    table_headers = soup.find_all("th", {"class": "th"})
    # print(table_headers)
    for th in table_headers:
        for dh_const in date_headers_cosnt:
            if dh_const in (th.get_text()):
                date_headers_keys.append(dh_const)
                date_headers[dh_const] = th['colspan']
                print(dh_const)
                print(th['colspan'])
                continue
        columns_num += 1
    # print(date_headers)
    # TODO: it might not be 3
    three_months_index = date_headers_keys.index(date_headers_cosnt[0])
    column_span = int(date_headers[date_headers_cosnt[0]])
    if three_months_index == 0:
        indices = range(three_months_index, three_months_index + column_span)
    else:
        indices = range(three_months_index * column_span, (three_months_index * column_span) + column_span)
    # print(three_months_index)
    # print(date_headers[date_headers_cosnt[0]])
    # print(indices)
    return indices
        
def find_twelve_months_ended_indices(soup: BeautifulSoup):
    # Parse the HTML table
    date_headers_cosnt = ["3 Months", "6 Months", "9 Months", "12 Months"]
    date_headers_keys = []
    date_headers = {}
    columns_num = 0
    table = soup.find('table')
    table_headers = soup.find_all("th", {"class": "th"})
    # print(table_headers)
    for th in table_headers:
        for dh_const in date_headers_cosnt:
            if dh_const in (th.get_text()):
                date_headers_keys.append(dh_const)
                date_headers[dh_const] = th['colspan']
                # print(dh_const)
                # print(th['colspan'])
                continue
        columns_num += 1
    # print(date_headers)
    if not date_headers:
        return False
    tweleve_months_index = date_headers_keys.index(date_headers_cosnt[3])
    column_span_tweleve = int(date_headers[date_headers_cosnt[3]])
    if tweleve_months_index == 0:
        indices = range(tweleve_months_index, tweleve_months_index + column_span_tweleve)
    else:
        # print("=======")
        column_span_three = int(date_headers[date_headers_cosnt[0]])
        indices = range(tweleve_months_index * column_span_three, (tweleve_months_index * column_span_three) + column_span_tweleve)
    # print(tweleve_months_index)

    # print(indices)
    return indices


def standardize_date(date: str) -> str:
    """
    Standardizes date strings by replacing abbreviations with full month names.

    Args:
        date (str): The date string to be standardized.

    Returns:
        str: The standardized date string.
    """
    for abbr, full in zip(calendar.month_abbr[1:], calendar.month_name[1:]):
        date = date.replace(abbr, full)
    return date


def keep_numbers_and_decimals_only_in_string(mixed_string: str):
    """
    Filters a string to keep only numbers and decimal points.

    Args:
        mixed_string (str): The string containing mixed characters.

    Returns:
        str: String containing only numbers and decimal points.
    """
    num = "1234567890."
    allowed = list(filter(lambda x: x in num, mixed_string))
    return "".join(allowed)


def create_dataframe_of_statement_values_columns_dates(
    values_set, columns, index_dates
) -> pd.DataFrame:
    """
    Creates a DataFrame from statement values, columns, and index dates.

    Args:
        values_set (list): List of values for each column.
        columns (list): List of column names.
        index_dates (pd.DatetimeIndex): DatetimeIndex for the DataFrame index.

    Returns:
        pd.DataFrame: DataFrame constructed from the given data.
    """
    transposed_values_set = list(zip(*values_set))
    df = pd.DataFrame(transposed_values_set, columns=columns, index=index_dates)
    return df


def process_one_statement(ticker, accession_number, statement_name, acc_num_unfiltered, quarterly=False):
    """
    Processes a single financial statement identified by ticker, accession number, and statement name.

    Args:
        ticker (str): The stock ticker.
        accession_number (str): The SEC accession number.
        statement_name (str): Name of the financial statement.

    Returns:
        pd.DataFrame or None: DataFrame of the processed statement or None if an error occurs.
    """
    try:
        # Fetch the statement HTML soup
        soup = get_statement_soup(
            ticker,
            accession_number,
            statement_name,
            headers=headers,
            statement_keys_map=statement_keys_map,
        )
    except Exception as e:
        logging.error(
            f"Failed to get statement soup: {e} for accession number: {accession_number}"
        )
        return None, None, None, None

    try:
        cal_facts = get_cal_xml_filename(ticker,
            accession_number,
            headers=headers)
    except Exception as e:
        cal_facts = None
        print(e)
    if soup:
        try:
            # Extract data and create DataFrame
            columns, values, dates, rows_that_are_sum, rows_text, sections_dict = extract_columns_values_and_dates_from_statement(
                soup, ticker, acc_num_unfiltered, statement_name, quarterly=quarterly
            )
            df = create_dataframe_of_statement_values_columns_dates(
                values, columns, dates
            )

            if not df.empty:
                # Remove duplicate columns
                df = df.drop_duplicates()
                df = df.T
                pass
            else:
                logging.warning(
                    f"Empty DataFrame for accession number: {accession_number}"
                )
                return None
            
            # TODO remove this
            if len(df.columns) > 3:
                # Select the last 3 columns
                last_three_columns = df.iloc[:, -3:]
                df = last_three_columns
            df = df.round(2)
            financial_statement = DataFrameWithStringListTracking(df, rows_that_are_sum, rows_text, cal_facts, sections_dict)
            return financial_statement
        except Exception as e:
            logging.error(f"Error processing statement: {e}")
            return None

def process_all_statements_facts(ticker, accession_number):
    """
    Processes a single financial statement identified by ticker, accession number, and statement name.

    Args:
        ticker (str): The stock ticker.
        accession_number (str): The SEC accession number.
        statement_name (str): Name of the financial statement.

    Returns:
        pd.DataFrame or None: DataFrame of the processed statement or None if an error occurs.
    """
    try:
        # Fetch the statement HTML soup
        soups = get_all_statements_soup(
            ticker,
            accession_number,
            headers=headers,
            statement_keys_map=statement_keys_map,
        )
    except Exception as e:
        logging.error(
            f"Failed to get statement soup: {e} for accession number: {accession_number}"
        )
        return None
    all_columns = {}
    if soups:
        for statement_name, soup in soups.items():
            try:
                # Extract data and create DataFrame
                columns = extract_columns_from_statement(
                    soup, get_duplicates=False
                )
                all_columns[statement_name] = columns
            except Exception as e:
                logging.error(f"Error processing statement: {e}")
                return None
                # print("ERROR")
        return all_columns

def get_label_dictionary(ticker, headers):
    facts = get_facts(ticker, headers)
    us_gaap_data = facts["facts"]["us-gaap"]
    labels_dict = {fact: details["label"] for fact, details in us_gaap_data.items()}
    return labels_dict


def rename_statement(statement, label_dictionary):
    def make_readable(name):
        # Insert a space before each capital letter (except the first one) if there is no space already
        result = ''
        for char in name:
            if char.isupper() and result and result[-1] != ' ':
                result += ' '
            result += char
        return result.strip()

    # Extract the part after the first "_" and then map it using the label dictionary
    statement.index = statement.index.map(lambda x: label_dictionary.get(x.split("_", 1)[-1], x) if label_dictionary.get(x.split("_", 1)[-1]) is not None else x)

    # Handle labels that do not contain an underscore
    statement.index = statement.index.map(lambda x: make_readable(x))

    return statement

# def rename_statement(statement, label_dictionary):
#     # Extract the part after the first "_" and then map it using the label dictionary
#     statement.index = statement.index.map(
#         lambda x: label_dictionary.get(x.split("_", 1)[-1], x) 
#     )
#     return statement

def is_next_element_class_text(html_content):
    """
    Check the class of the element after <td class="pl"><a> tags.
    
    Args:
    - html_content (str): HTML content to parse
    
    Returns:
    - str: Message indicating the class of the element after <td class="pl"><a> if it contains 'text',
           otherwise returns None.
    """
    # Parse HTML using BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')

    # Find all <td> elements with class="pl" and <a> elements within them
    td_pl_elements = soup.select("td.pl a")

    # Iterate over <a> elements
    for a_element in td_pl_elements:
        # Check if there is a next sibling element after <a> tag
        if a_element.next_sibling and a_element.next_sibling.name == 'td':
            # Get the class attribute of the next sibling element
            next_sibling_class = a_element.next_sibling.get('class')

            # Check if class is present and contains 'text'
            if next_sibling_class and 'text' in next_sibling_class:
                return True
    
    # If no such element found, return None
    return False

def merge_dfs(df1, df2):
    # Initialize an empty DataFrame for the merged result
    merged_df = pd.DataFrame()
    custom_merged = merge_index(df1, df2)
    df1 = df1.reindex(index=custom_merged, fill_value=0)
    df2 = df2.reindex(index=custom_merged, fill_value=0)
    # Merge columns from df1
    for column in df1.columns:
        merged_df[column] = df1[column]
    # Merge columns from df2 that are not already in df1
    for column in df2.columns:
        if column not in df1.columns:
            merged_df[column] = df2[column]
    # Sort the columns to sort by date
    merged_df = merged_df.sort_index(axis=1, ascending=False)
    return merged_df

def order_columns(df1, df2):
    # Combine columns from both DataFrames
    combined_columns = list(set(df1.columns) | set(df2.columns))
    # Sort the combined columns
    ordered_columns = sorted(combined_columns)
    # Reorder columns in both DataFrames
    df1 = df1.reindex(columns=ordered_columns)
    df2 = df2.reindex(columns=ordered_columns)
    return df1, df2

def merge_index(df1, df2):
    custom_merged = []
    df1_index = df1.index.tolist()
    df2_index = df2.index.tolist()
    size_of_index_1 = len(df1_index)
    size_of_index_2 = len(df2_index)
    second_index = 0
    first_index = 0
    for i in range(size_of_index_1):
        if first_index != size_of_index_1 and second_index != size_of_index_2:
            if df1_index[first_index] == df2_index[second_index]:
                custom_merged.append(df1_index[first_index])
                second_index = second_index + 1
                first_index = first_index + 1
            elif df1_index[first_index] not in df2_index:
                # index not in df2
                custom_merged.append(df1_index[first_index])
                first_index = first_index + 1
            else: # index not in df1
                for k in range(second_index, size_of_index_2):
                    if df1_index[first_index] == df2_index[k]:
                        custom_merged.append(df1_index[first_index])
                        second_index = k + 1
                        first_index = first_index + 1
                        continue
                    else:
                        custom_merged.append(df2_index[k]) 
        elif second_index == size_of_index_2:
            pass
        else:
            break
    return custom_merged
