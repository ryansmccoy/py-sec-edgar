import os
import logging

logger = logging.getLogger(__name__)

from py_sec_edgar import filing as edgar_filing

def extract_contents(feed_item):
    """
    Extracts the contents of a complete submission filing
    """

    if not os.path.exists(feed_item['cik_directory']):
        logger.info(f"\n\nCreating Folder\n\t {feed_item['filing_path']}")
        return

    if not os.path.exists(feed_item['extracted_filing_directory']) and not os.path.exists(feed_item['extracted_filing_directory'] + ".zip"):

        logger.info("\n\n\n\n\tExtracting Filing Documents:\n")

        try:
            contents = edgar_filing.complete_submission_filing(feed_item['filing_filepath'], output_directory=feed_item['extracted_filing_directory'])
            logger.info(contents)
        except UnicodeDecodeError as E:
            logger.error(f"\n\n\n\nError Decoding \n\n{E}")

        # todo: celery version of download full
        # consume_complete_submission_filing_txt.delay(feed_item, filepath_cik)
        logger.info("\n\n\n\n\tExtraction Complete\n")

    # if os.path.exists(feed_item['cik_directory']) and zip_contents:
    #     shutil.make_archive(feed_item['cik_directory'], 'zip', feed_item['cik_directory'])
    #     shutil.rmtree(feed_item['cik_directory'])
