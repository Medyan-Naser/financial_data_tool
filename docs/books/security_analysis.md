# Security Analysis  

---

<!-- ## Table of Contents

1. Introduction & Philosophy  
2. Key Concepts  
   - Intrinsic Value & Margin of Safety  
   - Capitalization Rate & Discounting  
   - Forecasting & Normalized Earnings  
3. Adjustments & “Nonrecurring” Items  
4. Types of Reserves & Balance Sheet Cleansing  
5. Inventory, Depreciation & LIFO / FIFO Adjustments  
6. Ratio Frameworks  
   - Per-share Ratios  
   - Price / Market Ratios  
   - Profitability Ratios  
   - Growth / Stability Ratios  
   - Credit & Coverage Ratios  
   - Other Operational Ratios  
7. Valuation of Senior vs Equity Securities  
8. Earnings Manipulation & Distortions  
9. Practical Approach & Strategy  
10. Limitations, Critiques & Modern Relevance  
11. Summary & Key Takeaways   -->

---

## 1. Introduction & Philosophy

- *Security Analysis* was first published in 1934 (and later revised) and remains the foundational text for value investing and rigorous fundamental analysis.
- The central goal is not to predict the future perfectly, but to estimate a **reasonable intrinsic value** and to buy securities with a **margin of safety** so that errors, volatility, or unforeseeable events do less damage.
- A key axiom: the difference between **intrinsic value** and the **market price** is what creates investment opportunities or dangers. 
- In the short run, markets may behave like voting machines; in the long run, they tend to weigh true value.
- Analytical rigor, skepticism of optimistic forecasts, and focus on safety are hallmarks of this method.  

---

## 2. Key Concepts

### Intrinsic Value & Margin of Safety

- Intrinsic value is not a precise point but rather a **range or estimate** of what a security “ought to be worth” based on facts, adjusted judgments, and future projections. 
- The margin of safety is the buffer between intrinsic value and purchase price. It protects against estimation error, future surprises, or adverse developments. 
- Overconfidence in growth forecasts is dangerous; many of the most serious mistakes in investing come from excessive optimism about future trends.

### Capitalization Rate & Discounting

- Graham uses the concept of a **capitalization rate** (or “multiplier”) to relate normalized earnings (or dividends) to value. That is,  

  $$
  \text{Value} = \frac{\text{Normalized earnings}}{\text{Capitalization rate}}
  $$  

  or equivalently, earnings × (1 / cap rate).
- The capitalization rate is influenced by:  
  - The **quality, stability, and predictability** of the earnings stream  
  - The **long-term outlook** of the business or industry  
  - The **financial strength** (debt, balance sheet risk)  
  - The **management quality and record**  
  - The **dividend policy and payout consistency**
- Nominal interest rates (market rates) have two components:  
  1. A **real rate** reflecting supply of savings and demand for capital  
  2. An **inflation premium** (expected inflation)  
  - Credit or default risk also adds a further premium. (Your note on this is aligned with Graham’s views.)  
- Thus the cap rate is not static — changes in macro conditions, inflation expectations, interest rates, and risk perceptions affect it.

### Forecasting & Normalized Earnings

- Since any forecast is uncertain, Graham emphasizes using **“normalized earnings”** (i.e. smoothed over good and bad years) rather than simply extrapolating the last year’s number.
- Three conventional methods to forecast earnings:  
  1. Link aggregate market profits to total corporate profits (ex: S&P level)  
  2. Connect aggregate sales to GNP, then profits to sales  
  3. Use ROE logic:  
     $$
     \text{ROE} = (\text{Sales} / \text{Book Value}) \times (\text{Profit Margin})
     $$  
     and project these components forward  
- The payout ratio must also be estimated (how much of earnings will be distributed vs retained)  
- After forecasting normalized future earnings, apply the capitalization rate to estimate value  

---

## 3. Adjustments & “Nonrecurring” Items

To get to clean, sustainable earnings, many adjustments are needed. Some of the usual items that should be stripped or adjusted:

### Past / prior years:

- Tax adjustments, forgiveness, or large nonrecurring tax items  
- Litigation losses, claims, settlement costs  
- Changes in accounting policies or estimates  
- Prior period restatements or corrections  

### In the current year:

- Gains/losses on the sale of fixed assets or investments (if non-core)  
- Discontinued operations or segments  
- Write-ups or write-downs of investments or foreign assets  
- Insurance gains or life insurance proceeds  
- Unusual or infrequent items:  
  - If both unusual *and* infrequent (extraordinary), these should appear below “net income” and shown net of tax  
  - If either unusual or infrequent (but not both), present them above net income, without tax effect, and disclose them  

