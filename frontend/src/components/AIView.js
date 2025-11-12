import React, { useState } from 'react';
import axios from 'axios';
import Plot from 'react-plotly.js';
import DraggableResizablePanel from './DraggableResizablePanel';
import AIModels from './AIModels';

const API_BASE_URL = 'http://localhost:8000';

function AIView() {
  const [ticker, setTicker] = useState('AAPL');
  const [activeModel, setActiveModel] = useState('overview');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // AI Model Data
  const [forecastData, setForecastData] = useState(null);
  const [volatilityData, setVolatilityData] = useState(null);
  
  // Z-index management for panels
  const [activePanelId, setActivePanelId] = useState(null);
  const [panelZIndexes, setPanelZIndexes] = useState({});
  
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

  // Handle panel focus - bring to front
  const handlePanelFocus = (panelId) => {
    setActivePanelId(panelId);
    // Assign z-index based on order of interaction
    setPanelZIndexes(prev => {
      const maxZ = Math.max(1, ...Object.values(prev));
      return {
        ...prev,
        [panelId]: maxZ + 1
      };
    });
  };

  // Get z-index for a panel (default to 1 if not set)
  const getPanelZIndex = (panelId) => {
    return panelZIndexes[panelId] || 1;
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
          className={`section-btn ${activeModel === 'ai-models' ? 'active' : ''}`}
          onClick={() => setActiveModel('ai-models')}
        >
          🤖 AI Analysis
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
              <div className="overview-card" onClick={() => setActiveModel('ai-models')} style={{ cursor: 'pointer' }}>
                <h4>🤖 AI Financial Analysis</h4>
                <p>Advanced ML models for comprehensive financial analysis</p>
                <ul>
                  <li>Financial Health Score (0-100)</li>
                  <li>Bankruptcy Risk Analysis</li>
                  <li>Trend Detection & Forecasting</li>
                  <li>Anomaly Detection</li>
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
                    onFocus={handlePanelFocus}
                    zIndex={getPanelZIndex('actualVsPredicted')}
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
                      config={{ responsive: true }}
                      />
                    </div>
                  </DraggableResizablePanel>
                  
                  <DraggableResizablePanel
                    id="forecast"
                    position={chartPanels.forecast.position}
                    size={chartPanels.forecast.size}
                    onPositionChange={(pos) => updatePanelPosition('forecast', pos)}
                    onSizeChange={(size) => updatePanelSize('forecast', size)}
                    onFocus={handlePanelFocus}
                    zIndex={getPanelZIndex('forecast')}
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
                      config={{ responsive: true }}
                      />
                    </div>
                  </DraggableResizablePanel>
                  
                  <DraggableResizablePanel
                    id="trainingLoss"
                    position={chartPanels.trainingLoss.position}
                    size={chartPanels.trainingLoss.size}
                    onPositionChange={(pos) => updatePanelPosition('trainingLoss', pos)}
                    onSizeChange={(size) => updatePanelSize('trainingLoss', size)}
                    onFocus={handlePanelFocus}
                    zIndex={getPanelZIndex('trainingLoss')}
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
                      config={{ responsive: true }}
                      />
                    </div>
                  </DraggableResizablePanel>

                  <DraggableResizablePanel
                    id="forecastTable"
                    position={chartPanels.forecastTable.position}
                    size={chartPanels.forecastTable.size}
                    onPositionChange={(pos) => updatePanelPosition('forecastTable', pos)}
                    onSizeChange={(size) => updatePanelSize('forecastTable', size)}
                    onFocus={handlePanelFocus}
                    zIndex={getPanelZIndex('forecastTable')}
                    minWidth={350}
                    minHeight={300}
                  >
                    <div className="forecast-table" style={{ height: '100%', overflow: 'auto' }}>
                      <h4>Forecast Data</h4>
                      <div className="table-wrapper">
                        <table className="financial-table">
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
                  </DraggableResizablePanel>
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
                <div className="volatility-charts" style={{ position: 'relative', minHeight: '1400px' }}>
                  <DraggableResizablePanel
                    id="returns"
                    position={chartPanels.returns.position}
                    size={chartPanels.returns.size}
                    onPositionChange={(pos) => updatePanelPosition('returns', pos)}
                    onSizeChange={(size) => updatePanelSize('returns', size)}
                    onFocus={handlePanelFocus}
                    zIndex={getPanelZIndex('returns')}
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
                      config={{ responsive: true }}
                      />
                    </div>
                  </DraggableResizablePanel>
                  
                  <DraggableResizablePanel
                    id="rollingVolatility"
                    position={chartPanels.rollingVolatility.position}
                    size={chartPanels.rollingVolatility.size}
                    onPositionChange={(pos) => updatePanelPosition('rollingVolatility', pos)}
                    onSizeChange={(size) => updatePanelSize('rollingVolatility', size)}
                    onFocus={handlePanelFocus}
                    zIndex={getPanelZIndex('rollingVolatility')}
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
                      config={{ responsive: true }}
                      />
                    </div>
                  </DraggableResizablePanel>
                  
                  <DraggableResizablePanel
                    id="volatilityForecast"
                    position={chartPanels.volatilityForecast.position}
                    size={chartPanels.volatilityForecast.size}
                    onPositionChange={(pos) => updatePanelPosition('volatilityForecast', pos)}
                    onSizeChange={(size) => updatePanelSize('volatilityForecast', size)}
                    onFocus={handlePanelFocus}
                    zIndex={getPanelZIndex('volatilityForecast')}
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
                      config={{ responsive: true }}
                      />
                    </div>
                  </DraggableResizablePanel>

                  <DraggableResizablePanel
                    id="garchSummary"
                    position={chartPanels.garchSummary.position}
                    size={chartPanels.garchSummary.size}
                    onPositionChange={(pos) => updatePanelPosition('garchSummary', pos)}
                    onSizeChange={(size) => updatePanelSize('garchSummary', size)}
                    onFocus={handlePanelFocus}
                    zIndex={getPanelZIndex('garchSummary')}
                    minWidth={400}
                    minHeight={300}
                  >
                    <div className="model-summary" style={{ height: '100%', overflow: 'auto' }}>
                      <h4>GARCH Model Summary</h4>
                      <pre style={{ whiteSpace: 'pre-wrap', wordWrap: 'break-word' }}>{volatilityData.model_summary}</pre>
                    </div>
                  </DraggableResizablePanel>
                </div>
              </div>
            )}
          </div>
        )}


        {/* AI Models */}
        {activeModel === 'ai-models' && (
          <AIModels ticker={ticker} />
        )}
      </div>
    </div>
  );
}

export default AIView;
