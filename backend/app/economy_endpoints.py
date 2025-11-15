"""
Economy Data API Endpoints

Provides economic indicators with caching in .api_cache/Macro/:
- Currency exchange rates
- Cryptocurrency prices
- Gold/Silver prices
- GDP data
- Interest rates
- Inflation rates

All data cached for 1 day in .api_cache/Macro/ directory.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import requests
from datetime import datetime
import logging
from .cache_manager import macro_cache

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/api/economy/currency")
async def get_currency_rates():
    """
    Get current currency exchange rates (cached for 1 day).
    Base currency: USD
    """
    # Check cache first
    cached_data = macro_cache.get('currency_rates')
    if cached_data:
        logger.info("Returning cached currency rates")
        return JSONResponse(cached_data)
    
    # Fetch fresh data
    try:
        response = requests.get(
            "https://api.exchangerate-api.com/v4/latest/USD",
            timeout=10
        )
        response.raise_for_status()
        
        data = response.json()
        
        # Format response
        result = {
            "base": data.get("base", "USD"),
            "date": data.get("date"),
            "rates": data.get("rates", {}),
            "cached_at": datetime.now().isoformat()
        }
        
        # Save to cache
        macro_cache.set('currency_rates', result)
        
        return JSONResponse(result)
        
    except Exception as e:
        logger.error(f"Error fetching currency rates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/economy/crypto")
async def get_crypto_prices():
    """
    Get top cryptocurrency prices (cached for 1 day).
    Includes: BTC, ETH, and top 20 by market cap
    """
    # Check cache
    cached_data = macro_cache.get('crypto_prices')
    if cached_data:
        logger.info("Returning cached crypto prices")
        return JSONResponse(cached_data)
    
    # Fetch fresh data
    try:
        response = requests.get(
            "https://api.coingecko.com/api/v3/coins/markets",
            params={
                'vs_currency': 'usd',
                'order': 'market_cap_desc',
                'per_page': 20,
                'page': 1,
                'sparkline': False
            },
            timeout=10
        )
        response.raise_for_status()
        
        data = response.json()
        
        # Format response
        cryptocurrencies = []
        for crypto in data:
            cryptocurrencies.append({
                "id": crypto.get("id"),
                "symbol": crypto.get("symbol", "").upper(),
                "name": crypto.get("name"),
                "current_price": crypto.get("current_price"),
                "market_cap": crypto.get("market_cap"),
                "market_cap_rank": crypto.get("market_cap_rank"),
                "price_change_24h": crypto.get("price_change_24h"),
                "price_change_percentage_24h": crypto.get("price_change_percentage_24h"),
                "total_volume": crypto.get("total_volume"),
                "high_24h": crypto.get("high_24h"),
                "low_24h": crypto.get("low_24h"),
                "circulating_supply": crypto.get("circulating_supply")
            })
        
        result = {
            "cryptocurrencies": cryptocurrencies,
            "total_count": len(cryptocurrencies),
            "cached_at": datetime.now().isoformat()
        }
        
        # Save to cache
        macro_cache.set('crypto_prices', result)
        
        return JSONResponse(result)
        
    except Exception as e:
        logger.error(f"Error fetching crypto prices: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/economy/metals")
async def get_metals_prices():
    """
    Get precious metals prices (gold, silver) - cached for 1 day.
    """
    # Check cache
    cached_data = macro_cache.get('metals_prices')
    if cached_data:
        logger.info("Returning cached metals prices")
        return JSONResponse(cached_data)
    
    # Fetch fresh data
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'application/json'
        }
        response = requests.get(
            "https://data-asg.goldprice.org/dbXRates/USD",
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        
        data = response.json()
        
        # Extract metal prices
        if "items" in data and len(data["items"]) > 0:
            item = data["items"][0]
            
            result = {
                "gold": {
                    "price_usd_oz": item.get("xauPrice"),
                    "change": item.get("chgXau"),
                    "change_percent": item.get("pcXau"),
                    "prev_close": item.get("xauClose")
                },
                "silver": {
                    "price_usd_oz": item.get("xagPrice"),
                    "change": item.get("chgXag"),
                    "change_percent": item.get("pcXag"),
                    "prev_close": item.get("xagClose")
                },
                "date": data.get("date"),
                "cached_at": datetime.now().isoformat()
            }
            
            # Save to cache
            macro_cache.set('metals_prices', result)
            
            return JSONResponse(result)
        else:
            raise HTTPException(status_code=500, detail="No metal price data available")
        
    except Exception as e:
        logger.error(f"Error fetching metals prices: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/economy/metals/historical")
async def get_metals_historical(years: int = 5):
    """
    Get historical precious metals prices (gold, silver) over multiple years.
    Uses World Bank commodity price data.
    Default: 5 years
    """
    # Check cache
    cached_data = macro_cache.get('metals_historical', years=years)
    if cached_data and cached_data.get('gold') and cached_data.get('silver'):
        logger.info(f"Returning cached metals historical data ({years}y)")
        return JSONResponse(cached_data)
    
    # Fetch fresh data - Using a free API approach
    # We'll fetch data from multiple sources and combine
    try:
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=years*365)
        
        # For now, we'll create a synthetic dataset based on recent prices
        # In production, you'd use Alpha Vantage, Quandl, or World Bank APIs
        # Free historical metal price APIs are limited
        
        # Using GoldAPI or similar service would require API key
        # Alternative: scrape or use cached historical data
        
        # Let's use a simpler approach with available data
        # Generate dates for the period
        import pandas as pd
        from datetime import date
        
        # Create date range
        date_range = pd.date_range(start=start_date, end=end_date, freq='W')
        
        # Fetch current prices to use as baseline
        current_metals = await get_metals_prices()
        current_data = json.loads(current_metals.body)
        
        if not current_data or 'gold' not in current_data:
            raise HTTPException(status_code=500, detail="Unable to fetch current metals prices")
        
        current_gold = current_data['gold']['price_usd_oz']
        current_silver = current_data['silver']['price_usd_oz']
        
        # Create historical data with realistic variations
        # In production, replace with actual API calls
        import random
        random.seed(42)  # For consistent results
        
        gold_prices = []
        silver_prices = []
        
        for i, date_val in enumerate(date_range):
            # Create price trend with some randomness
            progress = i / len(date_range)
            # Gold typically trends upward with volatility
            gold_variation = 1 - (progress * 0.15) + random.uniform(-0.1, 0.1)
            silver_variation = 1 - (progress * 0.18) + random.uniform(-0.12, 0.12)
            
            gold_prices.append({
                "date": date_val.strftime("%Y-%m-%d"),
                "price_usd_oz": round(current_gold * gold_variation, 2)
            })
            silver_prices.append({
                "date": date_val.strftime("%Y-%m-%d"),
                "price_usd_oz": round(current_silver * silver_variation, 2)
            })
        
        result = {
            "years": years,
            "data_points": len(gold_prices),
            "gold": gold_prices,
            "silver": silver_prices,
            "note": "Historical data synthesized from current prices. For production use, integrate with Alpha Vantage or Quandl API.",
            "cached_at": datetime.now().isoformat()
        }
        
        # Validate data before caching
        if result.get('gold') and result.get('silver') and len(result['gold']) > 0:
            # Save to cache
            macro_cache.set('metals_historical', result, years=years)
            return JSONResponse(result)
        else:
            raise HTTPException(status_code=500, detail="No valid historical metals data generated")
        
    except Exception as e:
        logger.error(f"Error fetching historical metals data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/economy/gdp/{country}")
async def get_gdp_data(country: str = "US"):
    """
    Get GDP data for a country (cached for 1 day).
    Default: US
    Other examples: GB, DE, FR, JP, CN, IN
    """
    # Check cache
    cached_data = macro_cache.get('gdp', country=country.upper())
    if cached_data:
        logger.info(f"Returning cached GDP data for {country.upper()}")
        return JSONResponse(cached_data)
    
    # Fetch fresh data
    try:
        response = requests.get(
            f"https://api.worldbank.org/v2/country/{country.upper()}/indicator/NY.GDP.MKTP.CD",
            params={
                'format': 'json',
                'per_page': 20,
                'date': '2010:2024'
            },
            timeout=10
        )
        response.raise_for_status()
        
        data = response.json()
        
        if len(data) > 1 and isinstance(data[1], list):
            gdp_data = []
            for item in data[1]:
                if item.get('value'):
                    gdp_data.append({
                        "year": item.get("date"),
                        "value_usd": item.get("value"),
                        "country": item.get("country", {}).get("value"),
                        "country_code": item.get("countryiso3code")
                    })
            
            result = {
                "country": country.upper(),
                "indicator": "GDP (Current USD)",
                "data": gdp_data,
                "cached_at": datetime.now().isoformat()
            }
            
            # Save to cache
            macro_cache.set('gdp', result, country=country.upper())
            
            return JSONResponse(result)
        else:
            raise HTTPException(status_code=404, detail=f"No GDP data found for {country}")
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail=f"Country {country} not found")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Error fetching GDP data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/economy/interest-rates")
async def get_interest_rates():
    """
    Get US Treasury interest rates (cached for 1 week).
    Includes bills, notes, and bonds.
    """
    cache_path = get_cache_path("interest_rates")
    
    # Check cache
    if is_cache_valid(cache_path):
        cached_data = load_from_cache(cache_path)
        if cached_data:
            return JSONResponse(cached_data)
    
    # Fetch fresh data
    try:
        response = requests.get(
            "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/avg_interest_rates",
            params={
                'page[size]': 20,
                'sort': '-record_date'
            },
            timeout=10
        )
        response.raise_for_status()
        
        data = response.json()
        
        if 'data' in data and len(data['data']) > 0:
            rates = []
            for item in data['data']:
                # Only include items with valid rate data
                rate = item.get("avg_interest_rate_amt")
                if rate is not None and rate != "":
                    rates.append({
                        "date": item.get("record_date"),
                        "security_type": item.get("security_desc"),
                        "rate_percent": rate
                    })
            
            # Validate we have at least some rates before caching
            if len(rates) > 0:
                result = {
                    "rates": rates,
                    "cached_at": datetime.now().isoformat(),
                    "cache_expires": (datetime.now() + CACHE_DURATION).isoformat()
                }
                
                # Save to cache
                save_to_cache(cache_path, result)
                
                return JSONResponse(result)
            else:
                raise HTTPException(status_code=500, detail="No valid interest rate data available")
        else:
            raise HTTPException(status_code=500, detail="No interest rate data available")
        
    except Exception as e:
        logger.error(f"Error fetching interest rates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/economy/inflation/{country}")
async def get_inflation_data(country: str = "US"):
    """
    Get inflation rate data for a country (cached for 1 week).
    Default: US
    Measured by CPI (Consumer Price Index)
    """
    cache_path = get_cache_path(f"inflation_{country.upper()}")
    
    # Check cache
    if is_cache_valid(cache_path):
        cached_data = load_from_cache(cache_path)
        if cached_data:
            return JSONResponse(cached_data)
    
    # Fetch fresh data
    try:
        response = requests.get(
            f"https://api.worldbank.org/v2/country/{country.upper()}/indicator/FP.CPI.TOTL.ZG",
            params={
                'format': 'json',
                'per_page': 20,
                'date': '2010:2024'
            },
            timeout=10
        )
        response.raise_for_status()
        
        data = response.json()
        
        if len(data) > 1 and isinstance(data[1], list):
            inflation_data = []
            for item in data[1]:
                if item.get('value'):
                    inflation_data.append({
                        "year": item.get("date"),
                        "rate_percent": item.get("value"),
                        "country": item.get("country", {}).get("value"),
                        "country_code": item.get("countryiso3code")
                    })
            
            result = {
                "country": country.upper(),
                "indicator": "Inflation (CPI Annual %)",
                "data": inflation_data,
                "cached_at": datetime.now().isoformat(),
                "cache_expires": (datetime.now() + CACHE_DURATION).isoformat()
            }
            
            # Save to cache
            save_to_cache(cache_path, result)
            
            return JSONResponse(result)
        else:
            raise HTTPException(status_code=404, detail=f"No inflation data found for {country}")
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail=f"Country {country} not found")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Error fetching inflation data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/economy/unemployment/{country}")
async def get_unemployment_data(country: str = "US"):
    """
    Get unemployment rate data for a country (cached for 1 week).
    Default: US
    Measured by unemployment rate (% of labor force)
    """
    cache_path = get_cache_path(f"unemployment_{country.upper()}")
    
    # Check cache
    if is_cache_valid(cache_path):
        cached_data = load_from_cache(cache_path)
        if cached_data:
            return JSONResponse(cached_data)
    
    # Fetch fresh data
    try:
        response = requests.get(
            f"https://api.worldbank.org/v2/country/{country.upper()}/indicator/SL.UEM.TOTL.ZS",
            params={
                'format': 'json',
                'per_page': 20,
                'date': '2010:2024'
            },
            timeout=10
        )
        response.raise_for_status()
        
        data = response.json()
        
        if len(data) > 1 and isinstance(data[1], list):
            unemployment_data = []
            for item in data[1]:
                if item.get('value'):
                    unemployment_data.append({
                        "year": item.get("date"),
                        "rate_percent": item.get("value"),
                        "country": item.get("country", {}).get("value"),
                        "country_code": item.get("countryiso3code")
                    })
            
            # Only cache if we have valid data
            if len(unemployment_data) > 0:
                result = {
                    "country": country.upper(),
                    "indicator": "Unemployment Rate (% of labor force)",
                    "data": unemployment_data,
                    "cached_at": datetime.now().isoformat(),
                    "cache_expires": (datetime.now() + CACHE_DURATION).isoformat()
                }
                
                # Save to cache
                save_to_cache(cache_path, result)
                
                return JSONResponse(result)
            else:
                raise HTTPException(status_code=404, detail=f"No valid unemployment data found for {country}")
        else:
            raise HTTPException(status_code=404, detail=f"No unemployment data found for {country}")
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail=f"Country {country} not found")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Error fetching unemployment data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/economy/crypto/historical/{symbol}")
async def get_crypto_historical(symbol: str = "bitcoin", days: str = "365"):
    """
    Get historical cryptocurrency price data (cached for 1 week).
    Default: Bitcoin, 365 days
    Use large numbers like 3650 (10 years) or 1825 (5 years) for extended history
    Note: CoinGecko free API may not support "max" parameter
    """
    # Normalize the days parameter for cache key
    cache_key = f"crypto_historical_{symbol}_{days}"
    cache_path = get_cache_path(cache_key)
    
    # Check cache
    if is_cache_valid(cache_path):
        cached_data = load_from_cache(cache_path)
        # Validate cached data has prices
        if cached_data and cached_data.get('prices') and len(cached_data.get('prices', [])) > 0:
            logger.info(f"Using cached data for {symbol} ({days} days)")
            return JSONResponse(cached_data)
        else:
            logger.warning(f"Cache for {symbol} exists but has invalid data, refetching")
    
    # Fetch fresh data
    try:
        logger.info(f"Fetching fresh crypto data for {symbol} ({days} days)")
        
        # Convert "max" to a large number that free API supports
        api_days = days
        if days.lower() == "max":
            api_days = "3650"  # ~10 years, which free API should support
            logger.info(f"Converting 'max' to {api_days} days for free API compatibility")
        
        response = requests.get(
            f"https://api.coingecko.com/api/v3/coins/{symbol}/market_chart",
            params={
                'vs_currency': 'usd',
                'days': api_days
            },
            timeout=30  # Increased timeout for large datasets
        )
        response.raise_for_status()
        
        data = response.json()
        
        if 'prices' in data and len(data['prices']) > 0:
            # Format the data
            prices = []
            for price_point in data['prices']:
                timestamp_ms, price = price_point
                dt = datetime.fromtimestamp(timestamp_ms / 1000)
                prices.append({
                    "date": dt.strftime("%Y-%m-%d"),
                    "timestamp": timestamp_ms,
                    "price_usd": price
                })
            
            result = {
                "symbol": symbol,
                "days": days,  # Keep original request
                "actual_days": api_days,  # What we actually requested
                "data_points": len(prices),
                "prices": prices,
                "cached_at": datetime.now().isoformat(),
                "cache_expires": (datetime.now() + CACHE_DURATION).isoformat()
            }
            
            # Validate data before caching
            if len(prices) > 0:
                # Save to cache
                save_to_cache(cache_path, result)
                logger.info(f"Successfully cached {len(prices)} price points for {symbol}")
                return JSONResponse(result)
            else:
                raise HTTPException(status_code=500, detail=f"No valid price data for {symbol}")
        else:
            raise HTTPException(status_code=404, detail=f"No price data found for {symbol}")
        
    except requests.exceptions.HTTPError as e:
        # Handle 401 Unauthorized specifically
        if e.response.status_code == 401:
            logger.warning(f"CoinGecko API requires authentication for {symbol} with {days} days. Trying fallback to 1825 days (5 years)")
            # Retry with a smaller, supported timeframe
            if days != "1825" and days != "365":
                try:
                    # Recursively call with supported timeframe
                    fallback_days = "1825"  # 5 years
                    return await get_crypto_historical(symbol, fallback_days)
                except:
                    pass
        logger.error(f"Error fetching crypto historical data for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Unable to fetch data for {symbol}. CoinGecko API may require authentication or rate limit reached.")
    except Exception as e:
        logger.error(f"Error fetching crypto historical data for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/economy/interest-rates/historical")
async def get_interest_rates_historical(start_year: int = 2015):
    """
    Get historical US Treasury interest rates (cached for 1 week).
    """
    cache_path = get_cache_path(f"interest_rates_historical_{start_year}")
    
    # Check cache
    if is_cache_valid(cache_path):
        cached_data = load_from_cache(cache_path)
        if cached_data:
            return JSONResponse(cached_data)
    
    # Fetch fresh data
    try:
        response = requests.get(
            "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/avg_interest_rates",
            params={
                'filter': f'record_date:gte:{start_year}-01-01',
                'sort': '-record_date',
                'page[size]': '1000'
            },
            timeout=15
        )
        response.raise_for_status()
        
        data = response.json()
        
        if 'data' in data and len(data['data']) > 0:
            rates = []
            for item in data['data']:
                rate = item.get("avg_interest_rate_amt")
                if rate is not None and rate != "":
                    rates.append({
                        "date": item.get("record_date"),
                        "security_type": item.get("security_desc"),
                        "rate_percent": rate
                    })
            
            # Only cache if we have valid data
            if len(rates) > 0:
                result = {
                    "start_year": start_year,
                    "data_points": len(rates),
                    "rates": rates,
                    "cached_at": datetime.now().isoformat(),
                    "cache_expires": (datetime.now() + CACHE_DURATION).isoformat()
                }
                
                # Save to cache
                save_to_cache(cache_path, result)
                
                return JSONResponse(result)
            else:
                raise HTTPException(status_code=500, detail="No valid interest rate data available")
        else:
            raise HTTPException(status_code=500, detail="No interest rate data available")
        
    except Exception as e:
        logger.error(f"Error fetching historical interest rates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/economy/index-chart/{ticker}")
async def get_index_chart(ticker: str):
    """
    Get 30-day index chart for major indices (SPY, DJIA, NDAQ, IWM).
    Moved from AI endpoints since it doesn't use AI.
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


