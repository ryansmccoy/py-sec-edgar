
#######################
# MONTHLY FILINGS FEEDS (XBRL)
# http://www.sec.gov/Archives/edgar/monthly/
# "./xbrlrss-{YEAR}-{MONTH}.xml"

import os
from datetime import datetime
from pprint import pprint
from urllib import parse
from urllib.parse import urljoin

import lxml.html
import pandas as pd
import requests
from bs4 import BeautifulSoup

from py_sec_edgar.proxy_request import ProxyRequest
from py_sec_edgar.utilities import flattenDict, edgar_filing_idx_create_filename, read_xml_feedparser, determine_if_sec_edgar_feed_and_local_files_differ
from .. import CONFIG


def download_edgar_filings_xbrl_rss_files():
    # download first xbrl file availible

    start_date = datetime.strptime("4/1/2005", "%m/%d/%Y")
    end_date = datetime.now()
    dates = [x for x in pd.date_range(start_date, end_date, freq='MS')]
    dates.reverse()
    for date in dates:
        try:
            vpn_agent = ProxyRequest()
            vpn_agent.generate_random_header_and_proxy_host()

            basename = 'xbrlrss-' + \
                       str(date.year) + '-' + str(date.month).zfill(2) + ".xml"
            filepath = os.path.join(CONFIG.SEC_MONTHLY_DIR, basename)
            edgarFilingsFeed = parse.urljoin(
                'https://www.sec.gov/Archives/edgar/monthly/', basename)
            if not os.path.exists(edgarFilingsFeed):
                r = requests.get(CONFIG.edgar_monthly_index, headers=vpn_agent.random_header,
                                 proxies=vpn_agent.random_proxy_host, timeout=(vpn_agent.connect_timeout, vpn_agent.read_timeout))

                # g.GET_FILE(edgarFilingsFeed, filepath)
        except Exception as e:
            print(e)


def generate_monthly_index_url_and_filepaths(day):
    basename = 'xbrlrss-' + str(day.year) + '-' + str(day.month).zfill(2)
    monthly_local_filepath = os.path.join(
        CONFIG.SEC_MONTHLY_DIR, basename + ".xml")
    monthly_url = urljoin(CONFIG.edgar_monthly_index, basename + ".xml")
    return monthly_url, monthly_local_filepath


def download_and_flatten_monthly_xbrl_filings_list():

    vpn_agent = ProxyRequest()
    vpn_agent.generate_random_header_and_proxy_host()

    r = requests.get(CONFIG.edgar_monthly_index, headers=vpn_agent.random_header,
                     proxies=vpn_agent.random_proxy_host, timeout=(vpn_agent.connect_timeout, vpn_agent.read_timeout))

    html = lxml.html.fromstring(r.text)
    html.make_links_absolute(CONFIG.edgar_monthly_index)
    html = lxml.html.tostring(html)
    soup = BeautifulSoup(html, 'lxml')
    urls = []
    [urls.append(link['href']) for link in soup.find_all('a', href=True)]
    urls = [i for i in urls if "xml" in i]
    urls.sort(reverse=True)

    print("Downloading Edgar Monthly XML Files to:\t" + CONFIG.SEC_MONTHLY_DIR)

    df = pd.DataFrame(urls, columns=['URLS'])

    df.to_excel(os.path.join(CONFIG.DATA_DIR,
                             'sec_gov_archives_edgar_monthly_xbrl_urls.xlsx'))

    for url in urls:
        filename = url.split('/')[-1:][0]

        fullfilepath = os.path.join(CONFIG.SEC_MONTHLY_DIR, filename)

        OUTPUT_FILENAME = os.path.join(os.path.dirname(
            fullfilepath), os.path.basename(fullfilepath.replace('.xml', ".xlsx")))

        try:

            if not os.path.isfile(os.path.join(CONFIG.SEC_MONTHLY_DIR, filename)) or url == urls[0]:
                print("Downloading " + fullfilepath)
                vpn_agent.generate_random_header_and_proxy_host()

                r = requests.get(url, headers=vpn_agent.random_header, proxies=vpn_agent.random_proxy_host, timeout=(
                    vpn_agent.connect_timeout, vpn_agent.read_timeout))

                with open(fullfilepath, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=1024):
                        if chunk:  # filter out keep-alive new chunks
                            f.write(chunk)

                # g.GET_FILE(url, fullfilepath)
            else:
                print("Found XML File " + fullfilepath)

            if not os.path.isfile(OUTPUT_FILENAME):
                print("Parsing XML File and Exporting to XLSX")

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
                new_columns_names = [column_name.replace(".", "_").replace(
                    ":", "_").lower() for column_name in df.columns.tolist()]
                df.columns = new_columns_names
                df['SOURCE_FILENAME'] = os.path.basename(fullfilepath)
                df['SOURCE_IMPORT_TIMESTAMP'] = datetime.now()
                df.index = [icount for icount in range(
                    0, len(df.index.tolist()))]
                df.index.name = '_id'
                print("exporting to excel {}".format(OUTPUT_FILENAME))
                df.to_excel(OUTPUT_FILENAME)
                print("")
                print("")
        except:
            print('Something Wrong')


