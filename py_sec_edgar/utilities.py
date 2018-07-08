# view-source:https://www.sec.gov/Archives/edgar/xbrl-rr.rss.xml
# https://www.sec.gov/Archives/edgar/usgaap.rss.xml
# https://www.sec.gov/Archives/edgar/xbrl-inline.rss.xml
# https://www.sec.gov/Archives/edgar/usgaap.rss.xml
# http://www.sec.gov/Archives/edgar/xbrlrss.all.xml
# https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&CIK=&type=10-K&company=&dateb=&owner=include&start=0&count=100&output=atom
import sys

import re
import shutil
import zipfile
from collections import OrderedDict

import string

import unicodedata

import os
import time
from datetime import date, datetime
from urllib.parse import urljoin

import pandas as pd
import requests
from dateutil.parser import parse
from time import mktime
from datetime import datetime

import binascii

# __all__ = ["Error", "encode", "decode"]
import feedparser

try:
    from py_sec_edgar.proxy_request import ProxyRequest
except:
    import proxy_request as full_index


class Error(Exception):
    pass

from bs4 import UnicodeDammit  # BeautifulSoup 4

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
    s = s.replace(r'—', "--")
    s = s.replace('â', " ")
    s = s.replace('\x97', "-")
    s = s.replace('\'s', "'s")
    s = s.replace(" 's", "'s")
    s = s.replace("nan", "")
    s = " ".join(s.split())
    # s = s.lower()
    return s


def clean_text_string_func_newlines(s):
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
    s = s.replace(r'—', "--")
    s = s.replace('â', " ")
    s = s.replace('\x97', "-")
    s = s.replace('\'s', "'s")
    s = s.replace(" 's", "'s")
    s = s.replace("nan", "")
    s = s.replace("\n", "")
    s = " ".join(s.split())
    # s = s.lower()
    return s


def clean_text_string_func_Az(s):
    s = s.replace('\r', ' ')
    s = s.replace('\t', ' ')
    s = s.replace('\f', ' ')
    # s = s.replace('\n', ' ')
    s = s.replace('\x92', "'")
    s = s.replace('\x93', '"')
    s = s.replace('\x94', '"')
    s = s.replace('\x96', "-")
    s = s.replace('\x95', "-")
    s = s.replace('\\', " ")
    s = s.replace('- ', " ")
    s = s.replace('â', " ")
    s = s.replace(" 's", "'s")
    re.sub(r"[A-z]\'", r"'", s)
    s = " ".join(s.split())
    # s = s.lower()
    return s


# lista = list(element.itertext())

def cleanLists_newlines(lista):
    lista = ['\n'.join(' '.join(line.split()) for line in x.split('\n')) for x in lista]
    lista = ["".join(x) for x in lista]
    lista = [x.replace('\b', ' ') for x in lista]
    lista = [x.replace('\n', '  ') for x in lista]
    lista = [x.encode('utf8') for x in lista]
    lista = [x.decode('utf8') for x in lista]
    lista = [unicodedata.normalize("NFKD", l) for l in lista]
    return lista


def cleanLists(lista):
    # lista = ['\n'.join(' '.join(line.split()) for line in x.split('\n')) for x in lista]
    lista = ["".join(x) for x in lista]
    lista = [x.replace('\b', ' ') for x in lista]
    lista = [x.encode('utf8') for x in lista]
    lista = [x.decode('utf8') for x in lista]
    lista = [unicodedata.normalize("NFKD", l) for l in lista]
    return lista


def normalize_accented_characters(i, vtext):
    # print("this text", vtext)
    try:
        ctext = unicodedata.normalize('NFKD', vtext).decode('utf-8').encode('ascii', 'ignore')
        return ctext
    except TypeError:
        ctext = clean_text_string_func(decode_html(unicodedata.normalize("NFKD", vtext)))
        return ctext
    except:
        # print('big prob', type(vtext))
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
        out_file.write(('begin %o %s\n' % ((mode & 0o777), name)).encode("ascii"))
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


def unzip_excel(fullfilepath):
    basename = os.path.basename(fullfilepath)
    extname = os.path.splitext(basename)
    dirname = os.path.dirname(fullfilepath)
    destfolder = os.path.join(dirname, extname[0])
    try:
        excel_file_name = "Financial_Report.xlsx"
        extracted_excel_file = os.path.join(dirname, excel_file_name)
        archive = zipfile.ZipFile(fullfilepath)
        for file in archive.namelist():
            if file == excel_file_name:
                archive.extract(file, dirname)
                os.rename(extracted_excel_file, zfullfilepath.replace('.zip', '.xlsx'))
    except:
        print("ERROR! ERROR! ABORT! ABORT! " + fullfilepath)


