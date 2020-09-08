# -*- coding: utf-8 -*-
"""Console script for td_trader

This script is the primary execution point for running the Daily and Intra-Day Execution Algo

Why does this file exist, and why __main__? For more info, read:

- https://www.python.org/dev/peps/pep-0338/
- https://docs.python.org/2/using/cmdline.html#cmdoption-m
- https://docs.python.org/3/using/cmdline.html#cmdoption-m
"""

import os
import sys
from pprint import pprint

import click

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import py_sec_edgar.feeds as py_sec_edgar_feeds
from py_sec_edgar.broker import BrokerManager
from py_sec_edgar.settings import CONFIG

@click.command()
@click.option('--ticker_list_filter', default=True)
@click.option('--form_list_filter', default=True)
@click.option('--save_output', default=False)
def main(ticker_list_filter, form_list_filter, save_output):

    py_sec_edgar_feeds.update_full_index_feed(skip_if_exists=True)

    # ticker_list_filer is set in refdata/tickers.csv
    # form_list_filter is specified in the settings file
    df_filings_idx = py_sec_edgar_feeds.load_filings_feed(ticker_list_filter=ticker_list_filter, form_list_filter=form_list_filter)

    filing_broker = BrokerManager(CONFIG)

    for i, sec_filing in df_filings_idx.iterrows():

        pprint(str(sec_filing))

        filing_broker.process_filing(sec_filing)

if __name__ == "__main__":

    main()
