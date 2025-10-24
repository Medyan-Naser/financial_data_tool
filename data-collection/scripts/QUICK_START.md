# Quick Start Guide

Get started with the Financial Data Collection Tool in 5 minutes.

## Prerequisites

1. **Python 3.8+** installed
2. **Required packages:**
   ```bash
   pip install pandas numpy requests beautifulsoup4 lxml
   ```

3. **Create headers.py** (SEC requires User-Agent):
   ```python
   # headers.py
   headers = {
       'User-Agent': 'Your Name your.email@example.com'
   }
   ```

## First Run

### Option 1: Command Line (Easiest)

```bash
# Navigate to the scripts directory
cd /Users/medyan/Desktop/projects/stock_analysis/financial_data_tool/data-collection/scripts

# Fetch Apple's latest income statement
python main.py --ticker AAPL
```

You should see output like:
```
================================================================================
                     AAPL - Income Statement - 2024-09-28                      
================================================================================
                                          2024-09-28  2023-09-30  2022-09-24
Total revenue                            391,035.00  383,285.00  394,328.00
COGS                                    -210,352.00 -214,137.00 -223,546.00
Gross profit                             180,683.00  169,148.00  170,782.00
...
```

### Option 2: Python Script

```python
# quick_test.py
from Company import Company
from Filling import Filling

# Fetch Apple data
company = Company(ticker="AAPL")
latest_filing = company.ten_k_fillings.iloc[0]

# Process the filing
filling = Filling(
    ticker="AAPL",
    cik=company.cik,
    acc_num_unfiltered=latest_filing,
    company_facts=company.company_facts
)

# Get income statement
filling.process_one_statement("income_statement")
mapped_df = filling.income_statement.get_mapped_df()

# Display
print(mapped_df)
```

Run it:
```bash
python quick_test.py
```

### Option 3: Interactive Examples

```bash
# Run the example script
python example.py
```

This demonstrates:
- Basic usage
- Company comparisons
- Mapping details
- Time series analysis

## Understanding the Output

### Original vs Mapped Data

**Original Data** (`og_df`):
- Raw data from EDGAR filing
- Company-specific row labels
- Example: `us-gaap_RevenueFromContractWithCustomerExcludingAssessedTax`

**Mapped Data** (`mapped_df`):
- Standardized row labels
- Consistent across all companies
- Example: `Total revenue`

### Common Commands

```bash
# Get 3 years of data
python main.py --ticker AAPL --years 3

# Save to CSV
python main.py --ticker AAPL --output ./data

# Quarterly data
python main.py --ticker AAPL --quarterly --years 4

# Debug mode
python main.py --ticker AAPL --verbose
```

## Test Different Companies

Try these to see how the tool handles different formats:

```bash
# Tech companies
python main.py --ticker MSFT
python main.py --ticker GOOGL
python main.py --ticker META

# Retail
python main.py --ticker WMT
python main.py --ticker TGT

# Finance
python main.py --ticker JPM
python main.py --ticker BAC
```

Each company uses different labels, but the tool maps them to the same standardized format!

## Troubleshooting

### Issue: "Must include User-Agent"

Create `headers.py`:
```python
headers = {
    'User-Agent': 'FirstName LastName your.email@domain.com'
}
```

### Issue: "Ticker not found"

Make sure the ticker is valid and uses the correct symbol. Check on [SEC EDGAR](https://www.sec.gov/edgar/searchedgar/companysearch.html).

### Issue: "No data returned"

Some companies might not have recent filings. Check:
```python
company = Company(ticker="TICKER")
print(company.ten_k_fillings)  # See available filings
```

### Issue: Rate limiting

SEC limits to 10 requests/second. If processing many companies, add delays between requests.

## Next Steps

1. **Read the full README.md** for detailed documentation
2. **Check example.py** for more advanced usage patterns
3. **Explore the code** to understand the mapping logic:
   - `statement_maps.py` - Pattern definitions
   - `FinancialStatement.py` - Mapping logic
   - `Filling.py` - Data extraction

## Quick Reference Card

| Task | Command |
|------|---------|
| Single company, latest year | `python main.py --ticker AAPL` |
| Multiple years | `python main.py --ticker AAPL --years 3` |
| Quarterly data | `python main.py --ticker AAPL --quarterly` |
| Save to CSV | `python main.py --ticker AAPL --output ./data` |
| Debug mode | `python main.py --ticker AAPL --verbose` |
| Python API | See example.py |

## Getting Help

- Check the main **README.md** for detailed documentation
- Review **example.py** for code samples
- Enable `--verbose` flag to see detailed logging
- Check the original `old_scripts/` directory for reference implementation

## Success Indicators

You'll know it's working when you see:
1. ✅ Filing downloaded successfully
2. ✅ Statement extracted
3. ✅ Rows mapped (check "Successfully mapped X out of Y rows")
4. ✅ Key facts present (Revenue, Net Income)

Example output:
```
2024-01-15 10:30:45 - INFO - Fetching financial data for AAPL...
2024-01-15 10:30:46 - INFO - Company CIK: 0000320193
2024-01-15 10:30:46 - INFO - Found 15 filings
2024-01-15 10:30:47 - INFO - Processing Income Statement...
2024-01-15 10:30:48 - INFO - Successfully mapped 25 out of 45 rows
```

## Ready to Go!

You're all set. Start with:

```bash
python main.py --ticker AAPL
```

Happy data collecting! 📊
