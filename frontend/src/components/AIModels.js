import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Plot from 'react-plotly.js';
import './AIModels.css';

const API_BASE_URL = 'http://localhost:8000';

function AIModels({ ticker }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [healthScore, setHealthScore] = useState(null);
  const [bankruptcyRisk, setBankruptcyRisk] = useState(null);
  const [trends, setTrends] = useState(null);
  const [anomalies, setAnomalies] = useState(null);
  const [quarterly, setQuarterly] = useState(false);

  useEffect(() => {
    if (ticker) {
      fetchAllModels();
    }
  }, [ticker, quarterly]);

  const fetchAllModels = async () => {
    setLoading(true);
    setError(null);

    try {
      const [healthRes, riskRes, trendsRes, anomaliesRes] = await Promise.all([
        axios.get(`${API_BASE_URL}/api/ai-models/health-score/${ticker}?quarterly=${quarterly}`),
        axios.get(`${API_BASE_URL}/api/ai-models/bankruptcy-risk/${ticker}?quarterly=${quarterly}`),
        axios.get(`${API_BASE_URL}/api/ai-models/trend-analysis/${ticker}?quarterly=${quarterly}`),
        axios.get(`${API_BASE_URL}/api/ai-models/anomaly-detection/${ticker}?quarterly=${quarterly}`)
      ]);

      setHealthScore(healthRes.data);
      setBankruptcyRisk(riskRes.data);
      setTrends(trendsRes.data);
      setAnomalies(anomaliesRes.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Error loading AI models');
      console.error('Error fetching AI models:', err);
    } finally {
      setLoading(false);
    }
  };

  if (!ticker) {
    return (
      <div className="ai-models-placeholder">
        <h3>🤖 AI-Powered Financial Analysis</h3>
        <p>Enter a ticker in the AI tab to see advanced financial analysis models.</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="ai-models-loading">
        <div className="spinner"></div>
        <p>Running AI analysis for {ticker}...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="ai-models-error">
        <h3>❌ Error</h3>
        <p>{error}</p>
        <button onClick={fetchAllModels} className="retry-btn">🔄 Retry</button>
      </div>
    );
  }

  return (
    <div className="ai-models-container">
      <div className="ai-models-header">
        <h2>🤖 AI Models for {ticker}</h2>
        <div className="period-selector">
          <button
            className={`period-btn ${!quarterly ? 'active' : ''}`}
            onClick={() => setQuarterly(false)}
          >
            Annual
          </button>
          <button
            className={`period-btn ${quarterly ? 'active' : ''}`}
            onClick={() => setQuarterly(true)}
          >
            Quarterly
          </button>
        </div>
      </div>

      {/* Financial Health Score */}
      {healthScore && (
        <div className="model-card health-score-card">
          <h3>💪 Financial Health Score</h3>
          <div className="health-score-main">
            <div className="score-circle" style={{ borderColor: healthScore.color }}>
              <span className="score-number">{healthScore.total_score}</span>
              <span className="score-label">/ 100</span>
            </div>
            <div className="score-details">
              <h4 style={{ color: healthScore.color }}>{healthScore.rating}</h4>
              <p>Based on comprehensive financial metrics analysis</p>
            </div>
          </div>

          <div className="score-breakdown">
            <h4>Score Breakdown</h4>
            <div className="breakdown-bars">
              {Object.entries(healthScore.breakdown).map(([key, value]) => (
                <div key={key} className="breakdown-item">
                  <div className="breakdown-label">
                    <span>{key.charAt(0).toUpperCase() + key.slice(1)}</span>
                    <span className="breakdown-value">{value}</span>
                  </div>
                  <div className="breakdown-bar">
                    <div
                      className="breakdown-fill"
                      style={{
                        width: `${(value / 25) * 100}%`,
                        background: healthScore.color
                      }}
                    ></div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {healthScore.metrics && healthScore.metrics.revenue.length > 0 && (
            <div className="score-chart">
              <Plot
                data={[
                  {
                    x: healthScore.metrics.dates,
                    y: healthScore.metrics.revenue,
                    type: 'bar',
                    name: 'Revenue',
                    marker: { color: '#667eea' }
                  },
                  {
                    x: healthScore.metrics.dates,
                    y: healthScore.metrics.net_income,
                    type: 'bar',
                    name: 'Net Income',
                    marker: { color: '#28a745' }
                  }
                ]}
                layout={{
                  title: 'Revenue & Net Income Trend',
                  xaxis: { title: 'Period' },
                  yaxis: { title: 'Amount ($)' },
                  barmode: 'group',
                  height: 300,
                  margin: { l: 60, r: 20, t: 40, b: 60 }
                }}
                style={{ width: '100%' }}
                config={{ responsive: true }}
              />
            </div>
          )}
        </div>
      )}

      {/* Bankruptcy Risk */}
      {bankruptcyRisk && (
        <div className="model-card bankruptcy-card">
          <h3>⚠️ Bankruptcy Risk Analysis</h3>
          <div className="risk-main">
            <div className="risk-indicator" style={{ borderColor: bankruptcyRisk.color }}>
              <div className="z-score">
                <span className="z-value">{bankruptcyRisk.z_score}</span>
                <span className="z-label">Z-Score</span>
              </div>
              <div className="risk-level" style={{ color: bankruptcyRisk.color }}>
                {bankruptcyRisk.risk_level}
              </div>
              <div className="risk-probability">
                {bankruptcyRisk.bankruptcy_probability}% probability
              </div>
            </div>

            <div className="risk-explanation">
              <h4>Altman Z-Score Components</h4>
              <div className="components-list">
                {Object.entries(bankruptcyRisk.components).map(([key, value]) => (
                  <div key={key} className="component-item">
                    <span className="component-name">
                      {key.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')}
                    </span>
                    <span className="component-value">{value}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="risk-zones">
            <h4>Risk Zone Interpretation</h4>
            <div className="zone-item safe">
              <span className="zone-label">✅ Safe Zone</span>
              <span className="zone-range">Z &gt; 2.99</span>
            </div>
            <div className="zone-item grey">
              <span className="zone-label">⚠️ Grey Zone</span>
              <span className="zone-range">1.81 &lt; Z &lt; 2.99</span>
            </div>
            <div className="zone-item distress">
              <span className="zone-label">❌ Distress Zone</span>
              <span className="zone-range">Z &lt; 1.81</span>
            </div>
          </div>
        </div>
      )}

      {/* Trend Analysis */}
      {trends && (
        <div className="model-card trends-card">
          <h3>📈 Trend Analysis</h3>
          <div className="trends-grid">
            {Object.entries(trends.trends).map(([metric, trend]) => (
              <div key={metric} className="trend-item">
                <div className="trend-header">
                  <h4>{metric.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')}</h4>
                  <span className={`trend-badge ${trend.direction}`}>
                    {trend.direction === 'strong_upward' && '📈 Strong Up'}
                    {trend.direction === 'upward' && '↗️ Up'}
                    {trend.direction === 'flat' && '➡️ Flat'}
                    {trend.direction === 'downward' && '↘️ Down'}
                    {trend.direction === 'strong_downward' && '📉 Strong Down'}
                    {trend.direction === 'insufficient_data' && '❓ No Data'}
                  </span>
                </div>
                {trend.direction !== 'insufficient_data' && (
                  <>
                    <div className="trend-values">
                      <div className="value-box">
                        <span className="value-label">First</span>
                        <span className="value-number">{trend.first_value.toLocaleString()}</span>
                      </div>
                      <div className="trend-arrow">→</div>
                      <div className="value-box">
                        <span className="value-label">Latest</span>
                        <span className="value-number">{trend.last_value.toLocaleString()}</span>
                      </div>
                    </div>
                    <div className="trend-change">
                      <span className={trend.change_pct >= 0 ? 'positive' : 'negative'}>
                        {trend.change_pct >= 0 ? '+' : ''}{trend.change_pct}%
                      </span>
                    </div>
                    <div className="trend-strength">
                      <div className="strength-bar">
                        <div
                          className="strength-fill"
                          style={{ width: `${Math.min(100, trend.strength)}%` }}
                        ></div>
                      </div>
                      <span className="strength-label">Strength: {trend.strength}%</span>
                    </div>
                  </>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Anomaly Detection */}
      {anomalies && (
        <div className="model-card anomalies-card">
          <h3>🔍 Anomaly Detection</h3>
          <div className="anomalies-summary">
            <div className="summary-stat">
              <span className="stat-number">{anomalies.summary.total_anomalies}</span>
              <span className="stat-label">Total Anomalies Detected</span>
            </div>
          </div>

          {Object.entries(anomalies.anomalies).map(([metric, items]) => (
            items.length > 0 && (
              <div key={metric} className="anomaly-section">
                <h4>{metric.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')}</h4>
                <div className="anomaly-list">
                  {items.map((anomaly, idx) => (
                    <div key={idx} className={`anomaly-item ${anomaly.severity}`}>
                      <div className="anomaly-icon">
                        {anomaly.type === 'spike' ? '📈' : '📉'}
                      </div>
                      <div className="anomaly-details">
                        <div className="anomaly-date">{anomaly.date}</div>
                        <div className="anomaly-info">
                          <span className="anomaly-value">${anomaly.value.toLocaleString()}</span>
                          <span className={`anomaly-badge ${anomaly.severity}`}>
                            {anomaly.severity} severity
                          </span>
                        </div>
                        <div className="anomaly-zscore">
                          Z-Score: {anomaly.z_score} (±{anomaly.z_score}σ from mean)
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )
          ))}

          {anomalies.summary.total_anomalies === 0 && (
            <div className="no-anomalies">
              <p>✅ No significant anomalies detected in the financial data.</p>
              <p>This indicates stable and consistent financial reporting.</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default AIModels;
