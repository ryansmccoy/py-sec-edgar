import logging
import os
import os.path
import time
import zipfile
from datetime import datetime

logger = logging.getLogger(__name__)

import re

re10k = re.compile('10-K')
regex_no_rfiles = re.compile(r'R.+\.htm')

logger = logging.getLogger(__name__)

import binascii
import string
import sys
import unicodedata

import feedparser
import pandas as pd
import requests
from bs4 import UnicodeDammit  # BeautifulSoup 4

from .settings import settings


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
    valid_chars = f"-_.() {string.ascii_letters}{string.digits}"
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
        local_filepath), f"temp_{os.path.basename(local_filepath)}")

    temp_size = file_size(temp_filepath)
    local_size = file_size(local_filepath)

    if local_size == temp_size:
        print(f"local_size {local_size} == temp_size {temp_size}")
        os.remove(temp_filepath)
        return False
    else:
        print(f"local_size {local_size} != temp_size {temp_size}")
        if os.path.exists(local_filepath):
            os.remove(local_filepath)
        os.rename(temp_filepath, temp_filepath.replace("temp_", ""))
        return True

def generate_folder_names_years_quarters(start_date, end_date):

    dates_data = []

    date_range = pd.date_range(datetime.strptime(start_date, "%m/%d/%Y"), datetime.strptime(end_date, "%m/%d/%Y"), freq="QE")

    for i, values in enumerate(date_range):
        # Fix quarter calculation: (month - 1) // 3 + 1
        quarter_num = (values.month - 1) // 3 + 1
        quarter = f'{values.year}', f"QTR{quarter_num}"
        dates_data.append(quarter)

    dates_quarters = list(set(dates_data))
    dates_quarters.sort(reverse=True)

    return dates_quarters

