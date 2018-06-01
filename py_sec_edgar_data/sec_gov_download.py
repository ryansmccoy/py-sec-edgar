# view-source:https://www.sec.gov/Archives/edgar/xbrl-rr.rss.xml
# https://www.sec.gov/Archives/edgar/usgaap.rss.xml
# https://www.sec.gov/Archives/edgar/xbrl-inline.rss.xml
# https://www.sec.gov/Archives/edgar/usgaap.rss.xml
# http://www.sec.gov/Archives/edgar/xbrlrss.all.xml
# https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&CIK=&type=10-K&company=&dateb=&owner=include&start=0&count=100&output=atom

import sys
from py_sec_edgar_data.settings import SEC_GOV_MONTHLY_DIR

import glob
import os
import feedparser
from datetime import datetime
from dateparser import parse
from py_sec_edgar_data.utilities import flattenDict, Gotem, edgar_filing_idx_create_filename, file_size
from urllib.parse import urljoin
import pandas as pd
desired_width = 600
pd.set_option('display.width', desired_width)

import os
import glob
from datetime import datetime
from urllib.parse import urljoin
from py_sec_edgar_data.settings import SEC_GOV_TXT_DIR, CONFIG_DIR, SEC_GOV_FULL_INDEX_DIR, SEC_GOV_OUTPUT_DIR, SEC_GOV_EDGAR_FILINGS_DIR, SEC_EDGAR_ARCHIVES_URL,SEC_GOV_MONTHLY_DIR,SEC_GOV_TXT_LATEST, BASE_DIR, DATA_DIR,SEC_GOV_DAILY_INDEX_DIR
from py_sec_edgar_data.utilities import walk_dir_fullpath, Gotem
from datetime import datetime, date
from datetime import timedelta
import sqlite3
edgar_Archives_url = r'https://www.sec.gov/Archives/'
import pandas as pd
from urllib import parse

from py_sec_edgar_data.settings import SEC_GOV_TXT_DIR, SEC_GOV_FULL_INDEX_DIR

edgar_monthly_index = urljoin(edgar_Archives_url, 'edgar/monthly/')

sec_dates = pd.date_range(datetime.today() - timedelta(days=365*22), datetime.today())
sec_dates_weekdays = sec_dates[sec_dates.weekday < 5]
sec_dates_weekdays = sec_dates_weekdays.sort_values(ascending=False)
sec_dates_months = sec_dates_weekdays[sec_dates_weekdays.day == sec_dates_weekdays[0].day]

idx_files = glob.glob(os.path.join(SEC_GOV_MONTHLY_DIR,"*.xlsx"))
idx_files.sort(reverse=True)

from py_sec_edgar_data.utilities import walk_dir_fullpath

edgar_Archives_url = r'https://www.sec.gov/Archives/'
edgar_full_index = urljoin(edgar_Archives_url,'edgar/full-index/')
edgar_full_master = urljoin(edgar_full_index,'master.idx')

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

import lxml.html
from pprint import pprint
edgar_monthly_url = r"https://www.sec.gov/Archives/edgar/monthly/"
from bs4 import BeautifulSoup

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
    print("Downloading Edgar Monthly XML Files to :" + SEC_GOV_MONTHLY_DIR)
    df = pd.DataFrame(urls, columns=['URLS'])
    df.to_excel(os.path.join(DATA_DIR, 'sec_gov_archives_edgar_monthly_xbrl_urls.xlsx'))
    for url in urls:
        filename = url.split('/')[-1:][0]
        if not os.path.isfile(os.path.join(SEC_GOV_MONTHLY_DIR, filename)) or url == urls[0]:
            fullfilepath = os.path.join(SEC_GOV_MONTHLY_DIR, filename)
            print("Downloading " + fullfilepath)
            g.GET_FILE(url, fullfilepath)

