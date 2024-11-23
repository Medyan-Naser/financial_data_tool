import React, { useEffect, useState } from "react";
import { getFinancialData } from "../api";
import GraphSection from "./GraphSection";
import TableSection from "./TableSection";
import "./FinancialChart.css";

const FinancialChart = ({ ticker }) => {
  const [financialData, setFinancialData] = useState(null);
  const [dividerPosition, setDividerPosition] = useState(50); // Initial 50/50 split
  const [activeTab, setActiveTab] = useState("income"); // Track the active tab ("income" or "balance")
  console.log("tickerf:", ticker)
  

  const handleDrag = (e) => {
    const newDividerPosition = (e.clientX / window.innerWidth) * 100;
    setDividerPosition(Math.min(Math.max(newDividerPosition, 10), 90)); // Limit between 10% and 90%
  };

  // Toggle between "income" and "balance" tabs
  const toggleTab = (tab) => {
    setActiveTab(tab);
  };

  useEffect(() => {
    const fetchData = async () => {
      try {
        const data = await getFinancialData(ticker);

        // Assuming the API returns income and balance data
        const structuredData = {
          balance: data.balance_sheet || { index: [], data: [], columns: [] },
          income: data.income_statement || { index: [], data: [], columns: [] },
        };
        setFinancialData(structuredData); // Set the structured data
      } catch (error) {
        console.error("Failed to fetch financial data", error);
      }
    };

    fetchData();
  }, [ticker]);

  const handleTickerChange = (event) => {
    const selectedTicker = event.target.value;
    setTicker(selectedTicker);
  };
  console.log("tickerf:", ticker)
  if (!financialData) return <div>Loading...</div>;
  
  return (
    <div className="container" style={{ height: "100vh", overflow: "hidden" }}>

      {/* Tab Buttons */}
      <div className="tab-buttons" style={{ marginTop: "60px", marginBottom: "10px", textAlign: "center" }}>
        <button 
          onClick={() => toggleTab("income")} 
          style={{ padding: "10px 20px", margin: "0 10px", cursor: "pointer",color: activeTab === "income" ? "white" : "black", backgroundColor: activeTab === "income" ? "#0056b3" : "#f5f5f5" }}>
          Income
        </button>
        <button 
          onClick={() => toggleTab("balance")} 
          style={{ padding: "10px 20px", margin: "0 10px", cursor: "pointer",color: activeTab === "balance" ? "white" : "black", backgroundColor: activeTab === "balance" ? "#0056b3" : "#f5f5f5" }}>
          Balance
        </button>
      </div>

      {/* Content Section */}
      <div style={{ display: "flex", height: "calc(100vh - 60px)" }}>
        {/* Table Section */}
        <div
          className="resizable-section"
          style={{
            width: `${dividerPosition}%`,
            height: "100%",
            overflowY: "auto",
            borderRight: "1px solid #ccc",
          }}
        >
          <TableSection
            financialData={financialData}  // Pass the data
            activeTab={activeTab}           // Pass the active tab ("income" or "balance")
          />
        </div>

        {/* Draggable Divider */}
        <div
          className="divider"
          style={{
            cursor: "col-resize",
            backgroundColor: "#ccc",
            width: "10px",
            height: "100%",
          }}
          onMouseDown={(e) => {
            e.preventDefault();
            document.addEventListener("mousemove", handleDrag);
            document.addEventListener("mouseup", () => {
              document.removeEventListener("mousemove", handleDrag);
            });
          }}
        ></div>

        {/* Chart Section */}
        <div
          className="resizable-section"
          style={{
            width: `${100 - dividerPosition}%`,
            height: "100%",
            overflowY: "auto",
          }}
        >
          <GraphSection financialData={financialData} />
        </div>
      </div>
    </div>
  );
};

export default FinancialChart;
