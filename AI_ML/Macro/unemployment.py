# # Unemployment
# 
# The results are updated monthly by The Federal Reserve. 

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
unrate = fred.get_series_latest_release('UNRATE')
unrate = pd.DataFrame(unrate)
unrate.columns=['Unemployment Rate']
unrate.index = pd.to_datetime(unrate.index)
unrate.index.name = 'Date'
#unrate


def get_unrate_vis():
    unrate_vis = px.line(unrate, x=unrate.index, y="Unemployment Rate", title='U.S. Unemployment Rate')
    unrate_vis.update_xaxes(
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
    return(unrate_vis)

