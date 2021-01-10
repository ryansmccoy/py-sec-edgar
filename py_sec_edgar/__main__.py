# -*- coding: utf-8 -*-
"""Console script for td_trader

This script is the primary execution point for running the Daily and Intra-Day Execution Algo

Why does this file exist, and why __main__? For more info, read:

- https://www.python.org/dev/peps/pep-0338/
- https://docs.python.org/2/using/cmdline.html#cmdoption-m
- https://docs.python.org/3/using/cmdline.html#cmdoption-m
"""
import logging

logger = logging.getLogger(__name__)

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pprint import pprint
from urllib.parse import urljoin

import click
import pandas as pd
import pyarrow.parquet as pq

import py_sec_edgar.feeds.full_index
from py_sec_edgar.process import FilingProcessor
from py_sec_edgar.utilities import cik_column_to_list

from py_sec_edgar.settings import CONFIG

@click.command()
@click.option('--ticker-list', default=True)
@click.option('--form-list', default=True)
def main(ticker_list, form_list):

    # Downloads the list of filings on the SEC Edgar website
    py_sec_edgar.feeds.full_index.update_full_index_feed(skip_if_exists=True)

    # Used to convert CIK to Tickers
    df_cik_tickers = pd.read_csv(CONFIG.TICKER_CIK_FILEPATH)

    # IDX Files contain URLs to the Filings, so we need them
    df_merged_idx = pq.read_table(CONFIG.MERGED_IDX_FILEPATH).to_pandas().sort_values("Date Filed", ascending=False)

    # If you specified tickers in py-sec-edgar/py_sec_edgar/settings.py
    # Then load the file and filter out only the companies specified
    if ticker_list:
        ticker_list = pd.read_csv(CONFIG.TICKER_LIST_FILEPATH, header=None).iloc[:, 0].tolist()
        df_cik_tickers = df_cik_tickers[df_cik_tickers['SYMBOL'].isin(ticker_list)]

    # If you specified forms in py-sec-edgar/py_sec_edgar/settings.py
    # Then Filter the URL list to only the forms specified
    if form_list:
        logging.info('\n\n\n\tLoading Forms Filter\n\n\n')
        df_merged_idx = df_merged_idx[df_merged_idx['Form Type'].isin(CONFIG.forms_list)]

    # return only list of CIK tickers for companies and forms specified
    cik_list = cik_column_to_list(df_cik_tickers)

    if ticker_list:
        df_merged_idx = df_merged_idx[df_merged_idx['CIK'].isin(cik_list)]

    # Create a new column in the dataframe of filings with the Output Filepaths
    df_filings = df_merged_idx.assign(url=df_merged_idx['Filename'].apply(lambda x: urljoin(CONFIG.edgar_Archives_url, x)))

    # Initialize the FilingProcessor which will oversee the Extraction process
    filing_broker = FilingProcessor(filing_data_dir=CONFIG.TXT_FILING_DATA_DIR, edgar_Archives_url=CONFIG.edgar_Archives_url)

    for i, sec_filing in df_filings.iterrows():

        pprint(str(sec_filing))

        filing_broker.process(sec_filing)

    return 0

if __name__ == "__main__":

    main()
