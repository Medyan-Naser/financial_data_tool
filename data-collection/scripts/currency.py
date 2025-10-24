from headers import *
from constants import *
from healpers import *
from collections import Counter
import logging

logger = logging.getLogger(__name__)


def check_for_two_currency(text):
    """
    Check if text contains references to multiple currencies.
    
    Args:
        text: Text to check for currency references
    
    Returns:
        bool: True if multiple currencies found, False otherwise
    """
    if not text or not isinstance(text, str):
        return False
    
    num_of_currencies = 0
    for currency, currency_sign in currency_map.items():
        if currency in text or currency_sign in text:
            num_of_currencies += 1
    
    if num_of_currencies > 1:
        logger.info(f"Multiple currencies detected in text: {text[:50]}...")
        return True
    return False

def extract_currency(text):
    """
    Extract currency code from text.
    
    Args:
        text: Text containing currency reference
    
    Returns:
        str: Currency code (e.g., 'USD', 'EUR') or None if not found
    """
    if not text or not isinstance(text, str):
        return None
    
    for currency, currency_sign in currency_map.items():
        if currency in text or currency_sign in text:
            return currency
    
    logger.debug(f"No currency found in text: {text[:50]}...")
    return None

def get_most_frequent_currency(currencies):
    """
    Get the most frequently occurring currency from a list.
    
    Args:
        currencies: List of currency codes
    
    Returns:
        str: Most frequent currency code or None if empty list
    """
    if not currencies:
        logger.warning("Empty currency list provided")
        return None
    
    # Filter out None values
    valid_currencies = [c for c in currencies if c is not None]
    
    if not valid_currencies:
        logger.warning("No valid currencies in list")
        return None
    
    currency_count = Counter(valid_currencies)
    most_frequent = currency_count.most_common(1)[0]
    
    logger.info(f"Most frequent currency: {most_frequent[0]} (appears {most_frequent[1]} times)")
    return most_frequent[0]
