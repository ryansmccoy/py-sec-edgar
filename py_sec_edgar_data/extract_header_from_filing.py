import sys

sys.path.append('..')

from datetime import datetime
import pandas as pd

desired_width = 400
pd.set_option('display.width', desired_width)
import io
import lxml.html

import os, datetime

from py_sec_edgar_data.process_complete_submission_filing import parse_filing_header


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
