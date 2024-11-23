import React, { useState } from "react";
import FinancialChart from "./components/FinancialChart";
import "./App.css";
import 'bootstrap/dist/css/bootstrap.css';
import TopBar from "./components/TopBar";

const App = () => {
  // State to hold the search term
  const [searchTerm, setSearchTerm] = useState("");

  // Function to update the search term
  const handleSearch = (term) => {
    setSearchTerm(term);
  };
  console.log("ticker:", searchTerm)
  return (
    <div className="app-container">
      {/* Navigation Bar */}
      <div className="col-12">
        <TopBar onSearch={handleSearch} />
      </div>

      {/* Main Content Section */}
      <header className="app-header text-center py-5">
        <h1 className="display-4 text-primary">Financial Dashboard</h1>
      </header>

      <main className="app-main fluid-container" >
        <div className="row justify-content-center">
          <div className="responsive-container">
            <div className="responsive-chart">
              {/* Pass search term to FinancialChart */}
              <FinancialChart ticker={searchTerm} />
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-dark text-white text-center py-3 mt-5">
        <p>© 2024 StockAnalysis. All rights reserved.</p>
      </footer>
    </div>
  );
};

export default App;
