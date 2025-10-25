import React from "react";
import "./YearRangeSlider.css";

/**
 * YearRangeSlider - A two-handled slider for selecting a year range
 * 
 * @param {Array} years - Array of available years (e.g., [2020, 2021, 2022, 2023, 2024])
 * @param {Array} selectedRange - Current selected range [startYear, endYear]
 * @param {Function} onChange - Callback when range changes: (newRange) => {}
 */
const YearRangeSlider = ({ years, selectedRange, onChange }) => {
  if (!years || years.length === 0) {
    return null;
  }

  // Sort years in ascending order
  const sortedYears = [...years].sort((a, b) => a - b);
  const minYear = sortedYears[0];
  const maxYear = sortedYears[sortedYears.length - 1];

  // Current selection
  const [start, end] = selectedRange || [minYear, maxYear];

  // Convert year to slider position (0-100)
  const yearToPosition = (year) => {
    if (maxYear === minYear) return 50;
    return ((year - minYear) / (maxYear - minYear)) * 100;
  };

  // Convert slider position to year
  const positionToYear = (position) => {
    const yearFloat = minYear + (position / 100) * (maxYear - minYear);
    // Snap to nearest available year
    return sortedYears.reduce((prev, curr) => 
      Math.abs(curr - yearFloat) < Math.abs(prev - yearFloat) ? curr : prev
    );
  };

  const handleStartChange = (e) => {
    const position = parseFloat(e.target.value);
    const newStart = positionToYear(position);
    
    // Ensure start doesn't exceed end
    if (newStart <= end) {
      onChange([newStart, end]);
    }
  };

  const handleEndChange = (e) => {
    const position = parseFloat(e.target.value);
    const newEnd = positionToYear(position);
    
    // Ensure end doesn't go below start
    if (newEnd >= start) {
      onChange([start, newEnd]);
    }
  };

  const handleReset = () => {
    onChange([minYear, maxYear]);
  };

  const startPos = yearToPosition(start);
  const endPos = yearToPosition(end);

  return (
    <div className="year-range-slider">
      <div className="year-range-header">
        <span className="year-range-label">
          Year Range: <strong>{start}</strong> to <strong>{end}</strong>
        </span>
        <button 
          className="year-range-reset" 
          onClick={handleReset}
          title="Reset to show all years"
        >
          Reset
        </button>
      </div>

      <div className="slider-container">
        {/* Background track */}
        <div className="slider-track"></div>
        
        {/* Selected range highlight */}
        <div 
          className="slider-range" 
          style={{
            left: `${startPos}%`,
            width: `${endPos - startPos}%`
          }}
        ></div>

        {/* Start handle */}
        <input
          type="range"
          min="0"
          max="100"
          step="any"
          value={startPos}
          onChange={handleStartChange}
          className="slider-input slider-start"
          title={`Start year: ${start}`}
        />

        {/* End handle */}
        <input
          type="range"
          min="0"
          max="100"
          step="any"
          value={endPos}
          onChange={handleEndChange}
          className="slider-input slider-end"
          title={`End year: ${end}`}
        />

        {/* Year markers */}
        <div className="year-markers">
          <span className="year-marker year-marker-min">{minYear}</span>
          <span className="year-marker year-marker-max">{maxYear}</span>
        </div>
      </div>
    </div>
  );
};

export default YearRangeSlider;
