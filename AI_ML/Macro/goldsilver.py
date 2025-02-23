# Import notebook libraries and dependencies
import os
import requests
import pandas as pd
import numpy as np
import plotly.express as px
import alpha_vantage as av
from alpha_vantage.foreignexchange import ForeignExchange
import yfinance as yf
from fredapi import Fred
import panel as pn

#Set API keys
os.environ["ALPHA_VANTAGE_API_KEY"] = "SX41SKXRRMA9Q01U"
os.environ["FRED_API_KEY"] = "69db3b36e2b3bf578e036a5f42d9b315"
av_api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
fred_api_key = os.getenv("FRED_API_KEY")

# Retreive Gold/USD exchange rate 
fe = ForeignExchange(key=av_api_key)
print(dir(fe))
data, _ = fe.get_currency_exchange_rate(from_currency='EUR',to_currency='USD')
data['5. Exchange Rate']=pd.to_numeric(data['5. Exchange Rate'],errors='coerce')
gold_price = round(data['5. Exchange Rate'],2)
#print(f"The Price of Gold is: ${gold_price}")


# Retreive Silver/USD exchange rate 
fe = ForeignExchange(key=av_api_key)
data, _ = fe.get_currency_exchange_rate(from_currency='CAD',to_currency='USD')
data['5. Exchange Rate']=pd.to_numeric(data['5. Exchange Rate'],errors='coerce')
silver_price = round(data['5. Exchange Rate'],2)
#print(f"The Price of Silver is: ${silver_price}")

# Calculate Gold/Silver Ratio
goldsilver_ratio = round(gold_price/silver_price,2)

# Retreive Dow Jones Industrial Average and 
ticker = "^DJI"
ticker = "AAPL"
ticker_data = yf.download(
    f'{ticker}', 
    period = "1d",
    interval = "1m",
    progress = False)
# ticker_data = yf.download("MSFT", start="2022-01-01", end="2022-12-31")
print(ticker_data)
djia=ticker_data['Close'].iloc[-1]
dowgold_ratio=round(djia/gold_price,2)
#print(f"The Dow/Gold ratio is: {dowgold_ratio}")


#Initiate response
fred = Fred(api_key=fred_api_key)

# Retrieve Federal Reserve data
re = fred.get_series_latest_release('MSPUS')
re = pd.DataFrame(re)
re.columns=['Single Family Home Price']
re.index = pd.to_datetime(re.index)
re.index.name = 'Date'
last_re_price = re.iloc[-1]

# Calculate RE/Gold ratio
re_gold_ratio = last_re_price/gold_price
#print(re_gold_ratio)


# Retrieve monetary base data
money = fred.get_series_latest_release('BOGMBASE')
money = pd.DataFrame(money)
print(money)
money.columns=['Monetary Base']
money.index = pd.to_datetime(money.index)
money.index.name = 'Date'
monetary_base_billions = round(money.iloc[-1]/1000,2)

# Calculate Gold/Monetary Base ratio
gold_base_ratio = gold_price/monetary_base_billions

def get_table():   
    import plotly.graph_objects as go

    table = go.Figure(data=[go.Table(header=dict(values=['Metrics', 'Values']),
                     cells=dict(values=[['Gold Spot', 'Silver Spot', 'Gold/Silver Ratio', 'Dow/Gold Ratio', "Real Estate/Gold Ratio", "Gold/Monetary Base Ratio"], 
                                        [gold_price, silver_price, goldsilver_ratio, dowgold_ratio, round(re_gold_ratio, 2), round(gold_base_ratio,2)]]))
                         ])
    return(table)

table = get_table()
print(table)

# Configure layout
macrorow1 = pn.Row(get_table()) #get_yield_curve_vis()



# Create a Title for the Dashboard
title = pn.pane.Markdown(
    """
# The Financial Analyst's Swiss Army Knife
""",
    width=800,
)

welcome = pn.pane.Markdown(
    """
### Hello Analysts!
This dashboard presents tools to support a variety of financial analysis techniques.
If you'd like to see a high-level overview of the economy, click the Macro tab. For a granular focus of stocks, click the Micro tab.
If you'd like to see a prediction of stock market prices and volatility, click the AI tab.
"""
)

# Create a tab layout for the dashboard
tabs = pn.Tabs(
    ("Welcome", pn.Column(welcome)),
    ("Macro", pn.Column(macrorow1))
 )

dashboard = pn.Column(pn.Row(title), tabs, width=900)


dashboard.servable()