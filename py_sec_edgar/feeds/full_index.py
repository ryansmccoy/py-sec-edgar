
#######################
# FULL-INDEX FILINGS FEEDS (TXT)
# https://www.sec.gov/Archives/edgar/full-index/
# "./{YEAR}/QTR{NUMBER}/"

from .. import CONFIG

from py_sec_edgar.utilities import generate_folder_names_years_quarters
from py_sec_edgar.proxy_request import ProxyRequest

import os
import os.path
from urllib.parse import urljoin

import pandas as pd

pd.set_option('display.float_format', lambda x: '%.5f' % x)  # pandas
pd.set_option('display.max_columns', 100)
pd.set_option('display.max_rows', 100)
pd.set_option('display.width', 600)

def convert_idx_to_csv(filepath):

    df = pd.read_csv(filepath, skiprows=10, names=['CIK', 'Company Name', 'Form Type', 'Date Filed', 'Filename'], sep='|', engine='python', parse_dates=True)

    df = df[-df['CIK'].str.contains("---")]

    df = df.sort_values('Date Filed', ascending=False)

    df = df.assign(published=pd.to_datetime(df['Date Filed']))

    df.reset_index()

    df.to_csv(filepath.replace(".idx", ".csv"), index=False)

def download(save_idx_as_csv=True, skip_if_exists=True):

    dates_quarters = generate_folder_names_years_quarters(CONFIG.index_start_date, CONFIG.index_end_date)


    latest_full_index_master = os.path.join(CONFIG.FULL_INDEX_DIR, "master.idx")

    if os.path.exists(latest_full_index_master):
        os.remove(latest_full_index_master)

    g = ProxyRequest()

    g.GET_FILE(CONFIG.edgar_full_master_url, latest_full_index_master)

    print("Downloading Latest {}".format(CONFIG.edgar_full_master_url))

    for year, qtr in dates_quarters:

        # CONFIG.index_files = ['master.idx']
        for i, file in enumerate(CONFIG.index_files):

            filepath = os.path.join(CONFIG.FULL_INDEX_DIR, year, qtr, file)

            if not os.path.exists(filepath) or skip_if_exists == False:

                if not os.path.exists(os.path.dirname(filepath)):
                    os.makedirs(os.path.dirname(filepath))

                url = urljoin(CONFIG.edgar_Archives_url, 'edgar/full-index/{}/{}/{}'.format(year, qtr, file))

                g.GET_FILE(url, filepath)

                if save_idx_as_csv == True:

                    print('Converting idx to csv')
                    convert_idx_to_csv(filepath)

if __name__ == "__main__":
    download()
