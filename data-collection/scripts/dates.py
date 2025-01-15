from bs4 import BeautifulSoup
import calendar # for date standarization
from currency import *

def standardize_date(date: str) -> str:
    """
    Standardizes date strings by replacing abbreviations with full month names
    Args:
        date (str): The date string to be standardized.
    Returns:
        str: The standardized date string.
    """
    for abbr, full in zip(calendar.month_abbr[1:], calendar.month_name[1:]):
        date = date.replace(abbr, full)
    return date

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
    dates = pd.to_datetime(dates)
    print(dates, date_indexes)
    return dates, date_indexes