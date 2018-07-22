# -*- coding: utf-8 -*-

"""

Todo:
    * refactor into class

"""
import sys

sys.path.append('..')
import csv
import io
import re
from html import unescape
from pprint import pprint
import lxml.html
from bs4 import BeautifulSoup
from py_sec_edgar.settings import Config
CONFIG = Config()
from datetime import datetime

from py_sec_edgar.utilities import file_size

re10k = re.compile('10-K')
import pandas as pd

regex_no_rfiles = re.compile(r'R.+\.htm')
from collections import defaultdict
import chardet
import os
# input_filepath = r'C:\sec_gov\Archives\edgar\data\913778\000114420418035277\0001144204-18-035277.txt'
# input_filepath = r'\\HV-WS1202\sec_gov\Archives\edgar\data\2017\QTR3\0001564590-17-017693.txt'
# input_filepath = r'C:\SECDATA\sec_gov\Archives\edgar\filings\2017\QTR1\0000034088-17-000017.txt'
# input_filepath = r'C:\SECDATA\sec_gov\Archives\edgar\filings\2017\QTR1\0000039263-17-000017.txt'
# input_filepath = r'C:\SECDATA\sec_gov\Archives\edgar\filings\2017\QTR1\0000065984-17-000098.txt'
from py_sec_edgar.utilities import format_filename
from py_sec_edgar.utilities import uudecode

# from celery import Celery
# # subprocess.call(['chmod', '-R', '+w', some_folder])
#
# def write_filing_header_to_file(SEC_FILING_HEADER_FILEPATH, sec_filing_documents):
#     with open(SEC_FILING_HEADER_FILEPATH, "w", newline='') as fp:
#         wr = csv.writer(fp, dialect='excel')
#         wr.writerow(["ITEM", "KEY", "VALUE"])
#         for i, (colname, value) in enumerate(sec_filing_documents.items()):
#             if isinstance(value, list):
#                 value = ", ".join(value)
#             wr.writerow([i, colname, value])

def parse_filing_header(raw_html):
    """parses the heading of an SEC Edgar filing"""

    lxml_html = lxml.html.fromstring(raw_html)

    root = lxml_html.getroottree()
    data = defaultdict(dict)
    valuename = ""

    # sec_header_element = root.xpath("//*/sec-header")[0]
    for sec_header_element in root.xpath("//*/sec-header"):
        soup = BeautifulSoup(lxml.html.tostring(sec_header_element), 'lxml')
        sec_header = re.findall(r'<(SEC-HEADER|sec-header)>(.*?)</(SEC-HEADER|sec-header)>', soup.prettify(), re.DOTALL)[0][1]
        # i, headerItem = list(enumerate(sec_header.split('\n')))[5]
        split_header = sec_header.split('\n')
        for i, headerItem in enumerate(split_header):
            if len(headerItem) > 0:
                try:
                    if "<" in headerItem and ">" in headerItem:
                        keyname = headerItem
                        valuename = split_header[i + 1]
                        data[i] = ["", "", keyname.strip(), valuename]
                    elif not headerItem.startswith("\t") and headerItem != valuename and "<" not in headerItem:
                        data[i] = ["", "", headerItem.split(":")[0].split("\t")[0], unescape(headerItem.split(":")[1].lstrip())]
                    elif headerItem != "" and headerItem != valuename and "<" not in headerItem:
                        data[i] = headerItem.split(":")[0].split("\t") + [unescape(headerItem.split(":")[1].lstrip())]
                    else:
                        print(headerItem)
                except:
                    keyname = headerItem.strip()
                    valuename = headerItem.strip()
                    print("found problem")

    header_dict = pd.DataFrame.from_dict(dict(data), orient='index')
    header_dict = header_dict.replace('', pd.np.nan)
    header_dict[1] = header_dict[1].ffill().bfill().tolist()
    header_dict = header_dict.iloc[:, 1:]
    header_dict = header_dict.dropna()
    header_dict.columns = ['GROUP', 'KEY', 'VALUE']
    return header_dict

