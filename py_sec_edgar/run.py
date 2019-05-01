# -*- coding: utf-8 -*-
import os
import sys
from pprint import pprint

import click
import pandas as pd

pd.set_option('display.float_format', lambda x: '%.5f' % x)  # pandas
pd.set_option('display.max_columns', 100)
pd.set_option('display.max_rows', 100)
pd.set_option('display.width', 600)

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import py_sec_edgar.feeds as py_sec_edgar_feeds
from py_sec_edgar.filing import SecEdgar

@click.command()
@click.option('--ticker_list_filter', default=True)
@click.option('--form_list_filter', default=True)
@click.option('--save_output', default=False)
def main(ticker_list_filter, form_list_filter, save_output):

    py_sec_edgar_feeds.update_full_index_feed(skip_if_exists=True)

    df_filings_idx = py_sec_edgar_feeds.load_filings_feed(ticker_list_filter=ticker_list_filter, form_list_filter=form_list_filter)

    for i, filing in df_filings_idx.iterrows():

        pprint(filing)

        sec_filing = SecEdgar(filing)
        sec_filing.download()
        sec_filing.load()
        sec_filing.parse_header(save_output=save_output)
        sec_filing.process_filing(save_output=save_output)

if __name__ == "__main__":

    main()
