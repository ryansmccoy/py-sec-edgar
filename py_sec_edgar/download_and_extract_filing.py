
from py_sec_edgar import CONFIG
from py_sec_edgar.proxy_request import ProxyRequest
import py_sec_edgar.filing

from pprint import pprint
import os

# from sqlalchemy import create_engine

# idx_engine = create_engine('sqlite:///merged_idx_files.db')
# df_idx.to_sql('idx', idx_engine, if_exists='append')
# df = pd.read_sql_query('SELECT * FROM idx LIMIT 3',idx_engine)

def filings(feed_item):

    pprint(feed_item)

    g = ProxyRequest()

    feed_item = dict(feed_item)

    folder_dir = os.path.basename(feed_item['Filename']).split('.')[0].replace("-","")

    folder_path_cik = CONFIG.TXT_FILING_DIR.replace("CIK", str(feed_item['CIK'])).replace("FOLDER", folder_dir)

    filepath_feed_item = os.path.join(folder_path_cik, os.path.basename(feed_item['Filename']))

    if not os.path.exists(filepath_feed_item):

        if not os.path.exists(folder_path_cik):
            os.makedirs(folder_path_cik)

        g.GET_FILE(feed_item['url'], filepath_feed_item)

        # todo: celery version of download full
        # consume_complete_submission_filing_txt.delay(feed_item, filepath_cik)

    else:
        print("Filepath Already exists\n\t {}".format(filepath_feed_item))
        # parse_and_download_quarterly_idx_file(CONFIG.edgar_full_master, local_master_idx)

    filing_contents = filepath_feed_item.replace(".txt", "_FILING_CONTENTS.csv").replace("-","")

    if not os.path.exists(filing_contents):

        py_sec_edgar.filing.complete_submission_filing(input_filepath=filepath_feed_item, output_directory=folder_path_cik, extraction_override=True)

        # todo: celery version of download full
        # consume_complete_submission_filing_txt.delay(feed_item, filepath_cik)

    else:
        print("\n\tFilepath Already exists\n\t {}".format(filepath_feed_item))
        # parse_and_download_quarterly_idx_file(CONFIG.edgar_full_master, local_master_idx)

