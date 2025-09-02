import logging
import os
from datetime import datetime
from urllib.parse import urljoin

import lxml.html
import pandas as pd
import requests
from bs4 import BeautifulSoup

from ..settings import settings
from ..utilities import flattenDict, read_xml_feedparser

#######################
# MONTHLY FILINGS FEEDS (XBRL)
# http://www.sec.gov/Archives/edgar/monthly/
# "./xbrlrss-{YEAR}-{MONTH}.xml"

def generate_monthly_index_url_and_filepaths(day):
    basename = 'xbrlrss-' + str(day.year) + '-' + str(day.month).zfill(2)
    monthly_local_filepath = os.path.join(
        str(settings.monthly_data_dir), basename + ".xml")
    monthly_url = urljoin(settings.edgar_monthly_index_url, basename + ".xml")
    return monthly_url, monthly_local_filepath

def download_and_flatten_monthly_xbrl_filings_list():
    import time
    http_headers = {'User-Agent': settings.user_agent}

    # Rate limiting: respect SEC's 10 requests per second limit
    time.sleep(settings.request_delay)

    r = requests.get(settings.edgar_monthly_index_url, headers=http_headers)

    html = lxml.html.fromstring(r.text)
    html.make_links_absolute(settings.edgar_monthly_index_url)
    html = lxml.html.tostring(html)
    soup = BeautifulSoup(html, 'lxml')
    urls = []
    [urls.append(link['href']) for link in soup.find_all('a', href=True)]
    urls = [i for i in urls if "xml" in i]
    urls.sort(reverse=True)

    logging.info("\n\n\n\nDownloading Edgar Monthly XML Files to:\t" + str(settings.monthly_data_dir))

    df = pd.DataFrame(urls, columns=['URLS'])

    df.to_excel(os.path.join(str(settings.data_dir),'sec_gov_archives_edgar_monthly_xbrl_urls.xlsx'))

    for url in urls:
        filename = url.split('/')[-1:][0]

        fullfilepath = os.path.join(str(settings.monthly_data_dir), filename)

        OUTPUT_FILENAME = os.path.join(os.path.dirname(
            fullfilepath), os.path.basename(fullfilepath.replace('.xml', ".xlsx")))

        try:

            if not os.path.isfile(os.path.join(str(settings.monthly_data_dir), filename)) or url == urls[0]:
                logging.info("\n\n\n\nDownloading " + fullfilepath)

                # Rate limiting: respect SEC's 10 requests per second limit
                time.sleep(settings.request_delay)

                r = requests.get(url, headers=http_headers)

                with open(fullfilepath, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=1024):
                        if chunk:  # filter out keep-alive new chunks
                            f.write(chunk)

                # g.get(url, fullfilepath)
            else:
                logging.info("\n\n\n\nFound XML File " + fullfilepath)

            if not os.path.isfile(OUTPUT_FILENAME):
                logging.info("\n\n\n\nParsing XML File and Exporting to XLSX")

                feeds = read_xml_feedparser(fullfilepath)

                list_ = []

                # item = feeds.entries[0]
                for item in feeds.entries:

                    feed_dict = flattenDict(item)
                    df_ = pd.DataFrame.from_dict(feed_dict, orient='index')
                    df_.columns = ['VALUES']
                    df_.index = [ind.replace(".", "_").replace(
                        ":", "_").upper() for ind in df_.index.tolist()]
                    df_ = df_.T

                    match = df_['EDGAR_XBRLFILE_FILE'].str.replace(
                        "-.+", "").str.upper().tolist()[0]

                    if "." in match or len(match) > 13:
                        df_['TICKER'] = "--"
                    else:
                        df_['TICKER'] = match

                    list_.append(df_)

                df = pd.concat(list_)
                new_columns_names = [column_name.replace(".", "_").replace(":", "_").lower() for column_name in df.columns.tolist()]
                df.columns = new_columns_names
                df['SOURCE_FILENAME'] = os.path.basename(fullfilepath)
                df['SOURCE_IMPORT_TIMESTAMP'] = datetime.now()
                df.index = [icount for icount in range(
                    0, len(df.index.tolist()))]
                df.index.name = '_id'
                logging.info(f"\n\n\n\nexporting to excel {OUTPUT_FILENAME}")
                df.to_excel(OUTPUT_FILENAME)
                logging.info("\n\n\n\n")
                logging.info("\n\n\n\n")
        except:
            logging.info('Something Wrong')




# def parse_monthly():
#
#     df_tickercheck = pd.read_excel(CONFIG.tickercheck, index_col=0, header=0)
#     df_cik_ticker = pd.read_excel(CONFIG.cik_ticker, header=0)
#
#     prev_val = datetime.now()
#     # i, day = list(enumerate(CONFIG.sec_dates_months))[0]
#     for i, day in enumerate(CONFIG.sec_dates_months):
#
#         if day.month != prev_val.month:
#
#             monthly_url, monthly_local_filepath = generate_monthly_index_url_and_filepaths(
#                 day)
#
#             status = edgar_and_local_differ(monthly_url, monthly_local_filepath)
#
#             feed = read_xml_feedparser(monthly_local_filepath)
#
#             logging.info(len(feed.entries))
#             for i, filing_json in enumerate(feed.entries):
#
#                 if "10-K" in filing_json["edgar_formtype"]:
#
#                     # or ("S-1" in item["edgar_formtype"]) or ("20-F" in item["edgar_formtype"]):
#
#                     item = flattenDict(filing_json)
#
#                     logging.info(item)
#
#                     try:
#                         ticker = df_tickercheck[df_tickercheck['EDGAR_CIKNUMBER'].isin(
#                             [item['edgar_ciknumber'].lstrip("0")])]
#                         symbol = ticker['SYMBOL'].tolist()[0]
#                     except:
#                         try:
#                             logging.info('searching backup')
#                             ticker = df_cik_ticker[df_cik_ticker['CIK'].isin(
#                                 [item['edgar_ciknumber'].lstrip("0")])]['Ticker'].tolist()[0]
#                         except:
#                             ticker = "TICKER"
#
#                     logging.info(item)
#                     basename = os.path.basename(
#                         monthly_local_filepath).replace(".xml", "")
#
#                     month_dir = os.path.join(CONFIG.SEC_TXT_DIR, str(
#                         day.year), '{:02d}'.format(day.month))
#
#                     if not os.path.exists(month_dir):
#                         os.makedirs(month_dir)
#                     if ticker != "TICKER":
#
#                         filepath = edgar_filing_idx_create_filename(basename, item, ticker)
#
#                         if not os.path.exists(filepath):
#
#                             r = requests.get(CONFIG.edgar_monthly_index)
#
#                             # consume_complete_submission_filing.delay(basename, item, ticker)
#                         else:
#                             logging.info('found file {}'.format(filepath))
#                     else:
#                         # consume_complete_submission_filing.delay(basename, item, ticker)
#                         logging.info('yes')
