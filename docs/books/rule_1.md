# Rule #1 — Notes & Guide

---

## 1) Quick overview

*Rule #1* is a value-investing approach that teaches how to find "wonderful companies" (companies with durable competitive advantages — "moats"), calculate an intrinsic value called the **Sticker Price**, use technical tools to time buys/sells, and apply strict risk rules (margin of safety, liquidity, and discipline).

---

## 2) The five types of moats (short definitions)

1. **Brand** — customers prefer and will pay more for the product (trust, reputation, lifestyle).
2. **Secret** — legal or technical protection like patents, trade secrets, or proprietary processes.
3. **Toll** — control of a market/channel so the company can collect fees or otherwise restrict access.
4. **Switching** — product/service so embedded that changing is costly or inconvenient for customers.
5. **Price** — cost advantage that allows undercutting competitors while remaining profitable.

> When assessing companies, look for evidence that one or more of these moats are real, durable, and meaningful.

---

## 3) The "Big Five" — moat confirmation metrics

Phil Town uses five growth/return metrics ("Big Five") as a quick quantitative check for a moat. Ideally, these should each average **≥ 10% per year** over the past 10 years:

- **Return on Invested Capital (ROIC)** — how efficiently the company turns capital into returns.
- **Sales (revenue) growth rate** — revenue expansion over time.
- **Earnings per share (EPS) growth rate** — profit growth allocated to shareholders.
- **Book value per share (BVPS / Equity per share) growth rate** — balance-sheet growth.
- **Free cash flow (FCF) growth rate** — cash available after operating and capital expenses.

If one of these is weak or inconsistent, investigate further (see Cash Flow section below).

---

## 4) Sticker Price (intrinsic value) — step-by-step

**What you need:**

1. Current EPS (earnings per share).
2. An estimated (future) EPS growth rate (use the company's past **equity** growth rate as your best proxy when possible).
3. An estimated future PE (price-to-earnings) multiple for the target year.
4. A minimum acceptable annual rate of return (Phil Town uses **15%** as his target).

**Steps:**

1. Project **future EPS**: `future_EPS = current_EPS * (1 + g)^n` where `g` = estimated annual EPS growth, `n` = years (Rule #1 commonly projects 10 years).
2. Estimate **future market price**: `future_market_price = future_EPS * estimated_future_PE`
3. Convert future market price back to today for your required return (Rule One often uses calculators that determine the target **Sticker Price** so that the investment returns 15% per year over the period). Practically, the common shorthand in Rule #1 materials: `Sticker Price = future_EPS * future_PE` and then apply the required return / margin-of-safety rules from there.

**Extra guidance:**

- Use the company’s **equity (book value) growth** as a better guide for sustainable growth than short-term EPS swings.
- For **future PE**, a rule of thumb in the book is to use a number related to the expected growth (some readers use ~2× growth rate as a quick proxy) but always check historical PE ranges and sector norms.
- After computing the Sticker Price, Rule #1 commonly uses a **Margin of Safety (MOS)** — often expressed as buying at **50% of Sticker Price** (or another safe fraction) to protect against estimation error.

**Example (illustrative):**

```
current_EPS = $2.00
estimated_growth = 12% per year
n = 10 years
future_EPS = 2 * (1.12)^10 ≈ 6.21
estimated_future_PE = 15
sticker_price ≈ 6.21 * 15 = $93.15
margin_of_safety_buy_price (50%) = $46.58
```

---

## 5) Technical tools for timing (three tools)

Phil Town recommends three technical indicators to help time entries and exits (used only after you’ve verified the company is fundamentally sound and priced below your Sticker Price):

1. **MACD (Moving Average Convergence Divergence)**
   - MACD is the difference between a short EMA and a long EMA. Town prefers a faster setting he finds better for his style (commonly reported as **8–17–9** in Rule #1 commentary rather than the classic 12–26–9).
   - Plot MACD and a trigger (signal) line (a short EMA of the MACD, e.g., 9-day). Buy signals are when MACD crosses **above** the signal line; sell signals the opposite.

2. **Stochastics (momentum / overbought-oversold)**
   - Measures where the current close sits within the high-low range over a lookback (book recommends 14 for the %K window).
   - A smoothed moving average of the %K (often %D) is used as a trigger (book recommends a 5-period smoothing).
   - When the %K crosses above %D from low territory, it’s a momentum buy; crossing below from high territory is a sell.

3. **Moving averages (market psychology)**
   - Simple or exponential moving averages smooth price action (book recommends tracking a 10-day MA for short-term timing).
   - If price crosses above the moving average, it’s bullish; if it crosses below, it’s bearish.

**Important:** These are **timing tools** — they do not replace the fundamental analysis. Use them to help avoid buying at the top or selling into panic.

---

## 6) Cash flow vs Free cash flow

- If **Free Cash Flow** (FCF) is volatile or hard to predict, Rule #1 suggests checking **Operating Cash Flow** as a more stable indicator of cash generated from core operations before large capital expenditures or dividend payouts.
- Operating Cash Flow growing year-to-year is a good sign; it can act as a substitute when FCF is inconsistent.

---

## 7) Liquidity guideline

Phil Town suggests a practical liquidity cutoff: prefer stocks that trade **at least ~500,000 shares/day** on average. The idea is to avoid illiquid names where large orders (yours or others’) move the price dramatically.

---

## 8) Practical checklist (to apply Rule #1 using your highlights)

1. Does the company have a clear moat (one or more of the five types)?
2. Do the Big Five metrics average ≥ 10% over the past 10 years? If not, why?
3. Is current EPS, and projected future EPS (using a conservative growth estimate), reasonable and backed by company fundamentals (use equity/book growth as a sanity check)?
4. Estimate a future PE (compare sector & historical PEs). Compute Sticker Price and your MOS buy price.
5. Check cash flow stability — operating cash flow if FCF is erratic.
6. Check liquidity — average daily volume ≥ ~500k shares.
7. Use MACD + Stochastics + Moving Average for timing entries/exits (don’t buy unless technicals aren’t screaming sell).
8. Confirm management honesty, sensible capital allocation, and reasonable debt levels.

---

## 9) Common pitfalls & notes

- **Relying solely on historical EPS** can mislead; Town recommends looking at equity/book growth as a steadier measure of business growth.
- **Technical indicators are tools, not rules** — they can give false signals; keep fundamentals first.
- **Estimations vary widely** — the Sticker Price is only as reliable as your growth and multiple assumptions. Use a conservative approach and wide MOS.

---

## 10) Suggested next actions

- Convert your favorite companies into the checklist above and compute Sticker Price + MOS for each.
- Keep a simple spreadsheet tracking the Big Five annually and technical signals so you can compare reality vs assumptions.

---
