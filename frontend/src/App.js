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

  // Fetch financial data when ticker is selected
  const handleTickerSelect = async (ticker) => {
    setSelectedTicker(ticker);
    setLoading(true);
    setError(null);
    setCharts([]); // Reset charts when changing ticker

    try {
      const response = await axios.get(`${API_BASE_URL}/api/financials/${ticker}`);
      setFinancialData(response.data);
      
      // Set active tab to first available statement
      const statements = response.data.statements;
      const firstAvailable = Object.keys(statements).find(key => statements[key].available);
      if (firstAvailable) {
        setActiveTab(firstAvailable);
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Error fetching financial data');
      setFinancialData(null);
    } finally {
      setLoading(false);
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
          <TickerSearch
            tickers={availableTickers}
            onSelect={handleTickerSelect}
            selectedTicker={selectedTicker}
          />
        )}
      </header>

      <main className="app-main">
        {/* Individual Stocks Tab */}
        {activeMainTab === 'stocks' && (
          <>
            {loading && <div className="loading">Loading financial data...</div>}
            {error && <div className="error">{error}</div>}

            {financialData && (
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
                <h2>{financialData.ticker} Financial Statements</h2>
                
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
