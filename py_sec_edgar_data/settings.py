import os
import platform
import sys
from datetime import datetime

year = datetime.today().year
month = datetime.today().month

latest_folder =  "{}/{}".format(str(year) ,str(month).zfill(2))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SEC_EDGAR_ARCHIVES_URL = r'https://www.sec.gov/Archives/'

# print(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if platform.system() == "Windows":
    print("\nRunning Windows OS")
    ROOT_DIR = os.path.abspath(os.sep)

    SECDATA_DIR_ROOT = os.path.join(ROOT_DIR, 'py-sec-edgar-data')
    APP_DIR = os.path.join(SECDATA_DIR_ROOT, 'py_sec_edgar_data')
    SEC_APP_DIR = os.path.join(APP_DIR, 'sec_data')

    SEC_GOV_DIR = os.path.join(SECDATA_DIR_ROOT, "sec_gov")

    DATA_DIR = os.path.join(SEC_GOV_DIR, r'DATA')
    SSD_DATA_DIR = os.path.join(r'B:\DATA')
    SEC_GOV_EDGAR_DIR = os.path.join(SEC_GOV_DIR, "Archives\edgar")
    OUTPUT_DIR = os.path.join(SEC_GOV_EDGAR_DIR, "DATA")

    SEC_GOV_EDGAR_FILINGS_DIR = os.path.join(SEC_GOV_EDGAR_DIR, "filings")

    SEC_GOV_TXT_DIR =  os.path.join(SEC_GOV_EDGAR_DIR, "filings")
    SEC_GOV_MONTHLY_DIR = os.path.join(SEC_GOV_EDGAR_DIR, "monthly")
    SEC_GOV_FULL_INDEX_DIR = os.path.join(SEC_GOV_EDGAR_DIR, "full-index")
    SEC_GOV_DAILY_INDEX_DIR = os.path.join(SEC_GOV_EDGAR_DIR, "daily-index")
    SEC_GOV_TXT_LATEST = os.path.join(SEC_GOV_EDGAR_DIR, latest_folder)

    SEC_GOV_OUTPUT_DIR = os.path.join(SEC_GOV_DIR, 'OUTPUT')

    if not os.path.exists(SEC_GOV_OUTPUT_DIR):
        print("{} Doesn't Exists".format(SEC_GOV_OUTPUT_DIR))
        print("Creating Directory")
        os.makedirs(SEC_GOV_OUTPUT_DIR)
    else:
        print("\t SEC Filing Output Directory: \t{}".format(SEC_GOV_OUTPUT_DIR))

    CONFIG_DIR = os.path.join(SEC_APP_DIR, "edgar_config")

if platform.system() == "Linux":

    print("\nRunning on Ubuntu OS")
    ROOT_DIR = os.path.abspath(os.sep)
    SECDATA_DIR_ROOT = os.path.join(ROOT_DIR, 'home/ryan/SECDATA')
    SEC_MAIN_DIR = os.path.join(SECDATA_DIR_ROOT, 'sec-data-python')
    SEC_APP_DIR = os.path.join(SEC_MAIN_DIR, 'sec_data')

    SEC_GOV_DIR = os.path.join(SECDATA_DIR_ROOT, "sec_gov")
    DATA_DIR = os.path.join(SEC_GOV_DIR, r'DATA')
    OUTPUT_DIR = os.path.join(SEC_GOV_DIR, 'OUTPUT')
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

    if not os.path.exists(SEC_GOV_OUTPUT_DIR):
        print("{} Doesn't Exists".format(SEC_GOV_OUTPUT_DIR))
        print("Creating Directory")
        os.makedirs(SEC_GOV_OUTPUT_DIR)
    else:
        print("\t SEC Filing Output Directory: \t{}".format(SEC_GOV_OUTPUT_DIR))

    ELASTIC = "localhost:5601"
    CONFIG_DIR = os.path.join(SEC_APP_DIR, "edgar_config")
