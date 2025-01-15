import React, { useState } from 'react';

const SearchBar = ({ onSearch }) => {
  const [ticker, setTicker] = useState('');

  const handleSearch = () => {
    if (ticker) {
      onSearch(ticker);
    }
  };

  return (
    <div className="search-bar">
      <input
        type="text"
        placeholder="Enter Stock Ticker"
        value={ticker}
        onChange={(e) => setTicker(e.target.value)}
      />
      <button onClick={handleSearch}>Search</button>
    </div>
  );
};

export default SearchBar;
