import React, { useState } from 'react';
import axios from 'axios';
import Plot from 'react-plotly.js';
import DraggableResizablePanel from './DraggableResizablePanel';

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
  
  // Panel state for draggable/resizable charts
  const [chartPanels, setChartPanels] = useState({
    actualVsPredicted: { position: { x: 20, y: 20 }, size: { width: 800, height: 450 } },
    forecast: { position: { x: 20, y: 490 }, size: { width: 800, height: 450 } },
    trainingLoss: { position: { x: 20, y: 960 }, size: { width: 800, height: 350 } },
    forecastTable: { position: { x: 840, y: 20 }, size: { width: 400, height: 500 } },
    returns: { position: { x: 20, y: 20 }, size: { width: 800, height: 450 } },
    rollingVolatility: { position: { x: 20, y: 490 }, size: { width: 800, height: 450 } },
    volatilityForecast: { position: { x: 20, y: 960 }, size: { width: 800, height: 450 } },
    garchSummary: { position: { x: 840, y: 20 }, size: { width: 500, height: 600 } },
    indexSPY: { position: { x: 20, y: 20 }, size: { width: 600, height: 400 } },
    indexDJIA: { position: { x: 640, y: 20 }, size: { width: 600, height: 400 } },
    indexNDAQ: { position: { x: 20, y: 440 }, size: { width: 600, height: 400 } },
    indexIWM: { position: { x: 640, y: 440 }, size: { width: 600, height: 400 } },
  });
  
  const updatePanelPosition = (panelId, position) => {
    setChartPanels(prev => ({
      ...prev,
      [panelId]: { ...prev[panelId], position }
    }));
  };
  
  const updatePanelSize = (panelId, size) => {
    setChartPanels(prev => ({
      ...prev,
      [panelId]: { ...prev[panelId], size }
    }));
  };

  const runStockForecast = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get(`${API_BASE_URL}/api/ai/stock-forecast/${ticker}`);
      setForecastData(response.data);
    } catch (err) {
      const errorMsg = err.response?.data?.detail || err.message;
      if (errorMsg.includes('rate limit') || errorMsg.includes('Too Many Requests')) {
        setError(`⚠️ Yahoo Finance rate limit exceeded. Please wait 2-3 minutes and try again. Tip: Try a different ticker or wait before retrying.`);
      } else {
        setError(`Error running forecast: ${errorMsg}`);
      }
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
      const errorMsg = err.response?.data?.detail || err.message;
      if (errorMsg.includes('rate limit') || errorMsg.includes('Too Many Requests')) {
        setError(`⚠️ Yahoo Finance rate limit exceeded. Please wait 2-3 minutes and try again. Tip: Try a different ticker or wait before retrying.`);
      } else {
        setError(`Error running volatility forecast: ${errorMsg}`);
      }
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
              <div className="overview-card" onClick={() => setActiveModel('price-forecast')} style={{ cursor: 'pointer' }}>
                <h4>📈 Price Forecast</h4>
                <p>LSTM Neural Network predicts next 11 days of stock prices</p>
                <ul>
                  <li>60-day historical data</li>
                  <li>3-layer LSTM architecture</li>
                  <li>70/30 train/test split</li>
                  <li>Forecasts 11 business days ahead</li>
                </ul>
              </div>
              <div className="overview-card" onClick={() => setActiveModel('volatility')} style={{ cursor: 'pointer' }}>
                <h4>📊 Volatility Forecast</h4>
                <p>GARCH model predicts price volatility</p>
                <ul>
                  <li>2-year historical returns</li>
                  <li>GARCH(2,2) model</li>
                  <li>Rolling 365-day predictions</li>
                  <li>7-day volatility forecast</li>
                </ul>
              </div>
              <div className="overview-card" onClick={() => { setActiveModel('indices'); loadAllIndices(); }} style={{ cursor: 'pointer' }}>
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
                
                <div className="forecast-charts" style={{ position: 'relative', minHeight: '1400px' }}>
                  <DraggableResizablePanel
                    id="actualVsPredicted"
                    position={chartPanels.actualVsPredicted.position}
                    size={chartPanels.actualVsPredicted.size}
                    onPositionChange={(pos) => updatePanelPosition('actualVsPredicted', pos)}
                    onSizeChange={(size) => updatePanelSize('actualVsPredicted', size)}
                    minWidth={400}
                    minHeight={300}
                  >
                    <div className="chart-container">
                      <h4>Actual vs Predicted Prices</h4>
                      <Plot 
                        data={forecastData.actual_vs_predicted.data} 
                        layout={forecastData.actual_vs_predicted.layout} 
                        style={{ width: '100%', height: 'calc(100% - 40px)' }}
                        useResizeHandler={true}
                      />
                    </div>
                  </DraggableResizablePanel>
                  
                  <DraggableResizablePanel
                    id="forecast"
                    position={chartPanels.forecast.position}
                    size={chartPanels.forecast.size}
                    onPositionChange={(pos) => updatePanelPosition('forecast', pos)}
                    onSizeChange={(size) => updatePanelSize('forecast', size)}
                    minWidth={400}
                    minHeight={300}
                  >
                    <div className="chart-container">
                      <h4>11-Day Price Forecast</h4>
                      <Plot 
                        data={forecastData.forecast.data} 
                        layout={forecastData.forecast.layout} 
                        style={{ width: '100%', height: 'calc(100% - 40px)' }}
                        useResizeHandler={true}
                      />
                    </div>
                  </DraggableResizablePanel>
                  
                  <DraggableResizablePanel
                    id="trainingLoss"
                    position={chartPanels.trainingLoss.position}
                    size={chartPanels.trainingLoss.size}
                    onPositionChange={(pos) => updatePanelPosition('trainingLoss', pos)}
                    onSizeChange={(size) => updatePanelSize('trainingLoss', size)}
                    minWidth={400}
                    minHeight={250}
                  >
                    <div className="chart-container">
                      <h4>Training Loss Over Time</h4>
                      <Plot 
                        data={forecastData.training_loss.data} 
                        layout={forecastData.training_loss.layout} 
                        style={{ width: '100%', height: 'calc(100% - 40px)' }}
                        useResizeHandler={true}
                      />
                    </div>
                  </DraggableResizablePanel>
                </div>

                <DraggableResizablePanel
                  id="forecastTable"
                  position={chartPanels.forecastTable.position}
                  size={chartPanels.forecastTable.size}
                  onPositionChange={(pos) => updatePanelPosition('forecastTable', pos)}
                  onSizeChange={(size) => updatePanelSize('forecastTable', size)}
                  minWidth={350}
                  minHeight={300}
                >
                  <div className="forecast-table" style={{ height: '100%', overflow: 'auto' }}>
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
                </DraggableResizablePanel>
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
                <div className="volatility-charts" style={{ position: 'relative', minHeight: '1400px' }}>
                  <DraggableResizablePanel
                    id="returns"
                    position={chartPanels.returns.position}
                    size={chartPanels.returns.size}
                    onPositionChange={(pos) => updatePanelPosition('returns', pos)}
                    onSizeChange={(size) => updatePanelSize('returns', size)}
                    minWidth={400}
                    minHeight={300}
                  >
                    <div className="chart-container">
                      <h4>Returns Over 2 Years</h4>
                      <Plot 
                        data={volatilityData.returns.data} 
                        layout={volatilityData.returns.layout} 
                        style={{ width: '100%', height: 'calc(100% - 40px)' }}
                        useResizeHandler={true}
                      />
                    </div>
                  </DraggableResizablePanel>
                  
                  <DraggableResizablePanel
                    id="rollingVolatility"
                    position={chartPanels.rollingVolatility.position}
                    size={chartPanels.rollingVolatility.size}
                    onPositionChange={(pos) => updatePanelPosition('rollingVolatility', pos)}
                    onSizeChange={(size) => updatePanelSize('rollingVolatility', size)}
                    minWidth={400}
                    minHeight={300}
                  >
                    <div className="chart-container">
                      <h4>Rolling Volatility Predictions (Last 365 Days)</h4>
                      <Plot 
                        data={volatilityData.rolling_volatility.data} 
                        layout={volatilityData.rolling_volatility.layout} 
                        style={{ width: '100%', height: 'calc(100% - 40px)' }}
                        useResizeHandler={true}
                      />
                    </div>
                  </DraggableResizablePanel>
                  
                  <DraggableResizablePanel
                    id="volatilityForecast"
                    position={chartPanels.volatilityForecast.position}
                    size={chartPanels.volatilityForecast.size}
                    onPositionChange={(pos) => updatePanelPosition('volatilityForecast', pos)}
                    onSizeChange={(size) => updatePanelSize('volatilityForecast', size)}
                    minWidth={400}
                    minHeight={300}
                  >
                    <div className="chart-container">
                      <h4>7-Day Volatility Forecast</h4>
                      <Plot 
                        data={volatilityData.forecast.data} 
                        layout={volatilityData.forecast.layout} 
                        style={{ width: '100%', height: 'calc(100% - 40px)' }}
                        useResizeHandler={true}
                      />
                    </div>
                  </DraggableResizablePanel>
                </div>

                <DraggableResizablePanel
                  id="garchSummary"
                  position={chartPanels.garchSummary.position}
                  size={chartPanels.garchSummary.size}
                  onPositionChange={(pos) => updatePanelPosition('garchSummary', pos)}
                  onSizeChange={(size) => updatePanelSize('garchSummary', size)}
                  minWidth={400}
                  minHeight={300}
                >
                  <div className="model-summary" style={{ height: '100%', overflow: 'auto' }}>
                    <h4>GARCH Model Summary</h4>
                    <pre style={{ whiteSpace: 'pre-wrap', wordWrap: 'break-word' }}>{volatilityData.model_summary}</pre>
                  </div>
                </DraggableResizablePanel>
              </div>
            )}
          </div>
        )}

        {/* Market Indices */}
        {activeModel === 'indices' && (
          <div className="indices-section" style={{ position: 'relative', minHeight: '900px' }}>
            <h3>Major Market Indices (30 Days)</h3>
            {['SPY', 'DJIA', 'NDAQ', 'IWM'].map(index => (
              <DraggableResizablePanel
                key={index}
                id={`index${index}`}
                position={chartPanels[`index${index}`].position}
                size={chartPanels[`index${index}`].size}
                onPositionChange={(pos) => updatePanelPosition(`index${index}`, pos)}
                onSizeChange={(size) => updatePanelSize(`index${index}`, size)}
                minWidth={400}
                minHeight={300}
              >
                <div className="index-chart" style={{ height: '100%' }}>
                  <h4>{index}</h4>
                  {indexData[index] ? (
                    <Plot 
                      data={indexData[index].chart.data} 
                      layout={indexData[index].chart.layout} 
                      style={{ width: '100%', height: 'calc(100% - 40px)' }}
                      useResizeHandler={true}
                    />
                  ) : (
                    <div className="loading-small">Loading...</div>
                  )}
                </div>
              </DraggableResizablePanel>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default AIView;
