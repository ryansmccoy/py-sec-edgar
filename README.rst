Python SEC Edgar
================

A Python package used to download complete submission filings from the
sec.gov/edgar website.

Features
--------
* Filter by Ticker
* Filter by Form Type
* Extract contents of Complete Submission Filing

Quick Start Guide
-----------------

Setup Environment (Windows)
~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

   git clone https://github.com/ryansmccoy/py-sec-edgar.git
   cd py-sec-edgar
   conda create -n py-sec-edgar python=3.6 pandas numpy lxml -y
   activate py-sec-edgar
   pip install -r requirements.txt

Setup Environment (Linux):
~~~~~~~~~~~~~~~~~~~~~~~~~~

::

   git clone https://github.com/ryansmccoy/py-sec-edgar.git
   cd py-sec-edgar
   conda create -n py-sec-edgar python=3.6 pandas numpy lxml -y
   source activate py-sec-edgar
   sudo mkdir /sec_gov
   sudo chown -R $USER:$USER /sec_gov
   pip install -r requirements.txt

Configure Settings (Optional):
-------------------------------

Specify Form Types, Start, and End Dates:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

   # py-sec-edgar/py_sec_edgar/settings.py

   # complete list @ py-sec-edgar/refdata/filing_types.xlsx

   forms_list = ['10-K', '20-F']

   # the urls of all filings are stored in index files
   # so need to download these index files
   # below just says download all of them

   start_date = "1/1/2018"
   end_date = "1/1/2020"

Specify Tickers:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

   # py-sec-edgar/refdata/tickers.csv

   AAPL
   MSFT
   BRK.B
   XOM
   GOOGL
   WFC


Run Example:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: console

    # python py_sec_edgar/run.py


Output:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

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
    Success!

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

                            FILENAME        TYPE SEQUENCE                                        DESCRIPTION                                    OUTPUT_FILEPATH                                  RELATIVE_FILEPATH                               DESCRIPTIVE_FILEPATH FILE_SIZE  FILE_SIZE_BYTES
    1             fy171810-kreport.htm        10-K        1                                        FY1718 10-K  C:\sec_gov\Archives\edgar\data\80424\000008042...  000008042418000055\FILES\0001-(10-K)_FY1718_10...       0001-(10-K)_FY1718_10-K_fy171810-kreport.htm    3.8 MB          4026348
    2        fy171810-kexhibit10x1.htm     EX-10.1        2  THE P&G 2001 STOCK AND INCENTIVE COMPENSATION ...  C:\sec_gov\Archives\edgar\data\80424\000008042...  000008042418000055\FILES\0002-(EX-10.1)_THE_PG...  0002-(EX-10.1)_THE_PG_2001_STOCK_AND_INCENTIVE...   98.1 KB           100409
    3        fy171810-kexhibit10x2.htm     EX-10.2        3                            THE P&G 1992 STOCK PLAN  C:\sec_gov\Archives\edgar\data\80424\000008042...  000008042418000055\FILES\0003-(EX-10.2)_THE_PG...  0003-(EX-10.2)_THE_PG_1992_STOCK_PLAN_fy171810...   82.9 KB            84925
    4        fy171810-kexhibit10x3.htm     EX-10.3        4      THE P&G EXECUTIVE GROUP LIFE INSURANCE POLICY  C:\sec_gov\Archives\edgar\data\80424\000008042...  000008042418000055\FILES\0004-(EX-10.3)_THE_PG...  0004-(EX-10.3)_THE_PG_EXECUTIVE_GROUP_LIFE_INS...  194.9 KB           199603
    5        fy171810-kexhibit10x5.htm     EX-10.5        5    THE P&G 1993 NON-EMPLOYEE DIRECTORS' STOCK PLAN  C:\sec_gov\Archives\edgar\data\80424\000008042...  000008042418000055\FILES\0005-(EX-10.5)_THE_PG...  0005-(EX-10.5)_THE_PG_1993_NON-EMPLOYEE_DIRECT...   35.0 KB            35863
    6        fy171810-kexhibit10x8.htm     EX-10.8        6    THE P&G 2003 NON-EMPLOYEE DIRECTORS' STOCK PLAN  C:\sec_gov\Archives\edgar\data\80424\000008042...  000008042418000055\FILES\0006-(EX-10.8)_THE_PG...  0006-(EX-10.8)_THE_PG_2003_NON-EMPLOYEE_DIRECT...   83.9 KB            85907
    7       fy171810-kexhibit10x10.htm    EX-10.10        7  SUMMARY OF THE COMPANY'S SHORT TERM ACHIEVEMEN...  C:\sec_gov\Archives\edgar\data\80424\000008042...  000008042418000055\FILES\0007-(EX-10.10)_SUMMA...  0007-(EX-10.10)_SUMMARY_OF_THE_COMPANYS_SHORT_...   27.0 KB            27625
    ...
    ...
    129                       R105.htm         XML      129                                IDEA: XBRL DOCUMENT  C:\sec_gov\Archives\edgar\data\80424\000008042...  000008042418000055\FILES\0129-(XML)_IDEA_XBRL_...             0129-(XML)_IDEA_XBRL_DOCUMENT_R105.htm   31.4 KB            32107
    130                       R106.htm         XML      130                                IDEA: XBRL DOCUMENT  C:\sec_gov\Archives\edgar\data\80424\000008042...  000008042418000055\FILES\0130-(XML)_IDEA_XBRL_...             0130-(XML)_IDEA_XBRL_DOCUMENT_R106.htm   40.0 KB            41005
    131          Financial_Report.xlsx       EXCEL      131                                IDEA: XBRL DOCUMENT  C:\sec_gov\Archives\edgar\data\80424\000008042...  000008042418000055\FILES\0130-(XML)_IDEA_XBRL_...             0130-(XML)_IDEA_XBRL_DOCUMENT_R106.htm  205.9 KB           210825
    132                        Show.js         XML      132                                IDEA: XBRL DOCUMENT  C:\sec_gov\Archives\edgar\data\80424\000008042...  000008042418000055\FILES\0132-(XML)_IDEA_XBRL_...              0132-(XML)_IDEA_XBRL_DOCUMENT_Show.js    1.3 KB             1366
    133                     report.css         XML      133                                IDEA: XBRL DOCUMENT  C:\sec_gov\Archives\edgar\data\80424\000008042...  000008042418000055\FILES\0133-(XML)_IDEA_XBRL_...           0133-(XML)_IDEA_XBRL_DOCUMENT_report.css    2.8 KB             2866
    134              FilingSummary.xml         XML      135                                IDEA: XBRL DOCUMENT  C:\sec_gov\Archives\edgar\data\80424\000008042...  000008042418000055\FILES\0135-(XML)_IDEA_XBRL_...    0135-(XML)_IDEA_XBRL_DOCUMENT_FilingSummary.xml   69.1 KB            70718
    135                 MetaLinks.json        JSON      137                                IDEA: XBRL DOCUMENT  C:\sec_gov\Archives\edgar\data\80424\000008042...  000008042418000055\FILES\0137-(JSON)_IDEA_XBRL...      0137-(JSON)_IDEA_XBRL_DOCUMENT_MetaLinks.json    1.0 MB          1054848
    136  0000080424-18-000055-xbrl.zip         ZIP      138                                IDEA: XBRL DOCUMENT  C:\sec_gov\Archives\edgar\data\80424\000008042...  000008042418000055\FILES\0137-(JSON)_IDEA_XBRL...      0137-(JSON)_IDEA_XBRL_DOCUMENT_MetaLinks.json  912.6 KB           934458

    Extraction Complete

