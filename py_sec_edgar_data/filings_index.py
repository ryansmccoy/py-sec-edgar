# view-source:https://www.sec.gov/Archives/edgar/xbrl-rr.rss.xml
# https://www.sec.gov/Archives/edgar/usgaap.rss.xml
# https://www.sec.gov/Archives/edgar/xbrl-inline.rss.xml
# https://www.sec.gov/Archives/edgar/usgaap.rss.xml
# http://www.sec.gov/Archives/edgar/xbrlrss.all.xml
# https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&CIK=&type=10-K&company=&dateb=&owner=include&start=0&count=100&output=atom

import sys
import glob
import os
import feedparser
from dateparser import parse
from py_sec_edgar_data.utilities import flattenDict, Gotem, edgar_filing_idx_create_filename, file_size
from urllib.parse import urljoin
import pandas as pd
desired_width = 600
pd.set_option('display.width', desired_width)

import pandas as pd
from urllib import parse

import lxml.html
from pprint import pprint
from bs4 import BeautifulSoup

from datetime import datetime, date
from datetime import timedelta
import sqlite3
import pandas as pd
from urllib import parse

from urllib import parse
import datetime
import os
import glob

import subprocess

import json
import os
import sqlite3
from urllib.parse import urljoin
from py_sec_edgar_data.utilities import walk_dir_fullpath, Gotem

from py_sec_edgar_data.settings import Config

CONFIG = Config()

full_index_files = ["company.gz",
                    "company.idx",
                    "company.Z",
                    "company.zip",
                    "crawler.idx",
                    "form.gz",
                    "form.idx",
                    "form.Z",
                    "form.zip",
                    "master.gz",
                    "master.idx",
                    "master.Z",
                    "master.zip",
                    "sitemap.quarterlyindex1.xml",
                    "xbrl.gz",
                    "xbrl.idx",
                    "xbrl.Z",
                    "xbrl.zip"]

def read_xml_feedparser(source_file):
    if source_file[0:4] == 'http':
        feed = feedparser.parse(source_file)
    elif source_file.endswith(".xml"):
        with open(source_file) as f:
            feedData = f.read()
        feed = feedparser.parse(feedData)
    else:
        feed = feedparser.parse(source_file)
    return feed

def edgar_monthly_xbrl_filings_feed(year, month):
    basename = 'xbrlrss-' + str(year) + '-' + str(month).zfill(2)
    print(basename)
    edgarFilingsFeed = os.path.join(CONFIG.SEC_MONTHLY_DIR, basename + ".xml")
    if not os.path.exists(edgarFilingsFeed):
        print("Did not find local xbrl file...Downloading")
        edgarFilingsFeed = parse.urljoin('http://www.sec.gov/Archives/edgar/monthly/', basename + ".xml")
        g.GET_FILE(edgarFilingsFeed, localfilename)
    return basename, localfilename

def determine_if_sec_edgar_feed_and_local_files_differ(url, local_filepath):

    temp_filepath = os.path.join(os.path.dirname(local_filepath), "temp_{}".format(os.path.basename(local_filepath)))
    g = Gotem()
    g.GET_FILE(url, temp_filepath)
    temp_size = file_size(temp_filepath)
    local_size = file_size(local_filepath)

    if local_size == temp_size:
        print("local_size {} == temp_size {}".format(local_size, temp_size))
        os.remove(temp_filepath)
        return False
    else:
        print("local_size {} != temp_size {}".format(local_size, temp_size))
        if os.path.exists(local_filepath):
            os.remove(local_filepath)
        os.rename(temp_filepath, temp_filepath.replace("temp_", ""))
        return True

def generate_list_of_local_filings():
    files_master = walk_dir_fullpath(CONFIG.SEC_TXT_DIR,contains='.txt')
    files_master = [filepath for filepath in files_master if "edgar" not in os.path.basename(filepath)]
    files_master_basename = [os.path.basename(filepath).split(".")[0] for filepath in files_master if "edgar" not in os.path.basename(filepath)]
    files_master.sort(reverse=True)

####################### FULL-INDEX

def download_recent_edgar_filings_xbrl_rss_feed():
    for _ in range(1,2):
        print(_)
        try:
            g = Gotem()
            basename = 'xbrlrss-' + str(datetime.now().year) + '-' + str(datetime.now().month - _).zfill(2) + ".xml"
            filepath = os.path.join(CONFIG.SEC_MONTHLY_DIR, basename)
            edgarFilingsFeed = parse.urljoin('https://www.sec.gov/Archives/edgar/monthly/', basename)
            g.GET_FILE(edgarFilingsFeed, filepath)
        except Exception as e:
            print(e)

####################### MONTHLY

