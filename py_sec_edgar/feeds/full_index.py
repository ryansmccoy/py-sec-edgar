import logging
import os
from urllib.parse import urljoin

from py_sec_edgar.feeds.idx import convert_idx_to_csv, merge_idx_files
from py_sec_edgar.settings import CONFIG
from py_sec_edgar.utilities import generate_folder_names_years_quarters, RetryRequest

#######################
# FULL-INDEX FILINGS FEEDS (TXT)
# https://www.sec.gov/Archives/edgar/full-index/
# "./{YEAR}/QTR{NUMBER}/"


def update_full_index_feed(save_idx_as_csv=True, skip_if_exists=False):

    dates_quarters = generate_folder_names_years_quarters(CONFIG.index_start_date, CONFIG.index_end_date)

    latest_full_index_master = os.path.join(CONFIG.FULL_INDEX_DATA_DIR, "master.idx")

    if os.path.exists(latest_full_index_master):
        os.remove(latest_full_index_master)

    g = RetryRequest()

    g.get(CONFIG.edgar_full_master_url, latest_full_index_master)

    convert_idx_to_csv(latest_full_index_master)

    for year, qtr in dates_quarters:

        # CONFIG.index_files = ['master.idx']
        for i, file in enumerate(CONFIG.index_files):

            filepath = os.path.join(CONFIG.FULL_INDEX_DATA_DIR, year, qtr, file)
            csv_filepath = filepath.replace('.idx', '.csv')

            if os.path.exists(filepath) and skip_if_exists == False:

                os.remove(filepath)

            if os.path.exists(csv_filepath) and skip_if_exists == False:

                os.remove(csv_filepath)

            if not os.path.exists(filepath):

                if not os.path.exists(os.path.dirname(filepath)):
                    os.makedirs(os.path.dirname(filepath))

                url = urljoin(CONFIG.edgar_Archives_url, f'edgar/full-index/{year}/{qtr}/{file}')

                g.get(url, filepath)

                if save_idx_as_csv == True:

                    logging.info('\n\n\tConverting idx to csv\n\n')
                    convert_idx_to_csv(filepath)

    logging.info('\n\n\tMerging IDX files\n\n')
    merge_idx_files()
    logging.info('\n\n\tCompleted Index Download\n\n\t')
