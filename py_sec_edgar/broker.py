import logging
import os
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

from py_sec_edgar.filing import download_filing, extract_filing

class FilingBroker:

    def __init__(self, CONFIG):

        logger.info("Initalizing Broker...")

        self.CONFIG = CONFIG
        self.CONFIG.BEGIN_PROCESS_FILINGS = True

        self.download_filing = download_filing
        self.extract_filing = extract_filing

        self.filings_processed = 0

    def pre_process(self, sec_filing):
        """
        Sets up the filepaths for the filing

        :param feed_item:
        :return: feed_item:

        # TODO:
            - Fix this
        """

        feed_item = dict(sec_filing)
        feed_item['cik_directory'] = self.CONFIG.TXT_FILING_DIR.replace("CIK", str(feed_item['CIK'])).replace("FOLDER", "")
        feed_item['filing_filepath'] = os.path.join(feed_item['cik_directory'], os.path.basename(feed_item['Filename']))
        feed_item['filing_zip_filepath'] = os.path.join(feed_item['cik_directory'], os.path.basename(feed_item['Filename']).replace('.txt', '.zip'))
        feed_item['filing_folder'] = os.path.basename(feed_item['Filename']).split('.')[0].replace("-", "")
        feed_item['extracted_filing_directory'] = self.CONFIG.TXT_FILING_DIR.replace("CIK", str(feed_item['CIK'])).replace("FOLDER", feed_item['filing_folder'])
        feed_item['filing_url'] = urljoin(self.CONFIG.edgar_Archives_url, feed_item['Filename'])

        return feed_item

    def process(self, sec_filing):
        """
        Manages the individual filing extraction process
        """

        filing_json = self.pre_process(sec_filing)

        filing_json = self.download_filing(filing_json)

        filing_content = self.extract_filing(filing_json)

        self.post_process(filing_content)

    def post_process(self, filing_contents):
        """
        Insert Custom Processing here

        :param filing_contents:
        :return:
        """
        pass

