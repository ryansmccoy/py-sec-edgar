import os
from datetime import datetime, timedelta
from urllib.parse import urljoin

import pandas as pd

class BaseConfig:

    # top level folders
    ROOT_DIR = os.path.abspath(os.sep)
    BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    APP_DIR = os.path.abspath(os.path.dirname(__file__))

    # reference data files
    REF_DIR = os.path.join(BASE_DIR, r'refdata')
    MERGED_IDX_FILEPATH = os.path.join(REF_DIR, 'merged_idx_files.pq')
    TICKER_LIST_FILEPATH = os.path.join(REF_DIR, "tickers.csv")
    TICKER_CIK_FILEPATH = os.path.join(REF_DIR, "cik_tickers.csv.zip")

    # sec data directories
    SEC_DATA_DIR = os.path.join(ROOT_DIR, "sec_gov")
    EDGAR_DATA_DIR = os.path.join(SEC_DATA_DIR, "Archives", "edgar")
    DATA_DIR = os.path.join(EDGAR_DATA_DIR, r'data')
    MONTHLY_DATA_DIR = os.path.join(EDGAR_DATA_DIR, "monthly")
    FULL_INDEX_DATA_DIR = os.path.join(EDGAR_DATA_DIR, "full-index")
    DAILY_INDEX_DATA_DIR = os.path.join(EDGAR_DATA_DIR, "daily-index")
    FILING_DATA_DIR = os.path.join(EDGAR_DATA_DIR, "filings")
    # used as template
    TXT_FILING_DATA_DIR = os.path.join(EDGAR_DATA_DIR, "data", "CIK", "FOLDER")

    # create data directories
    dirs_all = [SEC_DATA_DIR, DATA_DIR, EDGAR_DATA_DIR,
                MONTHLY_DATA_DIR, FULL_INDEX_DATA_DIR, DAILY_INDEX_DATA_DIR]

    print("Checking for Output BaseConfig")

    for directory in dirs_all:
        if not os.path.exists(directory):
            print(f"{directory} Doesn't Exists")
            print(f"Creating Directory {directory}")
            try:
                os.makedirs(directory)
            except:
                raise PermissionError(f"Could not create {directory} Directory")

    # important urls
    edgar_Archives_url = r'https://www.sec.gov/Archives/'
    edgar_full_index = urljoin(edgar_Archives_url, 'edgar/full-index/')
    edgar_full_master_url = urljoin(edgar_full_index, 'master.idx')
    edgar_monthly_index = urljoin(edgar_Archives_url, 'edgar/monthly/')

    # important dates
    sec_dates = pd.date_range(
        datetime.now() - timedelta(days=365 * 22), datetime.now())
    sec_dates_weekdays = sec_dates[sec_dates.weekday < 5].sort_values(ascending=False)
    sec_dates_months = sec_dates_weekdays[sec_dates_weekdays.day ==
                                          sec_dates_weekdays[0].day]

    #HTTP config
    USER_AGENT = "Sample Company Name AdminContact@<sample company domain>.com"

class Config(BaseConfig):

    # extract all contents from txt file
    extract_filing_contents = False

    # for complete list see py-sec-edgar/refdata/filing_types.xlsx
    forms_list = ['10-K', '20-F', '10-K/A']
    # forms_list = ['497', '497K']
    # forms_list = ['8-K']
    # the urls of all broker are stored in index files
    # so need to download these index files
    # below just says download all of them
    # index_start_date = "1/1/1993"
    index_start_date = "1/1/2019"

    index_end_date = datetime.now().strftime("%m/%d/%Y")

    # file with list of all broker for given period
    index_files = ['master.idx']

    TEST_MODE = False


CONFIG = Config()
