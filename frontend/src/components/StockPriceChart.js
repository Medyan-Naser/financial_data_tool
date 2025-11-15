import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import './StockPriceChart.css';

const API_BASE_URL = 'http://localhost:8000';

function StockPriceChart({ ticker }) {
  const [priceData, setPriceData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [period, setPeriod] = useState('max');
  const [chartType, setChartType] = useState('area'); // 'line' or 'area'

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

  // Prepare data for chart
  const prepareChartData = () => {
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
  };

  const chartData = prepareChartData();

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
            <AreaChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
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
              />
              <YAxis
                tickFormatter={formatYAxis}
                stroke="#999"
                style={{ fontSize: '12px' }}
              />
              <Tooltip content={<CustomTooltip />} />
              <Area
                type="monotone"
                dataKey="close"
                stroke="#2196F3"
                strokeWidth={2}
                fillOpacity={1}
                fill="url(#colorPrice)"
              />
            </AreaChart>
          ) : (
            <LineChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#444" />
              <XAxis
                dataKey="date"
                tickFormatter={formatXAxis}
                stroke="#999"
                style={{ fontSize: '12px' }}
              />
              <YAxis
                tickFormatter={formatYAxis}
                stroke="#999"
                style={{ fontSize: '12px' }}
              />
              <Tooltip content={<CustomTooltip />} />
              <Line
                type="monotone"
                dataKey="close"
                stroke="#2196F3"
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 6 }}
              />
            </LineChart>
          )}
        </ResponsiveContainer>
      </div>

      {/* Data summary */}
      <div className="chart-footer">
        <span>Data points: {chartData.length}</span>
        <span>Range: {priceData.historical.start_date} to {priceData.historical.end_date}</span>
        <span>Currency: {priceData.historical.currency}</span>
      </div>
    </div>
  );
}

export default StockPriceChart;
