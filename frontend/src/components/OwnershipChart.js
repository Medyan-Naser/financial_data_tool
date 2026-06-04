import React, { useState, useEffect } from 'react';
import {
  PieChart, Pie, Cell, ResponsiveContainer, Tooltip,
  LineChart, Line, XAxis, YAxis, CartesianGrid, Legend
} from 'recharts';
import { getCompanyOwnership, getOwnershipHistory } from '../api';
import './OwnershipChart.css';

const OWNERSHIP_COLORS = {
  institutional: '#3b82f6',
  insider: '#10b981',
  retail: '#f59e0b',
};

function formatValue(val) {
  if (val == null) return '—';
  if (val >= 1e12) return `$${(val / 1e12).toFixed(2)}T`;
  if (val >= 1e9) return `$${(val / 1e9).toFixed(2)}B`;
  if (val >= 1e6) return `$${(val / 1e6).toFixed(2)}M`;
  if (val >= 1e3) return `$${(val / 1e3).toFixed(1)}K`;
  return `$${val.toFixed(0)}`;
}

function formatShares(val) {
  if (val == null) return '—';
  if (val >= 1e9) return `${(val / 1e9).toFixed(2)}B`;
  if (val >= 1e6) return `${(val / 1e6).toFixed(2)}M`;
  if (val >= 1e3) return `${(val / 1e3).toFixed(1)}K`;
  return val.toLocaleString();
}

const CustomTooltip = ({ active, payload }) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="own-tooltip">
        <div className="own-tooltip-name">{data.name}</div>
        <div className="own-tooltip-value">{data.value?.toFixed(1)}%</div>
        {data.shares && (
          <div className="own-tooltip-shares">{formatShares(data.shares)} shares</div>
        )}
      </div>
    );
  }
  return null;
};

