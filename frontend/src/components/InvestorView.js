import React, { useState, useEffect, useRef } from 'react';
import ChartManager from './ChartManager';
import { searchInvestors, getInvestorHoldings, getInvestorFilings, getInvestorHistory } from '../api';
import './InvestorView.css';

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

/**
 * Convert 13F history API response to ChartManager chart config.
 * columns = filing dates (time-series x-axis)
 * data    = [ { name: companyName, values: [pct, pct, ...] }, ... ]
 */
function buildHistoryChartConfig(investorName, historyData) {
  return {
    id: `investor_${Date.now()}`,
    type: 'line',
    title: `${investorName} — Portfolio % Over Time`,
    ticker: investorName,
    statementType: 'investor_holdings',
    columns: historyData.columns,
    data: historyData.rows,
    selectedRowNames: historyData.rows.map(r => r.name),
    analysisMode: 'absolute',
    comparisonTicker: null,
  };
}


export default function InvestorView() {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchError, setSearchError] = useState(null);
  const [showDropdown, setShowDropdown] = useState(false);

  const [selectedInvestor, setSelectedInvestor] = useState(null);
  const [filings, setFilings] = useState([]);
  const [selectedFilingDate, setSelectedFilingDate] = useState('');
  const [holdings, setHoldings] = useState(null);
  const [historyChart, setHistoryChart] = useState(null);
  const [holdingsLoading, setHoldingsLoading] = useState(false);
  const [holdingsError, setHoldingsError] = useState(null);
  const [chartType, setChartType] = useState('line');

  const [sortField, setSortField] = useState('value');
  const [sortDir, setSortDir] = useState('desc');
  const [searchPage, setSearchPage] = useState(1);

  const searchDebounce = useRef(null);
  const dropdownRef = useRef(null);

  useEffect(() => {
    const handleClick = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setShowDropdown(false);
      }
    };
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  const handleSearchChange = (e) => {
    const val = e.target.value;
    setSearchQuery(val);
    clearTimeout(searchDebounce.current);
    if (val.length < 2) {
      setSearchResults([]);
      setShowDropdown(false);
      return;
    }
    searchDebounce.current = setTimeout(async () => {
      setSearchLoading(true);
      setSearchError(null);
      try {
        const res = await searchInvestors(val);
        setSearchResults(res.results || []);
        setShowDropdown(true);
      } catch (err) {
        setSearchError(err.message || 'Search failed');
        setSearchResults([]);
      } finally {
        setSearchLoading(false);
      }
    }, 400);
  };

  const handleSelectInvestor = async (investor) => {
    setSelectedInvestor(investor);
    setSearchQuery(investor.name);
    setShowDropdown(false);
    setHoldings(null);
    setHistoryChart(null);
    setHoldingsError(null);
    setFilings([]);
    setSelectedFilingDate('');

    try {
      const filingsData = await getInvestorFilings(investor.cik);
      const list = filingsData.filings || [];
      setFilings(list);
      if (list.length > 0) {
        setSelectedFilingDate(list[0].filingDate);
        await loadHoldings(investor.cik, list[0].filingDate);
      }
      // Load portfolio history for ChartManager
      loadHistory(investor.cik);
    } catch (err) {
      setHoldingsError(err.message || 'Failed to load filings');
    }
  };

  const loadHoldings = async (cik, date, forceRefresh = false) => {
    setHoldingsLoading(true);
    setHoldingsError(null);
    try {
      const data = await getInvestorHoldings(cik, date, forceRefresh);
      setHoldings(data);
    } catch (err) {
      setHoldingsError(err.message || 'Failed to load holdings');
    } finally {
      setHoldingsLoading(false);
    }
  };

  const loadHistory = async (cik, forceRefresh = false) => {
    try {
      const data = await getInvestorHistory(cik, { num_filings: 8, top_n: 15, force_refresh: forceRefresh });
      const config = buildHistoryChartConfig(data.investor_name, data);
      setHistoryChart({ ...config, type: chartType });
    } catch (err) {
      console.warn('Portfolio history unavailable:', err.message);
    }
  };

  const handleFilingDateChange = async (e) => {
    const date = e.target.value;
    setSelectedFilingDate(date);
    if (selectedInvestor) await loadHoldings(selectedInvestor.cik, date);
  };

  const handleRefresh = () => {
    if (selectedInvestor && selectedFilingDate) {
      loadHoldings(selectedInvestor.cik, selectedFilingDate, true);
      loadHistory(selectedInvestor.cik, true);
    }
  };

  const handleSort = (field) => {
    if (sortField === field) setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    else { setSortField(field); setSortDir('desc'); }
  };

  // Update chart type in historyChart when chartType changes
  useEffect(() => {
    if (historyChart) setHistoryChart(prev => ({ ...prev, type: chartType }));
  }, [chartType]);

  const sortedHoldings = holdings
    ? [...(holdings.holdings || [])].sort((a, b) => {
        const av = a[sortField] ?? 0;
        const bv = b[sortField] ?? 0;
        const cmp = typeof av === 'number' ? av - bv : String(av).localeCompare(String(bv));
        return sortDir === 'asc' ? cmp : -cmp;
      })
    : [];

  const PAGE_SIZE = 50;
  const pagedHoldings = sortedHoldings.slice((searchPage - 1) * PAGE_SIZE, searchPage * PAGE_SIZE);
  const totalPages = Math.max(1, Math.ceil(sortedHoldings.length / PAGE_SIZE));

  const SortTh = ({ field, label }) => (
    <th onClick={() => handleSort(field)} className="inv-sortable">
      {label}{sortField === field ? (sortDir === 'asc' ? ' ▲' : ' ▼') : ''}
    </th>
  );

  return (
    <div className="inv-root">
      <div className="inv-header">
        <h2>🏛️ Institutional Investors</h2>
        <p className="inv-subtitle">Form 13F-HR — institutional portfolio holdings</p>
      </div>

      {/* Search */}
      <div className="inv-search-section" ref={dropdownRef}>
        <div className="inv-search-wrap">
          <input
            className="inv-search-input"
            type="text"
            placeholder="Search investor name (e.g., Berkshire, Vanguard, BlackRock…)"
            value={searchQuery}
            onChange={handleSearchChange}
            onFocus={() => searchResults.length > 0 && setShowDropdown(true)}
          />
          {searchLoading && <span className="inv-search-spinner">⏳</span>}
        </div>

        {showDropdown && searchResults.length > 0 && (
          <div className="inv-dropdown">
            {searchResults.map((r) => (
              <div
                key={r.cik}
                className="inv-dropdown-item"
                onClick={() => handleSelectInvestor(r)}
              >
                <span className="inv-dropdown-name">{r.name}</span>
                <span className="inv-dropdown-cik">CIK {r.cik}</span>
              </div>
            ))}
          </div>
        )}

        {searchError && <div className="inv-error">❌ {searchError}</div>}
      </div>

      {!selectedInvestor && !searchLoading && (
        <div className="inv-welcome">
          <h3>Search for an institutional investor</h3>
          <p>Type a fund or company name to find their Form 13F portfolio filings.</p>
          <div className="inv-examples">
            <span>Examples:</span>
            {['Berkshire Hathaway', 'Vanguard', 'BlackRock', 'Renaissance Technologies'].map((name) => (
              <button
                key={name}
                className="inv-example-btn"
                onClick={() => {
                  setSearchQuery(name);
                  handleSearchChange({ target: { value: name } });
                }}
              >
                {name}
              </button>
            ))}
          </div>
        </div>
      )}

      {holdingsLoading && (
        <div className="inv-loading">⏳ Fetching 13F portfolio data from EDGAR…</div>
      )}

      {holdingsError && <div className="inv-error">❌ {holdingsError}</div>}

      {holdings && !holdingsLoading && (
        <>
          <div className="inv-investor-header">
            <div className="inv-investor-info">
              <h3 className="inv-investor-name">{holdings.investor_name}</h3>
              <span className="inv-cik-badge">CIK {holdings.cik}</span>
              {holdings.from_cache && <span className="inv-cache-badge">📦 Cached</span>}
            </div>
            <div className="inv-filing-controls">
              {filings.length > 0 && (
                <label className="inv-filing-label">
                  Filing date:
                  <select
                    className="inv-filing-select"
                    value={selectedFilingDate}
                    onChange={handleFilingDateChange}
                  >
                    {filings.map((f) => (
                      <option key={f.filingDate} value={f.filingDate}>
                        {f.filingDate} {f.reportDate ? `(Q: ${f.reportDate})` : ''}
                      </option>
                    ))}
                  </select>
                </label>
              )}
              <button className="inv-refresh-btn" onClick={handleRefresh}>
                🔄 Refresh
              </button>
            </div>
          </div>

          <div className="inv-portfolio-summary">
            <div className="inv-stat">
              <div className="inv-stat-label">Total Portfolio Value</div>
              <div className="inv-stat-value">{formatValue(holdings.total_portfolio_value)}</div>
            </div>
            <div className="inv-stat">
              <div className="inv-stat-label">Positions</div>
              <div className="inv-stat-value">{holdings.total_holdings.toLocaleString()}</div>
            </div>
            <div className="inv-stat">
              <div className="inv-stat-label">Report Date</div>
              <div className="inv-stat-value">{holdings.report_date || holdings.filing_date}</div>
            </div>
          </div>

          {/* Portfolio History Chart via ChartManager */}
          {historyChart && (
            <div className="inv-chart-section">
              <div className="inv-chart-header-row">
                <h3>Top Holdings — Portfolio Weight Over Time</h3>
                <div className="inv-chart-type-btns">
                  {['line', 'area', 'bar', 'stacked-area'].map(t => (
                    <button
                      key={t}
                      className={`inv-chart-type-btn ${chartType === t ? 'active' : ''}`}
                      onClick={() => setChartType(t)}
                    >
                      {t}
                    </button>
                  ))}
                </div>
              </div>
              <div className="inv-chart-manager-wrap">
                <ChartManager
                  charts={[{ ...historyChart, type: chartType }]}
                  onRemoveChart={() => {}}
                  ticker={selectedInvestor?.name || ''}
                />
              </div>
            </div>
          )}

          {/* Holdings Table */}
          <div className="inv-table-section">
            <div className="inv-table-header-row">
              <h3>Holdings ({sortedHoldings.length} positions)</h3>
              <div className="inv-pagination">
                <button
                  className="inv-page-btn"
                  disabled={searchPage === 1}
                  onClick={() => setSearchPage((p) => p - 1)}
                >
                  ←
                </button>
                <span className="inv-page-info">
                  {searchPage} / {totalPages}
                </span>
                <button
                  className="inv-page-btn"
                  disabled={searchPage >= totalPages}
                  onClick={() => setSearchPage((p) => p + 1)}
                >
                  →
                </button>
              </div>
            </div>

            <div className="inv-table-wrap">
              <table className="inv-table">
                <thead>
                  <tr>
                    <th>#</th>
                    <SortTh field="company_name" label="Company" />
                    <th>CUSIP</th>
                    <th>Class</th>
                    <SortTh field="shares" label="Shares" />
                    <SortTh field="value" label="Market Value" />
                    <SortTh field="portfolio_pct" label="Portfolio %" />
                  </tr>
                </thead>
                <tbody>
                  {pagedHoldings.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="inv-no-data">No holdings found</td>
                    </tr>
                  ) : (
                    pagedHoldings.map((h, idx) => {
                      const rank = (searchPage - 1) * PAGE_SIZE + idx + 1;
                      return (
                        <tr key={idx} className="inv-row">
                          <td className="inv-rank">{rank}</td>
                          <td className="inv-company">{h.company_name}</td>
                          <td className="inv-cusip">{h.cusip}</td>
                          <td className="inv-class">{h.title_of_class}</td>
                          <td className="inv-num">{formatShares(h.shares)}</td>
                          <td className="inv-num">{formatValue(h.value)}</td>
                          <td className="inv-num">
                            <div className="inv-pct-bar-wrap">
                              <div
                                className="inv-pct-bar"
                                style={{ width: `${Math.min(100, (h.portfolio_pct || 0) * 5)}%` }}
                              />
                              <span>{(h.portfolio_pct || 0).toFixed(2)}%</span>
                            </div>
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
