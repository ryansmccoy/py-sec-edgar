import re
from collections import defaultdict
from html import unescape

import lxml.html
import pandas as pd
from bs4 import BeautifulSoup


def header_parser(raw_html):
    """parses the heading of an SEC Edgar filing"""

    lxml_html = lxml.html.fromstring(raw_html)

    root = lxml_html.getroottree()
    data = defaultdict(dict)
    valuename = ""

    for sec_header_element in root.xpath("//*/sec-header"):
        soup = BeautifulSoup(lxml.html.tostring(sec_header_element), 'lxml')
        sec_header = re.findall(
            r'<(SEC-HEADER|sec-header)>(.*?)</(SEC-HEADER|sec-header)>', soup.prettify(), re.DOTALL)[0][1]

        split_header = sec_header.split('\n')
        for i, headerItem in enumerate(split_header):
            if len(headerItem) > 0:
                try:
                    if "<" in headerItem and ">" in headerItem:
                        keyname = headerItem
                        valuename = split_header[i + 1]
                        data[i] = ["", "", keyname.strip(), valuename]
                    elif not headerItem.startswith("\t") and headerItem != valuename and "<" not in headerItem:
                        data[i] = ["", "", headerItem.split(":")[0].split("\t")[0], unescape(headerItem.split(":")[1].lstrip())]
                    elif headerItem != "" and headerItem != valuename and "<" not in headerItem:
                        data[i] = headerItem.split(":")[0].split(
                            "\t") + [unescape(headerItem.split(":")[1].lstrip())]
                    else:
                        print(headerItem)
                except:
                    keyname = headerItem.strip()
                    valuename = headerItem.strip()
                    print("found problem")

    header_dict = pd.DataFrame.from_dict(dict(data), orient='index')
    header_dict = header_dict.replace('', pd.np.nan)
    header_dict[1] = header_dict[1].ffill().bfill().tolist()
    header_dict = header_dict.iloc[:, 1:]
    header_dict = header_dict.dropna()
    header_dict.columns = ['GROUP', 'KEY', 'VALUE']

    try:
        print(header_dict)
    except UnicodeEncodeError:
        pass
    return header_dict
