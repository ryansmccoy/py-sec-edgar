
import logging

logger = logging.getLogger(__name__)

from py_sec_edgar.download import download_filing
from py_sec_edgar.extract import extract_contents
from py_sec_edgar.utilities import prepare_filepaths

def broker(filing, extract_filing_contents=False):
    """
    Manages the individual filing extraction process
    """

    feed_item = prepare_filepaths(filing)

    feed_item = download_filing(feed_item)

    if extract_filing_contents:

        feed_item = extract_contents(feed_item)






