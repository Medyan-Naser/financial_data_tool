# Import notebook libraries and dependencies
import os
import requests
import pandas as pd
import numpy as np
import plotly.express as px
from fredapi import Fred

fred_api_key = "69db3b36e2b3bf578e036a5f42d9b315"

#Initiate response
fred = Fred(api_key=fred_api_key)

# Retrieve Federal Reserve data
debt_to_gdp = fred.get_series_latest_release('GFDEGDQ188S')
debt_to_gdp = pd.DataFrame(debt_to_gdp)
debt_to_gdp.columns=['Debt/GDP Ratio']
debt_to_gdp.index = pd.to_datetime(debt_to_gdp.index)
debt_to_gdp.index.name = 'Date'
#debt_to_gdp


def get_debt_to_gdp_vis():    
    debt_to_gdp_vis = px.line(debt_to_gdp, x=debt_to_gdp.index, y="Debt/GDP Ratio", title='U.S. Debt to GDP Ratio')
    debt_to_gdp_vis.update_xaxes(
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
    return(debt_to_gdp_vis)

print(debt_to_gdp)
print(get_debt_to_gdp_vis())




