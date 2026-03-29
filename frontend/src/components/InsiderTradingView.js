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
