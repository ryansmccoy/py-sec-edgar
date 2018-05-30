import sys

sys.path.append('..')

from datetime import datetime
# input_filepath = r'S:\Archives\edgar\data\2014\QTR3\0001047469-14-006723.txt'
import pandas as pd

desired_width = 400
pd.set_option('display.width', desired_width)
import io
import lxml.html

import os, datetime

try:
    from edgar_filing.process_complete_submission_filing import parse_filing_header
except:
    from process_complete_submission_filing import parse_filing_header


# ticker_check = r'E:\DATA\tickercheck.xlsx'
# df_ticker_check = pd.read_excel(ticker_check,header=0,index_col=0,parse_dates=True)
#
# ticker_check_final = r'E:\DATA\tickers_cik.xlsx'
# df_cik_final = pd.read_excel(ticker_check_final,header=0,index_col=0,parse_dates=True)
# filePath = r'S:\Archives\edgar\data\2017\QTR3\0000950123-17-006152.txt'
# filePath = r'S:\OUTPUT\0001140536-17-000008\wltw-20161231.xml'
# input_filepath = r'S:\Archives\edgar\data\2014\QTR3\0000910406-14-000035.txt'
# filePath = r'S:\OUTPUT\0001567619-17-000284\0021-(EX-101.INS)_XBRL_INSTANCE_FILE_lll-20161231.xml'
# parse_xbrl_data(filePath)


def extract_header_from_filing(input_filepath=None, header_output_filepath=None, df_bb=None, df_cik=None, ticker="--"):
    with io.open(input_filepath, "rb") as f:
        raw_html = f.read()

    # lxml is a fast html file parser c++
    lxml_html = lxml.html.fromstring(raw_html)

    root = lxml_html.getroottree()

    if header_output_filepath is None:
        header_output_filepath = r'S:\OUTPUT\HEADERS'

    try:
        df_header = parse_filing_header(root)
        df_header = df_header[['KEY', 'VALUE']].set_index('KEY')
        filename_items = ['FILED AS OF DATE', 'ACCESSION NUMBER', '<acceptance-datetime>', 'CENTRAL INDEX KEY', 'COMPANY CONFORMED NAME', 'CONFORMED SUBMISSION TYPE', 'CONFORMED PERIOD OF REPORT']
        header_dict = df_header[df_header.index.isin(filename_items)].reindex(filename_items).to_dict()['VALUE']

        edgfilename = str('edgaridx-' + header_dict['FILED AS OF DATE'][0:4] + "-" + header_dict['FILED AS OF DATE'][4:6] +
                          "_#2_" + header_dict['ACCESSION NUMBER'] +
                          "_#3_" + datetime.strptime(header_dict['<acceptance-datetime>'].strip(), "%Y%m%d%H%M%S").strftime("%Y-%m-%dTZ%H-%M-%S")
                          + "_#4_" + header_dict['CENTRAL INDEX KEY'].lstrip("0") +
                          "_#5_({})_".format(ticker) + header_dict['COMPANY CONFORMED NAME'].upper() +
                          "_#6_" + header_dict['CONFORMED SUBMISSION TYPE'] +
                          "_#7_" + header_dict['FILED AS OF DATE'])

        edgfilename = edgfilename.replace(" ", "_").replace(".", "_").replace(
            ",", "_").replace("/", "_").replace("__", "_").replace("/", "_").replace(" ", "_")
        sec_filing_output_directory = os.path.join(header_output_filepath, '{}.csv'.format(edgfilename))
        df_final = df_header.T
        df_final.index = [edgfilename]
        df_final.to_csv(sec_filing_output_directory)
        return edgfilename
    except:
        print("error {}".format(input_filepath))


if __name__ == '__main__':

    import argparse

    parser = argparse.ArgumentParser(description='SEC DATA Extract Header from Filing')
    parser.add_argument('--input_filepath', help='Input the Year(s) or ALL', action='append', nargs='*')
    parser.add_argument('--ticker', help='Input the Ticker(s) or ALL keyword', action='append', nargs='*')

    if len(sys.argv[1:]) >= 1:
        args = parser.parse_args()
        extract_header_from_filing(input_filepath=args.input_filepath[0][0], ticker=args.ticker[0][0])
    else:
        sys.exit(parser.print_help())
