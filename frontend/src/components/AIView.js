import React, { useState } from 'react';
import axios from 'axios';
import Plot from 'react-plotly.js';

const API_BASE_URL = 'http://localhost:8000';

function AIView() {
  const [ticker, setTicker] = useState('AAPL');
  const [activeModel, setActiveModel] = useState('overview');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // AI Model Data
  const [forecastData, setForecastData] = useState(null);
  const [volatilityData, setVolatilityData] = useState(null);
  const [indexData, setIndexData] = useState({});

  const runStockForecast = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get(`${API_BASE_URL}/api/ai/stock-forecast/${ticker}`);
      setForecastData(response.data);
    } catch (err) {
      setError(`Error running forecast: ${err.response?.data?.detail || err.message}`);
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const runVolatilityForecast = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get(`${API_BASE_URL}/api/ai/volatility/${ticker}`);
      setVolatilityData(response.data);
    } catch (err) {
      setError(`Error running volatility forecast: ${err.response?.data?.detail || err.message}`);
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const loadIndexChart = async (indexTicker) => {
    if (indexData[indexTicker]) return; // Already loaded
    
    try {
      const response = await axios.get(`${API_BASE_URL}/api/ai/index-chart/${indexTicker}`);
      setIndexData(prev => ({ ...prev, [indexTicker]: response.data }));
    } catch (err) {
      console.error(`Error loading ${indexTicker} chart:`, err);
    }
  };

  const loadAllIndices = async () => {
    setLoading(true);
    try {
      await Promise.all([
        loadIndexChart('SPY'),
        loadIndexChart('DJIA'),
        loadIndexChart('NDAQ'),
        loadIndexChart('IWM')
      ]);
    } catch (err) {
      setError('Error loading indices');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="ai-view">
      <h2>🤖 AI-Powered Predictions</h2>
      
      {/* Ticker Input */}
      <div className="ai-controls">
        <div className="ticker-input-group">
          <label>Stock Ticker:</label>
          <input
            type="text"
            value={ticker}
            onChange={(e) => setTicker(e.target.value.toUpperCase())}
            placeholder="Enter ticker (e.g., AAPL)"
            className="ai-ticker-input"
          />
        </div>
      </div>

      {/* Model Selection */}
      <div className="ai-sections">
        <button
          className={`section-btn ${activeModel === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveModel('overview')}
        >
          Overview
        </button>
        <button
          className={`section-btn ${activeModel === 'price-forecast' ? 'active' : ''}`}
          onClick={() => setActiveModel('price-forecast')}
        >
          Price Forecast (LSTM)
        </button>
        <button
          className={`section-btn ${activeModel === 'volatility' ? 'active' : ''}`}
          onClick={() => setActiveModel('volatility')}
        >
          Volatility (GARCH)
        </button>
        <button
          className={`section-btn ${activeModel === 'indices' ? 'active' : ''}`}
          onClick={() => {
            setActiveModel('indices');
            loadAllIndices();
          }}
        >
          Market Indices
        </button>
      </div>

      {/* Content Area */}
      <div className="ai-content">
        {loading && (
          <div className="loading-ai">
            <div className="spinner"></div>
            <p>Running AI model... This may take 30-60 seconds</p>
          </div>
        )}
        {error && <div className="error">{error}</div>}

        {/* Overview */}
        {activeModel === 'overview' && (
          <div className="ai-overview">
            <h3>AI Models Available</h3>
            <div className="overview-grid">
              <div className="overview-card">
                <h4>📈 Price Forecast</h4>
                <p>LSTM Neural Network predicts next 11 days of stock prices</p>
                <ul>
                  <li>60-day historical data</li>
                  <li>3-layer LSTM architecture</li>
                  <li>70/30 train/test split</li>
                  <li>Forecasts 11 business days ahead</li>
                </ul>
              </div>
              <div className="overview-card">
                <h4>📊 Volatility Forecast</h4>
                <p>GARCH model predicts price volatility</p>
                <ul>
                  <li>2-year historical returns</li>
                  <li>GARCH(2,2) model</li>
                  <li>Rolling 365-day predictions</li>
                  <li>7-day volatility forecast</li>
                </ul>
              </div>
              <div className="overview-card">
                <h4>📉 Market Indices</h4>
                <p>30-day charts for major indices</p>
                <ul>
                  <li>SPY - S&P 500</li>
                  <li>DJIA - Dow Jones</li>
                  <li>NDAQ - Nasdaq</li>
                  <li>IWM - Russell 2000</li>
                </ul>
              </div>
            </div>
            <div className="ai-instructions">
              <p>⚠️ <strong>Note:</strong> AI models can take 30-60 seconds to run. Please be patient.</p>
              <p>💡 Enter a ticker symbol above and select a model to begin.</p>
            </div>
          </div>
        )}

        {/* Price Forecast */}
        {activeModel === 'price-forecast' && (
          <div className="price-forecast-section">
            <h3>LSTM Price Forecast for {ticker}</h3>
            <button onClick={runStockForecast} disabled={loading} className="run-model-btn">
              {loading ? 'Running Model...' : 'Run Price Forecast'}
            </button>
            
            {forecastData && (
              <div className="forecast-results">
                <div className="model-metrics">
                  <h4>Model Performance</h4>
                  <p><strong>Test Set Loss (MSE):</strong> {forecastData.model_evaluation.toFixed(6)}</p>
                </div>
                
                <div className="forecast-charts">
                  <div className="chart-container">
                    <h4>Actual vs Predicted Prices</h4>
                    <Plot 
                      data={forecastData.actual_vs_predicted.data} 
                      layout={forecastData.actual_vs_predicted.layout} 
                      style={{ width: '100%', height: '400px' }}
                    />
                  </div>
                  
                  <div className="chart-container">
                    <h4>11-Day Price Forecast</h4>
                    <Plot 
                      data={forecastData.forecast.data} 
                      layout={forecastData.forecast.layout} 
                      style={{ width: '100%', height: '400px' }}
                    />
                  </div>
                  
                  <div className="chart-container">
                    <h4>Training Loss Over Time</h4>
                    <Plot 
                      data={forecastData.training_loss.data} 
                      layout={forecastData.training_loss.layout} 
                      style={{ width: '100%', height: '300px' }}
                    />
                  </div>
                </div>

                <div className="forecast-table">
                  <h4>Forecast Data</h4>
                  <table>
                    <thead>
                      <tr>
                        <th>Date</th>
                        <th>Predicted Price</th>
                      </tr>
                    </thead>
                    <tbody>
                      {forecastData.forecast_data.map((row, idx) => (
                        <tr key={idx}>
                          <td>{Object.keys(row)[0]}</td>
                          <td>${Object.values(row)[0].toFixed(2)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Volatility Forecast */}
        {activeModel === 'volatility' && (
          <div className="volatility-section">
            <h3>Volatility Forecast for {ticker}</h3>
            <button onClick={runVolatilityForecast} disabled={loading} className="run-model-btn">
              {loading ? 'Running Model...' : 'Run Volatility Forecast'}
            </button>
            
            {volatilityData && (
              <div className="volatility-results">
                <div className="volatility-charts">
                  <div className="chart-container">
                    <h4>Returns Over 2 Years</h4>
                    <Plot 
                      data={volatilityData.returns.data} 
                      layout={volatilityData.returns.layout} 
                      style={{ width: '100%', height: '400px' }}
                    />
                  </div>
                  
                  <div className="chart-container">
                    <h4>Rolling Volatility Predictions (Last 365 Days)</h4>
                    <Plot 
                      data={volatilityData.rolling_volatility.data} 
                      layout={volatilityData.rolling_volatility.layout} 
                      style={{ width: '100%', height: '400px' }}
                    />
                  </div>
                  
                  <div className="chart-container">
                    <h4>7-Day Volatility Forecast</h4>
                    <Plot 
                      data={volatilityData.forecast.data} 
                      layout={volatilityData.forecast.layout} 
                      style={{ width: '100%', height: '400px' }}
                    />
                  </div>
                </div>

                <div className="model-summary">
                  <h4>GARCH Model Summary</h4>
                  <pre>{volatilityData.model_summary}</pre>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Market Indices */}
        {activeModel === 'indices' && (
          <div className="indices-section">
            <h3>Major Market Indices (30 Days)</h3>
            <div className="indices-grid">
              {['SPY', 'DJIA', 'NDAQ', 'IWM'].map(index => (
                <div key={index} className="index-chart">
                  <h4>{index}</h4>
                  {indexData[index] ? (
                    <Plot 
                      data={indexData[index].chart.data} 
                      layout={indexData[index].chart.layout} 
                      style={{ width: '100%', height: '300px' }}
                    />
                  ) : (
                    <div className="loading-small">Loading...</div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default AIView;
