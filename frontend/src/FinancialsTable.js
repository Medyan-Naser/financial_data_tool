import React from 'react';

const FinancialsTable = ({ tableData }) => {
  if (!tableData) return <p>No data available.</p>;

  return (
    <table className="financial-table">
      <thead>
        <tr>
          <th>Financial Item</th>
          {tableData.columns.map((column, index) => (
            <th key={index}>{column}</th>
          ))}
        </tr>
      </thead>
      <tbody>
        {tableData.index.map((item, index) => (
          <tr key={index}>
            <td>{item}</td>
            {tableData.data[index].map((value, colIndex) => (
              <td key={colIndex}>{value}</td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
};

export default FinancialsTable;
