import os
from pprint import pprint
import glob
import filing as edgar_filing
try:
    import transformer as edgar_transformer
except:
    print('Transformer Not Found')
    
from settings import CONFIG
from proxy import ProxyRequest
import lxml.html
from bs4 import BeautifulSoup
import pandas as pd
from utilities import zip_folder
# from sqlalchemy import create_engine
# idx_engine = create_engine('sqlite:///merged_idx_files.db')
# df_idx.to_sql('idx', idx_engine, if_exists='append')
# df = pd.read_sql_query('SELECT * FROM idx LIMIT 3',idx_engine)

def broker(feed_item, extract_filing=True, extract_tables=False, zip_folder_contents=True):

    # extract_items = ['TABLES', 'EXCEL_TABLE']
    # feed_item['url'] = r'https://www.sec.gov/Archives/edgar/data/732717/0000732717-18-000076.txt'
    #zip_folder_contents = True
    extract_items = []

    pprint(feed_item.to_dict())

    feed_item = dict(feed_item)

    folder_dir = os.path.basename(feed_item['Filename']).split('.')[0].replace("-", "")

    folder_path_cik = CONFIG.TXT_FILING_DIR.replace(
        "CIK", str(feed_item['CIK'])).replace("FOLDER", folder_dir)

    filepath_feed_item = os.path.join(
        folder_path_cik, os.path.basename(feed_item['Filename']))

    if not os.path.exists(folder_path_cik) and not os.path.exists(folder_path_cik + ".zip"):

        if not os.path.exists(folder_path_cik):
            os.makedirs(folder_path_cik)

        g = ProxyRequest()

        g.GET_FILE(feed_item['url'], filepath_feed_item)

        # todo: celery version of download full
        # consume_complete_submission_filing_txt.delay(feed_item, filepath_cik)

    else:
        print("Filepath Already exists\n\t {}".format(filepath_feed_item))
        # parse_and_download_quarterly_idx_file(CONFIG.edgar_full_master, local_master_idx)

    filing_contents = filepath_feed_item.replace(
        ".txt", "_FILING_CONTENTS.csv").replace("-", "")

    if os.path.exists(folder_path_cik) and extract_filing and not os.path.exists(folder_path_cik + ".zip"):

        print("\n\tExtracting Filing Documents:\n")
        try:
            contents = edgar_filing.complete_submission_filing(input_filepath=filepath_feed_item, output_directory=folder_path_cik, extraction_override=True)
            print(contents)
        except UnicodeDecodeError:
            print("Error Decoding")

        # todo: celery version of download full
        # consume_complete_submission_filing_txt.delay(feed_item, filepath_cik)
        print("\n\tExtraction Complete\n")


    if extract_tables and not os.path.exists(folder_path_cik + ".zip"):

        filing_tables_path = os.path.join(folder_path_cik, 'TABLES')

        if not os.path.exists(filing_tables_path):
            os.makedirs(filing_tables_path)

        print("\n\tExtracting Filing Tables:\n")

        filing = glob.glob(os.path.join(folder_path_cik,"*(10-K)*.*"))

        header_file = glob.glob(os.path.join(folder_path_cik, "*HEADER*.*"))[0]

        df_header = pd.read_csv(header_file, index_col=0, header=0)
        df_header = df_header[['KEY', 'VALUE']].set_index('KEY')

        if len(filing) == 1:

            document  = edgar_filing.parse_10_K_filing(filing[0])

        # pprint(document)

        for element_number, element in document['lxml_dict'].items():

            if element.iter(tag="table"):

                # table_number, lxml_table_element = list(enumerate(element.iter(tag="table")))[0]
                for table_number, lxml_table_element in enumerate(element.iter(tag="table")):

                    if any(x == 'TABLES' for x in extract_items):

                        soup = BeautifulSoup(lxml.html.tostring(lxml_table_element), 'lxml')

                        export_filepath_html = os.path.join(filing_tables_path, "{:04d}-{}-TABLE.html".format(element_number, table_number))

                    if any(x == 'EXCEL_TABLE' for x in extract_items):

                        export_excel_filepath = os.path.join(filing_tables_path, "{:04d}-{}-TABLE.xlsx".format(element_number, table_number))

                        df_final = edgar_transformer.transform_html_table(soup.prettify(), export_filepath_html, df_header)

                        # if any(x == "HTML_TABLE" for x in list_of_what_to_extract):
                        if df_final is not None:

                            with open(export_filepath_html, 'w', encoding='utf-16') as f:
                                f.write(soup.prettify())

                            df_final.to_excel(export_excel_filepath, encoding='utf-16')
                            try:
                                print("\n\nTable {})\n".format(element_number))
                                print("\n\nFilepath:\t{})\n".format(export_excel_filepath))
                                print(df_final.to_string())
                            except:
                                print("Encoding Error, Can't Print Table!")

        # print(contents)
        # todo: celery version of download full
        # consume_complete_submission_filing_txt.delay(feed_item, filepath_cik)

    if os.path.exists(folder_path_cik) and zip_folder_contents:

        zip_folder(folder_path_cik, folder_path_cik + ".zip")

    print("\n\tExtraction Complete\n")
