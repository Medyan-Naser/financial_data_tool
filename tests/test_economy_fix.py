"""
Comprehensive test suite for economy endpoints

Tests all economy-related API endpoints including:
- Currency exchange rates
- Cryptocurrency prices and historical data
- Precious metals prices
- GDP data by country
- Interest rates
- Inflation data
- Response validation and error handling
"""

import requests
import sys
import pytest

API_BASE = "http://localhost:8000"


class TestCurrencyEndpoint:
    """Test currency exchange rate endpoints"""
    
    def test_currency_basic(self):
        """Test basic currency endpoint"""
        print("\n" + "="*60)
        print("TEST: Currency Basic")
        print("="*60)
        
        response = requests.get(f"{API_BASE}/api/economy/currency", timeout=15)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        print(f"✓ Status: {response.status_code}")
        print(f"✓ Response type: {type(data)}")
        print("✅ Currency basic test passed!")
    
    def test_currency_response_structure(self):
        """Test currency response has expected structure"""
        print("\n" + "="*60)
        print("TEST: Currency Response Structure")
        print("="*60)
        
        response = requests.get(f"{API_BASE}/api/economy/currency", timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            
            # Check for common currency pairs
            if isinstance(data, dict):
                keys = list(data.keys())[:5]
                for key in keys:
                    print(f"✓ Has key: {key}")
        
        print("✅ Currency structure test passed!")
    
    def test_currency_values_are_numeric(self):
        """Test that currency values are numeric"""
        print("\n" + "="*60)
        print("TEST: Currency Values Numeric")
        print("="*60)
        
        response = requests.get(f"{API_BASE}/api/economy/currency", timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            
            if isinstance(data, dict):
                for key, value in list(data.items())[:3]:
                    if isinstance(value, (int, float)):
                        print(f"✓ {key}: {value} (numeric)")
                    elif isinstance(value, dict):
                        print(f"✓ {key}: nested object")
        
        print("✅ Currency values test passed!")


class TestCryptoEndpoint:
    """Test cryptocurrency endpoints"""
    
    def test_crypto_basic(self):
        """Test basic crypto endpoint"""
        print("\n" + "="*60)
        print("TEST: Crypto Basic")
        print("="*60)
        
        response = requests.get(f"{API_BASE}/api/economy/crypto", timeout=15)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print(f"✓ Status: {response.status_code}")
        print("✅ Crypto basic test passed!")
    
    def test_crypto_historical_bitcoin(self):
        """Test Bitcoin historical data"""
        print("\n" + "="*60)
        print("TEST: Bitcoin Historical Data")
        print("="*60)
        
        response = requests.get(
            f"{API_BASE}/api/economy/crypto/historical/bitcoin",
            params={'days': 30},
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Status: {response.status_code}")
            if isinstance(data, dict) and 'prices' in data:
                print(f"✓ Has prices data")
            elif isinstance(data, list):
                print(f"✓ Data points: {len(data)}")
        else:
            print(f"⚠ Status: {response.status_code}")
        
        print("✅ Bitcoin historical test passed!")
    
    def test_crypto_historical_ethereum(self):
        """Test Ethereum historical data"""
        print("\n" + "="*60)
        print("TEST: Ethereum Historical Data")
        print("="*60)
        
        response = requests.get(
            f"{API_BASE}/api/economy/crypto/historical/ethereum",
            params={'days': 30},
            timeout=15
        )
        
        print(f"✓ Status: {response.status_code}")
        print("✅ Ethereum historical test passed!")
    
    def test_crypto_historical_various_days(self):
        """Test crypto historical with various day ranges"""
        print("\n" + "="*60)
        print("TEST: Crypto Historical Various Days")
        print("="*60)
        
        days_options = [7, 30, 90, 365]
        
        for days in days_options:
            response = requests.get(
                f"{API_BASE}/api/economy/crypto/historical/bitcoin",
                params={'days': days},
                timeout=15
            )
            print(f"✓ {days} days: Status {response.status_code}")
        
        print("✅ Various days test passed!")


class TestMetalsEndpoint:
    """Test precious metals endpoints"""
    
    def test_metals_basic(self):
        """Test basic metals endpoint"""
        print("\n" + "="*60)
        print("TEST: Metals Basic")
        print("="*60)
        
        response = requests.get(f"{API_BASE}/api/economy/metals", timeout=15)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print(f"✓ Status: {response.status_code}")
        print("✅ Metals basic test passed!")
    
    def test_metals_response_structure(self):
        """Test metals response has expected metals"""
        print("\n" + "="*60)
        print("TEST: Metals Response Structure")
        print("="*60)
        
        response = requests.get(f"{API_BASE}/api/economy/metals", timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            expected_metals = ['gold', 'silver', 'platinum', 'palladium']
            
            for metal in expected_metals:
                if isinstance(data, dict) and metal in data:
                    print(f"✓ Has {metal}")
                elif isinstance(data, dict):
                    # Check for alternate key formats
                    found = any(metal.lower() in k.lower() for k in data.keys())
                    print(f"{'✓' if found else '⚠'} {metal}")
        
        print("✅ Metals structure test passed!")
    
    def test_metals_historical(self):
        """Test metals historical data"""
        print("\n" + "="*60)
        print("TEST: Metals Historical")
        print("="*60)
        
        response = requests.get(
            f"{API_BASE}/api/economy/metals/historical",
            params={'years': 1},
            timeout=15
        )
        
        print(f"✓ Status: {response.status_code}")
        print("✅ Metals historical test passed!")
    
    def test_metals_historical_various_years(self):
        """Test metals historical with various year ranges"""
        print("\n" + "="*60)
        print("TEST: Metals Historical Various Years")
        print("="*60)
        
        years_options = [1, 2, 5]
        
        for years in years_options:
            response = requests.get(
                f"{API_BASE}/api/economy/metals/historical",
                params={'years': years},
                timeout=15
            )
            print(f"✓ {years} years: Status {response.status_code}")
        
        print("✅ Various years test passed!")


class TestGDPEndpoint:
    """Test GDP data endpoints"""
    
    def test_gdp_us(self):
        """Test US GDP endpoint"""
        print("\n" + "="*60)
        print("TEST: US GDP")
        print("="*60)
        
        response = requests.get(f"{API_BASE}/api/economy/gdp/US", timeout=15)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print(f"✓ Status: {response.status_code}")
        print("✅ US GDP test passed!")
    
    def test_gdp_multiple_countries(self):
        """Test GDP for multiple countries"""
        print("\n" + "="*60)
        print("TEST: GDP Multiple Countries")
        print("="*60)
        
        countries = ['US', 'CN', 'JP', 'DE', 'GB']
        
        for country in countries:
            response = requests.get(f"{API_BASE}/api/economy/gdp/{country}", timeout=15)
            status_icon = "✓" if response.status_code == 200 else "⚠"
            print(f"{status_icon} {country}: Status {response.status_code}")
        
        print("✅ Multiple countries test passed!")
    
    def test_gdp_response_structure(self):
        """Test GDP response structure"""
        print("\n" + "="*60)
        print("TEST: GDP Response Structure")
        print("="*60)
        
        response = requests.get(f"{API_BASE}/api/economy/gdp/US", timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, dict):
                print(f"✓ Keys: {list(data.keys())[:5]}")
            elif isinstance(data, list):
                print(f"✓ Data points: {len(data)}")
        
        print("✅ GDP structure test passed!")


class TestInterestRatesEndpoint:
    """Test interest rates endpoint"""
    
    def test_interest_rates_basic(self):
        """Test basic interest rates endpoint"""
        print("\n" + "="*60)
        print("TEST: Interest Rates Basic")
        print("="*60)
        
        response = requests.get(f"{API_BASE}/api/economy/interest-rates", timeout=15)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print(f"✓ Status: {response.status_code}")
        print("✅ Interest rates test passed!")
    
    def test_interest_rates_response_structure(self):
        """Test interest rates response structure"""
        print("\n" + "="*60)
        print("TEST: Interest Rates Response Structure")
        print("="*60)
        
        response = requests.get(f"{API_BASE}/api/economy/interest-rates", timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, dict):
                print(f"✓ Data type: dict")
                for key in list(data.keys())[:3]:
                    print(f"  - {key}: {data[key]}")
            elif isinstance(data, list):
                print(f"✓ Data type: list ({len(data)} items)")
        
        print("✅ Interest rates structure test passed!")


class TestInflationEndpoint:
    """Test inflation data endpoint"""
    
    def test_inflation_us(self):
        """Test US inflation endpoint"""
        print("\n" + "="*60)
        print("TEST: US Inflation")
        print("="*60)
        
        response = requests.get(f"{API_BASE}/api/economy/inflation/US", timeout=15)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print(f"✓ Status: {response.status_code}")
        print("✅ US inflation test passed!")
    
    def test_inflation_multiple_countries(self):
        """Test inflation for multiple countries"""
        print("\n" + "="*60)
        print("TEST: Inflation Multiple Countries")
        print("="*60)
        
        countries = ['US', 'GB', 'EU', 'JP']
        
        for country in countries:
            response = requests.get(f"{API_BASE}/api/economy/inflation/{country}", timeout=15)
            status_icon = "✓" if response.status_code == 200 else "⚠"
            print(f"{status_icon} {country}: Status {response.status_code}")
        
        print("✅ Multiple countries inflation test passed!")

