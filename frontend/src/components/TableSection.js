import React from "react";

const TableSection = ({ financialData, activeTab }) => {
  const renderTableData = () => {
    // console.log("finanData:", financialData);
    if (activeTab === "income") {
      return financialData.income || { index: [], data: [], columns: [] };
    } else if (activeTab === "balance") {
      return financialData.balance || { index: [], data: [], columns: [] };
    }
    return [];
  };

  const tableData = renderTableData();
  console.log("tabledat:", tableData);

  return (
    <div className="table-section">
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr>
            <th style={{ border: '2px solid white' }}>Financial Item</th>
            {tableData.columns.map((column, index) => (
              <th key={index} style={{ border: '2px solid white' }}>
                {column}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {tableData.index.map((item, index) => (
            <tr key={index}>
              <td style={{ border: '2px solid white' }}>{item}</td>
              {tableData.data[index].map((value, colIndex) => (
                <td key={colIndex} style={{ border: '2px solid white' }}>
                  {value}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default TableSection;
