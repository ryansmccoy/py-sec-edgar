import feedparser
import os
import glob
from datetime import datetime
from urllib.parse import urljoin
from py_sec_edgar_data.settings import Config
from py_sec_edgar_data.utilities import walk_dir_fullpath, Gotem
from datetime import datetime, date
from datetime import timedelta
import sqlite3
CONFIG = Config()
import pandas as pd

from py_sec_edgar_data.utilities import walk_dir_fullpath

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

        master_files = walk_dir_fullfilename(CONFIG.SEC_FULL_INDEX_DIR,contains="master.idx")
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
