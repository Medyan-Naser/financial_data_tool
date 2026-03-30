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
