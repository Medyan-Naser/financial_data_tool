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
