import time
import zipfile
from datetime import datetime
import os
import os.path
import logging

import re

from py_sec_edgar.filing import logger

re10k = re.compile('10-K')
regex_no_rfiles = re.compile(r'R.+\.htm')

logger = logging.getLogger(__name__)

import binascii
import string
import sys

import requests
import unicodedata
from bs4 import UnicodeDammit  # BeautifulSoup 4

import feedparser
import pandas as pd

class Error(Exception):
    pass

def decode_html(html_string):
    converted = UnicodeDammit(html_string)
    if not converted.unicode_markup:
        raise UnicodeDecodeError(
            "Failed to detect encoding, tried [%s]",
            ', '.join(converted.tried_encodings))
        # print converted.original_encoding
    return converted.unicode_markup

def clean_text_string_func(s):
    s = s.replace('\r', ' ')
    s = s.replace('\t', ' ')
    s = s.replace('\f', ' ')
    s = s.replace('\n', ' ')
    s = s.replace('\x92', "'")
    s = s.replace('\x93', '"')
    s = s.replace('\x94', '"')
    s = s.replace('\x96', "-")
    s = s.replace('\x95', "-")
    s = s.replace('\\', " ")
    s = s.replace('- ', "-")
    s = s.replace(r'â€”', "--")
    s = s.replace('aÌ‚', " ")
    s = s.replace('\x97', "-")
    s = s.replace('\'s', "'s")
    s = s.replace(" 's", "'s")
    s = s.replace("nan", "")
    s = " ".join(s.split())
    # s = s.lower()
    return s

def cleanLists_newlines(lista):
    lista = ['\n'.join(' '.join(line.split())
                       for line in x.split('\n')) for x in lista]
    lista = ["".join(x) for x in lista]
    lista = [x.replace('\b', ' ') for x in lista]
    lista = [x.replace('\n', '  ') for x in lista]
    lista = [x.encode('utf8') for x in lista]
    lista = [x.decode('utf8') for x in lista]
    lista = [unicodedata.normalize("NFKD", l) for l in lista]
    return lista


def cleanLists(lista):
    lista = ["".join(x) for x in lista]
    lista = [x.replace('\b', ' ') for x in lista]
    lista = [x.encode('utf8') for x in lista]
    lista = [x.decode('utf8') for x in lista]
    lista = [unicodedata.normalize("NFKD", l) for l in lista]
    return lista


def normalize_accented_characters(i, vtext):
    try:
        ctext = unicodedata.normalize('NFKD', vtext).decode(
            'utf-8').encode('ascii', 'ignore')
        return ctext
    except TypeError:
        ctext = clean_text_string_func(decode_html(
            unicodedata.normalize("NFKD", vtext)))
        return ctext
    except:
        ctext = str(vtext)
        return ctext


def format_filename(s):
    valid_chars = "-_.() {}{}".format(string.ascii_letters, string.digits)
    filename = ''.join(c for c in s if c in valid_chars)
    filename = filename.replace(' ', '_')
    return filename

def uuencode(in_file, out_file, name=None, mode=None):
    """Uuencode file"""

    """Implementation of the UUencode and UUdecode functions.

    encode(in_file, out_file [,name, mode])

    decode(in_file [, out_file, mode])

    """
    #
    # If in_file is a pathname open it and change defaults
    #
    opened_files = []
    try:
        if in_file == '-':
            in_file = sys.stdin.buffer
        elif isinstance(in_file, str):
            if name is None:
                name = os.path.basename(in_file)
            if mode is None:
                try:
                    mode = os.stat(in_file).st_mode
                except AttributeError:
                    pass
            in_file = open(in_file, 'rb')
            opened_files.append(in_file)
        #
        # Open out_file if it is a pathname
        #
        if out_file == '-':
            out_file = sys.stdout.buffer
        elif isinstance(out_file, str):
            out_file = open(out_file, 'wb')
            opened_files.append(out_file)
        #
        # Set defaults for name and mode
        #
        if name is None:
            name = '-'
        if mode is None:
            mode = 0o666
        #
        # Write the data
        #
        out_file.write(('begin %o %s\n' %
                        ((mode & 0o777), name)).encode("ascii"))
        data = in_file.read(45)
        while len(data) > 0:
            out_file.write(binascii.b2a_uu(data))
            data = in_file.read(45)
        out_file.write(b' \nend\n')
    finally:
        for f in opened_files:
            f.close()

def uudecode(in_file, out_file=None, mode=None, quiet=True):
    """Decode uuencoded file"""
    #
    # Open the input file, if needed.
    #
    opened_files = []
    if in_file == '-':
        in_file = sys.stdin.buffer
    elif isinstance(in_file, str):
        in_file = open(in_file, 'rb')
        opened_files.append(in_file)

    try:
        #
        # Read until a begin is encountered or we've exhausted the file
        #
        while True:
            hdr = in_file.readline()
            if not hdr:
                raise Error('No valid begin line found in input file')
            if not hdr.startswith(b'begin'):
                continue
            hdrfields = hdr.split(b' ', 2)
            if len(hdrfields) == 3 and hdrfields[0] == b'begin':
                try:
                    int(hdrfields[1], 8)
                    break
                except ValueError:
                    pass
        if out_file is None:
            # If the filename isn't ASCII, what's up with that?!?
            out_file = hdrfields[2].rstrip(b' \t\r\n\f').decode("ascii")
            if os.path.exists(out_file):
                raise Error('Cannot overwrite existing file: %s' % out_file)
        if mode is None:
            mode = int(hdrfields[1], 8)
        #
        # Open the output file
        #
        if out_file == '-':
            out_file = sys.stdout.buffer
        elif isinstance(out_file, str):
            fp = open(out_file, 'wb')
            try:
                os.path.chmod(out_file, mode)
            except AttributeError:
                pass
            out_file = fp
            opened_files.append(out_file)
        #
        # Main decoding loop
        #
        s = in_file.readline()
        while s and s.strip(b' \t\r\n\f') != b'end':
            try:
                data = binascii.a2b_uu(s)
            except binascii.Error as v:
                # Workaround for broken uuencoders by /Fredrik Lundh
                nbytes = (((s[0] - 32) & 63) * 4 + 5) // 3
                data = binascii.a2b_uu(s[:nbytes])
                if not quiet:
                    sys.stderr.write("Warning: %s\n" % v)
            out_file.write(data)
            s = in_file.readline()
        if not s:
            raise Error('Truncated input file')
    finally:
        for f in opened_files:
            f.close()

