import io
import os

import chardet
import lxml.html
from bs4 import BeautifulSoup

from py_sec_edgar.utilities import file_size


def filing_parser(filepath):
    """
    Parses html file
    :param filepath: html file
    :return: dictionary of file_contents including lxml_dict
    """
    # complete_submission_filing_filepath = filing[0]

    lxml_dict = {}

    try:
        # or codecs.open on Python 2
        raw_text = open(filepath, "rb").read()
        result = chardet.detect(raw_text)
        charenc = result['encoding']
        raw_text = raw_text.decode(charenc)
    except:
        charenc = ""
        with io.open(filepath, "rb") as f:
            raw_text = f.read()

    lxml_html = lxml.html.fromstring(raw_text)
    root = lxml_html.getroottree()
    soup = BeautifulSoup(lxml.html.tostring(root), 'lxml')

    filing = {}

    filing['FILEPATH'] = filepath

    for ii, element in enumerate(root.xpath("//*/body/*")):
        lxml_dict[ii] = element

    div_check = {}

    for ii, element in enumerate(lxml.html.fromstring(soup.prettify()).xpath("//*/div/*")):
        div_check[ii] = element

    filing['NUMBER_OF_ELEMENTS'] = len(lxml_dict)
    filing['FILE_SIZE'] = file_size(filing['FILEPATH'])
    filing['FILE_SIZE_BYTES'] = os.stat(filing['FILEPATH']).st_size
    filing['lxml_dict'] = lxml_dict
    filing['div_check'] = div_check
    filing['ENCODING'] = charenc

    return filing


