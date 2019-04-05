
"""Console script for py_sec_edgar."""

import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import py_sec_edgar.feeds as py_sec_edgar_feeds
import py_sec_edgar.etl as py_sec_edgar_etl

def main():

    py_sec_edgar_feeds.update_full_index_feed()

    df_filings = py_sec_edgar_feeds.load_filings_feed(ticker_list_filter=False, form_list_filter=True)

    for i, feed_item in df_filings.iterrows():

        py_sec_edgar_etl.broker(feed_item, extract_filing_contents=False)

if __name__ == "__main__":

    main()

    sys.exit()
