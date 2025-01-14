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
EUR = "EUR"
EUR_sign = "€"
CNY = "CNY"
CNY_sign = "¥"
# India
INR = "INR"
INR_sign = "₨"

currency_keys = [USD, EUR, CNY, INR]
currency_map = {USD: USD_sign, EUR: EUR_sign, CNY: CNY_sign, INR: INR_sign}

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
