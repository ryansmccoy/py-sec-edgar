
#######################
# FULL-INDEX FILINGS FEEDS (TXT)
# https://www.sec.gov/Archives/edgar/full-index/
# "./{YEAR}/QTR{NUMBER}/"

import os
import os.path
from urllib.parse import urljoin

import pandas as pd

from py_sec_edgar.proxy_request import ProxyRequest
from py_sec_edgar.utilities import generate_folder_names_years_quarters, walk_dir_fullpath
from .. import CONFIG

pd.set_option('display.float_format', lambda x: '%.5f' % x)  # pandas
pd.set_option('display.max_columns', 100)
pd.set_option('display.max_rows', 100)
pd.set_option('display.width', 600)

# import pyarrow as pa
# import pyarrow.parquet as pq
# import fastparquet as fp


def convert_idx_to_csv(filepath):
    df = pd.read_csv(filepath, skiprows=10, names=[
        'CIK', 'Company Name', 'Form Type', 'Date Filed', 'Filename'], sep='|', engine='python', parse_dates=True)

    df = df[-df['CIK'].str.contains("---")]

    df = df.sort_values('Date Filed', ascending=False)

    df = df.assign(published=pd.to_datetime(df['Date Filed']))

    df.reset_index()

    df.to_csv(filepath.replace(".idx", ".csv"), index=False)


def merge_idx_files():
    files = walk_dir_fullpath(CONFIG.FULL_INDEX_DIR, contains='.csv')

    files.sort(reverse=True)

    dfs = []

    for filepath in files:
        # print(filepath)
        df_ = pd.read_csv(filepath)
        dfs.append(df_)

    df_idx = pd.concat(dfs)

    out_path = os.path.join(CONFIG.REF_DIR, 'merged_idx_files.csv')

    df_idx.to_csv(out_path)

    # arrow_table = pa.Table.from_pandas(df_idx)
    # pq.write_table(arrow_table, out_path, compression='GZIP')

    # df_idx = fp.ParquetFile(out_path).to_pandas()


def download(save_idx_as_csv=True, skip_if_exists=True):
    dates_quarters = generate_folder_names_years_quarters(
        CONFIG.index_start_date, CONFIG.index_end_date)

    latest_full_index_master = os.path.join(
        CONFIG.FULL_INDEX_DIR, "master.idx")

    if os.path.exists(latest_full_index_master):
        os.remove(latest_full_index_master)

    g = ProxyRequest()

    print("Downloading Latest {}".format(CONFIG.edgar_full_master_url))

    g.GET_FILE(CONFIG.edgar_full_master_url, latest_full_index_master)

    convert_idx_to_csv(latest_full_index_master)

    for year, qtr in dates_quarters:

        # CONFIG.index_files = ['master.idx']
        for i, file in enumerate(CONFIG.index_files):

            filepath = os.path.join(CONFIG.FULL_INDEX_DIR, year, qtr, file)

            if not os.path.exists(filepath) or skip_if_exists == False:

                if not os.path.exists(os.path.dirname(filepath)):
                    os.makedirs(os.path.dirname(filepath))

                url = urljoin(CONFIG.edgar_Archives_url,
                              'edgar/full-index/{}/{}/{}'.format(year, qtr, file))

                g.GET_FILE(url, filepath)

            if save_idx_as_csv == True and skip_if_exists == False:

                print('\tConverting idx to csv')
                convert_idx_to_csv(filepath)

    print('Merging IDX files')
    merge_idx_files()


if __name__ == "__main__":
    download()
