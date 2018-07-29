# -*- coding: utf-8 -*-


"""Console script for py_sec_edgar."""

import os
import sys

sys.path.insert(0, "../py_sec_edgar")

import click
import pandas as pd

import py_sec_edgar.feeds
import py_sec_edgar.filing
import py_sec_edgar.extract_and_transform

from py_sec_edgar import CONFIG

pd.set_option('display.float_format', lambda x: '%.5f' % x)  # pandas
pd.set_option('display.max_columns', 100)
pd.set_option('display.max_rows', 100)
pd.set_option('display.width', 600)

from urllib.parse import urljoin
# from fastparquet import ParquetFile


@click.command()
def main(filter_ticker_list=False, filter_form_list=True):

    py_sec_edgar.feeds.full_index.download(save_idx_as_csv=True, skip_if_exists=True)

    merged_idx_files = os.path.join(CONFIG.REF_DIR, 'merged_idx_files.csv')

    # pf = ParquetFile(merged_idx_files.replace(".csv",".parq"))
    # df_idx = pf.to_pandas()

    df_idx = pd.read_csv(merged_idx_files, index_col=0, dtype={"CIK": int})

    df_idx = df_idx.sort_values("Date Filed", ascending=False)
    # df_idx = df_idx.set_index('CIK')

    if filter_ticker_list:
        # load ticker lookup and lookup CIK
        df_tickers = pd.read_csv(CONFIG.tickers_filepath, header=None)

        list_of_tickers = df_tickers.iloc[:, 0].tolist()

        # load CIK to tickers
        df_cik_tickers = pd.read_excel(CONFIG.tickercheck)

        # filter cik list only tickers in tickers.csv file
        df_cik_tickers = df_cik_tickers[df_cik_tickers['SYMBOL'].isin(
            list_of_tickers)]

        list_of_ciks = df_cik_tickers['CIK'].tolist()

        df_idx = df_idx[df_idx['CIK'].isin(list_of_ciks)]

    if filter_form_list:

        df_idx = df_idx[df_idx['Form Type'].isin(CONFIG.forms_list)]

        df_idx = df_idx.assign(url=df_idx['Filename'].apply(lambda x: urljoin(CONFIG.edgar_Archives_url, x)))

    for i, feed_item in df_idx.iterrows():

        py_sec_edgar.extract_and_transform.filings(feed_item)


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
