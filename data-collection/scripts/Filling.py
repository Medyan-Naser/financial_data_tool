from headers import *
from constants import *
from healpers import *
from FinancialStatement import *
from cal_xml import fetch_file_content, parse_calculation_arcs

import requests
from bs4 import BeautifulSoup
import re
import calendar # for date standarization
import logging

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

class Filling():

    def __init__(self, ticker, cik, accession_number) -> None:
        self.ticker = ticker
        self.accession_number = accession_number
        self.cik = cik
        
        self.xml_equations = None


    def _get_file_name(self, report):
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
        
    def _is_statement_file(self, short_name_tag, long_name_tag, file_name):
        """
        Determines if a given file is a financial statement file.
        """
        return (
            short_name_tag is not None
            and long_name_tag is not None
            and file_name  # Ensure file_name is not an empty string
            # and "Statement" in long_name_tag.text # check if this is needed
        )
    
    # TODO: what class this function belong to
    def get_statement_file_names_in_filing_summary(self):
        """
        Retrieves file names of financial statements from a filing summary.
        Returns:
            dict: Dictionary mapping statement types to their file names.
        """
        try:
            # Set up request session and get filing summary
            session = requests.Session()
            base_link = f"https://www.sec.gov/Archives/edgar/data/{self.cik}/{self.accession_number}"
            filing_summary_link = f"{base_link}/FilingSummary.xml"
            filing_summary_response = session.get(
                filing_summary_link, headers=headers
            ).content.decode("utf-8")

            # Parse the filing summary
            filing_summary_soup = BeautifulSoup(filing_summary_response, "lxml-xml")
            statement_file_names_dict = {}
            # Extract file names for statements
            for report in filing_summary_soup.find_all("Report"):
                file_name = self._get_file_name(report)
                short_name, long_name = report.find("ShortName"), report.find("LongName")
                if self._is_statement_file(short_name, long_name, file_name):
                    statement_file_names_dict[short_name.text.lower()] = file_name
            return statement_file_names_dict
        except requests.RequestException as e:
            print(f"An error occurred: {e}")
            return {}
    
    def get_date_indexes(self, column_indexes, target):
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
    
    def get_statement_soup(self, statement_name):
        """
        Retrieves the BeautifulSoup object for a specific financial statement.

        Args:
            ticker (str): Stock ticker symbol.
            accession_number (str): SEC filing accession number.
            statement_name (str): has to be 'balance_sheet', 'income_statement', 'cash_flow_statement'
        Returns:
            BeautifulSoup: Parsed HTML/XML content of the financial statement.
        """
        session = requests.Session()
        base_link = f"https://www.sec.gov/Archives/edgar/data/{self.cik}/{self.accession_number}"
        print(base_link)
        # Get statement file names
        statement_file_name_dict = self.get_statement_file_names_in_filing_summary()
        statement_link = None
        # Find the specific statement link
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
        

    def get_cal_xml_filename(self):
        """
        Retrieves the BeautifulSoup object for a specific financial statement.
        Returns:
            BeautifulSoup: Parsed HTML/XML content of the financial statement.

        Raises:
            ValueError: If the statement file name is not found or if there is an error fetching the statement.
        """
        session = requests.Session()
        base_link = f"https://www.sec.gov/Archives/edgar/data/{self.cik}/{self.accession_number}"
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
            self.xml_equations = parse_calculation_arcs(cal_content)
        except requests.RequestException as e:
            raise ValueError(f"Error fetching the statement: {e}")
        

    def extract_columns_values_and_dates_from_statement(self, soup: BeautifulSoup, ticker, accession_number, statement_name, get_duplicates=True, quarterly=False):
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
            date_time_index, header_indices = self.get_datetime_index_dates_from_statement(soup, quarterly=quarterly)
        else: 
            date_time_index, header_indices = self.get_datetime_index_dates_from_statement(soup, quarterly=quarterly, check_date_indexes=False)
        print(date_time_index)
        # TODO : this function is in company class
        company_facts, ld, taxonomy = facts_DF(ticker, headers)


        rows_that_are_sum = []
        sections_dict = {}

        for table in soup.find_all("table"):
            unit_multiplier = IN_THOUSANDS
            special_case = False

            # Check table headers for unit multipliers and special cases
            # TODO: using the get_facts function duoble check that the unit_multiplier is correct
            # The facts will have the right units. 

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
                                print(date_time_index, values_counter)
                                end_date = str(date_time_index[values_counter])
                                end_date = end_date.split(" ")[0]
                                # print(end_date)
                                criteria = f'fact=="{fact}" and accn=="{accession_number}" and end=="{end_date}"'
                                # print(criteria)
                                try:
                                    filtered_data = company_facts[(company_facts['fact'] == fact) & (company_facts['end'] == end_date) ]
                                except Exception as e:
                                    pass
                                filtered_value = 0
                                print("=================9")
                                try:
                                    filtered_value = filtered_data.iloc[0]['val']
                                except Exception as e:
                                    pass

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

    def get_datetime_index_dates_from_statement(self, soup: BeautifulSoup, quarterly=False, check_date_indexes=True) -> pd.DatetimeIndex:
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
                start_idx, end_idx = self.get_date_indexes(column_indexes, "3 Months")
            else:
                # dates = dates[three_months_index + three_colspan: three_months_index + three_colspan + twelve_colspan]
                start_idx, end_idx = self.get_date_indexes(column_indexes, "12 Months")
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
    

    def create_dataframe_of_statement_values_columns_dates(self, values_set, columns, index_dates) -> pd.DataFrame:
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
    

    def process_one_statement(self, ticker, accession_number, statement_name, acc_num_unfiltered, quarterly=False):
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
            soup = self.get_statement_soup(
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
            cal_facts = self.get_cal_xml_filename(ticker,
                accession_number,
                headers=headers)
        except Exception as e:
            cal_facts = None
            print(e)
        if soup:
            try:
                # Extract data and create DataFrame
                columns, values, dates, rows_that_are_sum, rows_text, sections_dict = self.extract_columns_values_and_dates_from_statement(
                    soup, ticker, acc_num_unfiltered, statement_name, quarterly=quarterly
                )
                df = self.create_dataframe_of_statement_values_columns_dates(
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
            




##################################################3
            
## TODO: need to adjust to new structure
            

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