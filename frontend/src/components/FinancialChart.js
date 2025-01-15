import React, { useEffect, useState } from "react";
import { getFinancialData } from "../api";
import GraphSection from "./GraphSection";
import TableSection from "./TableSection";
import "./FinancialChart.css";

const FinancialChart = ({ ticker }) => {
  const [financialData, setFinancialData] = useState(null);
  const [dividerPosition, setDividerPosition] = useState(50); // Initial 50/50 split
  const [activeTab, setActiveTab] = useState("income"); // Track the active tab ("income" or "balance")

  const handleDrag = (e) => {
    const newDividerPosition = (e.clientX / window.innerWidth) * 100;
    setDividerPosition(Math.min(Math.max(newDividerPosition, 10), 90)); // Limit between 10% and 90%
  };

  const toggleTab = (tab) => {
    setActiveTab(tab);
  };

  useEffect(() => {
    const fetchData = async () => {
      try {
        const data = await getFinancialData(ticker);

        const structuredData = {
          balance: data.balance_sheet || { index: [], data: [], columns: [] },
          income: data.income_statement || { index: [], data: [], columns: [] },
        };
        setFinancialData(structuredData);
      } catch (error) {
        console.error("Failed to fetch financial data", error);
      }
    };

    fetchData();
  }, [ticker]);

  if (!financialData) return <div>Loading...</div>;

  return (
    <div className="container">
      {/* Tab Buttons */}
      <div className="tab-buttons">
        <button
          onClick={() => toggleTab("income")}
          className={activeTab === "income" ? "active" : ""}
        >
          Income
        </button>
        <button
          onClick={() => toggleTab("balance")}
          className={activeTab === "balance" ? "active" : ""}
        >
          Balance
        </button>
      </div>

      {/* Content Section */}
      <div className="content">
        {/* Table Section */}
        <div
          className="resizable-section table-section"
          style={{ width: `${dividerPosition}%` }}
        >
          <TableSection
            financialData={financialData}
            activeTab={activeTab}
          />
        </div>

        {/* Draggable Divider */}
        <div
          className="divider"
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
          className="resizable-section graph-section"
          style={{ width: `${100 - dividerPosition}%` }}
        >
          <GraphSection financialData={financialData} />
        </div>
      </div>
    </div>
  );
};

export default FinancialChart;
