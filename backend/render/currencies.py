import requests
import pandas as pd
import plotly.graph_objects as go
import json
from io import StringIO  # Import StringIO


# URL of the page to scrape
url = "https://tradingeconomics.com/currencies"


# Headers to make the request look like it's from a real browser
headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
}

# Make a GET request with headers
response = requests.get(url, headers=headers)

# Use pandas to read tables from the response content
# print(response.text)
currencies = pd.read_html(StringIO(response.text))
# print(currencies)


# Declare columns we will drop from each commodity dataframe
columns = ['Unnamed: 0', 'Date']

# Create dataframes
major_currencies=currencies[0].drop(columns=columns)
print(major_currencies.to_json(orient='records'))

# print(major_currencies)
# Create functions to display dataframes in plotly format

def get_major_currencies():
    major_currencies_table = go.Figure(data=[go.Table(
    header=dict(values=list(major_currencies.columns),
                fill_color='lightgreen',
                align='left'),
    cells=dict(values=[major_currencies.Major, major_currencies.Price, major_currencies.Day, major_currencies.Weekly, major_currencies.Monthly, major_currencies.YoY],
               fill_color='white',
               align='left'))
])
    
    return (major_currencies_table)

# print(get_major_currencies())