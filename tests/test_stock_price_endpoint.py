"""
Test the stock price backend endpoint

Comprehensive test suite for stock price API endpoints including:
- Historical prices with various periods
- Real-time quotes
- Combined data endpoint
- Error handling for invalid tickers
- Response structure validation
- Edge cases and boundary conditions
"""

import requests
import json
import sys
import pytest

BASE_URL = "http://localhost:8000"
TEST_TICKER = "AAPL"
ALT_TICKER = "MSFT"
INVALID_TICKER = "INVALIDTICKER12345"

