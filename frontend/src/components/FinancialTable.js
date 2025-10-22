import React, { useState } from 'react';

function FinancialTable({ data, statementType, ticker, onAddChart }) {
  const [selectedRows, setSelectedRows] = useState([]);
  const [chartType, setChartType] = useState('line');
  const [showChartBuilder, setShowChartBuilder] = useState(false);

  const { columns, row_names, data: tableData } = data;

  const toggleRowSelection = (rowIndex) => {
    setSelectedRows(prev =>
      prev.includes(rowIndex)
        ? prev.filter(i => i !== rowIndex)
        : [...prev, rowIndex]
    );
  };

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
      title: `${ticker} - ${statementType.replace('_', ' ').toUpperCase()}`
    });

    // Reset selections
    setSelectedRows([]);
    setShowChartBuilder(false);
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
            <label>
              Chart Type:
              <select 
                value={chartType} 
                onChange={(e) => setChartType(e.target.value)}
                className="chart-type-select"
              >
                <option value="line">Line Chart</option>
                <option value="bar">Bar Chart</option>
                <option value="area">Area Chart</option>
              </select>
            </label>
            <button 
              className="btn-add-chart"
              onClick={handleCreateChart}
              disabled={selectedRows.length === 0}
            >
              Add Chart ({selectedRows.length} rows selected)
            </button>
          </div>
          <p className="hint">Select rows from the table below to include in your chart</p>
        </div>
      )}

      <div className="table-wrapper">
        <table className="financial-table">
          <thead>
            <tr>
              {showChartBuilder && <th className="checkbox-col">Select</th>}
              <th className="row-name-col">Metric</th>
              {columns.map((col, idx) => (
                <th key={idx}>{col}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {row_names.map((rowName, rowIndex) => (
              <tr key={rowIndex}>
                {showChartBuilder && (
                  <td className="checkbox-col">
                    <input
                      type="checkbox"
                      checked={selectedRows.includes(rowIndex)}
                      onChange={() => toggleRowSelection(rowIndex)}
                    />
                  </td>
                )}
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
