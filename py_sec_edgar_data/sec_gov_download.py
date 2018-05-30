# view-source:https://www.sec.gov/Archives/edgar/xbrl-rr.rss.xml
# https://www.sec.gov/Archives/edgar/usgaap.rss.xml
# https://www.sec.gov/Archives/edgar/xbrl-inline.rss.xml
# https://www.sec.gov/Archives/edgar/usgaap.rss.xml
# http://www.sec.gov/Archives/edgar/xbrlrss.all.xml
# https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&CIK=&type=10-K&company=&dateb=&owner=include&start=0&count=100&output=atom

import sys
sys.path.append('..')
from edgar_config import SEC_GOV_TXT_DIR,CONFIG_DIR, SEC_GOV_FULL_INDEX_DIR,SEC_GOV_OUTPUT_DIR, SEC_GOV_MONTHLY_DIR

import pandas as pd
import glob
import edgar_config
import os
import feedparser
from datetime import datetime
from edgar_utilities import gotem
from dateparser import parse
from edgar_utilities.flatten_edgar_xbrl_items import flattenDict

# input_filepath = r'S:\Archives\edgar\data\2014\QTR3\0001047469-14-006723.txt'
import pandas as pd
desired_width = 600
pd.set_option('display.width', desired_width)

from edgar_utilities.files_and_folders import walk_dir_fullfilename


def read_xml_feedparser(source_file):
    if source_file[0:4] == 'http':
        feed = feedparser.parse(source_file)
    elif source_file.endswith(".xml"):
        with open(source_file) as f:
            feedData = f.read()
        feed = feedparser.parse(feedData)
    else:
        feed = feedparser.parse(filepath)
    return feed

from edgar_config import SEC_GOV_TXT_DIR,CONFIG_DIR, SEC_GOV_FULL_INDEX_DIR,SEC_GOV_OUTPUT_DIR
#
# frame = pd.DataFrame()
# list_ = []
# for file_ in files_full_master[0:8]:
#     try:
#         df = pd.read_csv(file_, skiprows=10,
#                      names=['CIK', 'Company Name', 'Form Type', 'Date Filed', 'Filename'], sep='|',
#                      engine='python', parse_dates=True)
#         df['Source_Filename'] = file_
#         list_.append(df)
#     except:
#         print('Error Loading ' + file_)
#


def parse_master_idx():

    local_master_idx = os.path.join(SEC_GOV_FULL_INDEX_DIR, "master.idx")
    old_local_master_idx = '{}.old'.format(local_master_idx)

    if os.path.exists(local_master_idx):
        os.rename(local_master_idx, old_local_master_idx)
    else:
        with open(old_local_master_idx, 'w') as f:
            f.write(str())

    g = gotem.Gotem()
    g.GET_FILE(edgar_full_master, local_master_idx)
    g.GET_HTML(edgar_full_master, local_master_idx)
    df = pd.read_csv(local_master_idx, skiprows=10, names=['CIK', 'Company Name', 'Form Type', 'Date Filed', 'Filename'], sep='|', engine='python', parse_dates=True)
    df = df[-df['CIK'].str.contains("---")]
    df = df.sort_values('Date Filed', ascending=False)
    df['published'] = df['Date Filed'].apply(lambda x: datetime.combine(parse(x), parse("12:00:00").time()))
    df['link'] = df['Filename'].apply(lambda x: urljoin(edgar_Archives_url, x))
    df['edgar_ciknumber'] = df['CIK'].astype(str)
    df['edgar_companyname'] = df['Company Name']
    df['edgar_formtype'] = df['Form Type']
    df_master_with_tickers = pd.merge(df, df_tickers_cik, how='left', left_on=df.CIK, right_on=df_tickers_cik.EDGAR_CIKNUMBER)
    df_master_with_tickers = df_master_with_tickers.sort_values('Date Filed', ascending=False)
    df_master_with_tickers_10k = df_master_with_tickers[df_master_with_tickers['Form Type'].isin(['10-K'])]

    feed_items = df_master_with_tickers_10k.to_dict(orient='index')
    # item = list(feed_items.items())[0]
    for item in feed_items.items():

        feed_item = item[1]
        folder_path_cik = os.path.join(SEC_GOV_TXT_DIR ,'{}/QTR{}'.format(feed_item['published'].year, feed_item['published'].quarter))
        folder_path_cik_other = os.path.join(SEC_GOV_TXT_DIR, 'cik', feed_item['edgar_ciknumber'])

        if not os.path.exists(folder_path_cik):
            os.makedirs(folder_path_cik)

        filepath_cik = os.path.join(folder_path_cik, os.path.basename(feed_item['Filename']))

        if not os.path.exists(filepath_cik) and not os.path.exists(folder_path_cik_other):
            consume_complete_submission_filing_txt.delay(feed_item, filepath_cik)
        else:
            print("Filepath Already exists {}".format(filepath_cik))

            parse_and_download_quarterly_idx_file(edgar_full_master, local_master_idx)


