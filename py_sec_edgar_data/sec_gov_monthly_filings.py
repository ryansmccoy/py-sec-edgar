

edgar_Archives_url = r'https://www.sec.gov/Archives/'

edgar_monthly_index = urljoin(edgar_Archives_url, 'edgar/monthly/')

sec_dates = pd.date_range(datetime.today() - timedelta(days=365*22), datetime.today())
sec_dates_weekdays = sec_dates[sec_dates.weekday < 5]
sec_dates_weekdays = sec_dates_weekdays.sort_values(ascending=False)
sec_dates_months = sec_dates_weekdays[sec_dates_weekdays.day == sec_dates_weekdays[0].day]

idx_files = glob.glob(os.path.join(SEC_GOV_MONTHLY_DIR,"*.xlsx"))
idx_files.sort(reverse=True)

def download_recent_edgar_filings_xbrl_rss_feed():
    basename = 'xbrlrss-' + str(datetime.datetime.now().year) + '-' + str(datetime.datetime.now().month).zfill(2) + ".xml"
    filepath = os.path.join(SEC_XBRL_DIR, basename)
    edgarFilingsFeed = parse.urljoin('http://www.sec.gov/Archives/edgar/monthly/', basename)
    g = gotem.Gotem()
    g.GET_FILE(edgarFilingsFeed, filepath)
    return filepath

def generate_monthly_index_url_and_filepaths(day):
    basename = 'xbrlrss-' + str(day.year) + '-' + str(day.month).zfill(2)
    monthly_local_filepath = os.path.join(SEC_GOV_MONTHLY_DIR, basename + ".xml")
    monthly_url = urljoin('http://www.sec.gov/Archives/edgar/monthly/', basename + ".xml")
    return monthly_url, monthly_local_filepath

def get_sec_monthly_listings():
    g = gotem.Gotem()
    g.GET_URLS(edgar_monthly_url)
    urls = [i for i in g.list_urls if "xml" in i]
    urls.sort(reverse=True)
    print("Downloading Edgar Monthly XML Files to :" + SEC_XBRL_MONTHLY_DIR)
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
        cik_ticker = os.path.join(DATA_DIR, 'cik_ticker.xlsx')
        df_tickercheck = pd.read_excel(tickercheck_cik, index_col=0, header=0)
        df_cik_ticker = pd.read_excel(cik_ticker, index_col=0, header=0)
        df_cik_ticker = df_cik_ticker.reset_index()
        # i, day = list(enumerate(sec_dates_months))[0]
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
