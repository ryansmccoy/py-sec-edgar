# -*- coding: utf-8 -*-

import io
import logging
import os
import sys
from collections import defaultdict
from html import unescape
from urllib.parse import urljoin

import chardet
import lxml.html
import pandas as pd
from bs4 import BeautifulSoup

from py_sec_edgar import CONFIG
from py_sec_edgar.proxy import ProxyRequest
from py_sec_edgar.utilities import file_size
from py_sec_edgar.utilities import format_filename
from py_sec_edgar.utilities import uudecode
import os
import logging

logger = logging.getLogger(__name__)

from py_sec_edgar.proxy import ProxyRequest
import zipfile

logger = logging.getLogger(__name__)
import re

re10k = re.compile('10-K')
regex_no_rfiles = re.compile(r'R.+\.htm')

prop = ['filing_url', 'filing_folder', 'cik_directory', 'filing_filepath', 'filing_zip_filepath', 'extracted_filing_directory', 'filing_basename', 'header_directory', 'header_filepath', 'is_downloaded', 'is_loaded',
        'is_parsed_header', 'is_processed']


class SecEdgar:

    def __init__(self, filing, download=False, load=False, parse_header=False, process_filing=False):
        self.is_processed = False
        self.is_parsed_header = False
        self.is_loaded = False
        self.is_downloaded = False
        self.sec_filing = filing
        self.is_lxml_root = False
        self.filing_text = None
        self.lxml_root = None

        feed_item = dict(filing)

        self.filing_url = urljoin(CONFIG.edgar_Archives_url, feed_item['Filename'])
        self.filing_folder = os.path.basename(feed_item['Filename']).split('.')[0].replace("-", "")
        self.cik_directory = CONFIG.TXT_FILING_DIR.replace("CIK", str(feed_item['CIK'])).replace("FOLDER", "")
        self.filing_filepath = os.path.join(self.cik_directory, os.path.basename(feed_item['Filename']))
        self.filing_zip_filepath = os.path.join(self.cik_directory, os.path.basename(feed_item['Filename']).replace('.txt', '.zip'))
        self.extracted_filing_directory = CONFIG.TXT_FILING_DIR.replace("CIK", str(feed_item['CIK'])).replace("FOLDER", self.filing_folder)
        self.filing_basename = os.path.basename(self.filing_filepath)

        self.header_directory = self.extracted_filing_directory
        self.header_filepath = os.path.join(self.header_directory, f"{self.filing_basename.replace('.txt', '')}_FILING_HEADER.csv")
        self.check_if_exists(self.header_directory)

        if download == True:
            self.download()

        if load == True:
            self.load()

        if parse_header == True:
            self.parse_header()

        if process_filing == True:
            self.process_filing()

    def check_if_exists(self, path):

        if not os.path.exists(path):
            os.makedirs(path)

    def load(self):

        self._load(filing_filepath=self.filing_filepath)

    def _load(self, filing_filepath=None, lxml_root=True, file_stats=True):

        if self.is_loaded:
            return

        if not filing_filepath:
            filing_filepath = self.filing_filepath

        try:
            # or codecs.open on Python 2
            filing_text = open(filing_filepath, "rb").read()
            result = chardet.detect(filing_text)

            if result:
                self.charenc = result['encoding']

            with io.open(filing_filepath, "r", encoding=self.charenc) as f:
                self.filing_text = f.read()

            self.is_loaded = True
            logger.info(f"Filing Loaded")

        except:
            with io.open(filing_filepath, "rb") as f:
                self.filing_text = f.read()

        if lxml_root:
            lxml_html = lxml.html.fromstring(self.filing_text)
            self.lxml_root = lxml_html.getroottree()
            self.is_lxml_root = True
            logger.info(f"Filing Lxml")

        if file_stats:
            self.FILE_SIZE = file_size(self.filing_filepath)
            self.FILE_SIZE_BYTES = os.stat(self.filing_filepath).st_size
            self.ENCODING = self.charenc

    def download(self):
        self._download(filing_url=self.filing_url, filing_filepath=self.filing_filepath, overwrite_if_exists=True)

    def _download(self, filing_url=None, filing_filepath=None, overwrite_if_exists=False):
        try:

            if not filing_url:
                filing_url = self.filing_url
                print(filing_url)

            if not filing_filepath:
                filing_filepath = self.filing_filepath
                print(filing_filepath)

            if not os.path.exists(filing_filepath) and overwrite_if_exists == True:

                r = ProxyRequest()

                r.GET_FILE(filing_url, filing_filepath)

                self.is_downloaded = True
                logger.info(f"Filing Downloaded")

                # todo: celery version of download full
                # consume_complete_submission_filing_txt.delay(feed_item, filepath_cik)
            elif os.path.exists(filing_filepath):
                logger.error(f"Filing Already Exists")
                self.is_downloaded = True

        except Exception as e:
            logger.error(f"Couldn't Download File \n\t{e}")

    def parse_header(self, save_output=False):

        raw_html = self.filing_text

        self._parse_header(raw_html, save_output=save_output)

    def _parse_header(self, raw_html, save_output=False):
        """parses the heading of an SEC Edgar filing"""

        if not raw_html:
            self.load()

        lxml_html = lxml.html.fromstring(raw_html)

        root = lxml_html.getroottree()
        data = defaultdict(dict)
        valuename = ""

        for sec_header_element in root.xpath("//*/sec-header"):
            soup = BeautifulSoup(lxml.html.tostring(sec_header_element), 'lxml')
            sec_header = re.findall(
                r'<(SEC-HEADER|sec-header)>(.*?)</(SEC-HEADER|sec-header)>', soup.prettify(), re.DOTALL)[0][1]

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
                            data[i] = headerItem.split(":")[0].split(
                                "\t") + [unescape(headerItem.split(":")[1].lstrip())]
                        else:
                            print(headerItem)
                    except:
                        keyname = headerItem.strip()
                        valuename = headerItem.strip()
                        print("found problem")

        df_header = pd.DataFrame.from_dict(dict(data), orient='index')
        df_header = df_header.replace('', pd.np.nan)
        df_header[1] = df_header[1].ffill().bfill().tolist()
        df_header = df_header.iloc[:, 1:]
        df_header = df_header.dropna()
        df_header.columns = ['GROUP', 'KEY', 'VALUE']
        print(df_header)

        if save_output == True:
            df_header.to_csv(self.header_filepath)

        self.df_header = df_header
        self.is_parsed_header = True

    def process_filing(self, save_output=False):

        if os.path.exists(self.cik_directory) and not os.path.exists(self.cik_directory + ".zip"):
            try:
                logger.info("\n\n\n\n\tExtracting Filing Documents:\n")

                self._process_filing(self.filing_text, save_output=save_output)

                logger.info("\n\n\n\n\tExtraction Completed\n")

            except UnicodeDecodeError as E:
                logger.error(f"\n\n\n\nError Decoding \n\n{E}")

    def _process_filing(self, raw_text, save_output=False):
        """
        Given a filepath
        :param filepath:
        :param output_directory:
        :return:
        """

        elements_list = [('FILENAME', './/filename'), ('TYPE', './/type'),
                         ('SEQUENCE', './/sequence'), ('DESCRIPTION', './/description')]

        xbrl_doc = re.compile(r'<DOCUMENT>(.*?)</DOCUMENT>', re.DOTALL)
        xbrl_text = re.compile(r'<(TEXT|text)>(.*?)</(TEXT|text)>', re.MULTILINE | re.DOTALL)

        documents = xbrl_doc.findall(raw_text)

        filing_documents = {}

        for i, document in enumerate(documents, start=1):
            uue_filepath = None
            filing_document = {}

            lxml_html = lxml.html.fromstring(document)
            root = lxml_html.getroottree()

            for (element, element_path) in elements_list:
                try:
                    filing_document[f"{element}"] = root.xpath(f"{element_path}")[0].text.strip()
                except:
                    filing_document[f"{element}"] = ""

            raw_text = xbrl_text.findall(document)
            raw_text = raw_text[0][1].replace("<XBRL>", "").replace("</XBRL>", "").strip()
            raw_text = raw_text.replace("<XML>", "").replace("</XML>", "").strip()

            if raw_text.lower().startswith("begin") or document.lower().startswith("begin"):

                uue_filepath = os.path.join(self.filing_folder, filing_document['FILENAME'] + ".uue")
                output_filepath = os.path.join(self.filing_folder, uue_filepath.replace(".uue", ""))
                output_filename = os.path.basename(output_filepath)

                if save_output:
                    with open(uue_filepath, 'w', encoding=self.charenc) as f:
                        f.write(raw_text)

                    uudecode(uue_filepath, out_file=output_filepath)

            else:
                doc_num = f"{int(filing_document['SEQUENCE'])}".zfill(4)

                try:
                    output_filename = f"{doc_num}-({filing_document['TYPE']}) {filing_document['DESCRIPTION']} {filing_document['FILENAME']}"
                except:
                    output_filename = f"{doc_num}-({filing_document['TYPE']}) {filing_document['FILENAME']}".replace(" ", "_").replace(":", "").replace("__", "_")

                output_filename = output_filename.replace(" ", "_").replace(":", "").replace("__", "_")

                output_filename = format_filename(output_filename)
                output_filepath = os.path.join(self.filing_folder, output_filename)

                if save_output:
                    with open(output_filepath, 'w', encoding=self.charenc) as f:
                        f.write(raw_text)

            filing_document['RELATIVE_FILEPATH'] = os.path.join(os.path.basename(self.filing_folder), output_filepath)
            filing_document['DESCRIPTIVE_FILEPATH'] = output_filename

            if save_output:
                filing_document['FILE_SIZE'] = file_size(output_filepath)
                filing_document['FILE_SIZE_BYTES'] = os.stat(output_filepath).st_size

            filing_documents[i] = filing_document

            if uue_filepath and os.path.exists(uue_filepath):
                os.remove(uue_filepath)

        df_sec_filing_contents = pd.DataFrame.from_dict(filing_documents, orient='index')

        if save_output:
            df_sec_filing_contents.to_csv(os.path.join(self.filing_folder, f"{os.path.basename(self.filing_folder)}_FILING_CONTENTS.csv"))

        logger.info(df_sec_filing_contents)
        self.is_processed = True
        self.df_sec_filing_contents = df_sec_filing_contents

    def parse_filing(self, raw_text=None):
        """
        Parses html file
        :param sec_filing['filepath']: html file
        :return: dictionary of file_contents including lxml_dict
        """
        lxml_dict = {}

        lxml_html = lxml.html.fromstring(raw_text)
        root = lxml_html.getroottree()
        soup = BeautifulSoup(lxml.html.tostring(root), 'lxml')

        document_data = {}

        document_data['FILEPATH'] = self.filing_filepath

        for ii, element in enumerate(root.xpath("//*/body/*")):
            lxml_dict[ii] = element

        div_check = {}

        for ii, element in enumerate(lxml.html.fromstring(soup.prettify()).xpath("//*/div/*")):
            div_check[ii] = element
        document_data['div_check'] = div_check
        document_data['NUMBER_OF_ELEMENTS'] = len(lxml_dict)

        return document_data

    def __str__(self):
        print(f'\nSEC Filing:\n')

        for k in prop:
            print(f'\t{k}: \t{getattr(self, k)}')

