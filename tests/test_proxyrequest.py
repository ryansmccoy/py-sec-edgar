from py_sec_edgar import CONFIG
import os

url = r'https://www.sec.gov/Archives/edgar/data/897078/0001493152-18-009029.txt'
g = ProxyRequest()
local_master_idx = os.path.join(CONFIG.SEC_FULL_INDEX_DIR, "master.idx")
g.get(url, local_master_idx)
