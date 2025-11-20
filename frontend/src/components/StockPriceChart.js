import React, { useState, useEffect, useMemo } from 'react';
import axios from 'axios';
import {
  LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import './StockPriceChart.css';

const API_BASE_URL = 'http://localhost:8000';

const StockPriceChart = React.memo(({ ticker }) => {
  const [priceData, setPriceData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [period, setPeriod] = useState('1y');
  const [chartType, setChartType] = useState('line'); // 'line' or 'area'
  const [dataRange, setDataRange] = useState([0, 100]); // Percentage range for slider

  // Reset range when period changes
  useEffect(() => {
    setDataRange([0, 100]);
  }, [period]);

  // Fetch stock price data
  useEffect(() => {
    if (!ticker) return;

    const fetchPriceData = async () => {
      setLoading(true);
      setError(null);

      try {
        const response = await axios.get(
          `${API_BASE_URL}/api/stock-price/combined/${ticker}`,
          { params: { period } }
        );

        setPriceData(response.data);
      } catch (err) {
        console.error('Error fetching stock price:', err);
        setError(err.response?.data?.detail || 'Failed to fetch stock price data');
      } finally {
        setLoading(false);
      }
    };

    fetchPriceData();
  }, [ticker, period]);

  // Prepare data for chart (memoized for performance)
  const chartData = useMemo(() => {
    if (!priceData || !priceData.historical) return [];

    const { dates, close, open, high, low, volume } = priceData.historical;

    return dates.map((date, index) => ({
      date: date,
      close: close[index],
      open: open[index],
      high: high[index],
      low: low[index],
      volume: volume[index]
    }));
  }, [priceData]);

  // Filter data based on range slider
  const filteredChartData = useMemo(() => {
    if (!chartData || chartData.length === 0) return [];
    
    const startIndex = Math.floor((dataRange[0] / 100) * chartData.length);
    const endIndex = Math.ceil((dataRange[1] / 100) * chartData.length);
    
    return chartData.slice(startIndex, endIndex);
  }, [chartData, dataRange]);

  // Custom tooltip
  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="stock-price-tooltip">
          <p className="tooltip-date">{label}</p>
          <p className="tooltip-price">Close: ${data.close?.toFixed(2)}</p>
          <p className="tooltip-detail">Open: ${data.open?.toFixed(2)}</p>
          <p className="tooltip-detail">High: ${data.high?.toFixed(2)}</p>
          <p className="tooltip-detail">Low: ${data.low?.toFixed(2)}</p>
          <p className="tooltip-volume">Volume: {data.volume?.toLocaleString()}</p>
        </div>
      );
    }
    return null;
  };

  // Format large numbers
  const formatYAxis = (value) => {
    return `$${value.toFixed(0)}`;
  };

  // Format date for X-axis
  const formatXAxis = (dateStr) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { month: 'short', year: '2-digit' });
  };

  if (loading) {
    return (
      <div className="stock-price-chart loading">
        <div className="loading-spinner"></div>
        <p>Loading stock price data...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="stock-price-chart error">
        <p>⚠️ {error}</p>
      </div>
    );
  }

  if (!priceData || chartData.length === 0) {
    return (
      <div className="stock-price-chart no-data">
        <p>No stock price data available for {ticker}</p>
      </div>
    );
  }

  const currentPrice = priceData.quote?.current;
  const change = priceData.quote?.change;
  const changePercent = priceData.quote?.change_percent;
  const isPositive = change >= 0;

  return (
    <div className="stock-price-chart">
      {/* Header with current price and controls */}
      <div className="chart-header">
        <div className="price-info">
          <h3>{ticker} Stock Price</h3>
          <div className="current-price">
            <span className="price">${currentPrice?.toFixed(2)}</span>
            <span className={`change ${isPositive ? 'positive' : 'negative'}`}>
              {isPositive ? '+' : ''}{change?.toFixed(2)} ({changePercent?.toFixed(2)}%)
            </span>
          </div>
        </div>

        <div className="chart-controls">
          {/* Period selector */}
          <div className="period-selector">
            {['1mo', '3mo', '6mo', '1y', '2y', '5y', 'max'].map((p) => (
              <button
                key={p}
                className={`period-btn ${period === p ? 'active' : ''}`}
                onClick={() => setPeriod(p)}
              >
                {p.toUpperCase()}
              </button>
            ))}
          </div>

          {/* Chart type selector */}
          <div className="chart-type-selector">
            <button
              className={`type-btn ${chartType === 'line' ? 'active' : ''}`}
              onClick={() => setChartType('line')}
              title="Line Chart"
            >
              📈
            </button>
            <button
              className={`type-btn ${chartType === 'area' ? 'active' : ''}`}
              onClick={() => setChartType('area')}
              title="Area Chart"
            >
              📊
            </button>
          </div>
        </div>
      </div>

      {/* Chart */}
      <div className="chart-container">
        <ResponsiveContainer width="100%" height={400}>
          {chartType === 'area' ? (
            <AreaChart data={filteredChartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#2196F3" stopOpacity={0.8} />
                  <stop offset="95%" stopColor="#2196F3" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#444" />
              <XAxis
                dataKey="date"
                tickFormatter={formatXAxis}
                stroke="#999"
                style={{ fontSize: '12px' }}
                minTickGap={50}
              />
              <YAxis
                tickFormatter={formatYAxis}
                stroke="#999"
                style={{ fontSize: '12px' }}
                width={60}
              />
              <Tooltip content={<CustomTooltip />} />
              <Area
                type="monotone"
                dataKey="close"
                stroke="#2196F3"
                strokeWidth={2}
                fillOpacity={1}
                fill="url(#colorPrice)"
                isAnimationActive={false}
              />
            </AreaChart>
          ) : (
            <LineChart data={filteredChartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#444" />
              <XAxis
                dataKey="date"
                tickFormatter={formatXAxis}
                stroke="#999"
                style={{ fontSize: '12px' }}
                minTickGap={50}
              />
              <YAxis
                tickFormatter={formatYAxis}
                stroke="#999"
                style={{ fontSize: '12px' }}
                width={60}
              />
              <Tooltip content={<CustomTooltip />} />
              <Line
                type="monotone"
                dataKey="close"
                stroke="#2196F3"
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 6 }}
                isAnimationActive={false}
              />
            </LineChart>
          )}
        </ResponsiveContainer>
      </div>

      {/* Time Range Slider - Below Chart */}
      {chartData && chartData.length > 0 && (
        <div className="range-slider-container">
          <div className="range-label">
            <span>Zoom: {Math.round(dataRange[0])}% - {Math.round(dataRange[1])}% of data</span>
            <button 
              className="reset-range-btn"
              onClick={() => setDataRange([0, 100])}
              disabled={dataRange[0] === 0 && dataRange[1] === 100}
            >
              Reset Zoom
            </button>
          </div>
          <div className="dual-range-slider">
            <input
              type="range"
              min="0"
              max="100"
              value={dataRange[0]}
              onChange={(e) => {
                const newStart = parseInt(e.target.value);
                if (newStart < dataRange[1]) {
                  setDataRange([newStart, dataRange[1]]);
                }
              }}
              className="range-slider range-start"
            />
            <input
              type="range"
              min="0"
              max="100"
              value={dataRange[1]}
              onChange={(e) => {
                const newEnd = parseInt(e.target.value);
                if (newEnd > dataRange[0]) {
                  setDataRange([dataRange[0], newEnd]);
                }
              }}
              className="range-slider range-end"
            />
            <div className="slider-track">
              <div 
                className="slider-range" 
                style={{
                  left: `${dataRange[0]}%`,
                  width: `${dataRange[1] - dataRange[0]}%`
                }}
              />
            </div>
          </div>
        </div>
      )}

      {/* Data summary */}
      <div className="chart-footer">
        <span>Data points: {filteredChartData.length} of {chartData.length}</span>
        <span>Range: {priceData.historical.start_date} to {priceData.historical.end_date}</span>
        <span>Currency: {priceData.historical.currency}</span>
      </div>
    </div>
  );
});

export default StockPriceChart;
