import requests
import pandas as pd
import plotly.graph_objects as go


# URL of the page to scrape
url = "https://tradingeconomics.com/bonds"


# Headers to make the request look like it's from a real browser
headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
}

# Make a GET request with headers
response = requests.get(url, headers=headers)

# Use pandas to read tables from the response content
bonds = pd.read_html(response.text)

# Declare columns we will drop from each bond dataframe
columns = ['Unnamed: 0', 'Date']

# Create dataframes
major_10year = bonds[0].drop(columns=columns)
# major_10year.columns = ['Major', 'Yield', 'Day', 'Weekly', 'Monthly', 'YTD', 'Yearly']
europe_bonds = bonds[1].drop(columns=columns)
america_bonds = bonds[2].drop(columns=columns)
asia_bonds = bonds[3].drop(columns=columns)
australia_bonds = bonds[4].drop(columns=columns)
africa_bonds = bonds[5].drop(columns=columns)


# Create functions to display dataframes in plotly format

def get_major_10y():
    major_10y_table = go.Figure(data=[go.Table(
    header=dict(values=list(major_10year.columns),
                fill_color='tan',
                align='left'),
    cells=dict(values=[major_10year.Major10Y, major_10year.Yield, major_10year.Day, major_10year.Weekly, major_10year.Monthly, major_10year.YoY],
               fill_color='white',
               align='left'))
])
    return (major_10y_table)

def get_europe_bonds():
    europe_bonds_table = go.Figure(data=[go.Table(
    header=dict(values=list(europe_bonds.columns),
                fill_color='tan',
                align='left'),
    cells=dict(values=[europe_bonds.Europe, europe_bonds.Yield, europe_bonds.Day, europe_bonds.Weekly, europe_bonds.Monthly, europe_bonds.YoY],
               fill_color='white',
               align='left'))
])
    return (europe_bonds_table)

def get_america_bonds():
    america_bonds_table = go.Figure(data=[go.Table(
    header=dict(values=list(america_bonds.columns),
                fill_color='tan',
                align='left'),
    cells=dict(values=[america_bonds.America, america_bonds.Yield, america_bonds.Day, america_bonds.Weekly, america_bonds.Monthly, america_bonds.YoY],
               fill_color='white',
               align='left'))
])
    return (america_bonds_table)

def get_asia_bonds():
    asia_bonds_table = go.Figure(data=[go.Table(
    header=dict(values=list(asia_bonds.columns),
                fill_color='tan',
                align='left'),
    cells=dict(values=[asia_bonds.Asia, asia_bonds.Yield, asia_bonds.Day, asia_bonds.Weekly, asia_bonds.Monthly, asia_bonds.YoY],
               fill_color='white',
               align='left'))
])
    return (asia_bonds_table)

def get_australia_bonds():
    australia_bonds_table = go.Figure(data=[go.Table(
    header=dict(values=list(australia_bonds.columns),
                fill_color='tan',
                align='left'),
    cells=dict(values=[australia_bonds.Australia, australia_bonds.Yield, australia_bonds.Day, australia_bonds.Weekly, australia_bonds.Monthly, australia_bonds.YoY],
               fill_color='white',
               align='left'))
])
    return (australia_bonds_table)

def get_africa_bonds():
    africa_bonds_table = go.Figure(data=[go.Table(
    header=dict(values=list(africa_bonds.columns),
                fill_color='tan',
                align='left'),
    cells=dict(values=[africa_bonds.Africa, africa_bonds.Yield, africa_bonds.Day, africa_bonds.Weekly, africa_bonds.Monthly, africa_bonds.YoY],
               fill_color='white',
               align='left'))
])
    return (africa_bonds_table)


