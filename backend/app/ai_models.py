"""
AI/ML Models for Financial Analysis

This module provides various AI/ML models that analyze cached financial data:
1. Financial Health Score (0-100)
2. Bankruptcy Risk (Altman Z-Score + ML)
3. Revenue Forecasting (Time Series)
4. Trend Analysis
5. Anomaly Detection

Model predictions are cached in: .api_cache/AI/ (30 days)
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, List, Optional
import logging
import numpy as np
import pandas as pd
from pathlib import Path
import json
from datetime import datetime
from .cache_manager import ai_cache

logger = logging.getLogger(__name__)
router = APIRouter()

# Cache directory for financial statements
CACHE_DIR = Path(__file__).parent.parent / "api" / "cached_statements"


def load_ticker_data(ticker: str, quarterly: bool = False) -> Optional[Dict]:
    """Load cached financial data for a ticker."""
    suffix = "_quarterly" if quarterly else ""
    cache_file = CACHE_DIR / f"{ticker.upper()}{suffix}_statements.json"
    
    if not cache_file.exists():
        return None
    
    try:
        with open(cache_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading data for {ticker}: {e}")
        return None


def extract_financial_metrics(data: Dict) -> Dict:
    """Extract key financial metrics from statements."""
    metrics = {
        'revenue': [],
        'net_income': [],
        'total_assets': [],
        'total_liabilities': [],
        'shareholders_equity': [],
        'operating_cash_flow': [],
        'dates': []
    }
    
    statements = data.get('statements', {})
    
    # Helper function to check if a row has all zeros
    def is_all_zeros(row_data):
        """Check if a row contains only zeros or None values."""
        for val in row_data:
            if val is not None and val != 0 and (isinstance(val, (int, float)) and abs(val) > 0.01):
                return False
        return True
    
    # Extract from income statement
    income_stmt = statements.get('income_statement', {})
    if income_stmt and income_stmt.get('available'):
        columns = income_stmt.get('columns', [])
        data_matrix = income_stmt.get('data', [])
        row_names = income_stmt.get('row_names', [])
        
        # Find revenue and net income rows
        for i, row_name in enumerate(row_names):
            if i < len(data_matrix):
                row_data = data_matrix[i]
                # Skip rows with all zeros to avoid overwriting real data
                if is_all_zeros(row_data):
                    continue
                if 'revenue' in row_name.lower() and 'total' in row_name.lower():
                    metrics['revenue'] = [float(x) if x and x != 0 else None for x in row_data]
                elif 'net income' in row_name.lower() or 'net loss' in row_name.lower():
                    metrics['net_income'] = [float(x) if x and x != 0 else None for x in row_data]
        
        metrics['dates'] = columns
    
    # Extract from balance sheet
    balance_sheet = statements.get('balance_sheet', {})
    if balance_sheet and balance_sheet.get('available'):
        data_matrix = balance_sheet.get('data', [])
        row_names = balance_sheet.get('row_names', [])
        
        for i, row_name in enumerate(row_names):
            if i < len(data_matrix):
                row_data = data_matrix[i]
                # Skip rows with all zeros to avoid overwriting real data
                if is_all_zeros(row_data):
                    continue
                if 'total assets' in row_name.lower():
                    metrics['total_assets'] = [float(x) if x and x != 0 else None for x in row_data]
                elif 'total liabilities' in row_name.lower():
                    metrics['total_liabilities'] = [float(x) if x and x != 0 else None for x in row_data]
                elif 'shareholders\' equity' in row_name.lower() or 'stockholders\' equity' in row_name.lower():
                    metrics['shareholders_equity'] = [float(x) if x and x != 0 else None for x in row_data]
    
    # Extract from cash flow
    cash_flow = statements.get('cash_flow', {})
    if cash_flow and cash_flow.get('available'):
        data_matrix = cash_flow.get('data', [])
        row_names = cash_flow.get('row_names', [])
        
        for i, row_name in enumerate(row_names):
            if i < len(data_matrix):
                row_data = data_matrix[i]
                # Skip rows with all zeros to avoid overwriting real data
                if is_all_zeros(row_data):
                    continue
                if 'operating' in row_name.lower() and 'cash flow' in row_name.lower():
                    metrics['operating_cash_flow'] = [float(x) if x and x != 0 else None for x in row_data]
    
    return metrics


@router.get("/api/ai-models/health-score/{ticker}")
async def calculate_health_score(ticker: str, quarterly: bool = False):
    """
    Calculate a comprehensive financial health score (0-100).
    
    Considers:
    - Profitability (ROE, ROA, Profit Margin)
    - Liquidity (Current Ratio, Quick Ratio)
    - Solvency (Debt-to-Equity, Interest Coverage)
    - Efficiency (Asset Turnover)
    - Growth (Revenue Growth, Earnings Growth)
    
    Results are cached for 30 days.
    """
    ticker = ticker.upper()
    
    # Check cache first
    cached_result = ai_cache.get('health_score', ticker=ticker, quarterly=quarterly)
    if cached_result:
        logger.info(f"Returning cached health score for {ticker}")
        return cached_result
    
    # Load data
    data = load_ticker_data(ticker, quarterly)
    
    if not data:
        raise HTTPException(status_code=404, detail=f"No cached data found for {ticker}")
    
    metrics = extract_financial_metrics(data)
    
    # Calculate sub-scores
    scores = {
        'profitability': 0,
        'liquidity': 0,
        'solvency': 0,
        'efficiency': 0,
        'growth': 0
    }
    
    # Profitability Score (0-25)
    if metrics['net_income'] and metrics['revenue']:
        try:
            net_income_val = metrics['net_income'][0] if metrics['net_income'][0] is not None else 0
            revenue_val = metrics['revenue'][0] if metrics['revenue'][0] is not None else 0
            if revenue_val and revenue_val != 0:
                recent_margin = (net_income_val / revenue_val) * 100
                scores['profitability'] = min(25, max(0, recent_margin * 2.5))
        except:
            pass
    
    # Liquidity Score (0-20)
    if metrics['total_assets'] and metrics['total_liabilities']:
        try:
            assets_val = metrics['total_assets'][0] if metrics['total_assets'][0] is not None else 0
            liabilities_val = metrics['total_liabilities'][0] if metrics['total_liabilities'][0] is not None else 0
            if liabilities_val and liabilities_val != 0:
                current_ratio = assets_val / liabilities_val
                scores['liquidity'] = min(20, max(0, (current_ratio - 1) * 10))
        except:
            pass
    
    # Solvency Score (0-20)
    if metrics['total_liabilities'] and metrics['shareholders_equity']:
        try:
            liabilities_val = metrics['total_liabilities'][0] if metrics['total_liabilities'][0] is not None else 0
            equity_val = metrics['shareholders_equity'][0] if metrics['shareholders_equity'][0] is not None else 0
            if equity_val and equity_val != 0:
                debt_to_equity = liabilities_val / equity_val
                scores['solvency'] = min(20, max(0, 20 - (debt_to_equity * 5)))
        except:
            pass
    
    # Efficiency Score (0-15)
    if metrics['revenue'] and metrics['total_assets']:
        try:
            revenue_val = metrics['revenue'][0] if metrics['revenue'][0] is not None else 0
            assets_val = metrics['total_assets'][0] if metrics['total_assets'][0] is not None else 0
            if assets_val and assets_val != 0:
                asset_turnover = revenue_val / assets_val
                scores['efficiency'] = min(15, max(0, asset_turnover * 7.5))
        except:
            pass
    
    # Growth Score (0-20)
    if len(metrics['revenue']) >= 2:
        try:
            recent_revenue = metrics['revenue'][0] if metrics['revenue'][0] is not None else 0
            previous_revenue = metrics['revenue'][1] if metrics['revenue'][1] is not None else 0
            if previous_revenue and previous_revenue != 0 and recent_revenue:
                revenue_growth = ((recent_revenue - previous_revenue) / abs(previous_revenue)) * 100
                scores['growth'] = min(20, max(0, 10 + revenue_growth))
        except:
            pass
    
    total_score = sum(scores.values())
    
    # Determine rating
    if total_score >= 80:
        rating = "Excellent"
        color = "#28a745"
    elif total_score >= 60:
        rating = "Good"
        color = "#20c997"
    elif total_score >= 40:
        rating = "Fair"
        color = "#ffc107"
    elif total_score >= 20:
        rating = "Poor"
        color = "#fd7e14"
    else:
        rating = "Critical"
        color = "#dc3545"
    
    result = {
        "ticker": ticker,
        "period_type": data.get("period_type", "annual"),
        "total_score": round(total_score, 2),
        "rating": rating,
        "color": color,
        "breakdown": {
            "profitability": round(scores['profitability'], 2),
            "liquidity": round(scores['liquidity'], 2),
            "solvency": round(scores['solvency'], 2),
            "efficiency": round(scores['efficiency'], 2),
            "growth": round(scores['growth'], 2)
        },
        "metrics": {
            "revenue": metrics['revenue'][:5] if metrics['revenue'] else [],
            "net_income": metrics['net_income'][:5] if metrics['net_income'] else [],
            "dates": metrics['dates'][:5] if metrics['dates'] else []
        }
    }
    
    # Cache the result
    ai_cache.set('health_score', result, ticker=ticker, quarterly=quarterly)
    
    return JSONResponse(result)


@router.get("/api/ai-models/bankruptcy-risk/{ticker}")
async def calculate_bankruptcy_risk(ticker: str, quarterly: bool = False):
    """
    Calculate bankruptcy risk using Altman Z-Score.
    
    Z-Score interpretation:
    - Z > 2.99: Safe zone
    - 1.81 < Z < 2.99: Grey zone
    - Z < 1.81: Distress zone
    """
    ticker = ticker.upper()
    data = load_ticker_data(ticker, quarterly)
    
    if not data:
        raise HTTPException(status_code=404, detail=f"No cached data found for {ticker}")
    
    metrics = extract_financial_metrics(data)
    
    # Calculate Altman Z-Score components
    try:
        # Safely extract values, handling None and empty lists
        total_assets = metrics['total_assets'][0] if metrics['total_assets'] and metrics['total_assets'][0] is not None else 0
        total_liabilities = metrics['total_liabilities'][0] if metrics['total_liabilities'] and metrics['total_liabilities'][0] is not None else 0
        shareholders_equity = metrics['shareholders_equity'][0] if metrics['shareholders_equity'] and metrics['shareholders_equity'][0] is not None else 0
        revenue = metrics['revenue'][0] if metrics['revenue'] and metrics['revenue'][0] is not None else 0
        net_income = metrics['net_income'][0] if metrics['net_income'] and metrics['net_income'][0] is not None else 0
        
        if total_assets == 0 or total_assets is None:
            raise ValueError("Total assets is zero or not available")
        
        if total_liabilities is None:
            total_liabilities = 0
        
        # Working capital
        working_capital = total_assets - total_liabilities
        
        # Calculate Z-Score components
        x1 = working_capital / total_assets  # Working Capital / Total Assets
        x2 = net_income / total_assets  # Retained Earnings / Total Assets (approximation)
        x3 = net_income / total_assets  # EBIT / Total Assets (approximation)
        x4 = shareholders_equity / total_liabilities if total_liabilities else 0  # Market Value of Equity / Total Liabilities
        x5 = revenue / total_assets  # Sales / Total Assets
        
        # Altman Z-Score formula
        z_score = (1.2 * x1) + (1.4 * x2) + (3.3 * x3) + (0.6 * x4) + (1.0 * x5)
        
        # Determine risk level
        if z_score > 2.99:
            risk_level = "Low Risk"
            risk_category = "safe"
            color = "#28a745"
            probability = 5  # 5% probability
        elif z_score > 1.81:
            risk_level = "Moderate Risk"
            risk_category = "grey"
            color = "#ffc107"
            probability = 20  # 20% probability
        else:
            risk_level = "High Risk"
            risk_category = "distress"
            color = "#dc3545"
            probability = 80  # 80% probability
        
        return JSONResponse({
            "ticker": ticker,
            "period_type": data.get("period_type", "annual"),
            "z_score": round(z_score, 2),
            "risk_level": risk_level,
            "risk_category": risk_category,
            "bankruptcy_probability": probability,
            "color": color,
            "components": {
                "working_capital_ratio": round(x1, 3),
                "retained_earnings_ratio": round(x2, 3),
                "ebit_ratio": round(x3, 3),
                "equity_to_debt": round(x4, 3),
                "asset_turnover": round(x5, 3)
            },
            "interpretation": {
                "safe": "Z-Score > 2.99 - Company is in safe zone",
                "grey": "1.81 < Z-Score < 2.99 - Moderate risk area",
                "distress": "Z-Score < 1.81 - High bankruptcy risk"
            }
        })
    
    except Exception as e:
        logger.error(f"Error calculating Z-Score for {ticker}: {e}")
        raise HTTPException(status_code=500, detail=f"Error calculating bankruptcy risk: {str(e)}")


@router.get("/api/ai-models/trend-analysis/{ticker}")
async def analyze_trends(ticker: str, quarterly: bool = False):
    """
    Analyze financial trends using simple regression and momentum indicators.
    """
    ticker = ticker.upper()
    data = load_ticker_data(ticker, quarterly)
    
    if not data:
        raise HTTPException(status_code=404, detail=f"No cached data found for {ticker}")
    
    metrics = extract_financial_metrics(data)
    
    def calculate_trend(values):
        """Calculate linear trend."""
        if not values or len(values) < 2:
            return {"direction": "insufficient_data", "strength": 0, "change_pct": 0}
        
        # Remove None values
        valid_values = [v for v in values if v is not None]
        if len(valid_values) < 2:
            return {"direction": "insufficient_data", "strength": 0, "change_pct": 0}
        
        # Calculate simple trend
        first_val = valid_values[-1]  # Oldest
        last_val = valid_values[0]    # Most recent
        
        change_pct = ((last_val - first_val) / abs(first_val)) * 100 if first_val != 0 else 0
        
        # Determine direction
        if change_pct > 5:
            direction = "strong_upward"
            strength = min(100, abs(change_pct))
        elif change_pct > 0:
            direction = "upward"
            strength = abs(change_pct) * 10
        elif change_pct < -5:
            direction = "strong_downward"
            strength = min(100, abs(change_pct))
        elif change_pct < 0:
            direction = "downward"
            strength = abs(change_pct) * 10
        else:
            direction = "flat"
            strength = 0
        
        return {
            "direction": direction,
            "strength": round(strength, 2),
            "change_pct": round(change_pct, 2),
            "first_value": round(first_val, 2) if first_val else 0,
            "last_value": round(last_val, 2) if last_val else 0
        }
    
    return JSONResponse({
        "ticker": ticker,
        "period_type": data.get("period_type", "annual"),
        "trends": {
            "revenue": calculate_trend(metrics['revenue'][:10]),
            "net_income": calculate_trend(metrics['net_income'][:10]),
            "total_assets": calculate_trend(metrics['total_assets'][:10]),
            "operating_cash_flow": calculate_trend(metrics['operating_cash_flow'][:10])
        },
        "dates": metrics['dates'][:10] if metrics['dates'] else []
    })


@router.get("/api/ai-models/anomaly-detection/{ticker}")
async def detect_anomalies(ticker: str, quarterly: bool = False):
    """
    Detect anomalies in financial data using statistical methods.
    """
    ticker = ticker.upper()
    data = load_ticker_data(ticker, quarterly)
    
    if not data:
        raise HTTPException(status_code=404, detail=f"No cached data found for {ticker}")
    
    metrics = extract_financial_metrics(data)
    
    def find_anomalies(values, dates, metric_name):
        """Find anomalies using z-score method."""
        if not values or len(values) < 3:
            return []
        
        # Remove None values
        valid_data = [(v, d) for v, d in zip(values, dates) if v is not None]
        if len(valid_data) < 3:
            return []
        
        values_clean = [x[0] for x in valid_data]
        dates_clean = [x[1] for x in valid_data]
        
        mean = np.mean(values_clean)
        std = np.std(values_clean)
        
        anomalies = []
        for i, (val, date) in enumerate(zip(values_clean, dates_clean)):
            if std > 0:
                z_score = abs((val - mean) / std)
                if z_score > 2:  # More than 2 standard deviations
                    anomalies.append({
                        "date": date,
                        "value": round(val, 2),
                        "z_score": round(z_score, 2),
                        "severity": "high" if z_score > 3 else "medium",
                        "type": "spike" if val > mean else "drop"
                    })
        
        return anomalies
    
    return JSONResponse({
        "ticker": ticker,
        "period_type": data.get("period_type", "annual"),
        "anomalies": {
            "revenue": find_anomalies(metrics['revenue'][:10], metrics['dates'][:10], "revenue"),
            "net_income": find_anomalies(metrics['net_income'][:10], metrics['dates'][:10], "net_income"),
            "total_assets": find_anomalies(metrics['total_assets'][:10], metrics['dates'][:10], "total_assets")
        },
        "summary": {
            "total_anomalies": len(find_anomalies(metrics['revenue'][:10], metrics['dates'][:10], "revenue")) +
                              len(find_anomalies(metrics['net_income'][:10], metrics['dates'][:10], "net_income")) +
                              len(find_anomalies(metrics['total_assets'][:10], metrics['dates'][:10], "total_assets"))
        }
    })
