
results = []
celery = Celery()
celery.config_from_object('celeryconfig')
broker_url = 'amqp://guest:guest@localhost:5672//'

CELERY_IMPORTS = ('tasks')
CELERY_IGNORE_RESULT = False
BROKER_HOST = "127.0.0.1" #IP address of the server running RabbitMQ and Celery
BROKER_PORT = 5672
BROKER_URL='amqp://'
CELERY_RESULT_BACKEND = "amqp"
CELERY_IMPORTS=("tasks",)

# print('grabbing html files')
# url = config['EDGAR_URLS']['edgar_monthly_xml_list']
from py_sec_edgar.settings import flattenDict


def main(mode=None):
    month = 6
    year = 2017
    itemIndex = 0
    html_files_urls = {}
    sec_edgar_entries = {}
    basename, edgurl = edgar_filings_feed(year=year, month=month)

    feed = read_xml_feedparser(edgurl)
    url=r'https://www.sec.gov/Archives/edgar/daily-index/2017/QTR3/master.20170727.idx'
    i, item = list(enumerate(feed.entries))[5]
    for i, item in list(enumerate(feed.entries)):
        if ("10-K" in item["edgar_formtype"]):
            # or ("S-1" in item["edgar_formtype"]) or ("20-F" in item["edgar_formtype"]):
            flat_item = flattenDict(item)
            pprint(flat_item)
            sec_edgar_entries[i] = flat_item
            edgfilename = create_edgarfilename(basename, item)
            print(edgfilename)
            sec_edgar_entries[edgfilename] = item
            url = flat_item['link'].replace("-index.htm",".txt")
            filepath =  os.path.join(SEC_TXT_DIR, edgfilename+".txt")
            if not os.path.exists(filepath):
                edgar_download.edgars_download_celery_tasks.celery_download_edgars_complete_submission_file.delay(url,filepath)
