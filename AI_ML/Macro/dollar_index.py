# # Dollar Index
# 
# This chart tracks the U.S. dollar index. The Intercontinental Exchange's index is currently calculated by factoring in the exchange rates of six major world currencies, which include the Euro (EUR), Japanese yen (JPY), Canadian dollar (CAD), British pound (GBP), Swedish krona (SEK), and Swiss franc (CHF). 

# Import notebook libraries and dependencies
import os
import requests
import pandas as pd
import numpy as np
import plotly.express as px
import yfinance as yf


# Retreive data
ticker = "DX-Y.NYB"
dollar_index = yf.download(f'{ticker}', progress = False)
print(dollar_index)
#dollar_index.tail()

def get_dollar_index_vis():
    dollar_index_vis = px.line(data_frame=dollar_index, y=dollar_index[("Close", ticker)], x=dollar_index.index, title='Daily Close Price of U.S. Dollar Index')
    dollar_index_vis.update_xaxes(
        rangeslider_visible=True,
        rangeselector=dict(
            buttons=list([
                dict(count=1, label="1m", step="month", stepmode="backward"),
                dict(count=6, label="6m", step="month", stepmode="backward"),
                dict(count=1, label="YTD", step="year", stepmode="todate"),
                dict(count=1, label="1y", step="year", stepmode="backward"),
                dict(step="all")
            ])
        )
    )
    return(dollar_index_vis)

