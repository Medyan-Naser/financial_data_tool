# # Velocity of M2 Money Supply
# 
# The results will not be up to date since The Federal Reserve does not frequently update their data.  While it's not real-time data, it is the "Official" figure.

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
velocity = fred.get_series_latest_release('M2V')
velocity = pd.DataFrame(velocity)
velocity.columns=['Velocity']
velocity.index = pd.to_datetime(velocity.index)
velocity.index.name = 'Date'

def get_velocity_vis():
    velocity_vis = px.line(velocity, x=velocity.index, y="Velocity", title='Velocity of M2 Money Supply')
    velocity_vis.update_xaxes(
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
    return(velocity_vis)

