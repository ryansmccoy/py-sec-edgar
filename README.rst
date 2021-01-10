Python SEC Edgar
================

A Python application used to download and parse complete submission filings from the sec.gov/edgar website.  The goal for this project is to make it easy to get filings from the SEC website onto your computer for the companies and forms you desire.

A few hurdles that I've tried to ease with this project:

* CIK to Ticker Equivalent - probably the biggest hurdle is just figuring out the CIK for the company you want.  I've tried to bypass this via a reference file mapping CIK to tickers.  I'm sure there is a better way, but for now it seems to work.

* Organizing the Data - I decided to keep it simple and organize the data similar to the SEC Edgar website (which is explained below)

Features
--------
* Filter by Ticker
* Filter by Form Type
* Extract contents of Complete Submission Filing

Quick Start Guide
--------------------

Setup Environment (Windows)
~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

   git clone https://github.com/ryansmccoy/py-sec-edgar.git
   cd py-sec-edgar
   conda create -n py-sec-edgar python=3.8 pandas numpy lxml -y
   activate py-sec-edgar
   pip install -r requirements.txt

Setup Environment (Linux):
~~~~~~~~~~~~~~~~~~~~~~~~~~

::

   git clone https://github.com/ryansmccoy/py-sec-edgar.git
   cd py-sec-edgar
   conda create -n py-sec-edgar python=3.8 pandas numpy lxml -y
   source activate py-sec-edgar
   sudo mkdir /sec_gov
   sudo chown -R $USER:$USER /sec_gov
   pip install -r requirements.txt

Configure Settings (Optional)
-------------------------------

    # py-sec-edgar/py_sec_edgar/settings.py

Extracting Contents from Complete Submission Filing:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    # extract all contents from txt file
    # Set this to True and everything will be extracted from Complete Submission Filing
    # Note:  There is a lot of content in these filings, so be prepared

    extract_filing_contents = False

Specify Form Types, Start, and End Dates:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::


   # complete list @ py-sec-edgar/refdata/filing_types.xlsx

   forms_list = ['10-K', '20-F']

   # the urls of all filings are stored in index files
   # so need to download these index files
   # below just says download all of them

   start_date = "1/1/2018"
   end_date = "1/1/2025"

Specify Tickers:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

   # py-sec-edgar/refdata/tickers.csv

   AAPL
   MSFT
   XOM
   GOOGL
   WFC


Run Application
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: console

    $ cd py-sec-edgar
    $ python py_sec_edgar

Above, is the same as running (See notes at top of __main__.py file for explanation):

