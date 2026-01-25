# Stock Financial Metrics

This document describes all financial metrics extracted and calculated from company financial statements.

## Income Statement Metrics

| Metric | Description |
|--------|-------------|
| **Total Revenue** | Total income from all business activities before any deductions |
| **Cost of Goods Sold (COGS)** | Direct costs attributable to producing goods/services sold |
| **Gross Profit** | Revenue minus COGS; measures production efficiency |
| **SG&A** | Selling, General & Administrative expenses |
| **R&D** | Research & Development expenses |
| **Operating Income** | Profit from core business operations (EBIT) |
| **Interest Expense** | Cost of borrowing (debt interest payments) |
| **EBT** | Earnings Before Taxes |
| **Income Tax Expense** | Taxes paid on earnings |
| **Net Income** | Final profit after all expenses and taxes |
| **EPS Basic** | Earnings Per Share (basic shares outstanding) |
| **EPS Diluted** | Earnings Per Share (including stock options, convertibles) |

## Balance Sheet Metrics

### Assets

| Metric | Description |
|--------|-------------|
| **Cash & Cash Equivalents** | Highly liquid assets (cash, money market funds, T-bills < 90 days) |
| **Accounts Receivable** | Money owed by customers for goods/services delivered |
| **Inventory** | Raw materials, work-in-progress, and finished goods |
| **Current Assets** | Assets expected to be converted to cash within 1 year |
| **Property, Plant & Equipment (PP&E)** | Long-term tangible assets used in operations |
| **Goodwill** | Premium paid in acquisitions above fair market value |
| **Intangible Assets** | Non-physical assets (patents, trademarks, software) |
| **Total Assets** | Sum of all company-owned resources |

### Liabilities

| Metric | Description |
|--------|-------------|
| **Accounts Payable** | Money owed to suppliers for goods/services received |
| **Short-Term Debt** | Debt obligations due within 1 year |
| **Long-Term Debt** | Debt obligations due after 1 year |
| **Current Liabilities** | Obligations due within 1 year |
| **Total Liabilities** | Sum of all company obligations |

### Equity

| Metric | Description |
|--------|-------------|
| **Retained Earnings** | Accumulated profits not distributed as dividends |
| **Stockholders' Equity** | Net worth = Total Assets - Total Liabilities |
| **Total Equity** | Ownership value belonging to shareholders |

## Cash Flow Metrics

| Metric | Description |
|--------|-------------|
| **Operating Cash Flow** | Cash generated from core business operations |
| **Investing Cash Flow** | Cash used for/from investments (CapEx, acquisitions) |
| **Financing Cash Flow** | Cash from/to debt and equity financing |
| **Free Cash Flow** | Operating Cash Flow - Capital Expenditures |

## Health Score Components

The Financial Health Score (0-100) is calculated from five categories:

| Component | Weight | What It Measures |
|-----------|--------|------------------|
| **Profitability** | 25 pts | Net profit margins, ROE, ROA |
| **Liquidity** | 20 pts | Ability to meet short-term obligations |
| **Solvency** | 20 pts | Long-term debt sustainability |
| **Efficiency** | 15 pts | Asset utilization effectiveness |
| **Growth** | 20 pts | Revenue and earnings growth trends |

### Health Score Ratings

| Score Range | Rating | Interpretation |
|-------------|--------|----------------|
| 80-100 | Excellent | Strong financial position |
| 60-79 | Good | Healthy with minor concerns |
| 40-59 | Fair | Some financial stress indicators |
| 20-39 | Poor | Significant financial challenges |
| 0-19 | Critical | Severe financial distress |

## Bankruptcy Risk (Altman Z-Score)

The Z-Score predicts probability of bankruptcy within 2 years:

| Z-Score | Zone | Risk Level |
|---------|------|------------|
| > 2.99 | Safe | Low bankruptcy risk (~5%) |
| 1.81 - 2.99 | Grey | Moderate risk (~20%) |
| < 1.81 | Distress | High bankruptcy risk (~80%) |
