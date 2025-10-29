import sys
import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import json

# Add AI_ML directory to path
AI_ML_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'AI_ML')
sys.path.insert(0, os.path.join(AI_ML_PATH, 'Macro'))

router = APIRouter()

@router.get("/api/macro/commodities")
async def get_commodities_data():
    """
    Get commodities data (energy, metals, agricultural, livestock, industrial, index).
    """
    try:
        from commodities import (
            get_energy, get_metals, get_agricultural, 
            get_livestock, get_industrial, get_index,
            energy_json, metals_json, agricultural_json,
            industrial_json, livestock_json, commodities_index_json
        )
        
        return JSONResponse(content={
            "energy": {
                "data": energy_json,
                "chart": json.loads(get_energy().to_json())
            },
            "metals": {
                "data": metals_json,
                "chart": json.loads(get_metals().to_json())
            },
            "agricultural": {
                "data": agricultural_json,
                "chart": json.loads(get_agricultural().to_json())
            },
            "livestock": {
                "data": livestock_json,
                "chart": json.loads(get_livestock().to_json())
            },
            "industrial": {
                "data": industrial_json,
                "chart": json.loads(get_industrial().to_json())
            },
            "index": {
                "data": commodities_index_json,
                "chart": json.loads(get_index().to_json())
            }
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching commodities data: {str(e)}")


@router.get("/api/macro/currencies")
async def get_currencies_data():
    """
    Get major currencies data.
    """
    try:
        from currencies import get_major_currencies, major_currencies
        
        return JSONResponse(content={
            "data": json.loads(major_currencies.to_json(orient='records')),
            "chart": json.loads(get_major_currencies().to_json())
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching currencies data: {str(e)}")


@router.get("/api/macro/inflation")
async def get_inflation_data():
    """
    Get CPI inflation data from FRED.
    """
    try:
        from core_cpi_yoy_inflation import get_inflation_vis
        
        chart = get_inflation_vis()
        
        return JSONResponse(content={
            "chart": json.loads(chart.to_json())
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching inflation data: {str(e)}")


@router.get("/api/macro/debt-to-gdp")
async def get_debt_to_gdp_data():
    """
    Get debt to GDP ratio data.
    """
    try:
        from debt_to_gdp import get_debt_to_gdp_vis
        chart = get_debt_to_gdp_vis()
        return JSONResponse(content={
            "chart": json.loads(chart.to_json())
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching debt to GDP data: {str(e)}")


@router.get("/api/macro/dollar-index")
async def get_dollar_index_data():
    """
    Get dollar index data.
    """
    try:
        from dollar_index import get_dollar_index_vis
        chart = get_dollar_index_vis()
        return JSONResponse(content={
            "chart": json.loads(chart.to_json())
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching dollar index data: {str(e)}")


@router.get("/api/macro/velocity")
async def get_velocity_data():
    """
    Get money velocity data.
    """
    try:
        from velocity import get_velocity_vis
        chart = get_velocity_vis()
        return JSONResponse(content={
            "chart": json.loads(chart.to_json())
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching velocity data: {str(e)}")


@router.get("/api/macro/unemployment")
async def get_unemployment_data():
    """
    Get unemployment rate data.
    """
    try:
        from unemployment import get_unrate_vis
        
        chart = get_unrate_vis()
        
        return JSONResponse(content={
            "chart": json.loads(chart.to_json())
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching unemployment data: {str(e)}")


@router.get("/api/macro/real-estate")
async def get_real_estate_data():
    """
    Get real estate data.
    """
    try:
        from realestate import get_re_vis
        chart = get_re_vis()
        return JSONResponse(content={
            "chart": json.loads(chart.to_json())
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching real estate data: {str(e)}")

@router.get("/api/macro/markets")
async def get_markets_data():
    """
    Get key market indicators (gold, silver, oil, bitcoin, ethereum, dollar index) with YTD and YoY.
    """
    try:
        from markets import get_markets_table, markets_json
        return JSONResponse(content={
            "data": markets_json,
            "chart": json.loads(get_markets_table().to_json())
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching markets data: {str(e)}")


@router.get("/api/macro/bonds")
async def get_bonds_data():
    """
    Get global bonds data.
    """
    try:
        from global_bonds import (
            get_major_10y, get_europe_bonds, get_america_bonds,
            get_asia_bonds, get_australia_bonds, get_africa_bonds
        )
        
        return JSONResponse(content={
            "major_10y": json.loads(get_major_10y().to_json()),
            "europe": json.loads(get_europe_bonds().to_json()),
            "america": json.loads(get_america_bonds().to_json()),
            "asia": json.loads(get_asia_bonds().to_json()),
            "australia": json.loads(get_australia_bonds().to_json()),
            "africa": json.loads(get_africa_bonds().to_json())
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching bonds data: {str(e)}")


@router.get("/api/macro/yield-curve")
async def get_yield_curve_data():
    """
    Get US Treasury yield curve data.
    """
    try:
        from yield_curve import get_yield_curve_vis
        
        chart = get_yield_curve_vis()
        
        return JSONResponse(content={
            "chart": json.loads(chart.to_json())
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching yield curve data: {str(e)}")


@router.get("/api/macro/gdp-growth")
async def get_gdp_growth_data():
    """
    Get US GDP growth rate data.
    """
    try:
        from gdp_growth import get_gdp_growth_vis
        chart = get_gdp_growth_vis()
        if chart is None:
            raise HTTPException(status_code=503, detail="GDP data temporarily unavailable. The FRED API may be experiencing issues.")
        return JSONResponse(content={
            "chart": json.loads(chart.to_json())
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching GDP growth data: {str(e)}")


@router.get("/api/macro/consumer-sentiment")
async def get_consumer_sentiment_data():
    """
    Get consumer sentiment index data.
    """
    try:
        from gdp_growth import get_consumer_sentiment_vis
        chart = get_consumer_sentiment_vis()
        if chart is None:
            raise HTTPException(status_code=503, detail="Consumer sentiment data temporarily unavailable. The FRED API may be experiencing issues.")
        return JSONResponse(content={
            "chart": json.loads(chart.to_json())
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching consumer sentiment data: {str(e)}")


@router.get("/api/macro/pmi")
async def get_pmi_data():
    """
    Get ISM Manufacturing PMI data.
    """
    try:
        from gdp_growth import get_pmi_vis
        chart = get_pmi_vis()
        if chart is None:
            raise HTTPException(status_code=503, detail="PMI data temporarily unavailable. The FRED API may be experiencing issues.")
        return JSONResponse(content={
            "chart": json.loads(chart.to_json())
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching PMI data: {str(e)}")


@router.get("/api/macro/retail-sales")
async def get_retail_sales_data():
    """
    Get retail sales data.
    """
    try:
        from gdp_growth import get_retail_sales_vis
        chart = get_retail_sales_vis()
        if chart is None:
            raise HTTPException(status_code=503, detail="Retail sales data temporarily unavailable. The FRED API may be experiencing issues.")
        return JSONResponse(content={
            "chart": json.loads(chart.to_json())
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching retail sales data: {str(e)}")


@router.get("/api/macro/overview")
async def get_macro_overview():
    """
    Get overview summary of key economic indicators.
    """
    try:
        overview_data = {
            "indicators": [
                {
                    "name": "CPI Inflation",
                    "description": "Year-over-year inflation rate based on Consumer Price Index",
                    "available": True,
                    "section": "inflation"
                },
                {
                    "name": "Unemployment Rate",
                    "description": "Current unemployment rate in the United States",
                    "available": True,
                    "section": "unemployment"
                },
                {
                    "name": "GDP Growth",
                    "description": "Real GDP growth rate (quarterly % change)",
                    "available": True,
                    "section": "gdp-growth"
                },
                {
                    "name": "Consumer Sentiment",
                    "description": "University of Michigan Consumer Sentiment Index",
                    "available": True,
                    "section": "consumer-sentiment"
                },
                {
                    "name": "Manufacturing PMI",
                    "description": "ISM Manufacturing Purchasing Managers Index",
                    "available": True,
                    "section": "pmi"
                },
                {
                    "name": "Retail Sales",
                    "description": "US retail and food services sales",
                    "available": True,
                    "section": "retail-sales"
                },
                {
                    "name": "Treasury Yield Curve",
                    "description": "US Treasury yields across different maturities",
                    "available": True,
                    "section": "yield-curve"
                },
                {
                    "name": "Major Currencies",
                    "description": "Exchange rates of major world currencies vs USD",
                    "available": True,
                    "section": "currencies"
                },
                {
                    "name": "Commodities",
                    "description": "Prices of energy, metals, agricultural products, and more",
                    "available": True,
                    "section": "commodities"
                },
                {
                    "name": "Global Bonds",
                    "description": "10-year government bond yields across major economies",
                    "available": True,
                    "section": "bonds"
                }
            ],
            "status": "operational"
        }
        
        return JSONResponse(content=overview_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching overview: {str(e)}")
