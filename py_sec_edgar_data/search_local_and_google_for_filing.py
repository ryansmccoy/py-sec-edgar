# -*- coding: utf-8 -*-
import glob
import io
import os
import sys

from google.cloud import storage


# ^ this imports a bunch of file paths used to store the files
# check out the __init__.py file in the edgar_config folder
def search_for_sec_filings(TICKER=None, SEC_YEAR=None, SEC_TXT_DIR=None, OUTPUT=None):
    """
    Filters list of Bank filings using tickers and year of filings, first searching local directory and if the file is not present it will download them from google cloud

    example:

        (C:\Python\envs\secdata) C:\SECDATA\sec-data-python\sec_data\examples> python 10_query_sec_filings_by_ticker_and_year.py --tickers BAC --years 2017

    explanation:

        Say you wanted to extract the tables from the 2017 Bank of America Filing

        ./edgaridx-2017-02_txt_#2_edgar_data_70858_0000070858-17-000013_#3_2017-02-23TZ00-00-00_#4_70858_#5_(BAC)_BANK_OF_AMERICA_CORP_DE_#6_10-K_#7_2017-02-23.txt

        "#5_(BAC)_BANK_OF_AMERICA_CORP_DE_#6_10-K_#7_2017-02-23.txt"
        ^ each parameter will be passed against text to the right of #5 in filepath

        TICKER = "BAC"
        :param TICKER: Can either be individual ticker, list of tickers, or ALL which is equivalent to *

        SEC_YEAR = "2017"
        :param SEC_YEAR: By default, it selects filings from 2010+

    :param SEC_TXT_FILES: By default, when the program is initiated, it scans C:\SECDATA\EDGAR_IDX_FILINGS_TXT_1996-2017\ directory for TXT files

    :return: Filepath(s) for matching files
    """

    # create a list to store search variof the filings we are intersted in
    filing_filter = []
    # part 1 of filter is based on tickers
    if TICKER == ["ALL"] or TICKER == "ALL":
        print("Ticker Filter:\tALL")
        filing_filter.append("_")

    # if TICKER = string of characters then we assume it's just a ticker
    # and we append it to the filing filter list
    # i.e. TICKER = "JPM"
    elif isinstance(TICKER, str):
        print("Ticker Filter: \t{}".format(TICKER))
        filing_filter.append(TICKER)

    # if TICKER = list of tickers
    # and we append it to the filing filter list
    # i.e. TICKER = ["JPM", "WFC"]
    elif isinstance(TICKER, list):
        # this is called a list comprehenision, its basically a shortcut for loop
        # this says for each ticker in TICKER, add it to the filing_filter list
        # filing_filter.append([ticker.upper() for ticker in TICKER])
        #  the list comprehension above is the same as:
        for ticker in TICKER:
            print("Ticker Filter: \t{}".format(ticker))
            filing_filter.append(ticker)
    else:
        print("Please Specify Ticker")
        sys.exit()

    # 2nd part of filter is based on year
    if SEC_YEAR == ["ALL"] or SEC_YEAR == "ALL":
        print("Year Filter:\tALL")
        filing_filter.append("_")
        # adding a keyword variable constant across all filing filepaths
    elif isinstance(SEC_YEAR, str):
        print("Year Filter: \t{}".format(SEC_YEAR))
        filing_filter.append(SEC_YEAR)
    else:
        # if the user passed a list for the variable i.e. [2010,2011,2013]
        if isinstance(SEC_YEAR, list):
            # add the dates to the filing filter list
            # filing_filter.append([year for year in SEC_YEAR])
            for year in SEC_YEAR:
                print("Year Filter: \t{}".format(year))
                filing_filter.append(year)
        else:
            print("Please Specify Ticker")

    # using the example in the docstring, filing_filter = ["BAC", "2017"]
    print("Filing Filter: \t {}".format(filing_filter))
    # filing_filter = [2013 + y for y in range(0, 5)]
    # perform for loop over list of all filings and filter out only those containing SEC_YEAR and TICKER
    # glob is a module in the Python Standard Library which is used to search files in folders
    # remember SEC_TXT_FILES variable is:
    # C:\SECDATA\EDGAR_IDX_FILINGS_TXT_1996-2017
    # so we are just returning a list of filenames
    SEC_TXT_FILES = glob.glob(os.path.join(SEC_TXT_DIR, "*"))

    # return all files in the
    print("Total # of SEC-Filings on Local: \t{} files".format(len(SEC_TXT_FILES)))
    results = []
    #  list comprehension
    # return all the files with contain both items in the filing_filter variable
    for file in SEC_TXT_FILES:
        if all(str(x) in file for x in filing_filter):
            results.append(file)

    results.sort(reverse=True)
    # pretty inefficent way of doing this but oh well
    # for each file in the folder SECDATA\EDGAR..
    # results = []
    # for file in SEC_TXT_FILES:
    #     # if each of the filters we added to filing_filter pass
    #     if all(str(x) in file.split("#5")[1] for x in filing_filter):
    #         # add it to a list called results
    #         results.append(file)

    if len(results) > 0:
        print("Found {} files".format(len(results)))
        results.sort(reverse=True)
        for file in results:
            print("\t", file)
        return results

    else:
        print("No local file found... Checking Google Cloud for Backup")
        # the project we are using on google drive is called stately-gist-138923
        client = storage.Client(project='stately-gist-138923')
        # I didn't realize until after I created it that I could change the name
        # it was randomly generated by Google...

        # the bucket where all the sec filings are located is:
        bucket = client.get_bucket('sec_edgar_txt_filings')

        SEC_TXT_FILES = list(bucket.list_blobs(1000, prefix="EDGAR_IDX_FILINGS_TXT_1996-2017"))

        print("Total # of SEC-Filings on Google Cloud: \t{}".format(len(SEC_TXT_FILES)))

        # return list of files that contain elements in filing_filter list
        results = [file for file in SEC_TXT_FILES if all(str(x) in file.name.split("#5")[1] for x in filing_filter) and "10-K_A" not in file.name]

        # url_filepath = results[0]
        local_filepaths = []
        for url_filepath in results:
            filing_io = io.StringIO(url_filepath.download_as_string().decode('utf-8'))
            filename = os.path.basename(url_filepath.path)
            cfilename = filename.replace("%23", "#").replace("%28", "(").replace("%29", ")").replace("%2F", "/").replace("%26", "&")
            print("Downloading... {}".format(cfilename))
            new_filepath = os.path.join(SEC_TXT_DIR, os.path.basename(cfilename))
            raw_html = filing_io.read()
            with open(new_filepath, 'w', encoding='utf-8') as f:
                f.write(raw_html)
            print("Saved to ... {}".format(new_filepath))
            local_filepaths.append(new_filepath)

        print("Done!")
        return local_filepaths


def main(args):
    results = query_sec_files(TICKER=args.tickers[0], SEC_YEAR=args.years[0], SEC_TXT_DIR=None, OUTPUT=None)


if __name__ == '__main__':

    import argparse

    parser = argparse.ArgumentParser(description='SEC DATA Command Line')
    parser.add_argument('--tickers', help='Input the Ticker(s) or ALL keyword', action='append', nargs='*')
    parser.add_argument('--years', help='Input the Year(s) or ALL', action='append', nargs='*')

    if len(sys.argv[1:]) >= 1:
        args = parser.parse_args()
        print(args.tickers)
        main(args)
    else:
        sys.exit(parser.print_help())
