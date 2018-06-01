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

edgar_monthly_index = urljoin(edgar_Archives_url, 'edgar/monthly/')

sec_dates = pd.date_range(datetime.today() - timedelta(days=365*22), datetime.today())
sec_dates_weekdays = sec_dates[sec_dates.weekday < 5]
sec_dates_weekdays = sec_dates_weekdays.sort_values(ascending=False)
sec_dates_months = sec_dates_weekdays[sec_dates_weekdays.day == sec_dates_weekdays[0].day]

idx_files = glob.glob(os.path.join(SEC_GOV_MONTHLY_DIR,"*.xlsx"))
idx_files.sort(reverse=True)
g = Gotem()


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
                g = gotem.Gotem()
                g.GET_FILE(daily_url,daily_local_filepath)


edgar_monthly_url = r"https://www.sec.gov/Archives/edgar/monthly/"
def get_sec_monthly_listings():
    g = Gotem()
    g.GET_HTML(edgar_monthly_url)
    urls = [i for i in g.list_urls if "xml" in i]
    urls.sort(reverse=True)
    print("Downloading Edgar Monthly XML Files to :" + SEC_GOV_MONTHLY_DIR)
    df = pd.DataFrame(urls, columns=['URLS'])
    df.to_excel(secfiles_urls)
    for url in urls:
        filename = url.split('/')[-1:][0]
        if not os.path.isfile(os.path.join(SEC_XBRL_MONTHLY_DIR, filename)) or url == urls[0]:
            fullfilepath = os.path.join(SEC_XBRL_MONTHLY_DIR, filename)
            print("Downloading " + fullfilepath)
            g.GET_FILE(url, fullfilepath)

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

if __name__ == "__main__":
    g = Gotem()
    g.GET_URLS(edgar_monthly_url)
