import random
import time

import lxml.html

sys.path.append('..')
import requests

sys.path.append('..')
from py_sec_edgar_data.settings import CONFIG_DIR

import string
from bs4 import BeautifulSoup

import unicodedata

try:
    from bs4 import UnicodeDammit  # BeautifulSoup 4


    def decode_html(html_string):
        converted = UnicodeDammit(html_string)
        if not converted.unicode_markup:
            raise UnicodeDecodeError(
                "Failed to detect encoding, tried [%s]",
                ', '.join(converted.tried_encodings))
            # print converted.original_encoding
        return converted.unicode_markup

except ImportError:
    from BeautifulSoup import UnicodeDammit  # BeautifulSoup 3


    def decode_html(html_string):
        converted = UnicodeDammit(html_string, isHTML=True)
        if not converted.unicode:
            raise UnicodeDecodeError(
                "Failed to detect encoding, tried [%s]",
                ', '.join(converted.triedEncodings))
            # print converted.originalEncoding
        return converted.unicode


class Gotem(object):
    """
    Used to Downlod things throughs VPN
    """

    def __init__(self):

        self.file_list_user_agents = os.path.join(CONFIG_DIR, 'user_agents.txt')
        self.file_list_nordvpn_ips = os.path.join(CONFIG_DIR, 'vpn.py')
        self.USERNAME = os.getenv('VPN_USERNAME')
        self.PASSWORD = os.getenv('VPN_PASSWORD')
        self._generate_random_proxy_hosts()
        self.user_agent = self._generate_random_user_agent()
        self._headers = {'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                         'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
                         'Accept-Encoding': 'gzip,deflate,sdch',
                         'Accept-Language': 'en-US,en;q=0.8',
                         'Connection': 'close',
                         'User-Agent': self.user_agent}
        self.response = ""
        self.datastoragetype = None
        self.connect_timeout, self.read_timeout = 5.0, 30.0
        self.retry_counter = 3
        self.url = "No Url"

    def read_and_return(self, filename):
        with open(filename, 'r') as f:
            self.data = f.read().splitlines()
        return self.data

    def _generate_random_nordvpn_ip(self):
        self.list_nordvpn_ips = self.read_and_return(self.file_list_nordvpn_ips)
        self._nordvpn_ips = random.choice(self.data)
        print("\t IP: {}".format(self._nordvpn_ips))
        return self._nordvpn_ips

    def _generate_random_proxy_hosts(self):
        self.host = self._generate_random_nordvpn_ip()
        self.proxies = {
            'http': 'http://' + self.USERNAME + ':' + self.PASSWORD + '@' + self.host + ":" + '80',
            'https': 'https://' + self.USERNAME + ':' + self.PASSWORD + '@' + self.host + ":" + '80'
        }

    def _generate_random_user_agent(self):
        self.list_user_agents = self.read_and_return(self.file_list_user_agents)
        self._user_agent = random.choice(self.list_user_agents)
        print("\t USER-AGENT: {}".format(self._user_agent))

    def GET_HTML(self, url=None, filepath=None, retry_counter=3):
        if retry_counter == 0:
            print("Failed to Download " + url)
            print("HTML failed")
            self.r = "404"
            return
        self.url = url
        if filepath:
            self.filepath = filepath
        try:
            self.r = requests.get(url, stream=True, headers=self._headers, proxies=self.proxies, timeout=(self.connect_timeout, self.read_timeout))
            print('HTML Downloaded: {}'.format(url))
            return
        except:
            print("Retrying:", retry_counter)
            retry_counter -= 1
            self.GET_HTML(url=url, retry_counter=retry_counter)

    def GET_URL(self, url, params=None, filepath=None):
        self.url = url
        if filepath:
            self.filepath = filepath

        retry_counter = self.retry_counter
        while retry_counter > 0:
            try:
                self.r = requests.get(url, stream=True, params=params, headers=self._headers, proxies=self.proxies, timeout=(self.connect_timeout, self.read_timeout))
                status = "success"
                return status
            except:
                print("Retrying:", retry_counter)
                retry_counter -= 1
                if retry_counter == 0:
                    print("Failed to Download " + url)
                    status = "fail"
                    return status

    def get_multiple_html(self):
        dictofhtml = dict()
        for no, url in enumerate(self.urls):
            r = requests.get(self.url, headers=self._headers, proxies=self.proxies, timeout=2.0)
            dictofhtml[no] = {url: r.content}
            timed = time.sleep(random.randint(1, 3))
            print(timed)
        return dictofhtml

    def GET_FILE(self, url, filepath=None):
        self.filepath = filepath
        self.url = url
        retry_counter = self.retry_counter
        while retry_counter > 0:
            try:
                self.r = requests.get(url, stream=True, headers=self._headers, proxies=self.proxies,
                                      timeout=(self.connect_timeout, self.read_timeout))
                print('request made', self.proxies)
                with open(filepath, 'wb') as f:
                    for chunk in self.r.iter_content(chunk_size=1024):
                        if chunk:  # filter out keep-alive new chunks
                            f.write(chunk)
                status = "success"
                return status
            except:
                print("Retrying:", retry_counter)
                self._generate_random_nordvpn_ip()
                self._generate_random_proxy_hosts()
                time.sleep(1)
                retry_counter -= 1
                if retry_counter == 0:
                    print("Failed to Download " + url)
                    status = "fail"
                    return status

    def GET_FILE_CELERY(self, url, filepath):
        print('request made', self.proxies)
        self.r = requests.get(url, stream=True, headers=self._headers, proxies=self.proxies, timeout=(self.connect_timeout, self.read_timeout))
        with open(filepath, 'wb') as f:
            for chunk in self.r.iter_content(chunk_size=1024):
                if chunk:  # filter out keep-alive new chunks
                    f.write(chunk)
        status = "success"
        return status

    def GET_URLS(self, url):
        self.url = url
        try:
            html = self.GET_HTML(self.url)
            html = lxml.html.fromstring(html.text)
            html.make_links_absolute(url)
            html = lxml.html.tostring(html)
            soup = BeautifulSoup(html, 'lxml')
            urls = []
            [urls.append(link['href']) for link in soup.find_all('a', href=True)]
            self.list_urls = urls
        except:
            print("error w/ GET_URLS")

    def __repr__(self):
        return "URL: {}".format(self.url)


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


