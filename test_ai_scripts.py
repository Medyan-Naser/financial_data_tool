#!/usr/bin/env python3
"""
Test script for AI/ML models
Tests both the stock forecast (LSTM) and volatility (GARCH) models
"""

import sys
import os

# Add AI_ML directory to path
AI_ML_PATH = os.path.join(os.path.dirname(__file__), 'AI_ML')
sys.path.insert(0, os.path.join(AI_ML_PATH, 'AI'))

def test_stock_forecast(ticker='AAPL'):
    """Test LSTM stock price forecast"""
    print(f"\n{'='*60}")
    print(f"Testing Stock Forecast (LSTM) for {ticker}")
    print(f"{'='*60}\n")
    
    try:
        from stock_ml_model import get_ml_model
        
        print(f"📊 Running ML model for {ticker}...")
        print("⏳ This will take 30-60 seconds...\n")
        
        model_evaluation, ml_plot, forecast_plot, loss_plot, forecast_df = get_ml_model(ticker)
        
        print("✅ SUCCESS!\n")
        print(f"📈 Model Evaluation (MSE): {model_evaluation:.6f}")
        print(f"\n📅 11-Day Forecast:")
        print(forecast_df)
        print(f"\n📊 Forecast Data Type: {type(forecast_df)}")
        print(f"📊 Forecast Shape: {forecast_df.shape}")
        print(f"📊 Has NaN values: {forecast_df.isna().any().any()}")
        
        # Check for NaN
        if forecast_df.isna().any().any():
            print("\n⚠️  WARNING: Forecast contains NaN values!")
            print("NaN locations:")
            print(forecast_df[forecast_df.isna().any(axis=1)])
        else:
            print("\n✅ No NaN values - forecast is clean!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_volatility_forecast(ticker='AAPL'):
    """Test GARCH volatility forecast"""
    print(f"\n{'='*60}")
    print(f"Testing Volatility Forecast (GARCH) for {ticker}")
    print(f"{'='*60}\n")
    
    try:
        from predict_volatility import predict_volatility
        
        print(f"📊 Running GARCH model for {ticker}...")
        print("⏳ This will take 15-30 seconds...\n")
        
        returns_plot, model_summary, rolling_volatility_plot, forecast_plot = predict_volatility(ticker)
        
        print("✅ SUCCESS!\n")
        print("📈 GARCH Model Summary:")
        print(model_summary)
        print(f"\n✅ All plots generated successfully!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_index_chart(ticker='SPY'):
    """Test 30-day index chart"""
    print(f"\n{'='*60}")
    print(f"Testing Index Chart for {ticker}")
    print(f"{'='*60}\n")
    
    try:
        from predict_volatility import go_generate_index_chart
        
        print(f"📊 Generating index chart for {ticker}...")
        
        chart = go_generate_index_chart(ticker)
        
        print("✅ SUCCESS!")
        print(f"📊 Chart generated for {ticker}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("🧪 AI/ML MODELS TEST SUITE")
    print("="*60)
    print("\nThis will test all AI models to ensure they work correctly.")
    print("Expected runtime: ~2 minutes total\n")
    
    results = {}
    
    # Test 1: Stock Forecast
    results['stock_forecast'] = test_stock_forecast('AAPL')
    
    # Test 2: Volatility Forecast
    results['volatility'] = test_volatility_forecast('AAPL')
    
    # Test 3: Index Chart
    results['index_chart'] = test_index_chart('SPY')
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60 + "\n")
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:20s}: {status}")
    
    all_passed = all(results.values())
    
    print("\n" + "="*60)
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
        print("\nYour AI models are working correctly.")
        print("You can now use them in the web interface.")
    else:
        print("⚠️  SOME TESTS FAILED")
        print("\nPlease check the errors above.")
        print("Common issues:")
        print("  - Yahoo Finance rate limiting (wait 2-3 minutes)")
        print("  - Missing dependencies (run: pip install tensorflow keras arch)")
        print("  - Invalid ticker symbol")
    print("="*60 + "\n")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