def parse_master_idx():

    local_master_idx = os.path.join(SEC_GOV_FULL_INDEX_DIR, "master.idx")
    old_local_master_idx = '{}.old'.format(local_master_idx)

    if os.path.exists(local_master_idx):
        os.rename(local_master_idx, old_local_master_idx)
    else:
        with open(old_local_master_idx, 'w') as f:
            f.write(str())

    g = Gotem()
    g.GET_FILE(edgar_full_master, local_master_idx)
    g.GET_HTML(edgar_full_master, local_master_idx)
    df = pd.read_csv(local_master_idx, skiprows=10, names=['CIK', 'Company Name', 'Form Type', 'Date Filed', 'Filename'], sep='|', engine='python', parse_dates=True)
    df = df[-df['CIK'].str.contains("---")]
    df = df.sort_values('Date Filed', ascending=False)
    df['published'] = df['Date Filed'].apply(lambda x: datetime.combine(parse(x), parse("12:00:00").time()))
    df['link'] = df['Filename'].apply(lambda x: urljoin(edgar_Archives_url, x))
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
        folder_path_cik = os.path.join(SEC_GOV_TXT_DIR ,'{}/QTR{}'.format(feed_item['published'].year, feed_item['published'].quarter))
        folder_path_cik_other = os.path.join(SEC_GOV_TXT_DIR, 'cik', feed_item['edgar_ciknumber'])

        if not os.path.exists(folder_path_cik):
            os.makedirs(folder_path_cik)

        filepath_cik = os.path.join(folder_path_cik, os.path.basename(feed_item['Filename']))

        if not os.path.exists(filepath_cik) and not os.path.exists(folder_path_cik_other):
            consume_complete_submission_filing_txt.delay(feed_item, filepath_cik)
        else:
            print("Filepath Already exists {}".format(filepath_cik))
            parse_and_download_quarterly_idx_file(edgar_full_master, local_master_idx)


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

def load_headers_files():
    headers_combined = r'E:\DATA\headers.xlsx'
    df_headers_combined = pd.read_excel(headers_combined, header=0, index_col=0, parse_dates=True)

def generate_list_of_local_filings():
    files_master = walk_dir_fullpath(SEC_GOV_TXT_DIR,contains='.txt')
    files_master = [filepath for filepath in files_master if "edgar" not in os.path.basename(filepath)]
    files_master_basename = [os.path.basename(filepath).split(".")[0] for filepath in files_master if "edgar" not in os.path.basename(filepath)]
    files_master.sort(reverse=True)


def download_recent_edgar_filings_xbrl_rss_feed():
    for _ in range(1,2):
        print(_)
        try:
            basename = 'xbrlrss-' + str(datetime.now().year) + '-' + str(datetime.now().month - _).zfill(2) + ".xml"
            filepath = os.path.join(SEC_GOV_MONTHLY_DIR, basename)
            edgarFilingsFeed = parse.urljoin('https://www.sec.gov/Archives/edgar/monthly/', basename)
            g.GET_FILE(edgarFilingsFeed, filepath)
        except Exception as e:
            print(e)

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

def generate_monthly_index_url_and_filepaths(day):
    basename = 'xbrlrss-' + str(day.year) + '-' + str(day.month).zfill(2)
    monthly_local_filepath = os.path.join(SEC_GOV_MONTHLY_DIR, basename + ".xml")
    monthly_url = urljoin('https://www.sec.gov/Archives/edgar/monthly/', basename + ".xml")
    return monthly_url, monthly_local_filepath
# https://www.sec.gov/Archives/edgar/daily-index/2017/QTR3/
#/Archives/edgar/daily-index — daily index files through the current year;

edgar_Archives_url = r'https://www.sec.gov/Archives/'

edgar_daily_index = urljoin(edgar_Archives_url,'edgar/daily-index/')