def parse_monthly():

    df_tickercheck = pd.read_excel(CONFIG.tickercheck, index_col=0, header=0)
    df_cik_ticker = pd.read_excel(CONFIG.cik_ticker, header=0)

    prev_val = datetime.now()
    # i, day = list(enumerate(CONFIG.sec_dates_months))[0]
    for i, day in enumerate(CONFIG.sec_dates_months):

        if day.month != prev_val.month:

            monthly_url, monthly_local_filepath = generate_monthly_index_url_and_filepaths(
                day)

            status = determine_if_sec_edgar_feed_and_local_files_differ(
                monthly_url, monthly_local_filepath)

            feed = read_xml_feedparser(monthly_local_filepath)

            print(len(feed.entries))
            for i, feed_item in enumerate(feed.entries):

                if "10-K" in feed_item["edgar_formtype"]:

                    # or ("S-1" in item["edgar_formtype"]) or ("20-F" in item["edgar_formtype"]):

                    item = flattenDict(feed_item)

                    pprint(item)

                    try:
                        ticker = df_tickercheck[df_tickercheck['EDGAR_CIKNUMBER'].isin(
                            [item['edgar_ciknumber'].lstrip("0")])]
                        symbol = ticker['SYMBOL'].tolist()[0]
                    except:
                        try:
                            print('searching backup')
                            ticker = df_cik_ticker[df_cik_ticker['CIK'].isin(
                                [item['edgar_ciknumber'].lstrip("0")])]['Ticker'].tolist()[0]
                        except:
                            ticker = "TICKER"

                    pprint(item)
                    basename = os.path.basename(
                        monthly_local_filepath).replace(".xml", "")

                    month_dir = os.path.join(CONFIG.SEC_TXT_DIR, str(
                        day.year), '{:02d}'.format(day.month))

                    if not os.path.exists(month_dir):
                        os.makedirs(month_dir)
                    if ticker != "TICKER":

                        filepath = edgar_filing_idx_create_filename(
                            basename, item, ticker)

                        if not os.path.exists(filepath):

                            vpn_agent = ProxyRequest()
                            vpn_agent.generate_random_header_and_proxy_host()

                            r = requests.get(CONFIG.edgar_monthly_index, headers=vpn_agent.random_header, proxies=vpn_agent.random_proxy_host, timeout=(
                                vpn_agent.connect_timeout, vpn_agent.read_timeout))

                            # consume_complete_submission_filing.delay(basename, item, ticker)
                        else:
                            print('found file {}'.format(filepath))
                    else:
                        # consume_complete_submission_filing.delay(basename, item, ticker)
                        print('yes')
