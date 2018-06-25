import os
import platform
import sys
from datetime import datetime
from urllib.parse import urljoin
from datetime import timedelta
import pandas as pd

year = datetime.today().year
month = datetime.today().month

latest_folder =  "{}//{}".format(str(year) ,str(month).zfill(2))

SEC_EDGAR_ARCHIVES_URL = r'https://www.sec.gov/Archives/'

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

# print(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class Config(object):

    ROOT_DIR = os.path.abspath(os.sep)

    BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    # BASE_DIR = r'C:\@CODE\py-sec-edgar-data'
    APP_DIR = os.path.abspath(os.path.dirname(__file__))
    # APP_DIR = r'C:\@CODE\py-sec-edgar-data\py_sec_edgar_data'
    CONFIG_DIR = os.path.join(BASE_DIR, "config")
    # todo: need to reorganize get rid of irrelavent
    SEC_DIR = os.path.join(ROOT_DIR, "sec_gov")
    DATA_DIR = os.path.join(SEC_DIR, r'data')
    SEC_EDGAR_DIR = os.path.join(SEC_DIR, "Archives\edgar")
    SEC_MONTHLY_DIR = os.path.join(SEC_EDGAR_DIR, "monthly")
    SEC_FULL_INDEX_DIR = os.path.join(SEC_EDGAR_DIR, "full-index")
    SEC_DAILY_INDEX_DIR = os.path.join(SEC_EDGAR_DIR, "daily-index")
    SEC_TXT_LATEST = os.path.join(SEC_EDGAR_DIR, latest_folder)
    SEC_TXT_FILING_DIR =  os.path.join(SEC_EDGAR_DIR, "data", "CIK", "FOLDER")
    SEC_XBRL_ZIP_DIR = os.path.join(SEC_EDGAR_DIR, "xbrl-zip")
    SEC_XBRL_TXT_DIR = os.path.join(SEC_EDGAR_DIR, "xbrl")

    dirs_all = [SEC_DIR, DATA_DIR, SEC_EDGAR_DIR, SEC_TXT_FILING_DIR, SEC_MONTHLY_DIR, SEC_FULL_INDEX_DIR, SEC_DAILY_INDEX_DIR, SEC_TXT_LATEST, SEC_XBRL_TXT_DIR]

    for _ in dirs_all:

        if not os.path.exists(_):
            print("{} Doesn't Exists".format(_))
            print("Creating Directory")
            os.makedirs(_)
        else:
            print("\t SEC Filing Output Directory: \t{}".format(_))

    tickercheck = os.path.join(CONFIG_DIR, "TICKERCHECK_CIK_COMPANIES_ONLY.xlsx")
    cik_ticker = os.path.join(CONFIG_DIR, "cik_ticker_name_exchange_sic_business_incorporated_irs.xlsx")
    monthly_urls = os.path.join(CONFIG_DIR, "sec_gov_archives_edgar_monthly_xbrl_urls")

    edgar_Archives_url = r'https://www.sec.gov/Archives/'
    edgar_full_index = urljoin(edgar_Archives_url,'edgar/full-index/')
    edgar_full_master = urljoin(edgar_full_index,'master.idx')
    edgar_monthly_index = urljoin(edgar_Archives_url, 'edgar/monthly/')

    sec_dates = pd.date_range(datetime.now() - timedelta(days=365 * 22), datetime.now())
    sec_dates_weekdays = sec_dates[sec_dates.weekday < 5]
    sec_dates_weekdays = sec_dates_weekdays.sort_values(ascending=False)
    sec_dates_months = sec_dates_weekdays[sec_dates_weekdays.day == sec_dates_weekdays[0].day]