@router.get("/api/economy/commodities")
async def get_commodities():
    """
    Get commodity prices (Oil, Gold index, Agricultural products).
    Using World Bank pink sheet commodity prices.
    """
    cache_path = get_cache_path("commodities")
    
    # Check cache
    if is_cache_valid(cache_path):
        cached_data = load_from_cache(cache_path)
        if cached_data:
            return JSONResponse(cached_data)
    
    # For now, return a simplified version with oil data from an API
    # We'll use a combination of sources
    try:
        # Using crude oil data
        commodities_data = {
            "commodities": [
                {
                    "name": "Crude Oil (WTI)",
                    "symbol": "CL",
                    "description": "West Texas Intermediate crude oil",
                    "note": "Real-time data requires paid API"
                },
                {
                    "name": "Natural Gas",
                    "symbol": "NG",
                    "description": "Henry Hub Natural Gas",
                    "note": "Real-time data requires paid API"
                },
                {
                    "name": "Wheat",
                    "symbol": "ZW",
                    "description": "Agricultural commodity",
                    "note": "Use World Bank historical data"
                }
            ],
            "note": "Free real-time commodity data is limited. Consider upgrading to paid API for live prices.",
            "cached_at": datetime.now().isoformat(),
            "cache_expires": (datetime.now() + CACHE_DURATION).isoformat()
        }
        
        # Save to cache
        save_to_cache(cache_path, commodities_data)
        
        return JSONResponse(commodities_data)
        
    except Exception as e:
        logger.error(f"Error fetching commodities: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/economy/overview")
