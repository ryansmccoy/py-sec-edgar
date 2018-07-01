import pandas as pd
desired_width = 600
pd.set_option('display.width', desired_width)
import re
import requests

_CIK_URI = 'http://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={s}&count=10&output=xml'
yahoo_url = 'http://finance.yahoo.com/lookup?s='
string_match = 'companyName'

def grab_tickers_from_yahoo_cik():
    df=pd.read_excel(r'B:\_concat.xlsx', index_col=0, header=0)
    df=df[df['edgar_formtype'] == "10-K"]
    list_of_missing_ciks = df[df['Symbol'].astype(str) == "nan"]['CIK'].tolist()

    matches={}
    list_of_missing_cik=list(set(list_of_missing_ciks))
    for CIK in list_of_missing_cik:
        print(CIK)
        url =r'http://yahoo.brand.edgar-online.com/default.aspx?cik={}'.format(CIK)
        g = ProxyRequest.ProxyRequest()
        g.GET_HTML(url)
        try:
            re_string = re.search(r"t=[A-Z].+", g.r.text)
            if re_string:
                match = re_string.group(0).split('=')[1].split("'")[0]
                matches[CIK]=match
        except AttributeError:
            pass
import numpy as np

def load_ticker_to_cik_files():
    bb_update = r'B:\US_EXCHANGE_COMPANIES_big.xlsx'
    df_bb = pd.read_excel(bb_update,header=0,index_col=0,parse_dates=True)
    cik_ticker_check = r'B:\TICKERCHECK_CIK_COMPANIES_ONLY.xlsx'
    df_cik = pd.read_excel(cik_ticker_check,header=0,index_col=0)
    datacomb = r'B:\datacomb_no_format.xlsx'
    df_datacomb = pd.read_excel(datacomb, index_col=0, header=0)
    df_datacomb.T
    df_datacomb.replace('', np.nan, inplace=True)
    df_datacomb.replace('-', np.nan, inplace=True)
    df_datacomb.replace('0', np.nan, inplace=True)
    df_datacomb.replace('#N/A', np.nan, inplace=True)
    df_tickercheck.replace('', np.nan, inplace=True)
    df_tickercheck.replace('-', np.nan, inplace=True)
    df_tickercheck.replace('0', np.nan, inplace=True)
    df_tickercheck.replace('#N/A', np.nan, inplace=True)

    df_merged = pd.merge(df_tickercheck, df_datacomb, left_on='TICKER', right_on='TICKER')
    df_comb = df_tickercheck.combine_first(df_datacomb)

    df_merged.to_csv(r'c:\auto\merged.csv')

    tickercheck = r'B:\tickercheck.xlsx'
    df_tickercheck = pd.read_excel(tickercheck, index_col=0, header=0)

    return df_bb, df_cik
#
# ticker_check = r'E:\data\tickercheck.xlsx'
# df_ticker_check = pd.read_excel(ticker_check,header=0,index_col=0,parse_dates=True)
#
# ticker_check_final = r'E:\data\tickers_cik.xlsx'
# df_cik_final = pd.read_excel(ticker_check_final,header=0,index_col=0,parse_dates=True)

def get_cik(symbol):
    """
    Retrieves the CIK identifier of a given security from the SEC based on that
    security's market symbol (i.e. "stock ticker").

    :param symbol: Unique trading symbol (e.g. 'NVDA')
    :return: A corresponding CIK identifier (e.g. '1045810')
    """
    response = requests.get(_CIK_URI.format(s=symbol))
    page_data = bs4.BeautifulSoup(response.text, "html.parser")
    cik = page_data.companyinfo.cik.string
    return cik

def cik2ticker(item):
    URL = 'http://yahoo.brand.edgar-online.com/default.aspx?cik={}'
    RE_EXP = re.compile(r':\s+[\w\.\-\^]+\s')

    soup = BeautifulSoup(requests.get(URL.format(item['edgar_ciknumber'])).content, "lxml")
    for td in soup.find_all('td', {'class': 'tableTop'}):
        matched = RE_EXP.findall(td.text)
        if len(matched):
            return str(matched[0][1:].strip())
    return '0'

def get_cik_from_ticker(ticker_list):
    cik_dict = {}
    URL = 'http://www.sec.gov/cgi-bin/browse-edgar?CIK={}&Find=Search&owner=exclude&action=getcompany'
    CIK_RE = re.compile(r'.*CIK=(\d{10}).*')
    # ticker = DEFAULT_TICKERS[0]
    for ticker in ticker_list:
        try:
            g = ProxyRequest.ProxyRequest()
            g.GET_HTML(URL.format(ticker))
            text = g.r.content.decode()
            results = CIK_RE.findall(text)
            if len(results):
                cik_dict[str(ticker).lower()] = str(results[0])
        except:
            print('problem')
    return cik_dict

def load_ticker_to_cik_files():
    bb_update = r'US_EXCHANGE_COMPANIES_bbig.xlsx'
    bb_update = os.path.join(DATA_DIR,bb_update)

    df_bb = pd.read_excel(bb_update,header=0,index_col=0,parse_dates=True)

    cik_ticker_check = os.path.join(DATA_DIR,'TICKERCHECK_CIK_COMPANIES_ONLY.xlsx')
    df_cik = pd.read_excel(cik_ticker_check,header=0,index_col=0)

    return df_bb, df_cik
