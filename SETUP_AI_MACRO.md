# AI & Macro Features Setup Guide

This guide will help you set up the new AI predictions and Macro economic data features.

## Overview

Your financial data tool now has **3 main tabs**:
1. **📈 Individual Stocks** - Your existing financial statement analysis with draggable charts
2. **🌍 Economy** - Macro economic indicators (commodities, currencies, inflation, etc.)
3. **🤖 AI Predictions** - ML-powered stock forecasts and volatility analysis

## Backend Setup

### 1. Install Python Dependencies

The AI/ML scripts require additional Python packages:

```bash
cd backend
pip install tensorflow keras scikit-learn arch yfinance pandas numpy plotly fredapi requests beautifulsoup4
```

### 2. API Keys

The macro scripts use API keys. Update these in your Python scripts if needed:

- **FRED API Key**: Used for economic data (inflation, unemployment, etc.)
  - File: `AI_ML/Macro/core_cpi_yoy_inflation.py` (and others)
  - Current key: `69db3b36e2b3bf578e036a5f42d9b315`
  
- **Alpha Vantage API Key**: Used for some market data
  - File: `AI_ML/dashboard.py`
  - Current key: `SX41SKXRRMA9Q01U`

**Note**: These keys are already in the Python scripts. You may want to get your own keys for production use.

### 3. Start the Backend

```bash
cd backend
uvicorn app.main:app --reload
```

The backend will now have these new endpoints:
- `/api/ai/stock-forecast/{ticker}` - LSTM price predictions
- `/api/ai/volatility/{ticker}` - GARCH volatility forecasts
- `/api/ai/index-chart/{ticker}` - 30-day index charts
- `/api/macro/commodities` - Commodities data
- `/api/macro/currencies` - Currency exchange rates
- `/api/macro/inflation` - CPI inflation data
- `/api/macro/debt-to-gdp` - Debt to GDP ratio
- `/api/macro/dollar-index` - Dollar index
- `/api/macro/velocity` - Money velocity
- `/api/macro/unemployment` - Unemployment rate
- `/api/macro/real-estate` - Real estate data
- `/api/macro/bonds` - Global bonds data

## Frontend Setup

### 1. Install New Dependencies

```bash
cd frontend
npm install plotly.js react-plotly.js
```

### 2. Start the Frontend

```bash
npm start
```

## Usage Guide

### Individual Stocks Tab (Existing)
- Search for a ticker
- View financial statements
- Create draggable, resizable charts
- Compare tickers

### Economy Tab (NEW)
Navigate to different economic indicators:

1. **Commodities** - Energy, Metals, Agricultural, Livestock, Industrial, Index
2. **Currencies** - Major global currency exchange rates
3. **Inflation** - CPI inflation trends from FRED
4. **Debt/GDP** - National debt to GDP ratio
5. **Dollar Index** - US Dollar strength
6. **Money Velocity** - Money circulation rate
7. **Unemployment** - Employment statistics
8. **Real Estate** - Housing market trends
9. **Bonds** - Global bond yields (Major 10Y, Europe, America, Asia, Australia, Africa)

**Features:**
- Data loads **only when you click** on a section (lazy loading)
- Interactive Plotly charts
- Real-time data from trading economics and FRED

### AI Predictions Tab (NEW)
Select from these AI models:

#### 1. Price Forecast (LSTM)
- **What it does**: Predicts next 11 days of stock prices
- **Model**: 3-layer LSTM neural network
- **Training**: 60 days of historical data
- **Output**:
  - Actual vs Predicted prices chart
  - 11-day forecast chart
  - Training loss plot
  - Forecast data table

**⚠️ Takes 30-60 seconds to run**

#### 2. Volatility Forecast (GARCH)
- **What it does**: Predicts price volatility
- **Model**: GARCH(2,2) model
- **Training**: 2 years of historical returns
- **Output**:
  - Returns over 2 years
  - Rolling 365-day volatility predictions
  - 7-day volatility forecast
  - Model summary statistics

**⚠️ Takes 15-30 seconds to run**

