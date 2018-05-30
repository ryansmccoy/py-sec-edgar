import sys
sys.path.append('..')

#####################
import os.path
import subprocess

#   edgar_filings_celery_tasks.py
# need to import class if using seperate files
import lxml.html
import pandas as pd
import redis
import os
from time import sleep
from py_sec_edgar_data.edgar_filing.html_main import extract_content_from_complete_submittion_txt_filing
from py_sec_edgar_data.edgar_config import  SEC_GOV_EDGAR_FILINGS_DIR, SEC_GOV_EDGAR_DIR, SECDATA_DIR_ROOT, SEC_GOV_FULL_INDEX_DIR,SSD_DATA_DIR
from py_sec_edgar_data.edgar_utilities import gotem
from py_sec_edgar_data.edgar_utilities.edgar_filename import edgar_filing_idx_create_filename
from py_sec_edgar_data.edgar_download.cik_ticker_loader import cik2ticker, get_cik_from_ticker
# celery -A edgar_download.edgar_download/celery_download_complete_submission_filing worker --loglevel=info
from kombu import serialization
from celery import Celery
app = Celery('tasks', broker= "amqp://guest:guest@127.0.0.1:5672/")
app.conf.update(CELERY_ACCEPT_CONTENT=['json','application/x-python-serialize'],
                CELERY_TASK_SERIALIZER = 'json',
                CELERY_RESULT_SERIALIZER = 'json')
# app = Celery('tasks', broker='amqp://gotem:gotem@localhost')
# C:\SECDATA\sec-data-python\sec_data
# df = pd.read_excel(r'C:\gcloud-repos\secdata-repo\annual_html.xlsx')
#   pip install celery==3.1.21
#   celery -A celery_complete_submission_download worker --loglevel=info
#   celery -A edgar_download.celery_download_complete_submission_filing worker --loglevel=info
#   from celery.task.control import discard_all
#   discard_all()
#   ^ use above to clear celery queue
# celery -A edgar_elastic.elastic_update worker --loglevel=info
# docker run --link some-rabbit:rabbit --name some-celery -v c:\users\ryan\data:/home/user/data -d celery
###################################

from edgar_utilities.feed_finder import find_feeds
######################################
#  multi-step process for downloading html data from Edgars
#  See Edgar_filings_redis
# gsutil cp -n -r gs://gc-gotem-sec-data/data
from bs4 import BeautifulSoup
import json

@app.task(bind=True, max_retries=3)
def celery_consume_rss_feed(self, item):
    item = json.loads(item)
    item = item['ITEM']
    feeds = find_feeds(item['RSS_PAGE'])
    for i,feed in enumerate(feeds):
        item.update({i:feed})
    vals = pd.DataFrame.from_dict(item,orient='index')
    vals.to_csv(os.path.join(SSD_DATA_DIR,"{}.csv".format(item['netloc'])))

@app.task(bind=True, max_retries=3)
def celery_extract_content_from_complete_submittion_txt_filing(self, item):
    item = json.loads(item)

    if item['OUTPUT_FOLDER'] == "full-index":
        filepath = os.path.join(SEC_GOV_FULL_INDEX_DIR, item['RELATIVE_FILEPATH'])
    elif item['OUTPUT_FOLDER'] == 'filings':
        filepath = os.path.join(SEC_GOV_EDGAR_FILINGS_DIR, item['YEAR'], item['QUARTER'],item['FILE'])
    output_filepath = os.path.join(OUTPUT_DIR,item['CIK'],item['FILE'].replace('-',"").replace(".txt",""))
    print(output_filepath)
    extract_content_from_complete_submittion_txt_filing(input_filepath=filepath, output_filepath=output_filepath,extract_items=['HEADER_AND_DOCUMENTS'])

