import os
import pandas as pd

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