Alright, what did I just do?
============================

-  Created folder structure which mimics sec.gov website structure (see "Paths and Directory Structure" below)
-  Downloaded the necessary idx files (files containing the links to the sec filings) and merge them into combined file (fyi 1.9 GB csv)
-  loaded tickers from tickers.csv file and filters them
-  load forms from settings.py file and filters them
-  filter against forms set in settings.py file, and will then start downloading the individual filings for the tickers in the tickers.csv file.

Paths and Directory Structure


sec.gov website:

::

    https://www.sec.gov/

    https://www.sec.gov/Archives/edgar/full-index/ <- path where "index" files are located

    https://www.sec.gov/Archives/edgar/full-index/2018/QTR1/master.idx <- EDGAR Index Files are tab delimted txt files

    https://www.sec.gov/Archives/edgar/data/ <- path where all the actual filings are stored

    https://www.sec.gov/Archives/edgar/data/1041588/0001041588-18-000005.txt <- these are the complete submission file

    https://www.sec.gov/Archives/edgar/data/<CIK>/<ACCESSION_NUMBER_WITHOUT_DASHES>/<ACCESSION_NUMBER>.txt <-  follows this format

local folder equivalent:

::

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
----------------

In the example above, "0001193125-15-118890" is the "accession number," a unique identifier assigned automatically to an accepted submission by the EDGAR Filer System. The first set of numbers (0001193125) is the CIK of the entity submitting the filing. This could be the company or a third-party filer agent. Some filer agents without a regulatory requirement to make disclosure filings with the SEC have a CIK but no searchable presence in the public EDGAR database. The next 2 numbers (15) represent the year. The last series of numbers represent a sequential count of submitted filings from that CIK. The count is usually, but not always, reset to 0 at the start of each calendar year.

Filings Statistics
------------------

::

    Form 4        6,420,154  (Ownership)
    8-K           1,473,193  (Press Releases)
    10-K          180,787    (Annual Report)
    10-Q          552,059    (Quarterly Report)
    13F-HR        224,996    (Investment Fund Holdings)
    S-1           21,366     (IPO offering)
    ------------------
    Total         17,492,303

Download Time Estimates
-----------------------

::

     180,787        10-K filings
            8       seconds on average to download single filing
     ------------------
     1,446,296      seconds
     24,104.93      minutes
     401.75         hours
     ------------------
     16.74          days to download all 10-K filings via 1 connection

Todo
====

-  Feeds

   -  Make Full-Index more efficient
   -  Incorporate RSS Feed

-  Add Celery
-  need to figure out way to quickly access downloaded content
-  extract earnings data from 8-K
-  setup proper logging instead of print
-  add tests
