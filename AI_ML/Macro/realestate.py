# # Case-Shiller Home Price Index Ratio
# 
# This financial index roughly describes the value U.S. real estate.  


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
re = fred.get_series_latest_release('CSUSHPISA')
re = pd.DataFrame(re)
re.columns=['S&P/RE Ratio']
re.index = pd.to_datetime(re.index)
re.index.name = 'Date'

def get_re_vis():
    re_vis = px.line(re, x=re.index, y="S&P/RE Ratio", title='Cape-Shiller Home Price Index')
    re_vis.update_xaxes(
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
    return(re_vis)


