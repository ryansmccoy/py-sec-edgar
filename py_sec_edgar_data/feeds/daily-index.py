
#######################
# DAILY FILINGS FEEDS
# https://www.sec.gov/Archives/edgar/daily-index/
import os
from datetime import datetime
from urllib.parse import urljoin

from py_sec_edgar_data.feeds import CONFIG, determine_if_sec_edgar_feed_and_local_files_differ
from py_sec_edgar_data.gotem import Gotem
from datetime import timedelta
import pandas as pd

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
    sec_dates = pd.date_range(datetime.today() - timedelta(days=365 * 22), datetime.today())
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
