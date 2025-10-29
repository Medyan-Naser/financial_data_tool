import React, { useState } from 'react';
import axios from 'axios';
import Plot from 'react-plotly.js';
import DraggableResizablePanel from './DraggableResizablePanel';

const API_BASE_URL = 'http://localhost:8000';

function EconomyView() {
  const [activeView, setActiveView] = useState('overview');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // Economic Data States
  const [currencyData, setCurrencyData] = useState(null);
  const [cryptoData, setCryptoData] = useState(null);
  const [metalsData, setMetalsData] = useState(null);
  const [gdpData, setGdpData] = useState(null);
  const [inflationData, setInflationData] = useState(null);
  const [interestRatesData, setInterestRatesData] = useState(null);
  const [unemploymentData, setUnemploymentData] = useState(null);
  
  // Z-index management for panels
  const [activePanelId, setActivePanelId] = useState(null);
  const [panelZIndexes, setPanelZIndexes] = useState({});
  
  // Panel state for draggable/resizable components
  const [chartPanels, setChartPanels] = useState({
    currencyTable: { position: { x: 20, y: 20 }, size: { width: 600, height: 500 } },
    cryptoTable: { position: { x: 20, y: 20 }, size: { width: 900, height: 600 } },
    metalsCard: { position: { x: 20, y: 20 }, size: { width: 600, height: 350 } },
    gdpChart: { position: { x: 20, y: 20 }, size: { width: 900, height: 550 } },
    inflationChart: { position: { x: 20, y: 20 }, size: { width: 900, height: 550 } },
    interestRatesTable: { position: { x: 20, y: 20 }, size: { width: 900, height: 600 } },
    interestRatesChart: { position: { x: 20, y: 640 }, size: { width: 900, height: 500 } },
    unemploymentChart: { position: { x: 20, y: 20 }, size: { width: 900, height: 550 } },
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

  // Fetch Currency Data
  const fetchCurrencyData = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get(`${API_BASE_URL}/api/economy/currency`);
      setCurrencyData(response.data);
    } catch (err) {
      setError(`Error fetching currency data: ${err.message}`);
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Fetch Crypto Data
  const fetchCryptoData = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get(`${API_BASE_URL}/api/economy/crypto`);
      setCryptoData(response.data);
    } catch (err) {
      setError(`Error fetching crypto data: ${err.message}`);
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Fetch Metals Data
  const fetchMetalsData = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get(`${API_BASE_URL}/api/economy/metals`);
      setMetalsData(response.data);
    } catch (err) {
      setError(`Error fetching metals data: ${err.message}`);
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Fetch GDP Data
  const fetchGdpData = async (country = 'US') => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get(`${API_BASE_URL}/api/economy/gdp/${country}`);
      setGdpData(response.data);
    } catch (err) {
      setError(`Error fetching GDP data: ${err.message}`);
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Fetch Inflation Data
  const fetchInflationData = async (country = 'US') => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get(`${API_BASE_URL}/api/economy/inflation/${country}`);
      setInflationData(response.data);
    } catch (err) {
      setError(`Error fetching inflation data: ${err.message}`);
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Fetch Interest Rates Data
  const fetchInterestRatesData = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get(`${API_BASE_URL}/api/economy/interest-rates`);
      setInterestRatesData(response.data);
    } catch (err) {
      setError(`Error fetching interest rates: ${err.message}`);
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Fetch Unemployment Data
  const fetchUnemploymentData = async (country = 'US') => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get(`${API_BASE_URL}/api/economy/unemployment/${country}`);
      setUnemploymentData(response.data);
    } catch (err) {
      setError(`Error fetching unemployment data: ${err.message}`);
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Format currency for display
  const formatCurrency = (value) => {
    if (value === null || value === undefined) return '-';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(value);
  };

  // Format large numbers (for market cap, etc.)
  const formatLargeNumber = (value) => {
    if (value === null || value === undefined) return '-';
    if (value >= 1e12) return `$${(value / 1e12).toFixed(2)}T`;
    if (value >= 1e9) return `$${(value / 1e9).toFixed(2)}B`;
    if (value >= 1e6) return `$${(value / 1e6).toFixed(2)}M`;
    return `$${value.toFixed(2)}`;
  };

  // Format percentage
  const formatPercent = (value) => {
    if (value === null || value === undefined) return '-';
    const sign = value >= 0 ? '+' : '';
    return `${sign}${value.toFixed(2)}%`;
  };

  return (
    <div className="ai-view">
      <h2>🌍 Economic Indicators</h2>
      
      {/* Sub-navigation */}
      <div className="ai-sections">
        <button 
          className={`section-btn ${activeView === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveView('overview')}
        >
          Overview
        </button>
        <button 
          className={`section-btn ${activeView === 'currency' ? 'active' : ''}`}
          onClick={() => { setActiveView('currency'); fetchCurrencyData(); }}
        >
          💱 Currency
        </button>
        <button 
          className={`section-btn ${activeView === 'crypto' ? 'active' : ''}`}
          onClick={() => { setActiveView('crypto'); fetchCryptoData(); }}
        >
          ₿ Crypto
        </button>
        <button 
          className={`section-btn ${activeView === 'metals' ? 'active' : ''}`}
          onClick={() => { setActiveView('metals'); fetchMetalsData(); }}
        >
          🥇 Metals
        </button>
        <button 
          className={`section-btn ${activeView === 'gdp' ? 'active' : ''}`}
          onClick={() => { setActiveView('gdp'); fetchGdpData(); }}
        >
          📈 GDP
        </button>
        <button 
          className={`section-btn ${activeView === 'inflation' ? 'active' : ''}`}
          onClick={() => { setActiveView('inflation'); fetchInflationData(); }}
        >
          📉 Inflation
        </button>
        <button 
          className={`section-btn ${activeView === 'interest-rates' ? 'active' : ''}`}
          onClick={() => { setActiveView('interest-rates'); fetchInterestRatesData(); }}
        >
          💰 Interest Rates
        </button>
        <button 
          className={`section-btn ${activeView === 'unemployment' ? 'active' : ''}`}
          onClick={() => { setActiveView('unemployment'); fetchUnemploymentData(); }}
        >
          👔 Unemployment
        </button>
      </div>

      {/* Content Area */}
      <div className="ai-content">
        {/* Error Display */}
        {error && (
          <div className="error-message" style={{ 
            background: '#ff5252', 
            color: 'white', 
            padding: '15px 20px', 
            margin: '20px 0', 
            borderRadius: '8px' 
          }}>
            ⚠️ {error}
          </div>
        )}

        {/* Loading Indicator */}
        {loading && (
          <div className="loading-ai">
            <div className="spinner"></div>
            <p>Loading economic data...</p>
          </div>
        )}

        {/* Overview */}
        {activeView === 'overview' && (
          <div className="overview-panel" style={{ padding: '30px' }}>
            <h3>Economic Data Dashboard</h3>
            <p style={{ marginBottom: '30px', color: '#666' }}>
              Click any section button above to view detailed economic indicators
            </p>
            
            <div className="overview-grid">
              {[
                { title: 'Currency Rates', icon: '💱', desc: 'Live forex rates vs USD', onClick: () => { setActiveView('currency'); fetchCurrencyData(); } },
                { title: 'Cryptocurrency', icon: '₿', desc: 'Top 20 crypto by market cap', onClick: () => { setActiveView('crypto'); fetchCryptoData(); } },
                { title: 'Precious Metals', icon: '🥇', desc: 'Gold and silver prices', onClick: () => { setActiveView('metals'); fetchMetalsData(); } },
                { title: 'GDP Data', icon: '📈', desc: 'Gross Domestic Product trends', onClick: () => { setActiveView('gdp'); fetchGdpData(); } },
                { title: 'Inflation Rates', icon: '📉', desc: 'Consumer Price Index (CPI)', onClick: () => { setActiveView('inflation'); fetchInflationData(); } },
                { title: 'Interest Rates', icon: '💰', desc: 'US Treasury rates', onClick: () => { setActiveView('interest-rates'); fetchInterestRatesData(); } },
                { title: 'Unemployment', icon: '👔', desc: 'Labor market statistics', onClick: () => { setActiveView('unemployment'); fetchUnemploymentData(); } },
              ].map((card) => (
                <div 
                  key={card.title}
                  onClick={card.onClick}
                  className="overview-card"
                >
                  <div style={{ fontSize: '40px', marginBottom: '10px' }}>{card.icon}</div>
                  <h4>{card.title}</h4>
                  <p>{card.desc}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Currency View */}
        {activeView === 'currency' && currencyData && (
          <div className="currency-results" style={{ position: 'relative', minHeight: '600px' }}>
          <DraggableResizablePanel
            id="currencyTable"
            title="💱 Currency Exchange Rates"
            position={chartPanels.currencyTable.position}
            size={chartPanels.currencyTable.size}
            onPositionChange={(position) => updatePanelPosition('currencyTable', position)}
            onSizeChange={(size) => updatePanelSize('currencyTable', size)}
            onFocus={() => handlePanelFocus('currencyTable')}
            zIndex={getPanelZIndex('currencyTable')}
            minConstraints={[400, 300]}
          >
            <div style={{ padding: '15px' }}>
              <div style={{ marginBottom: '15px', fontSize: '13px', color: '#666' }}>
                <span>Base: {currencyData.base} | </span>
                <span>Date: {currencyData.date} | </span>
                <span style={{ color: '#667eea' }}>Cached until: {new Date(currencyData.cache_expires).toLocaleDateString()}</span>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(110px, 1fr))', gap: '12px' }}>
                {Object.entries(currencyData.rates)
                  .filter(([code]) => ['EUR', 'GBP', 'JPY', 'CHF', 'CAD', 'AUD', 'CNY', 'INR', 'BRL', 'MXN', 'SGD', 'HKD'].includes(code))
                  .map(([code, rate]) => (
                    <div key={code} style={{ background: '#f5f5f5', padding: '12px', borderRadius: '8px', textAlign: 'center' }}>
                      <div style={{ fontWeight: '700', fontSize: '14px', color: '#667eea', marginBottom: '6px' }}>{code}</div>
                      <div style={{ fontSize: '16px' }}>{rate.toFixed(4)}</div>
                    </div>
                  ))}
              </div>
            </div>
          </DraggableResizablePanel>
          </div>
        )}

        {/* Crypto View */}
        {activeView === 'crypto' && cryptoData && (
          <div className="crypto-results" style={{ position: 'relative', minHeight: '700px' }}>
          <DraggableResizablePanel
            id="cryptoTable"
            title="₿ Top Cryptocurrencies"
            position={chartPanels.cryptoTable.position}
            size={chartPanels.cryptoTable.size}
            onPositionChange={(position) => updatePanelPosition('cryptoTable', position)}
            onSizeChange={(size) => updatePanelSize('cryptoTable', size)}
            onFocus={() => handlePanelFocus('cryptoTable')}
            zIndex={getPanelZIndex('cryptoTable')}
            minConstraints={[700, 400]}
          >
            <div style={{ padding: '15px', overflowX: 'auto' }}>
              <div style={{ marginBottom: '15px', fontSize: '13px', color: '#666' }}>
                <span>Total: {cryptoData.total_count} cryptos | </span>
                <span style={{ color: '#667eea' }}>Cached until: {new Date(cryptoData.cache_expires).toLocaleDateString()}</span>
              </div>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px' }}>
                <thead style={{ background: '#f5f5f5' }}>
                  <tr>
                    <th style={{ padding: '12px', textAlign: 'left' }}>#</th>
                    <th style={{ padding: '12px', textAlign: 'left' }}>Name</th>
                    <th style={{ padding: '12px', textAlign: 'right' }}>Price</th>
                    <th style={{ padding: '12px', textAlign: 'right' }}>24h Change</th>
                    <th style={{ padding: '12px', textAlign: 'right' }}>Market Cap</th>
                    <th style={{ padding: '12px', textAlign: 'right' }}>Volume</th>
                  </tr>
                </thead>
                <tbody>
                  {cryptoData.cryptocurrencies.map((crypto) => (
                    <tr key={crypto.id} style={{ borderBottom: '1px solid #f0f0f0' }}>
                      <td style={{ padding: '12px' }}>{crypto.market_cap_rank}</td>
                      <td style={{ padding: '12px' }}>
                        <div><strong>{crypto.name}</strong></div>
                        <div style={{ fontSize: '12px', color: '#aaa' }}>{crypto.symbol}</div>
                      </td>
                      <td style={{ padding: '12px', textAlign: 'right', fontWeight: '600' }}>{formatCurrency(crypto.current_price)}</td>
                      <td style={{ padding: '12px', textAlign: 'right', fontWeight: '600', color: crypto.price_change_percentage_24h >= 0 ? '#4CAF50' : '#ff5252' }}>
                        {formatPercent(crypto.price_change_percentage_24h)}
                      </td>
                      <td style={{ padding: '12px', textAlign: 'right' }}>{formatLargeNumber(crypto.market_cap)}</td>
                      <td style={{ padding: '12px', textAlign: 'right' }}>{formatLargeNumber(crypto.total_volume)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </DraggableResizablePanel>
          </div>
        )}

        {/* Metals View */}
        {activeView === 'metals' && metalsData && (
          <div className="metals-results" style={{ position: 'relative', minHeight: '500px' }}>
          <DraggableResizablePanel
            id="metalsCard"
            title="🥇 Precious Metals Prices"
            position={chartPanels.metalsCard.position}
            size={chartPanels.metalsCard.size}
            onPositionChange={(position) => updatePanelPosition('metalsCard', position)}
            onSizeChange={(size) => updatePanelSize('metalsCard', size)}
            onFocus={() => handlePanelFocus('metalsCard')}
            zIndex={getPanelZIndex('metalsCard')}
            minConstraints={[400, 250]}
          >
            <div style={{ padding: '20px' }}>
              <div style={{ marginBottom: '20px', fontSize: '13px', color: '#666' }}>
                <span>{metalsData.date} | </span>
                <span style={{ color: '#667eea' }}>Cached until: {new Date(metalsData.cache_expires).toLocaleDateString()}</span>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '20px' }}>
                <div style={{ background: 'linear-gradient(145deg, #FFD700, #FFA500)', padding: '25px', borderRadius: '12px', color: 'white' }}>
                  <h3 style={{ marginBottom: '15px' }}>🥇 Gold</h3>
                  <div style={{ fontSize: '32px', fontWeight: '700', marginBottom: '10px' }}>${metalsData.gold.price_usd_oz.toFixed(2)}/oz</div>
                  <div style={{ fontSize: '18px', fontWeight: '600', marginBottom: '8px' }}>
                    {metalsData.gold.change >= 0 ? '▲' : '▼'} ${Math.abs(metalsData.gold.change).toFixed(2)} ({formatPercent(metalsData.gold.change_percent)})
                  </div>
                  <div style={{ fontSize: '13px', opacity: 0.9 }}>Prev Close: ${metalsData.gold.prev_close.toFixed(2)}</div>
                </div>
                <div style={{ background: 'linear-gradient(145deg, #C0C0C0, #A9A9A9)', padding: '25px', borderRadius: '12px', color: 'white' }}>
                  <h3 style={{ marginBottom: '15px' }}>⚪ Silver</h3>
                  <div style={{ fontSize: '32px', fontWeight: '700', marginBottom: '10px' }}>${metalsData.silver.price_usd_oz.toFixed(2)}/oz</div>
                  <div style={{ fontSize: '18px', fontWeight: '600', marginBottom: '8px' }}>
                    {metalsData.silver.change >= 0 ? '▲' : '▼'} ${Math.abs(metalsData.silver.change).toFixed(2)} ({formatPercent(metalsData.silver.change_percent)})
                  </div>
                  <div style={{ fontSize: '13px', opacity: 0.9 }}>Prev Close: ${metalsData.silver.prev_close.toFixed(2)}</div>
                </div>
              </div>
            </div>
          </DraggableResizablePanel>
          </div>
        )}

        {/* GDP View */}
        {activeView === 'gdp' && gdpData && (
          <div className="gdp-results" style={{ position: 'relative', minHeight: '700px' }}>
          <DraggableResizablePanel
            id="gdpChart"
            title="📈 GDP Historical Data"
            position={chartPanels.gdpChart.position}
            size={chartPanels.gdpChart.size}
            onPositionChange={(position) => updatePanelPosition('gdpChart', position)}
            onSizeChange={(size) => updatePanelSize('gdpChart', size)}
            onFocus={() => handlePanelFocus('gdpChart')}
            zIndex={getPanelZIndex('gdpChart')}
            minConstraints={[600, 400]}
          >
            <div style={{ padding: '15px' }}>
              <div style={{ marginBottom: '15px', fontSize: '13px', color: '#666' }}>
                <span>Country: {gdpData.country} | </span>
                <span style={{ color: '#667eea' }}>Cached until: {new Date(gdpData.cache_expires).toLocaleDateString()}</span>
              </div>
              <Plot
                data={[{
                  x: gdpData.data.map(d => d.year),
                  y: gdpData.data.map(d => d.value_usd / 1e12),
                  type: 'scatter',
                  mode: 'lines+markers',
                  marker: { color: '#667eea', size: 8 },
                  line: { color: '#667eea', width: 3 }
                }]}
                layout={{
                  title: `${gdpData.country} GDP Over Time`,
                  xaxis: { title: 'Year' },
                  yaxis: { title: 'GDP (Trillions USD)' },
                  margin: { t: 40, r: 20, b: 40, l: 60 }
                }}
                config={{ displayModeBar: true, displaylogo: false }}
                style={{ width: '100%', height: '450px' }}
              />
            </div>
          </DraggableResizablePanel>
          </div>
        )}

        {/* Inflation View */}
        {activeView === 'inflation' && inflationData && (
          <div className="inflation-results" style={{ position: 'relative', minHeight: '700px' }}>
          <DraggableResizablePanel
            id="inflationChart"
            title="📉 Inflation Rates"
            position={chartPanels.inflationChart.position}
            size={chartPanels.inflationChart.size}
            onPositionChange={(position) => updatePanelPosition('inflationChart', position)}
            onSizeChange={(size) => updatePanelSize('inflationChart', size)}
            onFocus={() => handlePanelFocus('inflationChart')}
            zIndex={getPanelZIndex('inflationChart')}
            minConstraints={[600, 400]}
          >
            <div style={{ padding: '15px' }}>
              <div style={{ marginBottom: '15px', fontSize: '13px', color: '#666' }}>
                <span>Country: {inflationData.country} | </span>
                <span style={{ color: '#667eea' }}>Cached until: {new Date(inflationData.cache_expires).toLocaleDateString()}</span>
              </div>
              <Plot
                data={[{
                  x: inflationData.data.map(d => d.year),
                  y: inflationData.data.map(d => d.rate_percent),
                  type: 'bar',
                  marker: { 
                    color: inflationData.data.map(d => d.rate_percent > 4 ? '#ff5252' : '#667eea')
                  }
                }]}
                layout={{
                  title: `${inflationData.country} Inflation Rate (CPI)`,
                  xaxis: { title: 'Year' },
                  yaxis: { title: 'Inflation Rate (%)' },
                  margin: { t: 40, r: 20, b: 40, l: 60 }
                }}
                config={{ displayModeBar: true, displaylogo: false }}
                style={{ width: '100%', height: '450px' }}
              />
            </div>
          </DraggableResizablePanel>
          </div>
        )}

        {/* Interest Rates View */}
        {activeView === 'interest-rates' && interestRatesData && (
          <div className="interest-rates-results" style={{ position: 'relative', minHeight: '700px' }}>
          <DraggableResizablePanel
            id="interestRatesTable"
            title="💰 US Treasury Interest Rates"
            position={chartPanels.interestRatesTable.position}
            size={chartPanels.interestRatesTable.size}
            onPositionChange={(position) => updatePanelPosition('interestRatesTable', position)}
            onSizeChange={(size) => updatePanelSize('interestRatesTable', size)}
            onFocus={() => handlePanelFocus('interestRatesTable')}
            zIndex={getPanelZIndex('interestRatesTable')}
            minConstraints={[700, 400]}
          >
            <div style={{ padding: '15px', overflowX: 'auto' }}>
              <div style={{ marginBottom: '15px', fontSize: '13px', color: '#666' }}>
                <span style={{ color: '#667eea' }}>Cached until: {new Date(interestRatesData.cache_expires).toLocaleDateString()}</span>
              </div>
              {interestRatesData.rates && interestRatesData.rates.length > 0 ? (
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px' }}>
                  <thead style={{ background: '#f5f5f5' }}>
                    <tr>
                      <th style={{ padding: '12px', textAlign: 'left' }}>Date</th>
                      <th style={{ padding: '12px', textAlign: 'left' }}>Security Type</th>
                      <th style={{ padding: '12px', textAlign: 'right' }}>Interest Rate</th>
                    </tr>
                  </thead>
                  <tbody>
                    {interestRatesData.rates.map((rate, index) => (
                      <tr key={index} style={{ borderBottom: '1px solid #f0f0f0' }}>
                        <td style={{ padding: '12px' }}>{rate.date}</td>
                        <td style={{ padding: '12px' }}>{rate.security_type}</td>
                        <td style={{ padding: '12px', textAlign: 'right', fontWeight: '700', color: '#667eea' }}>
                          {rate.rate_percent}%
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <div style={{ padding: '40px', textAlign: 'center', color: '#999' }}>
                  No interest rate data available
                </div>
              )}
            </div>
          </DraggableResizablePanel>
          
          {/* Interest Rates Historical Chart */}
          <DraggableResizablePanel
            id="interestRatesChart"
            title="📊 Interest Rates Trend"
            position={chartPanels.interestRatesChart.position}
            size={chartPanels.interestRatesChart.size}
            onPositionChange={(position) => updatePanelPosition('interestRatesChart', position)}
            onSizeChange={(size) => updatePanelSize('interestRatesChart', size)}
            onFocus={() => handlePanelFocus('interestRatesChart')}
            zIndex={getPanelZIndex('interestRatesChart')}
            minConstraints={[600, 400]}
          >
            <div style={{ padding: '15px' }}>
              <Plot
                data={[
                  {
                    x: interestRatesData.rates.filter(r => r.security_type && r.security_type.includes('Treasury Bills')).map((r, i) => i + 1),
                    y: interestRatesData.rates.filter(r => r.security_type && r.security_type.includes('Treasury Bills')).map(r => parseFloat(r.rate_percent) || 0),
                    type: 'scatter',
                    mode: 'lines+markers',
                    name: 'Treasury Bills',
                    marker: { color: '#667eea', size: 6 },
                    line: { color: '#667eea', width: 2 }
                  },
                  {
                    x: interestRatesData.rates.filter(r => r.security_type && r.security_type.includes('Treasury Notes')).map((r, i) => i + 1),
                    y: interestRatesData.rates.filter(r => r.security_type && r.security_type.includes('Treasury Notes')).map(r => parseFloat(r.rate_percent) || 0),
                    type: 'scatter',
                    mode: 'lines+markers',
                    name: 'Treasury Notes',
                    marker: { color: '#764ba2', size: 6 },
                    line: { color: '#764ba2', width: 2 }
                  },
                  {
                    x: interestRatesData.rates.filter(r => r.security_type && r.security_type.includes('Treasury Bonds')).map((r, i) => i + 1),
                    y: interestRatesData.rates.filter(r => r.security_type && r.security_type.includes('Treasury Bonds')).map(r => parseFloat(r.rate_percent) || 0),
                    type: 'scatter',
                    mode: 'lines+markers',
                    name: 'Treasury Bonds',
                    marker: { color: '#4CAF50', size: 6 },
                    line: { color: '#4CAF50', width: 2 }
                  }
                ]}
                layout={{
                  title: 'US Treasury Interest Rates Over Time',
                  xaxis: { title: 'Entry' },
                  yaxis: { title: 'Interest Rate (%)' },
                  legend: { x: 0, y: 1 },
                  margin: { t: 40, r: 20, b: 40, l: 60 }
                }}
                config={{ displayModeBar: true, displaylogo: false }}
                style={{ width: '100%', height: '420px' }}
              />
            </div>
          </DraggableResizablePanel>
          </div>
        )}

        {/* Unemployment View */}
        {activeView === 'unemployment' && unemploymentData && (
          <div className="unemployment-results" style={{ position: 'relative', minHeight: '700px' }}>
          <DraggableResizablePanel
            id="unemploymentChart"
            title="👔 Unemployment Rate"
            position={chartPanels.unemploymentChart.position}
            size={chartPanels.unemploymentChart.size}
            onPositionChange={(position) => updatePanelPosition('unemploymentChart', position)}
            onSizeChange={(size) => updatePanelSize('unemploymentChart', size)}
            onFocus={() => handlePanelFocus('unemploymentChart')}
            zIndex={getPanelZIndex('unemploymentChart')}
            minConstraints={[600, 400]}
          >
            <div style={{ padding: '15px' }}>
              <div style={{ marginBottom: '15px', fontSize: '13px', color: '#666' }}>
                <span>Country: {unemploymentData.country} | </span>
                <span style={{ color: '#667eea' }}>Cached until: {new Date(unemploymentData.cache_expires).toLocaleDateString()}</span>
              </div>
              <Plot
                data={[{
                  x: unemploymentData.data.map(d => d.year),
                  y: unemploymentData.data.map(d => d.rate_percent),
                  type: 'scatter',
                  mode: 'lines+markers',
                  fill: 'tozeroy',
                  marker: { color: '#ff9800', size: 8 },
                  line: { color: '#ff9800', width: 3 },
                  fillcolor: 'rgba(255, 152, 0, 0.2)'
                }]}
                layout={{
                  title: `${unemploymentData.country} Unemployment Rate`,
                  xaxis: { title: 'Year' },
                  yaxis: { title: 'Unemployment Rate (%)' },
                  margin: { t: 40, r: 20, b: 40, l: 60 }
                }}
                config={{ displayModeBar: true, displaylogo: false }}
                style={{ width: '100%', height: '450px' }}
              />
            </div>
          </DraggableResizablePanel>
          </div>
        )}
      </div>
    </div>
  );
}

export default EconomyView;
