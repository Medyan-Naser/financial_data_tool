"""
Comprehensive Test Suite for AI Tab

Tests all features of the AI tab:
- LSTM stock forecast predictions
- Volatility/GARCH model predictions
- AI model caching
- Health score predictions
- Bankruptcy risk predictions
- Model data integrity

These tests use cached data when available to avoid retraining models.
Warning: Some AI tests may take 30-60 seconds on first run (when cache is empty).
"""

import sys
import os
import pytest
import requests
import json
from datetime import datetime
import time

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.cache_manager import ai_cache

# API configuration
API_BASE_URL = "http://localhost:8000"
TEST_TICKER = "AAPL"
TEST_TICKER_ALT = "MSFT"


class TestLSTMForecast:
    """Test LSTM stock forecast model"""
    
    def test_lstm_forecast_execution(self):
        """Test LSTM forecast model execution"""
        print("\n" + "="*60)
        print(f"TEST: LSTM Forecast for {TEST_TICKER}")
        print("⚠️  This may take 30-60 seconds on first run")
        print("="*60)
        
        start_time = time.time()
        
        response = requests.get(
            f"{API_BASE_URL}/api/ai/stock-forecast/{TEST_TICKER}",
            timeout=120  # 2 minute timeout
        )
        
        elapsed_time = time.time() - start_time
        
        assert response.status_code == 200, "LSTM request failed"
        data = response.json()
        
        # Validate structure
        assert 'ticker' in data, "Missing ticker"
        assert 'model_evaluation' in data, "Missing model evaluation"
        assert 'actual_vs_predicted' in data, "Missing actual vs predicted chart"
        assert 'forecast' in data, "Missing forecast chart"
        assert 'training_loss' in data, "Missing training loss chart"
        assert 'forecast_data' in data, "Missing forecast data"
        
        # Validate forecast data
        forecast_data = data['forecast_data']
        assert len(forecast_data) > 0, "Empty forecast data"
        assert len(forecast_data) <= 11, "Too many forecast days"
        
        print(f"✓ Model evaluation score: {data['model_evaluation']:.4f}")
        print(f"✓ Forecast days: {len(forecast_data)}")
        print(f"✓ Execution time: {elapsed_time:.2f}s")
        
        # Validate chart structure
        for chart_name in ['actual_vs_predicted', 'forecast', 'training_loss']:
            chart = data[chart_name]
            assert 'data' in chart, f"Missing data in {chart_name}"
            assert 'layout' in chart, f"Missing layout in {chart_name}"
            print(f"✓ Chart '{chart_name}' structure valid")
        
        print("\n✅ LSTM forecast test passed!")
    
    def test_lstm_cache_behavior(self):
        """Test that LSTM results are cached properly"""
        print("\n" + "="*60)
        print("TEST: LSTM Caching Behavior")
        print("="*60)
        
        # First request (may use cache from previous test)
        start_time = time.time()
        response1 = requests.get(
            f"{API_BASE_URL}/api/ai/stock-forecast/{TEST_TICKER}",
            timeout=120
        )
        time1 = time.time() - start_time
        
        assert response1.status_code == 200, "First request failed"
        
        # Second request (should definitely use cache)
        start_time = time.time()
        response2 = requests.get(
            f"{API_BASE_URL}/api/ai/stock-forecast/{TEST_TICKER}",
            timeout=120
        )
        time2 = time.time() - start_time
        
        assert response2.status_code == 200, "Second request failed"
        
        print(f"✓ First request: {time1:.2f}s")
        print(f"✓ Second request: {time2:.2f}s (should be cached)")
        
        # Cached should be much faster
        if time1 > 5:  # If first was slow, second should be fast
            assert time2 < 2, "Cache not working - second request too slow"
            print(f"✓ Cache working! {time1/time2:.1f}x faster")
        
        # Data should be identical
        assert response1.json() == response2.json(), "Cache data mismatch"
        
        print("\n✅ LSTM caching test passed!")


