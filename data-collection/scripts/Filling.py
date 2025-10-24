from headers import *
from constants import *
from healpers import *
from FinancialStatement import *
from dates import *
from cal_xml import fetch_file_content, parse_calculation_arcs

import requests
from bs4 import BeautifulSoup
import re
import logging

def check_units(num1, num2):
    # Define the conversion factors
    num1 = float(num1)
    num2 = float(num2)
    # print( num1, num2)
    conversion_factors = {
        "dollars": 1,
        "thousands": 1000,
        "millions": 1000000,
        "cent": 1/1000
    }
    # Check if the second number represents the same value as the first number
    for unit, factor in conversion_factors.items():
        # print("##############")
        # print(num1)
        # print(num2 * factor)
        if num1 == num2 * factor:
            return float(factor) # * 1/1000 add for thousand def
    # If the second number doesn't represent the same value in any unit
    return False


def parse_table_header(table):
    # print("Parsing table header")
    # Check table headers for unit multipliers and special cases
    # TODO: using the get_facts function duoble check that the unit_multiplier is correct
    # The facts will have the right units. 
    unit_multiplier = IN_THOUSANDS
    shares_unit_multiplier = IN_DOLLARS
    special_case = False
    table_header = table.find("th")
    
    if table_header:
        header_text = table_header.get_text()
        # Determine unit multiplier based on header text
        if "in thousand" in header_text.lower():
            unit_multiplier = IN_THOUSANDS
        elif "in million" in header_text.lower():
            unit_multiplier = IN_MILLIONS
        else:
            unit_multiplier = IN_DOLLARS
        # Check for special case scenario
        if "unless otherwise specified" in header_text:
            special_case = True

        # check for shares unit
        if "shares in" in header_text.lower():
            # Find the position of "shares in"
            start_index = header_text.lower().find("shares in") + len("shares in")
            # Extract the unit by splitting the text after "shares in" and taking the first word
            unit = header_text[start_index:].lower().strip().split()[0]
            # print(unit)
            if "thousand" in unit:
                shares_unit_multiplier = IN_THOUSANDS
            elif "million" in unit:
                shares_unit_multiplier = IN_MILLIONS
            # print(shares_unit_multiplier)
    # print("End of Parsing table header")
    return unit_multiplier, shares_unit_multiplier


