import pandas as pd

desired_width = 600
pd.set_option('display.width', desired_width)
import sqlite3
import os
from py_sec_edgar_data.settings import SSD_DATA_DIR


def query_db_for_filings_data(date_qtr, form_filter=None, cik=None, LATEST_VAR=False):
    try:
        form_filter
    except:
        form_filter = None

    try:
        cik
    except:
        cik = None

    list_all_filings = []
    conn_filing_master = sqlite3.connect(os.path.join(SSD_DATA_DIR, "FILINGS_MASTER.DB"))

    if date_qtr == "LATEST" or LATEST_VAR == True:
        df_frame = pd.read_sql("SELECT * FROM TABLE_MASTER", conn_filing_master)
    else:
        df_frame = pd.read_sql("SELECT * FROM TABLE_{}_{}_MASTER".format(date_qtr[0], date_qtr[1]), conn_filing_master)

    if cik is not None:
        df_frame = df_frame[df_frame['CIK'].isin(cik.iloc[:, 0].tolist())]

    if form_filter is not None:
        df_frame = df_frame[df_frame['FORM_TYPE'].isin(form_filter)]

        # all_filings.append(filings)
        # df_all = pd.concat(all_filings)

    df_all = df_frame.drop_duplicates(subset=['FILENAME'])

    return df_all

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
