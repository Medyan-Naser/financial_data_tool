import React, { useState } from 'react';
import MultiSelectDropdown from './MultiSelectDropdown';

function FinancialTable({ data, statementType, ticker, onAddChart }) {
  const [selectedRows, setSelectedRows] = useState([]);
  const [chartType, setChartType] = useState('line');
  const [showChartBuilder, setShowChartBuilder] = useState(false);
  const [comparisonTicker, setComparisonTicker] = useState('');
  const [analysisMode, setAnalysisMode] = useState('absolute'); // absolute, growth, ratio
  const [viewMode, setViewMode] = useState('clean'); // 'clean' or 'raw'

  // Choose data based on view mode
  const hasRawData = data.raw_data && data.raw_row_names;
  const displayColumns = data.columns;
  const displayRowNames = viewMode === 'raw' && hasRawData ? data.raw_row_names : data.row_names;
  const displayData = viewMode === 'raw' && hasRawData ? data.raw_data : data.data;

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
        {/* View Mode Toggle */}
        <div className="view-toggle">
          <button 
            className={`toggle-btn ${viewMode === 'clean' ? 'active' : ''}`}
            onClick={() => setViewMode('clean')}
          >
            📊 Clean View
          </button>
          <button 
            className={`toggle-btn ${viewMode === 'raw' ? 'active' : ''}`}
            onClick={() => setViewMode('raw')}
            disabled={!hasRawData}
            title={hasRawData ? 'Show all original rows from SEC filing' : 'Raw data not available'}
          >
            🔍 Raw View (Debug)
          </button>
          {viewMode === 'raw' && hasRawData && (
            <span className="row-count">
              {data.raw_row_count || data.raw_row_names.length} rows
            </span>
          )}
        </div>
        
        <button 
          className="btn-create-chart"
          onClick={() => setShowChartBuilder(!showChartBuilder)}
          disabled={viewMode === 'raw'}
          title={viewMode === 'raw' ? 'Charts only available in Clean View' : ''}
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

      {viewMode === 'raw' && (
        <div className="raw-view-info">
          ℹ️ Raw View shows all original rows from the SEC filing with human-readable labels.
          Use this for debugging and validation. Switch to Clean View for mapped/standardized data.
        </div>
      )}

      <div className="table-wrapper">
        <table className={`financial-table ${viewMode === 'raw' ? 'raw-view' : ''}`}>
          <thead>
            <tr>
              <th className="row-name-col">Metric</th>
              {displayColumns.map((col, idx) => (
                <th key={idx}>{col}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {displayRowNames.map((rowName, rowIndex) => (
              <tr 
                key={rowIndex}
                className={selectedRows.includes(rowIndex) && viewMode === 'clean' ? 'row-selected' : ''}
              >
                <td className={`row-name-col ${viewMode === 'raw' ? 'raw-label' : ''}`} title={rowName}>
                  {rowName}
                </td>
                {displayData[rowIndex].map((value, colIndex) => (
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
