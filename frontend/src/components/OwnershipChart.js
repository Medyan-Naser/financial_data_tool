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
