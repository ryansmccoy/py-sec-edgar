import os
import shutil
import logging

logger = logging.getLogger(__name__)

from py_sec_edgar.proxy import ProxyRequest
import zipfile

def download_filing(feed_item, zip_filing=False):
    """
    {'CIK': 104169,
     'Company Name': 'Walmart Inc.',
     'Date Filed': '2019-03-28',
     'Filename': 'edgar/data/104169/0000104169-19-000016.txt',
     'Form Type': '10-K',
     'cik_directory': 'C:\\sec_gov\\Archives\\edgar\\data\\104169\\',
     'extracted_filing_directory': 'C:\\sec_gov\\Archives\\edgar\\data\\104169\\000010416919000016',
     'filing_filepath': 'C:\\sec_gov\\Archives\\edgar\\data\\104169\\0000104169-19-000016.txt',
     'filing_folder': '000010416919000016',
     'filing_url': 'https://www.sec.gov/Archives/edgar/data/104169/0000104169-19-000016.txt',
     'filing_zip_filepath': 'C:\\sec_gov\\Archives\\edgar\\data\\104169\\0000104169-19-000016.zip',
     'published': '2019-03-28',
     'url': 'https://www.sec.gov/Archives/edgar/data/104169/0000104169-19-000016.txt'}
    """
    if not os.path.exists(feed_item['cik_directory']):

        os.makedirs(feed_item['cik_directory'])

    if not os.path.exists(feed_item['filing_filepath']):

        g = ProxyRequest()

        g.GET_FILE(feed_item['filing_url'], feed_item['filing_filepath'])

        # todo: celery version of download full
        # consume_complete_submission_filing_txt.delay(feed_item, filepath_cik)

    elif os.path.exists(feed_item['filing_filepath']) or os.path.exists(feed_item['filing_zip_filepath']):
        logger.info(f"\n\nFile Already exists\t {feed_item['filing_filepath']}\n\n")
    else:
        logger.info(f"\n\nSomething Might be wrong\t {feed_item['filing_filepath']}\n\n")

    if zip_filing:

        zipfile.ZipFile(feed_item['filing_zip_filepath'], mode='w', compression=zipfile.ZIP_DEFLATED).write(feed_item['filing_filepath'])
        os.remove(feed_item['filing_filepath'])

    return feed_item