def parse_filing_header(raw_html):
    """parses the heading of an SEC Edgar filing"""

    lxml_html = lxml.html.fromstring(raw_html)

    root = lxml_html.getroottree()
    data = defaultdict(dict)
    valuename = ""

    for sec_header_element in root.xpath("//*/sec-header"):
        soup = BeautifulSoup(lxml.html.tostring(sec_header_element), 'lxml')
        sec_header = re.findall(
            r'<(SEC-HEADER|sec-header)>(.*?)</(SEC-HEADER|sec-header)>', soup.prettify(), re.DOTALL)[0][1]

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

def identify_filing(sec_filing_documents, override=None):
    max_doc = 0
    seq_no = 1
    f10_k = 0
    num_10k = 0
    f10_size = 0
    max_doc_size = 0
    size_seq_no = 0

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

def parse_filing(filepath):
    """
    Parses html file
    :param filepath: html file
    :return: dictionary of file_contents including lxml_dict
    """
    # complete_submission_filing_filepath = filing[0]

    lxml_dict = {}

    try:
        # or codecs.open on Python 2
        raw_text = open(filepath, "rb").read()
        result = chardet.detect(raw_text)
        charenc = result['encoding']
        raw_text = raw_text.decode(charenc)
    except:
        charenc = ""
        with io.open(filepath, "rb") as f:
            raw_text = f.read()

    lxml_html = lxml.html.fromstring(raw_text)
    root = lxml_html.getroottree()
    soup = BeautifulSoup(lxml.html.tostring(root), 'lxml')

    file_metadata = {}

    file_metadata['FILEPATH'] = filepath

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

