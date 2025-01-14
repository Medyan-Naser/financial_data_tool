# constants for thousand def
# IN_DOLLARS = 1/1000
# IN_THOUSANDS = 1
# IN_MILLIONS = 1000

# constants for dollar def
IN_DOLLARS = 1
IN_THOUSANDS = 1000
IN_MILLIONS = 1000000

# taxonimy
GAAP = "us-gaap"
IFRS = "ifrs-full"

# sections
FIRST_SECTION = "FIRST SECTION"

# currencies
USD = "USD"
USD_sign = "$"
CAD = "CAD"
CAD_sign = "$"
EUR = "EUR"
EUR_sign = "€"
CNY = "CNY"
CNY_sign = "¥"
# India
INR = "INR"
INR_sign = "₨"

currency_keys = [USD, CAD, EUR, CNY, INR]
currency_map = {USD: USD_sign, CAD: CAD_sign   , EUR: EUR_sign, CNY: CNY_sign, INR: INR_sign}

keep_value_unchanged = ['us-gaap_EarningsPerShareDiluted', 'us-gaap_EarningsPerShareBasic', 'us-gaap_WeightedAverageNumberOfSharesOutstandingBasic', 'us-gaap_WeightedAverageNumberOfDilutedSharesOutstanding']


statement_keys_map = {
    "balance_sheet": [
        "balance sheet",
        "balance sheets",
        "statement of financial position",
        "consolidated balance sheets",
        "consolidated balance sheet",
        "consolidated financial position",
        "consolidated balance sheets - southern",
        "consolidated statements of financial position",
        "consolidated statement of financial position",
        "consolidated statements of financial condition",
        "combined and consolidated balance sheet",
        "condensed consolidated balance sheets",
        "consolidated balance sheets, as of december 31",
        "dow consolidated balance sheets",
        "consolidated balance sheets (unaudited)",
        "Consolidated Statements of Financial Position",
    ],
    "income_statement": [
        "income statement",
        "income statements",
        "statement of earnings (loss)",
        "statement of income",
        "statement of comprehensive income",
        "statements of consolidated income",
        "statements of consolidated comprehensive income",
        "statements of operations",
        "consolidated statements of operations",
        "consolidated statement of operations",
        "consolidated statements of earnings",
        "consolidated statement of earnings",
        "consolidated statements of income",
        "consolidated statement of income",
        "combined and consolidated statement of income",
        "consolidated income statements",
        "consolidated income statement",
        "consolidated statement of comprehensive income",
        "condensed consolidated statements of earnings",
        "consolidated results of operations",
        "consolidated statements of income (loss)",
        "consolidated statements of income - southern",
        "consolidated statements of operations and comprehensive income",
        "consolidated statements of comprehensive income",
        "consolidated statements of operations and comprehensive loss",
        "CONSOLIDATED STATEMENTS OF OPERATIONS AND COMPREHENSIVE LOSS",
        "consolidated statements of comprehensive loss",
        "Consolidated Statements of Comprehensive (Loss) Income",
        "Consolidated and Combined Statements of Income",
        "Consolidated Statements of Net Earnings",
        "Consolidated Statements of Net Earnings (Loss)",
        "Consolidated and Combined Statements of (Loss) Income",
        # quaesinable
        "consolidated statements of profit",
    ],
    "cash_flow_statement": [
        "cash flows statement",
        "cash flows statements",
        "statement of cash flows",
        "statements of consolidated cash flows",
        "consolidated statements of cash flows",
        "consolidated statement of cash flows",
        "consolidated statement of cash flow",
        "consolidated cash flows statements",
        "consolidated cash flow statements",
        "condensed consolidated statements of cash flows",
        "consolidated statements of cash flows (unaudited)",
        "consolidated statements of cash flows - southern",
    ],
}


## income statement
GrossProfit = 'Gross profit'
OperatingIncome = 'Operating income'
EBT = 'EBT'
NetIncome = 'Net income'
NetIncome_with_unusal_items_1 = 'Net income including unusal items 1'
NetIncome_with_unusal_items_2 = 'Net income including unusal items 2'
NetIncome_with_unusal_items_3 = 'Net income including unusal items 3'
NetIncome_with_unusal_items_4 = 'Net income including unusal items 4'
TotalRevenue= 'Total revenue'
TotalOperatingExpense = 'Total operating expense'
TotalCostAndExpenses = 'C&E'
MinorityInterest = 'Minority Interest'


## Balance sheet
# Fact const
# Assets
CashAndCashEquivalent = "Cash And Cash Equivalen"
RestrictedCash = "Restricted Cash"
Goodwill = "Goodwill"
AccountsReceivable = "Accounts Receivable"
IntangibleAssets = "Intangible Assets"
OtherAssetsCurrent = "Other Assets Current"
CurrentAssets = "Current Assets"
OtherAssetsNoncurrent = "Other Assets Noncurrent"
NonCurrentAssets = "Non Current Assets"
OtherAssets = "Other Assets"
TotalAssets = "Total Assets"

#Liabilities
AccountsPayable = "Accounts Payable"
PropertyPlantAndEquipment = "Property Plant And Equipment"
ShortTermDebtCurrent = "Current portion of Short Term Debt"
LongTermDebtCurrent = "Current portion of Long Term Debt"
ShortTermDebt = "Short Term Debt"
LongTermDebt = "Long Term Debt"
DeferredTaxLiabilityNonCurrent = "Deferred Tax Liability Non Current"
LiabilitiesCurrent = "Current Liabilities"
OtherLiabilitiesNoncurrent = "Other Liabilities Non current"
NonLiabilitiesCurrent = "Non Current Liabilities"
OtherLiabilities = "Other Liabilities"
TotalLiabilities = "Total Liabilities"

RetainedEarnings = "Retained Earnings"

# equity
StockholdersEquity = "Stockholders Equity"
TotalEquity = "Total Equity"
TotalLiabilitiesAndEquity = "Total Liabilities And Equity"
