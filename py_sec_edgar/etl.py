
import os
from pprint import pprint
import shutil


import filing as edgar_filing

from settings import CONFIG
from proxy import ProxyRequest


def broker(feed_item, extract_filing=True, zip_folder_contents=True):
    """
    Manages the individual filing extraction process
    """
    pprint(feed_item.to_dict())
    feed_item = dict(feed_item)
    folder_dir = os.path.basename(feed_item['Filename']).split('.')[0].replace("-", "")
    folder_path_cik = CONFIG.TXT_FILING_DIR.replace("CIK", str(feed_item['CIK'])).replace("FOLDER", folder_dir)
    filepath_feed_item = os.path.join(folder_path_cik, os.path.basename(feed_item['Filename']))

    if not os.path.exists(folder_path_cik) and not os.path.exists(folder_path_cik + ".zip"):

        if not os.path.exists(folder_path_cik):
            os.makedirs(folder_path_cik)

        g = ProxyRequest()

        g.GET_FILE(feed_item['url'], filepath_feed_item)

        # todo: celery version of download full
        # consume_complete_submission_filing_txt.delay(feed_item, filepath_cik)

    else:
        print("Filepath Already exists\n\t {}".format(filepath_feed_item))

    if os.path.exists(folder_path_cik) and extract_filing and not os.path.exists(folder_path_cik + ".zip"):

        print("\n\tExtracting Filing Documents:\n")
        try:
            contents = edgar_filing.complete_submission_filing(input_filepath=filepath_feed_item, output_directory=folder_path_cik, extraction_override=True)
            print(contents)
        except UnicodeDecodeError:
            print("Error Decoding")

        # todo: celery version of download full
        # consume_complete_submission_filing_txt.delay(feed_item, filepath_cik)
        print("\n\tExtraction Complete\n")

    if os.path.exists(folder_path_cik) and zip_folder_contents:
        shutil.make_archive(folder_path_cik, 'zip', folder_path_cik)
        shutil.rmtree(folder_path_cik)
