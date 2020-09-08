import logging
import os
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

from py_sec_edgar.filing import download_filing, extract_filing

class BrokerManager:

    def __init__(self, CONFIG=None):

        if CONFIG == None:
            from py_sec_edgar.settings import CONFIG

        self.CONFIG = CONFIG
        self.extract_filing_contents = CONFIG.extract_filing_contents

        self.download_filing = download_filing
        self.extract_filing = extract_filing

        logger.info("Initalizing Broker...")

    def prepare_message(self, sec_filing):
        """
        Sets parameters needed for various aspects.

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

    def process_filing(self, sec_filing):
        """
        Manages the individual filing extraction process
        """

        broker_message = self.prepare_message(sec_filing)

        broker_message = self.download_filing(broker_message)

        filing_content = self.extract_filing(broker_message)
