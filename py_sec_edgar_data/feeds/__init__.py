# view-source:https://www.sec.gov/Archives/edgar/xbrl-rr.rss.xml
# https://www.sec.gov/Archives/edgar/usgaap.rss.xml
# https://www.sec.gov/Archives/edgar/xbrl-inline.rss.xml
# https://www.sec.gov/Archives/edgar/usgaap.rss.xml
# http://www.sec.gov/Archives/edgar/xbrlrss.all.xml
# https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&CIK=&type=10-K&company=&dateb=&owner=include&start=0&count=100&output=atom

from py_sec_edgar_data.utilities import flattenDict, file_size
import pandas as pd
desired_width = 600
pd.set_option('display.width', desired_width)

import subprocess

import feedparser
import os
import glob
from py_sec_edgar_data.settings import Config
from py_sec_edgar_data.gotem import Gotem
from datetime import datetime

CONFIG = Config()
import pandas as pd

from py_sec_edgar_data.utilities import walk_dir_fullpath

from py_sec_edgar_data.settings import Config


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

def generate_list_of_local_filings():
    files_master = walk_dir_fullpath(CONFIG.SEC_TXT_FILING_DIR, contains='.txt')
    files_master = [filepath for filepath in files_master if "edgar" not in os.path.basename(filepath)]
    files_master_basename = [os.path.basename(filepath).split(".")[0] for filepath in files_master if "edgar" not in os.path.basename(filepath)]
    files_master.sort(reverse=True)

####################### FULL-INDEX

def convert_list_of_filings_to_excel(edgar_feed_list="IDX"):

    if edgar_feed_list == "XBRL_XML":
        ext='.xml'
        files = glob.glob(os.path.join(CONFIG.SEC_MONTHLY_DIR,"*{}".format('.xml')))
        tablename = 'EDGAR_XBRLRSS_XML_ENTRIES'
        #OUTPUT_FILENAME = os.path.join(SEC_MONTHLY_DIR,os.path.basename(source_file.replace(ext, ".xlsx")))

    if edgar_feed_list == "XBRL_XLSX":
        edgar_feed_list = "XBRL_XLSX"
        ext='.xlsx'
        files = glob.glob(os.path.join(CONFIG.SEC_MONTHLY_DIR,"*{}".format(ext)))
        tablename = 'EDGAR_XBRLRSS_XML_ENTRIES'
        #OUTPUT_FILENAME = os.path.join(SEC_MONTHLY_DIR,os.path.basename(source_file.replace(ext, ".xlsx")))
        # DIR,os.path.basename(source_file.replace(ext, ".xlsx")))

    elif edgar_feed_list == "IDX":
        edgar_feed_list = "IDX"
        ext = ".idx"
        #files = glob.glob(os.path.join(SEC_FULL_INDEX_DIR,"*{}".format('.idx')))
        # df["BASENAME"] = df["FILENAME"].apply(lambda x: os.path.basename(x).split(".")[0])

        master_files = walk_dir_fullpath(CONFIG.SEC_FULL_INDEX_DIR,contains="master.idx")
        files.sort(reverse=True)
        files = [file for file in files if "old" not in file]
        # years = [year for year in range(1994, 2018)]
        # files = [filepath for filepath in files if any(str(year) in filepath for year in years)]
        edgar_feed_list = "IDX"
        #OUTPUT_FILENAME = os.path.join(SEC_FULL_INDEX_DIR,os.path.basename(source_file.replace(ext, ".xlsx")))
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

# https://www.sec.gov/Archives/edgar/daily-index/2017/QTR3/
#/Archives/edgar/daily-index — daily index files through the current year;

def main():
    from_year = 2016
    to_year = 2017
    XBRLLocation = "local"
    UpdateXBRLurls = False

    if XBRLLocation == "local":
        print("Globbing XBRL files in folder: " + CONFIG.XBRLfolder)
        xbrlfiles = glob.glob(os.path.join(CONFIG.SEC_XBRL_DIR,"*"))
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

if __name__ == "__main__":
    g = Gotem()
    g.GET_URLS(edgar_monthly_url)
