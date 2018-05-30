import json
import os
import sqlite3
from urllib.parse import urljoin

import pandas as pd

import py_sec_edgar_data.celery_consumer_filings
from py_sec_edgar_data.settings import SEC_GOV_FULL_INDEX_DIR, SEC_EDGAR_ARCHIVES_URL

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
    # i, file = list(enumerate(full_index_files))[0]

    for i, file in enumerate(full_index_files):
        item = {}
        item['OUTPUT_FOLDER'] = 'full-index'
        item['RELATIVE_FILEPATH'] = '{}'.format(file)
        item['OUTPUT_MAIN_FILEPATH'] = SEC_GOV_FULL_INDEX_DIR
        item['URL'] = urljoin(SEC_EDGAR_ARCHIVES_URL, 'edgar/full-index/{}'.format(file))
        item['OVERWRITE_FILE'] = True
        dir_name = os.path.dirname(os.path.join(SEC_GOV_FULL_INDEX_DIR,item['RELATIVE_FILEPATH']))

        if not os.path.exists(dir_name):
            os.makedirs(dir_name)

        py_sec_edgar_data.celery_consumer_filings.consume_sec_filing_txt.delay(json.dumps(item))

def load_idx_files_from_sqldb(start_year=None, end_year=None):
    conn = sqlite3.connect(filing_master)
    filepath = os.path.join(DATA_DIR, 'FILINGS_MASTER.db')
    years = [year for year in range(2012, 2018)]
    years.sort(reverse=True)
    master_files = walk_dir_fullfilename(SEC_GOV_FULL_INDEX_DIR, contains="master.idx")
    master_files.sort(reverse=True)
    files = [file for file in master_files if "old" not in file]
    # years = [year for year in range(1994, 2018)]
    frame = pd.DataFrame()
    year = years[0]
    for year in years:
        # years_files = [filepath for filepath in master_files if str(year) in filepath]
        # years_files = [file for file in years_files if "old" not in file]

        for year_file in years_files:
            print(year_file)
            table_name = year_file.split("full-index\\")[1].replace("\\", "_").upper().split(".")[0]
            df_frame = pd.read_sql("SELECT * FROM TABLE_{}".format(table_name), conn)
            frame = frame.append(df_frame)

    frame = frame.drop_duplicates(subset=['FILENAME'])
    frame = frame[frame['FORM_TYPE']=="10-K"]
    frame["BASENAME"] = frame["FILENAME"].apply(lambda x: os.path.basename(x).split(".")[0])
    df_matches = frame[frame["BASENAME"].isin(files_master_basename)]
    df_matches_not = frame[~frame["BASENAME"].isin(files_master_basename)]
    df_matched = pd.merge(frame, df_files_master, how='left')
    return frame
