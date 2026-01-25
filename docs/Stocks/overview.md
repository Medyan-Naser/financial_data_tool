# Stocks Tab Overview

The Stocks tab provides comprehensive financial data and analysis for publicly traded companies. Data is sourced from SEC EDGAR filings (10-K and 10-Q reports) and real-time market data providers.

## Features

### 1. Financial Statements

Three core financial statements are available for each ticker:

- **Income Statement** - Revenue, expenses, and profitability over a period
- **Balance Sheet** - Assets, liabilities, and shareholders' equity at a point in time
- **Cash Flow Statement** - Cash inflows and outflows from operations, investing, and financing

Both **annual** (10-K) and **quarterly** (10-Q) data are supported.

### 2. Stock Price Data

Real-time and historical price data including:

- **OHLC Data** - Open, High, Low, Close prices
- **Volume** - Trading volume
- **Time Periods** - 1D, 5D, 1M, 3M, 6M, 1Y, 2Y, 5Y, 10Y, YTD, MAX

### 3. AI/ML Analysis

Advanced analytics powered by machine learning:

- **Financial Health Score** (0-100) - Comprehensive health assessment
- **Bankruptcy Risk** - Altman Z-Score analysis
- **Trend Analysis** - Revenue and earnings trends
- **Anomaly Detection** - Unusual patterns in financial data

## Data Sources

| Data Type | Source | Update Frequency |
|-----------|--------|------------------|
| Financial Statements | SEC EDGAR | Quarterly |
| Historical Prices | yfinance | Daily |
| Real-time Quotes | Finnhub API | Real-time |

## Supported Tickers

Any US publicly traded company with SEC filings can be analyzed. Data is cached locally to minimize API calls and improve performance.

## Cache Behavior

- **Stock prices**: Cached for 1 week
- **Financial statements**: Cached until new filings available
- **AI predictions**: Cached for 30 days
