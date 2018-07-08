Python SEC Edgar (Currently Under Developement)
=============

Python package used to download filings from the sec.gov/edgar website, which through Q3/2017 contains 16,867,734 filings.


Using this Repo
---------------

    pip install -r requirements/requirements_dev.txt

### Run

CMD/Bash

    python examples/download_full_index_filings.py

Docker (Work in Progress)

    $  docker run -d -p 5672:5672 -p 15672:15672 --name sec-rabbit rabbitmq:management
    $  celery -A edgar_download.celery_download_complete_submission_filing worker --loglevel=info

Paths and Directory Structure
----------------

The filings follow the structure of sec.gov website.

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



TOTAL FILINGS
----------------------------
    QUARTER	         TOTAL # OF FILINGS
    1994_QTR1_MASTER	 20,879
    1994_QTR2_MASTER	 16,500
    1994_QTR3_MASTER	 13,066
    1994_QTR4_MASTER	 15,016
    1995_QTR1_MASTER	 31,875
    1995_QTR2_MASTER	 26,104
    1995_QTR3_MASTER	 26,699
    1995_QTR4_MASTER	 28,973
    1996_QTR1_MASTER	 49,925
    1996_QTR2_MASTER	 47,659
    1996_QTR3_MASTER	 50,641
    1996_QTR4_MASTER	 54,389
    1997_QTR1_MASTER	 91,096
    1997_QTR2_MASTER	 65,470
    1997_QTR3_MASTER	 60,142
    1997_QTR4_MASTER	 63,422
    1998_QTR1_MASTER	 106,666
    1998_QTR2_MASTER	 73,830
    1998_QTR3_MASTER	 67,234
    1998_QTR4_MASTER	 65,570
    1999_QTR1_MASTER	 105,531
    1999_QTR2_MASTER	 78,272
    1999_QTR3_MASTER	 68,631
    1999_QTR4_MASTER	 68,828
    2000_QTR1_MASTER	 116,209
    2000_QTR2_MASTER	 81,129
    2000_QTR3_MASTER	 72,571
    2000_QTR4_MASTER	 72,053
    2001_QTR1_MASTER	 111,740
    2001_QTR2_MASTER	 90,283
    2001_QTR3_MASTER	 74,313
    2001_QTR4_MASTER	 75,107
    2002_QTR1_MASTER	 125,189
    2002_QTR2_MASTER	 108,013
    2002_QTR3_MASTER	 97,533
    2002_QTR4_MASTER	 118,149
    2003_QTR1_MASTER	 183,595
    2003_QTR2_MASTER	 167,119
    2003_QTR3_MASTER	 212,258
    2003_QTR4_MASTER	 227,800
    2004_QTR1_MASTER	 312,029
    2004_QTR2_MASTER	 253,022
    2004_QTR3_MASTER	 217,726
    2004_QTR4_MASTER	 241,435
    2005_QTR1_MASTER	 317,763
    2005_QTR2_MASTER	 271,632
    2005_QTR3_MASTER	 242,173
    2005_QTR4_MASTER	 240,725
    2006_QTR1_MASTER	 335,579
    2006_QTR2_MASTER	 278,960
    2006_QTR3_MASTER	 232,131
    2006_QTR4_MASTER	 249,960
    2007_QTR1_MASTER	 339,880
    2007_QTR2_MASTER	 289,083
    2007_QTR3_MASTER	 252,072
    2007_QTR4_MASTER	 256,468
    2008_QTR1_MASTER	 328,709
    2008_QTR2_MASTER	 267,722
    2008_QTR3_MASTER	 220,734
    2008_QTR4_MASTER	 219,670
    2009_QTR1_MASTER	 300,080
    2009_QTR2_MASTER	 229,347
    2009_QTR3_MASTER	 200,688
    2009_QTR4_MASTER	 208,397
    2010_QTR1_MASTER	 300,558
    2010_QTR2_MASTER	 255,201
    2010_QTR3_MASTER	 203,928
    2010_QTR4_MASTER	 220,072
    2011_QTR1_MASTER	 307,649
    2011_QTR2_MASTER	 262,223
    2011_QTR3_MASTER	 207,148
    2011_QTR4_MASTER	 202,628
    2012_QTR1_MASTER	 309,488
    2012_QTR2_MASTER	 246,852
    2012_QTR3_MASTER	 203,727
    2012_QTR4_MASTER	 214,995
    2013_QTR1_MASTER	 303,587
    2013_QTR2_MASTER	 257,611
    2013_QTR3_MASTER	 213,037
    2013_QTR4_MASTER	 216,282
    2014_QTR1_MASTER	 311,692
    2014_QTR2_MASTER	 235,184
    2014_QTR3_MASTER	 212,388
    2014_QTR4_MASTER	 220,399
    2015_QTR1_MASTER	 318,625
    2015_QTR2_MASTER	 259,971
    2015_QTR3_MASTER	 206,951
    2015_QTR4_MASTER	 209,794
    2016_QTR1_MASTER	 308,848
    2016_QTR2_MASTER	 243,819
    2016_QTR3_MASTER	 201,518
    2016_QTR4_MASTER	 198,338
    2017_QTR1_MASTER	 311,392
    2017_QTR2_MASTER	 254,917
    2017_QTR3_MASTER	 113,448
                            16,867,734
