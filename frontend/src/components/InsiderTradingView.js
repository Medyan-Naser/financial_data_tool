import React, { useState, useEffect, useCallback } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine,
} from 'recharts';
import TickerSearch from '../TickerSearch';
import { getInsiderTransactions } from '../api';
import './InsiderTradingView.css';

const FILTER_OPTIONS = ['All', 'Buy', 'Sell', 'Award/Grant', 'Tax Withholding', 'Option/RSU Exercise'];

const TXN_TYPE_COLOR = {
  Buy: '#22c55e',
  Sell: '#ef4444',
  'Award/Grant': '#3b82f6',
  'Tax Withholding': '#f97316',
  'Option/RSU Exercise': '#a855f7',
};

function formatCurrency(val) {
  if (val == null) return '—';
  if (Math.abs(val) >= 1e9) return `$${(val / 1e9).toFixed(2)}B`;
  if (Math.abs(val) >= 1e6) return `$${(val / 1e6).toFixed(2)}M`;
  if (Math.abs(val) >= 1e3) return `$${(val / 1e3).toFixed(1)}K`;
  return `$${val.toFixed(2)}`;
}

function formatShares(val) {
  if (val == null) return '—';
  return val.toLocaleString();
}

function groupByMonth(transactions) {
  const map = {};
  for (const t of transactions) {
    const date = t.transaction_date || t.filing_date || '';
    if (!date) continue;
    const month = date.slice(0, 7); // "YYYY-MM"
    if (!map[month]) map[month] = { month, buy: 0, sell: 0 };
    const val = t.total_value || 0;
    const code = (t.transaction_code || '').toUpperCase();
    const type = t.transaction_type || '';
    if (code === 'P' || type === 'Buy') {
      map[month].buy += val;
    } else if (code === 'S' || type === 'Sell') {
      map[month].sell += -Math.abs(val);
    }
  }
  return Object.values(map).sort((a, b) => a.month.localeCompare(b.month));
}

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload || !payload.length) return null;
  return (
    <div className="itv-tooltip">
      <p className="itv-tooltip-label">{label}</p>
      {payload.map((p) => (
        <p key={p.name} style={{ color: p.fill || p.color }}>
          {p.name}: {formatCurrency(Math.abs(p.value))}
        </p>
      ))}
    </div>
  );
};