For each adjustment, the related tax effect (or deferred tax consequences) must also be considered.

---

## 4. Types of Reserves & Balance Sheet Cleansing

Reserves are provisions or allowances created for various future contingencies. Graham classifies three types:

1. **Valuation accounts** – e.g. allowances on receivables, inventory reserves  
2. **Liabilities (reserves)** – uncertain future liabilities or contingencies  
3. **Reserves for future development** – e.g. R&D reserves, or provisions for product development losses  

When such reserves or provisions are adjusted (increased or decreased), the balance sheet and income statement both change:

- A reserve creation may reduce equity (or increase liabilities)  
- If reserves are released, equity or income may be boosted  
- Assets may be reduced or revalued  

A key insight: clean up these reserves to avoid “hidden cushions” that obscure the true financial position.

---

## 5. Inventory, Depreciation & LIFO/FIFO Adjustments

These topics are among the more technical but are extremely important in real-world accounting distortions:

- **Lower of cost or market** is the standard rule for inventory (i.e. value it at whichever is lower).  
- Depreciation methods — the idea is to systematically expense the cost minus salvage over useful life (or by rational, justified methods).  
- Under inflation, **inventory profits** can arise: older, cheaper inventory is sold at higher prices.  
- **LIFO vs FIFO**:  
  - When costs are rising, FIFO often shows **higher profit**, but leads to paying higher taxes.  
  - When costs decline, FIFO might understate profit (your note about “layer invasion”)  
- If a company uses LIFO, an **adjustment** must be made: the **LIFO reserve** is the difference between FIFO inventory and LIFO inventory.  
  - Add that reserve back (net of tax) to capital in denominator when calculating return ratios  
  - Ensure consistency of numerator (earnings) and denominator (capital) in ratio calculations  

Correcting for LIFO gives a truer picture of underlying earnings and capital.

---

## 6. Ratio Frameworks

One of the strengths of *Security Analysis* is the systematic listing of ratios. Below is a cleaned, categorized version of your notes, with commentary:

### a) Per-share Ratios

1. **Earnings per Share (EPS)** = Earnings available to common / weighted average common shares  
2. **Dividend per Share** = Total dividends to common / weighted average shares  
3. **Sales per Share** = Sales / weighted average shares  
4. **Cash Flow per Share** = Operating cash flow after taxes / weighted average shares  
5. **Book Value per Share** = (Book equity – goodwill – most intangibles) / shares  
6. **Current Assets per Share** = (Current assets – claims senior to common) / shares  
7. **Quick Assets per Share** = (Cash + receivables – senior claims) / shares  
8. **Cash per Share** = (Cash – senior claims) / shares  

These help anchor per-share value metrics in clean accounting.

### b) Price / Market Ratios

9. **Price / Earnings (P/E)** = Price per share / EPS  
10. **Earnings yield** = EPS / Price  
11. **Dividend yield** = Dividend per share / Price  
12. **Sales per dollar of common (market)** = Sales / (shares × price)  
13. **Price / Book** = Price per share / Book value per share  

These ratios link market valuation to fundamentals.

### c) Profitability Ratios

14. **Return on Capital** = (Net income + minority interest + interest (tax-adjusted)) / (Tangible assets – short-term accrued payables)  
15. **Capital Turnover** = Sales / (Tangible assets – short-term accrued payables)  
16. **Earning Margin** = (Net income + minority interest + tax-adjusted interest) / Sales  
17. **Return on Capital before Depreciation** = (Net income + minority interest + tax-adjusted interest + depreciation) / (Tangible assets – short-term accrued payables)  
18. **Return on Common Equity** = (Net income – preferred dividends) / (Common equity – goodwill – most intangibles + deferred tax liability)  

These measure how well the company uses its capital and equity.

### d) Growth / Stability / Payout Ratios

19. **Growth in Sales** = (Sales final period) / (Sales base period)  
20. **Growth in Total Return** = (Net earned on total capital final) / (Net earned base)  
21. **Growth in EPS** = (EPS final period) / (EPS base period)  
22. **Maximum decline in coverage of senior charges** = Worst year / average of previous three years  
23. **Percent decline in return on capital** = Worst year / average of previous three years  
24. **Payout Ratio** = Dividend on common / Net income available for common  
25. **Dividend to Cash Flow** = Dividend / Cash flow from operations  

These measure how stable and sustainable growth and payouts are, and worst-case sensitivities.

### e) Credit & Coverage Ratios