def complete_submission_filing(filepath, output_directory=None):
    """
    Given a filepath
    :param filepath:
    :param output_directory:
    :return:
    """

    elements_list = [('FILENAME', './/filename'), ('TYPE', './/type'),
                     ('SEQUENCE', './/sequence'), ('DESCRIPTION', './/description')]

    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    else:
        logger.info(f"Folder Already Exists {output_directory}")

        return

    logger.info("extracting documents to {}".format(output_directory))

    xbrl_doc = re.compile(r'<DOCUMENT>(.*?)</DOCUMENT>', re.DOTALL)
    xbrl_text = re.compile(r'<(TEXT|text)>(.*?)</(TEXT|text)>', re.MULTILINE | re.DOTALL)

    try:
        # or codecs.open on Python 2
        raw_text = open(filepath, "rb").read()
        result = chardet.detect(raw_text)
        charenc = result['encoding']

        with io.open(filepath, "r", encoding=charenc) as f:
            raw_text = f.read()

    except:
        with io.open(filepath, "rb") as f:
            raw_text = f.read()

    sec_filing_header = parse_filing_header(raw_text)

    header_filepath = os.path.join(output_directory, f"{os.path.basename(output_directory)}_FILING_HEADER.csv")

    sec_filing_header.to_csv(header_filepath)

    documents = xbrl_doc.findall(raw_text)

    filing_documents = {}

    for i, document in enumerate(documents, start=1):
        uue_filepath = None
        filing_document = {}

        lxml_html = lxml.html.fromstring(document)
        root = lxml_html.getroottree()

        for (element, element_path) in elements_list:
            try:
                filing_document[f"{element}"] = root.xpath(f"{element_path}")[0].text.strip()
            except:
                filing_document[f"{element}"] = ""

        raw_text = xbrl_text.findall(document)
        raw_text = raw_text[0][1].replace("<XBRL>", "").replace("</XBRL>", "").strip()
        raw_text = raw_text.replace("<XML>", "").replace("</XML>", "").strip()

        if raw_text.lower().startswith("begin") or document.lower().startswith("begin"):

            uue_filepath = os.path.join(output_directory, filing_document['FILENAME'] + ".uue")
            output_filepath = os.path.join(output_directory, uue_filepath.replace(".uue", ""))
            output_filename = os.path.basename(output_filepath)

            with open(uue_filepath, 'w', encoding=charenc) as f:
                f.write(raw_text)

            uudecode(uue_filepath, out_file=output_filepath)

        else:
            doc_num = f"{int(filing_document['SEQUENCE'])}".zfill(4)

            try:
                output_filename = f"{doc_num}-({filing_document['TYPE']}) {filing_document['DESCRIPTION']} {filing_document['FILENAME']}"
            except:
                output_filename = f"{doc_num}-({filing_document['TYPE']}) {filing_document['FILENAME']}".replace(" ", "_").replace(":", "").replace("__", "_")

            output_filename = output_filename.replace(" ", "_").replace(":", "").replace("__", "_")

            output_filename = format_filename(output_filename)
            output_filepath = os.path.join(output_directory, output_filename)

            with open(output_filepath, 'w', encoding=charenc) as f:
                f.write(raw_text)

        filing_document['RELATIVE_FILEPATH'] = os.path.join(os.path.basename(output_directory), output_filepath)
        filing_document['DESCRIPTIVE_FILEPATH'] = output_filename

        filing_document['FILE_SIZE'] = file_size(output_filepath)
        filing_document['FILE_SIZE_BYTES'] = os.stat(output_filepath).st_size

        filing_documents[i] = filing_document

        if uue_filepath:
            os.remove(uue_filepath)

    df_sec_filing_contents = pd.DataFrame.from_dict(filing_documents, orient='index')
    df_sec_filing_contents.to_csv(os.path.join(output_directory, f"{os.path.basename(output_directory)}_FILING_CONTENTS.csv"))
    logger.info(df_sec_filing_contents)

    return df_sec_filing_contents

