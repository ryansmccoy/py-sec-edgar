import os
import random
import time

import lxml.html
import requests
from bs4 import BeautifulSoup
from pprint import pprint

class Gotem(object):
    """
    Used to Downlod things throughs VPN
    """

    def __init__(self):
        from py_sec_edgar_data.settings import Config
        CONFIG = Config()

        self.file_list_user_agents = os.path.join(CONFIG.CONFIG_DIR, 'user_agents.txt')
        self.file_list_nordvpn_ips = os.path.join(CONFIG.CONFIG_DIR, 'vpn.py')
        self.USERNAME = os.getenv('VPN_USERNAME')
        self.PASSWORD = os.getenv('VPN_PASSWORD')
        self.response = ""
        self.datastoragetype = None
        self.connect_timeout, self.read_timeout = 10.0, 30.0
        self.retry_counter = 3
        self.url = "No Url"

    def read_and_return(self, filename):
        with open(filename, 'r') as f:
            self.data = f.read().splitlines()
        return self.data

    def _generate_random_ip(self):
        self.list_nordvpn_ips = self.read_and_return(self.file_list_nordvpn_ips)
        self._nordvpn_ips = random.choice(self.data)
        print("\t IP: {}".format(self._nordvpn_ips))
        return self._nordvpn_ips

    def _generate_random_proxy_hosts(self):
        self.host = self._generate_random_ip()
        self.proxies = {
            'http': 'http://' + self.USERNAME + ':' + self.PASSWORD + '@' + self.host + ":" + '80',
        'https': 'http://' + self.USERNAME + ':' + self.PASSWORD + '@' + self.host + ":" + '80'
        }
        return self.proxies

    def _generate_random_header(self):
        self.list_user_agents = self.read_and_return(self.file_list_user_agents)
        _user_agent = random.choice(self.list_user_agents)

        _headers = {'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                         'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
                         'Accept-Encoding': 'gzip, deflate, br',
                         'Accept-Language': 'en-US,en;q=0.8',
                         'Connection': 'keep-alive',
                         'User-Agent': _user_agent,
                         'Upgrade-Insecure-Requests': '1'
                         }

        pprint(_headers)
        return _headers

    def GET_FILE(self, url, filepath=None):
        self.filepath = filepath
        self.url = url
        retry_counter = self.retry_counter

        while retry_counter > 0:
            try:

                random_header = self._generate_random_header()

                random_proxies = self._generate_random_proxy_hosts()

                self.r = requests.get(url, headers=random_header, proxies=random_proxies, timeout=(self.connect_timeout, self.read_timeout))

                print('\n\trequest made \n\t{}\n\n'.format(random_proxies))

                with open(filepath, 'wb') as f:
                    for chunk in self.r.iter_content(chunk_size=1024):
                        if chunk:  # filter out keep-alive new chunks
                            f.write(chunk)
                status = "success"
                return status
            except Exception as e:
                print(" \n\n\t {} \n\nRetrying:".format(e), retry_counter)
                # self._generate_random_nordvpn_ip()
                # self._generate_random_proxy_hosts()
                time.sleep(3)
                retry_counter -= 1
                if retry_counter == 0:
                    print("Failed to Download " + url)
                    status = "fail"
                    return status

    def GET_FILE_CELERY(self, url, filepath):
        print('request made', self.proxies)
        self.r = requests.get(url, stream=True, headers=self._headers, proxies=self.proxies, timeout=(self.connect_timeout, self.read_timeout))
        with open(filepath, 'wb') as f:
            for chunk in self.r.iter_content(chunk_size=1024):
                if chunk:  # filter out keep-alive new chunks
                    f.write(chunk)
        status = "success"
        return status

    def GET_URLS(self, url):
        self.url = url
        try:
            self.GET_HTML(url)
            html = lxml.html.fromstring(self.r.text)
            html.make_links_absolute(url)
            html = lxml.html.tostring(html)
            soup = BeautifulSoup(html, 'lxml')
            urls = []
            [urls.append(link['href']) for link in soup.find_all('a', href=True)]
            self.list_urls = urls
        except Exception as e:
            print(e)

    def __repr__(self):
        return "URL: {}".format(self.url)

if __name__ == "__main__":
    from py_sec_edgar_data.feeds import CONFIG
    import os
    g = Gotem()
    url = r'https://www.sec.gov/Archives/edgar/data/897078/0001493152-18-009029.txt'

    local_master_idx = os.path.join(CONFIG.SEC_FULL_INDEX_DIR, "master.idx")
    g.GET_FILE(url, local_master_idx)