def download_monthly_xbrl_filings_list():
    g = Gotem()
    g.GET_HTML(CONFIG.edgar_monthly_index)
    html = lxml.html.fromstring(g.r.text)
    html.make_links_absolute(CONFIG.edgar_monthly_index)
    html = lxml.html.tostring(html)
    soup = BeautifulSoup(html, 'lxml')
    urls = []
    [urls.append(link['href']) for link in soup.find_all('a', href=True)]
    urls = [i for i in urls if "xml" in i]
    urls.sort(reverse=True)

    print("Downloading Edgar Monthly XML Files to:\t" + CONFIG.SEC_MONTHLY_DIR)

    df = pd.DataFrame(urls, columns=['URLS'])

    df.to_excel(os.path.join(CONFIG.DATA_DIR, 'sec_gov_archives_edgar_monthly_xbrl_urls.xlsx'))

    for url in urls:
        filename = url.split('/')[-1:][0]
        fullfilepath = os.path.join(CONFIG.SEC_MONTHLY_DIR, filename)
        OUTPUT_FILENAME = os.path.join(os.path.dirname(fullfilepath), os.path.basename(fullfilepath.replace('.xml', ".xlsx")))

        if not os.path.isfile(os.path.join(CONFIG.SEC_MONTHLY_DIR, filename)) or url == urls[0]:
            print("Downloading " + fullfilepath)
            g.GET_FILE(url, fullfilepath)
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
                df_.index = [ind.replace(".","_").replace(":","_").upper() for ind in df_.index.tolist()]
                df_ = df_.T

                match = df_['EDGAR_XBRLFILE_FILE'].str.replace("-.+","").str.upper().tolist()[0]

                if "." in match or len(match) > 13:
                    df_['TICKER'] = "--"
                else:
                    df_['TICKER'] = match

                list_.append(df_)

            df = pd.concat(list_)
            new_columns_names = [column_name.replace(".","_").replace(":","_").lower() for column_name in df.columns.tolist()]
            df.columns = new_columns_names
            df['SOURCE_FILENAME'] = os.path.basename(fullfilepath)
            df['SOURCE_IMPORT_TIMESTAMP'] = datetime.now()
            df.index = [icount for icount in range(0, len(df.index.tolist()))]
            df.index.name = '_id'
            print("exporting to excel {}".format(OUTPUT_FILENAME))
            df.to_excel(OUTPUT_FILENAME)

def generate_monthly_index_url_and_filepaths(day):
    basename = 'xbrlrss-' + str(day.year) + '-' + str(day.month).zfill(2)
    monthly_local_filepath = os.path.join(CONFIG.SEC_MONTHLY_DIR, basename + ".xml")
    monthly_url = urljoin(CONFIG.edgar_monthly_index, basename + ".xml")
    return monthly_url, monthly_local_filepath

def parse_monthly():

    df_tickercheck = pd.read_excel(CONFIG.tickercheck, index_col=0, header=0)
    df_cik_ticker = pd.read_excel(CONFIG.cik_ticker, header=0)

    prev_val = datetime.now()
    # i, day = list(enumerate(CONFIG.sec_dates_months))[0]
    for i, day in enumerate(CONFIG.sec_dates_months):

        if day.month != prev_val.month:

            monthly_url, monthly_local_filepath= generate_monthly_index_url_and_filepaths(day)

            status = determine_if_sec_edgar_feed_and_local_files_differ(monthly_url, monthly_local_filepath)

            feed = read_xml_feedparser(monthly_local_filepath)

            print(len(feed.entries))
            # i, feed_item = list(enumerate(feed.entries))[2]
            for i, feed_item in list(enumerate(feed.entries)):
                if ("10-K" in feed_item["edgar_formtype"]):
                    # or ("S-1" in item["edgar_formtype"]) or ("20-F" in item["edgar_formtype"]):
                    item = flattenDict(feed_item)

                    try:
                        ticker = df_tickercheck[df_tickercheck['CIK'].isin([item['edgar_ciknumber'].lstrip("0")])]['SYMBOL'].tolist()[0]
                    except:
                        try:
                            print('searching backup')
                            ticker = df_cik_ticker[df_cik_ticker['CIK'].isin([item['edgar_ciknumber'].lstrip("0")])]['Ticker'].tolist()[0]
                        except:
                            ticker = "TICKER"
                    pprint(item)
                    basename = os.path.basename(monthly_local_filepath).replace(".xml", "")
                    month_dir = os.path.join(CONFIG.SEC_TXT_DIR, str(day.year), '{:02d}'.format(day.month))

                    if not os.path.exists(month_dir):
                        os.makedirs(month_dir)
                    if ticker != "TICKER":
                        filepath = edgar_filing_idx_create_filename(basename, item,ticker)
                        if not os.path.exists(filepath):
                            consume_complete_submission_filing.delay(basename, item, ticker)
                        else:
                            print('found file {}'.format(filepath))
                    else:
                        consume_complete_submission_filing.delay(basename, item, ticker)
            # if day.quarter != prev_val.quarter:
        #
        # if day.year != prev_val.year:
        #     pass

####################### DAILY

def generate_daily_index_urls_and_filepaths(day):
    edgar_url = r'https://www.sec.gov/Archives/edgar/'
    daily_files_templates = ["master", "form", "company", "crawler", "sitemap"]
    date_formated = datetime.strftime(day, "%Y%m%d")
    daily_files = []
    for template in daily_files_templates:
        download_url = urljoin(edgar_url, "daily-index/{}/QTR{}/{}.{}.idx".format(day.year, day.quarter, template, date_formated))
        local_filepath = os.path.join(CONFIG.SEC_DAILY_INDEX_DIR, "{}".format(day.year), "QTR{}".format(day.quarter), "{}.{}.idx".format(template, date_formated))
        daily_files.append((download_url, local_filepath))
    daily_files[-1] = (daily_files[-1][0].replace("idx", "xml"), daily_files[-1][1].replace("idx", "xml"))
    return daily_files


