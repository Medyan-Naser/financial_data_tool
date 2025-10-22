import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Plot from 'react-plotly.js';

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

  // Fetch data only when section is active
  useEffect(() => {
    if (activeSection === 'commodities' && !commoditiesData) {
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
      setError('Error loading debt to GDP data');
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
      setError('Error loading dollar index data');
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
      setError('Error loading velocity data');
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
      setError('Error loading real estate data');
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
              <div className="overview-card">
                <h4>📊 Commodities</h4>
                <p>Energy, Metals, Agricultural, Livestock, Industrial</p>
              </div>
              <div className="overview-card">
                <h4>💱 Currencies</h4>
                <p>Major global currency exchange rates</p>
              </div>
              <div className="overview-card">
                <h4>📈 Inflation</h4>
                <p>CPI and inflation trends</p>
              </div>
              <div className="overview-card">
                <h4>💰 Debt/GDP</h4>
                <p>National debt to GDP ratio</p>
              </div>
              <div className="overview-card">
                <h4>💵 Dollar Index</h4>
                <p>US Dollar strength indicator</p>
              </div>
              <div className="overview-card">
                <h4>⚡ Money Velocity</h4>
                <p>Money circulation rate</p>
              </div>
              <div className="overview-card">
                <h4>👥 Unemployment</h4>
                <p>Employment statistics</p>
              </div>
              <div className="overview-card">
                <h4>🏠 Real Estate</h4>
                <p>Housing market trends</p>
              </div>
              <div className="overview-card">
                <h4>🌐 Bonds</h4>
                <p>Global bond yields</p>
              </div>
            </div>
          </div>
        )}

        {/* Commodities */}
        {activeSection === 'commodities' && commoditiesData && (
          <div className="commodities-section">
            <h3>Commodities Data</h3>
            <div className="charts-grid-macro">
              <div className="macro-chart">
                <h4>Energy</h4>
                <Plot data={commoditiesData.energy.chart.data} layout={commoditiesData.energy.chart.layout} />
              </div>
              <div className="macro-chart">
                <h4>Metals</h4>
                <Plot data={commoditiesData.metals.chart.data} layout={commoditiesData.metals.chart.layout} />
              </div>
              <div className="macro-chart">
                <h4>Agricultural</h4>
                <Plot data={commoditiesData.agricultural.chart.data} layout={commoditiesData.agricultural.chart.layout} />
              </div>
              <div className="macro-chart">
                <h4>Livestock</h4>
                <Plot data={commoditiesData.livestock.chart.data} layout={commoditiesData.livestock.chart.layout} />
              </div>
              <div className="macro-chart">
                <h4>Industrial</h4>
                <Plot data={commoditiesData.industrial.chart.data} layout={commoditiesData.industrial.chart.layout} />
              </div>
              <div className="macro-chart">
                <h4>Index</h4>
                <Plot data={commoditiesData.index.chart.data} layout={commoditiesData.index.chart.layout} />
              </div>
            </div>
          </div>
        )}

        {/* Currencies */}
        {activeSection === 'currencies' && currenciesData && (
          <div className="currencies-section">
            <h3>Major Currencies</h3>
            <Plot data={currenciesData.chart.data} layout={currenciesData.chart.layout} />
          </div>
        )}

        {/* Inflation */}
        {activeSection === 'inflation' && inflationData && (
          <div className="inflation-section">
            <h3>CPI Inflation</h3>
            <Plot data={inflationData.chart.data} layout={inflationData.chart.layout} />
          </div>
        )}

        {/* Debt to GDP */}
        {activeSection === 'debt' && debtToGdpData && (
          <div className="debt-section">
            <h3>Debt to GDP Ratio</h3>
            <Plot data={debtToGdpData.chart.data} layout={debtToGdpData.chart.layout} />
          </div>
        )}

        {/* Dollar Index */}
        {activeSection === 'dollar' && dollarIndexData && (
          <div className="dollar-section">
            <h3>Dollar Index</h3>
            <Plot data={dollarIndexData.chart.data} layout={dollarIndexData.chart.layout} />
          </div>
        )}

        {/* Velocity */}
        {activeSection === 'velocity' && velocityData && (
          <div className="velocity-section">
            <h3>Money Velocity</h3>
            <Plot data={velocityData.chart.data} layout={velocityData.chart.layout} />
          </div>
        )}

        {/* Unemployment */}
        {activeSection === 'unemployment' && unemploymentData && (
          <div className="unemployment-section">
            <h3>Unemployment Rate</h3>
            <Plot data={unemploymentData.chart.data} layout={unemploymentData.chart.layout} />
          </div>
        )}

        {/* Real Estate */}
        {activeSection === 'realestate' && realEstateData && (
          <div className="realestate-section">
            <h3>Real Estate Trends</h3>
            <Plot data={realEstateData.chart.data} layout={realEstateData.chart.layout} />
          </div>
        )}

        {/* Bonds */}
        {activeSection === 'bonds' && bondsData && (
          <div className="bonds-section">
            <h3>Global Bonds</h3>
            <div className="charts-grid-macro">
              <div className="macro-chart">
                <h4>Major 10Y Bonds</h4>
                <Plot data={bondsData.major_10y.data} layout={bondsData.major_10y.layout} />
              </div>
              <div className="macro-chart">
                <h4>Europe Bonds</h4>
                <Plot data={bondsData.europe.data} layout={bondsData.europe.layout} />
              </div>
              <div className="macro-chart">
                <h4>America Bonds</h4>
                <Plot data={bondsData.america.data} layout={bondsData.america.layout} />
              </div>
              <div className="macro-chart">
                <h4>Asia Bonds</h4>
                <Plot data={bondsData.asia.data} layout={bondsData.asia.layout} />
              </div>
              <div className="macro-chart">
                <h4>Australia Bonds</h4>
                <Plot data={bondsData.australia.data} layout={bondsData.australia.layout} />
              </div>
              <div className="macro-chart">
                <h4>Africa Bonds</h4>
                <Plot data={bondsData.africa.data} layout={bondsData.africa.layout} />
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default MacroView;
