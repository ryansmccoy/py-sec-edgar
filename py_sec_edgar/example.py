# -*- coding: utf-8 -*-


"""Console script for py_sec_edgar."""

import os
import sys

import pandas as pd

import feeds as py_sec_edgar_feeds
import etl as py_sec_edgar_etl

from settings import CONFIG

pd.set_option('display.float_format', lambda x: '%.5f' % x)  # pandas
pd.set_option('display.max_columns', 100)
pd.set_option('display.max_rows', 100)
pd.set_option('display.width', 600)

from urllib.parse import urljoin
# from fastparquet import ParquetFile


def main(ticker_list=None, form_list=None):

    py_sec_edgar_feeds.download(save_idx_as_csv=True, skip_if_exists=True)

    merged_idx_files = os.path.join(CONFIG.REF_DIR, 'merged_idx_files.csv')

    df_idx = pd.read_csv(merged_idx_files, index_col=0, dtype={"CIK": int})

    df_idx = df_idx.sort_values("Date Filed", ascending=False)
    # df_idx = df_idx.set_index('CIK')

    if ticker_list:
        # load CIK to tickers
        df_cik_tickers = pd.read_excel(CONFIG.tickercheck)

        # filter cik list only tickers in tickers.csv file
        df_cik_tickers = df_cik_tickers[df_cik_tickers['SYMBOL'].isin(ticker_list)]

        list_of_ciks = df_cik_tickers['CIK'].tolist()

        df_idx = df_idx[df_idx['CIK'].isin(list_of_ciks)]

    if form_list:

        df_idx = df_idx[df_idx['Form Type'].isin(CONFIG.forms_list)]

        df_idx = df_idx.assign(url=df_idx['Filename'].apply(lambda x: urljoin(CONFIG.edgar_Archives_url, x)))

    for i, feed_item in df_idx.iterrows():

        py_sec_edgar_etl.filings(feed_item)


if __name__ == "__main__":

    # if you want to filter against a list of tickers, add them to tickers.csv
    tickers_filepath = os.path.join(CONFIG.APP_DIR, r'tickers.csv')

    ticker_list = pd.read_csv(tickers_filepath, header=None).iloc[:, 0].tolist()

    main(ticker_list=ticker_list, form_list=True)

    sys.exit()  # pragma: no cover
