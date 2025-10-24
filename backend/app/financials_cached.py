"""
Cached Financial Data API Endpoints

Provides API endpoints for fetching financial statements with caching and progress tracking.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from typing import Optional
import logging

from .data_collection_service import data_collection_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/api/financials/cached/{ticker}")
async def get_cached_financial_data(ticker: str, quarterly: bool = False):
    """
    Get financial data for a ticker from cache.
    
    Parameters:
    - ticker: Stock ticker symbol
    - quarterly: Get quarterly data (10-Q) instead of annual (10-K)
    
    Returns cached data if available, otherwise returns a 404 with cache status.
    """
    ticker = ticker.upper()
    
    # Check if cached
    if not data_collection_service.is_cached(ticker, quarterly):
        return JSONResponse(
            status_code=404,
            content={
                "ticker": ticker,
                "cached": False,
                "message": f"No cached data found for {ticker}. Use /api/financials/collect/{ticker} to fetch data."
            }
        )
    
    # Load from cache
    cached_data = data_collection_service.load_from_cache(ticker, quarterly)
    
    if not cached_data:
        return JSONResponse(
            status_code=500,
            content={
                "ticker": ticker,
                "cached": True,
                "error": "Failed to load cached data"
            }
        )
    
    return JSONResponse({
        **cached_data,
        "cached": True
    })


@router.get("/api/financials/collect/{ticker}")
async def collect_financial_data(
    ticker: str,
    years: int = 15,
    force_refresh: bool = False,
    quarterly: bool = False
):
    """
    Collect financial data for a ticker with real-time progress updates.
    
    This endpoint uses Server-Sent Events (SSE) to stream progress updates.
    
    Parameters:
    - ticker: Stock ticker symbol
    - years: Number of years/quarters to collect (default: 15)
    - force_refresh: Force re-collection even if cached (default: False)
    - quarterly: Collect quarterly data (10-Q) instead of annual (10-K)
    
    Returns: SSE stream with progress updates
    """
    ticker = ticker.upper()
    
    logger.info(f"Collection request for {ticker} (years={years}, force_refresh={force_refresh})")
    
    # Return SSE stream
    return StreamingResponse(
        data_collection_service.collect_data_with_progress(
            ticker=ticker,
            years=years,
            force_refresh=force_refresh,
            quarterly=quarterly
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )


@router.post("/api/financials/refresh/{ticker}")
async def refresh_financial_data(ticker: str, years: int = 15, quarterly: bool = False):
    """
    Force refresh financial data for a ticker.
    
    Parameters:
    - ticker: Stock ticker symbol
    - years: Number of years/quarters to collect
    - quarterly: Collect quarterly data instead of annual
    
    This is equivalent to collect with force_refresh=True.
    Returns SSE stream with progress updates.
    """
    ticker = ticker.upper()
    
    logger.info(f"Refresh request for {ticker} (years={years})")
    
    # Return SSE stream
    return StreamingResponse(
        data_collection_service.collect_data_with_progress(
            ticker=ticker,
            years=years,
            force_refresh=True,
            quarterly=quarterly
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.delete("/api/financials/cache/{ticker}")
async def delete_cached_data(ticker: str):
    """Delete cached data for a ticker."""
    ticker = ticker.upper()
    
    if data_collection_service.delete_cache(ticker):
        return JSONResponse({
            "ticker": ticker,
            "message": f"Cache deleted for {ticker}",
            "success": True
        })
    else:
        raise HTTPException(
            status_code=404,
            detail=f"No cached data found for {ticker}"
        )


@router.get("/api/financials/cache/status/{ticker}")
async def get_cache_status(ticker: str, quarterly: bool = False):
    """Check if a ticker has cached data (annual or quarterly)."""
    ticker = ticker.upper()
    
    is_cached = data_collection_service.is_cached(ticker, quarterly)
    
    response = {
        "ticker": ticker,
        "cached": is_cached
    }
    
    if is_cached:
        cached_data = data_collection_service.load_from_cache(ticker, quarterly)
        if cached_data:
            response["cached_at"] = cached_data.get("cached_at")
            response["collection_date"] = cached_data.get("collection_date")
            response["period_type"] = cached_data.get("period_type", "annual")
    
    return JSONResponse(response)
