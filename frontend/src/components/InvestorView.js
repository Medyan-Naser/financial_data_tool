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
