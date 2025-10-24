# Financial Data Collection Tool

A Python tool to fetch and structure financial statements from the SEC EDGAR database. Handles the complexity of different company formats and row labels across various filings.

## Overview

This tool solves a critical problem: **different companies use different labels for the same financial items**. For example:
- One company might call it "Revenue", another "Sales", another "Total Revenue"
- Row formats change between years and quarters
- Different taxonomies (US-GAAP, IFRS) have different naming conventions

The tool uses **smart pattern matching** to:
1. Extract financial data from EDGAR HTML filings
2. Map company-specific row labels to standardized terms
3. Create consistent, comparable financial statements

## Features

- ✅ Fetch 10-K (annual) and 10-Q (quarterly) filings
- ✅ Extract Income Statements, Balance Sheets, and Cash Flow Statements
- ✅ Intelligent mapping using regex patterns for both GAAP taxonomy and human-readable labels
- ✅ Handle multiple currencies and unit conversions (dollars/thousands/millions)
- ✅ Parse calculation relationships from XML files
- ✅ CLI interface for easy testing
- ✅ Export to CSV for analysis

## Installation

### Prerequisites

```bash
python 3.8+
```

### Required Packages

```bash
pip install pandas numpy requests beautifulsoup4 lxml
```

## Usage

### Command Line Interface

#### Basic Usage

Fetch the latest annual (10-K) income statement for a ticker:

```bash
python main.py --ticker AAPL
```

#### Fetch Multiple Years

```bash
python main.py --ticker AAPL --years 3
```

#### Quarterly Data (10-Q)

```bash
python main.py --ticker AAPL --quarterly --years 4
```

#### Save to CSV

```bash
python main.py --ticker AAPL --years 5 --output ./data
```

#### Verbose Mode

```bash
python main.py --ticker AAPL --verbose
```

### Python API

```python
from Company import Company
from Filling import Filling

# Initialize company
company = Company(ticker="AAPL")

# Get latest filing
latest_filing = company.ten_k_fillings.iloc[0]

# Process the filing
filling = Filling(
    ticker="AAPL",
    cik=company.cik,
    acc_num_unfiltered=latest_filing,
    company_facts=company.company_facts
)

# Process income statement
filling.process_one_statement("income_statement")

# Access original data
original_df = filling.income_statement.og_df

# Access mapped/standardized data
mapped_df = filling.income_statement.get_mapped_df()

print(mapped_df)
```

## Architecture

### Core Components

```
scripts/
├── main.py                    # CLI entry point
├── Company.py                 # Company data fetcher (CIK, filings, facts)
├── Filling.py                 # Filing processor (extracts statements from HTML)
├── FinancialStatement.py      # Base classes for statements with mapping logic
├── statement_maps.py          # MapFact definitions with regex patterns
├── constants.py               # Constants (currencies, units, fact names)
├── dates.py                   # Date parsing utilities
├── healpers.py                # Helper functions
├── headers.py                 # HTTP headers for SEC requests
└── cal_xml.py                 # XML calculation parser
```

### Data Flow

```
1. User specifies ticker
   ↓
2. Company class fetches CIK and filing list from SEC
   ↓
3. Filling class downloads specific filing HTML
   ↓
4. Extract raw data:
   - Parse HTML tables
   - Extract row labels (GAAP taxonomy + human text)
   - Get calculation relationships from XML
   ↓
5. Map to standardized format:
   - Match patterns in FinancialStatement.map_facts()
   - Use MapFact objects with regex patterns
   ↓
6. Return structured DataFrame
```

### Mapping System

The mapping system uses **MapFact** objects that define:

```python
MapFact(
    fact="Total revenue",               # Standardized name
    gaap_pattern=[                      # GAAP taxonomy patterns
        r"(?i)\btotal\w*revenue\b",
        r"(?i)\brevenue\w*total\b"
    ],
    human_pattern=[                     # Human-readable patterns
        r"(?i)\btotal\s+revenue\b",
        r"(?i)\bnet\s+sales\b"
    ]
)
```

**Pattern Matching Process:**
1. First tries GAAP patterns against row index (e.g., "us-gaap_RevenueFromContractWithCustomerExcludingAssessedTax")
2. Then tries human patterns against display text (e.g., "Total Net Revenue")
3. Maps first match found to standardized fact name

## How It Handles Company Differences

### Example: Revenue Mapping

Different companies report revenue differently:

| Company | GAAP Taxonomy | Display Text |
|---------|---------------|--------------|
| Apple | us-gaap_RevenueFromContractWithCustomerExcludingAssessedTax | Net sales |
| Microsoft | us-gaap_Revenues | Total revenue |
| Amazon | us-gaap_SalesRevenueNet | Net product sales |

