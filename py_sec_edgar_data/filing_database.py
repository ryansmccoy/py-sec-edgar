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