@app.task(bind=True, max_retries=3)
def consume_sec_filing_txt(self, item):
    item = json.loads(item)

    if item['OUTPUT_FOLDER'] == "full-index":
        filepath = os.path.join(SEC_GOV_FULL_INDEX_DIR, item['RELATIVE_FILEPATH'])
    elif item['OUTPUT_FOLDER'] == 'filings':
        filepath = os.path.join(SEC_GOV_EDGAR_FILINGS_DIR, item['YEAR'], item['QUARTER'],item['FILE'])

    if not os.path.exists(filepath) or item["OVERWRITE_FILE"] == True:
        try:
            g = gotem.Gotem()
            print(' [ X ] Requesting URL')
            g.GET_FILE(item['URL'], filepath)
            print(" [ X ] ", filepath)
        except:
            print(" ... trying again")
            self.retry(countdown=int(random.uniform(1, 2) ** self.request.retries))
            print('waiting 3 seconds')
            sleep(3)
    else:
        print("file already downloaded")

@app.task(bind=True, max_retries=3)
def r2_download_index_page(self, url, filename):
    xpath = r'//*[@id="formDiv"]/div/table'
    g = gotem.Gotem()
    # url = urls[0]
    # dataitem = list(df_banks.iterrows())[0]
    try:
        if r2.get(filename):
            print("data already availible")
        else:
            g.GET_HTML(url)
            root = lxml.html.fromstring(g.r.text)
            root.make_links_absolute(r'https://www.sec.gov', resolve_base_href=True)
            soup = BeautifulSoup(lxml.html.tostring(root).decode('utf-8'), "html.parser")
            g = gotem.Gotem()
            print(' [ X ] Requesting URL')
            g.GET_HTML(url)
            r4.set(filename, str(g.r.text))
    except:
        print('error')

main_url = r'https://www.sec.gov'

@app.task(bind=True, max_retries=3)
def r4_download_htmls_files_from_edgars(self, url, filename=None):
    try:
        if r4.get(filename):
            print("data already availible")
        else:
            g = gotem.Gotem()
            print(' [ X ] Requesting URL')
            g.GET_HTML(url)
            r4.set(filename, str(g.r.text))
    except:
        self.retry(countdown=int(random.uniform(2, 4) ** self.request.retries))
        print('waiting 3 seconds')
        sleep(3)


def r6_process_htmls_files_from_edgars(key):
    urls = []
    main_url = r'https://www.sec.gov'
    try:
        rhtml = r4.get(key).decode()
        lhtml = lxml.html.fromstring(rhtml)
        lhtml.make_links_absolute(main_url)
        html = lxml.html.tostring(lhtml)
        soup = BeautifulSoup(html, 'lxml')
        [urls.append(link['href']) for link in soup.find_all('a', href=True)]
        urls = [i for i in urls if "Archive" in i]
        df = pd.DataFrame(urls, columns=['URLS'])
        data = df.T.to_json()
        r6.set(key, str(data))
    except:
        print('prob celery ' + key)
        r6.set(key, "error pulling urls from redis")


#######################
#

@app.task(bind=True, max_retries=3)
def r8_download_all_files_from_single_edgars_filings(self, url, filename):
    main_url = r'https://www.sec.gov'
    try:
        g = gotem.Gotem()
        print(' [ X ] Requesting URL')
        html = g.GET_HTML(url)
        print(" [ X ] ", filename)
        # html = requests.get(url)
        r8.set(filename, html.text)
        print(" [ X ] Saved 2 Redis")
    except:
        print("xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxprob with celery... trying again")
        self.retry(countdown=int(random.uniform(2, 4) ** self.request.retries))
        print('waiting 3 seconds')
        sleep(3)

#######################
#

######################################
#  celery_process_sec_filing_with_arelle

import random, string

# filename = r'B:\SEC\IN\xbrlrss-2017-04\xbrlrss-2010-02_xml#2_000-50831_#3_2010-02-22TZ00-00-00_#4_0001281761_#5_REGIONS_FINANCIAL_CORP_#6_10-K_#7_20091231.zip'

