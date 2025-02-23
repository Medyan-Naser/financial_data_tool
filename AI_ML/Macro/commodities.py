
import requests
import pandas as pd
import plotly.graph_objects as go


# URL of the page to scrape
url = "https://tradingeconomics.com/commodities"

# Headers to make the request look like it's from a real browser
headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
}

# Make a GET request with headers
response = requests.get(url, headers=headers)

# Use pandas to read tables from the response content
commodities = pd.read_html(response.text)
print(commodities)

# Declare columns we will drop from each commodity dataframe
columns = ['Date']

# Create dataframes
energy=commodities[0].drop(columns=columns)
metals=commodities[1].drop(columns=columns)
agricultural=commodities[2].drop(columns=columns)
livestock=commodities[3].drop(columns=columns)
industrial=commodities[4].drop(columns=columns)
commodities_index=commodities[5].drop(columns=columns)


# Create functions to display dataframes in plotly format

def get_energy():
    energy_table = go.Figure(data=[go.Table(
    header=dict(values=list(energy.columns),
                fill_color='lightgoldenrodyellow',
                align='left'),
    cells=dict(values=[energy.Energy, energy.Price, energy.Day, energy.Weekly, energy.Monthly, energy.YoY],
               fill_color='white',
               align='left'))
])
    return (energy_table)

def get_metals():
    metals_table = go.Figure(data=[go.Table(
    header=dict(values=list(metals.columns),
                fill_color='gold',
                align='left'),
    cells=dict(values=[metals.Metals, metals.Price, metals.Day, metals.Weekly, metals.Monthly, metals.YoY],
               fill_color='white',
               align='left'))
])
    return (metals_table)

def get_agricultural():
    agricultural_table = go.Figure(data=[go.Table(
    header=dict(values=list(agricultural.columns),
                fill_color='mediumseagreen',
                align='left'),
    cells=dict(values=[agricultural.Agricultural, agricultural.Price, agricultural.Day, agricultural.Weekly, agricultural.Monthly, agricultural.YoY],
               fill_color='white',
               align='left'))
])
    return (agricultural_table)

def get_livestock():
    livestock_table = go.Figure(data=[go.Table(
    header=dict(values=list(livestock.columns),
                fill_color='firebrick',
                align='left'),
    cells=dict(values=[livestock.Livestock, livestock.Price, livestock.Day, livestock.Weekly, livestock.Monthly, livestock.YoY],
               fill_color='white',
               align='left'))
])
    return (livestock_table)

def get_industrial():
    industrial_table = go.Figure(data=[go.Table(
    header=dict(values=list(industrial.columns),
                fill_color='gray',
                align='left'),
    cells=dict(values=[industrial.Industrial, industrial.Price, industrial.Day, industrial.Weekly, industrial.Monthly, industrial.YoY],
               fill_color='white',
               align='left'))
])
    return (industrial_table)

def get_index():
    index_table = go.Figure(data=[go.Table(
    header=dict(values=list(commodities_index.columns),
                fill_color='mediumorchid',
                align='left'),
    cells=dict(values=[commodities_index.Index, commodities_index.Price, commodities_index.Day, commodities_index.Weekly, commodities_index.Monthly, commodities_index.YoY],
               fill_color='white',
               align='left'))
])
    return (index_table)



