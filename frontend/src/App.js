import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';
import FinancialTable from './components/FinancialTable';
import ChartManager from './components/ChartManager';
import TickerSearch from './components/TickerSearch';
import DraggableResizablePanel from './components/DraggableResizablePanel';
import AlignmentGuides from './components/AlignmentGuides';
import MacroView from './components/MacroView';
import AIView from './components/AIView';
import DataCollectionProgress from './components/DataCollectionProgress';
import { checkCacheStatus, getCachedFinancialData, collectFinancialData, refreshFinancialData } from './api';

const API_BASE_URL = 'http://localhost:8000';

function App() {
  const [availableTickers, setAvailableTickers] = useState([]);
  const [selectedTicker, setSelectedTicker] = useState(null);
  const [financialData, setFinancialData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeMainTab, setActiveMainTab] = useState('stocks'); // Main navigation: stocks, economy, ai
  const [activeTab, setActiveTab] = useState('income_statement');
  const [charts, setCharts] = useState([]);
  const [tablePanel, setTablePanel] = useState({
    position: { x: 20, y: 20 },
    size: { width: 1000, height: 700 }
  });
  const [chartPanels, setChartPanels] = useState({});
  const [draggingPanel, setDraggingPanel] = useState(null);
  const [alignmentGuides, setAlignmentGuides] = useState([]);
  
  // New state for caching and progress
  const [isCollecting, setIsCollecting] = useState(false);
  const [collectionProgress, setCollectionProgress] = useState({ status: '', message: '', progress: 0 });
  const [isCached, setIsCached] = useState(false);
  const [quarterly, setQuarterly] = useState(false); // Toggle for quarterly vs annual data

  // Fetch available tickers on mount
  useEffect(() => {
    const fetchTickers = async () => {
      try {
        const response = await axios.get(`${API_BASE_URL}/api/tickers`);
        setAvailableTickers(response.data.tickers);
      } catch (err) {
        console.error('Error fetching tickers:', err);
      }
    };
    fetchTickers();
  }, []);

  // Re-fetch data when quarterly toggle changes
  useEffect(() => {
    if (selectedTicker) {
      handleTickerSelect(selectedTicker);
    }
  }, [quarterly]);

  // Fetch financial data when ticker is selected
  const handleTickerSelect = async (ticker) => {
    setSelectedTicker(ticker);
    setLoading(true);
    setError(null);
    setCharts([]); // Reset charts when changing ticker
    setIsCollecting(false);
    setCollectionProgress({ status: '', message: '', progress: 0 });

    try {
      // First, check cache status
      const cacheStatus = await checkCacheStatus(ticker, quarterly);
      setIsCached(cacheStatus.cached);
      
      if (cacheStatus.cached) {
        // Load from cache (fast)
        const cachedData = await getCachedFinancialData(ticker, quarterly);
        if (cachedData) {
          setFinancialData(cachedData);
          
          // Set active tab to first available statement
          const statements = cachedData.statements;
          const firstAvailable = Object.keys(statements).find(key => statements[key].available);
          if (firstAvailable) {
            setActiveTab(firstAvailable);
          }
          setLoading(false);
          return;
        }
      }
      
      // Not cached - need to collect data
      setLoading(false);
      setIsCollecting(true);
      
      const data = await collectFinancialData(
        ticker,
        10, // 10 years or quarters
        false,
        (progressData) => {
          setCollectionProgress(progressData);
        },
        quarterly
      );
      
      setFinancialData(data);
      setIsCollecting(false);
      setIsCached(true);
      
      // Set active tab to first available statement
      const statements = data.statements;
      const firstAvailable = Object.keys(statements).find(key => statements[key].available);
      if (firstAvailable) {
        setActiveTab(firstAvailable);
      }
      
    } catch (err) {
      setError(err.message || 'Error fetching financial data');
      setFinancialData(null);
      setIsCollecting(false);
    } finally {
      setLoading(false);
    }
  };
  
  // Handle refresh request
  const handleRefresh = async () => {
    if (!selectedTicker || isCollecting) return;
    
    setIsCollecting(true);
    setError(null);
    setCollectionProgress({ status: 'starting', message: 'Refreshing data...', progress: 0 });
    
    try {
      const data = await refreshFinancialData(
        selectedTicker,
        10,
        (progressData) => {
          setCollectionProgress(progressData);
        },
        quarterly
      );
      
      setFinancialData(data);
      setIsCollecting(false);
      setIsCached(true);
      
      // Keep current active tab if available
      const statements = data.statements;
      if (!statements[activeTab]?.available) {
        const firstAvailable = Object.keys(statements).find(key => statements[key].available);
        if (firstAvailable) {
          setActiveTab(firstAvailable);
        }
      }
      
    } catch (err) {
      setError(err.message || 'Error refreshing financial data');
      setIsCollecting(false);
    }
  };

  const handleAddChart = (chartConfig) => {
    const newChartId = Date.now();
    const newChart = { ...chartConfig, id: newChartId };
    
    // Position new chart to the right of the last chart or table
    const allPanels = Object.values(chartPanels);
    let xPos = tablePanel.position.x + tablePanel.size.width + 15;
    let yPos = tablePanel.position.y;
    
    if (allPanels.length > 0) {
      const lastPanel = allPanels[allPanels.length - 1];
      xPos = lastPanel.position.x;
      yPos = lastPanel.position.y + lastPanel.size.height + 15;
    }
    
    setCharts([...charts, newChart]);
    setChartPanels(prev => ({
      ...prev,
      [newChartId]: {
        position: { x: xPos, y: yPos },
        size: { width: 800, height: 500 }
      }
    }));
  };

  const handleRemoveChart = (chartId) => {
    setCharts(charts.filter(chart => chart.id !== chartId));
    setChartPanels(prev => {
      const newPanels = { ...prev };
      delete newPanels[chartId];
      return newPanels;
    });
  };

  const handleUpdateChart = (chartId, updatedConfig) => {
    setCharts(charts.map(chart => 
      chart.id === chartId ? { ...updatedConfig, id: chartId } : chart
    ));
  };

  const currentStatement = financialData?.statements?.[activeTab];

  // Calculate alignment guides when dragging
  const calculateAlignmentGuides = (excludePanelId) => {
    const guides = [];
    const allPanels = [
      { id: 'table', ...tablePanel },
      ...Object.entries(chartPanels).map(([id, panel]) => ({ id, ...panel }))
    ].filter(p => p.id !== excludePanelId);

    allPanels.forEach(panel => {
      // Vertical guides (left, center, right edges)
      guides.push({ type: 'vertical', position: panel.position.x });
      guides.push({ type: 'vertical', position: panel.position.x + panel.size.width / 2 });
      guides.push({ type: 'vertical', position: panel.position.x + panel.size.width });
      
      // Horizontal guides (top, center, bottom edges)
      guides.push({ type: 'horizontal', position: panel.position.y });
      guides.push({ type: 'horizontal', position: panel.position.y + panel.size.height / 2 });
      guides.push({ type: 'horizontal', position: panel.position.y + panel.size.height });
    });

    return guides;
  };

  const handleTablePositionChange = (newPosition) => {
    setTablePanel(prev => ({ ...prev, position: newPosition }));
    setDraggingPanel('table');
    setAlignmentGuides(calculateAlignmentGuides('table'));
  };

  const handleTableSizeChange = (newSize) => {
    setTablePanel(prev => ({ ...prev, size: newSize }));
  };

  const handleChartPositionChange = (chartId, newPosition) => {
    setChartPanels(prev => ({
      ...prev,
      [chartId]: { ...prev[chartId], position: newPosition }
    }));
    setDraggingPanel(chartId);
    setAlignmentGuides(calculateAlignmentGuides(chartId));
  };

  const handleChartSizeChange = (chartId, newSize) => {
    setChartPanels(prev => ({
      ...prev,
      [chartId]: { ...prev[chartId], size: newSize }
    }));
  };

  // Clear guides when drag ends
  useEffect(() => {
    const handleMouseUp = () => {
      setDraggingPanel(null);
      setAlignmentGuides([]);
    };
    
    document.addEventListener('mouseup', handleMouseUp);
    return () => document.removeEventListener('mouseup', handleMouseUp);
  }, []);

  return (
    <div className="App">
      <header className="app-header">
        <h1>📊 Financial Data Tool</h1>
        
        {/* Main Navigation Tabs */}
        <div className="main-tabs">
          <button
            className={`main-tab ${activeMainTab === 'stocks' ? 'active' : ''}`}
            onClick={() => setActiveMainTab('stocks')}
          >
            📈 Individual Stocks
          </button>
          <button
            className={`main-tab ${activeMainTab === 'economy' ? 'active' : ''}`}
            onClick={() => setActiveMainTab('economy')}
          >
            🌍 Economy
          </button>
          <button
            className={`main-tab ${activeMainTab === 'ai' ? 'active' : ''}`}
            onClick={() => setActiveMainTab('ai')}
          >
            🤖 AI Predictions
          </button>
        </div>
        
        {activeMainTab === 'stocks' && (
          <div className="stocks-header-controls">
            <TickerSearch
              tickers={availableTickers}
              onSelect={handleTickerSelect}
              selectedTicker={selectedTicker}
            />
          </div>
        )}
      </header>

      <main className="app-main">
        {/* Individual Stocks Tab */}
        {activeMainTab === 'stocks' && (
          <>
            {loading && <div className="loading">⏳ Loading financial data...</div>}
            {error && <div className="error">❌ {error}</div>}
            
            {/* Progress Indicator during data collection */}
            {isCollecting && (
              <DataCollectionProgress
                status={collectionProgress.status}
                message={collectionProgress.message}
                progress={collectionProgress.progress}
              />
            )}
            
            {/* Refresh Button */}
            {selectedTicker && financialData && !isCollecting && (
              <div className="refresh-container">
                <button 
                  className="refresh-button"
                  onClick={handleRefresh}
                  disabled={isCollecting}
                  title="Refresh financial data from SEC EDGAR"
                >
                  🔄 Refresh Data
                </button>
                <p className="refresh-hint">Click to fetch the latest data from SEC EDGAR</p>
              </div>
            )}

            {financialData && !isCollecting && (
          <div className="canvas-container">
            <AlignmentGuides 
              guides={alignmentGuides} 
              show={draggingPanel !== null} 
            />
            
            {/* Table Panel */}
            <DraggableResizablePanel
              id="table"
              position={tablePanel.position}
              size={tablePanel.size}
              onPositionChange={handleTablePositionChange}
              onSizeChange={handleTableSizeChange}
              minWidth={400}
              minHeight={400}
              alignmentGuides={alignmentGuides}
              showAlignmentGuides={draggingPanel === 'table'}
            >
              <div className="data-section">
                <div className="financial-header">
                  <h2>{financialData.ticker} Financial Statements</h2>
                  <div className="header-badges">
                    {financialData.currency && (
                      <span className="currency-badge">{financialData.currency}</span>
                    )}
                    {financialData.period_type && (
                      <span className="period-badge">
                        {financialData.period_type === 'quarterly' ? '📊 Quarterly' : '📅 Annual'}
                      </span>
                    )}
                  </div>
                </div>
                
                {/* Period Toggle */}
                <div className="period-toggle">
                  <button
                    className={`toggle-btn ${!quarterly ? 'active' : ''}`}
                    onClick={() => setQuarterly(false)}
                  >
                    📅 Annual
                  </button>
                  <button
                    className={`toggle-btn ${quarterly ? 'active' : ''}`}
                    onClick={() => setQuarterly(true)}
                  >
                    📊 Quarterly
                  </button>
                </div>
                
                {/* Statement Tabs */}
                <div className="tabs">
                  {Object.entries(financialData.statements).map(([key, stmt]) => (
                    stmt.available && (
                      <button
                        key={key}
                        className={`tab ${activeTab === key ? 'active' : ''}`}
                        onClick={() => setActiveTab(key)}
                      >
                        {key.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                      </button>
                    )
                  ))}
                </div>

                {/* Financial Table */}
                {currentStatement?.available ? (
                  <FinancialTable
                    data={currentStatement}
                    statementType={activeTab}
                    ticker={financialData.ticker}
                    onAddChart={handleAddChart}
                  />
                ) : (
                  <div className="no-data">No data available for this statement</div>
                )}
              </div>
            </DraggableResizablePanel>

            {/* Chart Panels */}
            {charts.map((chart) => {
              const panel = chartPanels[chart.id];
              if (!panel) return null;
              
              return (
                <DraggableResizablePanel
                  key={chart.id}
                  id={chart.id}
                  position={panel.position}
                  size={panel.size}
                  onPositionChange={(pos) => handleChartPositionChange(chart.id, pos)}
                  onSizeChange={(size) => handleChartSizeChange(chart.id, size)}
                  minWidth={300}
                  minHeight={250}
                  alignmentGuides={alignmentGuides}
                  showAlignmentGuides={draggingPanel === chart.id}
                >
                  <ChartManager
                    charts={[chart]}
                    onRemoveChart={handleRemoveChart}
                    onUpdateChart={handleUpdateChart}
                    financialData={currentStatement}
                    ticker={financialData.ticker}
                  />
                </DraggableResizablePanel>
              );
            })}
          </div>
            )}

            {!selectedTicker && !loading && (
              <div className="welcome">
                <h2>Welcome to Financial Data Tool</h2>
                <p>Search for a ticker above to view financial statements and create visualizations.</p>
              </div>
            )}
          </>
        )}

        {/* Economy Tab */}
        {activeMainTab === 'economy' && (
          <MacroView />
        )}

        {/* AI Predictions Tab */}
        {activeMainTab === 'ai' && (
          <AIView />
        )}
      </main>
    </div>
  );
}

export default App;
