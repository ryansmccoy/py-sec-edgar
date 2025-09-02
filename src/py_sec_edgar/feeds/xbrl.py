import logging
import os
from datetime import datetime
from urllib import parse

import pandas as pd
import requests

from ..settings import CONFIG
from ..utilities import RetryRequest


def download_edgar_filings_xbrl_rss_files():
    # download first xbrl file availible

    g = RetryRequest()

    start_date = datetime.strptime("4/1/2005", "%m/%d/%Y")
    end_date = datetime.now()
    dates = [x for x in pd.date_range(start_date, end_date, freq='MS')]
    dates.reverse()
    http_headers = {'User-Agent': CONFIG.user_agent}
    for date in dates:
        try:

            basename = 'xbrlrss-' + \
                       str(date.year) + '-' + str(date.month).zfill(2) + ".xml"
            filepath = os.path.join(CONFIG.MONTHLY_DATA_DIR, basename)
            edgarFilingsFeed = parse.urljoin(
                'https://www.sec.gov/Archives/edgar/monthly/', basename)
            if not os.path.exists(filepath):
                # Rate limiting: respect SEC's 10 requests per second limit
                import time
                time.sleep(CONFIG.request_delay)
                r = requests.get(CONFIG.edgar_monthly_index, headers=http_headers)
                g.get(edgarFilingsFeed, filepath)

        except Exception as e:
            logging.info(e)
