import logging
logger = logging.getLogger(__name__)

import os
from urllib.parse import urljoin

from py_sec_edgar.utilities import download
from py_sec_edgar.extract import extract


class FilingProcessor:

    def __init__(self, filing_data_dir, edgar_Archives_url):

        logger.info("Initalizing FilingProcessor...")

        self.filing_data_dir = filing_data_dir
        self.edgar_Archives_url = edgar_Archives_url

        self.download = download
        self.extract = extract

    def generate_filepaths(self, sec_filing):
        """
        Sets up the filepaths for the filing

        :param filing_json:
        :return: filing_json:

        """

        feed_item = dict(sec_filing)
        feed_item['cik_directory'] = self.filing_data_dir.replace("CIK", str(feed_item['CIK'])).replace("FOLDER", "")
        feed_item['filing_filepath'] = os.path.join(feed_item['cik_directory'], os.path.basename(feed_item['Filename']))
        feed_item['filing_zip_filepath'] = os.path.join(feed_item['cik_directory'], os.path.basename(feed_item['Filename']).replace('.txt', '.zip'))
        feed_item['filing_folder'] = os.path.basename(feed_item['Filename']).split('.')[0].replace("-", "")
        feed_item['extracted_filing_directory'] = self.filing_data_dir.replace("CIK", str(feed_item['CIK'])).replace("FOLDER", feed_item['filing_folder'])
        feed_item['filing_url'] = urljoin(self.edgar_Archives_url, feed_item['Filename'])

        return feed_item

    def process(self, filing_meta):
        """
        Manages the individual filing extraction process
        """

        filing_filepaths = self.generate_filepaths(filing_meta)

        filing_filepaths = self.download(filing_filepaths)

        filing_content = self.extract(filing_filepaths)

        self.post_process(filing_content)

    def post_process(self, filing_contents):
        """
        Insert Custom Processing here

        :param filing_contents:
        :return:
        """
        pass

