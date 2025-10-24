import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Plot from 'react-plotly.js';
import DraggableResizablePanel from './DraggableResizablePanel';

const API_BASE_URL = 'http://localhost:8000';

function MacroView() {
  const [activeSection, setActiveSection] = useState('overview');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
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
  const [overviewData, setOverviewData] = useState(null);
  
  // Panel state for draggable/resizable charts
  const [chartPanels, setChartPanels] = useState({
    currencies: { position: { x: 20, y: 20 }, size: { width: 900, height: 500 } },
    inflation: { position: { x: 20, y: 20 }, size: { width: 900, height: 500 } },
    debt: { position: { x: 20, y: 20 }, size: { width: 900, height: 500 } },
    dollar: { position: { x: 20, y: 20 }, size: { width: 900, height: 500 } },
    velocity: { position: { x: 20, y: 20 }, size: { width: 900, height: 500 } },
    unemployment: { position: { x: 20, y: 20 }, size: { width: 900, height: 500 } },
    realestate: { position: { x: 20, y: 20 }, size: { width: 900, height: 500 } },
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
  
  const updatePanelSize = (panelId, size) => {
    setChartPanels(prev => ({
      ...prev,
      [panelId]: { ...prev[panelId], size }
    }));
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
    }
  }, [activeSection]);

  const fetchCommodities = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_BASE_URL}/api/macro/commodities`);
      setCommoditiesData(response.data);
    } catch (err) {
      setError('Error loading commodities data');
      console.error(err);
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
                <h4>� Dollar Index</h4>
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

        {/* Commodities */}
        {activeSection === 'commodities' && commoditiesData && (
          <div className="commodities-section" style={{ position: 'relative', minHeight: '1450px' }}>
            <h3>Commodities Data</h3>
            <DraggableResizablePanel
              id="commodityEnergy"
              position={chartPanels.commodityEnergy.position}
              size={chartPanels.commodityEnergy.size}
              onPositionChange={(pos) => updatePanelPosition('commodityEnergy', pos)}
              onSizeChange={(size) => updatePanelSize('commodityEnergy', size)}
              minWidth={400}
              minHeight={300}
            >
              <div className="macro-chart" style={{ height: '100%' }}>
                <h4>Energy</h4>
                <Plot 
                  data={commoditiesData.energy.chart.data} 
                  layout={commoditiesData.energy.chart.layout} 
                  style={{ width: '100%', height: 'calc(100% - 40px)' }}
                  useResizeHandler={true}
                  config={{ responsive: true }}
                />
              </div>
            </DraggableResizablePanel>
            
            <DraggableResizablePanel
              id="commodityMetals"
              position={chartPanels.commodityMetals.position}
              size={chartPanels.commodityMetals.size}
              onPositionChange={(pos) => updatePanelPosition('commodityMetals', pos)}
              onSizeChange={(size) => updatePanelSize('commodityMetals', size)}
              minWidth={400}
              minHeight={300}
            >
              <div className="macro-chart" style={{ height: '100%' }}>
                <h4>Metals</h4>
                <Plot 
                  data={commoditiesData.metals.chart.data} 
                  layout={commoditiesData.metals.chart.layout} 
                  style={{ width: '100%', height: 'calc(100% - 40px)' }}
                  useResizeHandler={true}
                  config={{ responsive: true }}
                />
              </div>
            </DraggableResizablePanel>
            
            <DraggableResizablePanel
              id="commodityAgricultural"
              position={chartPanels.commodityAgricultural.position}
              size={chartPanels.commodityAgricultural.size}
              onPositionChange={(pos) => updatePanelPosition('commodityAgricultural', pos)}
              onSizeChange={(size) => updatePanelSize('commodityAgricultural', size)}
              minWidth={400}
              minHeight={300}
            >
              <div className="macro-chart" style={{ height: '100%' }}>
                <h4>Agricultural</h4>
                <Plot 
                  data={commoditiesData.agricultural.chart.data} 
                  layout={commoditiesData.agricultural.chart.layout} 
                  style={{ width: '100%', height: 'calc(100% - 40px)' }}
                  useResizeHandler={true}
                  config={{ responsive: true }}
                />
              </div>
            </DraggableResizablePanel>
            
            <DraggableResizablePanel
              id="commodityLivestock"
              position={chartPanels.commodityLivestock.position}
              size={chartPanels.commodityLivestock.size}
              onPositionChange={(pos) => updatePanelPosition('commodityLivestock', pos)}
              onSizeChange={(size) => updatePanelSize('commodityLivestock', size)}
              minWidth={400}
              minHeight={300}
            >
              <div className="macro-chart" style={{ height: '100%' }}>
                <h4>Livestock</h4>
                <Plot 
                  data={commoditiesData.livestock.chart.data} 
                  layout={commoditiesData.livestock.chart.layout} 
                  style={{ width: '100%', height: 'calc(100% - 40px)' }}
                  useResizeHandler={true}
                  config={{ responsive: true }}
                />
              </div>
            </DraggableResizablePanel>
            
            <DraggableResizablePanel
              id="commodityIndustrial"
              position={chartPanels.commodityIndustrial.position}
              size={chartPanels.commodityIndustrial.size}
              onPositionChange={(pos) => updatePanelPosition('commodityIndustrial', pos)}
              onSizeChange={(size) => updatePanelSize('commodityIndustrial', size)}
              minWidth={400}
              minHeight={300}
            >
              <div className="macro-chart" style={{ height: '100%' }}>
                <h4>Industrial</h4>
                <Plot 
                  data={commoditiesData.industrial.chart.data} 
                  layout={commoditiesData.industrial.chart.layout} 
                  style={{ width: '100%', height: 'calc(100% - 40px)' }}
                  useResizeHandler={true}
                  config={{ responsive: true }}
                />
              </div>
            </DraggableResizablePanel>
            
            <DraggableResizablePanel
              id="commodityIndex"
              position={chartPanels.commodityIndex.position}
              size={chartPanels.commodityIndex.size}
              onPositionChange={(pos) => updatePanelPosition('commodityIndex', pos)}
              onSizeChange={(size) => updatePanelSize('commodityIndex', size)}
              minWidth={400}
              minHeight={300}
            >
              <div className="macro-chart" style={{ height: '100%' }}>
                <h4>Index</h4>
                <Plot 
                  data={commoditiesData.index.chart.data} 
                  layout={commoditiesData.index.chart.layout} 
                  style={{ width: '100%', height: 'calc(100% - 40px)' }}
                  useResizeHandler={true}
                  config={{ responsive: true }}
                />
              </div>
            </DraggableResizablePanel>
          </div>
        )}

        {/* Currencies */}
        {activeSection === 'currencies' && currenciesData && (
          <div className="currencies-section" style={{ position: 'relative', minHeight: '600px' }}>
            <h3>Major Currencies</h3>
            <DraggableResizablePanel
              id="currencies"
              position={chartPanels.currencies.position}
              size={chartPanels.currencies.size}
              onPositionChange={(pos) => updatePanelPosition('currencies', pos)}
              onSizeChange={(size) => updatePanelSize('currencies', size)}
              minWidth={500}
              minHeight={350}
            >
              <Plot 
                data={currenciesData.chart.data} 
                layout={currenciesData.chart.layout} 
                style={{ width: '100%', height: '100%' }}
                useResizeHandler={true}
                  config={{ responsive: true }}
              />
            </DraggableResizablePanel>
          </div>
        )}

        {/* Inflation */}
        {activeSection === 'inflation' && inflationData && (
          <div className="inflation-section" style={{ position: 'relative', minHeight: '600px' }}>
            <h3>CPI Inflation</h3>
            <DraggableResizablePanel
              id="inflation"
              position={chartPanels.inflation.position}
              size={chartPanels.inflation.size}
              onPositionChange={(pos) => updatePanelPosition('inflation', pos)}
              onSizeChange={(size) => updatePanelSize('inflation', size)}
              minWidth={500}
              minHeight={350}
            >
              <Plot 
                data={inflationData.chart.data} 
                layout={inflationData.chart.layout} 
                style={{ width: '100%', height: '100%' }}
                useResizeHandler={true}
                  config={{ responsive: true }}
              />
            </DraggableResizablePanel>
          </div>
        )}

        {/* Debt to GDP */}
        {activeSection === 'debt' && debtToGdpData && (
          <div className="debt-section" style={{ position: 'relative', minHeight: '600px' }}>
            <h3>Debt to GDP Ratio</h3>
            <DraggableResizablePanel
              id="debt"
              position={chartPanels.debt.position}
              size={chartPanels.debt.size}
              onPositionChange={(pos) => updatePanelPosition('debt', pos)}
              onSizeChange={(size) => updatePanelSize('debt', size)}
              minWidth={500}
              minHeight={350}
            >
              <Plot 
                data={debtToGdpData.chart.data} 
                layout={debtToGdpData.chart.layout} 
                style={{ width: '100%', height: '100%' }}
                useResizeHandler={true}
                  config={{ responsive: true }}
              />
            </DraggableResizablePanel>
          </div>
        )}

        {/* Dollar Index */}
        {activeSection === 'dollar' && dollarIndexData && (
          <div className="dollar-section" style={{ position: 'relative', minHeight: '600px' }}>
            <h3>Dollar Index</h3>
            <DraggableResizablePanel
              id="dollar"
              position={chartPanels.dollar.position}
              size={chartPanels.dollar.size}
              onPositionChange={(pos) => updatePanelPosition('dollar', pos)}
              onSizeChange={(size) => updatePanelSize('dollar', size)}
              minWidth={500}
              minHeight={350}
            >
              <Plot 
                data={dollarIndexData.chart.data} 
                layout={dollarIndexData.chart.layout} 
                style={{ width: '100%', height: '100%' }}
                useResizeHandler={true}
                  config={{ responsive: true }}
              />
            </DraggableResizablePanel>
          </div>
        )}

        {/* Velocity */}
        {activeSection === 'velocity' && velocityData && (
          <div className="velocity-section" style={{ position: 'relative', minHeight: '600px' }}>
            <h3>Money Velocity</h3>
            <DraggableResizablePanel
              id="velocity"
              position={chartPanels.velocity.position}
              size={chartPanels.velocity.size}
              onPositionChange={(pos) => updatePanelPosition('velocity', pos)}
              onSizeChange={(size) => updatePanelSize('velocity', size)}
              minWidth={500}
              minHeight={350}
            >
              <Plot 
                data={velocityData.chart.data} 
                layout={velocityData.chart.layout} 
                style={{ width: '100%', height: '100%' }}
                useResizeHandler={true}
                  config={{ responsive: true }}
              />
            </DraggableResizablePanel>
          </div>
        )}

        {/* Unemployment */}
        {activeSection === 'unemployment' && unemploymentData && (
          <div className="unemployment-section" style={{ position: 'relative', minHeight: '600px' }}>
            <h3>Unemployment Rate</h3>
            <DraggableResizablePanel
              id="unemployment"
              position={chartPanels.unemployment.position}
              size={chartPanels.unemployment.size}
              onPositionChange={(pos) => updatePanelPosition('unemployment', pos)}
              onSizeChange={(size) => updatePanelSize('unemployment', size)}
              minWidth={500}
              minHeight={350}
            >
              <Plot 
                data={unemploymentData.chart.data} 
                layout={unemploymentData.chart.layout} 
                style={{ width: '100%', height: '100%' }}
                useResizeHandler={true}
                  config={{ responsive: true }}
              />
            </DraggableResizablePanel>
          </div>
        )}

        {/* Real Estate */}
        {activeSection === 'realestate' && realEstateData && (
          <div className="realestate-section" style={{ position: 'relative', minHeight: '600px' }}>
            <h3>Real Estate Trends</h3>
            <DraggableResizablePanel
              id="realestate"
              position={chartPanels.realestate.position}
              size={chartPanels.realestate.size}
              onPositionChange={(pos) => updatePanelPosition('realestate', pos)}
              onSizeChange={(size) => updatePanelSize('realestate', size)}
              minWidth={500}
              minHeight={350}
            >
              <Plot 
                data={realEstateData.chart.data} 
                layout={realEstateData.chart.layout} 
                style={{ width: '100%', height: '100%' }}
                useResizeHandler={true}
                  config={{ responsive: true }}
              />
            </DraggableResizablePanel>
          </div>
        )}

        {/* Bonds */}
        {activeSection === 'bonds' && bondsData && (
          <div className="bonds-section" style={{ position: 'relative', minHeight: '1450px' }}>
            <h3>Global Bonds</h3>
            <DraggableResizablePanel
              id="bondMajor10y"
              position={chartPanels.bondMajor10y.position}
              size={chartPanels.bondMajor10y.size}
              onPositionChange={(pos) => updatePanelPosition('bondMajor10y', pos)}
              onSizeChange={(size) => updatePanelSize('bondMajor10y', size)}
              minWidth={400}
              minHeight={300}
            >
              <div className="macro-chart" style={{ height: '100%' }}>
                <h4>Major 10Y Bonds</h4>
                <Plot 
                  data={bondsData.major_10y.data} 
                  layout={bondsData.major_10y.layout} 
                  style={{ width: '100%', height: 'calc(100% - 40px)' }}
                  useResizeHandler={true}
                  config={{ responsive: true }}
                />
              </div>
            </DraggableResizablePanel>
            
            <DraggableResizablePanel
              id="bondEurope"
              position={chartPanels.bondEurope.position}
              size={chartPanels.bondEurope.size}
              onPositionChange={(pos) => updatePanelPosition('bondEurope', pos)}
              onSizeChange={(size) => updatePanelSize('bondEurope', size)}
              minWidth={400}
              minHeight={300}
            >
              <div className="macro-chart" style={{ height: '100%' }}>
                <h4>Europe Bonds</h4>
                <Plot 
                  data={bondsData.europe.data} 
                  layout={bondsData.europe.layout} 
                  style={{ width: '100%', height: 'calc(100% - 40px)' }}
                  useResizeHandler={true}
                  config={{ responsive: true }}
                />
              </div>
            </DraggableResizablePanel>
            
            <DraggableResizablePanel
              id="bondAmerica"
              position={chartPanels.bondAmerica.position}
              size={chartPanels.bondAmerica.size}
              onPositionChange={(pos) => updatePanelPosition('bondAmerica', pos)}
              onSizeChange={(size) => updatePanelSize('bondAmerica', size)}
              minWidth={400}
              minHeight={300}
            >
              <div className="macro-chart" style={{ height: '100%' }}>
                <h4>America Bonds</h4>
                <Plot 
                  data={bondsData.america.data} 
                  layout={bondsData.america.layout} 
                  style={{ width: '100%', height: 'calc(100% - 40px)' }}
                  useResizeHandler={true}
                  config={{ responsive: true }}
                />
              </div>
            </DraggableResizablePanel>
            
            <DraggableResizablePanel
              id="bondAsia"
              position={chartPanels.bondAsia.position}
              size={chartPanels.bondAsia.size}
              onPositionChange={(pos) => updatePanelPosition('bondAsia', pos)}
              onSizeChange={(size) => updatePanelSize('bondAsia', size)}
              minWidth={400}
              minHeight={300}
            >
              <div className="macro-chart" style={{ height: '100%' }}>
                <h4>Asia Bonds</h4>
                <Plot 
                  data={bondsData.asia.data} 
                  layout={bondsData.asia.layout} 
                  style={{ width: '100%', height: 'calc(100% - 40px)' }}
                  useResizeHandler={true}
                  config={{ responsive: true }}
                />
              </div>
            </DraggableResizablePanel>
            
            <DraggableResizablePanel
              id="bondAustralia"
              position={chartPanels.bondAustralia.position}
              size={chartPanels.bondAustralia.size}
              onPositionChange={(pos) => updatePanelPosition('bondAustralia', pos)}
              onSizeChange={(size) => updatePanelSize('bondAustralia', size)}
              minWidth={400}
              minHeight={300}
            >
              <div className="macro-chart" style={{ height: '100%' }}>
                <h4>Australia Bonds</h4>
                <Plot 
                  data={bondsData.australia.data} 
                  layout={bondsData.australia.layout} 
                  style={{ width: '100%', height: 'calc(100% - 40px)' }}
                  useResizeHandler={true}
                  config={{ responsive: true }}
                />
              </div>
            </DraggableResizablePanel>
            
            <DraggableResizablePanel
              id="bondAfrica"
              position={chartPanels.bondAfrica.position}
              size={chartPanels.bondAfrica.size}
              onPositionChange={(pos) => updatePanelPosition('bondAfrica', pos)}
              onSizeChange={(size) => updatePanelSize('bondAfrica', size)}
              minWidth={400}
              minHeight={300}
            >
              <div className="macro-chart" style={{ height: '100%' }}>
                <h4>Africa Bonds</h4>
                <Plot 
                  data={bondsData.africa.data} 
                  layout={bondsData.africa.layout} 
                  style={{ width: '100%', height: 'calc(100% - 40px)' }}
                  useResizeHandler={true}
                  config={{ responsive: true }}
                />
              </div>
            </DraggableResizablePanel>
          </div>
        )}

        {/* Yield Curve / Interest Rates */}
        {activeSection === 'yield-curve' && yieldCurveData && (
          <div className="yield-curve-section" style={{ position: 'relative', minHeight: '600px' }}>
            <h3>📊 US Treasury Yield Curve</h3>
            <p className="section-description">
              The yield curve shows the relationship between interest rates and different maturity periods for US Treasury securities.
              An inverted yield curve (short-term rates higher than long-term) often signals economic uncertainty.
            </p>
            <DraggableResizablePanel
              id="yieldCurve"
              position={chartPanels.yieldCurve.position}
              size={chartPanels.yieldCurve.size}
              onPositionChange={(pos) => updatePanelPosition('yieldCurve', pos)}
              onSizeChange={(size) => updatePanelSize('yieldCurve', size)}
              minWidth={500}
              minHeight={350}
            >
              <div className="macro-chart" style={{ height: '100%' }}>
                <Plot 
                  data={yieldCurveData.chart.data} 
                  layout={yieldCurveData.chart.layout} 
                  style={{ width: '100%', height: '100%' }}
                  useResizeHandler={true}
                  config={{ responsive: true }}
                />
              </div>
            </DraggableResizablePanel>
          </div>
        )}
      </div>
    </div>
  );
}

export default MacroView;