export default function OwnershipChart({ ticker }) {
  const [ownershipData, setOwnershipData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [viewMode, setViewMode] = useState('pie'); // 'pie', 'holders', or 'history'
  const [historyData, setHistoryData] = useState(null);
  const [historyLoading, setHistoryLoading] = useState(false);

  useEffect(() => {
    if (!ticker) return;
    
    const fetchOwnership = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await getCompanyOwnership(ticker);
        setOwnershipData(data);
      } catch (err) {
        setError(err.response?.data?.detail || err.message || 'Failed to load ownership data');
      } finally {
        setLoading(false);
      }
    };
    
    fetchOwnership();
  }, [ticker]);

  const handleRefresh = async () => {
    if (!ticker) return;
    setLoading(true);
    setError(null);
    try {
      const data = await getCompanyOwnership(ticker, true);
      setOwnershipData(data);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to refresh ownership data');
    } finally {
      setLoading(false);
    }
  };

  const fetchHistory = async () => {
    if (!ticker || historyData) return;
    setHistoryLoading(true);
    try {
      const data = await getOwnershipHistory(ticker, { quarters: 8 });
      setHistoryData(data);
    } catch (err) {
      console.error('Failed to load history:', err);
    } finally {
      setHistoryLoading(false);
    }
  };

  useEffect(() => {
    if (viewMode === 'history' && !historyData && !historyLoading) {
      fetchHistory();
    }
  }, [viewMode]);

  if (loading) {
    return (
      <div className="own-panel">
        <div className="own-header">
          <h3>📊 Company Ownership</h3>
        </div>
        <div className="own-loading">⏳ Loading ownership data from SEC EDGAR...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="own-panel">
        <div className="own-header">
          <h3>📊 Company Ownership</h3>
        </div>
        <div className="own-error">❌ {error}</div>
      </div>
    );
  }

  if (!ownershipData) {
    return (
      <div className="own-panel">
        <div className="own-header">
          <h3>📊 Company Ownership</h3>
        </div>
        <div className="own-empty">Select a ticker to view ownership data</div>
      </div>
    );
  }

  const breakdown = ownershipData.ownership_breakdown;
  
  const pieData = [
    {
      name: 'Institutional',
      value: breakdown.institutional?.percentage || 0,
      shares: breakdown.institutional?.shares,
      color: OWNERSHIP_COLORS.institutional,
    },
    {
      name: 'Insider',
      value: breakdown.insider?.percentage || 0,
      shares: breakdown.insider?.shares,
      color: OWNERSHIP_COLORS.insider,
    },
    {
      name: 'Retail/Other',
      value: breakdown.retail_other?.percentage || 0,
      shares: breakdown.retail_other?.shares,
      color: OWNERSHIP_COLORS.retail,
    },
  ].filter(d => d.value > 0);

  const topHolders = ownershipData.top_institutional_holders || [];
  const topInsiders = ownershipData.top_insiders || [];
  const sharesOutstanding = ownershipData.shares_outstanding || 1;

  const calcPct = (shares) => {
    if (!shares || !sharesOutstanding) return 0;
    return ((shares / sharesOutstanding) * 100).toFixed(2);
  };

  return (
    <div className="own-panel">
      <div className="own-header">
        <div className="own-title-row">
          <h3>📊 Company Ownership</h3>
        </div>
        <div className="own-controls">
          <div className="own-view-toggle">
            <button
              className={`own-view-btn ${viewMode === 'pie' ? 'active' : ''}`}
              onClick={() => setViewMode('pie')}
            >
              Breakdown
            </button>
            <button
              className={`own-view-btn ${viewMode === 'holders' ? 'active' : ''}`}
              onClick={() => setViewMode('holders')}
            >
              Top Holders
            </button>
            <button
              className={`own-view-btn ${viewMode === 'history' ? 'active' : ''}`}
              onClick={() => setViewMode('history')}
            >
              History
            </button>
          </div>
          <button className="own-refresh-btn" onClick={handleRefresh}>
            🔄
          </button>
        </div>
      </div>

      <div className="own-company-info">
        <span className="own-company-name">{ownershipData.company_name}</span>
        {ownershipData.shares_outstanding && (
          <span className="own-shares-out">
            {formatShares(ownershipData.shares_outstanding)} shares outstanding
          </span>
        )}
      </div>

      {viewMode === 'pie' && (
        <div className="own-content">
          <div className="own-chart-container">
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={90}
                  paddingAngle={2}
                  dataKey="value"
                  label={({ name, value }) => `${name}: ${value.toFixed(1)}%`}
                  labelLine={false}
                >
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div className="own-breakdown-stats">
            <div className="own-stat institutional">
              <div className="own-stat-icon" style={{ background: OWNERSHIP_COLORS.institutional }}>🏛️</div>
              <div className="own-stat-info">
                <div className="own-stat-label">Institutional</div>
                <div className="own-stat-value">{(breakdown.institutional?.percentage || 0).toFixed(1)}%</div>
                <div className="own-stat-detail">{breakdown.institutional?.num_holders || 0} holders</div>
              </div>
            </div>
            <div className="own-stat insider">
              <div className="own-stat-icon" style={{ background: OWNERSHIP_COLORS.insider }}>👤</div>
              <div className="own-stat-info">
                <div className="own-stat-label">Insider</div>
                <div className="own-stat-value">{(breakdown.insider?.percentage || 0).toFixed(1)}%</div>
                <div className="own-stat-detail">{breakdown.insider?.num_holders || 0} insiders</div>
              </div>
            </div>
            <div className="own-stat retail">
              <div className="own-stat-icon" style={{ background: OWNERSHIP_COLORS.retail }}>🌐</div>
              <div className="own-stat-info">
                <div className="own-stat-label">Retail/Other</div>
                <div className="own-stat-value">{(breakdown.retail_other?.percentage || 0).toFixed(1)}%</div>
                <div className="own-stat-detail">Public float</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {viewMode === 'holders' && (
        <div className="own-holders-content">
          {/* Large Shareholders (>5% from SC 13G/13D) */}
          {ownershipData.large_shareholders?.length > 0 && (
            <div className="own-holders-section">
              <h4>📈 Major Shareholders (&gt;5%)</h4>
              <div className="own-holders-list">
                {ownershipData.large_shareholders.slice(0, 6).map((sh, idx) => (
                  <div key={idx} className="own-holder-row major">
                    <span className="own-holder-rank">{idx + 1}</span>
                    <span className="own-holder-name">
                      {sh.name}
                      <span className="own-holder-date">{sh.form} - {sh.filing_date}</span>
                    </span>
                    {sh.percentage ? (
                      <span className="own-holder-pct major">{sh.percentage.toFixed(1)}%</span>
                    ) : (
                      <span className="own-holder-pct">{calcPct(sh.shares)}%</span>
                    )}
                    <span className="own-holder-shares">{formatShares(sh.shares)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {topHolders.length > 0 && (
            <div className="own-holders-section">
              <h4>🏛️ Institutional Holders (13F)</h4>
              <div className="own-holders-list">
                {topHolders.slice(0, 8).map((holder, idx) => (
                  <div key={idx} className="own-holder-row">
                    <span className="own-holder-rank">{idx + 1}</span>
                    <span className="own-holder-name">
                      {holder.investor_name}
                      {holder.report_date && (
                        <span className="own-holder-date">Q: {holder.report_date}</span>
                      )}
                    </span>
                    <span className="own-holder-pct">{calcPct(holder.shares)}%</span>
                    <span className="own-holder-shares">{formatShares(holder.shares)}</span>
                    <span className="own-holder-value">{formatValue(holder.value)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {topInsiders.length > 0 && (
            <div className="own-holders-section">
              <h4>👤 Top Insiders</h4>
              <div className="own-holders-list">
                {topInsiders.slice(0, 8).map((insider, idx) => (
                  <div key={idx} className="own-holder-row">
                    <span className="own-holder-rank">{idx + 1}</span>
                    <span className="own-holder-name">
                      {insider.name}
                      <span className="own-holder-role">{insider.role}</span>
                    </span>
                    <span className="own-holder-pct">{calcPct(insider.shares)}%</span>
                    <span className="own-holder-shares">{formatShares(insider.shares)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {topHolders.length === 0 && topInsiders.length === 0 && (
            <div className="own-no-holders">No holder data available</div>
          )}
        </div>
      )}

      {viewMode === 'history' && (
        <div className="own-history-content">
          {historyLoading ? (
            <div className="own-loading">Loading historical data...</div>
          ) : historyData && historyData.history && historyData.history.length > 1 ? (
            <>
              <ResponsiveContainer width="100%" height={220}>
                <LineChart data={historyData.history}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis 
                    dataKey="period" 
                    tick={{ fontSize: 11 }} 
                    tickFormatter={(val) => val.slice(0, 7)}
                  />
                  <YAxis 
                    tick={{ fontSize: 11 }} 
                    tickFormatter={(val) => `${val}%`}
                    domain={[0, 'auto']}
                  />
                  <Tooltip 
                    formatter={(val) => [`${val.toFixed(1)}%`, '']}
                    labelFormatter={(label) => `Period: ${label}`}
                  />
                  <Legend />
                  <Line 
                    type="monotone" 
                    dataKey="institutional_pct" 
                    name="Institutional" 
                    stroke={OWNERSHIP_COLORS.institutional} 
                    strokeWidth={2}
                    dot={{ r: 4 }}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="insider_pct" 
                    name="Insider" 
                    stroke={OWNERSHIP_COLORS.insider} 
                    strokeWidth={2}
                    dot={{ r: 4 }}
                  />
                </LineChart>
              </ResponsiveContainer>
              <div className="own-history-note">
                Ownership trends from quarterly 13F filings
              </div>
            </>
          ) : historyData && historyData.current ? (
            <div className="own-current-snapshot">
              <div className="own-snapshot-title">Current Ownership Snapshot</div>
              <div className="own-snapshot-stats">
                <div className="own-snapshot-stat">
                  <span className="own-snapshot-label">Institutional</span>
                  <span className="own-snapshot-value" style={{ color: OWNERSHIP_COLORS.institutional }}>
                    {historyData.current.institutional?.percentage?.toFixed(1) || 0}%
                  </span>
                </div>
                <div className="own-snapshot-stat">
                  <span className="own-snapshot-label">Insider</span>
                  <span className="own-snapshot-value" style={{ color: OWNERSHIP_COLORS.insider }}>
                    {historyData.current.insider?.percentage?.toFixed(1) || 0}%
                  </span>
                </div>
                <div className="own-snapshot-stat">
                  <span className="own-snapshot-label">Retail</span>
                  <span className="own-snapshot-value" style={{ color: OWNERSHIP_COLORS.retail }}>
                    {historyData.current.retail_other?.percentage?.toFixed(1) || 0}%
                  </span>
                </div>
              </div>
              <div className="own-history-note">
                Historical tracking requires aggregating quarterly 13F filings from all major institutions.
                Currently showing latest available data.
              </div>
            </div>
          ) : (
            <div className="own-no-holders">
              Historical data not available.
            </div>
          )}
        </div>
      )}

    </div>
  );
}