###### get files in cik folder

def get_list_of_cik_folders(FOLDER):
    folders = os.listdir(FOLDER)
    return folders


def get_fullfilepaths_files_in_folder(folder_to_process):
    files_in_folder = [os.path.join(folder_to_process, x) for x in os.listdir(folder_to_process)]
    return files_in_folder



def get_pattern_for_filename(filename, pattern):
    match = re.search(pattern, filename)
    s = match.start()
    e = match.end()
    result = filename[s:e]
    return result

def get_cik_form_period(filename):
    edgar_items = OrderedDict()
    for pkey, pvalue in pattern.items():
        try:
            result = get_pattern_for_filename(filename, pvalue)
            key, value = result.split("(")[0], result.split("(")[1][:-1]
            edgar_items[key] = value
        except:
            p = pkey
            edgar_items[p] = None
    return edgar_items

def move_file_to_new_folder(filename, new_file_path):
    basename = os.path.basename(filename)
    shutil.move(filename, new_file_path)


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

def create_edgarfilename(basename, item):
    try:
        edgfilepath = str(basename + "#2_" + item['edgar_filenumber'] + "_#3_" + date.fromtimestamp(
            mktime(item['published_parsed'])).strftime("%Y-%m-%dTZ%H-%M-%S") + "_#4_" + item[
                              'edgar_ciknumber'] + "_#5_" + item['edgar_companyname'] + "_#6_" + item[
                              'edgar_formtype'] + "_#7_" + item['edgar_period'])
    except:
        edgfilepath = str(basename + "#2_" + item['edgar_filenumber'] + "_#3_" + date.fromtimestamp(
            mktime(item['published_parsed'])).strftime("%Y-%m-%dTZ%H-%M-%S") + "_#4_" + item[
                              'edgar_ciknumber'] + "_#5_" + item['edgar_companyname'] + "_#6_" + item[
                              'edgar_formtype'] + "_#7_" + "NOPERIOD")


    return edgfilepath


def remove_bad_char(strng):
    try:
        valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
        edgar_filename_create = ''.join(c for c in strng if c in valid_chars)
    except:
        print(edgar_filename_create)
    return edgar_filename_create


def create_edgarfilename_one(item):
    try:
        # if ("10-K" in item["edgar_formtype"]) or ("S-1" in item["edgar_formtype"]) or ("20-F" in item["edgar_formtype"]) or ("8-K" in item["edgar_formtype"]):
        edgfilename = str("#2_" + item['edgar_filenumber'] + "_#3_" + datetime.fromtimestamp(
            mktime(item['published_parsed'])).strftime("%Y-%m-%dTZ%H-%M-%S") + "_#4_" + item[
                              'edgar_ciknumber'] + "_#5_" + item['edgar_companyname'] + "_#6_" + item[
                              'edgar_formtype'] + "_#7_" + item['edgar_period'])
    except:
        print("exception: Trying without Period")
        edgfilename = str("#2_" + item['edgar_filenumber'] + "_#3_" + datetime.fromtimestamp(
            mktime(item['published_parsed'])).strftime("%Y-%m-%dTZ%H-%M-%S") + "_#4_" + item[
                              'edgar_ciknumber'] + "_#5_" + item['edgar_companyname'] + "_#6_" + item[
                              'edgar_formtype'] + "_#7_" + "NOPERIOD")

    edgfilename.replace(" ", "_").replace(".", "_").replace(
        ",", "_").replace("/", "_").replace("__", "_").replace("/", "_")
    print(edgfilename)
    return edgfilename


