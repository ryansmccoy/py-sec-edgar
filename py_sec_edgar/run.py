# -*- coding: utf-8 -*-

import os, sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import py_sec_edgar.feeds as py_sec_edgar_feeds
import py_sec_edgar.broker as py_sec_edgar_etl

def main(ticker_list_filter=True, form_list_filter=True, extract_filing_contents=False):

    py_sec_edgar_feeds.update_full_index_feed(skip_if_exists=True)

    df_filings = py_sec_edgar_feeds.load_filings_feed(ticker_list_filter=True, form_list_filter=True)

    for i, filing in df_filings.iterrows():

        py_sec_edgar_etl.broker(filing, extract_filing_contents=False)

if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(description='Tool to download and extract contents from SEC Filings')
    parser.add_argument('-t', '--ticker_list_filter',help='Filter Filings based on refdata/tickers.csv', dest='ticker_list_filter', default=True, action='store_true')
    parser.add_argument('-f','--form_list_filter', help='Download only Forms specifed in settings.py', dest='form_list_filter',  default=True, action='store_true')
    parser.add_argument('-c','--extract_filing_contents', help='Extract the contents of the complete submission filing', dest='extract_filing_contents', default=False, action='store_true')

    if len(sys.argv[1:]) >= 1:
        args = parser.parse_args()
        main(ticker_list_filter=args.ticker_list_filter, form_list_filter=args.form_list_filter, extract_filing_contents=args.extract_filing_contents)
    else:
        sys.exit(parser.print_help())
