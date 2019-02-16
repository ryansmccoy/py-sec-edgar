
import os
from datetime import datetime
from pprint import pprint
import shutil

from settings import CONFIG
import filing as edgar_filing
from proxy import ProxyRequest

import logging
logger = logging.getLogger(__name__)

def broker(feed_item, extract_filing=False, zip_folder_contents=True):
    """
    Manages the individual filing extraction process
    """
    logger.info("\n\n\n\n\tStarting Filing Download:\n\n\n")

    logger.info(feed_item.to_dict())

    feed_item = dict(feed_item)

    year_dir = f"{datetime.strptime(feed_item['Date Filed'], '%Y-%m-%d').year}"

    quarter_dir = f"QTR{int((datetime.strptime(feed_item['Date Filed'], '%Y-%m-%d').month - 1) / 3) + 1}"

    output_folderpath = os.path.join(CONFIG.FILING_DIR, year_dir, quarter_dir)

    complete_submission_filing_filepath = os.path.join(output_folderpath, os.path.basename(feed_item['Filename']))

    if not os.path.exists(output_folderpath):
        os.makedirs(output_folderpath)

    if not os.path.exists(complete_submission_filing_filepath):

        g = ProxyRequest()

        g.GET_FILE(feed_item['url'], complete_submission_filing_filepath)

        # todo: celery version of download full
        # consume_complete_submission_filing_txt.delay(feed_item, filepath_cik)

    else:
        logger.info(f"Filepath Already exists\n\t {complete_submission_filing_filepath}")

    if extract_filing and os.path.exists(complete_submission_filing_filepath):

        cik_folder_dir = os.path.basename(feed_item['Filename']).split('.')[0].replace("-", "")

        output_directory = CONFIG.TXT_FILING_DIR.replace("CIK", str(feed_item['CIK'])).replace("FOLDER", cik_folder_dir)

        if os.path.exists(output_directory) and extract_filing and not os.path.exists(output_directory + ".zip"):

            if not os.path.exists(output_directory):
                os.makedirs(output_directory)

            logger.info("\n\n\n\n\tExtracting Filing Documents:\n\n\n\n")

            try:
                contents = edgar_filing.complete_submission_filing(complete_submission_filing_filepath=complete_submission_filing_filepath, output_directory=output_directory, extraction_override=True)
                logger.info(contents)
            except UnicodeDecodeError as E:
                logger.error(f"\n\n\n\nError Decoding \n\n{E}")

            # todo: celery version of download full
            # consume_complete_submission_filing_txt.delay(feed_item, filepath_cik)
            logger.info("\n\n\n\n\tExtraction Complete\n\n\n")

        if os.path.exists(output_directory) and zip_folder_contents:
            shutil.make_archive(output_directory, 'zip', output_directory)
            shutil.rmtree(output_directory)

    logger.info('\n\n\n\tCompleted Filings Download\n\n\n')
