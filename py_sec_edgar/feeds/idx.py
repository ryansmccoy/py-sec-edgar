import logging
import os
from urllib.parse import urljoin

import pandas as pd
import pyarrow as pa
from pyarrow import parquet as pq

from py_sec_edgar.settings import CONFIG
from py_sec_edgar.utilities import walk_dir_fullpath


def merge_idx_files():

    files = walk_dir_fullpath(CONFIG.FULL_INDEX_DATA_DIR, contains='.csv')

    files.sort(reverse=True)

    dfs = []

    for filepath in files:
        df_ = pd.read_csv(filepath)
        dfs.append(df_)

    df_idx = pd.concat(dfs)

    pa_filings = pa.Table.from_pandas(df_idx)

    # out_path = os.path.join(CONFIG.REF_DIR, 'merged_idx_files.csv')
    # df_idx.to_csv(out_path)

    pq_filepath = os.path.join(CONFIG.REF_DIR, 'merged_idx_files.pq')

    if os.path.exists(pq_filepath):
        os.remove(pq_filepath)

    pq.write_table(pa_filings, pq_filepath, compression='snappy')

    # arrow_table = pa.Table.from_pandas(df_idx)
    # pq.write_table(arrow_table, out_path, compression='GZIP')

    # df_idx = fp.ParquetFile(out_path).to_pandas()


def convert_idx_to_csv(filepath):
    # filepath = latest_full_index_master
    df = pd.read_csv(filepath, skiprows=10, names=['CIK', 'Company Name', 'Form Type', 'Date Filed', 'Filename'], sep='|', engine='python', parse_dates=True)

    df = df[-df['CIK'].str.contains("---")]

    df = df.sort_values('Date Filed', ascending=False)

    df = df.assign(published=pd.to_datetime(df['Date Filed']))

    df.reset_index()

    df.to_csv(filepath.replace(".idx", ".csv"), index=False)


def load_local_idx_filing_list(ticker_list_filter=True, form_list_filter=True):

    df_cik_tickers = pd.read_csv(CONFIG.TICKER_CIK_FILEPATH)

    logging.info('\n\n\n\tLoaded IDX files\n\n\n')

    df_merged_idx_filings = pq.read_table(CONFIG.MERGED_IDX_FILEPATH).to_pandas().sort_values("Date Filed", ascending=False)
    # df_merged_idx_filings = pd.read_csv(CONFIG.MERGED_IDX_FILEPATH, index_col=0,  dtype={"CIK": int}, encoding='latin-1')

    if ticker_list_filter:
        ticker_list = pd.read_csv(CONFIG.TICKER_LIST_FILEPATH, header=None).iloc[:, 0].tolist()
        df_cik_tickers = df_cik_tickers[df_cik_tickers['SYMBOL'].isin(ticker_list)]

    if form_list_filter:
        logging.info('\n\n\n\tLoading Forms Filter\n\n\n')
        df_merged_idx_filings = df_merged_idx_filings[df_merged_idx_filings['Form Type'].isin(CONFIG.forms_list)]

    df_cik_tickers = df_cik_tickers.dropna(subset=['CIK'])

    df_cik_tickers['CIK'] = df_cik_tickers['CIK'].astype(int)

    cik_list = df_cik_tickers['CIK'].tolist()

    if ticker_list_filter:
        df_merged_idx_filings = df_merged_idx_filings[df_merged_idx_filings['CIK'].isin(cik_list)]

    df_filings = df_merged_idx_filings.assign(url=df_merged_idx_filings['Filename'].apply(lambda x: urljoin(CONFIG.edgar_Archives_url, x)))

    return df_filings