#### 3. Market Indices
- **What it does**: Shows 30-day charts for major indices
- **Indices**: SPY, DJIA, NDAQ, IWM
- **Updates**: Real-time from yFinance

## Performance Notes

### Lazy Loading Implementation
✅ **Scripts only run when requested:**
- Macro data: Fetches only when you click on a section
- AI models: Run only when you click "Run Model" button
- No data loads on initial page load
- Each section caches data after first load

### AI Model Performance
The LSTM price forecast can take **30-60 seconds** because it:
- Fetches 60 days of stock data
- Trains a neural network with 10 epochs
- Makes predictions on test set
- Generates forecast for 11 days

The GARCH volatility model takes **15-30 seconds** because it:
- Fetches 2 years of stock data
- Fits GARCH model
- Performs 365 rolling predictions
- Forecasts 7 days ahead

## Architecture

### Backend Structure
```
backend/app/
├── main.py (includes all routers)
├── data.py (existing financial data endpoints)
├── ai_endpoints.py (NEW - AI predictions)
└── macro_endpoints.py (NEW - economic data)
```

### Frontend Structure
```
frontend/src/
├── App.js (updated with tab navigation)
├── components/
│   ├── AIView.js (NEW - AI predictions interface)
│   ├── MacroView.js (NEW - economic data interface)
│   ├── FinancialTable.js (existing)
│   ├── ChartManager.js (existing)
│   ├── DraggableResizablePanel.js (existing)
│   └── ... (other components)
└── App.css (updated with new styles)
```

## Troubleshooting

### Backend Issues

**Problem**: ModuleNotFoundError for AI libraries
```bash
pip install tensorflow keras scikit-learn arch
```

**Problem**: FRED API errors
- Get your own API key at: https://fred.stlouisfed.org/docs/api/api_key.html
- Update in the macro Python scripts

**Problem**: Trading Economics scraping fails
- The commodities/currencies scripts scrape tradingeconomics.com
- If blocked, you may need to add headers or use a different data source

### Frontend Issues

**Problem**: Plotly charts not rendering
```bash
cd frontend
npm install --save plotly.js react-plotly.js
```

**Problem**: CORS errors
- Make sure backend is running on localhost:8000
- Check `main.py` has correct CORS origins

**Problem**: AI models timeout
- Increase timeout in axios if needed
- AI models genuinely take 30-60 seconds (this is normal)

## API Response Examples

### AI Stock Forecast Response
```json
{
  "ticker": "AAPL",
  "model_evaluation": 0.000123,
  "actual_vs_predicted": {...plotly chart JSON...},
  "forecast": {...plotly chart JSON...},
  "training_loss": {...plotly chart JSON...},
  "forecast_data": [
    {"2024-01-15": 185.23},
    {"2024-01-16": 186.45},
    ...
  ]
}
```

### Macro Commodities Response
```json
{
  "energy": {
    "data": [...],
    "chart": {...plotly table JSON...}
  },
  "metals": {...},
  "agricultural": {...},
  ...
}
```

## Next Steps

1. **Customize AI Models**:
   - Adjust LSTM layers in `stock_ml_model.py`
   - Change forecast horizon (currently 11 days)
   - Modify GARCH parameters in `predict_volatility.py`

2. **Add More Macro Indicators**:
   - Create new endpoints in `macro_endpoints.py`
   - Add corresponding Python scripts in `AI_ML/Macro/`
   - Update `MacroView.js` with new sections

3. **Improve Performance**:
   - Cache AI model predictions
   - Use background tasks for long-running models
   - Implement WebSocket for real-time updates

4. **Deploy**:
   - Use environment variables for API keys
   - Consider using Celery for AI model queue
   - Deploy backend on cloud (AWS, GCP, etc.)

## Credits

- **LSTM Model**: Based on Keras/TensorFlow
- **GARCH Model**: Using arch library
- **Economic Data**: FRED API, Trading Economics
- **Stock Data**: yFinance
- **Visualization**: Plotly, Recharts

Enjoy your enhanced financial analysis tool! 🚀