Our regex patterns catch all these variations:
```python
gaap_pattern=[r"(?i)\brevenue", r"(?i)\bsales"]
human_pattern=[r"(?i)\btotal\s+revenue", r"(?i)\bnet\s+sales"]
```

### Example: Unit Conversion

Companies report in different units:
- Company A: "in millions" → multiply by 1,000,000
- Company B: "in thousands" → multiply by 1,000
- Company C: actual dollars → multiply by 1

The tool:
1. Parses table headers for unit indicators
2. Cross-references with SEC companyfacts API for validation
3. Applies correct multiplier automatically

## Key Classes

### Company

Handles company-level data:
- Converts ticker to CIK
- Fetches all filings (10-K, 10-Q, etc.)
- Gets company facts from SEC API

```python
company = Company(ticker="AAPL")
# Access: company.cik, company.ten_k_fillings, company.company_facts
```

### Filling

Processes a single filing:
- Downloads HTML from EDGAR
- Extracts statement tables
- Parses dates, units, row classes
- Creates original DataFrame

```python
filling = Filling(ticker, cik, accession_number, company_facts)
filling.process_one_statement("income_statement")
```

### FinancialStatement (Base Class)

- `IncomeStatement`: Revenue, expenses, net income
- `BalanceSheet`: Assets, liabilities, equity (TODO)
- `CashFlow`: Operating, investing, financing activities (TODO)

Each has:
- `og_df`: Original DataFrame from EDGAR
- `mapped_df`: Standardized DataFrame
- `map_facts()`: Mapping logic
- `get_mapped_df()`: Returns mapped data

## Testing

### Quick Test

```bash
# Test with a well-known company
python main.py --ticker AAPL --years 1

# Test quarterly data
python main.py --ticker MSFT --quarterly --years 2

# Test with verbose logging
python main.py --ticker GOOGL --verbose
```

### Validation

The tool includes validation to check:
- Key facts are present (Revenue, Net Income)
- No duplicate mappings
- Reasonable value ranges

Access validation results:
```python
validation = income_statement.validate_mapped_df()
print(validation)
```

## Common Issues & Solutions

### Issue: Missing Headers

```
Error: Must include User-Agent in headers
```

**Solution**: Create `headers.py`:
```python
headers = {
    'User-Agent': 'Your Name your.email@example.com'
}
```

### Issue: Pattern Not Matching

If a fact isn't being mapped, check:
1. Print original row labels: `print(filling.income_statement.og_df.index)`
2. Print human text: `print(filling.income_statement.rows_text)`
3. Add new pattern to `statement_maps.py`

### Issue: Rate Limiting

SEC limits requests to 10 per second. The tool includes delays, but if you hit limits:
- Add longer delays between requests
- Process fewer filings at once

## Extending the Tool

### Add New Fact Mapping

Edit `statement_maps.py`:

```python
self.NewFact = MapFact(
    fact="My New Fact",
    gaap_pattern=[
        r"(?i)\bnew\w*fact\b"
    ],
    human_pattern=[
        r"(?i)\bnew\s+fact\b"
    ]
)
```

Add constant to `constants.py`:
```python
NewFact = "My New Fact"
```

### Implement Balance Sheet Mapping

Currently stubbed out. To implement:
1. Create `BalanceSheetMap` in `statement_maps.py`
2. Update `BalanceSheet.map_facts()` in `FinancialStatement.py`
3. Add validation for key balance sheet facts

## Project Structure (Old vs New)

### Old Structure (`old_scripts/`)
- Contains original working logic
- More complex with equations and master lists
- Used for reference

### New Structure (`scripts/`)
- Cleaner architecture
- Better separation of concerns
- Easier to extend and test

## Future Enhancements

- [ ] Implement balance sheet mapping
- [ ] Implement cash flow mapping
- [ ] Add equation validation (e.g., Revenue - COGS = Gross Profit)
- [ ] Support for IFRS taxonomy
- [ ] Multi-currency handling improvements
- [ ] Batch processing for multiple tickers
- [ ] Database storage option
- [ ] Web API endpoint

## Contributing

To add new features:
1. Review old_scripts/ for reference implementation
2. Add patterns to statement_maps.py
3. Update constants.py with new fact names
4. Test with multiple companies
5. Update README

## License

[Add your license here]

## Resources

- [SEC EDGAR Search](https://www.sec.gov/edgar/searchedgar/companysearch.html)
- [XBRL US GAAP Taxonomy](https://xbrl.us/xbrl-taxonomy/2021-us-gaap/)
- [SEC Company Facts API](https://www.sec.gov/edgar/sec-api-documentation)

## Support

For issues or questions, please check:
1. Verbose logging: `--verbose`
2. Original DataFrame: `filling.income_statement.og_df`
3. Mapping results: `filling.income_statement.mapped_facts`
