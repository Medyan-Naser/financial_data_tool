import React, { useState } from "react";
import Select from "react-select";
import { Line, Bar } from "react-chartjs-2";
import { Chart, CategoryScale, LinearScale, LineElement, PointElement, Title, Tooltip, Legend } from 'chart.js'; // Import necessary parts of Chart.js

// Register necessary components for Chart.js
Chart.register(CategoryScale, LinearScale, LineElement, PointElement, Title, Tooltip, Legend);

const GraphSection = ({ financialData }) => {
  const [selectedItems, setSelectedItems] = useState([]);
  const [graphType, setGraphType] = useState("Line");
  const [graphData, setGraphData] = useState(null);

  const financialOptions = financialData.index.map((item) => ({
    value: item,
    label: item,
  }));

  const handleGraphTypeChange = (e) => setGraphType(e.target.value);

  const plotGraph = () => {
    if (!selectedItems.length || !financialData) return;

    const datasets = selectedItems.map(({ value }) => {
      const index = financialData.index.indexOf(value);
      return {
        label: value,
        data: financialData.data[index],
        borderColor: `rgba(${Math.floor(Math.random() * 255)}, 
                             ${Math.floor(Math.random() * 255)}, 
                             ${Math.floor(Math.random() * 255)}, 1)`,
        fill: false,
      };
    });

    setGraphData({
      labels: financialData.columns,
      datasets,
    });
  };

  return (
    <div style={{ width: "50%", padding: "10px" }}>
      <h2>Graph</h2>
      <div style={{ marginBottom: "10px" }}>
        <label htmlFor="graphType">Graph Type:</label>
        <select
          id="graphType"
          value={graphType}
          onChange={handleGraphTypeChange}
          style={{ marginLeft: "10px" }}
        >
          <option value="Line">Line</option>
          <option value="Bar">Bar</option>
        </select>
      </div>
      <div>
        <Select
          options={financialOptions}
          isMulti
          onChange={(selected) => setSelectedItems(selected)}
          placeholder="Select financial items..."
        />
      </div>
      <button className="btn btn-primary mt-3" onClick={plotGraph}>
        Plot Graph
      </button>
      <div style={{ marginTop: "20px", height: "70%" }}>
        {graphData && graphType === "Line" && <Line data={graphData} />}
        {graphData && graphType === "Bar" && <Bar data={graphData} />}
      </div>
    </div>
  );
};

export default GraphSection;
