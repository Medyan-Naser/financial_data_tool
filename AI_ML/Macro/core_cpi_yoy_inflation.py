
# Import notebook libraries and dependencies
import os
import requests
import pandas as pd
import numpy as np
import plotly.express as px
from fredapi import Fred


#Set API keys
fred_api_key = "69db3b36e2b3bf578e036a5f42d9b315"


#Initiate response
fred = Fred(api_key=fred_api_key)

# Retrieve Federal Reserve data
inflation = fred.get_series_latest_release('CPILFESL')
inflation = pd.DataFrame(inflation)
inflation.columns=['Inflation']
inflation.index = pd.to_datetime(inflation.index)
inflation.index.name = 'Date'
#inflation


def get_inflation_vis():
    inflation_vis = px.line(inflation, x=inflation.index, y="Inflation", title='The FEDs Inflation Statistic')
    inflation_vis.update_xaxes(
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
    return(inflation_vis)