def flattenDict(d, result=None):
    if result is None:
        result = {}
    for key in d:
        value = d[key]
        if isinstance(value, dict):
            value1 = {}
            for keyIn in value:
                value1[".".join([key, keyIn])] = value[keyIn]
            flattenDict(value1, result)
        elif isinstance(value, (list, tuple)):
            for indexB, element in enumerate(value):
                if isinstance(element, dict):
                    value1 = {}
                    index = 0
                    for keyIn in element:
                        newkey = ".".join([key, keyIn])
                        value1[".".join([key, keyIn])] = value[indexB][keyIn]
                        index += 1
                    for keyA in value1:
                        flattenDict(value1, result)
        else:
            result[key] = value
    return result


def walk_dir_fullpath(directory, contains=None):
    all_files = []
    for path, dirnames, files in os.walk(directory):
        for file in files:
            fullfilepath = os.path.join(path, file)
            if contains:
                if contains in file:
                    all_files.append(fullfilepath)
            else:
                all_files.append(fullfilepath)
    return all_files


def convert_bytes(num):
    """
    this function will convert bytes to MB.... GB... etc
    """
    for x in ['bytes', 'KB', 'MB', 'GB', 'TB']:
        if num < 1024.0:
            return "%3.1f %s" % (num, x)
        num /= 1024.0

def file_size(file_path):
    """
    this function will return the file size
    """
    if os.path.isfile(file_path):
        file_info = os.stat(file_path)
        return convert_bytes(file_info.st_size)

def read_xml_feedparser(source_file):
    if source_file[0:4] == 'http':
        feed = feedparser.parse(source_file)
    elif source_file.endswith(".xml"):
        with open(source_file) as f:
            feedData = f.read()
        feed = feedparser.parse(feedData)
    else:
        feed = feedparser.parse(source_file)
    return feed


desired_width = 600

def edgar_and_local_differ(url, local_filepath):
    temp_filepath = os.path.join(os.path.dirname(
        local_filepath), "temp_{}".format(os.path.basename(local_filepath)))

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

def generate_folder_names_years_quarters(start_date, end_date):

    dates_data = []

    date_range = pd.date_range(datetime.strptime(start_date, "%m/%d/%Y"), datetime.strptime(end_date, "%m/%d/%Y"), freq="Q")

    for i, values in enumerate(date_range):
        quarter = f'{values.year}', "QTR{}".format(int(values.month / 3))
        dates_data.append(quarter)

    dates_quarters = list(set(dates_data))
    dates_quarters.sort(reverse=True)

    return dates_quarters

class RetryRequest(object):
    def __init__(self):

        self.retry_counter = 3
        self.pause_for_courtesy = False
        self.connect_timeout, self.read_timeout = 10.0, 30.0

    def get(self, url, filepath):

        logger.info(f"\n\n\tDownloading: \t{url}\n")

        retry_counter = 0

        while retry_counter < self.retry_counter:
            try:
                r = requests.get(url, stream=True, timeout=(self.connect_timeout, self.read_timeout))

                logger.info(f"\n\n\tSaving to: \t{filepath}\n")

                with open(filepath, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=1024):
                        if chunk:  # filter out keep-alive new chunks
                            f.write(chunk)

                logger.info(f'\n\n\tSuccess!\tSaved to filepath:\t{filepath}\n\n')
                return

            except Exception as e:
                logger.error(f" \n\n\t {e} \n\nRetrying:", retry_counter)
                time.sleep(3)
                retry_counter -= 1
                if retry_counter == 0:
                    logger.info("Failed to Download " + url)
                    return


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


def cik_column_to_list(df):

    df_cik_tickers = df.dropna(subset=['CIK'])

    df_cik_tickers['CIK'] = df_cik_tickers['CIK'].astype(int)

    return df_cik_tickers['CIK'].tolist()


def download(filing_json, zip_filing=False):

    if not os.path.exists(filing_json['cik_directory']):
        os.makedirs(filing_json['cik_directory'])

    if not os.path.exists(filing_json['filing_filepath']):

        g = RetryRequest()

        g.get(filing_json['filing_url'], filing_json['filing_filepath'])

    elif os.path.exists(filing_json['filing_filepath']) or os.path.exists(filing_json['filing_zip_filepath']):
        logger.info(f"\n\nFile Already exists\t {filing_json['filing_filepath']}\n\n")

    if zip_filing:
        zipfile.ZipFile(filing_json['filing_zip_filepath'], mode='w', compression=zipfile.ZIP_DEFLATED).write(filing_json['filing_filepath'])
        os.remove(filing_json['filing_filepath'])

    return filing_json
