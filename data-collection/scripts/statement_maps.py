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
    Maps balance sheet line items to standardized format.
    
    Asset classifications:
    - Current assets (cash, receivables, inventory, etc.)
    - Non-current assets (PP&E, goodwill, intangibles, etc.)
    
    Liability classifications:
    - Current liabilities (payables, short-term debt, etc.)
    - Non-current liabilities (long-term debt, deferred taxes, etc.)
    
    Equity items:
    - Common stock, retained earnings, AOCI, etc.
    """
    
    def __init__(self):
        # ==================== CURRENT ASSETS ====================
        self.CashAndCashEquivalents = MapFact(
            fact=CashAndCashEquivalents,
            priority=9,
            gaap_pattern=[
                r"(?i)\bCashAndCashEquivalentsAtCarryingValue\b",
                r"(?i)\bCash\b",
            ],
            human_pattern=[
                r"(?i)^cash\s+and\s+cash\s+equivalents\b",
                r"(?i)^cash\b",
            ]
        )
        
        self.MarketableSecuritiesCurrent = MapFact(
            fact="Marketable Securities Current",
            priority=7,
            gaap_pattern=[
                r"(?i)\bMarketableSecuritiesCurrent\b",
                r"(?i)\bAvailableForSaleSecuritiesCurrent\b",
            ],
            human_pattern=[
                r"(?i)^marketable\s+securities\b",
                r"(?i)^short-?term\s+investments\b",
            ]
        )
        
        self.AccountsReceivable = MapFact(
            fact=AccountsReceivable,
            priority=8,
            gaap_pattern=[
                r"(?i)\bAccountsReceivableNet(Current)?\b",
                r"(?i)\bReceivablesNetCurrent\b",
            ],
            human_pattern=[
                r"(?i)^accounts\s+receivable(,\s+net)?\b",
                r"(?i)^trade\s+receivables\b",
            ]
        )
        
        self.VendorNonTradeReceivables = MapFact(
            fact="Vendor Non-Trade Receivables",
            priority=6,
            gaap_pattern=[
                r"(?i)\bNontradeReceivablesCurrent\b",
            ],
            human_pattern=[
                r"(?i)vendor\s+non-?trade\s+receivables\b",
            ]
        )
        
        self.Inventory = MapFact(
            fact=Inventory,
            priority=8,
            gaap_pattern=[
                r"(?i)\bInventoryNet\b",
                r"(?i)\bInventory\b",
            ],
            human_pattern=[
                r"(?i)^inventor(y|ies)\b",
            ]
        )
        
        self.OtherCurrentAssets = MapFact(
            fact="Other Current Assets",
            priority=6,
            gaap_pattern=[
                r"(?i)\bOtherAssetsCurrent\b",
                r"(?i)\bPrepaidExpenseCurrent\b",
            ],
            human_pattern=[
                r"(?i)^other\s+current\s+assets\b",
                r"(?i)^prepaid\s+expenses\b",
            ]
        )
        
        self.CurrentAssets = MapFact(
            fact=CurrentAssets,
            priority=9,
            gaap_pattern=[
                r"(?i)\bAssetsCurrent\b",
            ],
            human_pattern=[
                r"(?i)^total\s+current\s+assets\b",
            ]
        )
        
        # ==================== NON-CURRENT ASSETS ====================
        self.MarketableSecuritiesNoncurrent = MapFact(
            fact="Marketable Securities Noncurrent",
            priority=7,
            gaap_pattern=[
                r"(?i)\bMarketableSecuritiesNoncurrent\b",
                r"(?i)\bAvailableForSaleSecuritiesNoncurrent\b",
            ],
            human_pattern=[
                r"(?i)^long-?term\s+marketable\s+securities\b",
                r"(?i)^marketable\s+securities.*non-?current\b",
            ]
        )
        
        self.PropertyPlantEquipment = MapFact(
            fact=PropertyPlantEquipment,
            priority=8,
            gaap_pattern=[
                r"(?i)\bPropertyPlantAndEquipmentNet\b",
                r"(?i)\bPropertyPlantAndEquipment\b",
            ],
            human_pattern=[
                r"(?i)property.*plant.*equipment\b",
                r"(?i)^pp&e\b",
            ]
        )
        
        self.Goodwill = MapFact(
            fact=Goodwill,
            priority=7,
            gaap_pattern=[
                r"(?i)\bGoodwill\b",
            ],
            human_pattern=[
                r"(?i)^goodwill\b",
            ]
        )
        
        self.IntangibleAssets = MapFact(
            fact="Intangible Assets",
            priority=7,
            gaap_pattern=[
                r"(?i)\bIntangibleAssetsNetExcludingGoodwill\b",
                r"(?i)\bFiniteLivedIntangibleAssetsNet\b",
            ],
            human_pattern=[
                r"(?i)^intangible\s+assets\b",
            ]
        )
        
        self.OtherNoncurrentAssets = MapFact(
            fact="Other Noncurrent Assets",
            priority=6,
            gaap_pattern=[
                r"(?i)\bOtherAssetsNoncurrent\b",
            ],
            human_pattern=[
                r"(?i)^other\s+non-?current\s+assets\b",
            ]
        )
        
        self.NoncurrentAssets = MapFact(
            fact="Noncurrent Assets",
            priority=8,
            gaap_pattern=[
                r"(?i)\bAssetsNoncurrent\b",
            ],
            human_pattern=[
                r"(?i)^total\s+non-?current\s+assets\b",
            ]
        )
        
        self.TotalAssets = MapFact(
            fact=TotalAssets,
            priority=10,
            gaap_pattern=[
                r"(?i)^Assets$",  # Exact match to avoid matching AssetsCurrent
            ],
            human_pattern=[
                r"(?i)^total\s+assets\b",
            ]
        )
        
        # ==================== CURRENT LIABILITIES ====================
        self.AccountsPayable = MapFact(
            fact=AccountsPayable,
            priority=8,
            gaap_pattern=[
                r"(?i)\bAccountsPayable(Current)?\b",
            ],
            human_pattern=[
                r"(?i)^accounts\s+payable\b",
                r"(?i)^trade\s+payables\b",
            ]
        )
        
        self.OtherCurrentLiabilities = MapFact(
            fact="Other Current Liabilities",
            priority=6,
            gaap_pattern=[
                r"(?i)\bOtherLiabilitiesCurrent\b",
                r"(?i)\bAccruedLiabilitiesCurrent\b",
            ],
            human_pattern=[
                r"(?i)^other\s+current\s+liabilities\b",
                r"(?i)^accrued\s+liabilities\b",
            ]
        )
        
        self.DeferredRevenue = MapFact(
            fact="Deferred Revenue",
            priority=6,
            gaap_pattern=[
                r"(?i)\bContractWithCustomerLiability(Current)?\b",
                r"(?i)\bDeferredRevenue(Current)?\b",
            ],
            human_pattern=[
                r"(?i)^deferred\s+revenue\b",
                r"(?i)^unearned\s+revenue\b",
            ]
        )
        
        self.CommercialPaper = MapFact(
            fact="Commercial Paper",
            priority=6,
            gaap_pattern=[
                r"(?i)\bCommercialPaper\b",
            ],
            human_pattern=[
                r"(?i)^commercial\s+paper\b",
            ]
        )
        
        self.ShortTermDebt = MapFact(
            fact="Short Term Debt Current",
            priority=7,
            gaap_pattern=[
                r"(?i)\bLongTermDebtCurrent\b",  # Current portion of long-term debt
                r"(?i)\bShortTermBorrowings\b",
            ],
            human_pattern=[
                r"(?i)^term\s+debt\b",  # Apple uses this for current portion
                r"(?i)^current\s+portion.*debt\b",
                r"(?i)^short-?term\s+debt\b",
            ]
        )
        
        self.CurrentLiabilities = MapFact(
            fact=CurrentLiabilities,
            priority=9,
            gaap_pattern=[
                r"(?i)\bLiabilitiesCurrent\b",
            ],
            human_pattern=[
                r"(?i)^total\s+current\s+liabilities\b",
            ]
        )
        
        # ==================== NON-CURRENT LIABILITIES ====================
        self.LongTermDebt = MapFact(
            fact=LongTermDebt,
            priority=8,
            gaap_pattern=[
                r"(?i)\bLongTermDebtNoncurrent\b",
                r"(?i)\bLongTermDebtAndCapitalLeaseObligations\b",
            ],
            human_pattern=[
                r"(?i)^long-?term\s+debt\b",
                r"(?i)^term\s+debt.*non-?current\b",
            ]
        )
        
        self.OtherNoncurrentLiabilities = MapFact(
            fact="Other Noncurrent Liabilities",
            priority=6,
            gaap_pattern=[
                r"(?i)\bOtherLiabilitiesNoncurrent\b",
            ],
            human_pattern=[
                r"(?i)^other\s+non-?current\s+liabilities\b",
            ]
        )
        
        self.NoncurrentLiabilities = MapFact(
            fact="Noncurrent Liabilities",
            priority=8,
            gaap_pattern=[
                r"(?i)\bLiabilitiesNoncurrent\b",
            ],
            human_pattern=[
                r"(?i)^total\s+non-?current\s+liabilities\b",
            ]
        )
        
        self.TotalLiabilities = MapFact(
            fact=TotalLiabilities,
            priority=10,
            gaap_pattern=[
                r"(?i)^Liabilities$",  # Exact match
            ],
            human_pattern=[
                r"(?i)^total\s+liabilities\b",
            ]
        )
        
        # ==================== EQUITY ====================
        self.CommonStock = MapFact(
            fact="Common Stock",
            priority=6,
            gaap_pattern=[
                r"(?i)\bCommonStocksIncludingAdditionalPaidInCapital\b",
                r"(?i)\bCommonStockValue\b",
            ],
            human_pattern=[
                r"(?i)^common\s+stock\s+and\s+additional\s+paid-?in\s+capital\b",
                r"(?i)^common\s+stock\b",
            ]
        )
        
        self.RetainedEarnings = MapFact(
            fact=RetainedEarnings,
            priority=7,
            gaap_pattern=[
                r"(?i)\bRetainedEarningsAccumulatedDeficit\b",
                r"(?i)\bRetainedEarnings\b",
            ],
            human_pattern=[
                r"(?i)^retained\s+earnings\b",
                r"(?i)^accumulated\s+(deficit|earnings)\b",
            ]
        )
        
        self.AOCI = MapFact(
            fact="Accumulated Other Comprehensive Income",
            priority=6,
            gaap_pattern=[
                r"(?i)\bAccumulatedOtherComprehensiveIncomeLossNetOfTax\b",
            ],
            human_pattern=[
                r"(?i)^accumulated\s+other\s+comprehensive\s+(income|loss)\b",
                r"(?i)^aoci\b",
            ]
        )
        
        self.StockholdersEquity = MapFact(
            fact=StockholdersEquity,
            priority=9,
            gaap_pattern=[
                r"(?i)\bStockholdersEquity\b",
            ],
            human_pattern=[
                r"(?i)^(total\s+)?(shareholders?|stockholders?)\s+equity\b",
            ]
        )
        
        self.TotalLiabilitiesAndEquity = MapFact(
            fact="Total Liabilities And Equity",
            priority=10,
            gaap_pattern=[
                r"(?i)\bLiabilitiesAndStockholdersEquity\b",
            ],
            human_pattern=[
                r"(?i)^total\s+liabilities\s+and\s+(shareholders?|stockholders?)\s+equity\b",
            ]
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
            gaap_pattern=[
                r"(?i)\bShareBasedCompensation\b",
                r"(?i)\bAllocatedShareBasedCompensationExpense\b",
            ],
            human_pattern=[
                r"(?i)\bstock.based\s+compensation\b",
                r"(?i)\bshare.based\s+compensation\b",
            ]
        )
        
        self.OtherNoncashItems = MapFact(
            fact="Other noncash items",
            priority=5,
            gaap_pattern=[
                r"(?i)\bOtherNoncashIncomeExpense\b",
            ],
            human_pattern=[
                r"(?i)^other\b",
            ]
        )
        
        # Working Capital Changes
        self.ChangeInAccountsReceivable = MapFact(
            fact="Change in accounts receivable",
            priority=5,
            gaap_pattern=[
                r"(?i)\bIncreaseDecreaseInAccountsReceivable\b",
            ],
            human_pattern=[
                r"(?i)accounts\s+receivable",
            ]
        )
        
        self.ChangeInInventory = MapFact(
            fact="Change in inventory",
            priority=5,
            gaap_pattern=[
                r"(?i)\bIncreaseDecreaseInInventories\b",
            ],
            human_pattern=[
                r"(?i)inventor(y|ies)\b",
            ]
        )
        
        self.ChangeInAccountsPayable = MapFact(
            fact="Change in accounts payable",
            priority=5,
            gaap_pattern=[
                r"(?i)\bIncreaseDecreaseInAccountsPayable\b",
            ],
            human_pattern=[
                r"(?i)accounts\s+payable",
            ]
        )
        
        self.ChangeInOtherAssets = MapFact(
            fact="Change in other operating assets",
            priority=4,
            gaap_pattern=[
                r"(?i)\bIncreaseDecreaseInOtherOperatingAssets\b",
            ],
            human_pattern=[
                r"(?i)other.*assets",
            ]
        )
        
        self.ChangeInOtherLiabilities = MapFact(
            fact="Change in other operating liabilities",
            priority=4,
            gaap_pattern=[
                r"(?i)\bIncreaseDecreaseInOtherOperatingLiabilities\b",
            ],
            human_pattern=[
                r"(?i)other.*liabilities",
            ]
        )
        
        self.CashFromOperations = MapFact(
            fact="Net cash from operating activities",
            priority=10,
            gaap_pattern=[
                r"(?i)\bNetCashProvidedByUsedInOperatingActivities\b",
            ],
            human_pattern=[
                r"(?i)^net\s+cash\s+(provided\s+by|from)\s+operating\s+activities\b",
                r"(?i)^cash\s+(from|generated\s+by)\s+operat",
            ]
        )
        
        # ==================== INVESTING ACTIVITIES ====================
        self.PurchaseOfMarketableSecurities = MapFact(
            fact="Purchase of marketable securities",
            priority=6,
            gaap_pattern=[
                r"(?i)\bPaymentsToAcquireAvailableForSaleSecuritiesDebt\b",
                r"(?i)\bPaymentsToAcquireMarketableSecurities\b",
            ],
            human_pattern=[
                r"(?i)purchase.*marketable\s+securities",
            ]
        )
        
        self.ProceedsFromMarketableSecurities = MapFact(
            fact="Proceeds from marketable securities",
            priority=6,
            gaap_pattern=[
                r"(?i)\bProceedsFromMaturitiesPrepaymentsAndCallsOfAvailableForSaleSecurities\b",
                r"(?i)\bProceedsFromSaleOfAvailableForSaleSecuritiesDebt\b",
            ],
            human_pattern=[
                r"(?i)proceeds\s+from\s+(sales?|maturities).*marketable\s+securities",
            ]
        )
        
        self.CapEx = MapFact(
            fact="Capital expenditures",
            priority=8,
            gaap_pattern=[
                r"(?i)\bPaymentsToAcquirePropertyPlantAndEquipment\b",
                r"(?i)\bPaymentsForCapitalImprovements\b",
            ],
            human_pattern=[
                r"(?i)\bcapital\s+expenditures?\b",
                r"(?i)\bcapex\b",
                r"(?i)payment.*acquisition.*property.*equipment\b",
            ]
        )
        
        self.Acquisitions = MapFact(
            fact="Acquisitions",
            priority=6,
            gaap_pattern=[
                r"(?i)\bPaymentsToAcquireBusinessesNetOfCashAcquired\b",
            ],
            human_pattern=[
                r"(?i)\bacquisitions?\s+of\s+business\b",
            ]
        )
        
        self.CashFromInvesting = MapFact(
            fact="Net cash from investing activities",
            priority=10,
            gaap_pattern=[
                r"(?i)\bNetCashProvidedByUsedInInvestingActivities\b",
            ],
            human_pattern=[
                r"(?i)^net\s+cash\s+(used\s+in|from|generated.*by)\s+investing\s+activities\b",
                r"(?i)^cash\s+(used\s+in|from)\s+investing",
            ]
        )
        
        # ==================== FINANCING ACTIVITIES ====================
        self.TaxWithholdingForShareBasedComp = MapFact(
            fact="Tax withholding for share-based compensation",
            priority=5,
            gaap_pattern=[
                r"(?i)\bPaymentsRelatedToTaxWithholdingForShareBasedCompensation\b",
            ],
            human_pattern=[
                r"(?i)payment.*tax.*share.*compensation",
                r"(?i)payment.*tax.*equity\s+awards",
            ]
        )
        
        self.Dividends = MapFact(
            fact="Dividends paid",
            priority=7,
            gaap_pattern=[
                r"(?i)\bPaymentsOfDividends\b",
            ],
            human_pattern=[
                r"(?i)payment.*dividends",
            ]
        )
        
        self.StockRepurchases = MapFact(
            fact="Stock repurchases",
            priority=7,
            gaap_pattern=[
                r"(?i)\bPaymentsForRepurchaseOfCommonStock\b",
            ],
            human_pattern=[
                r"(?i)repurchase.*common\s+stock",
                r"(?i)buyback",
            ]
        )
        
        self.DebtIssuance = MapFact(
            fact="Proceeds from debt issuance",
            priority=6,
            gaap_pattern=[
                r"(?i)\bProceedsFromIssuanceOfLongTermDebt\b",
            ],
            human_pattern=[
                r"(?i)proceeds\s+from\s+issuance.*debt",
            ]
        )
        
        self.DebtRepayment = MapFact(
            fact="Debt repayment",
            priority=6,
            gaap_pattern=[
                r"(?i)\bRepaymentsOfLongTermDebt\b",
            ],
            human_pattern=[
                r"(?i)repayment.*debt",
            ]
        )
        
        self.CommercialPaperNet = MapFact(
            fact="Commercial paper net change",
            priority=5,
            gaap_pattern=[
                r"(?i)\bProceedsFromRepaymentsOfCommercialPaper\b",
            ],
            human_pattern=[
                r"(?i)commercial\s+paper.*net",
            ]
        )
        
        self.CashFromFinancing = MapFact(
            fact="Net cash from financing activities",
            priority=10,
            gaap_pattern=[
                r"(?i)\bNetCashProvidedByUsedInFinancingActivities\b",
            ],
            human_pattern=[
                r"(?i)^net\s+cash\s+(provided\s+by|used\s+in|from)\s+financing\s+activities\b",
                r"(?i)^cash\s+(used\s+in|from)\s+financing",
            ]
        )
        
        # ==================== NET CHANGE ====================
        self.NetChangeInCash = MapFact(
            fact="Net change in cash",
            priority=9,
            gaap_pattern=[r"(?i)\bCashCashEquivalentsRestrictedCashAndRestrictedCashEquivalentsPeriodIncreaseDecreaseIncludingExchangeRateEffect\b"],
            human_pattern=[r"(?i)^net\s+(increase|decrease|change).*cash\b"]
        )
