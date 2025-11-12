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
    r"(?i)OperatingIncome[LoLosss]*\b",
    r"(?i)ProfitLoss\b",
    r"(?i)NetIncomeLoss\b",
    r"(?i)IncomeLossFromContinuingOperations\b",
    r"(?i)ComprehensiveIncomeNet\b",
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
                r"(?i)Revenues?\b",
                r"(?i)SalesRevenueNet\b",
                r"(?i)RevenueFromContractWithCustomer\w*",
                r"(?i)SalesRevenueGoodsNet\b",
                r"(?i)SalesRevenueServicesNet\b",
                r"(?i)RevenueNet\b",
                r"(?i)NetSales\b",
                r"(?i)SalesRevenue\w*",
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
                r"(?i)CostOfGoodsAndServicesSold\b",
                r"(?i)CostOfGoodsSold\b",
                r"(?i)CostOfGoods\b",
                # Cost of revenue/sales  
                r"(?i)CostOfRevenue\b",  # Google uses this
                r"(?i)CostOfSales?\b",
                r"(?i)CostOfServices\b",
                # Product/service costs
                r"(?i)CostOfProduct\b",
                r"(?i)CostOfGoodsAndServicesExcluding\b",
                r"(?i)CostsAndExpenses\b",
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
                r"(?i)GrossProfit\b",
                r"(?i)GrossMargin\b",
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
                r"(?i)SellingGeneralAndAdministrativeExpense\b",
                r"(?i)GeneralAndAdministrativeExpense\b",  # Google splits into separate items
                r"(?i)SellingAndMarketingExpense\b",  # Google uses this separately
                r"(?i)MarketingExpense\b",
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
            gaap_pattern=[r"(?i)ResearchAndDevelopmentExpense\b"],
            human_pattern=[
                r"(?i)\bresearch\s+and\s+development\b",
                r"(?i)\br\s*&\s*d\b",
            ]
        )
        
        self.AmortizationDepreciation = MapFact(
            fact=AmortizationDepreciation,
            priority=6,
            gaap_pattern=[
                r"(?i)DepreciationAndAmortization\b",
                r"(?i)DepreciationDepletionAndAmortization\b",
            ],
            human_pattern=[
                r"(?i)\bdepreciation\s+and\s+amortization\b",
                r"(?i)\bd\s*&\s*a\b",
            ]
        )
        
        self.OtherOperatingExpense = MapFact(
            fact=OtherOperatingExpense,
            priority=5,
            gaap_pattern=[r"(?i)OtherOperatingIncomeExpense\w*"],
            human_pattern=[r"(?i)\bother\s+operating\s+expenses?\b"]
        )
        
        self.TotalOperatingExpense = MapFact(
            fact=TotalOperatingExpense,
            priority=7,
            gaap_pattern=[
                r"(?i)OperatingExpenses\b",
                r"(?i)OperatingExpensesAndCosts\b",
                r"(?i)CostsAndExpenses\b",  # Google uses "Total costs and expenses"
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
                r"(?i)OperatingIncome(Loss)?\b",
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
                r"(?i)InterestExpense\w*",
                r"(?i)InterestAndDebtExpense\b",
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
                r"(?i)InvestmentIncomeInterest\b",
                r"(?i)InterestAndOtherIncome\b",
                r"(?i)NonoperatingIncomeExpense\b",  # Apple uses this
                r"(?i)OtherNonoperatingIncomeExpense\b",
                r"(?i)InterestIncomeExpenseNet\b",
                r"(?i)IncomeLossFromEquityMethodInvestments\b",
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
                r"(?i)IncomeTaxExpenseBenefit\b",
                r"(?i)IncomeTaxesPaid\b",
                r"(?i)IncomeLossFromContinuingOperationsBeforeIncomeTaxes\w*",
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
                r"(?i)NetIncomeLoss\w*",
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
            gaap_pattern=[
                r"(?i)EarningsPerShareBasic\b",
                r"(?i)IncomeLossFromContinuingOperationsPerBasicShare\b",
            ],
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
            gaap_pattern=[
                r"(?i)EarningsPerShareDiluted\b",
                r"(?i)IncomeLossFromContinuingOperationsPerDilutedShare\b",
            ],
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
            gaap_pattern=[
                r"(?i)WeightedAverageNumberOfSharesOutstandingBasic\b",
                r"(?i)WeightedAverageNumberOfShareOutstandingBasic\b",
            ],
            human_pattern=[
                r"(?i)\bweighted.average.*shares.*basic\b",
                r"(?i)\bshares.*basic\b",
                r"(?i)^basic\s*\(.*shares\)",  # Apple: "Basic (in shares)"
            ]
        )
        
        self.WeightedAverageSharesOutstandingDiluted = MapFact(
            fact=WeightedAverageSharesOutstandingDiluted,
            priority=4,
            gaap_pattern=[
                r"(?i)WeightedAverageNumberOfDilutedSharesOutstanding\b",
                r"(?i)WeightedAverageNumberDilutedSharesOutstanding\w*",
            ],
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
                r"(?i)CashAndCashEquivalentsAtCarryingValue\b",
                r"(?i)Cash\b",
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
                r"(?i)MarketableSecuritiesCurrent\b",
                r"(?i)AvailableForSaleSecuritiesCurrent\b",
                r"(?i)ShortTermInvestments\b",
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
                r"(?i)AccountsReceivableNet(Current)?\b",
                r"(?i)ReceivablesNetCurrent\b",
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
                r"(?i)NontradeReceivablesCurrent\b",
            ],
            human_pattern=[
                r"(?i)vendor\s+non-?trade\s+receivables\b",
            ]
        )
        
        self.Inventory = MapFact(
            fact=Inventory,
            priority=8,
            gaap_pattern=[
                r"(?i)InventoryNet\b",
                r"(?i)Inventory\b",
            ],
            human_pattern=[
                r"(?i)^inventor(y|ies)\b",
            ]
        )
        
        self.OtherCurrentAssets = MapFact(
            fact="Other Current Assets",
            priority=6,
            gaap_pattern=[
                r"(?i)OtherAssetsCurrent\b",
                r"(?i)PrepaidExpenseCurrent\b",
                r"(?i)PrepaidExpenseAndOtherAssetsCurrent\b",
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
                r"(?i)AssetsCurrent\b",
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
                r"(?i)MarketableSecuritiesNoncurrent\b",
                r"(?i)AvailableForSaleSecuritiesNoncurrent\b",
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
                r"(?i)PropertyPlantAndEquipmentNet\b",
                r"(?i)PropertyPlantAndEquipment\w*",
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
                r"(?i)Goodwill\b",
            ],
            human_pattern=[
                r"(?i)^goodwill\b",
            ]
        )
        
        self.IntangibleAssets = MapFact(
            fact="Intangible Assets",
            priority=7,
            gaap_pattern=[
                r"(?i)IntangibleAssetsNetExcludingGoodwill\b",
                r"(?i)FiniteLivedIntangibleAssetsNet\b",
            ],
            human_pattern=[
                r"(?i)^intangible\s+assets\b",
            ]
        )
        
        self.OtherNoncurrentAssets = MapFact(
            fact="Other Noncurrent Assets",
            priority=6,
            gaap_pattern=[
                r"(?i)OtherAssetsNoncurrent\b",
                r"(?i)OtherAssets\b",
            ],
            human_pattern=[
                r"(?i)^other\s+non-?current\s+assets\b",
            ]
        )
        
        self.NoncurrentAssets = MapFact(
            fact="Noncurrent Assets",
            priority=8,
            gaap_pattern=[
                r"(?i)AssetsNoncurrent\b",
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
                r"(?i)_Assets$",  # Match us-gaap_Assets
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
                r"(?i)AccountsPayable(Current)?\b",
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
                r"(?i)OtherLiabilitiesCurrent\b",
                r"(?i)AccruedLiabilitiesCurrent\b",
                r"(?i)AccruedLiabilities\b",
                r"(?i)AccruedIncomeTaxesCurrent\b",
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
                r"(?i)ContractWithCustomerLiability\w*",
                r"(?i)DeferredRevenue\w*",
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
                r"(?i)CommercialPaper\b",
            ],
            human_pattern=[
                r"(?i)^commercial\s+paper\b",
            ]
        )
        
        self.ShortTermDebt = MapFact(
            fact="Short Term Debt Current",
            priority=7,
            gaap_pattern=[
                r"(?i)LongTermDebtCurrent\b",  # Current portion of long-term debt
                r"(?i)ShortTermBorrowings\b",
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
                r"(?i)LiabilitiesCurrent\b",
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
                r"(?i)LongTermDebtNoncurrent\b",
                r"(?i)LongTermDebtAndCapitalLeaseObligations\b",
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
                r"(?i)OtherLiabilitiesNoncurrent\b",
                r"(?i)DeferredTaxLiabilitiesNoncurrent\b",
                r"(?i)DeferredIncomeTaxLiabilitiesNet\b",
                r"(?i)OperatingLeaseLiability\w*",
            ],
            human_pattern=[
                r"(?i)^other\s+non-?current\s+liabilities\b",
            ]
        )
        
        self.NoncurrentLiabilities = MapFact(
            fact="Noncurrent Liabilities",
            priority=8,
            gaap_pattern=[
                r"(?i)LiabilitiesNoncurrent\b",
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
                r"(?i)_Liabilities$",  # Match us-gaap_Liabilities
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
                r"(?i)CommonStocksIncludingAdditionalPaidInCapital\b",
                r"(?i)CommonStockValue\b",
                r"(?i)AdditionalPaidInCapital\w*",
                r"(?i)PreferredStockValue\b",
                r"(?i)TreasuryStockValue\b",
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
                r"(?i)RetainedEarningsAccumulatedDeficit\b",
                r"(?i)RetainedEarnings\b",
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
                r"(?i)AccumulatedOtherComprehensiveIncomeLossNetOfTax\b",
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
                r"(?i)StockholdersEquity\b",
                r"(?i)ShareholdersEquity\b",
            ],
            human_pattern=[
                r"(?i)^(total\s+)?(shareholders?|stockholders?)\s+equity\b",
            ]
        )
        
        self.TotalLiabilitiesAndEquity = MapFact(
            fact="Total Liabilities And Equity",
            priority=10,
            gaap_pattern=[
                r"(?i)LiabilitiesAndStockholdersEquity\b",
                r"(?i)LiabilitiesAndShareholdersEquity\b",
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
            gaap_pattern=[
                r"(?i)NetIncomeLoss\w*",
                r"(?i)ProfitLoss\b",
            ],
            human_pattern=[r"(?i)^net\s+(income|earnings)\b"]
        )
        
        self.DepreciationAmortizationCF = MapFact(
            fact="Depreciation and amortization (CF)",
            priority=7,
            gaap_pattern=[
                r"(?i)DepreciationDepletionAndAmortization\b",
                r"(?i)Depreciation\w*",
            ],
            human_pattern=[r"(?i)^depreciation\s+and\s+amortization\b"]
        )
        
        self.StockBasedCompensation = MapFact(
            fact="Stock-based compensation",
            priority=6,
            gaap_pattern=[
                r"(?i)ShareBasedCompensation\b",
                r"(?i)AllocatedShareBasedCompensationExpense\b",
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
                r"(?i)OtherNoncashIncomeExpense\b",
                r"(?i)OtherOperatingActivitiesCashFlowStatement\b",
                r"(?i)DeferredIncomeTaxExpenseBenefit\b",
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
                r"(?i)IncreaseDecreaseInAccountsReceivable\w*",
            ],
            human_pattern=[
                r"(?i)accounts\s+receivable",
            ]
        )
        
        self.ChangeInInventory = MapFact(
            fact="Change in inventory",
            priority=5,
            gaap_pattern=[
                r"(?i)IncreaseDecreaseInInventories\b",
                r"(?i)InventoryWriteDown\b",
            ],
            human_pattern=[
                r"(?i)inventor(y|ies)\b",
            ]
        )
        
        self.ChangeInAccountsPayable = MapFact(
            fact="Change in accounts payable",
            priority=5,
            gaap_pattern=[
                r"(?i)IncreaseDecreaseInAccountsPayable\w*",
            ],
            human_pattern=[
                r"(?i)accounts\s+payable",
            ]
        )
        
        self.ChangeInOtherAssets = MapFact(
            fact="Change in other operating assets",
            priority=4,
            gaap_pattern=[
                r"(?i)IncreaseDecreaseInOtherOperatingAssets\b",
                r"(?i)IncreaseDecreaseInOther\w*Assets\w*",
                r"(?i)IncreaseDecreaseInPrepaidDeferredExpenseAndOtherAssets\b",
            ],
            human_pattern=[
                r"(?i)other.*assets",
            ]
        )
        
        self.ChangeInOtherLiabilities = MapFact(
            fact="Change in other operating liabilities",
            priority=4,
            gaap_pattern=[
                r"(?i)IncreaseDecreaseInOtherOperatingLiabilities\b",
                r"(?i)IncreaseDecreaseInAccruedLiabilities\w*",
                r"(?i)IncreaseDecreaseInContractWithCustomerLiability\b",
            ],
            human_pattern=[
                r"(?i)other.*liabilities",
            ]
        )
        
        self.CashFromOperations = MapFact(
            fact="Net cash from operating activities",
            priority=10,
            gaap_pattern=[
                r"(?i)NetCashProvidedByUsedInOperatingActivities\b",
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
                r"(?i)PaymentsToAcquireAvailableForSaleSecuritiesDebt\b",
                r"(?i)PaymentsToAcquireMarketableSecurities\b",
                r"(?i)PaymentsToAcquire\w*Securities\w*",
            ],
            human_pattern=[
                r"(?i)purchase.*marketable\s+securities",
            ]
        )
        
        self.ProceedsFromMarketableSecurities = MapFact(
            fact="Proceeds from marketable securities",
            priority=6,
            gaap_pattern=[
                r"(?i)ProceedsFromMaturitiesPrepaymentsAndCallsOfAvailableForSaleSecurities\b",
                r"(?i)ProceedsFromSaleOfAvailableForSaleSecuritiesDebt\b",
                r"(?i)ProceedsFrom\w*Securities\w*",
                r"(?i)ProceedsFromSale\w*Securities\w*",
                r"(?i)ProceedsFromMaturities\w*",
            ],
            human_pattern=[
                r"(?i)proceeds\s+from\s+(sales?|maturities).*marketable\s+securities",
            ]
        )
        
        self.CapEx = MapFact(
            fact="Capital expenditures",
            priority=8,
            gaap_pattern=[
                r"(?i)PaymentsToAcquirePropertyPlantAndEquipment\b",
                r"(?i)PaymentsForCapitalImprovements\b",
                r"(?i)PaymentsToAcquire\w*PlantAndEquipment\b",
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
                r"(?i)PaymentsToAcquireBusinessesNetOfCashAcquired\b",
                r"(?i)PaymentsToAcquireBusinesses\w*",
            ],
            human_pattern=[
                r"(?i)\bacquisitions?\s+of\s+business\b",
            ]
        )
        
        self.CashFromInvesting = MapFact(
            fact="Net cash from investing activities",
            priority=10,
            gaap_pattern=[
                r"(?i)NetCashProvidedByUsedInInvestingActivities\b",
                r"(?i)PaymentsForProceedsFromOtherInvestingActivities\b",
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
                r"(?i)PaymentsRelatedToTaxWithholdingForShareBasedCompensation\b",
                r"(?i)ExcessTaxBenefitFromShareBasedCompensationFinancingActivities\b",
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
                r"(?i)PaymentsOfDividends\w*",
                r"(?i)Dividends\w*",
            ],
            human_pattern=[
                r"(?i)payment.*dividends",
            ]
        )
        
        self.StockRepurchases = MapFact(
            fact="Stock repurchases",
            priority=7,
            gaap_pattern=[
                r"(?i)PaymentsForRepurchaseOfCommonStock\b",
                r"(?i)ProceedsFromIssuanceOfCommonStock\b",
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
                r"(?i)ProceedsFromIssuanceOfLongTermDebt\w*",
                r"(?i)ProceedsFromIssuance\w*Debt\w*",
                r"(?i)ProceedsFrom\w*Debt\w*",
            ],
            human_pattern=[
                r"(?i)proceeds\s+from\s+issuance.*debt",
            ]
        )
        
        self.DebtRepayment = MapFact(
            fact="Debt repayment",
            priority=6,
            gaap_pattern=[
                r"(?i)RepaymentsOfLongTermDebt\w*",
                r"(?i)RepaymentsOf\w*Debt\w*",
                r"(?i)Repayments\w*Debt\w*",
            ],
            human_pattern=[
                r"(?i)repayment.*debt",
            ]
        )
        
        self.CommercialPaperNet = MapFact(
            fact="Commercial paper net change",
            priority=5,
            gaap_pattern=[
                r"(?i)ProceedsFromRepaymentsOfCommercialPaper\w*",
                r"(?i)\w*CommercialPaper\w*",
            ],
            human_pattern=[
                r"(?i)commercial\s+paper.*net",
            ]
        )
        
        self.CashFromFinancing = MapFact(
            fact="Net cash from financing activities",
            priority=10,
            gaap_pattern=[
                r"(?i)NetCashProvidedByUsedInFinancingActivities\b",
                r"(?i)PaymentsForProceedsFromOtherFinancingActivities\b",
                r"(?i)ProceedsFromPaymentsForOtherFinancingActivities\b",
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
            gaap_pattern=[
                r"(?i)CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalentsPeriodIncreaseDecrease\w*",
                r"(?i)CashAndCashEquivalentsPeriodIncreaseDecrease\b",
                r"(?i)CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents\b",
                r"(?i)CashAndCashEquivalentsAtCarryingValue\b",
                r"(?i)EffectOfExchangeRateOnCash\w*",
                r"(?i)IncomeTaxesPaidNet\b",
            ],
            human_pattern=[r"(?i)^net\s+(increase|decrease|change).*cash\b"]
        )
