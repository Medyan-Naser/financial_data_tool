# panel serve dashboard.py 

import panel as pn
import plotly.graph_objects as go
from get_stock_prices import *
from stock_ml_model import *
from predict_volatility import *

pn.extension('plotly')

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
CHARLES. For a home recommendation based on location and price of interest, click the Real Estate tab.
"""
)

# Ticker input widget
ticker_widget = pn.widgets.TextInput(name="Enter Ticker Symbol", value="AAPL")

# Function to update the dashboard based on the ticker input
@pn.depends(ticker_widget, watch=True)
def update_dashboard(ticker):
    ticker_60 = get_60d_df(ticker)

    # Fetch ML model results
    model_evaluation, ml_plot, forecast_plot, loss_plot = get_ml_model(ticker)

    # Generate index charts
    spy_index = go_generate_index_chart("SPY")
    djia_index = go_generate_index_chart("DJIA")
    ndaq_index = go_generate_index_chart("NDAQ")
    iwm_index = go_generate_index_chart("IWM")

    # Predict volatility
    returns_plot_SPY, model_summary_SPY, rolling_volatility_plot_SPY, forecast_plot_SPY = predict_volatility("SPY")
    returns_plot_DJIA, model_summary_DJIA, rolling_volatility_plot_DJIA, forecast_plot_DJIA = predict_volatility("DJIA")
    returns_plot_NDAQ, model_summary_NDAQ, rolling_volatility_plot_NDAQ, forecast_plot_NDAQ = predict_volatility("NDAQ")
    returns_plot_IWM, model_summary_IWM, rolling_volatility_plot_IWM, forecast_plot_IWM = predict_volatility("IWM")

    # Create rows for the dashboard
    ai_row1 = pn.Row(spy_index, forecast_plot_SPY)
    ai_row2 = pn.Row(djia_index, forecast_plot_DJIA)
    ai_row3 = pn.Row(ndaq_index, forecast_plot_NDAQ)
    ai_row4 = pn.Row(iwm_index, forecast_plot_IWM)
    ai_row5 = pn.Row(max_linechart_ticker(ticker), forecast_plot)

    # Update tabs
    print(tabs)
    print(pn.Column(ai_row1, ai_row2, ai_row3, ai_row4, ai_row5))
    tabs[3] =("AI", pn.Column(ai_row1, ai_row2, ai_row3, ai_row4, ai_row5))

# Create a tab layout for the dashboard
tabs = pn.Tabs(
    ("Welcome", pn.Column(welcome)),
    ("Macro", pn.Column()),
    ("Micro", pn.Column()),
    ("AI", pn.Column())  # Initially empty, will be updated
)

# Create the main dashboard layout
dashboard = pn.Column(pn.Row(title), pn.Row(ticker_widget), tabs, width=900)

# Serve the dashboard
dashboard.servable()
