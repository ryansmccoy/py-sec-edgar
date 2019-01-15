import os
import logging
import time

from datetime import datetime, timedelta
from urllib.parse import urljoin

import pandas as pd
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

year = datetime.today().year
month = datetime.today().month

latest_folder = "{}//{}".format(str(year), str(month).zfill(2))

SEC_EDGAR_ARCHIVES_URL = r'https://www.sec.gov/Archives/'

def SetupLogger():

    if not os.path.exists("log"):
        os.makedirs("log")

    time.strftime("py-sec-edgar.%Y%m%d_%H%M%S.log")

    recfmt = '(%(threadName)s) %(asctime)s.%(msecs)03d %(levelname)s %(filename)s:%(lineno)d %(message)s'

    timefmt = '%y%m%d_%H:%M:%S'

    # logging.basicConfig( level=logging.DEBUG,
    #                    format=recfmt, datefmt=timefmt)
    logging.basicConfig(filename=time.strftime("log/py-sec-edgar.%y%m%d_%H%M%S.log"),
                        filemode="w",
                        level=logging.INFO,
                        format=recfmt, datefmt=timefmt)

    logger = logging.getLogger()
    console = logging.StreamHandler()
    console.setLevel(logging.ERROR)
    logger.addHandler(console)

class Folders:

    ROOT_DIR = os.path.abspath(os.sep)
    BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    APP_DIR = os.path.abspath(os.path.dirname(__file__))

    REF_DIR = os.path.join(BASE_DIR, r'refdata')

    # this file maps CIK to tickers
    tickercheck = os.path.join(REF_DIR, "cik_tickers.xlsx")

    CONFIG_DIR = os.path.join(BASE_DIR, "config")
    SEC_DIR = os.path.join(ROOT_DIR, "sec_gov")
    EDGAR_DIR = os.path.join(SEC_DIR, "Archives", "edgar")
    DATA_DIR = os.path.join(EDGAR_DIR, r'data')
    MONTHLY_DIR = os.path.join(EDGAR_DIR, "monthly")
    FULL_INDEX_DIR = os.path.join(EDGAR_DIR, "full-index")
    DAILY_INDEX_DIR = os.path.join(EDGAR_DIR, "daily-index")

    # used as template
    TXT_FILING_DIR = os.path.join(EDGAR_DIR, "data", "CIK", "FOLDER")

    dirs_all = [SEC_DIR, DATA_DIR, EDGAR_DIR,
                MONTHLY_DIR, FULL_INDEX_DIR, DAILY_INDEX_DIR]

    for _ in dirs_all:
        if not os.path.exists(_):
            print("{} Doesn't Exists".format(_))
            print("Creating Directory {}".format(SEC_DIR))
            os.makedirs(_)

    edgar_Archives_url = r'https://www.sec.gov/Archives/'
    edgar_full_index = urljoin(edgar_Archives_url, 'edgar/full-index/')
    edgar_full_master_url = urljoin(edgar_full_index, 'master.idx')
    edgar_monthly_index = urljoin(edgar_Archives_url, 'edgar/monthly/')

    sec_dates = pd.date_range(
        datetime.now() - timedelta(days=365 * 22), datetime.now())
    sec_dates_weekdays = sec_dates[sec_dates.weekday < 5]
    sec_dates_weekdays = sec_dates_weekdays.sort_values(ascending=False)
    sec_dates_months = sec_dates_weekdays[sec_dates_weekdays.day ==
                                          sec_dates_weekdays[0].day]

class Config(Folders):

    # extract all contents from txt file
    extract_filing_contents = False

    # for complete list see py-sec-edgar/refdata/filing_types.xlsx
    # forms_list = ['10-K', '20-F', '10-K/A', '10-Q']
    forms_list = ['497', '497K']

    # the urls of all broker are stored in index files
    # so need to download these index files
    # below just says download all of them
    index_start_date = "1/1/1993"
    index_end_date = datetime.now().strftime("%m/%d/%Y")

    # file with list of all broker for given period
    index_files = ['master.idx']

    # https://www.perfect-privacy.com/
    # allows 30 simultaneous connections
    # if going to use proxy, please only download on the weekends
    VPN_PROVIDER = "PP"

    THROTTLE = True


CONFIG = Config()
