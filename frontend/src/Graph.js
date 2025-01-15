import React, { useState } from 'react';
import { Line } from 'react-chartjs-2';
import { Chart as ChartJS, Tooltip, Legend, CategoryScale, LinearScale, PointElement, LineElement, Title } from 'chart.js';
import './Graph.css'; // Import custom styles for the graph

// Register required chart components
ChartJS.register(Tooltip, Legend, CategoryScale, LinearScale, PointElement, LineElement, Title);

const Graph = ({ data, columns, balanceSheetIndex, incomeStatementIndex }) => {
  const [selectedRows, setSelectedRows] = useState([]);

  // Handle the selection of rows
  const handleRowChange = (row) => {
    if (selectedRows.includes(row)) {
      setSelectedRows(selectedRows.filter((item) => item !== row)); // Deselect the row
    } else {
      setSelectedRows([...selectedRows, row]); // Select the row
    }
  };

  // Prepare the data for the graph
  const chartData = {
    labels: columns, // X-axis labels (dates)
    datasets: selectedRows.map((row) => ({
      label: row,
      data: data[row], // Data corresponding to the selected row
      fill: false,
      borderColor: `#${Math.floor(Math.random() * 16777215).toString(16)}`, // Random color for each row
      tension: 0.1,
      pointRadius: 5, // Make points more visible
      pointHoverRadius: 7, // Increase point size on hover
    })),
  };

  // Graph options for customization (including sorting dates)
  const chartOptions = {
    responsive: true,
    plugins: {
      tooltip: {
        enabled: true,
        mode: 'nearest',
        intersect: false,
        callbacks: {
          label: function (tooltipItem) {
            return `${tooltipItem.dataset.label}: ${tooltipItem.raw}`; // Display value on hover
          },
        },
      },
      legend: {
        position: 'top',
      },
    },
    scales: {
      x: {
        beginAtZero: false,
        ticks: {
          autoSkip: true,
          maxTicksLimit: 10,
        },
      },
      y: {
        beginAtZero: false,
        ticks: {
          callback: function (value) {
            return `$${value.toLocaleString()}`; // Format values as currency
          },
        },
      },
    },
    hover: {
      mode: 'nearest',
      intersect: false,
    },
  };

  return (
    <div className="graph-container">
      {/* Balance Sheet Section */}
      <div className="section-container">
        <h3>Balance Sheet</h3>
        <div className="row-selector">
          {balanceSheetIndex.map((row, i) => (
            <div
              key={i}
              onClick={() => handleRowChange(row)}
              className={`row-item ${selectedRows.includes(row) ? 'selected' : ''}`}
            >
              {row}
            </div>
          ))}
        </div>
      </div>

      {/* Income Statement Section */}
      <div className="section-container">
        <h3>Income Statement</h3>
        <div className="row-selector">
          {incomeStatementIndex.map((row, i) => (
            <div
              key={i}
              onClick={() => handleRowChange(row)}
              className={`row-item ${selectedRows.includes(row) ? 'selected' : ''}`}
            >
              {row}
            </div>
          ))}
        </div>
      </div>

      {/* Line chart */}
      <Line data={chartData} options={chartOptions} />
    </div>
  );
};

export default Graph;