def split_edgarfilename(filepath):
    filepath_stats = {}

    name_list = ['SEC_SOURCE', 'SEC_UID', 'SEC_DATETIME', 'SEC_CIK', 'TICKER_NAME', 'SEC_FORM', 'SEC_PERIOD']

    # split basename of edgar filing by # then if 2nd character is _ then start from 2 and upper else upper
    value_list = [value[2:].upper() if value[1] == "_" else value.upper() for value in os.path.basename(filepath).split("_#")]

    filepath_stats.update(dict(list(zip(name_list, value_list))))

    filepath_stats['SEC_DATE'] = filepath_stats['SEC_DATETIME'].split("TZ")[0]
    filepath_stats['SEC_PERIOD'] = filepath_stats['SEC_PERIOD'].split(".")[0].replace(".txt","")
    filepath_stats['SEC_YEAR'] = int(filepath_stats['SEC_PERIOD'][0:4])
    filepath_stats["TICKER"] = filepath_stats["TICKER_NAME"].split(")")[0][1:]
    filepath_stats["NAME"] = filepath_stats["TICKER_NAME"].split(")")[1][1:]
    filepath_stats['FILEPATH'] = filepath.upper()
    filepath_stats['DIRECTORY'] = os.path.dirname(filepath.upper())
    filepath_stats['BASENAME'] = os.path.basename(filepath.upper())
    filepath_stats['SEC_ARCHIVES_INDEX_URL'] = urljoin("https://www.sec.gov/Archives/", filepath_stats['SEC_UID'].replace("_","/").lower() + "-index.htm")
    filepath_stats['SEC_ARCHIVES_COMPLETE_FILING_URL'] = urljoin("https://www.sec.gov/Archives/",
                                                                 filepath_stats['SEC_UID'].replace("_","/").lower().replace("-","") + "/" +
                                                                 filepath_stats['SEC_UID'].split("_")[-1] + ".txt")
    try:
        filepath_stats['DATE_MODIFIED'] = time.strftime("%Y%m%dT%H%M%S", time.localtime(os.path.getmtime(filepath)))
        filepath_stats['DATE_CREATED'] = time.strftime("%Y%m%dT%H%M%S", time.localtime(os.path.getctime(filepath)))
    except:
        filepath_stats['DATE_MODIFIED'] = "#N/A"
        filepath_stats['DATE_CREATED'] = "#N/A"

    return filepath_stats


def edgar_filing_idx_create_filename(basename, item, ticker):
    date_string = datetime.strftime(parse(str(item['published'])), "%Y-%m-%dTZ%H-%M-%S")
    try:
        edgfilepath = 'edgaridx-{}_txt_#2_{}_#3_{}_#4_{}_#5_({})_{}_#6_{}_#7_{}'.format(basename[8:], item['link'].replace(r'http://www.sec.gov/Archives/',"").replace(".txt","").replace("/","_").replace("-index.htm",""), date_string, item['edgar_ciknumber'],ticker , item['edgar_companyname'],item['edgar_formtype'], item['edgar_period'])
    except:
        edgfilepath = 'edgaridx-{}_txt_#2_{}_#3_{}_#4_{}_#5_({})_{}_#6_{}_#7_{}'.format(basename[8:], item['link'].replace(r'http://www.sec.gov/Archives/', "").replace(".txt", "").replace("/", "_").replace("-index.htm", ""), date_string, item['edgar_ciknumber'], ticker, item['edgar_companyname'],item['edgar_formtype'], "NOPERIOD")

    edgfilepath = edgfilepath.replace(" ", "_").replace(",", "_").replace(".", "_").replace("/", "_").replace("\\","_").replace("__", "_")
    return edgfilepath + ".txt"

def edgar_filing_txt_create_filename(basename, item, ticker):
    date_string = datetime.strftime(parse(str(item['published'])), "%Y-%m-%dTZ%H-%M-%S")
    try:
        edgfilepath = 'edgaridx-{}_#2_{}_#3_{}_#4_{}_#5_({})_{}_#6_{}_#7_{}'.format(basename[8:], item['link'].replace(r'http://www.sec.gov/Archives/',"").replace(".txt","").replace("/","_").replace("-index.htm",""), date_string, item['edgar_ciknumber'],ticker , item['edgar_companyname'],item['edgar_formtype'], item['edgar_period'])
    except:
        edgfilepath = 'edgaridx-{}_#2_{}_#3_{}_#4_{}_#5_({})_{}_#6_{}_#7_{}'.format(basename[8:], item['link'].replace(r'http://www.sec.gov/Archives/', "").replace(".txt", "").replace("/", "_").replace("-index.htm", ""), date_string, item['edgar_ciknumber'], ticker, item['edgar_companyname'],item['edgar_formtype'], "NOPERIOD")

    edgfilepath = edgfilepath.replace(" ", "_").replace(",", "_").replace(".", "_").replace("/", "_").replace("\\","_").replace("__", "_")
    return edgfilepath + ".txt"


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

def determine_if_sec_edgar_feed_and_local_files_differ(url, local_filepath):

    temp_filepath = os.path.join(os.path.dirname(local_filepath), "temp_{}".format(os.path.basename(local_filepath)))

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
        quarter = '{}'.format(values.year), "QTR{}".format(int(values.month/3))
        dates_data.append(quarter)

    dates_quarters = list(set(dates_data))
    dates_quarters.sort(reverse=True)

    return dates_quarters


def scan_all_local_filings(directory, year=None):
    files = walk_dir_fullpath(os.path.join(directory,year))
    return files