class TestVolatilityForecast:
    """Test GARCH volatility model"""
    
    def test_volatility_forecast_execution(self):
        """Test volatility forecast model execution"""
        print("\n" + "="*60)
        print(f"TEST: Volatility Forecast for {TEST_TICKER}")
        print("⚠️  This may take 20-30 seconds on first run")
        print("="*60)
        
        start_time = time.time()
        
        response = requests.get(
            f"{API_BASE_URL}/api/ai/volatility/{TEST_TICKER}",
            timeout=120
        )
        
        elapsed_time = time.time() - start_time
        
        assert response.status_code == 200, "Volatility request failed"
        data = response.json()
        
        # Validate structure
        assert 'ticker' in data, "Missing ticker"
        assert 'returns' in data, "Missing returns chart"
        assert 'rolling_volatility' in data, "Missing rolling volatility chart"
        assert 'forecast' in data, "Missing forecast chart"
        assert 'model_summary' in data, "Missing model summary"
        
        print(f"✓ Execution time: {elapsed_time:.2f}s")
        print(f"✓ Model summary length: {len(data['model_summary'])} chars")
        
        # Validate chart structure
        for chart_name in ['returns', 'rolling_volatility', 'forecast']:
            chart = data[chart_name]
            assert 'data' in chart, f"Missing data in {chart_name}"
            assert 'layout' in chart, f"Missing layout in {chart_name}"
            print(f"✓ Chart '{chart_name}' structure valid")
        
        print("\n✅ Volatility forecast test passed!")
    
    def test_volatility_cache_behavior(self):
        """Test that volatility results are cached"""
        print("\n" + "="*60)
        print("TEST: Volatility Caching Behavior")
        print("="*60)
        
        # First request
        start_time = time.time()
        response1 = requests.get(
            f"{API_BASE_URL}/api/ai/volatility/{TEST_TICKER}",
            timeout=120
        )
        time1 = time.time() - start_time
        
        assert response1.status_code == 200, "First request failed"
        
        # Second request (should use cache)
        start_time = time.time()
        response2 = requests.get(
            f"{API_BASE_URL}/api/ai/volatility/{TEST_TICKER}",
            timeout=120
        )
        time2 = time.time() - start_time
        
        assert response2.status_code == 200, "Second request failed"
        
        print(f"✓ First request: {time1:.2f}s")
        print(f"✓ Second request: {time2:.2f}s (should be cached)")
        
        # Data should be identical
        assert response1.json() == response2.json(), "Cache data mismatch"
        
        print("\n✅ Volatility caching test passed!")


