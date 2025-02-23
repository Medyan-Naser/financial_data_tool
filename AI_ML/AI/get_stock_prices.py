


import pandas as pd
import numpy as np
import yfinance as yf
import plotly.express as px
import plotly.graph_objs as go


time_periods = ["1d","5d","1mo","60d","3mo","6mo","1y","2y","5y","10y","ytd","max"]
valid_intervals= ["1m","2m","2m","2m","1h","1h","1h","1h","1d","1d","1d","1d"]


# 

# ticker = "AAPL"
#idx = -1



def interval_to_df(ticker, time_periods, valid_intervals):
    df = yf.download(
        ticker,
        period = time_periods,
        interval = valid_intervals,
        progress = False
    )
    df = pd.DataFrame(df["Close"])
    df.index = pd.to_datetime(df.index)
    df = df.rename(columns = {ticker : "Close"})
    df.index.rename("Date", inplace = True)
    df["Returns"] = 100*df["Close"].pct_change()
    df["Color"] = np.where(df["Returns"]<0, "red", "green")
    return df




def max_interval_to_df(ticker):
    ticker_data = yf.download(
        ticker,
        period = "max",
        interval = "1d",
        progress = False
    )
    ticker_close = pd.DataFrame(ticker_data["Close"])
    ticker_close.index = pd.to_datetime(ticker_close.index)
    ticker_close = ticker_close.rename(columns = {ticker: "Close"})
    ticker_close.index.rename("Date", inplace = True)
    return ticker_close



def df_go_to_barchart_30d(ticker, df):
    fig = go.Figure()
    fig.add_trace(
        go.Bar(name = ticker,
               x = df.index,
               y = df["Returns"],
               marker_color = df["Color"],
               text = df["Close"]
              )
    )
    fig.update_xaxes(
        rangeslider_visible=True
    )
    fig.update_layout(barmode="stack",
                      title_text = ticker,
                      xaxis = dict(title_text = "Last 30 Days"),
                      yaxis = dict(title_text = 'Percent Change (%)')
                     )
    return fig




def max_linechart_ticker(ticker):
    ticker_plot = px.line(
        max_interval_to_df(ticker),
        x = max_interval_to_df(ticker).index ,
        y = "Close",
        title = ticker,
        labels = {"Close":"Price ($)", "Date":"Time"}
    )
    ticker_plot.update_xaxes(
        rangeslider_visible=True,
        rangeselector=dict(
            buttons=list([
                dict(count=1, label="1d", step="day", stepmode="backward"),
                dict(count=5, label="5d", step="day", stepmode="backward"),
                dict(count=1, label="1m", step="month", stepmode="backward"),
                dict(count=2, label="2m", step="month", stepmode="backward"),
                dict(count=3, label="3m", step="month", stepmode="backward"),
                dict(count=6, label="6m", step="month", stepmode="backward"),
                dict(count=1, label="YTD", step="year", stepmode="todate"),
                dict(count=1, label="1y", step="year", stepmode="backward"),
                dict(count=2, label="2y", step="year", stepmode="backward"),
                dict(count=5, label="5y", step="year", stepmode="backward"),
                dict(count=10, label="10y", step="year", stepmode="backward"),
                dict(step="all")
            ])
        )
    )
    return ticker_plot




def chart_line_ticker(ticker, time_periods, valid_intervals):
    ticker_plot = px.line(
        interval_to_df(ticker, time_periods, valid_intervals),
        x = interval_to_df(ticker, time_periods, valid_intervals).index ,
        y = "Close",
        title = ticker,
        labels = {"Close":"Price ($)", "Date":"Time"}
    )
    ticker_plot.update_xaxes(
        rangeslider_visible=True,
        rangeselector=dict(
            buttons=list([
                dict(count=1, label="1d", step="day", stepmode="backward"),
                dict(count=5, label="5d", step="day", stepmode="backward"),
                dict(count=1, label="1m", step="month", stepmode="backward"),
                dict(count=2, label="2m", step="month", stepmode="backward"),
                dict(count=3, label="3m", step="month", stepmode="backward"),
                dict(count=6, label="6m", step="month", stepmode="backward"),
                dict(count=1, label="YTD", step="year", stepmode="todate"),
                dict(count=1, label="1y", step="year", stepmode="backward"),
                dict(count=2, label="2y", step="year", stepmode="backward"),
                dict(count=5, label="5y", step="year", stepmode="backward"),
                dict(count=10, label="10y", step="year", stepmode="backward"),
                dict(step="all")
            ])
        )
    )
    return ticker_plot



def bar_chart_ticker(ticker, time_periods, valid_intervals):
    ticker_plot = px.bar(
        interval_to_df(ticker, time_periods, valid_intervals),
        x = interval_to_df(ticker, time_periods, valid_intervals).index ,
        y = "Close",
        title = ticker,
        labels = {"Close":"Price ($)", "Date":"Time"}
    )
    '''
    ticker_plot.update_xaxes(
        rangeslider_visible=True,
        rangeselector=dict(
            buttons=list([
                dict(count=1, label="1d", step="day", stepmode="backward"),
                dict(count=5, label="5d", step="day", stepmode="backward"),
                dict(count=10, label="10d", step="day", stepmode="backward"),
                dict(count=30, label="30d", step="day", stepmode="backward"),
                dict(count=3, label="3m", step="month", stepmode="backward"),
                dict(count=6, label="6m", step="month", stepmode="backward"),
                dict(count=1, label="YTD", step="year", stepmode="todate")
            ])
        )
    )
    '''
    ticker_plot.update_layout(barmode="relative")
    return ticker_plot



def get_60d_df(ticker):
    return interval_to_df(ticker, "60d", "2m")


# spy_60 = get_60d_df("SPY")
# print(spy_60)


