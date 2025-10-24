from constants import *
import re

"""
Comprehensive Financial Statement Mapping System

This module provides robust pattern matching for:
- Income Statements
- Balance Sheets  
- Cash Flow Statements

Strategy:
1. GAAP taxonomy matching (most reliable)
2. IFRS taxonomy matching (for international companies)
3. Human-readable text matching
4. Fuzzy/flexible matching for variations
5. Multiple passes with decreasing strictness
"""

# Common patterns for net income that appear in multiple contexts
gaap_income_patterns = [
    r"(?i)\bOperatingIncome\b",
    r"(?i)\bProfitLoss\b",
    r"(?i)\bNetIncomeLoss\b",
    r"(?i)\bIncomeLossFromContinuingOperations\b",
    r"(?i)\bComprehensiveIncomeNet\b",
    r"(?i)\bIncomeLoss\b",
    r"(?i)\bIncomeFromContinuingOperation\b"
]


class MapFact:
    """
    Represents a mapping between company-specific financial terms and standardized terms.
    
    Attributes:
        fact: Standardized fact name
        gaap_pattern: Regex patterns for US-GAAP taxonomy
        ifrs_pattern: Regex patterns for IFRS taxonomy
        human_pattern: Regex patterns for human-readable labels
        strict_compare: If True, require exact match
        priority: Higher priority facts are matched first (1-10)
    """

    def __init__(self, fact, human_pattern=[], gaap_pattern=[], ifrs_pattern=[], 
                 strict_compare=False, priority=5) -> None:
        self.fact = fact
        self.human_pattern = human_pattern if isinstance(human_pattern, list) else [human_pattern]
        self.gaap_pattern = gaap_pattern if isinstance(gaap_pattern, list) else [gaap_pattern]
        self.ifrs_pattern = ifrs_pattern if isinstance(ifrs_pattern, list) else [ifrs_pattern]
        self.strict_compare = strict_compare
        self.priority = priority
        self.index = None
        self.matches = []
        self.match = None
        self.master = None



