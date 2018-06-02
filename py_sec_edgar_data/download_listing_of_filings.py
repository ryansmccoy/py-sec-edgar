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

import os
import glob
from urllib.parse import urljoin
from py_sec_edgar_data.utilities import walk_dir_fullpath, Gotem
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

import py_sec_edgar_data.celery_consumer_filings
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

edgar_Archives_url = r'https://www.sec.gov/Archives/'
edgar_monthly_url = r"https://www.sec.gov/Archives/edgar/monthly/"
edgar_daily_index = urljoin(edgar_Archives_url,'edgar/daily-index/')
edgar_monthly_url = r"https://www.sec.gov/Archives/edgar/monthly/"
edgar_full_index = urljoin(edgar_Archives_url,'edgar/full-index/')
edgar_monthly_index = urljoin(edgar_Archives_url, 'edgar/monthly/')

edgar_full_master = urljoin(edgar_full_index,'master.idx')

def load_headers_files():
    headers_combined = r'E:\DATA\headers.xlsx'
    df_headers_combined = pd.read_excel(headers_combined, header=0, index_col=0, parse_dates=True)

def edgar_filings_feed(year, month):
    basename = 'xbrlrss-' + str(year) + '-' + str(month).zfill(2)
    print(basename)
    localfilename = os.path.join(X, basename + ".xml")
    if os.path.exists(localfilename):
        edgarFilingsFeed = localfilename
        print("found local xbrl file")
    else:
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
    files_master = walk_dir_fullpath(CONFIG.SEC_GOV_TXT_DIR,contains='.txt')
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
            filepath = os.path.join(CONFIG.SEC_GOV_MONTHLY_DIR, basename)
            edgarFilingsFeed = parse.urljoin('https://www.sec.gov/Archives/edgar/monthly/', basename)
            g.GET_FILE(edgarFilingsFeed, filepath)
        except Exception as e:
            print(e)

####################### MONTHLY

def generate_monthly_index_url_and_filepaths(day):
    basename = 'xbrlrss-' + str(day.year) + '-' + str(day.month).zfill(2)
    monthly_local_filepath = os.path.join(CONFIG.SEC_GOV_MONTHLY_DIR, basename + ".xml")
    monthly_url = urljoin('https://www.sec.gov/Archives/edgar/monthly/', basename + ".xml")
    return monthly_url, monthly_local_filepath

def get_sec_monthly_listings():
    g = Gotem()
    g.GET_HTML(edgar_monthly_url)
    html = lxml.html.fromstring(g.r.text)
    html.make_links_absolute(edgar_monthly_url)
    html = lxml.html.tostring(html)
    soup = BeautifulSoup(html, 'lxml')
    urls = []
    [urls.append(link['href']) for link in soup.find_all('a', href=True)]
    urls = [i for i in urls if "xml" in i]
    urls.sort(reverse=True)
    print("Downloading Edgar Monthly XML Files to :" + CONFIG.SEC_GOV_MONTHLY_DIR)
    df = pd.DataFrame(urls, columns=['URLS'])
    df.to_excel(os.path.join(CONFIG.DATA_DIR, 'sec_gov_archives_edgar_monthly_xbrl_urls.xlsx'))
    for url in urls:
        filename = url.split('/')[-1:][0]
        if not os.path.isfile(os.path.join(CONFIG.SEC_GOV_MONTHLY_DIR, filename)) or url == urls[0]:
            fullfilepath = os.path.join(CONFIG.SEC_GOV_MONTHLY_DIR, filename)
            print("Downloading " + fullfilepath)
            g.GET_FILE(url, fullfilepath)


####################### DAILY

def generate_daily_index_urls_and_filepaths(day):
    edgar_url = r'https://www.sec.gov/Archives/edgar/'
    daily_files_templates = ["master", "form", "company", "crawler", "sitemap"]
    date_formated = datetime.strftime(day, "%Y%m%d")
    daily_files = []
    for template in daily_files_templates:
        download_url = urljoin(edgar_url, "daily-index/{}/QTR{}/{}.{}.idx".format(day.year, day.quarter, template, date_formated))
        local_filepath = os.path.join(CONFIG.SEC_GOV_DAILY_INDEX_DIR, "{}".format(day.year), "QTR{}".format(day.quarter), "{}.{}.idx".format(template, date_formated))
        daily_files.append((download_url, local_filepath))
    daily_files[-1] = (daily_files[-1][0].replace("idx", "xml"), daily_files[-1][1].replace("idx", "xml"))
    return daily_files


def update_daily_files():
    sec_dates = pd.date_range(datetime.now() - timedelta(days=365 * 22), datetime.now())
    sec_dates_weekdays = sec_dates[sec_dates.weekday < 5]
    sec_dates_weekdays = sec_dates_weekdays.sort_values(ascending=False)
    sec_dates_months = sec_dates_weekdays[sec_dates_weekdays.day == sec_dates_weekdays[0].day]
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


# https://www.sec.gov/Archives/edgar/daily-index/2017/QTR3/
#/Archives/edgar/daily-index — daily index files through the current year;

def main():
    pypath = r'C:\Users\ryan\PycharmProjects\sec_data\sec_data\edgar_filings_celery_tasks_download.py'
    pythonfile = r'C:\Users\ryan\AppData\Local\conda\conda\envs\edgarfilings\python.exe'
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
