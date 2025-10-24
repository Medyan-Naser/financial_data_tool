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

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && searchTerm) {
      // If Enter is pressed, trigger search for the typed ticker
      // This allows searching for tickers not in the autocomplete list
      handleSelect(searchTerm.toUpperCase());
    }
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
        onKeyPress={handleKeyPress}
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