def generate_daily_index_urls_and_filepaths(day):
    edgar_url = r'https://www.sec.gov/Archives/edgar/'
    daily_files_templates = ["master", "form", "company", "crawler", "sitemap"]
    date_formated = datetime.strftime(day, "%Y%m%d")
    daily_files = []
    for template in daily_files_templates:
        download_url = urljoin(edgar_url, "daily-index/{}/QTR{}/{}.{}.idx".format(day.year, day.quarter, template, date_formated))
        local_filepath = os.path.join(SEC_GOV_DAILY_INDEX_DIR, "{}".format(day.year), "QTR{}".format(day.quarter), "{}.{}.idx".format(template, date_formated))
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

def parse_monthly():
    tickercheck_cik = os.path.join(DATA_DIR, 'TICKERCHECK_CIK_COMPANIES_ONLY.xlsx')
    cik_ticker = os.path.join(DATA_DIR, 'cik_ticker_name_exchange_sic_business_incorporated_irs.xlsx')
    df_tickercheck = pd.read_excel(tickercheck_cik, index_col=0, header=0)
    df_cik_ticker = pd.read_excel(cik_ticker, index_col=0, header=0)
    df_cik_ticker = df_cik_ticker.reset_index()
    # i, day = list(enumerate(sec_dates_months))[0]
    prev_val = datetime.today()
    for i, day in enumerate(sec_dates_months):
        if day.month != prev_val.month:
            monthly_url, monthly_local_filepath= generate_monthly_index_url_and_filepaths(day)
            # status = determine_if_sec_edgar_feed_and_local_files_differ(monthly_url, monthly_local_filepath)
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
                    month_dir = os.path.join(SEC_GOV_TXT_DIR, str(day.year), '{:02d}'.format(day.month))

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