def update_daily_files():

    for i, day in enumerate(sec_dates_weekdays):
        daily_files = generate_daily_index_urls_and_filepaths(day)
        # url, local = daily_files[0]
        for daily_url, daily_local_filepath in daily_files:
            if consecutive_days_same < 5 and os.path.exists(daily_local_filepath):
                status = determine_if_sec_edgar_feed_and_local_files_differ(daily_url, daily_local_filepath)
                consecutive_days_same = 0
            elif consecutive_days_same > 5 and os.path.exists(daily_local_filepath):
                pass
            else:
                g = Gotem()
                g.GET_FILE(daily_url,daily_local_filepath)

def parse_master_idx():

    local_master_idx = os.path.join(CONFIG.SEC_FULL_INDEX_DIR, "master.idx")
    old_local_master_idx = '{}.old'.format(local_master_idx)

    if os.path.exists(local_master_idx):
        os.rename(local_master_idx, old_local_master_idx)
    else:
        with open(old_local_master_idx, 'w') as f:
            f.write(str())

    g = Gotem()
    g.GET_FILE(CONFIG.edgar_full_master, local_master_idx)
    g.GET_HTML(CONFIG.edgar_full_master, local_master_idx)
    df = pd.read_csv(local_master_idx, skiprows=10, names=['CIK', 'Company Name', 'Form Type', 'Date Filed', 'Filename'], sep='|', engine='python', parse_dates=True)
    df = df[-df['CIK'].str.contains("---")]
    df = df.sort_values('Date Filed', ascending=False)
    df['published'] = df['Date Filed'].apply(lambda x: datetime.combine(parse(x), parse("12:00:00").time()))
    df['link'] = df['Filename'].apply(lambda x: urljoin(CONFIG.edgar_Archives_url, x))
    df['edgar_ciknumber'] = df['CIK'].astype(str)
    df['edgar_companyname'] = df['Company Name']
    df['edgar_formtype'] = df['Form Type']
    df_master_with_tickers = pd.merge(df, df_tickers_cik, how='left', left_on=df.CIK, right_on=df_tickers_cik.EDGAR_CIKNUMBER)
    df_master_with_tickers = df_master_with_tickers.sort_values('Date Filed', ascending=False)
    df_master_with_tickers_10k = df_master_with_tickers[df_master_with_tickers['Form Type'].isin(['10-K'])]

    feed_items = df_master_with_tickers_10k.to_dict(orient='index')
    # item = list(feed_items.items())[0]
    for item in feed_items.items():

        feed_item = item[1]
        folder_path_cik = os.path.join(CONFIG.SEC_TXT_DIR ,'{}/QTR{}'.format(feed_item['published'].year, feed_item['published'].quarter))
        folder_path_cik_other = os.path.join(CONFIG.SEC_TXT_DIR, 'cik', feed_item['edgar_ciknumber'])

        if not os.path.exists(folder_path_cik):
            os.makedirs(folder_path_cik)

        filepath_cik = os.path.join(folder_path_cik, os.path.basename(feed_item['Filename']))

        if not os.path.exists(filepath_cik) and not os.path.exists(folder_path_cik_other):
            consume_complete_submission_filing_txt.delay(feed_item, filepath_cik)
        else:
            print("Filepath Already exists {}".format(filepath_cik))
            parse_and_download_quarterly_idx_file(CONFIG.edgar_full_master, local_master_idx)

# https://www.sec.gov/Archives/edgar/daily-index/2017/QTR3/
#/Archives/edgar/daily-index — daily index files through the current year;

def main():
    from_year = 2016
    to_year = 2017
    XBRLLocation = "local"
    UpdateXBRLurls = False

    if XBRLLocation == "local":
        print("Globbing XBRL files in folder: " + CONFIG.XBRLfolder)
        xbrlfiles = glob.glob(os.path.join(CONFIG.SEC_XBRL_DIR,"*"))
        xbrlfiles.sort(reverse=True)

    if UpdateXBRLurls == True:
        # source_file = r'https://www.sec.gov/xbrlrss-2017-03.xml'
        secfiles_urls = r'C:\Users\ryan\PycharmProjects\sec_data\sec_data\data\secfiles_urls.xlsx'
        df = pd.read_excel(secfles_urls)
        mode = "red"
        df = df[df['URLS'].str.contains('201')]
        urls = list(df['URLS'])

    for year in range(from_year, to_year + 1):
        for month in range(1, 12 + 1):
            try:
                subprocess.Popen([pythonfile, pypath, '--date', str(month), str(year)])
            except:
                print("problem getting sec filings urls from feed {} {}".format(str(month), str(year)))

if __name__ == "__main__":
    g = Gotem()
    g.GET_URLS(edgar_monthly_url)
