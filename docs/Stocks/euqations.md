# Financial Equations & Formulas

This document contains all financial equations and formulas used in the stock analysis system.

## Profitability Ratios

### Gross Profit Margin
```
Gross Profit Margin = (Total Revenue - COGS) / Total Revenue × 100
```
Measures the percentage of revenue retained after direct production costs.

### Net Profit Margin
```
Net Profit Margin = Net Income / Total Revenue × 100
```
Measures overall profitability after all expenses.

### Return on Assets (ROA)
```
ROA = Net Income / Total Assets × 100
```
Measures how efficiently a company uses its assets to generate profit.

### Return on Equity (ROE)
```
ROE = Net Income / Shareholders' Equity × 100
```
Measures return generated on shareholders' investment.

## Liquidity Ratios

### Current Ratio
```
Current Ratio = Current Assets / Current Liabilities
```
- **> 2.0**: Strong liquidity
- **1.0 - 2.0**: Adequate liquidity
- **< 1.0**: Potential liquidity issues

### Quick Ratio (Acid Test)
```
Quick Ratio = (Current Assets - Inventory) / Current Liabilities
```
More conservative measure excluding less-liquid inventory.

## Solvency Ratios

### Debt-to-Equity Ratio
```
D/E Ratio = Total Liabilities / Shareholders' Equity
```
- **< 1.0**: Conservative financing
- **1.0 - 2.0**: Moderate leverage
- **> 2.0**: High leverage (higher risk)

### Debt-to-Assets Ratio
```
Debt-to-Assets = Total Liabilities / Total Assets
```
Percentage of assets financed by debt.

## Efficiency Ratios

### Asset Turnover
```
Asset Turnover = Total Revenue / Total Assets
```
Measures how efficiently assets generate revenue.

### Inventory Turnover
```
Inventory Turnover = COGS / Average Inventory
```
How many times inventory is sold and replaced per period.

## Valuation Ratios

### Earnings Per Share (EPS)
```
EPS Basic = Net Income / Weighted Average Shares Outstanding (Basic)
EPS Diluted = Net Income / Weighted Average Shares Outstanding (Diluted)
```

### Price-to-Earnings (P/E)
```
P/E Ratio = Stock Price / Earnings Per Share
```

## Altman Z-Score (Bankruptcy Prediction)

The Z-Score formula for public manufacturing companies:

```
Z = 1.2×X₁ + 1.4×X₂ + 3.3×X₃ + 0.6×X₄ + 1.0×X₅
```

Where:
- **X₁** = Working Capital / Total Assets
- **X₂** = Retained Earnings / Total Assets
- **X₃** = EBIT / Total Assets
- **X₄** = Market Value of Equity / Total Liabilities
- **X₅** = Sales / Total Assets

### Z-Score Interpretation
| Score | Zone | Probability of Bankruptcy |
|-------|------|---------------------------|
| Z > 2.99 | Safe Zone | ~5% within 2 years |
| 1.81 < Z < 2.99 | Grey Zone | ~20% within 2 years |
| Z < 1.81 | Distress Zone | ~80% within 2 years |

