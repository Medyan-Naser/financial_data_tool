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
  