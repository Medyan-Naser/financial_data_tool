import React from "react";

const TableSection = ({ financialData, ticker, setTicker }) => {
  return (
    <div
      style={{
        width: "50%",
        overflow: "auto",
        borderRight: "1px solid #ccc",
        padding: "10px",
      }}
    >
      <h2>Financial Data Statement</h2>
      <div>
        <label htmlFor="ticker">Ticker:</label>
        <input
          id="ticker"
          type="text"
          value={ticker}
          onChange={(e) => setTicker(e.target.value.toUpperCase())}
          placeholder="Enter stock ticker"
        />
      </div>
      <table
        className="table"
        style={{
          width: "100%",
          borderCollapse: "collapse",
        }}
      >
        <thead>
          <tr>
            <th>Financial Item</th>
            {financialData.columns.map((column, index) => (
              <th key={index}>{column}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {financialData.index.map((item, index) => (
            <tr key={index}>
              <td>{item}</td>
              {financialData.data[index].map((value, colIndex) => (
                <td key={colIndex}>{value}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default TableSection;
