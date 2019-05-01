import logging

logger = logging.getLogger(__name__)

from py_sec_edgar.filing import download_filing
from py_sec_edgar.utilities import prepare_message

def broker(sec_filing, extract_filing_contents=False):
    """
    Manages the individual filing extraction process
    """
    filing_message = prepare_message(sec_filing)

    filing_message = download_filing(filing_message)

    if extract_filing_contents:

        feed_item = extract_contents(filing_message)






