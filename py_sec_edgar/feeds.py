import os
from datetime import datetime, timedelta
from urllib import parse
from urllib.parse import urljoin

import logging
logger = logging.getLogger(__name__)

import lxml.html
import pandas as pd

import pyarrow as pa
import pyarrow.parquet as pq

import requests
from bs4 import BeautifulSoup

from py_sec_edgar import CONFIG
from py_sec_edgar.proxy import ProxyRequest
from py_sec_edgar.utilities import determine_if_sec_edgar_feed_and_local_files_differ, walk_dir_fullpath, generate_folder_names_years_quarters, read_xml_feedparser, flattenDict

def load_filings_feed(ticker_list_filter=True, form_list_filter=True):

    df_cik_tickers = pd.read_csv(CONFIG.TICKER_CIK)

    logging.info('\n\n\n\tLoaded IDX files\n\n\n')

    df_merged_idx_filings = pq.read_table(CONFIG.MERGED_IDX_FILE).to_pandas().sort_values("Date Filed", ascending=False)
    # df_merged_idx_filings = pd.read_csv(CONFIG.MERGED_IDX_FILE, index_col=0,  dtype={"CIK": int}, encoding='latin-1')

    if ticker_list_filter:
        ticker_list = pd.read_csv(CONFIG.TICKER_LIST, header=None).iloc[:, 0].tolist()
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

#######################
# DAILY FILINGS FEEDS
# https://www.sec.gov/Archives/edgar/daily-index/
# https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&CIK=&type=&company=&dateb=&owner=include&start=0&count=400&output=atom
# https://www.sec.gov/cgi-bin/browse-edgar?company=&CIK=&type=8-K&type=8-K&owner=exclude&count=400&action=getcurrent

def generate_daily_index_urls_and_filepaths(day):
    edgar_url = r'https://www.sec.gov/Archives/edgar/'
    daily_files_templates = ["master", "form", "company", "crawler", "sitemap"]
    date_formated = datetime.strftime(day, "%Y%m%d")
    daily_files = []
    for template in daily_files_templates:
        download_url = urljoin(edgar_url, "daily-index/{}/QTR{}/{}.{}.idx".format(
            day.year, day.quarter, template, date_formated))
        local_filepath = os.path.join(CONFIG.SEC_DAILY_INDEX_DIR, "{}".format(
            day.year), "QTR{}".format(day.quarter), "{}.{}.idx".format(template, date_formated))
        daily_files.append((download_url, local_filepath))
    daily_files[-1] = (daily_files[-1][0].replace("idx", "xml"),
                       daily_files[-1][1].replace("idx", "xml"))
    return daily_files

def update_daily_files():
    sec_dates = pd.date_range(
        datetime.today() - timedelta(days=365 * 22), datetime.today())
    sec_dates_weekdays = sec_dates[sec_dates.weekday < 5]
    sec_dates_weekdays = sec_dates_weekdays.sort_values(ascending=False)

    for i, day in enumerate(sec_dates_weekdays):
        daily_files = generate_daily_index_urls_and_filepaths(day)
        # url, local = daily_files[0]
        for daily_url, daily_local_filepath in daily_files:

            if consecutive_days_same < 5 and os.path.exists(daily_local_filepath):
                status = determine_if_sec_edgar_feed_and_local_files_differ(
                    daily_url, daily_local_filepath)
                consecutive_days_same = 0
            elif consecutive_days_same > 5 and os.path.exists(daily_local_filepath):
                pass
            else:
                g = ProxyRequest()
                g.GET_FILE(daily_url, daily_local_filepath)


def merge_idx_files():

    files = walk_dir_fullpath(CONFIG.FULL_INDEX_DIR, contains='.csv')

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

#######################
# FULL-INDEX FILINGS FEEDS (TXT)
# https://www.sec.gov/Archives/edgar/full-index/
# "./{YEAR}/QTR{NUMBER}/"

def update_full_index_feed(save_idx_as_csv=True, skip_if_exists=True):

    dates_quarters = generate_folder_names_years_quarters(CONFIG.index_start_date, CONFIG.index_end_date)

    latest_full_index_master = os.path.join(CONFIG.FULL_INDEX_DIR, "master.idx")

    if os.path.exists(latest_full_index_master):
        os.remove(latest_full_index_master)

    g = ProxyRequest()

    g.GET_FILE(CONFIG.edgar_full_master_url, latest_full_index_master)

    convert_idx_to_csv(latest_full_index_master)

    for year, qtr in dates_quarters:

        # CONFIG.index_files = ['master.idx']
        for i, file in enumerate(CONFIG.index_files):

            filepath = os.path.join(CONFIG.FULL_INDEX_DIR, year, qtr, file)

            if not os.path.exists(filepath) or skip_if_exists == False:

                if not os.path.exists(os.path.dirname(filepath)):
                    os.makedirs(os.path.dirname(filepath))

                url = urljoin(CONFIG.edgar_Archives_url,'edgar/full-index/{}/{}/{}'.format(year, qtr, file))

                g.GET_FILE(url, filepath)

            if save_idx_as_csv == True and skip_if_exists == False:

                logging.info('\n\n\tConverting idx to csv\n\n')
                convert_idx_to_csv(filepath)

    logging.info('\n\n\n\tMerging IDX files\n\n\n\t')
    merge_idx_files()
    logging.info('\n\n\n\tCompleted Index Download\n\n\n\t')


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
            logging.info(e)


