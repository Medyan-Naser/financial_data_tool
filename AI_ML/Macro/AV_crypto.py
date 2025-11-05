
# Import notebook libraries and dependencies
import os
import requests
import pandas as pd
import numpy as np
import plotly.express as px
from alpha_vantage.cryptocurrencies import CryptoCurrencies

av_api_key = "SX41SKXRRMA9Q01U"

def get_btc_vis():
    """
    Get Bitcoin price visualization.
    """
    try:
        cc = CryptoCurrencies(key=av_api_key, output_format='pandas')
        data, meta_data = cc.get_digital_currency_daily(symbol='BTC', market='CNY')
        btc = data
        
        if btc.empty or '4b. close (USD)' not in btc.columns:
            # Return figure with empty trace so frontend can handle it
            import plotly.graph_objects as go
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=[], y=[], mode='lines', name='Bitcoin'))
            fig.update_layout(title='Daily Close Price of Bitcoin (USD)')
            return fig
        
        btc_vis = px.line(
            data_frame=btc, 
            y='4b. close (USD)', 
            x=btc.index, 
            title='Daily Close Price of Bitcoin (USD)'
        )
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
        return btc_vis
    except Exception as e:
        print(f"Error fetching Bitcoin data: {e}")
        import plotly.graph_objects as go
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=[], y=[], mode='lines', name='Bitcoin'))
        fig.update_layout(title='Daily Close Price of Bitcoin (USD)')
        return fig


def get_eth_vis():
    """
    Get Ethereum price visualization.
    """
    try:
        cc = CryptoCurrencies(key=av_api_key, output_format='pandas')
        data, meta_data = cc.get_digital_currency_daily(symbol='ETH', market='CNY')
        eth = data
        
        if eth.empty or '4b. close (USD)' not in eth.columns:
            # Return figure with empty trace so frontend can handle it
            import plotly.graph_objects as go
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=[], y=[], mode='lines', name='Ethereum'))
            fig.update_layout(title='Daily Close Price of Ethereum (USD)')
            return fig
        
        eth_vis = px.line(
            data_frame=eth, 
            y='4b. close (USD)', 
            x=eth.index, 
            title='Daily Close Price of Ethereum (USD)'
        )
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
        return eth_vis
    except Exception as e:
        print(f"Error fetching Ethereum data: {e}")
        import plotly.graph_objects as go
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=[], y=[], mode='lines', name='Ethereum'))
        fig.update_layout(title='Daily Close Price of Ethereum (USD)')
        return fig