def determine_if_sec_edgar_feed_and_local_files_differ(url, local_filepath):

    temp_filepath = os.path.join(os.path.dirname(local_filepath), "temp_{}".format(os.path.basename(local_filepath)))
    g = gotem.Gotem()
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

def load_headers_files():
    headers_combined = r'E:\DATA\headers.xlsx'
    df_headers_combined = pd.read_excel(headers_combined, header=0, index_col=0, parse_dates=True)

def generate_list_of_local_filings():
    files_master = walk_dir_fullfilename(SEC_GOV_TXT_DIR,contains='.txt')
    files_master = [filepath for filepath in files_master if "edgar" not in os.path.basename(filepath)]
    files_master_basename = [os.path.basename(filepath).split(".")[0] for filepath in files_master if "edgar" not in os.path.basename(filepath)]
    files_master.sort(reverse=True)
    # source_file = files[0]
    # source_file = files[5]


def main(edgare_feed_list="IDX"):

    if edgar_feed_list == "XBRL_XML":
        ext='.xml'
        files = glob.glob(os.path.join(SEC_GOV_MONTHLY_DIR,"*{}".format('.xml')))
        tablename = 'EDGAR_XBRLRSS_XML_ENTRIES'
        #OUTPUT_FILENAME = os.path.join(SEC_GOV_MONTHLY_DIR,os.path.basename(source_file.replace(ext, ".xlsx")))

    if edgar_feed_list == "XBRL_XLSX":
        edgar_feed_list = "XBRL_XLSX"
        ext='.xlsx'
        files = glob.glob(os.path.join(SEC_GOV_MONTHLY_DIR,"*{}".format(ext)))
        tablename = 'EDGAR_XBRLRSS_XML_ENTRIES'
        #OUTPUT_FILENAME = os.path.join(SEC_GOV_MONTHLY_DIR,os.path.basename(source_file.replace(ext, ".xlsx")))
        # DIR,os.path.basename(source_file.replace(ext, ".xlsx")))

    elif edgar_feed_list == "IDX":
        edgar_feed_list = "IDX"
        ext = ".idx"
        #files = glob.glob(os.path.join(SEC_GOV_FULL_INDEX_DIR,"*{}".format('.idx')))
        # df["BASENAME"] = df["FILENAME"].apply(lambda x: os.path.basename(x).split(".")[0])

        master_files = walk_dir_fullfilename(SEC_GOV_FULL_INDEX_DIR,contains="master.idx")
        files.sort(reverse=True)
        files = [file for file in files if "old" not in file]
        # years = [year for year in range(1994, 2018)]
        # files = [filepath for filepath in files if any(str(year) in filepath for year in years)]
        edgar_feed_list = "IDX"
        #OUTPUT_FILENAME = os.path.join(SEC_GOV_FULL_INDEX_DIR,os.path.basename(source_file.replace(ext, ".xlsx")))
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


if __name__ == '__main__':

    import argparse
    parser = argparse.ArgumentParser(description='SEC DATA Extract Header from Filing')
    parser.add_argument('--input_filepath', help='Input the Year(s) or ALL', action='append', nargs='*')
    parser.add_argument('--ticker', help='Input the Ticker(s) or ALL keyword', action='append', nargs='*')

    if len(sys.argv[1:]) >= 1:
        args = parser.parse_args()
        extract_header_from_filing(input_filepath=args.input_filepath[0], ticker=args.ticker[0])
    else:
        sys.exit(parser.print_help())
