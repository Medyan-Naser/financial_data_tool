"""
COMPREHENSIVE FINANCIAL STATEMENT MAPPING SYSTEM

This file contains extensive pattern matching for all three financial statements.
Designed to handle variations across companies, taxonomies (US-GAAP, IFRS), and reporting styles.

MATCHING STRATEGY:
1. High-priority exact matches (Revenue, Net Income, Total Assets)
2. GAAP taxonomy patterns
3. IFRS taxonomy patterns  
4. Human-readable patterns
5. Fuzzy/flexible patterns for edge cases

USAGE:
  from statement_maps import IncomeStatementMap, BalanceSheetMap, CashFlowMap
  inc_map = IncomeStatementMap()
  # Access individual MapFact objects: inc_map.TotalRevenue
"""

from constants import *
import re


# Common income patterns used across multiple items
GAAP_INCOME_PATTERNS = [
    r"(?i)\bOperatingIncome[LoLosss]*\b",
    r"(?i)\bProfitLoss\b",
    r"(?i)\bNetIncomeLoss\b",
    r"(?i)\bIncomeLossFromContinuingOperations\b",
    r"(?i)\bComprehensiveIncomeNet\b",
]


class MapFact:
    """
    Represents mapping between company-specific terms and standardized financial terms.
    
    Args:
        fact: Standardized fact name (e.g., "Total revenue")
        gaap_pattern: List of regex patterns for US-GAAP taxonomy
        ifrs_pattern: List of regex patterns for IFRS taxonomy  
        human_pattern: List of regex patterns for human-readable labels
        priority: Matching priority (1-10, higher = match first)
        strict_compare: If True, require exact string match
    """
    
    def __init__(self, fact, gaap_pattern=[], ifrs_pattern=[], human_pattern=[], 
                 priority=5, strict_compare=False):
        self.fact = fact
        self.gaap_pattern = gaap_pattern if isinstance(gaap_pattern, list) else [gaap_pattern]
        self.ifrs_pattern = ifrs_pattern if isinstance(ifrs_pattern, list) else [ifrs_pattern]
        self.human_pattern = human_pattern if isinstance(human_pattern, list) else [human_pattern]
        self.priority = priority
        self.strict_compare = strict_compare
        # Runtime attributes
        self.index = None
        self.matches = []
        self.match = None
        self.master = None


#########################################
# INCOME STATEMENT MAPPING
#########################################

