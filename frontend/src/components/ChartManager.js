import React from 'react';
import {
  LineChart, Line, BarChart, Bar, AreaChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';

function ChartManager({ charts, onRemoveChart, ticker }) {
  const formatChartData = (chart) => {
    const { data, columns } = chart;
    
    // Transform data to format needed by recharts
    return columns.map((col, colIndex) => {
      const point = { date: col };
      data.forEach(row => {
        point[row.name] = parseFloat(row.values[colIndex]) || 0;
      });
      return point;
    });
  };

  const getRandomColor = (index) => {
    const colors = [
      '#8884d8', '#82ca9d', '#ffc658', '#ff7c7c', '#a4de6c',
      '#d084d0', '#8dd1e1', '#ffbb28', '#ff8042', '#00C49F'
    ];
    return colors[index % colors.length];
  };

  const renderChart = (chart) => {
    const chartData = formatChartData(chart);
    const commonProps = {
      width: '100%',
      height: 300
    };

    switch (chart.type) {
      case 'bar':
        return (
          <ResponsiveContainer {...commonProps}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip formatter={(value) => formatValue(value)} />
              <Legend />
              {chart.data.map((row, idx) => (
                <Bar
                  key={row.name}
                  dataKey={row.name}
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
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip formatter={(value) => formatValue(value)} />
              <Legend />
              {chart.data.map((row, idx) => (
                <Area
                  key={row.name}
                  type="monotone"
                  dataKey={row.name}
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
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip formatter={(value) => formatValue(value)} />
              <Legend />
              {chart.data.map((row, idx) => (
                <Line
                  key={row.name}
                  type="monotone"
                  dataKey={row.name}
                  stroke={getRandomColor(idx)}
                  strokeWidth={2}
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
            <div key={chart.id} className="chart-card">
              <div className="chart-header">
                <h4>{chart.title}</h4>
                <button
                  className="btn-remove"
                  onClick={() => onRemoveChart(chart.id)}
                  title="Remove chart"
                >
                  ✕
                </button>
              </div>
              <div className="chart-content">
                {renderChart(chart)}
              </div>
              <div className="chart-info">
                <small>
                  Type: {chart.type.charAt(0).toUpperCase() + chart.type.slice(1)} | 
                  Metrics: {chart.data.length}
                </small>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default ChartManager;