@app.task
def celery_process_sec_filing_with_arelle(filename):
    """
    Process SEC Edgar Zip files containing XML files from period ending, example below:

    C:\SEC\IN\2017\03\CIK(0001579428)_FORM(10-K)_PERIOD(20161231).zip
        Files within Zipfile:

            rvlt-20161231_pre.xml
            rvlt-20161231_lab.xml
            rvlt-20161231_def.xml
            rvlt-20161231_cal.xml
            rvlt-20161231.xsd
            rvlt-20161231.xml

    :param filename: i.e. C:\SEC\IN\2017\03\CIK(0001579428)_FORM(10-K)_PERIOD(20161231).zip
    :return: new zip file containing financial_report.xlsx i.e. C:\SEC\OUT\2017\03\CIK(0001579428)_FORM(10-K)_PERIOD(20161231).zip
    """

    pythonfile = r'C:\Python\envs\stocks\python.exe'
    edgarpython = r'C:\Arelle\re3\edgarrenderer\EdgarRenderer.py'
    tempfoldername = str(''.join(random.choice(string.ascii_lowercase) for i in range(24)))
    os.mkdir(os.path.join(os.path.dirname(filename), tempfoldername))

    try:
        print("-> Starting: [{}]".format(filename))
        subprocess.Popen(
            [pythonfile, edgarpython, '--reports', tempfoldername, '--xdgConfigHome=C:\\Arelle\\re3', '-f', filename,
             '-o', filename.replace("\\IN\\", "\\OUT\\")])
    except:
        print('error: {}'.format(filename))

@app.task(bind=True, max_retries=3)
def celery_download_edgars_alternative_files(self, url, filename):
    try:
        g = gotem.Gotem()
        print(' [ X ] Requesting URL')
        print(" [ X ] ", filename)
        # html = requests.get(url)
        g.GET_FILE(url, filename)
        print(" [ X ] Saved 2 Disk")
    except:
        print(" [   ] trying again")
        self.retry(countdown=int(random.uniform(2, 4) ** self.request.retries))


##################################

def extract_from_redis_to_local():
    datapath = r'SEC\EDGAR_FILINGS'
    keys = r10.keys("*")
    for key in keys:
        try:
            key = key.decode()
            key = key.replace("\\", "_")
            # key = keys[0].decode()
            # s= list(cik_dict.values())[0]
            data = r10.get(key).decode()
            fullfilepath = os.path.join(onedrive, key + '.txt')
            if os.path.exists(os.path.join(onedrive, key + '.txt')):
                print("filename already exists")
            else:
                with io.open(fullfilepath, "w", encoding="utf-8") as f:
                    f.write(data)
        except:
            print('cant save file' + fullfilepath)

@app.task(bind=True, max_retries=3)
def consume_complete_submission_filing(self, basename, item, ticker):
    main_url = r'https://www.sec.gov'
    if ticker == "TICKER":
        try:
            ticker = cik2ticker(item['ed.gar_ciknumber'])
        except:
            try:
                ticker = item['edgar_xbrlfile.file'].split('-')[0].upper()
                if "JPG" in ticker:
                    ticker = get_cik_from_ticker([item['edgar_ciknumber']])
            except:
                print("searching online")
                ticker = get_cik_from_ticker([item['edgar_ciknumber']])
                print(ticker)

    folder_path = os.path.join(SEC_GOV_EDGAR_FILINGS_DIR, basename.replace("xbrlrss-","").replace("-","/"))
    edgfilename = edgar_filing_idx_create_filename(basename, item, ticker)
    url = item['link'].replace("-index.htm", ".txt")
    filepath = os.path.join(folder_path, edgfilename)

    if not os.path.exists(filepath):
        try:
            g = gotem.Gotem()
            print(' [ X ] Requesting URL')
            g.GET_FILE(url, filepath)
            print(" [ X ] ", filepath)
        except:
            print("xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxprob with celery... trying again")
            self.retry(countdown=int(random.uniform(2, 4) ** self.request.retries))
            print('waiting 3 seconds')
            sleep(3)
    else:
        print("file already downloaded")


@app.task(bind=True, max_retries=3)
def consume_complete_submission_filing_txt(self, item, filepath):
    main_url = r'https://www.sec.gov'
    if not os.path.exists(filepath):
        try:
            g = gotem.Gotem()
            print(' [ X ] Requesting URL')
            g.GET_FILE_CELERY(item['link'], filepath)
            print(" [ X ] ", filepath)
        except:
            print("... trying again")
            self.retry(countdown=int(random.uniform(2, 4) ** self.request.retries))
    else:
        print("file already downloaded")