class IncomeStatementMap:
    """
    Comprehensive Income Statement mapping covering:
    - Revenue (all variations)
    - Cost of goods/services
    - Operating expenses (SG&A, R&D, D&A, etc.)
    - Operating income
    - Non-operating items (interest, gains/losses, FX)
    - Pre-tax income
    - Taxes
    - Net income
    - EPS and shares
    """
    
    def __init__(self):
        
        # ==================== REVENUE ====================
        self.TotalRevenue = MapFact(
            fact=TotalRevenue,
            priority=10,
            gaap_pattern=[
                r"(?i)\bRevenues?\b",
                r"(?i)\bSalesRevenueNet\b",
                r"(?i)\bRevenueFromContractWithCustomer\w*\b",
                r"(?i)\bSalesRevenueGoodsNet\b",
                r"(?i)\bSalesRevenueServicesNet\b",
                r"(?i)\bRevenueNet\b",
                r"(?i)\bNetSales\b",
            ],
            ifrs_pattern=[
                r"(?i)\bRevenue\b",
                r"(?i)\bTurnover\b",
            ],
            human_pattern=[
                r"(?i)^total\s+(net\s+)?revenues?\b",
                r"(?i)^(net\s+)?revenues?\b",
                r"(?i)^(net\s+)?sales\b",
                r"(?i)^total\s+sales\b",
            ]
        )
        
        # ==================== COST OF REVENUE ====================
        self.COGS = MapFact(
            fact=COGS,
            priority=9,
            gaap_pattern=[
                # Cost of goods
                r"(?i)\bCostOfGoodsAndServicesSold\b",
                r"(?i)\bCostOfGoodsSold\b",
                r"(?i)\bCostOfGoods\b",
                # Cost of revenue/sales  
                r"(?i)\bCostOfRevenue\b",  # Google uses this
                r"(?i)\bCostOfSales?\b",
                r"(?i)\bCostOfServices\b",
                # Product/service costs
                r"(?i)\bCostOfProduct\b",
                r"(?i)\bCostOfGoodsAndServicesExcluding\b",
            ],
            ifrs_pattern=[
                r"(?i)\bCostOfSales\b",
            ],
            human_pattern=[
                r"(?i)^cost\s+of\s+(goods\s+and\s+services\s+sold|goods\s+sold|revenue|sales)\b",
                r"(?i)^cost\s+of\s+(goods|sales|revenue|services)\b",
                r"(?i)^costs?\s+of\s+sales?\b",  # Apple uses "Cost of sales"
                r"(?i)^cost\s+of\s+revenues?\b",  # Google uses "Cost of revenues"
            ]
        )
        
        # ==================== GROSS PROFIT ====================
        self.GrossProfit = MapFact(
            fact=GrossProfit,
            priority=8,
            gaap_pattern=[
                r"(?i)\bGrossProfit\b",
                r"(?i)\bGrossMargin\b",
            ],
            ifrs_pattern=[
                r"(?i)\bGrossProfit\b",
            ],
            human_pattern=[
                r"(?i)^gross\s+(profit|margin|income)\b",
                r"(?i)^gross\s+margin\b",  # Apple uses "Gross margin"
                r"(?i)^gross\s+income\b",
            ]
        )
        
        # ==================== OPERATING EXPENSES ====================
        self.SGnA = MapFact(
            fact=SGnA,
            priority=7,
            gaap_pattern=[
                r"(?i)\bSellingGeneralAndAdministrativeExpense\b",
                r"(?i)\bGeneralAndAdministrativeExpense\b",  # Google splits into separate items
                r"(?i)\bSellingAndMarketingExpense\b",  # Google uses this separately
            ],
            human_pattern=[
                r"(?i)\bselling\s*,?\s*general\s+and\s+administrative\b",
                r"(?i)\bgeneral\s+and\s+administrative\b",  # Google: "General and administrative"
                r"(?i)\bsg&a\b",
                r"(?i)^sales\s+and\s+marketing\b",  # Google: "Sales and marketing"
                r"(?i)^selling\s+and\s+marketing\b",
            ]
        )
        
        self.RnD = MapFact(
            fact=RnD,
            priority=7,
            gaap_pattern=[r"(?i)\bResearchAndDevelopmentExpense\b"],
            human_pattern=[
                r"(?i)\bresearch\s+and\s+development\b",
                r"(?i)\br\s*&\s*d\b",
            ]
        )
        
        self.AmortizationDepreciation = MapFact(
            fact=AmortizationDepreciation,
            priority=6,
            gaap_pattern=[
                r"(?i)\bDepreciationAndAmortization\b",
                r"(?i)\bDepreciationDepletionAndAmortization\b",
            ],
            human_pattern=[
                r"(?i)\bdepreciation\s+and\s+amortization\b",
                r"(?i)\bd\s*&\s*a\b",
            ]
        )
        
        self.OtherOperatingExpense = MapFact(
            fact=OtherOperatingExpense,
            priority=5,
            gaap_pattern=[r"(?i)\bOtherOperatingIncomeExpense\b"],
            human_pattern=[r"(?i)\bother\s+operating\s+expenses?\b"]
        )
        
        self.TotalOperatingExpense = MapFact(
            fact=TotalOperatingExpense,
            priority=7,
            gaap_pattern=[
                r"(?i)\bOperatingExpenses\b",
                r"(?i)\bOperatingExpensesAndCosts\b",
                r"(?i)\bCostsAndExpenses\b",  # Google uses "Total costs and expenses"
            ],
            human_pattern=[
                r"(?i)^total\s+operating\s+expenses?\b",
                r"(?i)^operating\s+expenses?\b",
                r"(?i)^total\s+costs\s+and\s+expenses?\b",  # Google
            ]
        )
        
        # ==================== OPERATING INCOME ====================
        self.OperatingIncome = MapFact(
            fact=OperatingIncome,
            priority=8,
            gaap_pattern=[
                r"(?i)\bOperatingIncome(Loss)?\b",
                *GAAP_INCOME_PATTERNS
            ],
            human_pattern=[
                r"(?i)^operating\s+income\b",
                r"(?i)^income\s+from\s+operations\b",
            ]
        )
        
        # ==================== NON-OPERATING ITEMS ====================
        self.InterestExpense = MapFact(
            fact=InterestExpense,
            priority=6,
            gaap_pattern=[
                r"(?i)\bInterestExpense\b",
                r"(?i)\bInterestAndDebtExpense\b",
            ],
            human_pattern=[
                r"(?i)^interest\s+expense\b",
                r"(?i)^interest\s+and\s+debt\s+expense\b",
            ],
            strict_compare=True
        )
        
        self.InterestInvestmentIncome = MapFact(
            fact=InterestInvestmentIncome,
            priority=6,
            gaap_pattern=[
                r"(?i)\bInvestmentIncomeInterest\b",
                r"(?i)\bInterestAndOtherIncome\b",
                r"(?i)\bNonoperatingIncomeExpense\b",  # Apple uses this
                r"(?i)\bOtherNonoperatingIncomeExpense\b",
                r"(?i)\bInterestIncomeExpenseNet\b",
            ],
            human_pattern=[
                r"(?i)\binterest\s+(and\s+other\s+)?income\b",
                r"(?i)\bother\s+income\b",
                r"(?i)\bother\s+income.*expense.*net\b",  # Apple: "Other income/(expense), net"
                r"(?i)\binterest\s+and\s+other.*income\b",
                r"(?i)\binterest.*other.*net\b",
            ]
        )
        
        # ==================== INCOME BEFORE TAX ====================
        self.IncomeTaxExpense = MapFact(
            fact=IncomeTaxExpense,
            priority=8,
            gaap_pattern=[
                r"(?i)\bIncomeTaxExpenseBenefit\b",
                r"(?i)\bIncomeTaxesPaid\b",
            ],
            human_pattern=[
                r"(?i)^income\s+tax\s+(expense|provision)\b",
                r"(?i)^provision\s+for\s+income\s+taxes\b",
                r"(?i)^income\s+taxes\b",
                r"(?i)^tax\s+(expense|provision)\b",
            ]
        )
        
        # ==================== NET INCOME ====================
        self.NetIncome = MapFact(
            fact=NetIncome,
            priority=10,
            gaap_pattern=[
                r"(?i)\bNetIncomeLoss\b",
                *GAAP_INCOME_PATTERNS
            ],
            human_pattern=[
                r"(?i)^net\s+(income|earnings|profit)\b",
                r"(?i)^net\s+income\s+attributable\b",
            ]
        )
        
        # ==================== EARNINGS PER SHARE ====================
        self.EarningsPerShareBasic = MapFact(
            fact=EarningsPerShareBasic,
            priority=5,
            gaap_pattern=[r"(?i)\bEarningsPerShareBasic\b"],
            human_pattern=[
                r"(?i)\bearnings?\s+per\s+share\s*[-:,]?\s*basic\b",
                r"(?i)\bbasic\s+eps\b",
                r"(?i)^basic\s*\(",  # Apple: "Basic (in dollars per share)"
                r"(?i)^basic\s*$",  # Just "Basic"
                r"(?i)basic\s+net\s+income\s+per\s+share",  # Google: "Basic net income per share"
            ]
        )
        
        self.EarningsPerShareDiluted = MapFact(
            fact=EarningsPerShareDiluted,
            priority=5,
            gaap_pattern=[r"(?i)\bEarningsPerShareDiluted\b"],
            human_pattern=[
                r"(?i)\bearnings?\s+per\s+share\s*[-:,]?\s*diluted\b",
                r"(?i)\bdiluted\s+eps\b",
                r"(?i)^diluted\s*\(",  # Apple: "Diluted (in dollars per share)"
                r"(?i)^diluted\s*$",  # Just "Diluted"
                r"(?i)diluted\s+net\s+income\s+per\s+share",  # Google: "Diluted net income per share"
            ]
        )
        
        self.WeightedAverageSharesOutstandingBasic = MapFact(
            fact=WeightedAverageSharesOutstandingBasic,
            priority=4,
            gaap_pattern=[r"(?i)\bWeightedAverageNumberOfSharesOutstandingBasic\b"],
            human_pattern=[
                r"(?i)\bweighted.average.*shares.*basic\b",
                r"(?i)\bshares.*basic\b",
                r"(?i)^basic\s*\(.*shares\)",  # Apple: "Basic (in shares)"
            ]
        )
        
        self.WeightedAverageSharesOutstandingDiluted = MapFact(
            fact=WeightedAverageSharesOutstandingDiluted,
            priority=4,
            gaap_pattern=[r"(?i)\bWeightedAverageNumberOfDilutedSharesOutstanding\b"],
            human_pattern=[
                r"(?i)\bweighted.average.*shares.*diluted\b",
                r"(?i)\bshares.*diluted\b",
                r"(?i)^diluted\s*\(.*shares\)",  # Apple: "Diluted (in shares)"
            ]
        )


