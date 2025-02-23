# # Daily and Yearly Sector Performances
# 
# The visualization illustrates the daily percentage gain or loss in each of the 10 distinct sectors of the economy.


# Import notebook libraries and dependencies
import os
import requests
import pandas as pd
import numpy as np
import plotly.express as px
import alpha_vantage as av
from alpha_vantage.sectors import SectorPerformances # degraded


# Set API key
av_api_key = "SX41SKXRRMA9Q01U"


# Retreive sector performances
sp = SectorPerformances(key=av_api_key, output_format='pandas')
data, meta_data = sp.get_sector()
percent_data = data.mul(100, axis=1)


# Create daily performances function
def get_sector_performance_vis():
    sector_performance_vis = px.bar(percent_data, y='Rank B: Day Performance', x=percent_data.index, text='Rank B: Day Performance', title='Daily Performance per Sector (%)')
    sector_performance_vis.update_traces(texttemplate='%{text:.2s}', textposition='inside')
    sector_performance_vis.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')
    return(sector_performance_vis)


# Create yearly performances function
def get_sector_performance_vis2():
    sector_performance_vis2 = px.bar(percent_data, y='Rank G: Year Performance', x=percent_data.index, text='Rank G: Year Performance', title='Yearly Performance per Sector (%)')
    sector_performance_vis2.update_traces(texttemplate='%{text:.2s}', textposition='inside')
    sector_performance_vis2.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')
    return(sector_performance_vis2)


print(get_sector_performance_vis())
print(get_sector_performance_vis2())