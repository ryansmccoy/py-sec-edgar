# -*- coding: utf-8 -*-

import os, sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import py_sec_edgar.feeds as py_sec_edgar_feeds
import py_sec_edgar.broker as py_sec_edgar_etl

def main(ticker_list_filter=True, form_list_filter=True, extract_filing_contents=False):

    py_sec_edgar_feeds.update_full_index_feed(skip_if_exists=True)

    df_filings = py_sec_edgar_feeds.load_filings_feed(ticker_list_filter=ticker_list_filter, form_list_filter=form_list_filter)

    for i, filing in df_filings.iterrows():

        py_sec_edgar_etl.broker(filing, extract_filing_contents=extract_filing_contents)

if __name__ == "__main__":

    main()
    sys.exit()
