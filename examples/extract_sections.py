import os
from pathlib import Path
from bs4 import BeautifulSoup
import re
from lxml.html.clean import clean_html
import lxml.html
import io
import html2text
import requests

print("Downloading Apple's 10-K Filing and Extracting Sections")

part_pattern = re.compile("(?s)(?i)(?m)> +Part|>Part|^Part", re.IGNORECASE + re.MULTILINE)
item_pattern = re.compile("(?s)(?i)(?m)> +Item|>Item|^Item", re.IGNORECASE + re.MULTILINE)
substitute_html = re.compile("(?s)<.*?>")

# for example, I"m going to download filing directly
# set to the folderpath of an extracted 10-K filing
folderpath = r'C:\sec_gov\Archives\edgar\data\320193\000032019320000096'
filename = r'0001-(10-K)_10-K_aapl-20200926.htm'
filepath = os.path.join(folderpath, filename)

# create folders
Path(folderpath).mkdir(exist_ok=True, parents=True)

# download the html file
response = requests.get(r'https://www.sec.gov/Archives/edgar/data/320193/000032019320000096/aapl-20200926.htm')

# save it in the filepath created above
with open(filepath, 'w') as f:
    f.write(response.content.decode('utf-8'))

# root = lxml.html.parse(filepath, parser=lxml.html.HTMLParser(encoding='utf-8')).getroot()

# read it into variable
with open(filepath, "r", encoding='utf-8') as f:
    raw_html = f.read()

# search for the parts/items of filing and replace it with unique character to split on later
updated_html = part_pattern.sub(">°Part", raw_html)
updated_html = item_pattern.sub(">°Item", updated_html)

# remove tables because they can be parsed seperately
lxml_html = lxml.html.fromstring(updated_html)
root = lxml_html.getroottree()

# remove tables because we can analyze them seperately
# table = list(root.iter(tag='table'))[11]
for i, table in enumerate(root.iter(tag='table')):

    table_text = table.text_content()

    # i just used two entries to determine whether we were looking at toc table
    if "Financial Data" in table_text or "Mine Safety Disclosures" in table_text:
        print("Found Sections")
        print(table_text)
        pass
    else:
        # drop table from HTML
        table.drop_tree()

updated_raw_html = lxml.html.tostring(root)

soup = BeautifulSoup(updated_raw_html, 'lxml')

h = html2text.HTML2Text()
raw_text = h.handle(soup.prettify())

for idx, item in enumerate(raw_text.split("°Item")):
    # if text is longer than 100 characters save it.
    # could create a regex that parses first line to match [0-9]\. [A-z].+
    # then save filename
    if len(item) > 100:
        with io.open(filepath.replace(".htm", f"text_{idx}.txt"), "w", encoding='utf-8') as f:
            f.write(item)

print(f"AAPL 10-k Sections Saved:\n{folderpath}")
