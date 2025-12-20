#!/usr/bin/env python3
"""
Test script for economic data APIs
Tests free APIs for: currency, crypto, gold/metals, GDP, inflation, interest rates
"""

import requests
import json
from datetime import datetime


def test_exchangerate_api():
    """Test ExchangeRate-API (Free, no key needed)"""
    print("\n" + "="*60)
    print("Testing ExchangeRate-API (Currency Data)")
    print("="*60)
    
    try:
        # Free endpoint - latest rates against USD
        url = "https://api.exchangerate-api.com/v4/latest/USD"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ SUCCESS")
            print(f"   Base: {data.get('base')}")
            print(f"   Date: {data.get('date')}")
            print(f"   Sample rates:")
            rates = data.get('rates', {})
            for currency in ['EUR', 'GBP', 'JPY', 'CNY', 'INR']:
                if currency in rates:
                    print(f"     {currency}: {rates[currency]}")
            return True
        else:
            print(f"❌ FAILED: Status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def test_coingecko_api():
    """Test CoinGecko API (Free, no key needed)"""
    print("\n" + "="*60)
    print("Testing CoinGecko API (Cryptocurrency Data)")
    print("="*60)
    
    try:
        # Get top cryptocurrencies by market cap
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {
            'vs_currency': 'usd',
            'order': 'market_cap_desc',
            'per_page': 10,
            'page': 1
        }
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ SUCCESS")
            print(f"   Top cryptocurrencies:")
            for crypto in data[:5]:
                name = crypto.get('name')
                symbol = crypto.get('symbol', '').upper()
                price = crypto.get('current_price')
                change_24h = crypto.get('price_change_percentage_24h', 0)
                print(f"     {name} ({symbol}): ${price:,.2f} ({change_24h:+.2f}%)")
            return True
        else:
            print(f"❌ FAILED: Status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def test_metals_api():
    """Test Metals-API.com (Free tier available)"""
    print("\n" + "="*60)
    print("Testing Metals-API (Gold/Metals Data)")
    print("="*60)
    
    try:
        # Note: Requires API key, but has free tier
        # For now, test the endpoint structure
        print("⚠️  Note: Metals-API requires free API key")
        print("   Sign up at: https://metals-api.com")
        print("   Free tier: 50 requests/month")
        return None  # Neutral result
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def test_gold_api_alternative():
    """Test Gold-API.com alternative (free, no key)"""
    print("\n" + "="*60)
    print("Testing Gold-API Alternative")
    print("="*60)
    
    try:
        # Alternative: Use ExchangeRate-API with XAU (gold ounce)
        url = "https://api.exchangerate-api.com/v4/latest/XAU"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ SUCCESS (via ExchangeRate-API)")
            print(f"   Gold (XAU) rates:")
            rates = data.get('rates', {})
            if 'USD' in rates:
                gold_price_usd = 1 / rates['USD']
                print(f"     Gold per oz: ${gold_price_usd:,.2f}")
            return True
        else:
            print(f"❌ FAILED: Status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def test_fred_api():
    """Test FRED API (Federal Reserve Economic Data)"""
    print("\n" + "="*60)
    print("Testing FRED API (GDP, Inflation, Interest Rates)")
    print("="*60)
    
    try:
        print("⚠️  Note: FRED API requires free API key")
        print("   Sign up at: https://fred.stlouisfed.org/docs/api/api_key.html")
        print("   Free tier: Unlimited requests")
        print("   ")
        print("   Example series available:")
        print("     - GDP: https://fred.stlouisfed.org/series/GDP")
        print("     - CPI (Inflation): https://fred.stlouisfed.org/series/CPIAUCSL")
        print("     - Federal Funds Rate: https://fred.stlouisfed.org/series/DFF")
        print("     - Unemployment: https://fred.stlouisfed.org/series/UNRATE")
        return None
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def test_worldbank_api():
    """Test World Bank API (Free, no key needed)"""
    print("\n" + "="*60)
    print("Testing World Bank API (GDP, Inflation)")
    print("="*60)
    
    try:
        # Get GDP for USA
        url = "https://api.worldbank.org/v2/country/US/indicator/NY.GDP.MKTP.CD"
        params = {
            'format': 'json',
            'per_page': 5,
            'date': '2020:2023'
        }
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if len(data) > 1 and isinstance(data[1], list):
                print("✅ SUCCESS")
                print(f"   USA GDP (recent years):")
                for item in data[1][:5]:
                    year = item.get('date')
                    value = item.get('value')
                    if value:
                        print(f"     {year}: ${value/1e12:.2f} Trillion")
                return True
        print(f"❌ FAILED: Status {response.status_code}")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def test_treasury_api():
    """Test US Treasury API (Interest Rates) - Free, no key"""
    print("\n" + "="*60)
    print("Testing US Treasury API (Interest Rates)")
    print("="*60)
    
    try:
        # Get daily treasury yield curve rates
        url = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/avg_interest_rates"
        params = {
            'page[size]': 10,
            'sort': '-record_date'
        }
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and len(data['data']) > 0:
                print("✅ SUCCESS")
                print(f"   Recent interest rates:")
                for item in data['data'][:3]:
                    date = item.get('record_date')
                    rate = item.get('avg_interest_rate_amt')
                    security_desc = item.get('security_desc', '')[:40]
                    if rate:
                        print(f"     {date}: {rate}% - {security_desc}")
                return True
        print(f"❌ FAILED: Status {response.status_code}")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def main():
    """Run all API tests"""
    print("\n" + "="*60)
    print("ECONOMIC DATA API TESTING")
    print("="*60)
    print(f"Testing Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {}
    
    # Test each API
    results['ExchangeRate-API (Currency)'] = test_exchangerate_api()
    results['CoinGecko (Crypto)'] = test_coingecko_api()
    results['Gold-API Alternative'] = test_gold_api_alternative()
    results['World Bank (GDP)'] = test_worldbank_api()
    results['US Treasury (Interest Rates)'] = test_treasury_api()
    results['Metals-API (Gold/Metals)'] = test_metals_api()
    results['FRED (Economic Indicators)'] = test_fred_api()
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v is True)
    failed = sum(1 for v in results.values() if v is False)
    needs_key = sum(1 for v in results.values() if v is None)
    
    for api, result in results.items():
        if result is True:
            status = "✅ WORKING"
        elif result is False:
            status = "❌ FAILED"
        else:
            status = "🔑 NEEDS KEY"
        print(f"  {status}: {api}")
    
    print(f"\nResults: {passed} working, {failed} failed, {needs_key} need API keys")
    print("\nRecommendation:")
    print("  1. Use ExchangeRate-API for currency data (free, no key)")
    print("  2. Use CoinGecko for cryptocurrency data (free, no key)")
    print("  3. Use World Bank API for GDP data (free, no key)")
    print("  4. Use US Treasury API for interest rates (free, no key)")
    print("  5. Consider FRED API for inflation/detailed economic data (free key)")
    print("  6. Use ExchangeRate-API XAU for gold prices (free, no key)")
    print("")


if __name__ == "__main__":
    main()
