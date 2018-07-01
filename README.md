Python SEC Edgar Data (Currently Under Developement)
=============

Python package used to download filings from the sec.gov/edgar website, which through Q3/2017 contains 16,867,734 filings.


Using this Repo
---------------

    pip install -r requirements/requirements_dev.txt

### Run

Bash (Work in Progress)

    python py_sec_edgar_data/cli_full_index.py

Docker (Work in Progress)

    $  docker run -d -p 5672:5672 -p 15672:15672 --name sec-rabbit rabbitmq:management
    $  celery -A edgar_download.celery_download_complete_submission_filing worker --loglevel=info

### Download Folder Structure
---------------

https://www.sec.gov/Archives/edgar/full-index/ <- path where the urls for all the filings are located

    https://www.sec.gov/Archives/edgar/full-index/2018/QTR1/master.idx

files will be downloaded to:

    c:\sec_gov\Archives\edgar\full-index\2018\QTR1\master.idx


https://www.sec.gov/Archives/edgar/data/ <- path where all the filings are stored

    https://www.sec.gov/Archives/edgar/data/1041588/0001041588-18-000005.txt

files will be downloaded to:

    c:\sec_gov\Archives\edgar\data\1041588\000104158818000005\0001041588-18-000005.txt
