import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import DraggableResizablePanel from './DraggableResizablePanel';

const API_BASE_URL = 'http://localhost:8000';

function MacroView() {
  const [activeSection, setActiveSection] = useState('overview');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // Z-index management for panels
  const [activePanelId, setActivePanelId] = useState(null);
  const [panelZIndexes, setPanelZIndexes] = useState({});
  
  // Data states
  const [commoditiesData, setCommoditiesData] = useState(null);
  const [currenciesData, setCurrenciesData] = useState(null);
  const [inflationData, setInflationData] = useState(null);
  const [debtToGdpData, setDebtToGdpData] = useState(null);
  const [dollarIndexData, setDollarIndexData] = useState(null);
  const [velocityData, setVelocityData] = useState(null);
  const [unemploymentData, setUnemploymentData] = useState(null);
  const [realEstateData, setRealEstateData] = useState(null);
  const [bondsData, setBondsData] = useState(null);
  const [yieldCurveData, setYieldCurveData] = useState(null);
  const [marketsData, setMarketsData] = useState(null);
  const [overviewData, setOverviewData] = useState(null);
  const [gdpGrowthData, setGdpGrowthData] = useState(null);
  const [consumerSentimentData, setConsumerSentimentData] = useState(null);
  const [pmiData, setPmiData] = useState(null);
  const [retailSalesData, setRetailSalesData] = useState(null);
  
  // Panel state for draggable/resizable charts
  const [chartPanels, setChartPanels] = useState({
    currencies: { position: { x: 20, y: 20 }, size: { width: 900, height: 500 } },
    inflation: { position: { x: 20, y: 20 }, size: { width: 900, height: 500 } },
    debt: { position: { x: 20, y: 20 }, size: { width: 900, height: 500 } },
    dollar: { position: { x: 20, y: 20 }, size: { width: 900, height: 500 } },
    velocity: { position: { x: 20, y: 20 }, size: { width: 900, height: 500 } },
    unemployment: { position: { x: 20, y: 20 }, size: { width: 900, height: 500 } },
    realestate: { position: { x: 20, y: 20 }, size: { width: 900, height: 500 } },
    gdpGrowth: { position: { x: 20, y: 20 }, size: { width: 900, height: 500 } },
    consumerSentiment: { position: { x: 20, y: 20 }, size: { width: 900, height: 500 } },
    pmi: { position: { x: 20, y: 20 }, size: { width: 900, height: 500 } },
    retailSales: { position: { x: 20, y: 20 }, size: { width: 900, height: 500 } },
    commodityEnergy: { position: { x: 20, y: 20 }, size: { width: 600, height: 450 } },
    commodityMetals: { position: { x: 640, y: 20 }, size: { width: 600, height: 450 } },
    commodityAgricultural: { position: { x: 20, y: 490 }, size: { width: 600, height: 450 } },
    commodityLivestock: { position: { x: 640, y: 490 }, size: { width: 600, height: 450 } },
    commodityIndustrial: { position: { x: 20, y: 960 }, size: { width: 600, height: 450 } },
    commodityIndex: { position: { x: 640, y: 960 }, size: { width: 600, height: 450 } },
    bondMajor10y: { position: { x: 20, y: 20 }, size: { width: 600, height: 450 } },
    bondEurope: { position: { x: 640, y: 20 }, size: { width: 600, height: 450 } },
    bondAmerica: { position: { x: 20, y: 490 }, size: { width: 600, height: 450 } },
    bondAsia: { position: { x: 640, y: 490 }, size: { width: 600, height: 450 } },
    bondAustralia: { position: { x: 20, y: 960 }, size: { width: 600, height: 450 } },
    bondAfrica: { position: { x: 640, y: 960 }, size: { width: 600, height: 450 } },
    yieldCurve: { position: { x: 20, y: 20 }, size: { width: 900, height: 500 } },
  });
  
  const updatePanelPosition = (panelId, position) => {
    setChartPanels(prev => ({
      ...prev,
      [panelId]: { ...prev[panelId], position }
    }));
  };

  const fetchMarkets = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_BASE_URL}/api/macro/markets`);
      setMarketsData(response.data);
    } catch (err) {
      setError('Error loading markets data');
      console.error(err);
    } finally {
      setLoading(false);
    }
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

  // Fetch data only when section is active
  useEffect(() => {
    if (activeSection === 'overview' && !overviewData) {
      fetchOverview();
    } else if (activeSection === 'commodities' && !commoditiesData) {
      fetchCommodities();
    } else if (activeSection === 'currencies' && !currenciesData) {
      fetchCurrencies();
    } else if (activeSection === 'inflation' && !inflationData) {
      fetchInflation();
    } else if (activeSection === 'debt' && !debtToGdpData) {
      fetchDebtToGdp();
    } else if (activeSection === 'dollar' && !dollarIndexData) {
      fetchDollarIndex();
    } else if (activeSection === 'velocity' && !velocityData) {
      fetchVelocity();
    } else if (activeSection === 'unemployment' && !unemploymentData) {
      fetchUnemployment();
    } else if (activeSection === 'realestate' && !realEstateData) {
      fetchRealEstate();
    } else if (activeSection === 'bonds' && !bondsData) {
      fetchBonds();
    } else if (activeSection === 'yield-curve' && !yieldCurveData) {
      fetchYieldCurve();
    } else if (activeSection === 'markets' && !marketsData) {
      fetchMarkets();
    } else if (activeSection === 'gdp-growth' && !gdpGrowthData) {
      fetchGdpGrowth();
    } else if (activeSection === 'consumer-sentiment' && !consumerSentimentData) {
      fetchConsumerSentiment();
    } else if (activeSection === 'pmi' && !pmiData) {
      fetchPmi();
    } else if (activeSection === 'retail-sales' && !retailSalesData) {
      fetchRetailSales();
    }
  }, [activeSection]);

  const fetchCommodities = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_BASE_URL}/api/macro/commodities`);
      console.log('Fetched commodities data:', response.data);
      setCommoditiesData(response.data);
    } catch (err) {
      setError('Error loading commodities data');
      console.error('Error fetching commodities:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchCurrencies = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_BASE_URL}/api/macro/currencies`);
      setCurrenciesData(response.data);
    } catch (err) {
      setError('Error loading currencies data');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const fetchInflation = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_BASE_URL}/api/macro/inflation`);
      setInflationData(response.data);
    } catch (err) {
      setError('Error loading inflation data');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const fetchDebtToGdp = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_BASE_URL}/api/macro/debt-to-gdp`);
      setDebtToGdpData(response.data);
    } catch (err) {
      if (err.response?.status === 503) {
        setError(err.response.data.detail);
      } else {
        setError('Error loading debt to GDP data');
      }
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const fetchDollarIndex = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_BASE_URL}/api/macro/dollar-index`);
      setDollarIndexData(response.data);
    } catch (err) {
      if (err.response?.status === 503) {
        setError(err.response.data.detail);
      } else {
        setError('Error loading dollar index data');
      }
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const fetchVelocity = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_BASE_URL}/api/macro/velocity`);
      setVelocityData(response.data);
    } catch (err) {
      if (err.response?.status === 503) {
        setError(err.response.data.detail);
      } else {
        setError('Error loading velocity data');
      }
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const fetchUnemployment = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_BASE_URL}/api/macro/unemployment`);
      setUnemploymentData(response.data);
    } catch (err) {
      setError('Error loading unemployment data');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const fetchRealEstate = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_BASE_URL}/api/macro/real-estate`);
      setRealEstateData(response.data);
    } catch (err) {
      if (err.response?.status === 503) {
        setError(err.response.data.detail);
      } else {
        setError('Error loading real estate data');
      }
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const fetchBonds = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_BASE_URL}/api/macro/bonds`);
      setBondsData(response.data);
    } catch (err) {
      setError('Error loading bonds data');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const fetchYieldCurve = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_BASE_URL}/api/macro/yield-curve`);
      setYieldCurveData(response.data);
    } catch (err) {
      setError('Error loading yield curve data');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const fetchOverview = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_BASE_URL}/api/macro/overview`);
      setOverviewData(response.data);
    } catch (err) {
      setError('Error loading overview data');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const fetchGdpGrowth = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_BASE_URL}/api/macro/gdp-growth`);
      setGdpGrowthData(response.data);
    } catch (err) {
      setError('Error loading GDP growth data');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const fetchConsumerSentiment = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_BASE_URL}/api/macro/consumer-sentiment`);
      setConsumerSentimentData(response.data);
    } catch (err) {
      setError('Error loading consumer sentiment data');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const fetchPmi = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_BASE_URL}/api/macro/pmi`);
      setPmiData(response.data);
    } catch (err) {
      setError('Error loading PMI data');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const fetchRetailSales = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_BASE_URL}/api/macro/retail-sales`);
      setRetailSalesData(response.data);
    } catch (err) {
      setError('Error loading retail sales data');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Decode base64 array if needed (Plotly sometimes encodes large arrays)
  const decodeBase64Array = (data) => {
    if (typeof data === 'string') {
      try {
        const binaryString = atob(data);
        const bytes = new Uint8Array(binaryString.length);
        for (let i = 0; i < binaryString.length; i++) {
          bytes[i] = binaryString.charCodeAt(i);
        }
        const floatArray = new Float64Array(bytes.buffer);
        return Array.from(floatArray);
      } catch (e) {
        console.error('Failed to decode base64 array:', e);
        return [];
      }
    }
    return data;
  };

  // Utility function to convert Plotly data format to Recharts format
  const convertPlotlyToRecharts = (plotlyData) => {
    console.log('Converting Plotly data:', plotlyData);
    
    if (!plotlyData) {
      console.log('No plotly data provided');
      return [];
    }
    
    // Handle the Plotly JSON structure which has both 'data' and 'layout'
    const traces = plotlyData.data || [];
    
    if (traces.length === 0) {
      console.log('No traces found in plotly data');
      return [];
    }
    
    // Check if this is a table type (not a chart)
    if (traces[0] && traces[0].type === 'table') {
      console.log('This is a table, not a chart');
      return [];
    }
    
    console.log('Found traces:', traces.length);
    
    const result = [];
    
    // Find the maximum length across all traces
    const maxLength = Math.max(...traces.map(trace => {
      const x = trace.x || [];
      return Array.isArray(x) ? x.length : 0;
    }));
    
    console.log('Max data points:', maxLength);
    
    // Build recharts data format
    for (let i = 0; i < maxLength; i++) {
      const point = {};
      let hasDate = false;
      
      traces.forEach((trace, traceIndex) => {
        const xData = trace.x || [];
        let yData = trace.y || [];
        
        // Decode base64 if needed
        yData = decodeBase64Array(yData);
        
        if (xData[i] !== undefined && xData[i] !== null) {
          // Handle date formatting
          const dateValue = xData[i];
          if (typeof dateValue === 'string') {
            // Extract just the date part if it's an ISO string
            point.date = dateValue.split('T')[0];
          } else if (typeof dateValue === 'number') {
            point.date = new Date(dateValue).toISOString().split('T')[0];
          } else {
            point.date = String(dateValue);
          }
          hasDate = true;
        }
        
        if (yData[i] !== undefined && yData[i] !== null) {
          const key = trace.name || `Series ${traceIndex + 1}`;
          const value = typeof yData[i] === 'number' ? yData[i] : parseFloat(yData[i]);
          if (!isNaN(value)) {
            point[key] = value;
          }
        }
      });
      
      if (hasDate && Object.keys(point).length > 1) {
        result.push(point);
      }
    }
    
    console.log('Converted data points:', result.length);
    if (result.length > 0) {
      console.log('Sample data point:', result[0]);
    }
    
    return result;
  };

  // Get all series keys from recharts data
  const getSeriesKeys = (data) => {
    if (!data || data.length === 0) return [];
    return Object.keys(data[0]).filter(key => key !== 'date');
  };

  // Get random color for series
  const getColor = (index) => {
    const colors = [
      '#8884d8', '#82ca9d', '#ffc658', '#ff7c7c', '#a4de6c',
      '#d084d0', '#8dd1e1', '#ffbb28', '#ff8042', '#00C49F'
    ];
    return colors[index % colors.length];
  };

  // Format large numbers
  const formatValue = (value) => {
    if (value === null || value === undefined) return '-';
    const num = parseFloat(value);
    if (isNaN(num)) return value;
    
    if (Math.abs(num) >= 1e9) {
      return (num / 1e9).toFixed(2) + 'B';
    } else if (Math.abs(num) >= 1e6) {
      return (num / 1e6).toFixed(2) + 'M';
    } else if (Math.abs(num) >= 1e3) {
      return (num / 1e3).toFixed(2) + 'K';
    }
    return num.toFixed(2);
  };

  // Render table (for commodities, currencies, etc.)
  const renderTable = (plotlyData, title) => {
    console.log(`Rendering table: ${title}`, plotlyData);
    
    if (!plotlyData || !plotlyData.data || plotlyData.data.length === 0) {
      return (
        <div className="chart-container" style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
          <h4>{title}</h4>
          <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <div className="chart-loading">No data available</div>
          </div>
        </div>
      );
    }

    const tableData = plotlyData.data[0];
    if (tableData.type !== 'table' || !tableData.header || !tableData.cells) {
      return <div className="chart-loading">Invalid table data</div>;
    }

    const headers = tableData.header.values || [];
    const cells = tableData.cells.values || [];
    const numRows = cells.length > 0 ? cells[0].length : 0;

    return (
      <div className="chart-container" style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
        <h4>{title}</h4>
        <div style={{ flex: 1, overflow: 'auto' }}>
          <div className="table-wrapper">
            <table className="financial-table">
              <thead>
                <tr>
                  {headers.map((header, idx) => (
                    <th key={idx}>{header}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {Array.from({ length: numRows }).map((_, rowIdx) => (
                  <tr key={rowIdx}>
                    {cells.map((colData, colIdx) => (
                      <td key={colIdx} className={colIdx === 0 ? 'row-name-col' : 'data-cell'}>
                        {colData[rowIdx] !== undefined && colData[rowIdx] !== null 
                          ? String(colData[rowIdx]) 
                          : '-'}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    );
  };

  // Render chart using Recharts (matching stock chart style)
  const renderChart = (data, title) => {
    console.log(`Rendering chart: ${title}`, data);
    
    if (!data) {
      console.error(`No data provided for ${title}`);
      return (
        <div className="chart-container" style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
          <h4>{title}</h4>
          <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <div className="chart-loading">No data available</div>
          </div>
        </div>
      );
    }

    // Check if this is a table type
    if (data.data && data.data[0] && data.data[0].type === 'table') {
      return renderTable(data, title);
    }

    const chartData = convertPlotlyToRecharts(data);
    const seriesKeys = getSeriesKeys(chartData);
    
    if (chartData.length === 0) {
      console.warn(`No chart data after conversion for ${title}`);
      return (
        <div className="chart-container" style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
          <h4>{title}</h4>
          <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <div className="chart-loading">Unable to load chart data</div>
          </div>
        </div>
      );
    }

    console.log(`Successfully converted data for ${title}:`, chartData.length, 'points');

    return (
      <div className="chart-container" style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
        <h4>{title}</h4>
        <div style={{ flex: 1 }}>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="date" 
                angle={-45} 
                textAnchor="end" 
                height={80}
                tick={{ fontSize: 12 }}
              />
              <YAxis 
                tickFormatter={formatValue}
                tick={{ fontSize: 12 }}
              />
              <Tooltip formatter={formatValue} />
              <Legend wrapperStyle={{ paddingTop: '10px' }} />
              {seriesKeys.map((key, idx) => (
                <Line
                  key={key}
                  type="monotone"
                  dataKey={key}
                  stroke={getColor(idx)}
                  strokeWidth={2}
                  dot={false}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    );
  };

  return (
    <div className="macro-view">
      <h2>🌍 Economic Indicators</h2>
      
      {/* Section Navigation */}
      <div className="macro-sections">
        <button
          className={`section-btn ${activeSection === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveSection('overview')}
        >
          Overview
        </button>
        <button
          className={`section-btn ${activeSection === 'commodities' ? 'active' : ''}`}
          onClick={() => setActiveSection('commodities')}
        >
          Commodities
        </button>
        <button
          className={`section-btn ${activeSection === 'currencies' ? 'active' : ''}`}
          onClick={() => setActiveSection('currencies')}
        >
          Currencies
        </button>
        <button
          className={`section-btn ${activeSection === 'inflation' ? 'active' : ''}`}
          onClick={() => setActiveSection('inflation')}
        >
          Inflation
        </button>
        <button
          className={`section-btn ${activeSection === 'debt' ? 'active' : ''}`}
          onClick={() => setActiveSection('debt')}
        >
          Debt/GDP
        </button>
        <button
          className={`section-btn ${activeSection === 'dollar' ? 'active' : ''}`}
          onClick={() => setActiveSection('dollar')}
        >
          Dollar Index
        </button>
        <button
          className={`section-btn ${activeSection === 'velocity' ? 'active' : ''}`}
          onClick={() => setActiveSection('velocity')}
        >
          Money Velocity
        </button>
        <button
          className={`section-btn ${activeSection === 'unemployment' ? 'active' : ''}`}
          onClick={() => setActiveSection('unemployment')}
        >
          Unemployment
        </button>
        <button
          className={`section-btn ${activeSection === 'realestate' ? 'active' : ''}`}
          onClick={() => setActiveSection('realestate')}
        >
          Real Estate
        </button>
        <button
          className={`section-btn ${activeSection === 'bonds' ? 'active' : ''}`}
          onClick={() => setActiveSection('bonds')}
        >
          Bonds
        </button>
        <button
          className={`section-btn ${activeSection === 'yield-curve' ? 'active' : ''}`}
          onClick={() => setActiveSection('yield-curve')}
        >
          📊 Interest Rates
        </button>
        <button
          className={`section-btn ${activeSection === 'markets' ? 'active' : ''}`}
          onClick={() => setActiveSection('markets')}
        >
          Markets
        </button>
        <button
          className={`section-btn ${activeSection === 'gdp-growth' ? 'active' : ''}`}
          onClick={() => setActiveSection('gdp-growth')}
        >
          GDP Growth
        </button>
        <button
          className={`section-btn ${activeSection === 'consumer-sentiment' ? 'active' : ''}`}
          onClick={() => setActiveSection('consumer-sentiment')}
        >
          Consumer Sentiment
        </button>
        <button
          className={`section-btn ${activeSection === 'pmi' ? 'active' : ''}`}
          onClick={() => setActiveSection('pmi')}
        >
          Manufacturing PMI
        </button>
        <button
          className={`section-btn ${activeSection === 'retail-sales' ? 'active' : ''}`}
          onClick={() => setActiveSection('retail-sales')}
        >
          Retail Sales
        </button>
      </div>

      {/* Content Area */}
      <div className="macro-content">
        {loading && <div className="loading">Loading data...</div>}
        {error && <div className="error">{error}</div>}

        {/* Overview */}
        {activeSection === 'overview' && (
          <div className="macro-overview">
            <h3>Economic Data Dashboard</h3>
            <p>Select a category above to view detailed economic indicators and trends.</p>
            <div className="overview-grid">
              <div className="overview-card" onClick={() => setActiveSection('commodities')} style={{ cursor: 'pointer' }}>
                <h4>📊 Commodities</h4>
                <p>Energy, Metals, Agricultural, Livestock, Industrial</p>
              </div>
              <div className="overview-card" onClick={() => setActiveSection('currencies')} style={{ cursor: 'pointer' }}>
                <h4>💱 Currencies</h4>
                <p>Major global currency exchange rates</p>
              </div>
              <div className="overview-card" onClick={() => setActiveSection('inflation')} style={{ cursor: 'pointer' }}>
                <h4>📈 Inflation</h4>
                <p>CPI and inflation trends</p>
              </div>
              <div className="overview-card" onClick={() => setActiveSection('debt')} style={{ cursor: 'pointer' }}>
                <h4>💰 Debt/GDP</h4>
                <p>National debt to GDP ratio</p>
              </div>
              <div className="overview-card" onClick={() => setActiveSection('dollar')} style={{ cursor: 'pointer' }}>
                <h4> Dollar Index</h4>
                <p>US Dollar strength indicator</p>
              </div>
              <div className="overview-card" onClick={() => setActiveSection('velocity')} style={{ cursor: 'pointer' }}>
                <h4>⚡ Money Velocity</h4>
                <p>Money circulation rate</p>
              </div>
              <div className="overview-card" onClick={() => setActiveSection('unemployment')} style={{ cursor: 'pointer' }}>
                <h4>👥 Unemployment</h4>
                <p>Employment statistics</p>
              </div>
              <div className="overview-card" onClick={() => setActiveSection('realestate')} style={{ cursor: 'pointer' }}>
                <h4>🏠 Real Estate</h4>
                <p>Housing market trends</p>
              </div>
              <div className="overview-card" onClick={() => setActiveSection('bonds')} style={{ cursor: 'pointer' }}>
                <h4>🌐 Bonds</h4>
                <p>Global bond yields</p>
              </div>
            </div>
          </div>
        )}

        {/* Markets */}
        {activeSection === 'markets' && marketsData && (
          <div className="markets-section" style={{ position: 'relative', minHeight: '400px' }}>
            <h3>Key Market Indicators</h3>
            <DraggableResizablePanel
              id="marketsTable"
              position={{ x: 20, y: 20 }}
              size={{ width: 900, height: 400 }}
              onPositionChange={() => {}}
              onSizeChange={() => {}}
              minWidth={500}
              minHeight={300}
            >
              {renderTable(marketsData.chart, 'Markets Overview')}
            </DraggableResizablePanel>
          </div>
        )}

        {/* Commodities */}
        {activeSection === 'commodities' && commoditiesData && (
          <div className="commodities-section">
            <div className="data-section">
              <h3>Commodities Data</h3>
              <div style={{ position: 'relative', minHeight: '1450px' }}>
              <DraggableResizablePanel
                id="commodityEnergy"
                position={chartPanels.commodityEnergy.position}
                size={chartPanels.commodityEnergy.size}
                onPositionChange={(pos) => updatePanelPosition('commodityEnergy', pos)}
                onSizeChange={(size) => updatePanelSize('commodityEnergy', size)}
                onFocus={handlePanelFocus}
                zIndex={getPanelZIndex('commodityEnergy')}
                minWidth={400}
                minHeight={300}
              >
              {renderChart(commoditiesData.energy.chart, 'Energy Commodities')}
            </DraggableResizablePanel>
            
            <DraggableResizablePanel
              id="commodityMetals"
              position={chartPanels.commodityMetals.position}
              size={chartPanels.commodityMetals.size}
              onPositionChange={(pos) => updatePanelPosition('commodityMetals', pos)}
              onSizeChange={(size) => updatePanelSize('commodityMetals', size)}
              onFocus={handlePanelFocus}
              zIndex={getPanelZIndex('commodityMetals')}
              minWidth={400}
              minHeight={300}
            >
              {renderChart(commoditiesData.metals.chart, 'Metals')}
            </DraggableResizablePanel>
            
            <DraggableResizablePanel
              id="commodityAgricultural"
              position={chartPanels.commodityAgricultural.position}
              size={chartPanels.commodityAgricultural.size}
              onPositionChange={(pos) => updatePanelPosition('commodityAgricultural', pos)}
              onSizeChange={(size) => updatePanelSize('commodityAgricultural', size)}
              onFocus={handlePanelFocus}
              zIndex={getPanelZIndex('commodityAgricultural')}
              minWidth={400}
              minHeight={300}
            >
              {renderChart(commoditiesData.agricultural.chart, 'Agricultural')}
            </DraggableResizablePanel>
            
            <DraggableResizablePanel
              id="commodityLivestock"
              position={chartPanels.commodityLivestock.position}
              size={chartPanels.commodityLivestock.size}
              onPositionChange={(pos) => updatePanelPosition('commodityLivestock', pos)}
              onSizeChange={(size) => updatePanelSize('commodityLivestock', size)}
              onFocus={handlePanelFocus}
              zIndex={getPanelZIndex('commodityLivestock')}
              minWidth={400}
              minHeight={300}
            >
              {renderChart(commoditiesData.livestock.chart, 'Livestock')}
            </DraggableResizablePanel>
            
            <DraggableResizablePanel
              id="commodityIndustrial"
              position={chartPanels.commodityIndustrial.position}
              size={chartPanels.commodityIndustrial.size}
              onPositionChange={(pos) => updatePanelPosition('commodityIndustrial', pos)}
              onSizeChange={(size) => updatePanelSize('commodityIndustrial', size)}
              onFocus={handlePanelFocus}
              zIndex={getPanelZIndex('commodityIndustrial')}
              minWidth={400}
              minHeight={300}
            >
              {renderChart(commoditiesData.industrial.chart, 'Industrial')}
            </DraggableResizablePanel>
            
            <DraggableResizablePanel
              id="commodityIndex"
              position={chartPanels.commodityIndex.position}
              size={chartPanels.commodityIndex.size}
              onPositionChange={(pos) => updatePanelPosition('commodityIndex', pos)}
              onSizeChange={(size) => updatePanelSize('commodityIndex', size)}
              onFocus={handlePanelFocus}
              zIndex={getPanelZIndex('commodityIndex')}
              minWidth={400}
              minHeight={300}
            >
              {renderChart(commoditiesData.index.chart, 'Commodity Index')}
            </DraggableResizablePanel>
              </div>
            </div>
          </div>
        )}

        {/* Currencies */}
        {activeSection === 'currencies' && currenciesData && (
          <div className="currencies-section">
            <div className="data-section">
              <h3>Major Currencies</h3>
              <div style={{ position: 'relative', minHeight: '600px' }}>
              <DraggableResizablePanel
                id="currencies"
                position={chartPanels.currencies.position}
                size={chartPanels.currencies.size}
                onPositionChange={(pos) => updatePanelPosition('currencies', pos)}
                onSizeChange={(size) => updatePanelSize('currencies', size)}
                onFocus={handlePanelFocus}
                zIndex={getPanelZIndex('currencies')}
                minWidth={500}
                minHeight={350}
              >
                {renderChart(currenciesData.chart, 'Major Currencies')}
              </DraggableResizablePanel>
              </div>
            </div>
          </div>
        )}

        {/* Inflation */}
        {activeSection === 'inflation' && inflationData && (
          <div className="inflation-section">
            <div className="data-section">
              <h3>CPI Inflation</h3>
              <div style={{ position: 'relative', minHeight: '600px' }}>
              <DraggableResizablePanel
                id="inflation"
                position={chartPanels.inflation.position}
                size={chartPanels.inflation.size}
                onPositionChange={(pos) => updatePanelPosition('inflation', pos)}
                onSizeChange={(size) => updatePanelSize('inflation', size)}
                onFocus={handlePanelFocus}
                zIndex={getPanelZIndex('inflation')}
                minWidth={500}
                minHeight={350}
              >
                {renderChart(inflationData.chart, 'CPI Inflation')}
              </DraggableResizablePanel>
              </div>
            </div>
          </div>
        )}

        {/* Debt to GDP */}
        {activeSection === 'debt' && debtToGdpData && (
          <div className="debt-section">
            <div className="data-section">
              <h3>Debt to GDP Ratio</h3>
              <div style={{ position: 'relative', minHeight: '600px' }}>
              <DraggableResizablePanel
                id="debt"
                position={chartPanels.debt.position}
                size={chartPanels.debt.size}
                onPositionChange={(pos) => updatePanelPosition('debt', pos)}
                onSizeChange={(size) => updatePanelSize('debt', size)}
                onFocus={handlePanelFocus}
                zIndex={getPanelZIndex('debt')}
                minWidth={500}
                minHeight={350}
              >
                {renderChart(debtToGdpData.chart, 'Debt to GDP Ratio')}
              </DraggableResizablePanel>
              </div>
            </div>
          </div>
        )}

        {/* Dollar Index */}
        {activeSection === 'dollar' && dollarIndexData && (
          <div className="dollar-section">
            <div className="data-section">
              <h3>Dollar Index</h3>
              <div style={{ position: 'relative', minHeight: '600px' }}>
              <DraggableResizablePanel
                id="dollar"
                position={chartPanels.dollar.position}
                size={chartPanels.dollar.size}
                onPositionChange={(pos) => updatePanelPosition('dollar', pos)}
                onSizeChange={(size) => updatePanelSize('dollar', size)}
                onFocus={handlePanelFocus}
                zIndex={getPanelZIndex('dollar')}
                minWidth={500}
                minHeight={350}
              >
                {renderChart(dollarIndexData.chart, 'Dollar Index')}
              </DraggableResizablePanel>
              </div>
            </div>
          </div>
        )}

        {/* Velocity */}
        {activeSection === 'velocity' && velocityData && (
          <div className="velocity-section">
            <div className="data-section">
              <h3>Money Velocity</h3>
              <div style={{ position: 'relative', minHeight: '600px' }}>
              <DraggableResizablePanel
                id="velocity"
                position={chartPanels.velocity.position}
                size={chartPanels.velocity.size}
                onPositionChange={(pos) => updatePanelPosition('velocity', pos)}
                onSizeChange={(size) => updatePanelSize('velocity', size)}
                onFocus={handlePanelFocus}
                zIndex={getPanelZIndex('velocity')}
                minWidth={500}
                minHeight={350}
              >
                {renderChart(velocityData.chart, 'Money Velocity')}
              </DraggableResizablePanel>
              </div>
            </div>
          </div>
        )}

        {/* Unemployment */}
        {activeSection === 'unemployment' && unemploymentData && (
          <div className="unemployment-section">
            <div className="data-section">
              <h3>Unemployment Rate</h3>
              <div style={{ position: 'relative', minHeight: '600px' }}>
              <DraggableResizablePanel
                id="unemployment"
                position={chartPanels.unemployment.position}
                size={chartPanels.unemployment.size}
                onPositionChange={(pos) => updatePanelPosition('unemployment', pos)}
                onSizeChange={(size) => updatePanelSize('unemployment', size)}
                onFocus={handlePanelFocus}
                zIndex={getPanelZIndex('unemployment')}
                minWidth={500}
                minHeight={350}
              >
                {renderChart(unemploymentData.chart, 'Unemployment Rate')}
              </DraggableResizablePanel>
              </div>
            </div>
          </div>
        )}

        {/* Real Estate */}
        {activeSection === 'realestate' && realEstateData && (
          <div className="realestate-section">
            <div className="data-section">
              <h3>Real Estate Trends</h3>
              <div style={{ position: 'relative', minHeight: '600px' }}>
              <DraggableResizablePanel
                id="realestate"
                position={chartPanels.realestate.position}
                size={chartPanels.realestate.size}
                onPositionChange={(pos) => updatePanelPosition('realestate', pos)}
                onSizeChange={(size) => updatePanelSize('realestate', size)}
                onFocus={handlePanelFocus}
                zIndex={getPanelZIndex('realestate')}
                minWidth={500}
                minHeight={350}
              >
                {renderChart(realEstateData.chart, 'Real Estate Trends')}
              </DraggableResizablePanel>
              </div>
            </div>
          </div>
        )}

        {/* Bonds */}
        {activeSection === 'bonds' && bondsData && (
          <div className="bonds-section">
            <div className="data-section">
              <h3>Global Bonds</h3>
              <div style={{ position: 'relative', minHeight: '1450px' }}>
            <DraggableResizablePanel
              id="bondMajor10y"
              position={chartPanels.bondMajor10y.position}
              size={chartPanels.bondMajor10y.size}
              onPositionChange={(pos) => updatePanelPosition('bondMajor10y', pos)}
              onSizeChange={(size) => updatePanelSize('bondMajor10y', size)}
              onFocus={handlePanelFocus}
              zIndex={getPanelZIndex('bondMajor10y')}
              minWidth={400}
              minHeight={300}
            >
              {renderChart(bondsData.major_10y, 'Major 10Y Bonds')}
            </DraggableResizablePanel>
            
            <DraggableResizablePanel
              id="bondEurope"
              position={chartPanels.bondEurope.position}
              size={chartPanels.bondEurope.size}
              onPositionChange={(pos) => updatePanelPosition('bondEurope', pos)}
              onSizeChange={(size) => updatePanelSize('bondEurope', size)}
              onFocus={handlePanelFocus}
              zIndex={getPanelZIndex('bondEurope')}
              minWidth={400}
              minHeight={300}
            >
              {renderChart(bondsData.europe, 'Europe Bonds')}
            </DraggableResizablePanel>
            
            <DraggableResizablePanel
              id="bondAmerica"
              position={chartPanels.bondAmerica.position}
              size={chartPanels.bondAmerica.size}
              onPositionChange={(pos) => updatePanelPosition('bondAmerica', pos)}
              onSizeChange={(size) => updatePanelSize('bondAmerica', size)}
              onFocus={handlePanelFocus}
              zIndex={getPanelZIndex('bondAmerica')}
              minWidth={400}
              minHeight={300}
            >
              {renderChart(bondsData.america, 'America Bonds')}
            </DraggableResizablePanel>
            
            <DraggableResizablePanel
              id="bondAsia"
              position={chartPanels.bondAsia.position}
              size={chartPanels.bondAsia.size}
              onPositionChange={(pos) => updatePanelPosition('bondAsia', pos)}
              onSizeChange={(size) => updatePanelSize('bondAsia', size)}
              onFocus={handlePanelFocus}
              zIndex={getPanelZIndex('bondAsia')}
              minWidth={400}
              minHeight={300}
            >
              {renderChart(bondsData.asia, 'Asia Bonds')}
            </DraggableResizablePanel>
            
            <DraggableResizablePanel
              id="bondAustralia"
              position={chartPanels.bondAustralia.position}
              size={chartPanels.bondAustralia.size}
              onPositionChange={(pos) => updatePanelPosition('bondAustralia', pos)}
              onSizeChange={(size) => updatePanelSize('bondAustralia', size)}
              onFocus={handlePanelFocus}
              zIndex={getPanelZIndex('bondAustralia')}
              minWidth={400}
              minHeight={300}
            >
              {renderChart(bondsData.australia, 'Australia Bonds')}
            </DraggableResizablePanel>
            
            <DraggableResizablePanel
              id="bondAfrica"
              position={chartPanels.bondAfrica.position}
              size={chartPanels.bondAfrica.size}
              onPositionChange={(pos) => updatePanelPosition('bondAfrica', pos)}
              onSizeChange={(size) => updatePanelSize('bondAfrica', size)}
              onFocus={handlePanelFocus}
              zIndex={getPanelZIndex('bondAfrica')}
              minWidth={400}
              minHeight={300}
            >
              {renderChart(bondsData.africa, 'Africa Bonds')}
            </DraggableResizablePanel>
              </div>
            </div>
          </div>
        )}

        {/* Yield Curve / Interest Rates */}
        {activeSection === 'yield-curve' && yieldCurveData && (
          <div className="yield-curve-section">
            <div className="data-section">
              <h3>📊 US Treasury Yield Curve</h3>
              <p className="section-description">
                The yield curve shows the relationship between interest rates and different maturity periods for US Treasury securities.
                An inverted yield curve (short-term rates higher than long-term) often signals economic uncertainty.
              </p>
              <div style={{ position: 'relative', minHeight: '600px' }}>
              <DraggableResizablePanel
                id="yieldCurve"
                position={chartPanels.yieldCurve.position}
                size={chartPanels.yieldCurve.size}
                onPositionChange={(pos) => updatePanelPosition('yieldCurve', pos)}
                onSizeChange={(size) => updatePanelSize('yieldCurve', size)}
                onFocus={handlePanelFocus}
                zIndex={getPanelZIndex('yieldCurve')}
                minWidth={500}
                minHeight={350}
              >
                {renderChart(yieldCurveData.chart, 'US Treasury Yield Curve')}
              </DraggableResizablePanel>
              </div>
            </div>
          </div>
        )}

        {/* GDP Growth */}
        {activeSection === 'gdp-growth' && gdpGrowthData && (
          <div className="gdp-section">
            <div className="data-section">
              <h3>📈 GDP Growth Rate</h3>
              <div style={{ position: 'relative', minHeight: '600px' }}>
              <DraggableResizablePanel
                id="gdpGrowth"
                position={chartPanels.gdpGrowth.position}
                size={chartPanels.gdpGrowth.size}
                onPositionChange={(pos) => updatePanelPosition('gdpGrowth', pos)}
                onSizeChange={(size) => updatePanelSize('gdpGrowth', size)}
                onFocus={handlePanelFocus}
                zIndex={getPanelZIndex('gdpGrowth')}
                minWidth={500}
                minHeight={350}
              >
                {renderChart(gdpGrowthData.chart, 'US Real GDP Growth')}
              </DraggableResizablePanel>
              </div>
            </div>
          </div>
        )}

        {/* Consumer Sentiment */}
        {activeSection === 'consumer-sentiment' && consumerSentimentData && (
          <div className="sentiment-section">
            <div className="data-section">
              <h3>💭 Consumer Sentiment Index</h3>
              <div style={{ position: 'relative', minHeight: '600px' }}>
              <DraggableResizablePanel
                id="consumerSentiment"
                position={chartPanels.consumerSentiment.position}
                size={chartPanels.consumerSentiment.size}
                onPositionChange={(pos) => updatePanelPosition('consumerSentiment', pos)}
                onSizeChange={(size) => updatePanelSize('consumerSentiment', size)}
                onFocus={handlePanelFocus}
                zIndex={getPanelZIndex('consumerSentiment')}
                minWidth={500}
                minHeight={350}
              >
                {renderChart(consumerSentimentData.chart, 'Consumer Sentiment')}
              </DraggableResizablePanel>
              </div>
            </div>
          </div>
        )}

        {/* Manufacturing PMI */}
        {activeSection === 'pmi' && pmiData && (
          <div className="pmi-section">
            <div className="data-section">
              <h3>🏭 Manufacturing PMI</h3>
              <div style={{ position: 'relative', minHeight: '600px' }}>
              <DraggableResizablePanel
                id="pmi"
                position={chartPanels.pmi.position}
                size={chartPanels.pmi.size}
                onPositionChange={(pos) => updatePanelPosition('pmi', pos)}
                onSizeChange={(size) => updatePanelSize('pmi', size)}
                onFocus={handlePanelFocus}
                zIndex={getPanelZIndex('pmi')}
                minWidth={500}
                minHeight={350}
              >
                {renderChart(pmiData.chart, 'Manufacturing PMI')}
              </DraggableResizablePanel>
              </div>
            </div>
          </div>
        )}

        {/* Retail Sales */}
        {activeSection === 'retail-sales' && retailSalesData && (
          <div className="retail-section">
            <div className="data-section">
              <h3>🛒 Retail Sales</h3>
              <div style={{ position: 'relative', minHeight: '600px' }}>
              <DraggableResizablePanel
                id="retailSales"
                position={chartPanels.retailSales.position}
                size={chartPanels.retailSales.size}
                onPositionChange={(pos) => updatePanelPosition('retailSales', pos)}
                onSizeChange={(size) => updatePanelSize('retailSales', size)}
                onFocus={handlePanelFocus}
                zIndex={getPanelZIndex('retailSales')}
                minWidth={500}
                minHeight={350}
              >
                {renderChart(retailSalesData.chart, 'US Retail Sales')}
              </DraggableResizablePanel>
              </div>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}

export default MacroView;
