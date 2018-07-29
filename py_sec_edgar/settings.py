from datetime import datetime

from .folders import Folders

from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

year = datetime.today().year
month = datetime.today().month

latest_folder = "{}//{}".format(str(year), str(month).zfill(2))

SEC_EDGAR_ARCHIVES_URL = r'https://www.sec.gov/Archives/'

class Config(Folders):

    # extract all contents from txt file
    extract_filing_contents = False

    # for complete list see py-sec-edgar/refdata/filing_types.xlsx
    forms_list = ['10-K', '20-F', '10-K/A']

    # the urls of all filings are stored in index files
    # so need to download these index files
    # below just says download all of them
    index_start_date = "1/1/1993"
    index_end_date = datetime.now().strftime("%m/%d/%Y")

    # file with list of all filings for given period
    index_files = ['master.idx']

    # https://www.perfect-privacy.com/
    # allows 30 simultaneous connections
    # if going to use proxy, please only download on the weekends
    VPN_PROVIDER = "PP"