26. **Current Ratio** = Current assets / Current liabilities  
27. **Quick Ratio** = (Current assets – inventories) / Current liabilities  
28. **Cash Ratio** = Cash items / Current liabilities  
29. **Equity Ratio** = Common equity (book) / (Tangible assets – accrued payables)  
30. **Equity Ratio (market)** = Market equity / (Tangible assets – accrued payables)  
31. **Coverage of Senior Charges** = Pre-tax earnings for capital / Senior charges  
32. **Cash Flow Coverage of Senior Charges** = (Operating cash flow after taxes + senior charges) / Senior charges  
33. **Cash Flow to Total Capital** = (Operating cash flow after taxes + tax-adjusted interest) / (Tangible assets – accrued payables)  
34. **Total Debt Service Coverage** = (Operating cash flow after taxes + tax-adjusted interest) / (Interest + rent + current maturities + sinking fund payments)  
35. **Defensive Interval in Days** = (Cash + receivables) × 365 / (Operating expenses – depreciation – other noncash charges)  

These measure liquidity, solvency, and coverage risk.

### f) Other Operational Ratios

36. **Depreciation to Sales** = Depreciation / Sales  
37. **Depreciation to Gross Plant** = Depreciation / Gross plant  
38. **Inventory Turnover** = Cost of goods sold / (Inventory including LIFO reserve)  
39. **Accounts Receivable Turnover** = Sales / Accounts receivable  

These help reveal operational efficiency and hidden distortions.

---

## 7. Valuation of Senior vs Equity Securities

Graham classifies securities broadly into two groups:

- **Senior securities**  
  1. Fixed value securities (e.g. bonds, preferred stock held to maturity)  
  2. Variable value securities (e.g. convertible bonds, preferred, or bonds that may be sold before maturity)  

- **Equity / common securities**  
  These have greater risk and variability, so valuation needs to be more cautious, and margin of safety is especially crucial.

In valuing senior securities, safety, coverage, and asset backing are dominant. For equity, growth, stability, earnings power, and reinvestment prospects are more critical.

---

## 8. Earnings Manipulation & Distortions

Graham warns against various techniques through which management can distort “reported earnings.” Some common distortions:

1. Accelerating depreciation (unduly aggressive)  
2. Decelerating depreciation  
3. Capitalizing normal operating expenses (i.e. moving current expenses to balance sheet)  
4. Labeling ordinary items as “extraordinary” to exclude them  
5. Premature revenue recognition  
6. Deferring or shifting current expenses into future periods  

Because of these, the analyst must scrutinize footnotes, accounting policies, consistency, and management incentives.

One practical rule: buy stocks whose reported **current assets alone** exceed the market price (i.e. price < net current assets). That gives a margin of safety in a liquidation sense.

---

## 9. Practical Approach & Strategy

- The analyst should first **clean and restate** financials (strip out nonrecurring items, adjust reserves, normalize earnings)  
- Then use multiple valuation approaches (multiples, dividend-based, net-asset based, etc.) to triangulate value  
- Always build in **conservatism** — avoid stretching assumptions  
- Look for **discrepancies** between intrinsic value and market price  
- Diversify, but not excessively dilute one’s best ideas  
- Be patient — it often takes time for the market to “correct” mispricings  
- Recognize that pure analysis cannot capture all risks; fund management, business cycles, regulatory, etc. must be considered  
- Don’t overestimate one’s forecasting ability — better to err on safety than speculative optimism  

In his later life, Graham himself observed that for many securities, the cost of deep analysis may outweigh the incremental benefit versus simpler screening or diversification strategies.

---

## 10. Limitations, Critiques & Modern Relevance

- Forecasting is inherently uncertain; Graham cautioned strongly about overreliance on projections.
- Many accounting standards have evolved since Graham’s era; modern financials (IFRS, GAAP) have new complexities (e.g. lease accounting, fair value, off-balance sheet items).  
- Some sectors today (technology, intangible-heavy businesses) depart from the capital-intensive models Graham often assumed.  
- The idea of efficient markets and quantitative factor investing has challenged pure fundamental approaches.  
- Nonetheless, many core principles — margin of safety, skepticism, adjusting for anomalies, understanding capital structure — remain deeply relevant.

---

## 11. Summary & Key Takeaways

- The central task is estimating intrinsic value based on adjusted earnings / cash flows and applying a realistic capitalization rate  
- Always insist on a **margin of safety**, because forecasts will err  
- Scrub the financials — remove one-time items, correct accounting peculiarities, adjust reserves  
- Use a broad set of ratios to test consistency, performance, stability, coverage, and growth  
- Be conservative in assumptions, especially for pessimistic cases  
- Recognize that simple rules (e.g. price < current assets) sometimes offer striking safety  
- Be mindful of limitations of analysis and evolving accounting / business realities  
- Price is what you pay; value is what you get — and the gap between the two is where opportunity lies  

---