#########################################
# BALANCE SHEET MAPPING
#########################################

class BalanceSheetMap:
    """
    Comprehensive Balance Sheet mapping covering:
    - Current assets (cash, receivables, inventory, etc.)
    - Non-current assets (PP&E, intangibles, etc.)
    - Total assets
    - Current liabilities (payables, short-term debt, etc.)
    - Non-current liabilities (long-term debt, etc.)
    - Total liabilities
    - Equity (common stock, retained earnings, etc.)
    - Total equity
    """
    
    def __init__(self):
        
        # ==================== ASSETS - CURRENT ====================
        self.CashAndCashEquivalents = MapFact(
            fact=CashAndCashEquivalent,
            priority=9,
            gaap_pattern=[r"(?i)\bCashAndCashEquivalentsAtCarryingValue\b"],
            human_pattern=[r"(?i)^cash\s+and\s+cash\s+equivalents\b"]
        )
        
        self.AccountsReceivable = MapFact(
            fact=AccountsReceivable,
            priority=7,
            gaap_pattern=[r"(?i)\bAccountsReceivableNet\w*\b"],
            human_pattern=[r"(?i)^(accounts|trade)\s+receivables?\b"]
        )
        
        self.Inventory = MapFact(
            fact="Inventory",
            priority=7,
            gaap_pattern=[r"(?i)\bInventoryNet\b"],
            human_pattern=[r"(?i)^inventor(y|ies)\b"]
        )
        
        self.CurrentAssets = MapFact(
            fact=CurrentAssets,
            priority=8,
            gaap_pattern=[r"(?i)\bAssetsCurrent\b"],
            human_pattern=[r"(?i)^total\s+current\s+assets\b"]
        )
        
        # ==================== ASSETS - NON-CURRENT ====================
        self.PropertyPlantEquipment = MapFact(
            fact=PropertyPlantAndEquipment,
            priority=7,
            gaap_pattern=[r"(?i)\bPropertyPlantAndEquipmentNet\b"],
            human_pattern=[
                r"(?i)^property[,\s]+plant\s+and\s+equipment\b",
                r"(?i)^pp&e\b",
            ]
        )
        
        self.Goodwill = MapFact(
            fact=Goodwill,
            priority=6,
            gaap_pattern=[r"(?i)\bGoodwill\b"],
            human_pattern=[r"(?i)^goodwill\b"]
        )
        
        self.IntangibleAssets = MapFact(
            fact=IntangibleAssets,
            priority=6,
            gaap_pattern=[r"(?i)\bIntangibleAssetsNetExcludingGoodwill\b"],
            human_pattern=[r"(?i)^intangible\s+assets\b"]
        )
        
        self.TotalAssets = MapFact(
            fact=TotalAssets,
            priority=10,
            gaap_pattern=[r"(?i)\bAssets\b"],
            human_pattern=[r"(?i)^total\s+assets\b"]
        )
        
        # ==================== LIABILITIES - CURRENT ====================
        self.AccountsPayable = MapFact(
            fact=AccountsPayable,
            priority=7,
            gaap_pattern=[r"(?i)\bAccountsPayableCurrent\b"],
            human_pattern=[r"(?i)^(accounts|trade)\s+payables?\b"]
        )
        
        self.ShortTermDebt = MapFact(
            fact=ShortTermDebt,
            priority=7,
            gaap_pattern=[
                r"(?i)\bDebtCurrent\b",
                r"(?i)\bShortTermBorrowings\b",
            ],
            human_pattern=[
                r"(?i)^short.term\s+debt\b",
                r"(?i)^current\s+portion\s+of\s+.*debt\b",
            ]
        )
        
        self.CurrentLiabilities = MapFact(
            fact=LiabilitiesCurrent,
            priority=8,
            gaap_pattern=[r"(?i)\bLiabilitiesCurrent\b"],
            human_pattern=[r"(?i)^total\s+current\s+liabilities\b"]
        )
        
        # ==================== LIABILITIES - NON-CURRENT ====================
        self.LongTermDebt = MapFact(
            fact=LongTermDebt,
            priority=7,
            gaap_pattern=[
                r"(?i)\bLongTermDebtNoncurrent\b",
                r"(?i)\bLongTermDebt\b",
            ],
            human_pattern=[r"(?i)^long.term\s+debt\b"]
        )
        
        self.TotalLiabilities = MapFact(
            fact=TotalLiabilities,
            priority=9,
            gaap_pattern=[r"(?i)\bLiabilities\b"],
            human_pattern=[r"(?i)^total\s+liabilities\b"]
        )
        
        # ==================== EQUITY ====================
        self.RetainedEarnings = MapFact(
            fact=RetainedEarnings,
            priority=6,
            gaap_pattern=[r"(?i)\bRetainedEarningsAccumulatedDeficit\b"],
            human_pattern=[r"(?i)^retained\s+earnings\b"]
        )
        
        self.StockholdersEquity = MapFact(
            fact=StockholdersEquity,
            priority=9,
            gaap_pattern=[r"(?i)\bStockholdersEquity\b"],
            human_pattern=[
                r"(?i)^total\s+(stockholders?|shareholders?).equity\b",
                r"(?i)^total\s+equity\b",
            ]
        )
        
        self.TotalLiabilitiesAndEquity = MapFact(
            fact=TotalLiabilitiesAndEquity,
            priority=9,
            gaap_pattern=[r"(?i)\bLiabilitiesAndStockholdersEquity\b"],
            human_pattern=[r"(?i)^total\s+liabilities\s+and\s+(stockholders?|shareholders?).equity\b"]
        )


