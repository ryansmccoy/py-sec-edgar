from urllib import parse
import datetime
import os
from py_sec_edgar_data.settings import SEC_TXT_DIR, SEC_OUTPUT_DIR, DATA_DIR, SEC_IDX_DIR,SEC_XBRL_DIR

from celery import Celery
import glob

import subprocess

# C:\Program Files\MongoDB\Server\3.4\bin\mongod.exe --db=C:\Users\ryan\PycharmProjects\sec-edgars\sec-edgars\data\mongo\db

now = datetime.datetime.now()

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

def main():
    pypath = r'C:\Users\ryan\PycharmProjects\sec_data\sec_data\edgar_filings_celery_tasks_download.py'
    pythonfile = r'C:\Users\ryan\AppData\Local\conda\conda\envs\edgarfilings\python.exe'
    from_year = 2016
    to_year = 2017
    XBRLLocation = "local"
    UpdateXBRLurls = False

    if XBRLLocation == "local":
        print("Globbing XBRL files in folder: " + XBRLfolder)
        xbrlfiles = glob.glob(os.path.join(SEC_XBRL_DIR,"*"))
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


# celery -A celery_task_processer worker --loglevel=info
if __name__ == "__main__":
    main()