.. code-block:: console

    $ cd py-sec-edgar
    $ python py_sec_edgar/__main__.py


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
    CIK                                                         72971
    Company Name                             WELLS FARGO & COMPANY/MN
    Form Type                                                    10-K
    Date Filed                                             2019-02-27
    Filename                edgar/data/72971/0000072971-19-000227.txt
    published                                              2019-02-27
    url             https://www.sec.gov/Archives/edgar/data/72971/...
    Name: 103670, dtype: object
    2019-05-01 14:14:49,841 ERROR py_sec_edgar.filing: Filing Already Exists
    2019-05-01 14:14:51,844 INFO py_sec_edgar.filing: Filing Loaded
    2019-05-01 14:14:55,613 INFO py_sec_edgar.filing: Filing Lxml

                   GROUP                                 KEY                             VALUE
    1       COMPANY DATA      0000072971-19-000227.hdr.sgml                           20190227
    2       COMPANY DATA               <acceptance-datetime>                    20190227152351
    4       COMPANY DATA                    ACCESSION NUMBER              0000072971-19-000227
    5       COMPANY DATA           CONFORMED SUBMISSION TYPE                              10-K
    6       COMPANY DATA               PUBLIC DOCUMENT COUNT                               211
    7       COMPANY DATA          CONFORMED PERIOD OF REPORT                          20181231
    8       COMPANY DATA                    FILED AS OF DATE                          20190227
    9       COMPANY DATA                   DATE AS OF CHANGE                          20190227
    14      COMPANY DATA              COMPANY CONFORMED NAME          WELLS FARGO & COMPANY/MN
    15      COMPANY DATA                   CENTRAL INDEX KEY                        0000072971
    16      COMPANY DATA  STANDARD INDUSTRIAL CLASSIFICATION  NATIONAL COMMERCIAL BANKS [6021]
    17      COMPANY DATA                          IRS NUMBER                         410449260
    18      COMPANY DATA              STATE OF INCORPORATION                                DE
    19      COMPANY DATA                     FISCAL YEAR END                              1231
    22     FILING VALUES                           FORM TYPE                              10-K
    23     FILING VALUES                             SEC ACT                          1934 Act
    24     FILING VALUES                     SEC FILE NUMBER                         001-02979
    25     FILING VALUES                         FILM NUMBER                          19637386
    28  BUSINESS ADDRESS                            STREET 1             420 MONTGOMERY STREET
    29  BUSINESS ADDRESS                                CITY                     SAN FRANCISCO
    30  BUSINESS ADDRESS                               STATE                                CA
    31  BUSINESS ADDRESS                                 ZIP                             94163
    32  BUSINESS ADDRESS                      BUSINESS PHONE                        6126671234
    35      MAIL ADDRESS                            STREET 1             420 MONTGOMERY STREET
    36      MAIL ADDRESS                                CITY                     SAN FRANCISCO
    37      MAIL ADDRESS                               STATE                                CA
    38      MAIL ADDRESS                                 ZIP                             94163
    41    FORMER COMPANY               FORMER CONFORMED NAME               WELLS FARGO & CO/MN
    42    FORMER COMPANY                 DATE OF NAME CHANGE                          19981103
    45    FORMER COMPANY               FORMER CONFORMED NAME                      NORWEST CORP
    46    FORMER COMPANY                 DATE OF NAME CHANGE                          19920703
    49    FORMER COMPANY               FORMER CONFORMED NAME          NORTHWEST BANCORPORATION
    50    FORMER COMPANY                 DATE OF NAME CHANGE                          19830516
    51    FORMER COMPANY              </acceptance-datetime>
    2019-05-01 14:14:59,984 INFO py_sec_edgar.filing:

            Extracting Filing Documents:

    2019-05-01 14:15:07,547 INFO py_sec_edgar.filing:                           FILENAME        TYPE SEQUENCE                                        DESCRIPTION                                  RELATIVE_FILEPATH
    1             wfc-12312018x10k.htm        10-K        1                                          FORM 10-K  000007297119000227\0001-(10...         0001-(10-K)_FORM_10-K_wfc-12312018x10k.htm
    2           wfc-12312018xex10a.htm     EX-10.A        2                                       EXHIBIT 10.A  000007297119000227\0002-(EX...  0002-(EX-10.A)_EXHIBIT_10.A_wfc-12312018xex10a...
    3           wfc-12312018xex10c.htm     EX-10.C        3                                       EXHIBIT 10.C  000007297119000227\0003-(EX...  0003-(EX-10.C)_EXHIBIT_10.C_wfc-12312018xex10c...
    4           wfc-12312018xex10i.htm     EX-10.I        4                                       EXHIBIT 10.I  000007297119000227\0004-(EX...  0004-(EX-10.I)_EXHIBIT_10.I_wfc-12312018xex10i...
    5           wfc-12312018xex10j.htm     EX-10.J        5                                       EXHIBIT 10.J  000007297119000227\0005-(EX...  0005-(EX-10.J)_EXHIBIT_10.J_wfc-12312018xex10j...
    204                       R183.htm         XML      204                                IDEA: XBRL DOCUMENT  000007297119000227\0204-(XM...             0204-(XML)_IDEA_XBRL_DOCUMENT_R183.htm
    205                       R184.htm         XML      205                                IDEA: XBRL DOCUMENT  000007297119000227\0205-(XM...             0205-(XML)_IDEA_XBRL_DOCUMENT_R184.htm
    206                       R185.htm         XML      206                                IDEA: XBRL DOCUMENT  000007297119000227\0206-(XM...             0206-(XML)_IDEA_XBRL_DOCUMENT_R185.htm
    207          Financial_Report.xlsx       EXCEL      207                                IDEA: XBRL DOCUMENT  000007297119000227\00000729...                              Financial_Report.xlsx
    208                        Show.js         XML      208                                IDEA: XBRL DOCUMENT  000007297119000227\0208-(XM...              0208-(XML)_IDEA_XBRL_DOCUMENT_Show.js
    209                     report.css         XML      209                                IDEA: XBRL DOCUMENT  000007297119000227\0209-(XM...           0209-(XML)_IDEA_XBRL_DOCUMENT_report.css
    210              FilingSummary.xml         XML      211                                IDEA: XBRL DOCUMENT  000007297119000227\0211-(XM...    0211-(XML)_IDEA_XBRL_DOCUMENT_FilingSummary.xml
    211  0000072971-19-000227-xbrl.zip         ZIP      213                                IDEA: XBRL DOCUMENT  000007297119000227\00000729...                      0000072971-19-000227-xbrl.zip

    [211 rows x 6 columns]
    2019-05-01 14:15:07,690 INFO py_sec_edgar.filing:


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

Alright, what can I do now that I have this data?
------------------------------------------------------------------------------------------------------------------

How about we extract the sections of a 10-K Filing and perform some NLP?

.. code-block:: console

    $ cd py-sec-edgar
    $ python examples/extract_sections.py

Or, how about we extract financial data from the Financial Reports.xlsx file:

https://www.sec.gov/Archives/edgar/data/320193/000032019320000096/Financial_Report.xlsx

^ fyi, this financial report file is is contained in most complete submission 10-K/Q filings

Output:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    AAPL 10-k Sections Saved: C:\sec_gov\Archives\edgar\data\320193\000032019320000096


Why download the Complete Submission Filing?
----------------------------------------------

* Most Efficient and Courteous way of getting data from SEC website
    * Contains everything the company filed in filing in one file
    * Not making multiple download requests per filing

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

-  Add Multi-Threading
-  need to figure out way to quickly access downloaded content
-  extract earnings data from 8-K
-  setup proper logging instead of print
-  add tests
-  need to add add way to quickly update new tickers