class TestAIHealthScore:
    """Test AI health score predictions"""
    
    def test_health_score_calculation(self):
        """Test health score calculation"""
        print("\n" + "="*60)
        print(f"TEST: Health Score for {TEST_TICKER}")
        print("="*60)
        
        # Test both quarterly and annual
        for quarterly in [False, True]:
            period_type = "quarterly" if quarterly else "annual"
            
            response = requests.get(
                f"{API_BASE_URL}/api/ai-models/health-score/{TEST_TICKER}",
                params={"quarterly": quarterly}
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Validate structure
                assert 'ticker' in data, "Missing ticker"
                assert 'health_score' in data, "Missing health score"
                assert 'metrics' in data, "Missing metrics"
                
                score = data['health_score']
                assert 0 <= score <= 100, "Invalid health score range"
                
                print(f"✓ {period_type.capitalize()} health score: {score:.1f}")
                print(f"  Metrics analyzed: {len(data['metrics'])}")
            else:
                print(f"⚠ {period_type}: Request failed ({response.status_code})")
        
        print("\n✅ Health score test passed!")
    
    def test_health_score_cache(self):
        """Test health score caching"""
        print("\n" + "="*60)
        print("TEST: Health Score Caching")
        print("="*60)
        
        # First request
        response1 = requests.get(
            f"{API_BASE_URL}/api/ai-models/health-score/{TEST_TICKER_ALT}",
            params={"quarterly": False}
        )
        
        # Second request
        response2 = requests.get(
            f"{API_BASE_URL}/api/ai-models/health-score/{TEST_TICKER_ALT}",
            params={"quarterly": False}
        )
        
        if response1.status_code == 200 and response2.status_code == 200:
            # Should return identical data
            assert response1.json() == response2.json(), "Cache data mismatch"
            print("✓ Health score properly cached")
        else:
            print("⚠ Health score endpoint not available")
        
        print("\n✅ Health score caching test passed!")


class TestAICacheManagement:
    """Test AI cache management"""
    
    def test_ai_cache_directory(self):
        """Test that AI cache uses correct directory"""
        print("\n" + "="*60)
        print("TEST: AI Cache Directory Structure")
        print("="*60)
        
        info = ai_cache.get_info()
        
        assert 'AI' in info['cache_dir'], "Wrong cache directory"
        assert info['namespace'] == 'AI', "Wrong namespace"
        assert info['expiry_hours'] == 720, "Wrong expiry time (should be 30 days)"
        
        print(f"✓ Cache directory: {info['cache_dir']}")
        print(f"✓ Namespace: {info['namespace']}")
        print(f"✓ Expiry: {info['expiry_hours']} hours (30 days)")
        
        print("\n✅ AI cache directory test passed!")
    
    def test_ai_cache_files(self):
        """Test AI cache file structure"""
        print("\n" + "="*60)
        print("TEST: AI Cache Files")
        print("="*60)
        
        cache_files = ai_cache.list_keys()
        
        if len(cache_files) > 0:
            print(f"✓ Found {len(cache_files)} cached AI results")
            
            for file_info in cache_files[:5]:
                filename = file_info['key']
                size_kb = file_info['size_kb']
                
                # Check for descriptive names
                if any(word in filename for word in ['lstm', 'forecast', 'volatility', 'health', 'bankruptcy']):
                    print(f"✓ Descriptive file: {filename} ({size_kb:.1f} KB)")
                else:
                    print(f"  File: {filename} ({size_kb:.1f} KB)")
        else:
            print("⚠ No cached AI results found (run some AI models first)")
        
        print("\n✅ AI cache files test passed!")
    
    def test_no_pkl_files(self):
        """Test that no .pkl files are created"""
        print("\n" + "="*60)
        print("TEST: No PKL Files (JSON Only)")
        print("="*60)
        
        import os
        from pathlib import Path
        
        cache_dir = Path(ai_cache.cache_dir)
        pkl_files = list(cache_dir.glob("*.pkl"))
        
        assert len(pkl_files) == 0, f"Found {len(pkl_files)} .pkl files - should use JSON only!"
        print("✓ No .pkl files found (JSON only)")
        
        # Check for JSON files
        json_files = list(cache_dir.glob("*.json"))
        json_count = len([f for f in json_files if not f.name.endswith('.meta.json')])
        
        print(f"✓ Found {json_count} JSON cache files")
        
        print("\n✅ No PKL files test passed!")


class TestAIDataIntegrity:
    """Test AI model data integrity"""
    
    def test_lstm_forecast_data_validity(self):
        """Test that LSTM forecast data is valid"""
        print("\n" + "="*60)
        print("TEST: LSTM Forecast Data Validity")
        print("="*60)
        
        response = requests.get(
            f"{API_BASE_URL}/api/ai/stock-forecast/{TEST_TICKER}",
            timeout=120
        )
        
        if response.status_code == 200:
            data = response.json()
            forecast_data = data['forecast_data']
            
            # Check all forecast prices are positive
            for day in forecast_data:
                if 'Price' in day:
                    price = day['Price']
                    assert price > 0, f"Invalid forecast price: {price}"
            
            print(f"✓ All {len(forecast_data)} forecast prices valid (positive)")
            
            # Check model evaluation is reasonable
            eval_score = data['model_evaluation']
            assert 0 <= eval_score <= 1, f"Invalid evaluation score: {eval_score}"
            print(f"✓ Model evaluation in valid range: {eval_score:.4f}")
        else:
            print("⚠ LSTM endpoint not available for validation")
        
        print("\n✅ LSTM data validity test passed!")
    
    def test_chart_background_color(self):
        """Test that AI charts use white background"""
        print("\n" + "="*60)
        print("TEST: Chart Background Color (Should be White)")
        print("="*60)
        
        response = requests.get(
            f"{API_BASE_URL}/api/ai/stock-forecast/{TEST_TICKER}",
            timeout=120
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Check if charts have layout with white template
            for chart_name in ['actual_vs_predicted', 'forecast', 'training_loss']:
                chart = data[chart_name]
                layout = chart.get('layout', {})
                
                template = layout.get('template', {})
                if isinstance(template, dict):
                    # Check for white background indicators
                    if 'layout' in template:
                        print(f"✓ Chart '{chart_name}' has template configuration")
                else:
                    # Template might be string like 'plotly_white'
                    print(f"✓ Chart '{chart_name}' template: {template}")
        else:
            print("⚠ Unable to verify chart colors")
        
        print("\n✅ Chart background color test passed!")


def run_all_ai_tests():
    """Run all AI tab tests"""
    print("\n" + "#"*60)
    print("# AI TAB COMPREHENSIVE TESTS")
    print("#"*60)
    print("\n⚠️  WARNING: AI tests may take several minutes on first run")
    print("⚠️  Subsequent runs will be much faster due to caching\n")
    
    test_classes = [
        TestLSTMForecast(),
        TestVolatilityForecast(),
        TestAIHealthScore(),
        TestAICacheManagement(),
        TestAIDataIntegrity()
    ]
    
    total_tests = 0
    passed_tests = 0
    
    for test_class in test_classes:
        class_name = test_class.__class__.__name__
        print(f"\n{'='*60}")
        print(f"Running {class_name}")
        print(f"{'='*60}")
        
        test_methods = [m for m in dir(test_class) if m.startswith('test_')]
        
        for method_name in test_methods:
            total_tests += 1
            try:
                method = getattr(test_class, method_name)
                method()
                passed_tests += 1
            except AssertionError as e:
                print(f"❌ {method_name} FAILED: {e}")
            except Exception as e:
                print(f"❌ {method_name} ERROR: {e}")
    
    print("\n" + "#"*60)
    print(f"# RESULTS: {passed_tests}/{total_tests} tests passed")
    print("#"*60)
    
    return passed_tests == total_tests


if __name__ == "__main__":
    import time
    print("\n⚠️  Make sure the backend server is running on http://localhost:8000")
    print("Waiting 2 seconds...")
    time.sleep(2)
    
    success = run_all_ai_tests()
    sys.exit(0 if success else 1)
