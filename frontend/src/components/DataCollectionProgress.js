import React from 'react';
import './DataCollectionProgress.css';

/**
 * Progress indicator for financial data collection
 */
const DataCollectionProgress = ({ status, message, progress }) => {
  const getStatusIcon = () => {
    switch (status) {
      case 'cached':
        return '💾';
      case 'starting':
        return '🚀';
      case 'collecting':
        return '📥';
      case 'processing':
        return '⚙️';
      case 'saving':
        return '💾';
      case 'complete':
        return '✅';
      case 'error':
        return '❌';
      default:
        return '⏳';
    }
  };

  const getStatusColor = () => {
    switch (status) {
      case 'complete':
        return '#4caf50';
      case 'error':
        return '#f44336';
      case 'cached':
        return '#2196f3';
      default:
        return '#ff9800';
    }
  };

  return (
    <div className="data-collection-progress">
      <div className="progress-header">
        <span className="progress-icon">{getStatusIcon()}</span>
        <h3 className="progress-title">
          {status === 'cached' && 'Loading from Cache'}
          {status === 'starting' && 'Initializing Data Collection'}
          {status === 'collecting' && 'Collecting Financial Data'}
          {status === 'processing' && 'Processing Data'}
          {status === 'saving' && 'Saving to Cache'}
          {status === 'complete' && 'Complete!'}
          {status === 'error' && 'Error'}
        </h3>
      </div>

      <div className="progress-message">{message}</div>

      <div className="progress-bar-container">
        <div
          className="progress-bar-fill"
          style={{
            width: `${progress || 0}%`,
            backgroundColor: getStatusColor()
          }}
        >
          <span className="progress-text">{Math.round(progress || 0)}%</span>
        </div>
      </div>

      {status === 'collecting' && (
        <div className="progress-details">
          <p className="progress-hint">
            💡 This may take 1-3 minutes for 15 years of data...
          </p>
        </div>
      )}

      {status === 'error' && (
        <div className="progress-error">
          <p>⚠️ {message}</p>
          <p className="error-hint">
            Please check the ticker symbol and try again.
          </p>
        </div>
      )}
    </div>
  );
};

export default DataCollectionProgress;