#########################################
# CASH FLOW STATEMENT MAPPING
#########################################

class CashFlowMap:
    """
    Comprehensive Cash Flow Statement mapping covering:
    - Operating activities (net income adjustments, working capital changes)
    - Investing activities (CapEx, acquisitions, investments)
    - Financing activities (debt, equity, dividends)
    - Net change in cash
    """
    
    def __init__(self):
        
        # ==================== OPERATING ACTIVITIES ====================
        self.NetIncomeCF = MapFact(
            fact="Net income (CF)",
            priority=9,
            gaap_pattern=[r"(?i)\bNetIncomeLoss\b"],
            human_pattern=[r"(?i)^net\s+(income|earnings)\b"]
        )
        
        self.DepreciationAmortizationCF = MapFact(
            fact="Depreciation and amortization (CF)",
            priority=7,
            gaap_pattern=[r"(?i)\bDepreciationDepletionAndAmortization\b"],
            human_pattern=[r"(?i)^depreciation\s+and\s+amortization\b"]
        )
        
        self.StockBasedCompensation = MapFact(
            fact="Stock-based compensation",
            priority=6,
            gaap_pattern=[r"(?i)\bShareBasedCompensation\b"],
            human_pattern=[r"(?i)\bstock.based\s+compensation\b"]
        )
        
        self.ChangeInWorkingCapital = MapFact(
            fact="Change in working capital",
            priority=6,
            gaap_pattern=[r"(?i)\bIncreaseDecreaseInOperatingCapital\b"],
            human_pattern=[r"(?i)\bchange.*working\s+capital\b"]
        )
        
        self.CashFromOperations = MapFact(
            fact="Net cash from operating activities",
            priority=10,
            gaap_pattern=[r"(?i)\bNetCashProvidedByUsedInOperatingActivities\b"],
            human_pattern=[
                r"(?i)^net\s+cash\s+(provided\s+by|from)\s+operating\s+activities\b",
                r"(?i)^cash\s+from\s+operations\b",
            ]
        )
        
        # ==================== INVESTING ACTIVITIES ====================
        self.CapEx = MapFact(
            fact="Capital expenditures",
            priority=8,
            gaap_pattern=[r"(?i)\bPaymentsToAcquirePropertyPlantAndEquipment\b"],
            human_pattern=[
                r"(?i)\bcapital\s+expenditures?\b",
                r"(?i)\bcapex\b",
                r"(?i)\bpurchase.*property.*equipment\b",
            ]
        )
        
        self.Acquisitions = MapFact(
            fact="Acquisitions",
            priority=6,
            gaap_pattern=[r"(?i)\bPaymentsToAcquireBusinessesNetOfCashAcquired\b"],
            human_pattern=[r"(?i)\bacquisitions?\s+of\s+business\b"]
        )
        
        self.CashFromInvesting = MapFact(
            fact="Net cash from investing activities",
            priority=9,
            gaap_pattern=[r"(?i)\bNetCashProvidedByUsedInInvestingActivities\b"],
            human_pattern=[r"(?i)^net\s+cash\s+(used\s+in|from)\s+investing\s+activities\b"]
        )
        
        # ==================== FINANCING ACTIVITIES ====================
        self.DebtIssuance = MapFact(
            fact="Proceeds from debt issuance",
            priority=6,
            gaap_pattern=[r"(?i)\bProceedsFromIssuanceOfLongTermDebt\b"],
            human_pattern=[r"(?i)\bproceeds\s+from.*debt\b"]
        )
        
        self.DebtRepayment = MapFact(
            fact="Debt repayment",
            priority=6,
            gaap_pattern=[r"(?i)\bRepaymentsOfLongTermDebt\b"],
            human_pattern=[r"(?i)\brepayment.*debt\b"]
        )
        
        self.Dividends = MapFact(
            fact="Dividends paid",
            priority=7,
            gaap_pattern=[r"(?i)\bPaymentsOfDividends\b"],
            human_pattern=[r"(?i)\bdividends\s+paid\b"]
        )
        
        self.CashFromFinancing = MapFact(
            fact="Net cash from financing activities",
            priority=9,
            gaap_pattern=[r"(?i)\bNetCashProvidedByUsedInFinancingActivities\b"],
            human_pattern=[r"(?i)^net\s+cash\s+(provided\s+by|from)\s+financing\s+activities\b"]
        )
        
        # ==================== NET CHANGE ====================
        self.NetChangeInCash = MapFact(
            fact="Net change in cash",
            priority=9,
            gaap_pattern=[r"(?i)\bCashCashEquivalentsRestrictedCashAndRestrictedCashEquivalentsPeriodIncreaseDecreaseIncludingExchangeRateEffect\b"],
            human_pattern=[r"(?i)^net\s+(increase|decrease|change).*cash\b"]
        )
