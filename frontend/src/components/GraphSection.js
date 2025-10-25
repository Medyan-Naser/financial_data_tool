import React, { useState, useEffect } from "react";
import Select from "react-select";
import { Line, Bar } from "react-chartjs-2";
import {
  Chart,
  CategoryScale,
  LinearScale,
  LineElement,
  PointElement,
  Title,
  Tooltip,
  Legend,
} from "chart.js"; // Import necessary parts of Chart.js
import YearRangeSlider from "./YearRangeSlider";
import "./GraphSection.css"; // Import the stylesheet

// Register necessary components for Chart.js
Chart.register(CategoryScale, LinearScale, LineElement, PointElement, Title, Tooltip, Legend);

const GraphSection = ({ financialData }) => {
  const [selectedItems, setSelectedItems] = useState([]);
  const [graphType, setGraphType] = useState("Line");
  const [graphData, setGraphData] = useState(null);
  const [selectedTab, setSelectedTab] = useState("income");
  const [yearRange, setYearRange] = useState(null);

  // Ensure financialData exists and has tab1 and tab2
  const tabData = {
    income: financialData.income || { index: [], data: [], columns: [] },
    balance: financialData.balance || { index: [], data: [], columns: [] },
  };

  useEffect(() => {
    console.log("test:", tabData);
  }, [financialData]);

  const financialOptions = tabData[selectedTab].index.map((item) => ({
    value: item,
    label: item,
  }));

  const handleGraphTypeChange = (e) => setGraphType(e.target.value);

  const handleTabChange = (tab) => {
    setSelectedTab(tab);
    setSelectedItems([]); // Reset selection when tab changes
  };

  // Extract years from column dates
  const getAvailableYears = () => {
    const columns = tabData[selectedTab].columns || [];
    return columns.map(col => {
      const date = new Date(col);
      return date.getFullYear();
    }).filter((year, index, self) => self.indexOf(year) === index).sort((a, b) => a - b);
  };

  // Initialize year range when data changes
  useEffect(() => {
    const years = getAvailableYears();
    if (years.length > 0 && !yearRange) {
      setYearRange([years[0], years[years.length - 1]]);
    }
  }, [financialData, selectedTab]);

  // Filter data by year range
  const getFilteredData = () => {
    if (!yearRange) return { columns: tabData[selectedTab].columns, data: tabData[selectedTab].data };

    const columns = tabData[selectedTab].columns || [];
    const [startYear, endYear] = yearRange;

    // Find indices of columns within year range
    const filteredIndices = [];
    const filteredColumns = [];

    columns.forEach((col, idx) => {
      const year = new Date(col).getFullYear();
      if (year >= startYear && year <= endYear) {
        filteredIndices.push(idx);
        filteredColumns.push(col);
      }
    });

    // Filter data arrays
    const filteredData = tabData[selectedTab].data.map(row => 
      filteredIndices.map(idx => row[idx])
    );

    return { columns: filteredColumns, data: filteredData };
  };

  const plotGraph = () => {
    if (!selectedItems.length || !financialData) return;

    const { columns, data } = getFilteredData();

    const datasets = selectedItems.map(({ value }) => {
      const index = tabData[selectedTab].index.indexOf(value);
      return {
        label: value,
        data: data[index],
        borderColor: `rgba(${Math.floor(Math.random() * 255)}, 
                             ${Math.floor(Math.random() * 255)}, 
                             ${Math.floor(Math.random() * 255)}, 1)`,
        fill: false,
      };
    });

    setGraphData({
      labels: columns,
      datasets,
    });
  };

  // Replot when year range changes
  useEffect(() => {
    if (selectedItems.length > 0 && yearRange) {
      plotGraph();
    }
  }, [yearRange]);

  return (
    <div className="graph-section-container">
      {/* Graph type selection */}
      <div className="graph-type-selector">
        <label htmlFor="graphType">Graph Type:</label>
        <select id="graphType" value={graphType} onChange={handleGraphTypeChange}>
          <option value="Line">Line</option>
          <option value="Bar">Bar</option>
        </select>
      </div>

      {/* Select financial data */}
      <div>
        <Select
          options={financialOptions}
          isMulti
          onChange={(selected) => setSelectedItems(selected)}
          placeholder="Select financial items..."
        />
      </div>

      {/* Button to plot the graph */}
      <button className="btn-primary" onClick={plotGraph}>
        Plot Graph
      </button>

      {/* Year Range Slider */}
      {yearRange && graphData && (
        <YearRangeSlider
          years={getAvailableYears()}
          selectedRange={yearRange}
          onChange={setYearRange}
        />
      )}

      {/* Graph display */}
      <div className="graph-display">
        {graphData && graphType === "Line" && (
          <Line 
            data={graphData} 
            options={{
              scales: {
                x: { reverse: true },
              },
            }} 
          />
        )}
        {graphData && graphType === "Bar" && <Bar data={graphData} />}
      </div>
    </div>
  );
};

export default GraphSection;