class RetryRequest:
    """
    HTTP request handler with configurable retry logic and exponential backoff.
    
    Follows best practices for robust network requests with proper error handling
    and rate limiting for SEC EDGAR API compliance.
    """

    def __init__(self, max_retries=3, base_delay=1.0, max_delay=60.0, backoff_factor=2.0):
        """
        Initialize RetryRequest with configurable retry parameters.
        
        Args:
            max_retries: Maximum number of retry attempts
            base_delay: Initial delay between retries in seconds
            max_delay: Maximum delay between retries in seconds  
            backoff_factor: Exponential backoff multiplier
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.connect_timeout = 10.0
        self.read_timeout = 30.0

        # Create session for SEC compliance
        self.session = requests.Session()
        self.session.headers.update(settings.get_request_headers())

    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay for retry attempt with exponential backoff."""
        delay = self.base_delay * (self.backoff_factor ** attempt)
        return min(delay, self.max_delay)

    def _should_retry(self, exception: Exception, attempt: int) -> bool:
        """Determine if request should be retried based on exception type and attempt count."""
        if attempt >= self.max_retries:
            return False

        # Retry on network-related exceptions
        retryable_exceptions = (
            requests.exceptions.ConnectTimeout,
            requests.exceptions.ReadTimeout,
            requests.exceptions.ConnectionError,
            requests.exceptions.HTTPError
        )

        if isinstance(exception, retryable_exceptions):
            return True

        # Retry on specific HTTP status codes for HTTPError
        if isinstance(exception, requests.exceptions.HTTPError) and hasattr(exception, 'response'):
            if exception.response is not None:
                status_code = exception.response.status_code
                # Retry on server errors (5xx) and rate limiting (429)
                return status_code >= 500 or status_code == 429

        return False

    def get(self, url: str, **kwargs) -> requests.Response:
        """
        Perform HTTP GET request with retry logic and rate limiting.
        
        Args:
            url: URL to request
            **kwargs: Additional arguments passed to requests.get
            
        Returns:
            requests.Response: The successful response object
            
        Raises:
            requests.exceptions.RequestException: If all retry attempts fail
        """
        logger.info(f"Requesting: {url}")

        # Apply SEC rate limiting
        time.sleep(settings.request_delay)

        # Set timeouts if not provided
        if 'timeout' not in kwargs:
            kwargs['timeout'] = (self.connect_timeout, self.read_timeout)

        # Remove headers from kwargs as they're handled by session
        kwargs.pop('headers', None)

        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                logger.debug(f"Attempt {attempt + 1}/{self.max_retries + 1} for {url}")

                response = self.session.get(url, **kwargs)
                response.raise_for_status()  # Raise exception for bad status codes

                logger.info(f"Request successful: {url} (Status: {response.status_code})")
                return response

            except Exception as e:
                last_exception = e

                if not self._should_retry(e, attempt):
                    logger.error(f"Request failed permanently: {url} - {e}")
                    break

                delay = self._calculate_delay(attempt)
                logger.warning(f"Request failed (attempt {attempt + 1}): {e}")
                logger.info(f"Retrying in {delay:.1f} seconds...")
                time.sleep(delay)

        # All retries exhausted
        logger.error(f"💥 All retry attempts failed for {url}")
        raise last_exception or requests.exceptions.RequestException(f"Failed to fetch {url}")

    def download_file(self, url: str, filepath: str, chunk_size: int = 8192) -> bool:
        """
        Download a file from URL to local filepath with retry logic.
        
        Args:
            url: URL to download from
            filepath: Local path to save the file
            chunk_size: Size of chunks for streaming download
            
        Returns:
            bool: True if download successful, False otherwise
        """
        try:
            logger.info(f"Downloading: {url}")
            logger.info(f"Saving to: {filepath}")

            # Ensure directory exists
            os.makedirs(os.path.dirname(filepath), exist_ok=True)

            # Use streaming download for large files
            response = self.get(url, stream=True)

            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0

            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:  # Filter out keep-alive chunks
                        f.write(chunk)
                        downloaded_size += len(chunk)

                        # Log progress for large files
                        if total_size > 0 and downloaded_size % (chunk_size * 100) == 0:
                            progress = (downloaded_size / total_size) * 100
                            logger.debug(f"Download progress: {progress:.1f}%")

            logger.info(f"Download completed: {filepath}")
            logger.info(f"File size: {convert_bytes(downloaded_size)}")
            return True

        except Exception as e:
            logger.error(f"Download failed: {url} - {e}")

            # Clean up partial file on failure
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                    logger.debug(f"🧹 Cleaned up partial file: {filepath}")
                except OSError:
                    pass

            return False

    def get_json(self, url: str, **kwargs) -> dict:
        """
        Fetch and parse JSON from URL with retry logic.
        
        Args:
            url: URL to fetch JSON from
            **kwargs: Additional arguments passed to get()
            
        Returns:
            dict: Parsed JSON data
            
        Raises:
            requests.exceptions.RequestException: If request fails
            ValueError: If response is not valid JSON
        """
        response = self.get(url, **kwargs)
        try:
            return response.json()
        except ValueError as e:
            logger.error(f"❌ Invalid JSON response from {url}: {e}")
            raise ValueError(f"Invalid JSON response from {url}") from e


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
    print(f"Parsing DOC {i}")
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

        # Use the new download_file method instead of the old get method
        success = g.download_file(filing_json['filing_url'], filing_json['filing_filepath'])

        if not success:
            logger.error(f"Failed to download {filing_json['filing_url']}")
            return filing_json

    elif os.path.exists(filing_json['filing_filepath']) or os.path.exists(filing_json['filing_zip_filepath']):
        logger.info(f"⚠️  File already exists: {filing_json['filing_filepath']}")

    if zip_filing and os.path.exists(filing_json['filing_filepath']):
        zipfile.ZipFile(filing_json['filing_zip_filepath'], mode='w', compression=zipfile.ZIP_DEFLATED).write(filing_json['filing_filepath'])
        os.remove(filing_json['filing_filepath'])

    return filing_json
