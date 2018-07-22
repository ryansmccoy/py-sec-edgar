import os
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
class Folders(object):

    ROOT_DIR = os.path.abspath(os.sep)
    BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    APP_DIR = os.path.abspath(os.path.dirname(__file__))
    EXAMPLES_DIR = os.path.join(BASE_DIR,'examples')

    REF_DIR = os.path.join(BASE_DIR, r'refdata')

    # if you want to filter against a list of tickers, add them to tickers.csv
    tickers_filepath = os.path.join(EXAMPLES_DIR, r'tickers.csv')

    # this file maps CIK to tickers
    tickercheck = os.path.join(REF_DIR, "cik_tickers.xlsx")

    CONFIG_DIR = os.path.join(BASE_DIR, "config")
    SEC_DIR = os.path.join(ROOT_DIR, "sec_gov")
    EDGAR_DIR = os.path.join(SEC_DIR, "Archives","edgar")
    DATA_DIR = os.path.join(EDGAR_DIR, r'data')
    MONTHLY_DIR = os.path.join(EDGAR_DIR, "monthly")
    FULL_INDEX_DIR = os.path.join(EDGAR_DIR, "full-index")
    DAILY_INDEX_DIR = os.path.join(EDGAR_DIR, "daily-index")

    # TXT_LATEST = os.path.join(EDGAR_DIR, latest_folder)
    # used as template
    TXT_FILING_DIR = os.path.join(EDGAR_DIR, "data", "CIK", "FOLDER")

    dirs_all = [SEC_DIR, DATA_DIR, EDGAR_DIR, MONTHLY_DIR, FULL_INDEX_DIR, DAILY_INDEX_DIR]

    for _ in dirs_all:
        if not os.path.exists(_):
            print("{} Doesn't Exists".format(_))
            print("Creating Directory {}".format(SEC_DIR))
            os.makedirs(_)

    edgar_Archives_url = r'https://www.sec.gov/Archives/'
    edgar_full_index = urljoin(edgar_Archives_url,'edgar/full-index/')
    edgar_full_master_url = urljoin(edgar_full_index, 'master.idx')
    edgar_monthly_index = urljoin(edgar_Archives_url, 'edgar/monthly/')

    sec_dates = pd.date_range(datetime.now() - timedelta(days=365 * 22), datetime.now())
    sec_dates_weekdays = sec_dates[sec_dates.weekday < 5]
    sec_dates_weekdays = sec_dates_weekdays.sort_values(ascending=False)
    sec_dates_months = sec_dates_weekdays[sec_dates_weekdays.day == sec_dates_weekdays[0].day]

class Config(Folders):

    VPN_PROVIDER = "PP"

    # for complete list see py-sec-edgar/refdata/filing_types.xlsx
    forms_list = ['10-K', '20-F', '10-K/A', ]

    # the urls of all filings are stored in index files
    # so need to download these index files
    #below just says download all of them
    index_start_date = "1/1/1993"
    index_end_date = datetime.now().strftime("%m/%d/%Y")

    # file with list of all filings for given period
    index_files = ['master.idx']

    # index_files = ["company.gz",
    #                     "company.idx",
    #                     "company.Z",
    #                     "company.zip",
    #                     "crawler.idx",
    #                     "form.gz",
    #                     "form.idx",
    #                     "form.Z",
    #                     "form.zip",
    #                     "master.gz",
    #                     "master.idx",
    #                     "master.Z",
    #                     "master.zip",
    #                     "sitemap.quarterlyindex1.xml",
    #                     "xbrl.gz",
    #                     "xbrl.idx",
    #                     "xbrl.Z",
    #                     "xbrl.zip"]