def extract_header_from_filing(input_filepath=None, header_output_filepath=None, ticker="--"):

    with io.open(input_filepath, "rb") as f:
        raw_html = f.read()

    # lxml is a fast html file parser c++
    # lxml_html = lxml.html.fromstring(raw_html)

    # root = lxml_html.getroottree()

    if header_output_filepath is None:
        header_output_filepath = os.path.dirname(input_filepath.replace(".txt", "-header.csv"))

    try:
        df_header = parse_filing_header(raw_html)

        df_header = df_header[['KEY', 'VALUE']].set_index('KEY')
        filename_items = ['FILED AS OF DATE', 'ACCESSION NUMBER', '<acceptance-datetime>', 'CENTRAL INDEX KEY', 'COMPANY CONFORMED NAME', 'CONFORMED SUBMISSION TYPE', 'CONFORMED PERIOD OF REPORT']
        header_dict = df_header[df_header.index.isin(filename_items)].reindex(filename_items).to_dict()['VALUE']

        edgfilename = str('edgaridx-' + header_dict['FILED AS OF DATE'][0:4] + "-" + header_dict['FILED AS OF DATE'][4:6] +
                          "_#2_" + header_dict['ACCESSION NUMBER'] +
                          "_#3_" + datetime.strptime(header_dict['<acceptance-datetime>'].strip(), "%Y%m%d%H%M%S").strftime("%Y-%m-%dTZ%H-%M-%S")
                          + "_#4_" + header_dict['CENTRAL INDEX KEY'].lstrip("0") +
                          "_#5_({})_".format(ticker) + header_dict['COMPANY CONFORMED NAME'].upper() +
                          "_#6_" + header_dict['CONFORMED SUBMISSION TYPE'] +
                          "_#7_" + header_dict['FILED AS OF DATE'])

        edgfilename = edgfilename.replace(" ", "_").replace(".", "_").replace(
            ",", "_").replace("/", "_").replace("__", "_").replace("/", "_").replace(" ", "_")

        sec_filing_output_directory = os.path.join(header_output_filepath, '{}.csv'.format(edgfilename))
        df_final = df_header.T
        df_final.index = [edgfilename]
        df_final.to_csv(sec_filing_output_directory)
        return edgfilename
    except:
        print("error {}".format(input_filepath))

def _parse_single_document():
    """extracts the meta-data from an individual document inside an SEC Edgar Filing"""
    root = lxml.html.fromstring(r.text)
    root = root.getroottree()
    sec_filing_docs = {}
    d_of_matches = {}
    re_matches = re.compile("-----BEGIN PRIVACY-ENHANCED MESSAGE-----")
    re_matches = re.compile('<(DOCUMENT|document)>(.*?)</(DOCUMENT|document)>', re.DOTALL)
    matches = re_matches.findall(lxml.html.tostring(root).decode())
    # i, match = list(enumerate(matches))[0]
    for i, match in enumerate(matches):
        d_of_matches[i] = match
        # print(match[0:1000])
        sequenceItem = re.findall('<SEQUENCE>.+', match)[0].replace("<SEQUENCE>", "")
        typeItem = re.findall('<TYPE>.+', matches[0])[0].replace("<TYPE>", "")
        filepathItem = re.findall('<filepath>.+', match)[0].replace("<filepath>", "")
        descriptionItem = re.findall('<DESCRIPTION>.+', match)[0].replace("<DESCRIPTION>", "")
        textItem = re.findall('<TEXT>.*', match, re.DOTALL + re.MULTILINE)[0].replace("<TEXT>", "").strip().split(":")
        sec_filing_docs[i] = {"TYPE": typeItem,
                              "SEQUENCE": sequenceItem,
                              "filepath": filepathItem,
                              "DESCRIPTION": descriptionItem,
                              "TEXT": textItem[1]}
    return sec_filing_docs


def identify_10_K_filing(sec_filing_documents, override=None):
    max_doc = 0
    seq_no = 1
    f10_k = 0
    num_10k = 0
    f10_size = 0
    max_doc_size = 0
    size_seq_no = 0
    file_metadata = []

    for i, document in sec_filing_documents.items():
        try:
            print("\t DOC ", i, " ", document['DESCRIPTION'], " Elements = ", document['NUMBER_OF_ELEMENTS'], 'size: ', document['FILE_SIZE'])

            search_desc = re10k.search(document['DESCRIPTION'])

            if document['FILE_SIZE_BYTES'] > max_doc_size:
                size_seq_no, max_doc_size = i, document['FILE_SIZE_BYTES']

            if search_desc:
                f10_k, num_10k = i, document['NUMBER_OF_ELEMENTS']
                f10_size = document['FILE_SIZE_BYTES']
            if i == 1:
                seq_no, max_doc = i, document['NUMBER_OF_ELEMENTS']
            else:
                if document['NUMBER_OF_ELEMENTS'] > max_doc:
                    seq_no, max_doc = i, document['NUMBER_OF_ELEMENTS']
        except:
            pass
    try:
        if override:
            print('override in effect... returning DOC #', seq_no - 1)
            seq_no = override
    except:
        pass

    if f10_k != seq_no != size_seq_no:

        if max_doc / (num_10k + 1) > 10 and max_doc_size < f10_size:
            i, document = list(sec_filing_documents.items())[seq_no - 1]
        else:
            # print(f"10-K found on {f10_k}")
            if max_doc_size > f10_size:
                i, document = list(sec_filing_documents.items())[size_seq_no - 1]
            else:
                i, document = list(sec_filing_documents.items())[f10_k - 1]
    else:
        i, document = list(sec_filing_documents.items())[seq_no - 1]
    print("Parsing DOC {}".format(i))
    return i, document

