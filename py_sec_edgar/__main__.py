# -*- coding: utf-8 -*-
"""Console script for td_trader

This script is the primary execution point for running the Daily and Intra-Day Execution Algo

Why does this file exist, and why __main__? For more info, read:

- https://www.python.org/dev/peps/pep-0338/
- https://docs.python.org/2/using/cmdline.html#cmdoption-m
- https://docs.python.org/3/using/cmdline.html#cmdoption-m
"""
import logging
import concurrent.futures
import logging

logger = logging.getLogger(__name__)

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import click
import pandas as pd
import pyarrow.parquet as pq

import py_sec_edgar.feeds.full_index

import concurrent.futures
import requests
from py_sec_edgar.settings import CONFIG

import os
from urllib.parse import urljoin
from pathlib import Path

def load_filing_index(ticker_list, form_list, merged_idx_filepath):

    # Downloads the list of filings on the SEC Edgar website
    py_sec_edgar.feeds.full_index.update_full_index_feed(skip_if_exists=True)

    # Used to convert CIK to Tickers
    url = r'https://www.sec.gov/include/ticker.txt'
    df_symbol_cik = pd.read_csv(url, delimiter="\t", names=['SYMBOL', 'CIK'])
    df_symbol_cik['SYMBOL'] = df_symbol_cik['SYMBOL'].str.upper()

    # IDX Files contain URLs to the Filings, so we need them
    df_merged_idx = pq.read_table(merged_idx_filepath).to_pandas().sort_values("Date Filed", ascending=False)

    # If you specified tickers in py-sec-edgar/py_sec_edgar/settings.py
    # Then load the file and filter out only the companies specified
    if ticker_list:
        df_ticker_list = pd.read_csv(ticker_list, header=None).iloc[:, 0].tolist()
        df_symbol_cik = df_symbol_cik[df_symbol_cik['SYMBOL'].isin(df_ticker_list)]

    # If you specified forms in py-sec-edgar/py_sec_edgar/settings.py
    # Then Filter the URL list to only the forms specified
    if form_list:
        logging.info('\n\n\n\tLoading Forms Filter\n\n\n')
        df_merged_idx = df_merged_idx[df_merged_idx['Form Type'].isin(CONFIG.forms_list)]

    # return only list of CIK tickers for companies and forms specified
    df_symbol_cik = df_symbol_cik.dropna(subset=['CIK'])
    df_symbol_cik['CIK'] = df_symbol_cik['CIK'].astype(int)
    cik_list = df_symbol_cik['CIK'].tolist()

    if ticker_list:
        df_merged_idx = df_merged_idx[df_merged_idx['CIK'].isin(cik_list)]
    #
    # # Create a new column in the dataframe of filings with the Output Filepaths
    # df_filings = df_merged_idx.assign(url=df_merged_idx['Filename'].apply(lambda x: urljoin(r'https://www.sec.gov/Archives/', x)))
    # df_filings = df_filings.assign(filepath=df_filings['Filename'].apply(lambda x: os.path.join(download_directory, x)))

    return df_merged_idx

def download_filing(filing_name, download_directory, sec_url=r'https://www.sec.gov/Archives/'):

    url = urljoin(sec_url,filing_name)
    filepath = os.path.join(download_directory, filing_name)

    directory = os.path.dirname(filepath)
    Path(directory).mkdir(parents=True, exist_ok=True)

    print(f"Downloading {url}")
    print(f"Saving to {filepath}")

    with requests.Session() as s:
        response = s.get(url)
        with open(filepath, 'w') as f:
            f.write(response.content.decode())

    return filepath

if __name__ == "__main__":

    download_directory = CONFIG.ARCHIVE_DIR

    filter_form_list = True
    ticker_list = CONFIG.TICKER_LIST_FILEPATH
    merged_idx_filepath = CONFIG.MERGED_IDX_FILEPATH

    df_merged_idx = load_filing_index(ticker_list, filter_form_list, merged_idx_filepath)

    # We can use a with statement to ensure threads are cleaned up promptly
    with concurrent.futures.ProcessPoolExecutor(max_workers=4) as executor:
        # Start the load operations and mark each future with its URL
        future_to_url = {
            executor.submit(download_filing, url, download_directory): url
            for url in df_merged_idx['Filename'].tolist()
        }
        # if CONFIG.extract_filing_contents:
        #
        #     for future in concurrent.futures.as_completed(future_to_url):
        #
        #         url = future_to_url[future]
        #
        #         try:
        #             filing_filepath = future.result()
        #         except Exception as exc:
        #             print(f'{url!r} generated an exception: {exc}')
        #         else:
        #             print(f'{url!r} page is saved {len(filing_filepath)}')
