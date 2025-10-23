import sys
import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import subprocess
import json
import numpy as np
import pandas as pd
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add AI_ML directory to path
AI_ML_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'AI_ML')
sys.path.insert(0, AI_ML_PATH)
sys.path.insert(0, os.path.join(AI_ML_PATH, 'AI'))

router = APIRouter()

@router.get("/api/ai/stock-forecast/{ticker}")
async def get_stock_forecast(ticker: str):
    """
    Get ML-based stock price forecast using LSTM model.
    This endpoint calls the stock_ml_model.py script.
    Warning: This can take 30-60 seconds to run.
    """
    try:
        # Validate ticker
        ticker = ticker.upper().strip()
        if not ticker:
            raise HTTPException(status_code=400, detail="Ticker symbol is required")
        
        # Import here to avoid loading on startup
        from stock_ml_model import get_ml_model
        
        logger.info(f"Starting ML model for ticker: {ticker}")
        
        # Run the ML model
        model_evaluation, ml_plot, forecast_plot, loss_plot, forecast_df = get_ml_model(ticker)
        
        logger.info(f"ML model completed for {ticker}")
        logger.info(f"Model evaluation: {model_evaluation}")
        logger.info(f"Forecast shape: {forecast_df.shape}")
        logger.info(f"Forecast data:\n{forecast_df}")
        
        # Clean forecast_df to handle NaN/Inf values for JSON serialization
        forecast_df_clean = forecast_df.copy()
        forecast_df_clean = forecast_df_clean.replace([np.inf, -np.inf], np.nan)
        forecast_df_clean = forecast_df_clean.ffill().bfill()
        
        logger.info(f"Cleaned forecast - has NaN: {forecast_df_clean.isna().any().any()}")
        logger.info(f"Cleaned forecast:\n{forecast_df_clean}")
        
        # Convert Plotly figures to JSON
        response_data = {
            "ticker": ticker,
            "model_evaluation": float(model_evaluation) if not np.isnan(model_evaluation) else 0.0,
            "actual_vs_predicted": json.loads(ml_plot.to_json()),
            "forecast": json.loads(forecast_plot.to_json()),
            "training_loss": json.loads(loss_plot.to_json()),
            "forecast_data": forecast_df_clean.to_dict(orient='records')
        }
        
        logger.info(f"Response prepared successfully for {ticker}")
        return JSONResponse(content=response_data)
    except ValueError as e:
        logger.error(f"ValueError for {ticker}: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid ticker or no data available: {str(e)}")
    except Exception as e:
        import traceback
        error_detail = f"Error running ML model: {str(e)}\n{traceback.format_exc()}"
        logger.error(f"Exception for {ticker}: {error_detail}")
        raise HTTPException(status_code=500, detail=error_detail)


@router.get("/api/ai/volatility/{ticker}")
async def get_volatility_forecast(ticker: str):
    """
    Get volatility forecast using GARCH model.
    This endpoint calls the predict_volatility.py script.
    """
    try:
        # Validate ticker
        ticker = ticker.upper().strip()
        if not ticker:
            raise HTTPException(status_code=400, detail="Ticker symbol is required")
        
        # Import here to avoid loading on startup
        from predict_volatility import predict_volatility
        
        # Run volatility prediction
        returns_plot, model_summary, rolling_volatility_plot, forecast_plot = predict_volatility(ticker)
        
        # Convert Plotly figures to JSON
        return JSONResponse(content={
            "ticker": ticker,
            "returns": json.loads(returns_plot.to_json()),
            "rolling_volatility": json.loads(rolling_volatility_plot.to_json()),
            "forecast": json.loads(forecast_plot.to_json()),
            "model_summary": str(model_summary)
        })
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid ticker or no data available: {str(e)}")
    except Exception as e:
        import traceback
        error_detail = f"Error running volatility model: {str(e)}\n{traceback.format_exc()}"
        raise HTTPException(status_code=500, detail=error_detail)


@router.get("/api/ai/index-chart/{ticker}")
async def get_index_chart(ticker: str):
    """
    Get 30-day index chart for major indices (SPY, DJIA, NDAQ, IWM).
    """
    try:
        # Validate ticker
        ticker = ticker.upper().strip()
        if not ticker:
            raise HTTPException(status_code=400, detail="Ticker symbol is required")
        
        from predict_volatility import go_generate_index_chart
        
        chart = go_generate_index_chart(ticker)
        
        return JSONResponse(content={
            "ticker": ticker,
            "chart": json.loads(chart.to_json())
        })
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid ticker or no data available: {str(e)}")
    except Exception as e:
        import traceback
        error_detail = f"Error generating index chart: {str(e)}\n{traceback.format_exc()}"
        raise HTTPException(status_code=500, detail=error_detail)