#######################
# MONTHLY FILINGS FEEDS (XBRL)
# http://www.sec.gov/Archives/edgar/monthly/
# "./xbrlrss-{YEAR}-{MONTH}.xml"


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

    logging.info("\n\n\n\nDownloading Edgar Monthly XML Files to:\t" + CONFIG.SEC_MONTHLY_DIR)

    df = pd.DataFrame(urls, columns=['URLS'])

    df.to_excel(os.path.join(CONFIG.DATA_DIR,'sec_gov_archives_edgar_monthly_xbrl_urls.xlsx'))

    for url in urls:
        filename = url.split('/')[-1:][0]

        fullfilepath = os.path.join(CONFIG.SEC_MONTHLY_DIR, filename)

        OUTPUT_FILENAME = os.path.join(os.path.dirname(
            fullfilepath), os.path.basename(fullfilepath.replace('.xml', ".xlsx")))

        try:

            if not os.path.isfile(os.path.join(CONFIG.SEC_MONTHLY_DIR, filename)) or url == urls[0]:
                logging.info("\n\n\n\nDownloading " + fullfilepath)
                vpn_agent.generate_random_header_and_proxy_host()

                r = requests.get(url, headers=vpn_agent.random_header, proxies=vpn_agent.random_proxy_host, timeout=(
                    vpn_agent.connect_timeout, vpn_agent.read_timeout))

                with open(fullfilepath, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=1024):
                        if chunk:  # filter out keep-alive new chunks
                            f.write(chunk)

                # g.GET_FILE(url, fullfilepath)
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
                logging.info("\n\n\n\nexporting to excel {}".format(OUTPUT_FILENAME))
                df.to_excel(OUTPUT_FILENAME)
                logging.info("\n\n\n\n")
                logging.info("\n\n\n\n")
        except:
            logging.info('Something Wrong')


def parse_monthly():

    df_tickercheck = pd.read_excel(CONFIG.tickercheck, index_col=0, header=0)
    df_cik_ticker = pd.read_excel(CONFIG.cik_ticker, header=0)

    prev_val = datetime.now()
    # i, day = list(enumerate(CONFIG.sec_dates_months))[0]
    for i, day in enumerate(CONFIG.sec_dates_months):

        if day.month != prev_val.month:

            monthly_url, monthly_local_filepath = generate_monthly_index_url_and_filepaths(
                day)

            status = determine_if_sec_edgar_feed_and_local_files_differ(monthly_url, monthly_local_filepath)

            feed = read_xml_feedparser(monthly_local_filepath)

            logging.info(len(feed.entries))
            for i, feed_item in enumerate(feed.entries):

                if "10-K" in feed_item["edgar_formtype"]:

                    # or ("S-1" in item["edgar_formtype"]) or ("20-F" in item["edgar_formtype"]):

                    item = flattenDict(feed_item)

                    logging.info(item)

                    try:
                        ticker = df_tickercheck[df_tickercheck['EDGAR_CIKNUMBER'].isin(
                            [item['edgar_ciknumber'].lstrip("0")])]
                        symbol = ticker['SYMBOL'].tolist()[0]
                    except:
                        try:
                            logging.info('searching backup')
                            ticker = df_cik_ticker[df_cik_ticker['CIK'].isin(
                                [item['edgar_ciknumber'].lstrip("0")])]['Ticker'].tolist()[0]
                        except:
                            ticker = "TICKER"

                    logging.info(item)
                    basename = os.path.basename(
                        monthly_local_filepath).replace(".xml", "")

                    month_dir = os.path.join(CONFIG.SEC_TXT_DIR, str(
                        day.year), '{:02d}'.format(day.month))

                    if not os.path.exists(month_dir):
                        os.makedirs(month_dir)
                    if ticker != "TICKER":

                        filepath = edgar_filing_idx_create_filename(basename, item, ticker)

                        if not os.path.exists(filepath):

                            vpn_agent = ProxyRequest()
                            vpn_agent.generate_random_header_and_proxy_host()

                            r = requests.get(CONFIG.edgar_monthly_index, headers=vpn_agent.random_header, proxies=vpn_agent.random_proxy_host, timeout=(
                                vpn_agent.connect_timeout, vpn_agent.read_timeout))

                            # consume_complete_submission_filing.delay(basename, item, ticker)
                        else:
                            logging.info('found file {}'.format(filepath))
                    else:
                        # consume_complete_submission_filing.delay(basename, item, ticker)
                        logging.info('yes')

