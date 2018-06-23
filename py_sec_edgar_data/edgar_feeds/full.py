import os
from datetime import datetime
from urllib.parse import urljoin

import pandas as pd
from dateparser import parse

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


def parse_master_idx():

    local_master_idx = os.path.join(CONFIG.SEC_FULL_INDEX_DIR, "master.idx")
    old_local_master_idx = '{}.old'.format(local_master_idx)

    if os.path.exists(local_master_idx):
        os.rename(local_master_idx, old_local_master_idx)
    else:
        with open(old_local_master_idx, 'w') as f:
            f.write(str())

    g = Gotem()
    g.GET_FILE(CONFIG.edgar_full_master, local_master_idx)
    g.GET_HTML(CONFIG.edgar_full_master, local_master_idx)

    g = Gotem()
    g.GET_HTML(CONFIG.edgar_monthly_index)

    df = pd.read_csv(local_master_idx, skiprows=10, names=['CIK', 'Company Name', 'Form Type', 'Date Filed', 'Filename'], sep='|', engine='python', parse_dates=True)
    df = df[-df['CIK'].str.contains("---")]
    df = df.sort_values('Date Filed', ascending=False)
    df['published'] = df['Date Filed'].apply(lambda x: datetime.combine(parse(x), parse("12:00:00").time()))
    df['link'] = df['Filename'].apply(lambda x: urljoin(CONFIG.edgar_Archives_url, x))
    df['edgar_ciknumber'] = df['CIK'].astype(str)
    df['edgar_companyname'] = df['Company Name']
    df['edgar_formtype'] = df['Form Type']
    df_master_with_tickers = pd.merge(df, df_tickers_cik, how='left', left_on=df.CIK, right_on=df_tickers_cik.EDGAR_CIKNUMBER)
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