"""Implementation of the UUencode and UUdecode functions.

encode(in_file, out_file [,name, mode])

decode(in_file [, out_file, mode])

"""

import binascii

__all__ = ["Error", "encode", "decode"]


class Error(Exception):
    pass


def uuencode(in_file, out_file, name=None, mode=None):
    """Uuencode file"""
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


import sys


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


import os
import re
import shutil
import zipfile
from collections import OrderedDict


def walk_dir_fullfilename(directory, contains=None):
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


# all_files = walk_dir_fullfilename(FOLDER)

def calc_unprocessed(udir, pdir):
    unproscessed_files = walk_dir_fullfilename(udir)
    up = [unprocessed.replace(udir, "") for unprocessed in unproscessed_files]
    len(up)

    processed_files = walk_dir_fullfilename(pdir)
    pr = [processed.replace(pdir, "") for processed in processed_files]
    len(pr)

    c1 = Counter(up)
    c2 = Counter(pr)
    diff = list((c1 - c2).elements())
    len(diff)
    diff = [os.path.join(udir + file) for file in diff]
    return diff


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


# cik_folders = get_list_of_cik_folders(CIK_FOLDER)

def get_fullfilepaths_files_in_folder(folder_to_process):
    files_in_folder = [os.path.join(folder_to_process, x) for x in os.listdir(folder_to_process)]
    return files_in_folder


# all_files = get_fullfilepaths_files_in_folder(FOLDER)


def get_pattern_for_filename(filename, pattern):
    match = re.search(pattern, filename)
    s = match.start()
    e = match.end()
    result = filename[s:e]
    return result


# get_pattern_for_filename(filename, pattern)

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


# edgar_items = get_cik_form_period(filename)


# new_file_path = generate_new_filepath_from_dict(edgar_items)

def move_file_to_new_folder(filename, new_file_path):
    basename = os.path.basename(filename)
    shutil.move(filename, new_file_path)


# unprocessed_filings = produce(unprocessed_filings[0:5])
# file = diff[1]
# filename = r'C:\SEC\IN\2012\12\CIK(0000801898)_FORM(10-K)_PERIOD(20121026).zip'

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


def edgar_filing_idx_create_filename(item):
    date_string = str(parse(item['published']).strftime("%Y-%m-%dTZ%H-%M-%S"))
    edgfilepath = 'edgaridx-{}_txt_#2_{}_#3_{}_#4_{}_#5_({})_{}_#6_{}_#7_{}.txt'.format(
        str(item['edgar_filingdate'][0:6]), os.path.dirname(item['link'].replace(r'http://www.sec.gov/Archives/', "")).replace("/", "_"), date_string, item['edgar_ciknumber'], "TICKER", item['edgar_companyname'],
        item['edgar_formtype'], str(item['edgar_period']))
    edgfilepath = edgfilepath.replace(" ", "_").replace(",", "_").replace(".", "_").replace("/", "_").replace("\\", "_").replace("__", "_").replace("_txt", "")
    return edgfilepath
