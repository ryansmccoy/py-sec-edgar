import json
import os
import os.path
from datetime import datetime
from urllib.parse import urljoin

import pandas as pd
from dateparser import parse

from py_sec_edgar_data.celery_producer_filings import CONFIG
from py_sec_edgar_data.edgar_feeds.edgar_feeds import CONFIG
from py_sec_edgar_data.gotem import Gotem

full_index_files = ["company.gz",
                    "company.idx",
                    "company.Z",
                    "company.zip",
                    "crawler.idx",
                    "form.gz",
                    "form.idx",
                    "form.Z",
                    "form.zip",
                    "master.gz",
                    "master.idx",
                    "master.Z",
                    "master.zip",
                    "sitemap.quarterlyindex1.xml",
                    "xbrl.gz",
                    "xbrl.idx",
                    "xbrl.Z",
                    "xbrl.zip"]

def download_latest_quarterly_full_index_files():

    for i, file in enumerate(full_index_files):

        item = {}
        item['OUTPUT_FOLDER'] = 'full-index'
        item['RELATIVE_FILEPATH'] = '{}'.format(file)
        item['OUTPUT_MAIN_FILEPATH'] = CONFIG.SEC_FULL_INDEX_DIR
        item['URL'] = urljoin(CONFIG.edgar_Archives_url, 'edgar/full-index/{}'.format(file))
        item['OVERWRITE_FILE'] = True
        dir_name = os.path.dirname(os.path.join(CONFIG.SEC_FULL_INDEX_DIR, item['RELATIVE_FILEPATH']))

        if not os.path.exists(dir_name):
            os.makedirs(dir_name)

        # py_sec_edgar_data.celery_consumer_filings.consume_sec_filing_txt.delay(json.dumps(item))
        g.GET_FILE(item['URL'], os.path.join(item['OUTPUT_MAIN_FILEPATH'], item['RELATIVE_FILEPATH']))


def parse_and_download_latest_master():

    local_master_idx = os.path.join(CONFIG.SEC_FULL_INDEX_DIR, "master.idx")

    if os.path.exists(local_master_idx):
        os.remove(local_master_idx)

    g = Gotem()
    g.GET_FILE(CONFIG.edgar_full_master, local_master_idx)

    df = pd.read_csv(local_master_idx, skiprows=10, names=['CIK', 'Company Name', 'Form Type', 'Date Filed', 'Filename'], sep='|', engine='python', parse_dates=True)
    df = df[-df['CIK'].str.contains("---")]
    df = df.sort_values('Date Filed', ascending=False)
    df = df.assign(published=pd.to_datetime(df['Date Filed']))
    # df['published'] = df['Date Filed'].apply(lambda x: datetime.combine(parse(x), parse("12:00:00").time()))
    df['link'] = df['Filename'].apply(lambda x: urljoin(CONFIG.edgar_Archives_url, x))
    df['edgar_ciknumber'] = df['CIK'].astype(str)
    df['edgar_companyname'] = df['Company Name']
    df['edgar_formtype'] = df['Form Type']
    df_tickers_cik = pd.read_excel(CONFIG.tickercheck)
    df_tickers_cik = df_tickers_cik.assign(EDGAR_CIKNUMBER=df_tickers_cik['EDGAR_CIKNUMBER'].astype(str))
    df_master_with_tickers = pd.merge(df, df_tickers_cik, how='left', left_on=df.edgar_ciknumber, right_on=df_tickers_cik.EDGAR_CIKNUMBER)
    df_master_with_tickers = df_master_with_tickers.sort_values('Date Filed', ascending=False)
    df_master_with_tickers_10k = df_master_with_tickers[df_master_with_tickers['Form Type'].isin(['10-K'])]
    feed_items = df_master_with_tickers_10k.to_dict(orient='index')

    # item = list(feed_items.items())[0]

    for item in feed_items.items():
        feed_item = item[1]
        folder_path_cik = os.path.join(CONFIG.SEC_TXT_DIR ,'{}/QTR{}'.format(feed_item['published'].year, feed_item['published'].quarter))
        folder_path_cik_other = os.path.join(CONFIG.SEC_TXT_DIR, 'cik', feed_item['edgar_ciknumber'])

        if not os.path.exists(folder_path_cik):
            os.makedirs(folder_path_cik)

        filepath_cik = os.path.join(folder_path_cik, os.path.basename(feed_item['Filename']))

        if not os.path.exists(filepath_cik) and not os.path.exists(folder_path_cik_other):
            consume_complete_submission_filing_txt.delay(feed_item, filepath_cik)
        else:
            print("Filepath Already exists {}".format(filepath_cik))
            parse_and_download_quarterly_idx_file(CONFIG.edgar_full_master, local_master_idx)

