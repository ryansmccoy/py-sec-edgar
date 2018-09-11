Python SEC Edgar
=============

Python package used to download complete submission filings from the sec.gov/edgar website.


Features:
 - Filter by Ticker
 - Filter by Form Type
 - Proxy

# Quick Start Guides

#### Setup Environment:

    conda create -n py-sec-edgar python=3.6 pandas numpy lxml -y
    activate py-sec-edgar
    pip install -r requirements/requirements_dev.txt

#### Configure Settings (Optional):

py-sec-edgar/py_sec_edgar/settings.py

    # for complete list see py-sec-edgar/refdata/filing_types.xlsx
    # to filter against specific forms, add to list

    forms_list = ['10-K', '20-F']

    # the urls of all filings are stored in index files
    # so need to download these index files
    # below just says download all of them

    start_date = "1/1/1993"
    end_date = "1/1/2020"

#### Configure Tickers (Optional):

py-sec-edgar/py_sec_edgar/tickers.csv

    AAPL
    MSFT
    BRK.B
    XOM
    GOOGL
    WFC

#### Configure Proxy (Optional):

rename .env.template to .env

py-sec-edgar/py_sec_edgar/.env

    # perfect-privacy.com
    USERNAME=user@domain.com
    PASSWORD=password


#### Run Example:

    python py_sec_edgar/example.py

#### Output Example:

    Starting Index Download:

        Downloading Latest https://www.sec.gov/Archives/edgar/full-index/master.idx

        Downloading: 	https://www.sec.gov/Archives/edgar/full-index/master.idx
        Saving to: 	C:\sec_gov\Archives\edgar\full-index\master.idx
        Selected User-Agent:	{'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.98 Safari/537.36'}
        Success!	Saved to filepath:	C:\sec_gov\Archives\edgar\full-index\master.idx

    Completed Index Download

    Starting Filings Download:

        CIK                                                         80424
        Company Name                                  PROCTER & GAMBLE Co
        Form Type                                                    10-K
        Date Filed                                             2018-08-07
        Filename                edgar/data/80424/0000080424-18-000055.txt
        published                                              2018-08-07
        url             https://www.sec.gov/Archives/edgar/data/80424/...

        Downloading: 	https://www.sec.gov/Archives/edgar/data/80424/0000080424-18-000055.txt
        Saving to: 	C:\sec_gov\Archives\edgar\data\80424\000008042418000055\0000080424-18-000055.txt
        Selected User-Agent:	{'User-Agent': 'Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36'}
        Success!	Saved to filepath:	C:\sec_gov\Archives\edgar\data\80424\000008042418000055\0000080424-18-000055.txt

    Complete Filings Download

    Extracting Filing Documents:

        Path:  C:\sec_gov\Archives\edgar\data\80424\000008042418000055

                       GROUP                                 KEY                                              VALUE
        1       COMPANY DATA      0000080424-18-000055.hdr.sgml                                            20180807
        2       COMPANY DATA               <acceptance-datetime>                                     20180807161922
        4       COMPANY DATA                    ACCESSION NUMBER                               0000080424-18-000055
        5       COMPANY DATA           CONFORMED SUBMISSION TYPE                                               10-K
        6       COMPANY DATA               PUBLIC DOCUMENT COUNT                                                136
        7       COMPANY DATA          CONFORMED PERIOD OF REPORT                                           20180630
        8       COMPANY DATA                    FILED AS OF DATE                                           20180807
        9       COMPANY DATA                   DATE AS OF CHANGE                                           20180807
        14      COMPANY DATA              COMPANY CONFORMED NAME                                PROCTER & GAMBLE Co
        15      COMPANY DATA                   CENTRAL INDEX KEY                                         0000080424
        16      COMPANY DATA  STANDARD INDUSTRIAL CLASSIFICATION  SOAP, DETERGENT, CLEANING PREPARATIONS, PERFUM...
        17      COMPANY DATA                          IRS NUMBER                                          310411980
        18      COMPANY DATA              STATE OF INCORPORATION                                                 OH
        19      COMPANY DATA                     FISCAL YEAR END                                               0630
        22     FILING VALUES                           FORM TYPE                                               10-K
        23     FILING VALUES                             SEC ACT                                           1934 Act
        24     FILING VALUES                     SEC FILE NUMBER                                          001-00434
        25     FILING VALUES                         FILM NUMBER                                           18998362
        28  BUSINESS ADDRESS                            STREET 1                         ONE PROCTER & GAMBLE PLAZA
        29  BUSINESS ADDRESS                                CITY                                         CINCINNATI
        30  BUSINESS ADDRESS                               STATE                                                 OH
        31  BUSINESS ADDRESS                                 ZIP                                              45202
        32  BUSINESS ADDRESS                      BUSINESS PHONE                                         5139831100
        35      MAIL ADDRESS                            STREET 1                         ONE PROCTER & GAMBLE PLAZA
        36      MAIL ADDRESS                                CITY                                         CINCINNATI
        37      MAIL ADDRESS                               STATE                                                 OH
        38      MAIL ADDRESS                                 ZIP                                              45202
        41    FORMER COMPANY               FORMER CONFORMED NAME                                PROCTER & GAMBLE CO
        42    FORMER COMPANY                 DATE OF NAME CHANGE                                           19920703

    Extraction Complete





