import pandas as pd

def calc_yoy_growth2(df):
    # Calculate year-over-year growth in revenue
    yoy_growth = df.loc['total revenue'].pct_change() * 100
    print(yoy_growth)
    # Calculate growth over 3 years
    three_year_growth = ((df.loc['total revenue'] / df.loc['total revenue'].shift(3)) - 1) * 100
    # Calculate growth over 5 years
    five_year_growth = ((df.loc['total revenue'] / df.loc['total revenue'].shift(5)) - 1) * 100
    # Create a DataFrame to hold the additional rows
    additional_rows = pd.DataFrame(
        (yoy_growth,
        three_year_growth,
        five_year_growth)
    , index=['YoY Growth', '3-Year Growth', '5-Year Growth'])
    # Concatenate the additional rows with the original DataFrame
    df = pd.concat([df, additional_rows])

    return df

def acquirer_multiple(df):
    """
    The Acquirer’s Multiple = (the enterprise value) / (operating earnings)
    The enterprise value = market cap + debt + like debt + preferred stock + minority interests – cash – cash equivalent
    Operating Earnings = Revenue - Cost of Goods Sold - Selling, General, and Administrative Costs - Depreciation and Amortization
    """
    # balance sheet
    market_cap = get_market_cap()
    debt = longtermdebt + shortermdebt 
    preferred_stock = 0
    minority_interests = 0
    cash = cash
    cash_eqvl = 0

    EV = market_cap + debt + preferred_stock + minority_interests + cash + cash_eqvl

    # income statment
    revenue = revenue #usually first item
    COGS = costofrevenue
    SG_AC = GeneralAndAdministrativeExpense
    D_A = Depreciation + Amortization

    operating_earning = revenue - COGS - SG_AC - D_A

    acquirer_mu = EV / operating_earning

def get_roic(income_statement, balance_sheet):
    '''
    EBIT = operating income
    Return on invested capital = EBIT / 
    ROIC = (net income – dividends) / (debt + equity)
    '''

    common_columns = list(set(income_statement.columns).intersection(balance_sheet.columns))

    fact_name = 'ROIC'
    income_statement.loc[fact_name] = None
    for column in common_columns:
        try:
            Operating_income = income_statement.loc['Operating income', column]
        except KeyError:
            Operating_income = income_statement.loc['EBT', column]
        Debt = (balance_sheet.loc['Short term debt', column]) + (balance_sheet.loc['Long term debt', column])
        equity = balance_sheet.loc['Total equity', column]
        ROIC = Operating_income / (Debt + equity)
        income_statement.loc[fact_name, column] = ROIC * 100
        print(ROIC)

    return income_statement
    

def get_growth_rate():

    '''
    revenue growth rate
    Earning per share (EPS) growth rate
    Equity or book value per share (BVPS) growth rate
    Free cash flow (FCF or cash) growth rate

    '''
    shares = get_number_of_shares()
    revenue = revenue #usually first item