class Filling():

    def __init__(self, ticker, cik, acc_num_unfiltered, company_facts, quarterly=False) -> None:
        self.ticker = ticker
        acc_num_filtered = acc_num_unfiltered.replace("-", "")
        self.accession_number_unfiltered = acc_num_unfiltered
        self.accession_number = acc_num_filtered
        self.cik = cik
        self.company_facts = company_facts
        self.quarterly = quarterly
        self.yearly = not quarterly
        
        self.income_statement = None
        self.balance_sheet = None
        self.cash_flow = None

        self.xml_equations = None
        self.statements_file_name_dict = None
        self.company_facts_DF = None
        self.taxonomy = None
        self.facts_taxonomy_to_financial_terms = {} # before named labels_dict
        self.unit_multiplier_set = []

        self.get_statement_file_names_in_filing_summary()
        self.get_cal_xml_equations()
        self.get_company_facts_DF()

    def get_company_facts_DF(self):
        """
        Converts company facts into a DataFrame.
        Returns: tuple: DataFrame of facts and a dictionary of labels.
        """
        # Retrieve facts data
        taxonomy = GAAP
        try:
            us_gaap_data = self.company_facts["facts"][GAAP]
        except Exception as e:
            try:
                us_gaap_data = self.company_facts["facts"][IFRS]
                taxonomy = IFRS
            except Exception as e:
                pass
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
        self.company_facts_DF = df.drop_duplicates(subset=["fact", "end", "val"])
        self.facts_taxonomy_to_financial_terms = {fact: details["label"] for fact, details in us_gaap_data.items()}
        self.taxonomy = taxonomy

    def _get_file_name(self, report):
        """
        Extracts the file name from an XML report tag.
        Args: report (Tag): BeautifulSoup tag representing the report.
        Returns: str: File name extracted from the tag.
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
            # and "Statement" in long_name_tag.text # not alway true!
        )
    
    def get_statement_file_names_in_filing_summary(self):
        """
        Retrieves file names of financial statements from a filing summary.
        The title of the R.htm files
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
            self.statements_file_name_dict = statement_file_names_dict
        except requests.RequestException as e:
            raise ValueError(f"Error fetching the Filing Summary: {e}")
            print(f"An error occurred: {e}")
            
    def get_cal_xml_equations(self):
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
        
    
    def get_statement_file_soup(self, statement_name):
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
        
        statement_link = None
        # Find the specific statement link
        for possible_key in statement_keys_map.get(statement_name.lower(), []):
            file_name = self.statements_file_name_dict.get(possible_key.lower())
            file_name_loss = self.statements_file_name_dict.get((possible_key.lower() + " (loss)"))
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
            #ShortNames = self.statements_file_name_dict.find_all("ShortName")
            # TODO: check again if one of the maps is in one of files R1, R2,...

            statement_link_found = False

            for possible_key in statement_keys_map.get(statement_name.lower(), []):
                for short in self.statements_file_name_dict:
                    # check if the R{num} is less than R10
                    if possible_key in short.lower():
                        print(short.lower(), int(re.search(r'R(\d+)', self.statements_file_name_dict.get(short.lower())).group(1)))
                        if int(re.search(r'R(\d+)', self.statements_file_name_dict.get(short.lower())).group(1)) < 10:
                            file_name = self.statements_file_name_dict.get(short.lower())
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
        

    def get_unit_multiplier(self, row_title, end_date, value_from_table):
        unit_multiplier = 1
        if (row_title not in keep_value_unchanged) : #and ("in dollars" not in onclick_elements[0].get_text(strip=True).lower()) and ("in shares" not in onclick_elements[0].get_text(strip=True).lower()) and ("per share" not in onclick_elements[0].get_text(strip=True).lower()) :
            index = row_title.find(f"{self.taxonomy}_")
            if index != -1:  # TODO now i filter through every cell, only filter if the firct cell is 0
                # Slice the string to get the part after "us-gaap_"
                fact = row_title[index + len(f"{self.taxonomy}_"):]
                end_date = str(end_date)
                end_date = end_date.split(" ")[0]
                # print(end_date)
                criteria = f'fact=="{fact}" and accn=="{self.accession_number_unfiltered}" and end=="{end_date}"'
                # print(criteria)
                try:
                    filtered_data = self.company_facts_DF[(self.company_facts_DF['fact'] == fact) & (self.company_facts_DF['end'] == end_date) ]
                except Exception as e:
                    pass
                filtered_value = 0
                try:
                    filtered_value = filtered_data.iloc[0]['val']
                except Exception as e:
                    pass

                if filtered_value != 0:
                    fact_unit = check_units(abs(filtered_value), value_from_table)
                    # print("##############unit")
                    # print(fact_unit)
                    if fact_unit:
                        unit_multiplier = fact_unit
        return unit_multiplier


    def extract_columns_values_and_dates_from_statement(self, soup: BeautifulSoup, statement_name, get_duplicates=True):
        """
        Extracts columns, values, and dates from an HTML soup object representing a financial statement.
        Args:
            soup (BeautifulSoup): The BeautifulSoup object of the HTML document.
        Returns:
            tuple: Tuple containing columns, values_set, and dates.
        """


        columns = []
        values_set = []
        unit_multiplier_set = []
        text_set = {}
        if statement_name == "income_statement":
            dates, date_indexes = get_datetime_index_dates_from_statement(soup, quarterly=self.quarterly)
        else: 
            dates, date_indexes = get_datetime_index_dates_from_statement(soup, quarterly=self.quarterly, check_date_indexes=False)
        # print(dates)
        # TODO : this function is in company class


        rows_that_are_sum = []
        sections_dict = {}

        for table in soup.find_all("table"):
            unit_multiplier, shares_unit_multiplier = parse_table_header(table)
            # Fact check the multipler later
            # Process each row of the table
            inside_section = False
            is_row_header = False
            current_section_name = FIRST_SECTION
            for row in table.select("tr"):
                onclick_elements = row.select("td.pl a, td.pl.custom a")
                if not onclick_elements:
                    continue

                onclick_attr = onclick_elements[0]["onclick"]
                row_title = onclick_attr.split("defref_")[-1].split("',")[0]
                row_text = onclick_elements[0].get_text(strip=True)

                if get_duplicates:
                    row_contain_number = row.select("td.num, td.nump")
                    if row_contain_number:
                        is_row_header = False
                    else:
                        if row_title.endswith("Abstract"):
                            current_section_name = onclick_elements[0].get_text(strip=True)
                            if current_section_name:
                                if is_row_header: # previous row is also header
                                    row_section_name += ":" + current_section_name
                                    current_section_name = row_section_name
                                else:
                                    row_section_name = current_section_name
                                is_row_header = True
                                inside_section = True
                                continue
                            else:
                                continue

                                    
                row_class = row.get('class')
                # print("row class:" , row_class)
                if row_class == ['reu'] or row_class == ['rou']:
                    rows_that_are_sum.append(row_title)
                # TODO 'rh' is the class for row header
                if row_class == ['rh']:
                    continue
                if row_title in columns and (not get_duplicates):
                    continue
                if row_title in columns and inside_section:
                    row_title = row_section_name + ":" + row_title
                    while (row_title in columns):
                        # TODO: fix when multiple valuea are the same even when they are inside the section
                        row_title = "D1:" + row_title # str(random.randint(1, 10))
                
                # Add the fact to the corresponding section in the dictionary

                if current_section_name in sections_dict:
                    sections_dict[current_section_name].append(row_title)
                else:
                    sections_dict[current_section_name] = [row_title]

                
                column = row_title
                columns.append(column)
                text_set[column] = row_text
                length_dates = len(dates)
                values = [0] * length_dates
                column_counter = 0
                # Process each cell in the row
                for date_idx, cell in enumerate((row.select("td.text, td.nump, td.num"))):
                    if date_idx not in date_indexes:
                        continue

                    if "text" in cell.get("class"):
                        column_counter += 1
                        continue

                    # Clean and parse cell value
                    a_tag = cell.find('a')
                    if a_tag:
                        value = keep_numbers_and_decimals_only_in_string(
                        a_tag.get_text().replace("$", "")
                        .replace(",", "") .replace("(", "")
                        .replace(")", "").strip()
                    )
                    else:
                        value = keep_numbers_and_decimals_only_in_string(
                            cell.text.replace("$", "")
                            .replace(",", "").replace("(", "")
                            .replace(")", "").strip()
                        )
                    if value and date_idx == date_indexes[0]:
                        value = float(value)
                        # Adjust value based on special case and cell class
                        # TODO can not get the unit for the stuff that have the same name.
                        # edgar tools knows how to do it!
                        if (row_title not in keep_value_unchanged) : #and ("in dollars" not in onclick_elements[0].get_text(strip=True).lower()) and ("in shares" not in onclick_elements[0].get_text(strip=True).lower()) and ("per share" not in onclick_elements[0].get_text(strip=True).lower()) :
                            if ":" in row_title: # use same unit as base fact
                                if row_title.split(":")[-1] in columns:
                                    index = columns.index(row_title.split(":")[-1])
                                    unit_multiplier = unit_multiplier_set[index]
                                # else:
                                #     unit_multiplier = self.get_unit_multiplier(row_title, date_indexes[column_counter], value)
                            else:
                                unit_multiplier = self.get_unit_multiplier(row_title, dates[column_counter], value)
                            if "nump" in cell.get("class"):
                                values[column_counter] = value * unit_multiplier
                            else:
                                values[column_counter] = -value * unit_multiplier
                        else:
                            # this will make sure the other columns of that row to not be changed
                            if row_title in shares_facts:
                                unit_multiplier = shares_unit_multiplier
                            else:
                                unit_multiplier = 1 
                            if "nump" in cell.get("class"):
                                values[column_counter] = value * unit_multiplier
                            else:
                                values[column_counter] = -value * unit_multiplier
                        column_counter += 1
                    elif value:
                        value = float(value)
                        if "nump" in cell.get("class"):
                            values[column_counter] = value * unit_multiplier
                        else:
                            values[column_counter] = -value * unit_multiplier
                        column_counter += 1
                    else:
                        pass # it is a title row
                values_set.append(values)
                unit_multiplier_set.append(unit_multiplier)
        return columns, values_set, dates, rows_that_are_sum, text_set, sections_dict



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
        # print("testttttttt")
        # print(values_set)
        # print(transposed_values_set)
        df = pd.DataFrame(transposed_values_set, columns=columns, index=index_dates)
        # ensure that data is displayed as float
        pd.set_option('display.float_format', '{:.2f}'.format)
        return df
    

    def process_one_statement(self, statement_name):
        """
        Processes a single financial statement identified by ticker, accession number, and statement name.
        Args:
            accession_number (str): The SEC accession number.
            statement_name (str): Name of the financial statement.
        Returns:
            pd.DataFrame or None: DataFrame of the processed statement or None if an error occurs.
        """
        try:
            # Fetch the statement HTML soup
            soup = self.get_statement_file_soup(statement_name)
        except Exception as e:
            logging.error(f"Failed to get statement soup: {e} for accession number: {self.accession_number}")
            return None
        if soup:
            try:
                # Extract data and create DataFrame
                columns, values, dates, rows_that_are_sum, rows_text, sections_dict = self.extract_columns_values_and_dates_from_statement(
                    soup, statement_name,
                )
                df = self.create_dataframe_of_statement_values_columns_dates(values, columns, dates)

                if not df.empty:
                    # Remove duplicate columns
                    df = df.drop_duplicates()
                    df = df.T
                    pass
                else:
                    logging.warning(f"Empty DataFrame for accession number: {self.accession_number}")
                    return None
                
                # TODO remove the check for 3 columns
                # if len(df.columns) > 3:
                #     # Select the last 3 columns
                #     last_three_columns = df.iloc[:, -3:]
                #     df = last_three_columns
                df = df.round(2)
                if statement_name == 'income_statement':
                    self.income_statement = IncomeStatement(df, rows_that_are_sum, rows_text, self.xml_equations, sections_dict)
                elif statement_name == 'balance_sheet':
                    self.balance_sheet = BalanceSheet(df, rows_that_are_sum, rows_text, self.xml_equations, sections_dict)
                elif statement_name == 'cash_flow_statement':
                    self.cash_flow = CashFlow(df, rows_that_are_sum, rows_text, self.xml_equations, sections_dict)
            except Exception as e:
                logging.error(f"Error processing statement: {e}")

            




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