from constants import *

# income_names = ['OperatingIncome', 'ProfitLoss', 'NetIncomeLoss', 'IncomeLossFromContinuingOperations', 'ComprehensiveIncomeNet', 'IncomeLoss', 'IncomeFromContinuingOperation']
gapp_income_patterns = [
    r"(?i)\bOperatingIncome\b",
    r"(?i)\bProfitLoss\b",
    r"(?i)\bNetIncomeLoss\b",
    r"(?i)\bIncomeLossFromContinuingOperations\b",
    r"(?i)\bComprehensiveIncomeNet\b",
    r"(?i)\bIncomeLoss\b",
    r"(?i)\bIncomeFromContinuingOperation\b"
]

class MapFact:

    def __init__(self, fact, human_pattern=[], gaap_pattern=[], strict_compare=False) -> None:
        self.fact = fact
        self.human_pattern = human_pattern
        self.gaap_pattern = gaap_pattern
        self.strict_compare = strict_compare
        self.index = None
        self.matches = []
        self.match = None
        # a master attr to attach some rows as sum for a specific row, so do not use that row in calc only use the master
        # every row should be potentially a sum of other rows and it will become a master, but master can have masters
        self.master = None



class IncomeStatementMap():

    # def __init__(self):
    #     self.TotalRevenue = MapFact(fact=TotalRevenue, gaap_pattern=['Revenue', 'Sales', 'Income'], highest=True)
    #     self.COGS = MapFact(fact=COGS, gaap_pattern=['CostOfGoodsAndServicesSold', 'CostOfGoodsSold', 'CostOfGoods', 'CostOfRevenue', 'CostOfSale'], highest=True)
    #     self.GrossProfit = MapFact(fact=GrossProfit, gaap_pattern=['GrossProfit'])
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
        self.TotalRevenue = MapFact(
            fact=TotalRevenue,
            gaap_pattern=[
                r"(?i)\btotal\w*revenue\b", r"(?i)\brevenue\w*total\b",
                r"(?i)\bsales\w*revenue\b", r"(?i)\bincome\w*revenue\b"
            ],
            human_pattern=[
                r"(?i)\btotal\s+\w*\s*revenue\b", r"(?i)\brevenue\s+\w*\s*total\b",
                r"(?i)\bsales\s+\w*\s*revenue\b", r"(?i)\bincome\s+\w*\s*revenue\b"
            ]
        )

        self.COGS = MapFact(
            fact=COGS,
            gaap_pattern=[
                r"(?i)\bcost\w*goods\b", r"(?i)\bcost\w*goodssold\b",
                r"(?i)\bcost\w*revenue\b", r"(?i)\bcost\w*sales\b"
            ],
            human_pattern=[
                r"(?i)\bcost\s+\w*\s*goods\b", r"(?i)\bcost\s+\w*\s*goods\s*and\s*services\b",
                r"(?i)\bcost\s+\w*\s*sales\b", r"(?i)\brevenue\s+\w*\s*cost\b"
            ]
        )

        self.GrossProfit = MapFact(
            fact=GrossProfit,
            gaap_pattern=[
                r"(?i)\bgross\w*profit\b", r"(?i)\bprofit\w*gross\b"
            ],
            human_pattern=[
                r"(?i)\bgross\s+\w*\s*profit\b", r"(?i)\bgross\b"
            ]
        )

        self.SGnA = MapFact(
            fact=SGnA,
            gaap_pattern=[
                r"(?i)\bselling\w*general\w*administrative\b", r"(?i)\bselling\w*marketing\b",
                r"(?i)\bgeneral\w*administrative\b",
            ],
            human_pattern=[
                r"(?i)\bselling\s+\w*\s+general\s+\w*\s+administrative\b",  r"(?i)\bsales\s+\w*\s+marketing\b",
                r"(?i)\bgeneral\s+\w*\s+administrative\b", r"(?i)\badministrative\b",
                r"(?i)\bsg&a\b"

            ]
        )

        self.RnD = MapFact(
            fact=RnD,
            gaap_pattern=[
                r"(?i)\bresearch\w*development\b",
            ],
            human_pattern=[
                r"(?i)\bresearch\s+\w*\s+development\b", r"(?i)\bresearch\b", r"(?i)\bdevelopment\b", r"(?i)\bR&D\b"

            ]
        )

        self.AmortizationDepreciation = MapFact(
            fact=AmortizationDepreciation,
            gaap_pattern=[
                r"(?i)\bamortization\b", r"(?i)\bdepreciation\b",
                r"(?i)\bdepreciation\w*amortization\b"            ],
            human_pattern=[
                r"(?i)\bamortization\b", r"(?i)\bdepreciation\b",
                r"(?i)\bdepreciation\s+\w*\s+amortization\b", r"(?i)\bD\s*&\s*A\b"
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
