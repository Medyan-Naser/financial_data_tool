import React, { useState } from 'react';

function TickerSearch({ tickers, onSelect, selectedTicker }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [showDropdown, setShowDropdown] = useState(false);

  const filteredTickers = tickers.filter(ticker =>
    ticker.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleSelect = (ticker) => {
    onSelect(ticker);
    setSearchTerm(ticker);
    setShowDropdown(false);
  };

  return (
    <div className="ticker-search">
      <input
        type="text"
        placeholder="Search for a ticker (e.g., AAPL, AMZN)..."
        value={searchTerm}
        onChange={(e) => {
          setSearchTerm(e.target.value);
          setShowDropdown(true);
        }}
        onFocus={() => setShowDropdown(true)}
        className="search-input"
      />
      {showDropdown && searchTerm && filteredTickers.length > 0 && (
        <div className="dropdown">
          {filteredTickers.slice(0, 10).map(ticker => (
            <div
              key={ticker}
              className="dropdown-item"
              onClick={() => handleSelect(ticker)}
            >
              {ticker}
            </div>
          ))}
        </div>
      )}
      {selectedTicker && (
        <div className="selected-ticker">
          Selected: <strong>{selectedTicker}</strong>
        </div>
      )}
    </div>
  );
}

export default TickerSearch;