def parse_10k_html_document(input_filepath):
    lxml_dict = {}

    try:
        # or codecs.open on Python 2
        raw_text = open(input_filepath, "rb").read()
        result = chardet.detect(raw_text)
        charenc = result['encoding']
        raw_text = raw_text.decode(charenc)
    except:
        with io.open(input_filepath, "rb") as f:
            raw_text = f.read()

    lxml_html = lxml.html.fromstring(raw_text)
    root = lxml_html.getroottree()
    soup = BeautifulSoup(lxml.html.tostring(root), 'lxml')

    file_metadata = {}
    file_metadata['FILEPATH'] = input_filepath

    for ii, element in enumerate(root.xpath("//*/body/*")):
        lxml_dict[ii] = element

    div_check = {}
    for ii, element in enumerate(lxml.html.fromstring(soup.prettify()).xpath("//*/div/*")):
        div_check[ii] = element

    file_metadata['NUMBER_OF_ELEMENTS'] = len(lxml_dict)
    file_metadata['FILE_SIZE'] = file_size(file_metadata['FILEPATH'])
    file_metadata['FILE_SIZE_BYTES'] = os.stat(file_metadata['FILEPATH']).st_size
    file_metadata['lxml_dict'] = lxml_dict
    file_metadata['div_check'] = div_check
    file_metadata['ENCODING'] = charenc

    return file_metadata

def create_header_file_from_complete_submission_filing(root=None, input_filepath=None, output_directory=None):

    print("\nSplitting the Complete Submission Filing\n")
    filing_header = defaultdict(dict)
    if root.xpath("//*/sec-header"):
        filing_header['SEC-HEADER'] = parse_filing_header(root)
        filepath_dict = edgar_filename.split_edgarfilename(input_filepath)
        incremented_values = [{i: (key, val)} for i, (key, val) in enumerate(filepath_dict.items(), start=len(filing_header) + 1)]
        for item in incremented_values:
            filing_header['SEC-HEADER'].update(item)

        pprint(filing_header)

    SEC_FILING_HEADER_FILEPATH = os.path.join(output_directory, "SEC_FILING_HEADER_{}.CSV".format(os.path.basename(output_directory)))

    try:
        with open(SEC_FILING_HEADER_FILEPATH, "w", newline='') as fp:
            wr = csv.writer(fp, dialect='excel')
            wr.writerow(["ITEM", "KEY", "VALUE"])
            for i, (colname, value) in filing_header["SEC-HEADER"].items():
                if isinstance(value, list):
                    value = ", ".join(value)
                wr.writerow([i, colname, value])
    except KeyError:
        print("no header")

    return filing_header, SEC_FILING_HEADER_FILEPATH


