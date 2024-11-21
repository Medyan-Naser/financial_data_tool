import React, { useEffect, useState } from "react";
import { getFinancialData } from "./api";
import GraphSection from "./GraphSection";
import TableSection from "./TableSection";

const FinancialTable = () => {
  const [financialData, setFinancialData] = useState(null);
  const [ticker, setTicker] = useState("AAPL");

  useEffect(() => {
    const fetchData = async () => {
      try {
        const data = await getFinancialData(ticker);
        setFinancialData(data);
      } catch (error) {
        console.error("Failed to fetch financial data", error);
      }
    };

    fetchData();
  }, [ticker]);

  if (!financialData) return <div>Loading...</div>;

  return (
    <div className="container" style={{ display: "flex", height: "80vh" }}>
      <TableSection
        financialData={financialData}
        ticker={ticker}
        setTicker={setTicker}
      />
      <GraphSection financialData={financialData} />
    </div>
  );
};

export default FinancialTable;
