import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  LineChart, Line, BarChart, Bar, AreaChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import ResizablePanel from './ResizablePanel';
import YearRangeSlider from './YearRangeSlider';

const API_BASE_URL = 'http://localhost:8000';

function ChartManager({ charts, onRemoveChart, ticker }) {
  const [comparisonData, setComparisonData] = useState({});
  const [loadingComparison, setLoadingComparison] = useState({});
  const [yearRange, setYearRange] = useState(null);

  // Fetch comparison data when needed
  useEffect(() => {
    charts.forEach(async (chart) => {
      if (chart.comparisonTicker && !comparisonData[chart.id]) {
        setLoadingComparison(prev => ({ ...prev, [chart.id]: true }));
        
        // Parse comma-separated tickers
        const tickers = chart.comparisonTicker.split(',').map(t => t.trim()).filter(t => t);
        
        try {
          // Fetch data for all tickers
          const responses = await Promise.all(
            tickers.map(ticker => 
              axios.get(`${API_BASE_URL}/api/financials/${ticker}/${chart.statementType}`)
                .catch(err => {
                  console.error(`Error fetching data for ${ticker}:`, err);
                  return null;
                })
            )
          );
          
          // Create a map of ticker -> data
          const tickerDataMap = {};
          responses.forEach((response, index) => {
            if (response && response.data) {
              tickerDataMap[tickers[index]] = response.data;
            }
          });
          
          setComparisonData(prev => ({
            ...prev,
            [chart.id]: tickerDataMap
          }));
        } catch (error) {
          console.error(`Error fetching comparison data:`, error);
          setComparisonData(prev => ({
            ...prev,
            [chart.id]: null // Mark as failed
          }));
        } finally {
          setLoadingComparison(prev => ({ ...prev, [chart.id]: false }));
        }
      }
    });
  }, [charts]);
  // Extract available years from chart columns
  const getAvailableYears = (chart) => {
    if (!chart || !chart.columns) return [];
    return chart.columns.map(col => new Date(col).getFullYear())
      .filter((year, index, self) => self.indexOf(year) === index)
      .sort((a, b) => a - b);
  };

  // Initialize year range when chart changes
  useEffect(() => {
    if (charts.length > 0) {
      const chart = charts[0];
      const years = getAvailableYears(chart);
      if (years.length > 0 && !yearRange) {
        setYearRange([years[0], years[years.length - 1]]);
      }
    }
  }, [charts]);

  // Filter columns by year range
  const filterColumnsByYearRange = (columns) => {
    if (!yearRange || !columns) return { filteredColumns: columns, filteredIndices: columns.map((_, i) => i) };
    
    const [startYear, endYear] = yearRange;
    const filteredIndices = [];
    const filteredColumns = [];
    
    columns.forEach((col, idx) => {
      const year = new Date(col).getFullYear();
      if (year >= startYear && year <= endYear) {
        filteredIndices.push(idx);
        filteredColumns.push(col);
      }
    });
    
    return { filteredColumns, filteredIndices };
  };

  const formatChartData = (chart) => {
    const { data, columns, comparisonTicker, selectedRowNames } = chart;
    const comparison = comparisonData[chart.id];
    
    // Filter columns by year range
    const { filteredColumns, filteredIndices } = filterColumnsByYearRange(columns);
    
    // Transform data to format needed by recharts
    const chartData = filteredColumns.map((col, filteredIndex) => {
      const colIndex = filteredIndices[filteredIndex];
      const point = { date: col };
      
      // Add primary ticker data (use original colIndex from unfiltered data)
      data.forEach(row => {
        point[`${chart.ticker}: ${row.name}`] = parseFloat(row.values[colIndex]) || 0;
      });
      
      // Add comparison ticker(s) data if available
      if (comparison && typeof comparison === 'object') {
        // Handle multiple tickers (comparison is now a map)
        Object.keys(comparison).forEach(compTicker => {
          const compData = comparison[compTicker];
          if (compData && compData.available) {
            selectedRowNames.forEach(rowName => {
              const rowIndex = compData.row_names.indexOf(rowName);
              if (rowIndex !== -1) {
                const compValue = compData.data[rowIndex]?.[colIndex];
                point[`${compTicker}: ${rowName}`] = parseFloat(compValue) || 0;
              }
            });
          }
        });
      }
      
      return point;
    });
    
    return chartData;
  };

  const getRandomColor = (index) => {
    const colors = [
      '#8884d8', '#82ca9d', '#ffc658', '#ff7c7c', '#a4de6c',
      '#d084d0', '#8dd1e1', '#ffbb28', '#ff8042', '#00C49F'
    ];
    return colors[index % colors.length];
  };

  const getYAxisDomain = (chartData) => {
    if (!chartData || chartData.length === 0) return ['auto', 'auto'];
    
    let min = Infinity;
    let max = -Infinity;
    
    chartData.forEach(point => {
      Object.keys(point).forEach(key => {
        if (key !== 'date') {
          const value = parseFloat(point[key]);
          if (!isNaN(value)) {
            min = Math.min(min, value);
            max = Math.max(max, value);
          }
        }
      });
    });
    
    // Add 10% padding to the range
    const padding = (max - min) * 0.1;
    return [Math.floor(min - padding), Math.ceil(max + padding)];
  };

  const getAllSeriesKeys = (chart) => {
    const chartData = formatChartData(chart);
    if (chartData.length === 0) return [];
    
    const keys = Object.keys(chartData[0]).filter(key => key !== 'date');
    return keys;
  };

  const renderChart = (chart) => {
    const chartData = formatChartData(chart);
    const yDomain = getYAxisDomain(chartData);
    const seriesKeys = getAllSeriesKeys(chart);
    const commonProps = {
      width: '100%',
      height: '100%'
    };

    switch (chart.type) {
      case 'bar':
        return (
          <ResponsiveContainer {...commonProps}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" angle={-45} textAnchor="end" height={80} />
              <YAxis domain={yDomain} tickFormatter={(value) => formatValue(value)} />
              <Tooltip formatter={(value) => formatValue(value)} />
              <Legend wrapperStyle={{ paddingTop: '10px' }} />
              {seriesKeys.map((key, idx) => (
                <Bar
                  key={key}
                  dataKey={key}
                  fill={getRandomColor(idx)}
                />
              ))}
            </BarChart>
          </ResponsiveContainer>
        );

      case 'area':
        return (
          <ResponsiveContainer {...commonProps}>
            <AreaChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" angle={-45} textAnchor="end" height={80} />
              <YAxis domain={yDomain} tickFormatter={(value) => formatValue(value)} />
              <Tooltip formatter={(value) => formatValue(value)} />
              <Legend wrapperStyle={{ paddingTop: '10px' }} />
              {seriesKeys.map((key, idx) => (
                <Area
                  key={key}
                  type="monotone"
                  dataKey={key}
                  stroke={getRandomColor(idx)}
                  fill={getRandomColor(idx)}
                  fillOpacity={0.6}
                />
              ))}
            </AreaChart>
          </ResponsiveContainer>
        );

      default: // line
        return (
          <ResponsiveContainer {...commonProps}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" angle={-45} textAnchor="end" height={80} />
              <YAxis domain={yDomain} tickFormatter={(value) => formatValue(value)} />
              <Tooltip formatter={(value) => formatValue(value)} />
              <Legend wrapperStyle={{ paddingTop: '10px' }} />
              {seriesKeys.map((key, idx) => (
                <Line
                  key={key}
                  type="monotone"
                  dataKey={key}
                  stroke={getRandomColor(idx)}
                  strokeWidth={2}
                  dot={false}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        );
    }
  };

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

  if (charts.length === 0) {
    return (
      <div className="chart-manager">
        <div className="no-charts">
          <p>No charts created yet. Use the Chart Builder to create visualizations.</p>
        </div>
      </div>
    );
  }

  const chart = charts[0]; // Render only the first chart (single chart mode)

  return (
    <div className="chart-card">
      <div className="chart-header">
        <h4>
          {chart.title}
          {chart.comparisonTicker && (
            <span className="comparison-badge">
              vs {chart.comparisonTicker.split(',').map(t => t.trim()).join(', ')}
            </span>
          )}
        </h4>
        <button
          className="btn-remove"
          onClick={() => onRemoveChart(chart.id)}
          title="Remove chart"
        >
          ✕
        </button>
      </div>
      <div className="chart-content">
        {loadingComparison[chart.id] ? (
          <div className="chart-loading">Loading comparison data...</div>
        ) : chart.comparisonTicker && comparisonData[chart.id] === null ? (
          <div className="chart-error">
            <p>⚠️ Could not load data for {chart.comparisonTicker}</p>
            {renderChart(chart)}
          </div>
        ) : (
          renderChart(chart)
        )}
      </div>
      {/* Year Range Slider */}
      {yearRange && (
        <div style={{ padding: '0 20px 20px 20px' }}>
          <YearRangeSlider
            years={getAvailableYears(chart)}
            selectedRange={yearRange}
            onChange={setYearRange}
          />
        </div>
      )}
      
      <div className="chart-info">
        <small>
          Type: {chart.type.charAt(0).toUpperCase() + chart.type.slice(1)} | 
          Metrics: {chart.data.length}
          {chart.comparisonTicker && comparisonData[chart.id] && (
            <span> | Comparing with {Object.keys(comparisonData[chart.id] || {}).join(', ')}</span>
          )}
        </small>
      </div>
    </div>
  );
}

export default ChartManager;