export default function InsiderTradingView({ availableTickers }) {
  const [selectedTicker, setSelectedTicker] = useState(null);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState('All');
  const [includeDerivatives, setIncludeDerivatives] = useState(false);
  const [limit, setLimit] = useState(40);
  const [sortField, setSortField] = useState('transaction_date');
  const [sortDir, setSortDir] = useState('desc');

  const fetchData = useCallback(async (ticker, opts = {}) => {
    if (!ticker) return;
    setLoading(true);
    setError(null);
    setData(null);
    try {
      const result = await getInsiderTransactions(ticker, {
        limit: opts.limit ?? limit,
        include_derivatives: opts.includeDerivatives ?? includeDerivatives,
        force_refresh: opts.forceRefresh ?? false,
      });
      setData(result);
    } catch (err) {
      setError(err.message || 'Failed to fetch insider transactions');
    } finally {
      setLoading(false);
    }
  }, [limit, includeDerivatives]);

  useEffect(() => {
    if (selectedTicker) fetchData(selectedTicker);
  }, [selectedTicker, includeDerivatives, limit]);

  const handleTickerSelect = (ticker) => {
    setSelectedTicker(ticker);
    setFilter('All');
  };

  const handleSort = (field) => {
    if (sortField === field) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortField(field);
      setSortDir('desc');
    }
  };

  const filteredTransactions = data?.transactions
    ? data.transactions.filter((t) => {
        if (filter === 'All') return true;
        if (filter === 'Buy') return t.transaction_type === 'Buy';
        if (filter === 'Sell') return t.transaction_type === 'Sell';
        return (t.transaction_type || '').startsWith(filter);
      })
    : [];

  const sortedTransactions = [...filteredTransactions].sort((a, b) => {
    const av = a[sortField] ?? '';
    const bv = b[sortField] ?? '';
    const cmp = typeof av === 'number' ? av - bv : String(av).localeCompare(String(bv));
    return sortDir === 'asc' ? cmp : -cmp;
  });

  const chartData = data ? groupByMonth(data.transactions) : [];

  const SortHeader = ({ field, label }) => (
    <th onClick={() => handleSort(field)} className="itv-sortable">
      {label} {sortField === field ? (sortDir === 'asc' ? '▲' : '▼') : ''}
    </th>
  );

  return (
    <div className="itv-root">
      <div className="itv-header">
        <h2>👥 Insider Trading</h2>
        <p className="itv-subtitle">Form 4 filings — reported insider transactions</p>
      </div>

      <div className="itv-controls">
        <div className="itv-search-wrap">
          <TickerSearch
            tickers={availableTickers}
            onSelect={handleTickerSelect}
            selectedTicker={selectedTicker}
          />
        </div>

        <div className="itv-options">
          <label className="itv-option-label">
            <input
              type="checkbox"
              checked={includeDerivatives}
              onChange={(e) => setIncludeDerivatives(e.target.checked)}
            />
            Include RSU/options
          </label>
          <label className="itv-option-label">
            Filings:
            <select
              value={limit}
              onChange={(e) => setLimit(Number(e.target.value))}
              className="itv-select"
            >
              {[20, 40, 60, 80, 100].map((n) => (
                <option key={n} value={n}>{n}</option>
              ))}
            </select>
          </label>
          {data && !loading && (
            <button
              className="itv-refresh-btn"
              onClick={() => fetchData(selectedTicker, { forceRefresh: true })}
            >
              🔄 Refresh
            </button>
          )}
        </div>
      </div>

      {loading && (
        <div className="itv-loading">
          ⏳ Fetching Form 4 filings from EDGAR…
          <div className="itv-loading-hint">Parsing up to {limit} filings — may take a moment</div>
        </div>
      )}

      {error && <div className="itv-error">❌ {error}</div>}

      {!selectedTicker && !loading && (
        <div className="itv-welcome">
          <h3>Search for a ticker to view insider transactions</h3>
          <p>Uses SEC EDGAR Form 4 filings. Only tickers in your cache list are shown, but you can type any ticker directly.</p>
        </div>
      )}

      {data && !loading && (
        <>
          <div className="itv-summary">
            <span className="itv-company">{data.company_name} ({data.ticker})</span>
            <span className="itv-meta">
              {data.transactions.length} transactions from {data.total_filings_parsed} filings
              {data.parse_errors > 0 && ` · ${data.parse_errors} parse errors`}
            </span>
            {data.from_cache && <span className="itv-cache-badge">📦 Cached</span>}
          </div>

          {/* Activity Chart */}
          {chartData.length > 0 && (
            <div className="itv-chart-section">
              <h3>Net Insider Activity by Month</h3>
              <p className="itv-chart-note">Green = purchases · Red = sales (by dollar value)</p>
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={chartData} margin={{ top: 10, right: 20, left: 20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="month" tick={{ fill: '#94a3b8', fontSize: 11 }} />
                  <YAxis
                    tickFormatter={(v) => formatCurrency(Math.abs(v))}
                    tick={{ fill: '#94a3b8', fontSize: 11 }}
                  />
                  <Tooltip content={<CustomTooltip />} />
                  <Legend wrapperStyle={{ color: '#94a3b8' }} />
                  <ReferenceLine y={0} stroke="#64748b" />
                  <Bar dataKey="buy" name="Purchases" fill="#22c55e" radius={[3, 3, 0, 0]} />
                  <Bar dataKey="sell" name="Sales" fill="#ef4444" radius={[0, 0, 3, 3]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Filters */}
          <div className="itv-filter-bar">
            {FILTER_OPTIONS.map((f) => (
              <button
                key={f}
                className={`itv-filter-btn ${filter === f ? 'active' : ''}`}
                onClick={() => setFilter(f)}
              >
                {f}
              </button>
            ))}
          </div>

          {/* Transactions Table */}
          <div className="itv-table-wrap">
            <table className="itv-table">
              <thead>
                <tr>
                  <SortHeader field="transaction_date" label="Date" />
                  <SortHeader field="insider_name" label="Insider" />
                  <SortHeader field="insider_role" label="Role" />
                  <SortHeader field="transaction_type" label="Type" />
                  <SortHeader field="shares" label="Shares" />
                  <SortHeader field="price_per_share" label="Price" />
                  <SortHeader field="total_value" label="Total Value" />
                  <th>Security</th>
                </tr>
              </thead>
              <tbody>
                {sortedTransactions.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="itv-no-data">
                      No transactions found for filter: {filter}
                    </td>
                  </tr>
                ) : (
                  sortedTransactions.map((t, idx) => {
                    const color = TXN_TYPE_COLOR[t.transaction_type] || '#94a3b8';
                    return (
                      <tr key={idx} className="itv-row">
                        <td>{t.transaction_date || '—'}</td>
                        <td className="itv-name">{t.insider_name}</td>
                        <td className="itv-role">{t.insider_role}</td>
                        <td>
                          <span className="itv-type-badge" style={{ background: color + '22', color }}>
                            {t.transaction_type}
                          </span>
                        </td>
                        <td className="itv-num">{formatShares(t.shares)}</td>
                        <td className="itv-num">
                          {t.price_per_share != null ? `$${t.price_per_share.toFixed(2)}` : '—'}
                        </td>
                        <td className="itv-num">{formatCurrency(t.total_value)}</td>
                        <td className="itv-security">{t.security_title}</td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
