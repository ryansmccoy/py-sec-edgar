# -*- coding: utf-8 -*-

"""Top-level package for Python SEC Edgar Data."""
import os
import time
from datetime import datetime, timedelta
from urllib.parse import urljoin

import pandas as pd

__author__ = """Ryan S. McCoy"""
__email__ = '18177650+ryansmccoy@users.noreply.github.com'
__version__ = '0.1.0'

import logging
logging.getLogger(__name__).addHandler(logging.NullHandler())

header_list = ["ACCESSION NUMBER", "CONFORMED SUBMISSION TYPE", "PUBLIC DOCUMENT COUNT",
               "CONFORMED PERIOD OF REPORT", "FILED AS OF DATE", "DATE AS OF CHANGE", "FILER", "COMPANY data",
               "COMPANY CONFORMED NAME", "CENTRAL INDEX KEY", "STANDARD INDUSTRIAL CLASSIFICATION", "IRS NUMBER",
               "STATE OF INCORPORATION", "FISCAL YEAR END", "FILING VALUES", "FORM TYPE", "SEC ACT",
               "SEC FILE NUMBER", "FILM NUMBER", "BUSINESS ADDRESS", "STREET 1", "STREET 2", "CITY", "STATE", "ZIP",
               "BUSINESS PHONE", "MAIL ADDRESS", "STREET 1", "STREET 2", "CITY", "STATE", "ZIP", "FORMER COMPANY",
               "FORMER CONFORMED NAME", "DATE OF NAME CHANGE"]

header = {
    "COMPANY data": {
        "COMPANY CONFORMED NAME": "",
        "CENTRAL INDEX KEY": "",
        "STANDARD INDUSTRIAL CLASSIFICATION": "",
        "IRS NUMBER": "",
        "STATE OF INCORPORATION": "",
        "FISCAL YEAR END": ""},
    "FILING VALUES": {
        "FORM TYPE": "",
        "SEC ACT": "",
        "SEC FILE NUMBER": "",
        "FILM NUMBER": ""},
    "BUSINESS ADDRESS": {
        "STREET 1": "",
        "STREET 2": "",
        "CITY": "",
        "STATE": "",
        "ZIP": "",
        "BUSINESS PHONE": ""},
    "MAIL ADDRESS": {
        "STREET 1": "",
        "STREET 2": "",
        "CITY": "",
        "STATE": "",
        "ZIP": ""},
    "FORMER COMPANY": {
        "FORMER CONFORMED NAME": "",
        "DATE OF NAME CHANGE": ""}
}

year = datetime.today().year
month = datetime.today().month
latest_folder = "{}//{}".format(str(year), str(month).zfill(2))
SEC_EDGAR_ARCHIVES_URL = r'https://www.sec.gov/Archives/'

from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())


def SetupLogger():

    if not os.path.exists("log"):
        os.makedirs("log")

    time.strftime("py-sec-edgar.%Y%m%d_%H%M%S.log")

    recfmt = '(%(threadName)s) %(asctime)s.%(msecs)03d %(levelname)s %(filename)s:%(lineno)d %(message)s'

    timefmt = '%y%m%d_%H:%M:%S'

    logging.basicConfig(filename=time.strftime("log/py-sec-edgar.%y%m%d_%H%M%S.log"),
                        filemode="w",
                        level=logging.INFO,
                        format=recfmt, datefmt=timefmt)

    logger = logging.getLogger()

    console = logging.StreamHandler()
    console.setLevel(logging.ERROR)

    logger.addHandler(console)

from py_sec_edgar.settings import Config

class Folders(Config):

    ROOT_DIR = os.path.abspath(os.sep)
    BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    APP_DIR = os.path.abspath(os.path.dirname(__file__))

    REF_DIR = os.path.join(BASE_DIR, r'refdata')

    CONFIG_DIR = os.path.join(BASE_DIR, "config")
    SEC_DIR = os.path.join(ROOT_DIR, "sec_gov")
    EDGAR_DIR = os.path.join(SEC_DIR, "Archives", "edgar")
    DATA_DIR = os.path.join(EDGAR_DIR, r'data')
    MONTHLY_DIR = os.path.join(EDGAR_DIR, "monthly")
    FULL_INDEX_DIR = os.path.join(EDGAR_DIR, "full-index")
    DAILY_INDEX_DIR = os.path.join(EDGAR_DIR, "daily-index")
    FILING_DIR = os.path.join(EDGAR_DIR, "filings")

    MERGED_IDX_FILE = os.path.join(REF_DIR, 'merged_idx_files.pq')
    TICKER_LIST = os.path.join(REF_DIR, "tickers.csv")
    TICKER_CIK = os.path.join(REF_DIR, "cik_tickers.csv")

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

CONFIG = Folders()

config = {
    'disable_existing_loggers': False,
    'version': 1,
    'formatters': {
        'short': {
            'format': '%(asctime)s %(levelname)s %(name)s: %(message)s'
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'formatter': 'short',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        '': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'plugins': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False
        }
    },
}

import logging.config

logging.config.dictConfig(config)
