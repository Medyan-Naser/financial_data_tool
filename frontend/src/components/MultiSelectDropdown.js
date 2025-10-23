import React, { useState, useRef, useEffect } from 'react';

function MultiSelectDropdown({ options, selected, onChange, placeholder = "Select options..." }) {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const toggleOption = (value) => {
    const newSelected = selected.includes(value)
      ? selected.filter(v => v !== value)
      : [...selected, value];
    onChange(newSelected);
  };

  const clearAll = () => {
    onChange([]);
  };

  return (
    <div className="multi-select-dropdown" ref={dropdownRef}>
      <div 
        className="multi-select-header" 
        onClick={() => setIsOpen(!isOpen)}
      >
        <span className="multi-select-text">
          {selected.length === 0 
            ? placeholder 
            : `${selected.length} selected`}
        </span>
        <span className="multi-select-arrow">{isOpen ? '▲' : '▼'}</span>
      </div>
      
      {isOpen && (
        <div className="multi-select-options">
          <div className="multi-select-actions">
            <button 
              onClick={(e) => {
                e.stopPropagation();
                clearAll();
              }}
              className="btn-clear-all"
            >
              Clear All
            </button>
            <span className="selected-count">{selected.length} selected</span>
          </div>
          
          <div className="multi-select-list">
            {options.map((option, idx) => (
              <label 
                key={idx} 
                className="multi-select-option"
                onClick={(e) => e.stopPropagation()}
              >
                <input
                  type="checkbox"
                  checked={selected.includes(idx)}
                  onChange={() => toggleOption(idx)}
                />
                <span className="option-label">{option}</span>
              </label>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default MultiSelectDropdown;
