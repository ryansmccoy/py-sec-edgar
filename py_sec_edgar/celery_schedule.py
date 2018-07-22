import bisect
import json
import os
import os.path
from datetime import datetime, date
from datetime import timedelta
from urllib import parse
from urllib.parse import urljoin

import pandas as pd

import py_sec_edgar

# from dateparser import parse
# from dateutil.parser import parse

desired_width = 600
pd.set_option('display.width', desired_width)
from py_sec_edgar.database import query_db_for_filings_data

sec_dates = pd.date_range(
    datetime.today() - timedelta(days=365 * 22), datetime.today())
sec_dates_weekdays = sec_dates[sec_dates.weekday < 5]
sec_dates_weekdays = sec_dates_weekdays.sort_values(ascending=False)
sec_dates_months = sec_dates_weekdays[sec_dates_weekdays.day ==
                                      sec_dates_weekdays[0].day]
from py_sec_edgar.settings import Config
CONFIG = Config()

# form_filter = ['8-K','424','424']
# form_filter = ['10-K']
#conn_local = sqlite3.connect(os.path.join(DATA_DIR, "LOCAL_FILEPATHS.DB"))


def get_quarter_begin(date_value):
    qbegins = [date(date_value.year, month, 1) for month in (1, 4, 7, 10)]
    idx = bisect.bisect(qbegins, date_value)
    return qbegins[idx - 1]


def edgar_filing_idx_create_filename(item):
    date_string = str(parse(item['published']).strftime("%Y-%m-%dTZ%H-%M-%S"))
    edgfilepath = 'edgaridx-{}_txt_#2_{}_#3_{}_#4_{}_#5_({})_{}_#6_{}_#7_{}.txt'.format(
        str(item['edgar_filingdate'][0:6]), os.path.dirname(item['link'].replace(r'http://www.sec.gov/Archives/', "")).replace("/", "_"), date_string, item['edgar_ciknumber'], item['ticker'], item['edgar_companyname'],
        item['edgar_formtype'], str(item['edgar_period']))
    edgfilepath = edgfilepath.replace(" ", "_").replace(",", "_").replace(
        ".", "_").replace("/", "_").replace("\\", "_").replace("__", "_").replace("_txt", "")
    return edgfilepath


def cik_ticker_lookup():
    df_tickcheck = pd.read_excel(CONFIG.tickercheck, index_col=0, header=0)
    df_tickcheck['CIK'] = df_tickcheck['CIK'].fillna(
        "-1").astype(int).astype(str)
    df_tick = df_tickcheck.set_index('CIK')
    df_tick = df_tick[df_tick.index != "-1"]
    return df_tick


def celery_feed_all_filings_for_download(df_all_filings, celery_enabled=True):
    all_items = []
    for ii, file in enumerate(df_all_filings.itertuples()):

        quarter = '{}'.format(datetime.strptime(file.DATE_FILED, '%Y-%m-%d').year), "QTR{}".format(
            int((datetime.strptime(file.DATE_FILED, '%Y-%m-%d').month - 1) / 3) + 1)
        item = {}

        for k, v in dict(file._asdict()).items():
            item[k] = str(v)

        item['YEAR'] = '{}'.format(quarter[0])
        item['QUARTER'] = "{}".format(quarter[1])
        item['FILE'] = '{}'.format(os.path.basename(file.FILENAME))
        url_quarter = 'edgar/data/{}/{}/{}'.format(file.CIK, os.path.basename(
            file.FILENAME).replace("-", "").replace(".txt", ""), os.path.basename(file.FILENAME))
        item['URL'] = urljoin(edgar_Archives_url, url_quarter)
        item['LOCAL'] = os.path.join('{}'.format(quarter[0]), "{}".format(
            quarter[1]), '{}'.format(os.path.basename(file.FILENAME)))
        item['OUTPUT_FOLDER'] = 'filings'
        item['OVERWRITE_FILE'] = False

        item['windows_output_folder'] = os.path.join(
            CONFIG.SEC_EDGAR_FILINGS_DIR, os.path.dirname(item['LOCAL']))
        item['windows_output_filepath'] = os.path.join(
            CONFIG.SEC_EDGAR_FILINGS_DIR, item['LOCAL'])
        all_items.append(item)

        if not os.path.exists(item['windows_output_folder']):
            os.makedirs(item['windows_output_folder'])

        if not os.path.exists(item['windows_output_filepath']):
            print("downloading {}".format(item['windows_output_filepath']))
            if celery_enabled == True:
                py_sec_edgar.celery_consumer_filings.consume_sec_filing_txt.delay(
                    json.dumps(item))
            else:
                import requests
                r = requests.get(item['URL'])
                with open(os.path.join(item['windows_output_filepath']), 'w', encoding='utf-8') as f:
                    f.write(r.text)
        else:
            print("Filepath Already exists {}".format(
                item['windows_output_filepath']))

    return all_items
    #df.to_sql("LOCAL_FILEPATHS",conn_local, if_exists='append',index=False)


def filter_form(df_filings, form_filter):
    df_frame = df_filings[df_filings['FORM_TYPE'].isin(form_filter)]
    return df_frame

#
# Docker (Work in Progress)
#
#     $  docker run -d -p 5672:5672 -p 15672:15672 --name sec-rabbit rabbitmq:management
#     $  celery -A edgar_download.celery_download_complete_submission_filing worker --loglevel=info


def main():
    start_date = "2015-01-01"
    end_date = "2017-06-30"
    dates_quarters = generate_folder_names_years_quarters(end_date, start_date)
    all_files = []
    years_all = []
    form_filter = ['ABS-15G', 'ABS-15G/A']
    # form_filter = ['10-K', '20-F']
    # qtr_date = dates_quarters[0]
    for qtr_date in dates_quarters:
        df_all_filings = query_db_for_filings_data(
            qtr_date, form_filter=form_filter)
        df_filings = celery_feed_all_filings_for_download(df_all_filings)
        all_files.append(pd.DataFrame(df_filings))

    # df = df_all_filings.sort_values("DATE_FILED", ascending=False)

    #df_frame = filter_form(df, fund_form_filter)

    all_items = celery_feed_all_filings_for_download(df_frame.iloc[0:5000, :])
    df_all_items = pd.DataFrame(all_items)
    df_all_items.to_csv(os.path.join(CONFIG.DATA_DIR, "N-Q_filings.csv"))
    for year, quarter in dates_quarters:
        years_all.append(year)

    years_all = list(set(years_all))

    # year = years_all[0]
    for year in years_all:
        files = scan_all_local_filings(year)
        all_files.append(files)

    all_files_flat = sum(all_files, [])
    len(all_files_flat)
    files = [file.split("\\")[-1] for file in all_files_flat]
    uni = list(set(files))

    df_all_filings['SHORT'] = df_all_filings['FILENAME'].apply(
        lambda x: x.split("/")[-1])

    df_l = pd.DataFrame(uni, columns=['FILENAME'])
    df_l.to_excel(os.path.join(CONFIG.DATA_DIR, "all_filings_local.xlsx"))
    df_all_downloaded = df_all_filings[df_all_filings['SHORT'].isin(uni)]
    df_all_downloaded.to_excel(os.path.join(
        CONFIG.DATA_DIR, "all_fili2ngs.xlsx"))


if __name__ == "__main__":
    main()
