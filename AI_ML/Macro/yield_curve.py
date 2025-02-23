# # Yield Curve
# 
# The visualization displays the daily U.S. Treasury yield curve from one month bills to 30 year bonds. Used web scraper to pull in the data.

# Import notebook libraries and dependencies
import os
import requests
import pandas as pd
import numpy as np
import plotly.express as px
from bs4 import BeautifulSoup


# Scrape U.S. Treasury data
url = "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/pages/xmlview?data=daily_treasury_real_yield_curve&field_tdr_date_value_month=202502"
soup = BeautifulSoup(requests.get(url).text,'lxml')
table = soup.find_all('m:properties')
tbondvalues = []
for i in table:
    # tbondvalues.append([i.find('d:new_date').text[:10],i.find('d:bc_1month').text,i.find('d:bc_2month').text,i.find('d:bc_3month').text,i.find('d:bc_6month').text,i.find('d:bc_1year').text,i.find('d:bc_2year').text,i.find('d:bc_3year').text,i.find('d:bc_5year').text,i.find('d:bc_10year').text,i.find('d:bc_20year').text,i.find('d:bc_30year').text])
    tbondvalues.append([i.find('d:NEW_DATE').text[:10],i.find('d:TC_5YEAR').text,i.find('d:TC_7YEAR').text,i.find('d:TC_10YEAR').text,i.find('d:TC_20YEAR').text,i.find('d:TC_30YEAR').text])
ustcurve = pd.DataFrame(tbondvalues,columns=['date','5y','7y', '10y', '20y','30y'])


# Clean data
ustcurve.iloc[:,1:] = ustcurve.iloc[:,1:].apply(pd.to_numeric)#/100
ustcurve['date'] = pd.to_datetime(ustcurve['date'])
yield_curve=ustcurve.set_index('date').sort_index(ascending=False)
print(yield_curve)
yield_curve.head()



# Set today's date and plot the yield curve

def get_yield_curve_vis():
    yield_curve_vis = px.line(yield_curve.iloc[0],
                              title='U.S. Treasury Yield Curve (%)')
    yield_curve_vis.update_layout(
        xaxis_title="Maturity",
        yaxis_title="Treasury Yield")
    return(yield_curve_vis)


print(get_yield_curve_vis())