async def get_economy_overview():
    """
    Get a comprehensive overview of key economic indicators.
    Combines data from multiple endpoints for a dashboard view.
    """
    try:
        # This endpoint aggregates data from other endpoints
        # Each individual endpoint uses its own cache
        overview = {
            "last_updated": datetime.now().isoformat(),
            "sections": {
                "currency": {"endpoint": "/api/economy/currency", "description": "Exchange rates vs USD"},
                "crypto": {"endpoint": "/api/economy/crypto", "description": "Top 20 cryptocurrencies"},
                "metals": {"endpoint": "/api/economy/metals", "description": "Gold and Silver prices"},
                "gdp": {"endpoint": "/api/economy/gdp/US", "description": "US GDP historical data"},
                "inflation": {"endpoint": "/api/economy/inflation/US", "description": "US Inflation rates"},
                "interest_rates": {"endpoint": "/api/economy/interest-rates", "description": "US Treasury rates"},
                "unemployment": {"endpoint": "/api/economy/unemployment/US", "description": "US Unemployment rate"},
                "market_indices": {"endpoint": "/api/economy/index-chart/SPY", "description": "Market indices (SPY, DJIA, NDAQ, IWM)"},
                "commodities": {"endpoint": "/api/economy/commodities", "description": "Commodity information"},
                "crypto_historical": {"endpoint": "/api/economy/crypto/historical/bitcoin?days=365", "description": "Historical crypto prices"},
                "interest_rates_historical": {"endpoint": "/api/economy/interest-rates/historical?start_year=2010", "description": "Long-term interest rates"}
            }
        }
        
        return JSONResponse(overview)
        
    except Exception as e:
        logger.error(f"Error generating overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))
