import sys
#####################
import os.path

#   edgar_filings_celery_tasks.py
# need to import class if using seperate files
import pandas as pd
import os
from time import sleep
from py_sec_edgar_data.utilities import edgar_filing_idx_create_filename, Gotem
from py_sec_edgar_data.cik_ticker_loader import cik2ticker, get_cik_from_ticker
import py_sec_edgar_data.process_complete_submission_filing
from py_sec_edgar_data.settings import Config
import json
import py_sec_edgar_data.download_listing_of_filings

CONFIG = Config()

from py_sec_edgar_data.celery import app

@app.task(bind=True, max_retries=3)
def celery_consume_rss_feed(self, item):
    item = json.loads(item)
    item = item['ITEM']
    feeds = find_feeds(item['RSS_PAGE'])
    for i,feed in enumerate(feeds):
        item.update({i:feed})
    vals = pd.DataFrame.from_dict(item,orient='index')
    vals.to_csv(os.path.join(CONFIG.DATA_DIR,"{}.csv".format(item['netloc'])))

@app.task(bind=True, max_retries=3)
def celery_extract_content_from_complete_submission_txt_filing(self, item):
    item = json.loads(item)

    if item['OUTPUT_FOLDER'] == "full-index":
        filepath = os.path.join(CONFIG.SEC_GOV_FULL_INDEX_DIR, item['RELATIVE_FILEPATH'])
    elif item['OUTPUT_FOLDER'] == 'filings':
        filepath = os.path.join(CONFIG.SEC_GOV_EDGAR_FILINGS_DIR, item['YEAR'], item['QUARTER'],item['FILE'])
    output_filepath = os.path.join(CONFIG.OUTPUT_DIR,item['CIK'],item['FILE'].replace('-',"").replace(".txt",""))
    print(output_filepath)
    py_sec_edgar_data.process_complete_submission_filing.extract_documents_from_complete_submission_txt_filing(input_filepath=filepath, output_filepath=output_filepath,extract_items=['HEADER_AND_DOCUMENTS'])


@app.task(bind=True, max_retries=3)
def consume_sec_filing_txt(self, item):
    item = json.loads(item)

    if item['OUTPUT_FOLDER'] == "full-index":
        filepath = os.path.join(CONFIG.SEC_GOV_FULL_INDEX_DIR, item['RELATIVE_FILEPATH'])
    elif item['OUTPUT_FOLDER'] == 'filings':
        filepath = os.path.join(CONFIG.SEC_GOV_EDGAR_FILINGS_DIR, item['YEAR'], item['QUARTER'],item['FILE'])

    if not os.path.exists(filepath) or item["OVERWRITE_FILE"] == True:
        try:
            g = Gotem()
            print(' [ X ] Requesting URL')
            g.GET_FILE(item['URL'], filepath)
            print(" [ X ] ", filepath)
        except:
            print(" ... trying again")
            self.retry(countdown=int(random.uniform(1, 2) ** self.request.retries))
            print('waiting 3 seconds')
            sleep(3)
    else:
        print("file already downloaded")
######################################
#  celery_process_sec_filing_with_arelle


@app.task(bind=True, max_retries=3)
def download_recent_edgar_filings_xbrl_rss_feed(self, url, filename):
    try:

        print(' [ X ] Requesting URL')
        print(" [ X ] ", filename)
        # html = requests.get(url)
        py_sec_edgar_data.download_listing_of_filings.download_recent_edgar_filings_xbrl_rss_feed()
        print(" [ X ] Saved 2 Disk")
    except:
        print(" [   ] trying again")
        self.retry(countdown=int(random.uniform(2, 4) ** self.request.retries))


import random

@app.task(bind=True, max_retries=3)
def consume_complete_submission_filing(self, basename, item, ticker):
    main_url = r'https://www.sec.gov'
    if ticker == "TICKER":
        try:
            ticker = cik2ticker(item['ed.gar_ciknumber'])
        except:
            try:
                ticker = item['edgar_xbrlfile.file'].split('-')[0].upper()
                if "JPG" in ticker:
                    ticker = get_cik_from_ticker([item['edgar_ciknumber']])
            except:
                print("searching online")
                ticker = get_cik_from_ticker([item['edgar_ciknumber']])
                print(ticker)

    folder_path = os.path.join(CONFIG.SEC_GOV_EDGAR_FILINGS_DIR, basename.replace("xbrlrss-","").replace("-","/"))
    edgfilename = edgar_filing_idx_create_filename(basename, item, ticker)
    url = item['link'].replace("-index.htm", ".txt")
    filepath = os.path.join(folder_path, edgfilename)

    if not os.path.exists(filepath):
        try:
            g = Gotem()
            print(' [ X ] Requesting URL')
            g.GET_FILE(url, filepath)
            print(" [ X ] ", filepath)
        except:
            print("xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxprob with celery... trying again")
            self.retry(countdown=int(random.uniform(2, 4) ** self.request.retries))
            print('waiting 3 seconds')
            sleep(3)
    else:
        print("file already downloaded")


@app.task(bind=True, max_retries=3)
def consume_complete_submission_filing_txt(self, item, filepath):
    main_url = r'https://www.sec.gov'
    if not os.path.exists(filepath):
        try:
            g = Gotem()
            print(' [ X ] Requesting URL')
            g.GET_FILE_CELERY(item['link'], filepath)
            print(" [ X ] ", filepath)
        except:
            print("... trying again")
            self.retry(countdown=int(random.uniform(2, 4) ** self.request.retries))
    else:
        print("file already downloaded")
