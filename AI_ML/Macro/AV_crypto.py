
# Import notebook libraries and dependencies
import os
import requests
import pandas as pd
import numpy as np
import plotly.express as px
import alpha_vantage as av
from alpha_vantage.cryptocurrencies import CryptoCurrencies

av_api_key = "SX41SKXRRMA9Q01U"

cc = CryptoCurrencies(key=av_api_key, output_format='pandas')
data, meta_data = cc.get_digital_currency_daily(symbol='BTC', market='CNY')
btc = data


def get_btc_vis():
    btc_vis = px.line(data_frame=btc, y='4b. close (USD)', x=btc.index, title='Daily Close Price of Bitcoin (USD)')
    btc_vis.update_xaxes(
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
    return(btc_vis)



# Retreive ETH daily prices
cc = CryptoCurrencies(key=av_api_key, output_format='pandas')
data, meta_data = cc.get_digital_currency_daily(symbol='ETH', market='CNY')
eth = data


def get_eth_vis():   
    eth_vis = px.line(data_frame=eth, y='4b. close (USD)', x=eth.index, title='Daily Close Price of Ethereum (USD)')
    eth_vis.update_xaxes(
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
    return(eth_vis)