class IncomeStatementMap():
    """
    Comprehensive mapping for Income Statement line items.
    
    Covers:
    - Revenue (all forms)
    - COGS and direct costs
    - Operating expenses (SG&A, R&D, D&A)
    - Operating income
    - Non-operating items (interest, investments, FX)
    - Income taxes
    - Net income
    - EPS and shares
    """
    #     self.SGnA = MapFact(fact=SGnA, gaap_pattern=['SellingGeneralAndAdministrative', 'SellingAndMarketing', 'GeneralAndAdministrative'], highest=True)
    #     self.RnD = MapFact(fact=RnD, gaap_pattern=['ResearchAndDevelopment'], highest=True)
    #     self.AmoritizationDepreciatio = MapFact(fact=AmoritizationDepreciatio, gaap_pattern=['Amortization'], highest=True)
    #     self.OtherOperatingExpense = MapFact(fact=OtherOperatingExpense, gaap_pattern=['OtherOperatingIncomeExpense'])
    #     self.TotalOperatingExpense = MapFact(fact=TotalOperatingExpense, gaap_pattern=['OperatingExpenses']) #  equation="sum of everythin agter Gross profit",
    #     self.TotalCostAndExpenses = MapFact(fact='C&E', gaap_pattern=['CostsAndExpenses', 'LossesAndExpenses'])
    #     self.OperatingIncome = MapFact(fact=OperatingIncome, gaap_pattern=['OperatingIncome', 'IncomeLossFromContinuingOperations', 'ProfitLoss']) # equation="Gross profit - Total operating expense",
    #     self.InterestExpense = MapFact(fact=InterestExpense, gaap_pattern=['InterestExpense'], strict_compare=True)
    #     self.InterestInvestmentIncome = MapFact(fact=InterestInvestmentIncome, gaap_pattern=['InvestmentIncomeInterest', 'InterestAndOtherIncome'], strict_compare=True)
    #     self.CurencyExchange = MapFact(fact=CurencyExchange, gaap_pattern=[])
    #     self.OtherNonOperationgIncomeExpense = MapFact(fact=OtherNonOperationgIncomeExpense, gaap_pattern=['OtherNonoperatingIncomeExpense'])
    #     self.TotalNonOperationgIncomeExpense = MapFact(fact=TotalNonOperationgIncomeExpense, gaap_pattern=['NonoperatingIncomeExpense', 'Nonoperating'])
    #     self.EBTexcl = MapFact(fact=EBTexcl, gaap_pattern=income_names)
    #     self.IncomeTaxExpense = MapFact(fact=IncomeTaxExpense, gaap_pattern=['IncomeTaxExpense'])
    #     self.NetIncome = MapFact(fact=NetIncome, gaap_pattern=income_names) #  equation="EBT - Income tax expense",
    #     self.MinorityInterest = MapFact(fact=MinorityInterest, gaap_pattern=['AttributableToNoncontrollinterest', 'AttributableToNoncontrollingInterest'])
    #     self.EarningsPerShareBasic = MapFact(fact=EarningsPerShareBasic, gaap_pattern=['EarningsPerShareBasic'])
    #     self.EarningsPerShareDiluted = MapFact(fact=EarningsPerShareDiluted, gaap_pattern=['EarningsPerShareDiluted'])
    #     self.WeightedAverageSharesOutstandingBasic =  MapFact(fact=WeightedAverageSharesOutstandingBasic, gaap_pattern=['WeightedAverageNumberOfSharesOutstandingBasic'])
    #     self.WeightedAverageSharesOutstandingDiluted = MapFact(fact=WeightedAverageSharesOutstandingDiluted, gaap_pattern=['WeightedAverageNumberOfDilutedSharesOutstanding'])
    
    def __init__(self):
        # ============ REVENUE ============
        self.TotalRevenue = MapFact(
            fact=TotalRevenue,
            priority=10,  # Highest priority
            gaap_pattern=[
                # Direct revenue matches
                r"(?i)\bRevenues?\b",
                r"(?i)\bSalesRevenueNet\b",
                r"(?i)\bRevenueFromContractWithCustomer\w*\b",
                r"(?i)\bSalesRevenueGoodsNet\b",
                r"(?i)\bSalesRevenueServicesNet\b",
                # Total revenue variants
                r"(?i)\bRevenueNet\b",
                r"(?i)\bTotalRevenue\b",
                # Sales variants
                r"(?i)\bNetSales\b",
                r"(?i)\bSales\b",
            ],
            ifrs_pattern=[
                r"(?i)\bRevenue\b",
                r"(?i)\bTurnover\b",
            ],
            human_pattern=[
                # Total revenue variations
                r"(?i)^\s*total\s+\w*\s*revenues?\b",
                r"(?i)^\s*net\s+sales\b",
                r"(?i)^\s*revenues?\s*,?\s*net\b",
                r"(?i)^\s*sales\b",
                r"(?i)^\s*total\s+net\s+revenues?\b",
                r"(?i)^\s*net\s+revenues?\b",
            ]
        )

        # ============ COST OF REVENUE ============
        self.COGS = MapFact(
            fact=COGS,
            priority=9,
            gaap_pattern=[
                # Cost of goods
                r"(?i)\bCostOfGoodsAndServicesSold\b",
                r"(?i)\bCostOfGoodsSold\b",
                r"(?i)\bCostOfGoods\b",
                # Cost of revenue/sales
                r"(?i)\bCostOfRevenue\b",
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
                r"(?i)^\s*cost\s+of\s+\w*\s*goods\b",
                r"(?i)^\s*cost\s+of\s+\w*\s*sales?\b",
                r"(?i)^\s*cost\s+of\s+\w*\s*revenues?\b",
                r"(?i)^\s*cost\s+of\s+\w*\s*services\b",
                r"(?i)^\s*cost\s+of\s+\w*\s*products?\b",
                r"(?i)\bcosts\s+and\s+expenses\b",
            ]
        )

        # ============ GROSS PROFIT ============
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
                r"(?i)^\s*gross\s+profit\b",
                r"(?i)^\s*gross\s+margin\b",
                r"(?i)^\s*gross\s+income\b",
            ]
        )

        # ============ OPERATING EXPENSES ============
        self.SGnA = MapFact(
            fact=SGnA,
            priority=7,
            gaap_pattern=[
                r"(?i)\bSellingGeneralAndAdministrativeExpense\b",
                r"(?i)\bGeneralAndAdministrativeExpense\b",
                r"(?i)\bSellingAndMarketingExpense\b",
                r"(?i)\bSG&AExpense\b",
                r"(?i)\bMarketingAndAdvertisingExpense\b",
            ],
            human_pattern=[
                r"(?i)\bselling\s*,?\s*general\s+and\s+administrative\b",
                r"(?i)\bgeneral\s+and\s+administrative\b",
                r"(?i)\bsales\s+and\s+marketing\b",
                r"(?i)\bsg\s*&\s*a\b",
                r"(?i)\bselling\s+and\s+administrative\b",
                r"(?i)^\s*administrative\s+expenses?\b",
            ]
        )

        self.RnD = MapFact(
            fact=RnD,
            priority=7,
            gaap_pattern=[
                r"(?i)\bResearchAndDevelopmentExpense\b",
                r"(?i)\bResearchDevelopment\b",
                r"(?i)\bR&DExpense\b",
            ],
            human_pattern=[
                r"(?i)\bresearch\s+and\s+development\b",
                r"(?i)\br\s*&\s*d\b",
                r"(?i)^\s*research\s+expenses?\b",
            ]
        )

        self.AmortizationDepreciation = MapFact(
            fact=AmortizationDepreciation,
            priority=6,
            gaap_pattern=[
                r"(?i)\bDepreciationAndAmortization\b",
                r"(?i)\bDepreciationDepletionAndAmortization\b",
                r"(?i)\bAmortizationOfIntangibleAssets\b",
                r"(?i)\bDepreciation\b",
                r"(?i)\bAmortization\b",
            ],
            human_pattern=[
                r"(?i)\bdepreciation\s+and\s+amortization\b",
                r"(?i)\bamortization\s+and\s+depreciation\b",
                r"(?i)\bd\s*&\s*a\b",
                r"(?i)^\s*depreciation\b",
                r"(?i)^\s*amortization\b",
            ]
        )

        self.OtherOperatingExpense = MapFact(
            fact=OtherOperatingExpense,
            gaap_pattern=[
                r"(?i)\bother\w*operating\w*incomeexpense\b", r"(?i)\bother\w*expense\b"
            ],
            human_pattern=[
                r"(?i)\bother\s+\w*\s+operating\s+\w*\s+income\s*expense\b", r"(?i)\bother\s+\w*\s+expenses\b"
            ]
        )

        self.TotalOperatingExpense = MapFact(
            fact=TotalOperatingExpense,
            gaap_pattern=[
                r"(?i)\boperating\w*expenses\b"
            ],
            human_pattern=[
                r"(?i)\btotal\s+\w*\s+operating\s+\w*\s+expenses\b"
            ]
        )

        self.TotalCostAndExpenses = MapFact(
            fact=TotalCostAndExpenses,
            gaap_pattern=[
                r"(?i)\bcosts\w*expenses\b", r"(?i)\blosses\w*expenses\b"
            ],
            human_pattern=[
                r"(?i)\btotal\s+\w*\s+costs\s+\w*\s+expenses\b", r"(?i)\blosses\s+\w*\s+expenses\b"
            ]
        )

        self.OperatingIncome = MapFact(
            fact=OperatingIncome,
            gaap_pattern=[
                r"(?i)\boperating\w*income\b",  r"(?i)\bincome\w*loss\b",
                r"(?i)\bprofit\w*loss\b", *gapp_income_patterns
            ],
            human_pattern=[
                r"(?i)\boperating\s+\w*\s+income\b", r"(?i)\bincome\s+\w*\s+loss\b",
                r"(?i)\bprofit\s+\w*\s+loss\b"
            ]
        )

        self.InterestExpense = MapFact(
            fact=InterestExpense,
            gaap_pattern=[
                r"(?i)\binterest\w*expense\b"
            ],
            human_pattern=[
                r"(?i)\binterest\s+\w*\s+expense\b"
            ],
            strict_compare=True
        )

        self.InterestInvestmentIncome = MapFact(
            fact=InterestInvestmentIncome,
            gaap_pattern=[
                r"(?i)\binvestment\w*income\w*interest\b", r"(?i)\binterest\w*otherincome\b"
            ],
            human_pattern=[
                r"(?i)\binvestment\s+\w*\s+income\s+\w*\s+interest\b",  r"(?i)\binterest\s+\w*\s+and\s+other\s+income\b"
            ],
            strict_compare=True
        )

        # The other entries follow the same format.

        self.CurencyExchange = MapFact(
            fact=CurencyExchange,
            gaap_pattern=[
                r"(?i)\bcurrency\w*exchange\b"
            ],
            human_pattern=[
                r"(?i)\bcurrency\s+\w*\s+exchange\b"
            ]
        )

        self.OtherNonOperatingIncomeExpense = MapFact(
            fact=OtherNonOperatingIncomeExpense,
            gaap_pattern=[
                r"(?i)\bother\w*nonoperating\w*incomeexpense\b"
            ],
            human_pattern=[
                r"(?i)\bother\s+\w*\s+nonoperating\s+\w*\s+income\s*expense\b"
            ]
        )

        self.TotalNonOperatingIncomeExpense = MapFact(
            fact=TotalNonOperatingIncomeExpense,
            gaap_pattern=[
                r"(?i)\bnonoperating\w*incomeexpense\b", r"(?i)\bnonoperating\b"
            ],
            human_pattern=[
                r"(?i)\btotal\s+\w*\s+nonoperating\s+\w*\s+income\s*expense\b", r"(?i)\bnonoperating\b"
            ]
        )

        self.EBTexcl = MapFact(
            fact=EBTexcl,
            gaap_pattern=[
                r"(?i)\bebt\w*excluding\w*unusual\w*items\b" , *gapp_income_patterns
            ],
            human_pattern=[
                r"(?i)\bebt\s+\w*\s+excluding\s+unusual\s+items\b"
            ]
        )

        self.AssetWritedown = MapFact(
            fact=AssetWritedown,
            gaap_pattern=[
                r"(?i)\basset\w*writedown\b"
            ],
            human_pattern=[
                r"(?i)\basset\s+\w*\s+writedown\b"
            ]
        )

        self.LegalSettlements = MapFact(
            fact=LegalSettlements,
            gaap_pattern=[
                r"(?i)\blegal\w*settlements\b"
            ],
            human_pattern=[
                r"(?i)\blegal\s+\w*\s+settlements\b"
            ]
        )

        self.MergerRestructuringCharges = MapFact(
            fact=MergerRestructuringCharges,
            gaap_pattern=[
                r"(?i)\bmerger\w*restructuring\w*charges\b"
            ],
            human_pattern=[
                r"(?i)\bmerger\s+\w*\s+restructuring\s+\w*\s+charges\b"
            ]
        )

        self.GainLossSaleInvestments = MapFact(
            fact="Gain/loss on sale of investments",
            gaap_pattern=[
                r"(?i)\b(gain|loss)\w*sale\w*investments\b"  # Matches either "gain" or "loss"
            ],
            human_pattern=[
                r"(?i)\b(gain|loss)\s+\w*\s+sale\s+investments\b"  # Matches either "gain" or "loss"
            ]
        )

        self.GainLossSaleAssets = MapFact(
            fact="Gain/loss on sale of assets",
            gaap_pattern=[
                r"(?i)\b(gain|loss)\w*sale\w*assets\b"  # Matches either "gain" or "loss"
            ],
            human_pattern=[
                r"(?i)\b(gain|loss)\s+\w*\s+sale\s+assets\b"  # Matches either "gain" or "loss"
            ]
        )


        self.OtherUnusualItems = MapFact(
            fact=OtherUnusualItems,
            gaap_pattern=[
                r"(?i)\bother\w*unusual\w*items\b"
            ],
            human_pattern=[
                r"(?i)\bother\s+\w*\s+unusual\s+items\b"
            ]
        )

        self.EBTincl = MapFact(
            fact=EBTincl,
            gaap_pattern=[
                r"(?i)\bebt\w*include\w*unusual\w*items\b", *gapp_income_patterns
            ],
            human_pattern=[
                r"(?i)\bebt\s+\w*\s+include\s+unusual\s+items\b"
            ]
        )

        self.IncomeTaxExpense = MapFact(
            fact=IncomeTaxExpense,
            gaap_pattern=[
                r"(?i)\bincome\w*taxexpense\b"
            ],
            human_pattern=[
                r"(?i)\bincome\s+\w*\s+tax\s+expense\b"
            ]
        )

        self.NetIncome = MapFact(
            fact=NetIncome,
            gaap_pattern=[
                r"(?i)\bnet\w*income\b", r"(?i)\bincome\w*net\b", *gapp_income_patterns
            ],
            human_pattern=[
                r"(?i)\bnet\s+\w*\s+income\b", r"(?i)\bincome\s+\w*\s+net\b"
            ]
        )

        self.MinorityInterest = MapFact(
            fact=MinorityInterest,
            gaap_pattern=[
                r"(?i)\bminority\w*interest\b"
            ],
            human_pattern=[
                r"(?i)\bminority\s+\w*\s+interest\b"
            ]
        )

        self.EarningsPerShareBasic = MapFact(
            fact=EarningsPerShareBasic,
            gaap_pattern=[
                r"(?i)\bearnings\w*per\w*share\w*basic\b"
            ],
            human_pattern=[
                r"(?i)\bEPS\s+basic/weighted"
            ]
        )

        self.EarningsPerShareDiluted = MapFact(
            fact=EarningsPerShareDiluted,
            gaap_pattern=[
                r"(?i)\bearnings\w*per\w*share\w*diluted\b"
            ],
            human_pattern=[
                r"(?i)\bEPS\s+diluted\b"
            ]
        )

        self.WeightedAverageSharesOutstandingBasic = MapFact(
            fact=WeightedAverageSharesOutstandingBasic,
            gaap_pattern=[
                r"(?i)\bweighted\w*average\w*shares\w*outstanding\w*basic\b"
            ],
            human_pattern=[
                r"(?i)\bweighted\s+average\s+shares\s+outstanding\s+basic\b"
            ]
        )

        self.WeightedAverageSharesOutstandingDiluted = MapFact(
            fact=WeightedAverageSharesOutstandingDiluted,
            gaap_pattern=[
                r"(?i)\bweighted\w*average\w*shares\w*outstanding\w*diluted\b"
            ],
            human_pattern=[
                r"(?i)\bweighted\s+average\s+shares\s+outstanding\s+diluted\b"
            ]
        )
