
from get_stock_prices import *
from stock_ml_model import *
from predict_volatility import *
import json
from plotly.utils import PlotlyJSONEncoder


ticker="AAPL"

# ticker_60 = get_60d_df(ticker)

# print(ticker_60)
# Fetch ML model results

model_evaluation, ml_plot, forecast_plot, loss_plot, forecast_df = get_ml_model(ticker)

# Generate index charts
spy_index = go_generate_index_chart("SPY")
# djia_index = go_generate_index_chart("DJIA")
# ndaq_index = go_generate_index_chart("NDAQ")
# iwm_index = go_generate_index_chart("IWM")

# Predict volatility
returns_plot_SPY, model_summary_SPY, rolling_volatility_plot_SPY, forecast_plot_SPY = predict_volatility("SPY")
# returns_plot_DJIA, model_summary_DJIA, rolling_volatility_plot_DJIA, forecast_plot_DJIA = predict_volatility("DJIA")
# returns_plot_NDAQ, model_summary_NDAQ, rolling_volatility_plot_NDAQ, forecast_plot_NDAQ = predict_volatility("NDAQ")
# returns_plot_IWM, model_summary_IWM, rolling_volatility_plot_IWM, forecast_plot_IWM = predict_volatility("IWM")

# print(forecast_df.to_json(orient='records'))
forecast_plot_json = json.loads(forecast_plot.to_json())
spy_index_json = json.loads(spy_index.to_json())
returns_plot_SPY_json = json.loads(returns_plot_SPY.to_json())
rolling_volatility_plot_SPY_json = json.loads(rolling_volatility_plot_SPY.to_json())
forecast_plot_SPY_json = json.loads(forecast_plot_SPY.to_json())

print(json.dumps([forecast_plot_json, spy_index_json, returns_plot_SPY_json, rolling_volatility_plot_SPY_json, forecast_plot_SPY_json], indent=2))

# print(forecast_df, forecast_plot)
# print(json.dumps(obj=forecast_plot, cls=PlotlyJSONEncoder))