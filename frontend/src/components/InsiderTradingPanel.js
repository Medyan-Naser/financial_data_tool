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
