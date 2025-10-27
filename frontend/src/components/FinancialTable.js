import React, { useState } from 'react';
import MultiSelectDropdown from './MultiSelectDropdown';

function FinancialTable({ data, statementType, ticker, onAddChart }) {
  const [selectedRows, setSelectedRows] = useState([]);
  const [chartType, setChartType] = useState('line');
  const [showChartBuilder, setShowChartBuilder] = useState(false);
  const [comparisonTicker, setComparisonTicker] = useState('');
  const [analysisMode, setAnalysisMode] = useState('absolute'); // absolute, growth, ratio

  const { columns, row_names, data: tableData } = data;

  const handleCreateChart = () => {
    if (selectedRows.length === 0) {
      alert('Please select at least one row to create a chart');
      return;
    }

    const chartData = selectedRows.map(rowIndex => ({
      name: row_names[rowIndex],
      values: tableData[rowIndex]
    }));

    onAddChart({
      type: chartType,
      data: chartData,
      columns: columns,
      title: `${ticker} - ${statementType.replace('_', ' ').toUpperCase()}`,
      ticker: ticker,
      statementType: statementType,
      selectedRowNames: selectedRows.map(idx => row_names[idx]),
      comparisonTicker: comparisonTicker || null,
      analysisMode: analysisMode
    });

    // Don't reset selections to allow creating multiple charts
  };

  const formatValue = (value) => {
    if (value === null || value === undefined || value === '') return '-';
    const num = parseFloat(value);
    if (isNaN(num)) return value;
    
    // Format large numbers
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
    <div className="financial-table-container">
      <div className="table-controls">
        <button 
          className="btn-create-chart"
          onClick={() => setShowChartBuilder(!showChartBuilder)}
        >
          {showChartBuilder ? 'Hide Chart Builder' : '📈 Create Chart'}
        </button>
      </div>

      {showChartBuilder && (
        <div className="chart-builder">
          <h3>Chart Builder</h3>
          <div className="chart-options">
            <div className="option-group">
              <label>Select Metrics:</label>
              <MultiSelectDropdown
                options={row_names}
                selected={selectedRows}
                onChange={setSelectedRows}
                placeholder="Select metrics to chart..."
              />
            </div>
            
            <div className="option-group">
              <label>Chart Type:</label>
              <select 
                value={chartType} 
                onChange={(e) => setChartType(e.target.value)}
                className="chart-type-select"
              >
                <option value="line">📈 Line Chart</option>
                <option value="bar">📊 Bar Chart</option>
                <option value="area">📉 Area Chart</option>
                <option value="stacked-bar">📚 Stacked Bar Chart</option>
                <option value="stacked-area">🌊 Stacked Area Chart</option>
                <option value="scatter">🔵 Scatter Plot</option>
                <option value="composed">🎯 Composed Chart (Line + Bar)</option>
              </select>
            </div>

            <div className="option-group">
              <label>Analysis Mode:</label>
              <select 
                value={analysisMode} 
                onChange={(e) => setAnalysisMode(e.target.value)}
                className="analysis-mode-select"
              >
                <option value="absolute">Absolute Values</option>
                <option value="growth">Year-over-Year Growth %</option>
                <option value="ratio">As % of First Metric</option>
              </select>
            </div>

            <div className="option-group">
              <label>Compare with Ticker(s) (optional):</label>
              <input
                type="text"
                placeholder="e.g., AMZN or AMZN,GOOGL,MSFT"
                value={comparisonTicker}
                onChange={(e) => setComparisonTicker(e.target.value.toUpperCase())}
                className="comparison-ticker-input"
              />
              <p className="hint">Comma-separated for multiple tickers, or leave blank</p>
            </div>
            
            <button 
              className="btn-add-chart"
              onClick={handleCreateChart}
              disabled={selectedRows.length === 0}
            >
              Add Chart ({selectedRows.length} selected)
            </button>
          </div>
        </div>
      )}

      <div className="table-wrapper">
        <table className="financial-table">
          <thead>
            <tr>
              <th className="row-name-col">Metric</th>
              {columns.map((col, idx) => (
                <th key={idx}>{col}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {row_names.map((rowName, rowIndex) => (
              <tr 
                key={rowIndex}
                className={selectedRows.includes(rowIndex) ? 'row-selected' : ''}
              >
                <td className="row-name-col" title={rowName}>
                  {rowName}
                </td>
                {tableData[rowIndex].map((value, colIndex) => (
                  <td key={colIndex} className="data-cell">
                    {formatValue(value)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default FinancialTable;