def main(edgar_feed_list="IDX"):

    if edgar_feed_list == "XBRL_XML":
        ext='.xml'
        files = glob.glob(os.path.join(SEC_GOV_MONTHLY_DIR,"*{}".format('.xml')))
        tablename = 'EDGAR_XBRLRSS_XML_ENTRIES'
        #OUTPUT_FILENAME = os.path.join(SEC_GOV_MONTHLY_DIR,os.path.basename(source_file.replace(ext, ".xlsx")))

    if edgar_feed_list == "XBRL_XLSX":
        edgar_feed_list = "XBRL_XLSX"
        ext='.xlsx'
        files = glob.glob(os.path.join(SEC_GOV_MONTHLY_DIR,"*{}".format(ext)))
        tablename = 'EDGAR_XBRLRSS_XML_ENTRIES'
        #OUTPUT_FILENAME = os.path.join(SEC_GOV_MONTHLY_DIR,os.path.basename(source_file.replace(ext, ".xlsx")))
        # DIR,os.path.basename(source_file.replace(ext, ".xlsx")))

    elif edgar_feed_list == "IDX":
        edgar_feed_list = "IDX"
        ext = ".idx"
        #files = glob.glob(os.path.join(SEC_GOV_FULL_INDEX_DIR,"*{}".format('.idx')))
        # df["BASENAME"] = df["FILENAME"].apply(lambda x: os.path.basename(x).split(".")[0])

        master_files = walk_dir_fullfilename(SEC_GOV_FULL_INDEX_DIR,contains="master.idx")
        files.sort(reverse=True)
        files = [file for file in files if "old" not in file]
        # years = [year for year in range(1994, 2018)]
        # files = [filepath for filepath in files if any(str(year) in filepath for year in years)]
        edgar_feed_list = "IDX"
        #OUTPUT_FILENAME = os.path.join(SEC_GOV_FULL_INDEX_DIR,os.path.basename(source_file.replace(ext, ".xlsx")))
        tablename = 'EDGAR_IDXRSS_MASTER_FEED'
    else:
        return

    frame = pd.DataFrame()
    #source_file = files[0]
    for source_file in files:
        print("Parsing ", source_file)
        if "XBRL_XML" in edgar_feed_list:
            list_ = []
            feed = feedparser.parse(source_file)
            # item = feed.entries[10]
            for item in feed.entries:
                e = flattenDict(item)
                d = pd.DataFrame.from_dict(e, orient='index')
                d.columns = ['VALUES']
                d.index = [ind.replace(".","_").replace(":","_").upper() for ind in d.index.tolist()]
                d = d.T
                match = d['EDGAR_XBRLFILE_FILE'].str.replace("-.+","").str.upper().tolist()[0]
                if "." in match or len(match) > 13:
                    d['TICKER'] = "--"
                else:
                    d['TICKER'] = match
                #df = df.append(d.T)
                list_.append(d)
            df = pd.concat(list_)
        else:
            if source_file.endswith(".csv"):
                df = pd.read_csv(source_file, skiprows=10, names=['CIK', 'Company Name', 'Form Type', 'Date Filed', 'Filename'], sep='|', engine='python')
                df['SOURCE_FILENAME'] = source_file.split("full-index\\")[1].replace("\\", "_").upper()
                df = df[-df['CIK'].str.contains("---")]

            if source_file.endswith(".xlsx"):
                df = pd.read_excel(source_file,index_col=0, header=0, parse_dates=True)

            df['SOURCE_IMPORT_TIMESTAMP'] = datetime.now().strftime("%Y-%m-%dTZ%H-%M-%S")
            new_columns_names = [column_name.replace(".", "_").replace(":", "_").replace(" ", "_").upper() for column_name in df.columns.tolist()]
            df.columns = new_columns_names
            frame = frame.append(df)
            try:
                frame = frame.drop_duplicates(subset=['EDGAR_ACCESSIONNUMBER'])
            except:
                pass
            frame['dir_name'] = frame['link'].apply(lambda x: x.rsplit('/', 1)[0])
            frame['Financial_Report'] = frame['dirname'].apply(lambda x: '{}/{}'.format(x, "Financial_Report.xlsx"))
            frame.to_sql("TABLE_XBRL", conn, if_exists='replace',index=False)

        frame.columns = [col.lower() for col in frame.columns.tolist()]

        frame = frame[frame['edgar_formtype'].isin(['10-K'])]
        frame['edgar_filingdate']=frame['edgar_filingdate'].apply(lambda x: datetime.strptime(str(x), "%m/%d/%Y"))
        frame=frame.sort_values('edgar_filingdate',ascending=False)

        new_columns_names = [column_name.replace(".","_").replace(":","_").lower() for column_name in df.columns.tolist()]
        df.columns = new_columns_names
        df['SOURCE_FILENAME'.format(edgar_feed_list.upper())] = os.path.basename(source_file)
        df['SOURCE_IMPORT_TIMESTAMP'.format(edgar_feed_list.upper())] = datetime.now()
        df.index = [icount for icount in range(0, len(df.index.tolist()))]
        df.index.name = '_id'
        OUTPUT_FILENAME = os.path.join(os.path.dirname(source_file), os.path.basename(source_file.replace(ext, ".xlsx")))
        print("exporting to excel {}".format(OUTPUT_FILENAME))
        df.to_excel(OUTPUT_FILENAME)
        print("inserting into SQL DB")
        # df.to_sql(tablename, engine,index_label="_id", if_exists='append')


if __name__ == '__main__':

    import argparse
    parser = argparse.ArgumentParser(description='SEC DATA Extract Header from Filing')
    parser.add_argument('--input_filepath', help='Input the Year(s) or ALL', action='append', nargs='*')
    parser.add_argument('--ticker', help='Input the Ticker(s) or ALL keyword', action='append', nargs='*')

    if len(sys.argv[1:]) >= 1:
        args = parser.parse_args()
        extract_header_from_filing(input_filepath=args.input_filepath[0], ticker=args.ticker[0])
    else:
        sys.exit(parser.print_help())
