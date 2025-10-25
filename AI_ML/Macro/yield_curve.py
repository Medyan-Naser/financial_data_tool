# # Yield Curve (Interest Rates)
# 
# The visualization displays the daily U.S. Treasury yield curve from 5 to 30 year bonds.
# Used web scraper to pull in the data from Treasury.gov

# Import notebook libraries and dependencies
import os
import requests
import pandas as pd
import numpy as np
import plotly.express as px
from bs4 import BeautifulSoup
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def fetch_yield_curve_data():
    """
    Fetch the latest U.S. Treasury yield curve data.
    Uses dynamic date to always get current data.
    """
    try:
        # Get current year and month
        now = datetime.now()
        year_month = now.strftime("%Y%m")  # e.g., "202510" for October 2025
        
        # Scrape U.S. Treasury data with current month
        url = f"https://home.treasury.gov/resource-center/data-chart-center/interest-rates/pages/xmlview?data=daily_treasury_real_yield_curve&field_tdr_date_value_month={year_month}"
        
        logger.info(f"Fetching yield curve data from: {url}")
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'xml')
        table = soup.find_all('properties')
        
        if not table or len(table) == 0:
            logger.warning(f"No data found for {year_month}, trying previous month...")
            # Try previous month if current month has no data yet
            prev_month = datetime(now.year, now.month, 1) - pd.DateOffset(months=1)
            year_month = prev_month.strftime("%Y%m")
            url = f"https://home.treasury.gov/resource-center/data-chart-center/interest-rates/pages/xmlview?data=daily_treasury_real_yield_curve&field_tdr_date_value_month={year_month}"
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'xml')
            table = soup.find_all('properties')
        
        tbondvalues = []
        for i in table:
            try:
                # Try both naming conventions
                date_elem = i.find('NEW_DATE') or i.find('new_date')
                tc_5y = i.find('TC_5YEAR') or i.find('tc_5year')
                tc_7y = i.find('TC_7YEAR') or i.find('tc_7year')
                tc_10y = i.find('TC_10YEAR') or i.find('tc_10year')
                tc_20y = i.find('TC_20YEAR') or i.find('tc_20year')
                tc_30y = i.find('TC_30YEAR') or i.find('tc_30year')
                
                if date_elem and tc_5y and tc_7y and tc_10y and tc_20y and tc_30y:
                    date_str = date_elem.text[:10] if date_elem.text else None
                    if date_str:
                        tbondvalues.append([
                            date_str,
                            tc_5y.text,
                            tc_7y.text,
                            tc_10y.text,
                            tc_20y.text,
                            tc_30y.text
                        ])
            except Exception as e:
                logger.debug(f"Error parsing row: {e}")
                continue
        
        if not tbondvalues:
            raise ValueError("No valid yield curve data found")
        
        ustcurve = pd.DataFrame(tbondvalues, columns=['date', '5y', '7y', '10y', '20y', '30y'])
        
        # Clean data
        ustcurve.iloc[:, 1:] = ustcurve.iloc[:, 1:].apply(pd.to_numeric, errors='coerce')
        ustcurve['date'] = pd.to_datetime(ustcurve['date'])
        
        # Remove rows with NaN values
        ustcurve = ustcurve.dropna()
        
        yield_curve = ustcurve.set_index('date').sort_index(ascending=False)
        
        logger.info(f"Successfully fetched {len(yield_curve)} days of yield curve data")
        
        return yield_curve
        
    except Exception as e:
        logger.error(f"Error fetching yield curve data: {e}")
        raise


# Fetch data on module load
try:
    yield_curve = fetch_yield_curve_data()
except Exception as e:
    logger.error(f"Failed to load yield curve data: {e}")
    # Create empty dataframe as fallback
    yield_curve = pd.DataFrame(columns=['5y', '7y', '10y', '20y', '30y'])


def get_yield_curve_vis():
    """
    Create a visualization of the latest U.S. Treasury yield curve.
    """
    if yield_curve.empty:
        # Return empty figure if no data
        import plotly.graph_objects as go
        fig = go.Figure()
        fig.add_annotation(
            text="No yield curve data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16)
        )
        return fig
    
    # Get the most recent date's data
    latest_data = yield_curve.iloc[0]
    
    # Create line chart
    yield_curve_vis = px.line(
        latest_data,
        title=f'U.S. Treasury Yield Curve (%) - {yield_curve.index[0].strftime("%Y-%m-%d")}'
    )
    
    yield_curve_vis.update_layout(
        xaxis_title="Maturity",
        yaxis_title="Treasury Yield (%)",
        hovermode='x unified'
    )
    
    return yield_curve_vis

