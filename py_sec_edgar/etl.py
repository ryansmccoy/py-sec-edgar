
import os
from datetime import datetime
import shutil

from settings import CONFIG
import filing as edgar_filing
from proxy import ProxyRequest

import logging
logger = logging.getLogger(__name__)

def broker(feed_item, extract_filing_contents=False):
    """
    Manages the individual filing extraction process
    """

    feed_item = prepare_filepaths(feed_item)

    feed_item = download_filing(feed_item)

    if extract_filing_contents:

        feed_item = extract_contents(feed_item)

def prepare_filepaths(feed_item):
    """
    Sets parameters needed for various aspects

    feed_item['year_dir'] = '2019'
    feed_item['quarter_dir'] = 'QTR1'
    feed_item['output_folderpath'] = 'C:\\sec_gov\\Archives\\edgar\\filings\\2019\\QTR1'
    feed_item['filing_filepath'] = 'C:\\sec_gov\\Archives\\edgar\\filings\\2019\\QTR1\\0001694665-19-000013.txt'
    feed_item['filing_directory'] = 'C:\\sec_gov\\Archives\\edgar\\data\\1694665\\'
    feed_item['filing_path'] = 'C:\\sec_gov\\Archives\\edgar\\data\\1694665\\0001694665-19-000013.txt'
    feed_item['cik_folder_dir'] = '000169466519000013'
    feed_item['extracted_filing_directory'] = 'C:\\sec_gov\\Archives\\edgar\\data\\1694665\\000169466519000013'

    :param feed_item:
    :return: feed_item:
    """

    feed_item = dict(feed_item)
    feed_item['year_dir'] = f"{datetime.strptime(feed_item['Date Filed'], '%Y-%m-%d').year}"
    feed_item['quarter_dir'] = f"QTR{int((datetime.strptime(feed_item['Date Filed'], '%Y-%m-%d').month - 1) / 3) + 1}"
    feed_item['output_folderpath'] = os.path.join(CONFIG.FILING_DIR, feed_item['year_dir'], feed_item['quarter_dir'])
    feed_item['filing_filepath'] = os.path.join(feed_item['output_folderpath'], os.path.basename(feed_item['Filename']))
    feed_item['filing_directory'] = CONFIG.TXT_FILING_DIR.replace("CIK", str(feed_item['CIK'])).replace("FOLDER", "")
    feed_item['filing_path'] = os.path.join(feed_item['filing_directory'], os.path.basename(feed_item['Filename']))
    feed_item['cik_folder_dir'] = os.path.basename(feed_item['Filename']).split('.')[0].replace("-", "")
    feed_item['extracted_filing_directory'] = CONFIG.TXT_FILING_DIR.replace("CIK", str(feed_item['CIK'])).replace("FOLDER", feed_item['cik_folder_dir'])

    return feed_item

def download_filing(feed_item, zip_contents=True):

    if not os.path.exists(feed_item['filing_directory']):

        os.makedirs(feed_item['filing_directory'])
        logger.info(f"\n\nCreating Folder\n\t {feed_item['filing_path']}\n\n")

    if not os.path.exists(feed_item['filing_filepath']) and not os.path.exists(feed_item['filing_path']):

        logger.info(f"\n\n\tStarting Filing Download: \t{feed_item}\n\n")

        g = ProxyRequest()

        g.GET_FILE(feed_item['url'], feed_item['filing_path'])

        # todo: celery version of download full
        # consume_complete_submission_filing_txt.delay(feed_item, filepath_cik)

        logger.info('\n\n\n\tCompleted Filings Download\n\n\n')

    elif os.path.exists(feed_item['filing_filepath']) and not os.path.exists(feed_item['filing_path']):

        logger.info(f"\n\nFilepath Already exists, Moving\t {feed_item['filing_filepath']}\n\n")

        shutil.move(feed_item['filing_filepath'], feed_item['filing_path'])

        logger.info(f"\n\nNew Filepath \t {feed_item['filing_path']}\n\n")

    elif os.path.exists(feed_item['filing_filepath']) and os.path.exists(feed_item['filing_path']):

        logger.info(f"\n\nFilepath Already exists Deleting\n\t {feed_item['filing_filepath']}\n\n")

        os.remove(feed_item['filing_filepath'])

    elif not os.path.exists(feed_item['filing_filepath']) and os.path.exists(feed_item['filing_path']):

        logger.info(f"\n\nFilepath Already exists\t {feed_item['filing_path']}\n\n")
    else:
        logger.info(f"\n\nSomething Might be wrong\t {feed_item['filing_path']}\n\n")

    if zip_contents:
        shutil.make_archive(feed_item['output_directory'], 'zip', feed_item['output_directory'])

    return feed_item

def extract_contents(feed_item, zip_contents=True):

    if os.path.exists(feed_item['extracted_filing_directory']):

        if not os.path.exists(feed_item['filing_directory']):
            os.makedirs(feed_item['filing_directory'])
            logger.info(f"\n\nCreating Folder\n\t {feed_item['filing_path']}")

        if os.path.exists(feed_item['output_directory']) and not os.path.exists(feed_item['output_directory'] + ".zip"):

            if not os.path.exists(feed_item['output_directory']):
                os.makedirs(feed_item['output_directory'])

            logger.info("\n\n\n\n\tExtracting Filing Documents:\n")

            try:
                contents = edgar_filing.complete_submission_filing(feed_item['filing_filepath'], output_directory=feed_item['output_directory'], extraction_override=True)
                logger.info(contents)
            except UnicodeDecodeError as E:
                logger.error(f"\n\n\n\nError Decoding \n\n{E}")

            # todo: celery version of download full
            # consume_complete_submission_filing_txt.delay(feed_item, filepath_cik)
            logger.info("\n\n\n\n\tExtraction Complete\n")

        if os.path.exists(feed_item['output_directory']) and zip_contents:
            shutil.make_archive(feed_item['output_directory'], 'zip', feed_item['output_directory'])
            shutil.rmtree(feed_item['output_directory'])






