import React from 'react';

const Navbar = ({ activeTab, onTabChange }) => {
  return (
    <nav className="navbar">
      <button onClick={() => onTabChange("balance_sheet")} className={activeTab === "balance_sheet" ? 'active' : ''}>
        Balance Sheet
      </button>
      <button onClick={() => onTabChange("income_statement")} className={activeTab === "income_statement" ? 'active' : ''}>
        Income Statement
      </button>
    </nav>
  );
};

export default Navbar;