def extract_contents(feed_item):
    """
    Extracts the contents of a complete submission filing
    """

    if not os.path.exists(feed_item['extracted_filing_directory']) and not os.path.exists(feed_item['extracted_filing_directory'] + ".zip"):

        logger.info("\n\n\n\n\tExtracting Filing Documents:\n")

        try:
            contents = complete_submission_filing(feed_item['filing_filepath'], output_directory=feed_item['extracted_filing_directory'])
            logger.info(contents)
        except UnicodeDecodeError as E:
            logger.error(f"\n\n\n\nError Decoding \n\n{E}")

        logger.info("\n\n\n\n\tExtraction Complete\n")

def download_filing(feed_item, zip_filing=False):

    if not os.path.exists(feed_item['cik_directory']):

        os.makedirs(feed_item['cik_directory'])

    if not os.path.exists(feed_item['filing_filepath']):

        g = ProxyRequest()

        g.GET_FILE(feed_item['filing_url'], feed_item['filing_filepath'])

    elif os.path.exists(feed_item['filing_filepath']) or os.path.exists(feed_item['filing_zip_filepath']):
        logger.info(f"\n\nFile Already exists\t {feed_item['filing_filepath']}\n\n")

    if zip_filing:

        zipfile.ZipFile(feed_item['filing_zip_filepath'], mode='w', compression=zipfile.ZIP_DEFLATED).write(feed_item['filing_filepath'])
        os.remove(feed_item['filing_filepath'])

    return feed_item
