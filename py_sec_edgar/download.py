
from py_sec_edgar import CONFIG
from py_sec_edgar.proxy_request import ProxyRequest

from pprint import pprint
import os
from urllib.parse import urljoin

import pandas as pd

pd.set_option('display.float_format', lambda x: '%.5f' % x)  # pandas
pd.set_option('display.max_columns', 100)
pd.set_option('display.max_rows', 100)
pd.set_option('display.width', 600)

# import fastparquet as fp

def download_filings():

    merged_idx_files = os.path.join(CONFIG.REF_DIR, 'merged_idx_files.csv')

    # df_idx = fp.ParquetFile(merged_idx_files.replace(".csv",".parq")).to_pandas()

    df_idx = pd.read_csv(merged_idx_files, index_col=0, dtype={"CIK": int})
    # df_idx = df_idx.set_index('CIK')

    # load ticker lookup and lookup CIK
    df_tickers = pd.read_csv(CONFIG.tickers_filepath, header=None)
    list_of_tickers = df_tickers.iloc[:,0].tolist()

    # load CIK to tickers
    df_cik_tickers = pd.read_excel(CONFIG.tickercheck)

    df_cik_tickers = df_cik_tickers[df_cik_tickers['SYMBOL'].isin(list_of_tickers)]

    list_of_ciks = df_cik_tickers['CIK'].tolist()

    df_filtered_idx = df_idx[df_idx['CIK'].isin(list_of_ciks)]

    df_filtered_idx = df_filtered_idx[df_filtered_idx['Form Type'].isin(CONFIG.forms_list)]

    df_filtered_idx = df_filtered_idx.assign(url=df_filtered_idx['Filename'].apply(lambda x: urljoin(CONFIG.edgar_Archives_url, x)))

    g = ProxyRequest()

    # i, feed_item = list(df_with_tickers.to_dict(orient='index').items())[23]
    for i, feed_item in df_filtered_idx.to_dict(orient='index').items():

        folder_dir = os.path.basename(feed_item['Filename']).split('.')[0].replace("-","")
        folder_path_cik = CONFIG.TXT_FILING_DIR.replace("CIK", str(feed_item['CIK'])).replace("FOLDER", folder_dir)

        filepath_feed_item = os.path.join(folder_path_cik, os.path.basename(feed_item['Filename']))

        if not os.path.exists(filepath_feed_item):

            if not os.path.exists(folder_path_cik):
                os.makedirs(folder_path_cik)

            pprint(feed_item)

            g.GET_FILE(feed_item['url'], filepath_feed_item)

            # todo: celery version of download full
            # consume_complete_submission_filing_txt.delay(feed_item, filepath_cik)
        else:
            print("Filepath Already exists\n\t {}".format(filepath_feed_item))
            # parse_and_download_quarterly_idx_file(CONFIG.edgar_full_master, local_master_idx)
