# Run the files so we can call the functions within
# Function names in the file are cateloged at the bottom of each cell

# panel serve dashboard.py 

import os
import time
import panel as pn
pn.extension('plotly')
from AI.get_stock_prices import *
from AI.stock_ml_model import *
from AI.predict_volatility import *

from Macro.commodities import *
from Macro.core_cpi_yoy_inflation import *
from Macro.currencies import *
from Macro.debt_to_gdp import *
from Macro.dollar_index import *
from Macro.global_bonds import *
from Macro.realestate import *
from Macro.unemployment import *
from Macro.velocity import *


fred_api_key = "69db3b36e2b3bf578e036a5f42d9b315"
av_api_key = "SX41SKXRRMA9Q01U"

# ticker = "AAPL"


# Create a Title for the Dashboard
title = pn.pane.Markdown(
    """
# Financial Analysis Tool
""",
    width=800,
)

welcome = pn.pane.Markdown(
    """
### 
This dashboard presents tools to support a variety of financial analysis techniques.
If you'd like to see a high-level overview of the economy, click the Macro tab. For a granular focus of stocks, click the Micro tab.
For a home recommendation based on location and price of interest, click the Real Estate tab.
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
    tabs[2] =("AI", pn.Column(ai_row1, ai_row2, ai_row3, ai_row4, ai_row5))



# Configure layout
# macrorow1 = pn.Row(get_table()) #get_yield_curve_vis()
macrorow2 = pn.Row(get_inflation_vis(), get_debt_to_gdp_vis())
macrorow3 = pn.Row(get_dollar_index_vis(),get_velocity_vis())
# macrorow4 = pn.Row(get_btc_vis(), get_eth_vis())
macrorow5 = pn.Row(get_unrate_vis(), get_re_vis())
# macrorow6 = pn.Row(get_sector_performance_vis(),get_sector_performance_vis2())
macrorow7 = pn.Row(get_energy(), get_metals())
macrorow8 = pn.Row(get_agricultural(), get_livestock())
macrorow9 = pn.Row(get_industrial(), get_index())
macrorow10 = pn.Row(get_major_10y(), get_europe_bonds()) 
macrorow11 = pn.Row(get_america_bonds(), get_asia_bonds())
macrorow12 = pn.Row(get_australia_bonds(), get_africa_bonds())
macrorow13 = pn.Row(get_major_currencies())



# Create a tab layout for the dashboard
tabs = pn.Tabs(
    ("Welcome", pn.Column(welcome)),
    ("Macro", pn.Column(macrorow2, macrorow3, macrorow5,macrorow7, macrorow8, macrorow9, macrorow10, macrorow11, macrorow12, macrorow13)),
    # ("Micro", pn.Column(microrow1, microrow2, microrow3, microrow4, microrow5, microrow6)),
    ("AI", pn.Column()) # ai_row1, ai_row2, ai_row3, ai_row4, ai_row5
 )

# Create the main dashboard layout
dashboard = pn.Column(pn.Row(title), pn.Row(ticker_widget), tabs, width=900)

# Serve the dashboard
dashboard.servable()





