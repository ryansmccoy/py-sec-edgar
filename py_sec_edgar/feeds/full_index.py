
#######################
# FULL-INDEX FILINGS FEEDS (TXT)
# https://www.sec.gov/Archives/edgar/full-index/
# "./{YEAR}/QTR{NUMBER}/"

import os
import os.path
from urllib.parse import urljoin
from datetime import datetime

import pandas as pd
pd.set_option('display.float_format', lambda x: '%.5f' % x)  # pandas
pd.set_option('display.max_columns', 100)
pd.set_option('display.max_rows', 100)
pd.set_option('display.width', 600)

try:
    from py_sec_edgar.utilities import format_filename
    from py_sec_edgar.proxy_request import ProxyRequest
    from py_sec_edgar.settings import Config
except:
    from proxy_request import ProxyRequest
    from settings import Config
    from utilities import format_filename

CONFIG = Config()

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

index_files = ['master.idx']

def generate_folder_names_years_quarters(start_date, end_date):

    dates_data = []
    date_range = pd.date_range(datetime.strptime(start_date, "%m/%d/%Y"), datetime.strptime(end_date, "%m/%d/%Y"), freq="Q")

    for i, values in enumerate(date_range):
        quarter = '{}'.format(values.year), "QTR{}".format(int(values.month/3))
        dates_data.append(quarter)

    dates_quarters = list(set(dates_data))
    dates_quarters.sort(reverse=True)

    return dates_quarters

def scan_all_local_filings(main_dir=None, year=None):
    files = walk_dir_fullpath(os.path.join(main_dir,"{}".format(year)))
    return files

def download_latest_full_index_files():
    g = ProxyRequest()

    local_idx = os.path.join(CONFIG.FULL_INDEX_DIR, "master.idx")

    if os.path.exists(local_idx):
        os.remove(local_idx)

    g.GET_FILE(CONFIG.edgar_full_master_url, local_idx)

    dates_quarters = generate_folder_names_years_quarters(CONFIG.index_start_date, CONFIG.index_end_date)

    print("Downloading Latest {}".format(CONFIG.edgar_full_master_url))

    for qtr in dates_quarters:

        for i, file in enumerate(index_files):

            url = urljoin(CONFIG.edgar_Archives_url, 'edgar/full-index/{}/{}/{}'.format(qtr[0], qtr[1], file))

            filepath = os.path.join(CONFIG.FULL_INDEX_DIR, '{}/{}/{}'.format(qtr[0], qtr[1], file))

            if not os.path.exists(os.path.dirname(filepath)):
                os.makedirs(os.path.dirname(filepath))

            g.GET_FILE(url, filepath)

            print('saved {}'.format(filepath))

def download_index_file(url, filepath):

    g = ProxyRequest()

    g.GET_FILE(url, filepath)

    df = pd.read_csv(filepath, skiprows=10, names=['CIK', 'Company Name', 'Form Type', 'Date Filed', 'Filename'], sep='|', engine='python', parse_dates=True)

    df = df[-df['CIK'].str.contains("---")]

    df = df.sort_values('Date Filed', ascending=False)

    df = df.assign(published=pd.to_datetime(df['Date Filed']))

    df.reset_index()

    df.to_csv(filepath.replace(".idx", ".csv"), index=False)


def download_filings_from_idx():

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

if __name__ == "__main__":
    download_filings_from_idx()
