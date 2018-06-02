import os
import platform
import sys
from datetime import datetime

year = datetime.today().year
month = datetime.today().month

latest_folder =  "{}//{}".format(str(year) ,str(month).zfill(2))

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SEC_EDGAR_ARCHIVES_URL = r'https://www.sec.gov/Archives/'

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

# print(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class Config(object):



    if platform.system() == "Windows":
        print("\nRunning Windows OS")
        ROOT_DIR = os.path.abspath(os.sep)
        BASE_DIR = os.path.abspath(os.path.dirname(__file__))
        SECDATA_DIR_ROOT = os.path.dirname(BASE_DIR)

        APP_DIR = os.path.join(SECDATA_DIR_ROOT, 'py_sec_edgar_data')
        SEC_APP_DIR = os.path.join(APP_DIR)
        SEC_GOV_DIR = os.path.join(SECDATA_DIR_ROOT, "sec_gov")

        DATA_DIR = os.path.join(SECDATA_DIR_ROOT, r'data')

        SEC_GOV_EDGAR_DIR = os.path.join(SEC_GOV_DIR, "Archives\edgar")

        OUTPUT_DIR = os.path.join(SEC_GOV_EDGAR_DIR, "data")

        SEC_GOV_EDGAR_FILINGS_DIR = os.path.join(SEC_GOV_EDGAR_DIR, "filings")

        SEC_GOV_TXT_DIR =  os.path.join(SEC_GOV_EDGAR_DIR, "filings")
        SEC_GOV_MONTHLY_DIR = os.path.join(SEC_GOV_EDGAR_DIR, "monthly")
        SEC_GOV_FULL_INDEX_DIR = os.path.join(SEC_GOV_EDGAR_DIR, "full-index")
        SEC_GOV_DAILY_INDEX_DIR = os.path.join(SEC_GOV_EDGAR_DIR, "daily-index")
        SEC_GOV_TXT_LATEST = os.path.join(SEC_GOV_EDGAR_DIR, latest_folder)
        SEC_GOV_XBRL_ZIP_DIR = os.path.join(SEC_GOV_EDGAR_DIR, "xbrl-zip")
        SEC_GOV_XBRL_TXT_DIR = os.path.join(SEC_GOV_EDGAR_DIR, "xbrl")

        dirs_all = [SEC_GOV_EDGAR_DIR,OUTPUT_DIR,SEC_GOV_EDGAR_FILINGS_DIR,SEC_GOV_TXT_DIR,SEC_GOV_MONTHLY_DIR,SEC_GOV_FULL_INDEX_DIR,SEC_GOV_DAILY_INDEX_DIR,SEC_GOV_TXT_LATEST,SEC_GOV_XBRL_TXT_DIR]

        for _ in dirs_all:

            if not os.path.exists(_):
                print("{} Doesn't Exists".format(_))
                print("Creating Directory")
                os.makedirs(_)
            else:
                print("\t SEC Filing Output Directory: \t{}".format(_))

        CONFIG_DIR = os.path.join(SECDATA_DIR_ROOT, "config")

    elif platform.system() == "Linux":
        BASE_DIR = os.path.abspath(os.path.dirname(__file__))

        print("\nRunning on Ubuntu OS")
        ROOT_DIR = os.path.abspath(os.sep)
        SECDATA_DIR_ROOT = os.path.dirname(BASE_DIR)
        SEC_MAIN_DIR = os.path.join(ROOT_DIR, 'py-sec-edgar-data')
        SEC_APP_DIR = os.path.join(SEC_MAIN_DIR, 'py_sec_edgar_data')

        SEC_GOV_DIR = os.path.join(SECDATA_DIR_ROOT)
        DATA_DIR = os.path.join(SECDATA_DIR_ROOT, r'data')
        SEC_GOV_EDGAR_DIR =  os.path.join(SEC_GOV_DIR, "Archives","edgar")
        OUTPUT_DIR = os.path.join(SEC_GOV_EDGAR_DIR, "data")
        SEC_GOV_EDGAR_FILINGS_DIR = os.path.join(SEC_GOV_EDGAR_DIR, "filings")

        SEC_GOV_TXT_DIR =  os.path.join(SEC_GOV_EDGAR_DIR, "filings")
        SEC_GOV_MONTHLY_DIR = os.path.join(SEC_GOV_EDGAR_DIR, "monthly")
        SEC_GOV_FULL_INDEX_DIR = os.path.join(SEC_GOV_EDGAR_DIR, "full-index")
        SEC_GOV_DAILY_INDEX_DIR = os.path.join(SEC_GOV_EDGAR_DIR, "daily-index")
        SEC_GOV_TXT_LATEST = os.path.join(SEC_GOV_EDGAR_DIR, latest_folder)
        SSD_DATA_DIR = os.path.join(SECDATA_DIR_ROOT,'data')

        SEC_GOV_OUTPUT_DIR = os.path.join(SEC_GOV_DIR, 'OUTPUT')

        dirs_all = [SEC_GOV_EDGAR_DIR, OUTPUT_DIR, SEC_GOV_EDGAR_FILINGS_DIR, SEC_GOV_TXT_DIR, SEC_GOV_MONTHLY_DIR, SEC_GOV_FULL_INDEX_DIR, SEC_GOV_DAILY_INDEX_DIR, SEC_GOV_TXT_LATEST, SEC_GOV_OUTPUT_DIR]

        for _ in dirs_all:

            if not os.path.exists(_):
                print("{} Doesn't Exists".format(_))
                print("Creating Directory")
                os.makedirs(_)
            else:
                print("\t SEC Filing Output Directory: \t{}".format(_))

        ELASTIC = "localhost:5601"
        CONFIG_DIR = os.path.join(SECDATA_DIR_ROOT, "config")

    tickercheck = os.path.join(DATA_DIR, "TICKERCHECK_CIK_COMPANIES_ONLY.xlsx")
    monthly_urls = os.path.join(DATA_DIR, "sec_gov_archives_edgar_monthly_xbrl_urls.xlsx.xlsx")

