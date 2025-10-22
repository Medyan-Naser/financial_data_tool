import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  LineChart, Line, BarChart, Bar, AreaChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import ResizablePanel from './ResizablePanel';

const API_BASE_URL = 'http://localhost:8000';

function ChartManager({ charts, onRemoveChart, ticker }) {
  const [comparisonData, setComparisonData] = useState({});
  const [loadingComparison, setLoadingComparison] = useState({});

  // Fetch comparison data when needed
  useEffect(() => {
    charts.forEach(async (chart) => {
      if (chart.comparisonTicker && !comparisonData[chart.id]) {
        setLoadingComparison(prev => ({ ...prev, [chart.id]: true }));
        try {
          const response = await axios.get(
            `${API_BASE_URL}/api/financials/${chart.comparisonTicker}/${chart.statementType}`
          );
          setComparisonData(prev => ({
            ...prev,
            [chart.id]: response.data
          }));
        } catch (error) {
          console.error(`Error fetching comparison data for ${chart.comparisonTicker}:`, error);
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
  const formatChartData = (chart) => {
    const { data, columns, comparisonTicker, selectedRowNames } = chart;
    const comparison = comparisonData[chart.id];
    
    // Transform data to format needed by recharts
    const chartData = columns.map((col, colIndex) => {
      const point = { date: col };
      
      // Add primary ticker data
      data.forEach(row => {
        point[`${chart.ticker}: ${row.name}`] = parseFloat(row.values[colIndex]) || 0;
      });
      
      // Add comparison ticker data if available
      if (comparison && comparison.available) {
        selectedRowNames.forEach(rowName => {
          const rowIndex = comparison.row_names.indexOf(rowName);
          if (rowIndex !== -1) {
            const compValue = comparison.data[rowIndex]?.[colIndex];
            point[`${comparisonTicker}: ${rowName}`] = parseFloat(compValue) || 0;
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

  return (
    <div className="chart-manager">
      <h3>📊 Charts</h3>
      {charts.length === 0 ? (
        <div className="no-charts">
          <p>No charts created yet. Use the Chart Builder to create visualizations.</p>
        </div>
      ) : (
        <div className="charts-grid">
          {charts.map((chart) => (
            <ResizablePanel 
              key={chart.id} 
              minWidth={300} 
              minHeight={250}
              defaultWidth={600}
              defaultHeight={400}
            >
              <div className="chart-card">
                <div className="chart-header">
                  <h4>
                    {chart.title}
                    {chart.comparisonTicker && (
                      <span className="comparison-badge">
                        vs {chart.comparisonTicker}
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
                <div className="chart-info">
                  <small>
                    Type: {chart.type.charAt(0).toUpperCase() + chart.type.slice(1)} | 
                    Metrics: {chart.data.length}
                    {chart.comparisonTicker && comparisonData[chart.id] && (
                      <span> | Comparing with {chart.comparisonTicker}</span>
                    )}
                  </small>
                </div>
              </div>
            </ResizablePanel>
          ))}
        </div>
      )}
    </div>
  );
}

export default ChartManager;
