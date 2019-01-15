# -*- coding: utf-8 -*-

import sys
import io
import chardet
import os
from html import unescape
import lxml.html
from bs4 import BeautifulSoup
import pandas as pd
from collections import defaultdict

from utilities import file_size
from settings import CONFIG
from utilities import format_filename
from utilities import uudecode

import re
re10k = re.compile('10-K')
regex_no_rfiles = re.compile(r'R.+\.htm')


def parse_filing_header(raw_html):
    """parses the heading of an SEC Edgar filing"""

    lxml_html = lxml.html.fromstring(raw_html)

    root = lxml_html.getroottree()
    data = defaultdict(dict)
    valuename = ""

    # sec_header_element = root.xpath("//*/sec-header")[0]
    for sec_header_element in root.xpath("//*/sec-header"):
        soup = BeautifulSoup(lxml.html.tostring(sec_header_element), 'lxml')
        sec_header = re.findall(
            r'<(SEC-HEADER|sec-header)>(.*?)</(SEC-HEADER|sec-header)>', soup.prettify(), re.DOTALL)[0][1]
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
                        data[i] = ["", "", headerItem.split(":")[0].split(
                            "\t")[0], unescape(headerItem.split(":")[1].lstrip())]
                    elif headerItem != "" and headerItem != valuename and "<" not in headerItem:
                        data[i] = headerItem.split(":")[0].split(
                            "\t") + [unescape(headerItem.split(":")[1].lstrip())]
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
    try:
        print(header_dict)
    except UnicodeEncodeError:
        pass
    return header_dict

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
            print("\t DOC ", i, " ", document['DESCRIPTION'], " Elements = ",
                  document['NUMBER_OF_ELEMENTS'], 'size: ', document['FILE_SIZE'])

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
                i, document = list(sec_filing_documents.items())[
                    size_seq_no - 1]
            else:
                i, document = list(sec_filing_documents.items())[f10_k - 1]
    else:
        i, document = list(sec_filing_documents.items())[seq_no - 1]
    print("Parsing DOC {}".format(i))
    return i, document

def parse_10_K_filing(input_filepath):

    # input_filepath = filing[0]

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


def complete_submission_filing(input_filepath=None, output_directory=None, file_ext=None, extraction_override=False):
    FOLDER_PATH = True
    elements_list = [('FILENAME', './/filename'), ('TYPE', './/type'),
                     ('SEQUENCE', './/sequence'), ('DESCRIPTION', './/description')]

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
        xbrl_text = re.compile(
            r'<(TEXT|text)>(.*?)</(TEXT|text)>', re.MULTILINE | re.DOTALL)

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

        if not FOLDER_PATH:
            CIK_KEY = sec_filing_header[sec_filing_header['KEY'].isin(
                ['CENTRAL INDEX KEY'])]['VALUE']
            cik_folder_path = os.path.join(
                output_directory, CIK_KEY.tolist()[0].lstrip("0"))
            output_directory = os.path.join(cik_folder_path, os.path.basename(
                input_filepath.replace(".txt", "").replace("-", "")))

        headers_path = os.path.dirname(input_filepath)

        if not os.path.exists(headers_path):
            os.makedirs(headers_path)

        header_filepath = os.path.join(headers_path, "{}_FILING_HEADER.csv".format(
            os.path.basename(output_directory)))

        sec_filing_header.to_csv(header_filepath)

        documents = xbrl_doc.findall(raw_text)

        sec_filing_documents = {}
        debug_sec_filing_documents = {}

        for i, document in enumerate(documents, start=1):
            uue_file = False
            file_metadata = {}

            lxml_html = lxml.html.fromstring(document)
            root = lxml_html.getroottree()

            # (key, value) = elements_list[0]
            for (key, value) in elements_list:
                try:
                    file_metadata["{}".format(key)] = root.xpath(
                        "{}".format(value))[0].text.strip()
                except:
                    file_metadata["{}".format(key)] = ""

            debug_sec_filing_documents[i] = file_metadata

            raw_text = xbrl_text.findall(document)
            raw_text = raw_text[0][1].replace(
                "<XBRL>", "").replace("</XBRL>", "").strip()
            raw_text = raw_text.replace(
                "<XML>", "").replace("</XML>", "").strip()

            if raw_text.lower().startswith("begin"):

                # output_filepath = format_filename(file_metadata['FILENAME'].replace(" ", "_").replace(":", ""))

                output_document = os.path.join(
                    output_directory, file_metadata['FILENAME'] + ".uue")
                with open(output_document, 'w', encoding=charenc) as f:
                    f.write(raw_text)

                uudecode(output_document,
                         out_file=output_document.replace(".uue", ""))

                uue_file = True

            elif document.lower().startswith("begin"):

                output_document = os.path.join(
                    output_directory, file_metadata['FILENAME'] + ".uue")

                with open(output_document, 'w', encoding=charenc) as f:
                    f.write(raw_text)

                uudecode(output_document,
                         out_file=output_document.replace(".uue", ""))

                os.remove(output_document)
                uue_file = True

            else:

                try:

                    output_filepath = '{:04d}-({}) {} {}'.format(int(file_metadata['SEQUENCE']),
                                                                 file_metadata['TYPE'],
                                                                 file_metadata['DESCRIPTION'],
                                                                 file_metadata['FILENAME']
                                                                 ).replace(" ", "_").replace(":", "").replace("__", "_")

                    output_filepath = format_filename(output_filepath)
                    # print(output_filepath)
                    output_document = os.path.join(
                        output_directory, output_filepath)

                    with open(output_document, 'w', encoding=charenc) as f:
                        f.write(raw_text)
                except:

                    output_filepath = '{:04d}-({}) {}'.format(int(file_metadata['SEQUENCE']),
                                                                 file_metadata['TYPE'],
                                                                 file_metadata['FILENAME']).replace(" ", "_").replace(":", "").replace("__", "_")

                    output_filepath = format_filename(output_filepath)
                    # print(output_filepath)
                    output_document = os.path.join(
                        output_directory, output_filepath)

                    with open(output_document, 'w', encoding=charenc) as f:
                        f.write(raw_text)

            debug_sec_filing_documents[i]['OUTPUT_FILEPATH'] = output_document

            file_metadata['RELATIVE_FILEPATH'] = os.path.join(
                os.path.basename(output_directory), 'FILES', output_filepath)
            file_metadata['DESCRIPTIVE_FILEPATH'] = output_filepath

            file_metadata['FILE_SIZE'] = file_size(output_document)
            file_metadata['FILE_SIZE_BYTES'] = os.stat(output_document).st_size

            sec_filing_documents[i] = file_metadata

            if uue_file == True:
                os.remove(output_document)

        df_sec_filing_contents = pd.DataFrame.from_dict(
            sec_filing_documents, orient='index')
        df_sec_filing_contents.to_csv(os.path.join(
            output_directory, "{}_FILING_CONTENTS.csv".format(os.path.basename(output_directory))))
        return df_sec_filing_contents
    else:
        print("already extracted")
        return output_directory


if __name__ == '__main__':

    import argparse

    parser = argparse.ArgumentParser(
        description='SEC data Extract Header from Filing')
    parser.add_argument(
        '--input_filepath', help='Input the Year(s) or ALL', action='append', nargs='*')
    parser.add_argument(
        '--ticker', help='Input the Ticker(s) or ALL keyword', action='append', nargs='*')

    if len(sys.argv[1:]) >= 1:
        args = parser.parse_args()
        complete_submission_filing(input_filepath=None, output_directory=None, file_ext=None, extraction_override=False)
    else:
        sys.exit(parser.print_help())