def complete_submission_filing(input_filepath=None, output_directory=None, file_ext=None, extraction_override=False):

    FOLDER_PATH = True
    elements_list = [('FILENAME', './/filename'), ('TYPE', './/type'), ('SEQUENCE', './/sequence'), ('DESCRIPTION', './/description')]

    try:
        if not os.path.exists(output_directory):
            folder_exists = False
        else:
            folder_exists = True

    except:
        FOLDER_PATH = False
        folder_exists = False
        print("failed")

    if folder_exists == False or extraction_override == True:
        # print(output_directory)
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)

        print("extracting documents from {}".format(input_filepath))

        try:
            file_ext
        except:
            file_ext = ['.']

        xbrl_doc = re.compile(r'<DOCUMENT>(.*?)</DOCUMENT>', re.DOTALL)
        xbrl_text = re.compile(r'<(TEXT|text)>(.*?)</(TEXT|text)>', re.MULTILINE | re.DOTALL)

        try:
            # or codecs.open on Python 2
            raw_text = open(input_filepath, "rb").read()
            result = chardet.detect(raw_text)
            charenc = result['encoding']

            with io.open(input_filepath, "r", encoding=charenc) as f:
                raw_text = f.read()

        except:
            with io.open(input_filepath, "rb") as f:
                raw_text = f.read()

        sec_filing_header = parse_filing_header(raw_text)

        if FOLDER_PATH == False:
            CIK_KEY = sec_filing_header[sec_filing_header['KEY'].isin(['CENTRAL INDEX KEY'])]['VALUE']
            cik_folder_path = os.path.join(output_directory, CIK_KEY.tolist()[0].lstrip("0"))
            output_directory = os.path.join(cik_folder_path, os.path.basename(input_filepath.replace(".txt", "").replace("-", "")))

        headers_path = os.path.dirname(input_filepath)

        if not os.path.exists(headers_path):
            os.makedirs(headers_path)

        header_filepath = os.path.join(headers_path, "{}_FILING_HEADER.csv".format(os.path.basename(output_directory)))

        sec_filing_header.to_csv(header_filepath)

        documents = xbrl_doc.findall(raw_text)

        sec_filing_documents = {}
        debug_sec_filing_documents = {}

        # i, document = list(enumerate(documents, start=1))[1]
        for i, document in enumerate(documents, start=1):
            uue_file = False
            file_metadata = {}

            lxml_html = lxml.html.fromstring(document)
            root = lxml_html.getroottree()

            # (key, value) = elements_list[0]
            for (key, value) in elements_list:
                try:
                    file_metadata["{}".format(key)] = root.xpath("{}".format(value))[0].text.strip()
                except:
                    file_metadata["{}".format(key)] = ""

            debug_sec_filing_documents[i] = file_metadata

            raw_text = xbrl_text.findall(document)
            raw_text = raw_text[0][1].replace("<XBRL>", "").replace("</XBRL>", "").strip()
            raw_text = raw_text.replace("<XML>", "").replace("</XML>", "").strip()

            if raw_text.lower().startswith("begin"):

                # output_filepath = format_filename(file_metadata['FILENAME'].replace(" ", "_").replace(":", ""))

                output_document = os.path.join(output_directory, file_metadata['FILENAME'] + ".uue")
                with open(output_document, 'w', encoding=charenc) as f:
                    f.write(raw_text)

                uudecode(output_document, out_file=output_document.replace(".uue", ""))

                uue_file = True

            elif document.lower().startswith("begin"):

                # output_filepath = format_filename(file_metadata['FILENAME'].replace(" ", "_").replace(":", ""))
                output_document = os.path.join(output_directory, file_metadata['FILENAME'] + ".uue")

                with open(output_document, 'w', encoding=charenc) as f:
                    f.write(raw_text)

                uudecode(output_document, out_file=output_document.replace(".uue", ""))

                os.remove(output_document)
                uue_file = True

            else:
                # print(file_metadata)
                # print(output_directory)
                output_filepath = '{:04d}-({}) {} {}'.format(int(file_metadata['SEQUENCE']), file_metadata['TYPE'], file_metadata['DESCRIPTION'], file_metadata['FILENAME']).replace(" ", "_").replace(":", "").replace(
                    "__", "_")

                output_filepath = format_filename(output_filepath)
                # print(output_filepath)
                output_document = os.path.join(output_directory, output_filepath)

                with open(output_document, 'w', encoding=charenc) as f:
                    f.write(raw_text)

            debug_sec_filing_documents[i]['OUTPUT_FILEPATH'] = output_document

            file_metadata['RELATIVE_FILEPATH'] = os.path.join(os.path.basename(output_directory), 'FILES', output_filepath)
            file_metadata['DESCRIPTIVE_FILEPATH'] = output_filepath

            file_metadata['FILE_SIZE'] = file_size(output_document)
            file_metadata['FILE_SIZE_BYTES'] = os.stat(output_document).st_size

            sec_filing_documents[i] = file_metadata

            if uue_file == True:
                os.remove(output_document)

        df_sec_filing_contents = pd.DataFrame.from_dict(sec_filing_documents, orient='index')
        df_sec_filing_contents.to_csv(os.path.join(output_directory, "{}_FILING_CONTENTS.csv".format(os.path.basename(output_directory))))
        return df_sec_filing_contents
    else:
        print("already extracted")
        return output_directory


# https://www.sec.gov/Archives/edgar/daily-index/2017/QTR3/
#/Archives/edgar/daily-index — daily index files through the current year;


if __name__ == '__main__':

    import argparse
    parser = argparse.ArgumentParser(description='SEC data Extract Header from Filing')
    parser.add_argument('--input_filepath', help='Input the Year(s) or ALL', action='append', nargs='*')
    parser.add_argument('--ticker', help='Input the Ticker(s) or ALL keyword', action='append', nargs='*')

    if len(sys.argv[1:]) >= 1:
        args = parser.parse_args()
        extract_header_from_filing(input_filepath=args.input_filepath[0])
    else:
        sys.exit(parser.print_help())
