# -*- coding: utf-8 -*-
from pprint import pprint
import os, sys
import click

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

    for i, filing_json in df_filings_idx.iterrows():

        pprint(filing_json)

        sec_filing = SecEdgar(filing_json)
        sec_filing.download()
        sec_filing.load()
        sec_filing.parse_header(save_output=save_output)
        sec_filing.process_filing(save_output=save_output)

if __name__ == "__main__":

    main()
