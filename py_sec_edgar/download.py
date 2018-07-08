
from . import CONFIG

from py_sec_edgar.proxy_request import ProxyRequest

import os
from urllib.parse import urljoin

import pandas as pd

pd.set_option('display.float_format', lambda x: '%.5f' % x)  # pandas
pd.set_option('display.max_columns', 100)
pd.set_option('display.max_rows', 100)
pd.set_option('display.width', 600)

def download_filings():

    local_idx = os.path.join(CONFIG.FULL_INDEX_DIR, "master.idx")

    df_idx = pd.read_csv(local_idx.replace(".idx", ".csv"))
    df_idx = df_idx.assign(url=df_idx['Filename'].apply(lambda x: urljoin(CONFIG.edgar_Archives_url, x)))
    df_idx = df_idx.assign(CIK=df_idx['CIK'].astype(str))
    df_idx = df_idx.set_index('CIK')

    # load ticker lookup
    df_tickers = pd.read_excel(CONFIG.tickercheck)
    df_tickers =  df_tickers.assign(CIK= df_tickers['CIK'].astype(str))
    df_tickers = df_tickers.set_index('CIK')

    df = pd.merge(df_idx, df_tickers, how='left', left_index=True, right_index=True)
    df = df.reset_index()
    df = df.sort_values('Date Filed', ascending=False)

    # todo: allow for ability to filter forms dynamically
    g = ProxyRequest()

    df = df[df['Form Type'].isin(CONFIG.forms_list)]

    df = df.assign(published=pd.to_datetime(df['published']))

    # i, feed_item = list(df_with_tickers.to_dict(orient='index').items())[23]
    for i, feed_item in df.to_dict(orient='index').items():

        folder_dir = os.path.basename(feed_item['Filename']).split('.')[0].replace("-","")
        folder_path_cik = CONFIG.TXT_FILING_DIR.replace("CIK", str(feed_item['CIK'])).replace("FOLDER", folder_dir)

        filepath_feed_item = os.path.join(folder_path_cik, os.path.basename(feed_item['Filename']))

        if not os.path.exists(filepath_feed_item):

            if not os.path.exists(folder_path_cik):
                os.makedirs(folder_path_cik)

            g.GET_FILE(feed_item['link'], filepath_feed_item)

            # todo: celery version of download full
            # consume_complete_submission_filing_txt.delay(feed_item, filepath_cik)
        else:
            print("Filepath Already exists\n\t {}".format(filepath_feed_item))
            # parse_and_download_quarterly_idx_file(CONFIG.edgar_full_master, local_master_idx)
