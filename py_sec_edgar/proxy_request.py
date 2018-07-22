
import os
import random
import time

import pandas as pd
import requests


class ProxyRequest(object):
    def __init__(self):
        from py_sec_edgar import CONFIG

        self.retry_counter = 3

        self.pause_for_courtesy = False

        # file_list_user_agents = os.path.join(CONFIG.CONFIG_DIR, 'user_agents.txt')
        #
        # with open(file_list_user_agents, 'r') as f:
        #     self.list_user_agents = f.read().splitlines()

        # self.proxy_pool = cycle(self.proxies)

        if CONFIG.VPN_PROVIDER is None or CONFIG.VPN_PROVIDER == "N":

            self.USERNAME = os.getenv('N_USERNAME')
            self.PASSWORD = os.getenv('N_PASSWORD')
            self.VPN_LIST = os.getenv('N_SERVER_LIST')

            self.service = "http"
            proxies = pd.read_csv(self.VPN_LIST, index_col=0)
            # proxies = pd.read_csv(VPN_LIST, index_col=0)

            self.proxies = proxies['IP'].tolist()

        elif CONFIG.VPN_PROVIDER == "PP":

            self.USERNAME = os.getenv('PP_USERNAME')
            self.PASSWORD = os.getenv('PP_PASSWORD')
            self.VPN_LIST = os.getenv('PP_SERVER_LIST')
            self.port = 5080
            self.service = "socks5"

            proxies = pd.read_csv(self.VPN_LIST, index_col=0)
            # proxies = pd.read_csv(VPN_LIST, index_col=0)

            self.proxies = proxies['IP'].tolist()

        self.connect_timeout, self.read_timeout = 10.0, 30.0

        self.list_user_agents = [
            'Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_1) AppleWebKit/602.2.14 (KHTML, like Gecko) Version/10.0.1 Safari/602.2.14',
            'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.98 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.98 Safari/537.36',
            'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36',
            'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:50.0) Gecko/20100101 Firefox/50.0'
        ]

    def generate_random_proxy_hosts(self):
        proxy = random.choice(self.proxies)

        proxies = {
            'http': '{}://{}:{}@{}:{}'.format(self.service, self.USERNAME, self.PASSWORD, proxy, self.port),
            'https': '{}://{}:{}@{}:{}'.format(self.service, self.USERNAME, self.PASSWORD, proxy, self.port)
        }

        print("\n\tSelected-Proxy:\t{}".format(proxies))

        return proxies

    def generate_random_header(self):
        _user_agent = random.choice(self.list_user_agents)

        _headers = {'User-Agent': _user_agent}

        print("\n\tSelected User-Agent:\t{}\n".format(_headers))
        return _headers

    def generate_random_header_and_proxy_host(self):

        self.random_proxy_host = self.generate_random_proxy_hosts()

        self.random_header = self.generate_random_header()

        if self.pause_for_courtesy:
            print('\tpausing ... as a courtesy...\n')

            time.sleep(random.randrange(5, 10))

    def GET_FILE(self, url, filepath):

        print("\n\tDownloading: \t{}\n".format(url))
        print("\n\tSaving to: \t{}\n".format(filepath))

        retry_counter = 0

        while retry_counter < self.retry_counter:
            try:

                self.generate_random_header_and_proxy_host()

                self.r = requests.get(url, stream=True, headers=self.random_header, proxies=self.random_proxy_host, timeout=(
                    self.connect_timeout, self.read_timeout))

                with open(filepath, 'wb') as f:
                    for chunk in self.r.iter_content(chunk_size=1024):
                        if chunk:  # filter out keep-alive new chunks
                            f.write(chunk)

                print('\n\tSuccess!\tSaved to filepath:\t{}\n'.format(filepath))
                break

            except Exception as e:
                print(" \n\n\t {} \n\nRetrying:".format(e), retry_counter)
                time.sleep(3)
                retry_counter -= 1
                if retry_counter == 0:
                    print("Failed to Download " + url)

        self.random_header = None
        self.random_proxy_host = None


if __name__ == "__main__":
    from py_sec_edgar import CONFIG
    import os
    url = r'https://www.sec.gov/Archives/edgar/data/897078/0001493152-18-009029.txt'
    g = ProxyRequest()
    local_master_idx = os.path.join(CONFIG.SEC_FULL_INDEX_DIR, "master.idx")
    g.GET_FILE(url, local_master_idx)
