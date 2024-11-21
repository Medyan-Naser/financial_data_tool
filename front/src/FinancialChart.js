import React, { useEffect, useState } from "react";
import { getFinancialData } from "./api";

const FinancialTable = () => {
  const [financialData, setFinancialData] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      const data = await getFinancialData();
      setFinancialData(data);
    };

    fetchData();
  }, []);

  if (!financialData) return <div>Loading...</div>;

  return (
    <div>
      <h2>Financial Data Statement</h2>
      <table border="1">
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

export default FinancialTable;
