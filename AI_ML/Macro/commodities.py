import requests
import pandas as pd
import plotly.graph_objects as go
from io import StringIO  # Import StringIO
import json


# URL of the page to scrape
url = "https://tradingeconomics.com/commodities"

# Headers to make the request look like it's from a real browser
headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
}

# Make a GET request with headers
response = requests.get(url, headers=headers)

# Use pandas to read tables from the response content
commodities = pd.read_html(StringIO(response.text))
# print(commodities)

# Declare columns we will drop from each commodity dataframe
columns = ['Date']

# Create dataframes
energy=commodities[0].drop(columns=columns)
metals=commodities[1].drop(columns=columns)
agricultural=commodities[2].drop(columns=columns)
industrial=commodities[3].drop(columns=columns)
livestock=commodities[4].drop(columns=columns)
commodities_index=commodities[5].drop(columns=columns)

# print(energy.to_json(orient='records'))
# print(metals.to_json(orient='records'))
# Convert to JSON, then parse it into Python objects before dumping
energy_json = json.loads(energy.to_json(orient='records'))
metals_json = json.loads(metals.to_json(orient='records'))
agricultural_json = json.loads(agricultural.to_json(orient='records'))
industrial_json = json.loads(industrial.to_json(orient='records'))
livestock_json = json.loads(livestock.to_json(orient='records'))
commodities_index_json = json.loads(commodities_index.to_json(orient='records'))

# Now dump the final JSON
print(json.dumps([energy_json, metals_json, agricultural_json, industrial_json, livestock_json, commodities_index_json], indent=2))
# print(json.dumps([energy.to_json(orient='records'), metals.to_json(orient='records')]))


# Create functions to display dataframes in plotly format

def get_energy():
    energy_table = go.Figure(data=[go.Table(
    header=dict(values=list(energy.columns),
                fill_color='lightgoldenrodyellow',
                align='left'),
    cells=dict(values=[energy[col] for col in energy.columns],
               fill_color='white',
               align='left'))
])
    return (energy_table)

def get_metals():
    metals_table = go.Figure(data=[go.Table(
    header=dict(values=list(metals.columns),
                fill_color='gold',
                align='left'),
    cells=dict(values=[metals[col] for col in metals.columns],
               fill_color='white',
               align='left'))
])
    return (metals_table)

def get_agricultural():
    agricultural_table = go.Figure(data=[go.Table(
    header=dict(values=list(agricultural.columns),
                fill_color='mediumseagreen',
                align='left'),
    cells=dict(values=[agricultural[col] for col in agricultural.columns],
               fill_color='white',
               align='left'))
])
    return (agricultural_table)

def get_livestock():
    livestock_table = go.Figure(data=[go.Table(
    header=dict(values=list(livestock.columns),
                fill_color='firebrick',
                align='left'),
    cells=dict(values=[livestock[col] for col in livestock.columns],
               fill_color='white',
               align='left'))
])
    return (livestock_table)

def get_industrial():
    industrial_table = go.Figure(data=[go.Table(
    header=dict(values=list(industrial.columns),
                fill_color='gray',
                align='left'),
    cells=dict(values=[industrial[col] for col in industrial.columns],
               fill_color='white',
               align='left'))
])
    return (industrial_table)

def get_index():
    index_table = go.Figure(data=[go.Table(
    header=dict(values=list(commodities_index.columns),
                fill_color='mediumorchid',
                align='left'),
    cells=dict(values=[commodities_index[col] for col in commodities_index.columns],
               fill_color='white',
               align='left'))
])
    return (index_table)

