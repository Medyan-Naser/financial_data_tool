import React, { useState, useEffect, useCallback } from 'react';
import ChartManager from './ChartManager';
import { getInsiderTransactions } from '../api';
import './InsiderTradingPanel.css';

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

/**
 * Convert insider transactions list into ChartManager-compatible chart config.
 * Groups buy/sell dollar amounts by month (YYYY-MM) → columns & data arrays.
 *
 * Buy  (positive): P = open-market purchase
 *                  M + acquired_disposed='A' = RSU/option exercise (acquiring shares)
 * Sell (negative): S = open-market sale
 *                  F = tax-withholding disposal
 * Excluded: M+D (derivative bookkeeping), gifts (G), awards (A)
 * Uses SHARE COUNTS (not dollar values) because RSU exercises have no total_value.
 */
function buildChartConfig(ticker, transactions) {
  const monthMap = {};

  for (const t of transactions) {
    const date = t.transaction_date || t.filing_date || '';
    if (!date) continue;
    const month = date.slice(0, 7); // "YYYY-MM"
    if (!monthMap[month]) monthMap[month] = { buy: 0, sell: 0 };

    const shares = t.shares || 0;
    const code = (t.transaction_code || '').toUpperCase();
    const ad   = (t.acquired_disposed || '').toUpperCase();

    if (code === 'P' || (code === 'M' && ad === 'A')) {
      monthMap[month].buy += shares;
    } else if (code === 'S' || code === 'F') {
      monthMap[month].sell += shares;
    }
  }

  // Sort months chronologically (oldest → newest, ChartManager reverses internally)
  const sortedMonths = Object.keys(monthMap).sort((a, b) => a.localeCompare(b));

  const columns = sortedMonths.map(m => `${m}-01`); // full date for ChartManager
  const buyValues = sortedMonths.map(m => monthMap[m].buy);
  const sellValues = sortedMonths.map(m => -monthMap[m].sell); // negative = below axis

  return {
    id: `insider_${ticker}_${Date.now()}`,
    type: 'bar',
    title: `${ticker} — Insider Trading Activity`,
    ticker,
    statementType: 'insider_activity',
    columns,
    data: [
      { name: 'Acquired (shares)', values: buyValues },
      { name: 'Disposed (shares)', values: sellValues },
    ],
    selectedRowNames: ['Acquired (shares)', 'Disposed (shares)'],
    analysisMode: 'absolute',
    comparisonTicker: null,
  };
}

const FILTER_OPTIONS = ['All', 'Acquired', 'Disposed', 'Other'];

const DEFAULT_YEARS = 10;

export default function InsiderTradingPanel({ ticker }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [chartConfig, setChartConfig] = useState(null);
  const [filter, setFilter] = useState('All');

  const fetchData = useCallback(async (forceRefresh = false) => {
    if (!ticker) return;
    setLoading(true);
    setError(null);
    try {
      const result = await getInsiderTransactions(ticker, {
        years: DEFAULT_YEARS,
        force_refresh: forceRefresh,
      });
      setData(result);
      const config = buildChartConfig(ticker, result.transactions || []);
      setChartConfig(config);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to fetch insider data');
    } finally {
      setLoading(false);
    }
  }, [ticker]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const filteredTxns = (data?.transactions || []).filter(t => {
    if (filter === 'All') return true;
    const ad = (t.acquired_disposed || '').toUpperCase();
    if (filter === 'Acquired') return ad === 'A';
    if (filter === 'Disposed') return ad === 'D';
    return ad !== 'A' && ad !== 'D'; // Other: gifts, conversions, etc.
  });

  return (
    <div className="itp-root">
      {/* Panel Header */}
      <div className="itp-header">
        <div className="itp-title-row">
          <span className="itp-icon">👥</span>
          <h3 className="itp-title">Insider Trading — {ticker}</h3>
        </div>
        <div className="itp-header-controls">
          <button className="itp-refresh-btn" onClick={() => fetchData(true)} title="Refresh from EDGAR">
            🔄
          </button>
        </div>
      </div>

      {loading && (
        <div className="itp-loading">
          ⏳ Fetching Form 4 filings from EDGAR…
          <div className="itp-loading-sub">Collecting {DEFAULT_YEARS}-year history (first load may take ~30s)</div>
        </div>
      )}

      {error && <div className="itp-error">❌ {error}</div>}

      {/* Chart via ChartManager — onRemoveChart is no-op since panel is always shown */}
      {chartConfig && !loading && (
        <div className="itp-chart-wrap">
          <ChartManager
            charts={[chartConfig]}
            onRemoveChart={() => {}}
            ticker={ticker}
          />
        </div>
      )}

      {/* Mini summary */}
      {data && !loading && (
        <div className="itp-summary-row">
          <span className="itp-summary-txt">
            {data.transactions?.length ?? 0} transactions · {data.total_filings_parsed} filings parsed
            {data.parse_errors > 0 && ` · ${data.parse_errors} errors`}
          </span>
          <span className="itp-company">{data.company_name}</span>
        </div>
      )}

      {/* Filter bar */}
      {data && !loading && (
        <div className="itp-filter-bar">
          {FILTER_OPTIONS.map(f => (
            <button
              key={f}
              className={`itp-filter-btn ${filter === f ? 'active' : ''}`}
              onClick={() => setFilter(f)}
            >
              {f}
            </button>
          ))}
        </div>
      )}

      {/* Transactions table */}
      {data && !loading && filteredTxns.length > 0 && (
        <div className="itp-table-wrap">
          <table className="itp-table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Insider</th>
                <th>Role</th>
                <th>Type</th>
                <th>Shares</th>
                <th>Price</th>
                <th>Value</th>
              </tr>
            </thead>
            <tbody>
              {filteredTxns.slice(0, 50).map((t, idx) => {
                const color = TXN_TYPE_COLOR[t.transaction_type] || '#94a3b8';
                return (
                  <tr key={idx} className="itp-row">
                    <td>{t.transaction_date || '—'}</td>
                    <td className="itp-name">{t.insider_name}</td>
                    <td className="itp-role">{t.insider_role}</td>
                    <td>
                      <span className="itp-type-pill" style={{ background: `${color}22`, color }}>
                        {t.transaction_type}
                      </span>
                    </td>
                    <td className="itp-num">{t.shares != null ? t.shares.toLocaleString() : '—'}</td>
                    <td className="itp-num">
                      {t.price_per_share != null ? `$${t.price_per_share.toFixed(2)}` : '—'}
                    </td>
                    <td className="itp-num">{formatCurrency(t.total_value)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          {filteredTxns.length > 50 && (
            <div className="itp-table-more">Showing 50 of {filteredTxns.length} transactions</div>
          )}
        </div>
      )}
    </div>
  );
}
