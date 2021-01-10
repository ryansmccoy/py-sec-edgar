# -*- coding: utf-8 -*-

"""Top-level package for Python SEC Edgar Data."""

__author__ = """Ryan S. McCoy"""
__email__ = 'github@ryansmccoy.com'
__version__ = '0.1.0'
import logging

logging.getLogger(__name__).addHandler(logging.NullHandler())

import os
import time
from datetime import datetime

import pandas as pd

pd.set_option('display.float_format', lambda x: '%.5f' % x)  # pandas
pd.set_option('display.max_columns', 100)
pd.set_option('display.max_rows', 100)
pd.set_option('display.width', 600)


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


# CONFIG = BaseConfig()

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
