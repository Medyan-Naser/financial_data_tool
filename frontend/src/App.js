import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';
import FinancialTable from './components/FinancialTable';
import ChartManager from './components/ChartManager';
import TickerSearch from './components/TickerSearch';
import ResizablePanel from './components/ResizablePanel';

const API_BASE_URL = 'http://localhost:8000';

function App() {
  const [availableTickers, setAvailableTickers] = useState([]);
  const [selectedTicker, setSelectedTicker] = useState(null);
  const [financialData, setFinancialData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('income_statement');
  const [charts, setCharts] = useState([]);

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
    setCharts([...charts, { ...chartConfig, id: Date.now() }]);
  };

  const handleRemoveChart = (chartId) => {
    setCharts(charts.filter(chart => chart.id !== chartId));
  };

  const handleUpdateChart = (chartId, updatedConfig) => {
    setCharts(charts.map(chart => 
      chart.id === chartId ? { ...updatedConfig, id: chartId } : chart
    ));
  };

  const currentStatement = financialData?.statements?.[activeTab];

  return (
    <div className="App">
      <header className="app-header">
        <h1>📊 Financial Data Tool</h1>
        <TickerSearch
          tickers={availableTickers}
          onSelect={handleTickerSelect}
          selectedTicker={selectedTicker}
        />
      </header>

      <main className="app-main">
        {loading && <div className="loading">Loading financial data...</div>}
        {error && <div className="error">{error}</div>}

        {financialData && (
          <div className="content-wrapper">
            <ResizablePanel
              minWidth={400}
              minHeight={400}
              defaultWidth={800}
              defaultHeight={600}
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
            </ResizablePanel>

            {/* Chart Section */}
            {charts.length > 0 && (
              <div className="charts-section">
                <ChartManager
                  charts={charts}
                  onRemoveChart={handleRemoveChart}
                  onUpdateChart={handleUpdateChart}
                  financialData={currentStatement}
                  ticker={financialData.ticker}
                />
              </div>
            )}
          </div>
        )}

        {!selectedTicker && !loading && (
          <div className="welcome">
            <h2>Welcome to Financial Data Tool</h2>
            <p>Search for a ticker above to view financial statements and create visualizations.</p>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
