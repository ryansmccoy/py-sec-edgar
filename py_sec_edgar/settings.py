from datetime import datetime
from py_sec_edgar import Folders

class Config(Folders):

    # extract all contents from txt file
    extract_filing_contents = False

    # for complete list see py-sec-edgar/refdata/filing_types.xlsx
    forms_list = ['10-K', '20-F', '10-K/A']
    # forms_list = ['497', '497K']
    # forms_list = ['8-K']
    # the urls of all broker are stored in index files
    # so need to download these index files
    # below just says download all of them
    # index_start_date = "1/1/1993"
    index_start_date = "1/1/2019"

    index_end_date = datetime.now().strftime("%m/%d/%Y")

    # file with list of all broker for given period
    index_files = ['master.idx']

    # https://www.perfect-privacy.com/
    # allows 30 simultaneous connections
    # if going to use proxy, please only download on the weekends
    VPN_PROVIDER = "PP"



CONFIG = Config()
