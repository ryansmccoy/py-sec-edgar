import numpy as np

file = r'C:\@PROJECTS\py-sec-edgar\refdata\merged_idx_files.csv'

df_idx = pd.read_csv(file, index_col=0, dtype={"CIK": int})

df_idx['CIK'].nunique()
# 642,927

df_idx['Form Type'].nunique()
# 679

df_forms = df_idx.groupby(['Form Type']).size().to_frame('Form Type').sort_values('Form Type', ascending=False)

import feedparser

df_idx['Form Type'].str.contains("10-K")


from utilities import read_xml_feedparser

url = r'https://www.sec.gov/cgi-bin/browse-edgar?company=&CIK=&type=8-K&type=8-K&owner=exclude&count=400&action=getcurrent'
feed = feedparser.parse(url)
calendar = r'https://www.benzinga.com/calendar/earnings'
xpath = r'//*[@id="fin-cal-table"]/div[2]/div/table'
import io
import requests
import pandas as pd


fidelity = r'https://eresearch.fidelity.com/eresearch/conferenceCalls.jhtml?tab=earnings&begindate=1/29/2019'
df = pd.read_html(fidelity)
