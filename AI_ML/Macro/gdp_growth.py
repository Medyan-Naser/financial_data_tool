import os
import pandas as pd
import plotly.express as px
import sys

# Add parent directory to path for cached fredapi
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Use cached fredapi to avoid rate limiting
try:
    from cached_fredapi import Fred
except ImportError:
    from fredapi import Fred
    print("Warning: Using direct FRED API - caching not available")

# Set API key
fred_api_key = os.getenv("FRED_API_KEY", "69db3b36e2b3bf578e036a5f42d9b315")

# Initiate FRED API
fred = Fred(api_key=fred_api_key)

def get_gdp_growth_vis():
    """
    Get US GDP growth rate (Real GDP, quarterly percentage change)
    """
    try:
        # Real GDP (A191RL1Q225SBEA) - percent change from preceding period
        gdp_growth = fred.get_series_latest_release('A191RL1Q225SBEA')
        gdp_df = pd.DataFrame(gdp_growth, columns=['GDP Growth (%)'])
        gdp_df.index.name = 'Date'
        
        fig = px.line(
            gdp_df, 
            x=gdp_df.index, 
            y='GDP Growth (%)',
            title='📈 US Real GDP Growth Rate (Quarterly % Change)'
        )
        
        fig.update_xaxes(
            rangeslider_visible=True,
            rangeselector=dict(
                buttons=list([
                    dict(count=1, label="1Y", step="year", stepmode="backward"),
                    dict(count=5, label="5Y", step="year", stepmode="backward"),
                    dict(count=10, label="10Y", step="year", stepmode="backward"),
                    dict(step="all", label="All")
                ])
            )
        )
        
        # Add horizontal line at 0
        fig.add_hline(y=0, line_dash="dash", line_color="red", opacity=0.5)
        
        return fig
    except Exception as e:
        print(f"Error fetching GDP data: {e}")
        return None


def get_consumer_sentiment_vis():
    """
    Get University of Michigan Consumer Sentiment Index
    """
    try:
        # UMCSENT - University of Michigan: Consumer Sentiment
        sentiment = fred.get_series_latest_release('UMCSENT')
        sentiment_df = pd.DataFrame(sentiment, columns=['Consumer Sentiment'])
        sentiment_df.index.name = 'Date'
        
        fig = px.line(
            sentiment_df,
            x=sentiment_df.index,
            y='Consumer Sentiment',
            title='💭 University of Michigan Consumer Sentiment Index'
        )
        
        fig.update_xaxes(
            rangeslider_visible=True,
            rangeselector=dict(
                buttons=list([
                    dict(count=1, label="1Y", step="year", stepmode="backward"),
                    dict(count=5, label="5Y", step="year", stepmode="backward"),
                    dict(count=10, label="10Y", step="year", stepmode="backward"),
                    dict(step="all", label="All")
                ])
            )
        )
        
        return fig
    except Exception as e:
        print(f"Error fetching consumer sentiment data: {e}")
        return None


def get_pmi_vis():
    """
    Get ISM Manufacturing PMI (Purchasing Managers Index)
    PMI > 50 indicates expansion, < 50 indicates contraction
    """
    try:
        # Try multiple series IDs as FRED may have deprecated old ones
        series_ids = ['NAPM', 'MANEMP', 'TOTALSA']  # Common PMI series IDs
        pmi = None
        last_error = None
        
        for series_id in series_ids:
            try:
                pmi = fred.get_series_latest_release(series_id)
                if pmi is not None and not pmi.empty:
                    break
            except Exception as e:
                last_error = e
                continue
        
        if pmi is None or pmi.empty:
            raise Exception(f"Could not fetch PMI data from any series. Last error: {last_error}")
        
        pmi_df = pd.DataFrame(pmi, columns=['PMI Index'])
        pmi_df.index.name = 'Date'
        
        fig = px.line(
            pmi_df,
            x=pmi_df.index,
            y='PMI Index',
            title='🏭 ISM Manufacturing PMI (>50 = Expansion)'
        )
        
        fig.update_xaxes(
            rangeslider_visible=True,
            rangeselector=dict(
                buttons=list([
                    dict(count=1, label="1Y", step="year", stepmode="backward"),
                    dict(count=5, label="5Y", step="year", stepmode="backward"),
                    dict(count=10, label="10Y", step="year", stepmode="backward"),
                    dict(step="all", label="All")
                ])
            )
        )
        
        # Add horizontal line at 50 (expansion/contraction threshold)
        fig.add_hline(y=50, line_dash="dash", line_color="orange", opacity=0.7,
                     annotation_text="Expansion/Contraction Line")
        
        return fig
    except Exception as e:
        print(f"Error fetching PMI data: {e}")
        return None


def get_retail_sales_vis():
    """
    Get Retail Sales (month-over-month percent change)
    """
    try:
        # RSXFS - Advance Real Retail and Food Services Sales
        retail = fred.get_series_latest_release('RSXFS')
        retail_df = pd.DataFrame(retail, columns=['Retail Sales'])
        retail_df.index.name = 'Date'
        
        fig = px.line(
            retail_df,
            x=retail_df.index,
            y='Retail Sales',
            title='🛒 US Retail Sales (Millions of Dollars)'
        )
        
        fig.update_xaxes(
            rangeslider_visible=True,
            rangeselector=dict(
                buttons=list([
                    dict(count=1, label="1Y", step="year", stepmode="backward"),
                    dict(count=5, label="5Y", step="year", stepmode="backward"),
                    dict(count=10, label="10Y", step="year", stepmode="backward"),
                    dict(step="all", label="All")
                ])
            )
        )
        
        return fig
    except Exception as e:
        print(f"Error fetching retail sales data: {e}")
        return None
