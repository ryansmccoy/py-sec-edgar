import py_sec_edgar_data.tasks

import time
if __name__ == '__main__':
    for _ in range(10):
        result = py_sec_edgar_data.tasks.download_recent_edgar_filings_xbrl_rss_feed.delay()
        print('Task finished?',result.ready())
        print('Task result:',result.result)
        time.sleep(1)
        print('Task finished"',result.ready())
        print('Task result:',result.result)

