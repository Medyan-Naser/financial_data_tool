from headers import *
from constants import *
from healpers import *
from collections import Counter # for currency check


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
    for currency, currency_sign in currency_map.items():
        if currency in text or currency_sign in text:
            return currency
    return None

def get_most_frequent_currency(currencies):
    # Get the most frequent currency from the list
    currency_count = Counter(currencies)
    most_frequent_currency = currency_count.most_common(1)[0][0]
    return most_frequent_currency