# Alright, what did I just do?
 - Create folder structure which mimics sec.gov website structure (see "Paths and Directory Structure" below)
 - Download the necessary idx files and merge them into combined file (fyi 1.9 GB csv)
 - load tickers from tickers.csv file and filters them
 - load forms from settings.py file and filters them
 - filter against forms set in settings.py file, and will then start downloading the individual filings for the tickers in the tickers.csv file.


##### Paths and Directory Structure

   sec.gov website:

    https://www.sec.gov/

    https://www.sec.gov/Archives/edgar/full-index/ <- path where "index" files are located

    https://www.sec.gov/Archives/edgar/full-index/2018/QTR1/master.idx <- EDGAR Index Files are tab delimted txt files

    https://www.sec.gov/Archives/edgar/data/ <- path where all the actual filings are stored

    https://www.sec.gov/Archives/edgar/data/1041588/0001041588-18-000005.txt <- these are the complete submission file

    https://www.sec.gov/Archives/edgar/data/<CIK>/<ACCESSION_NUMBER_WITHOUT_DASHES>/<ACCESSION_NUMBER>.txt <-  follows this format

local folder equivalent:

    C:\sec_gov\

    C:\sec_gov\Archives\edgar\full-index\ <- path where "index" files are located

    c:\sec_gov\Archives\edgar\full-index\2018\QTR1\master.idx <- EDGAR Index Files are tab delimted txt files

    c:\sec_gov\Archives\edgar\data\ <- path where all the actual filings are stored

    c:\sec_gov\Archives\edgar\data\1041588\000104158818000005\0001041588-18-000005.txt <- these are the complete submission file

    c:\sec_gov\Archives\edgar\data\<CIK>\<ACCESSION_NUMBER_WITHOUT_DASHES>\<ACCESSION_NUMBER>.txt <-  follow this format


Central Index Key (CIK)
-----------------------
The CIK is the unique numerical identifier assigned by the EDGAR system to filers when they sign up to make filings to the SEC. CIK numbers remain unique to the filer; they are not recycled.

Accession Number
---------------
In the example above, "0001193125-15-118890" is the "accession number," a unique identifier assigned automatically to an accepted submission by the EDGAR Filer System. The first set of numbers (0001193125) is the CIK of the entity submitting the filing. This could be the company or a third-party filer agent. Some filer agents without a regulatory requirement to make disclosure filings with the SEC have a CIK but no searchable presence in the public EDGAR database. The next 2 numbers (15) represent the year. The last series of numbers represent a sequential count of submitted filings from that CIK. The count is usually, but not always, reset to 0 at the start of each calendar year.



Filings Statistics
------------------

    Form 4        6,420,154
    8-K	 1,473,193
    10-K	   180,787
    10-Q	   552,059
    13F-HR	   224,996
    S-1	    21,366
    ------------------
    Total         17,492,303


Download Time Estimates
-----------------------

	 180,787        10-K filings
            8       seconds on average to download single filing
     ------------------
     1,446,296 	    seconds
	 24,104.93 	    minutes
	 401.75 	    hours
     ------------------
	 16.74 	        days to download all 10-K filings via 1 connection


# Todo
 * need to figure out way to quickly access downloaded content
