# import argparse
#
#
# parser = argparse.ArgumentParser(description='SEC Filings Monthly Downloader')
# parser.add_argument('--date', help='Input the month and year seperated by space', action='append', nargs='*')
# args = parser.parse_args()

import datetime
import json
import os
import sys
import zipfile
from urllib import parse

import feedparser
import redis
from celery import Celery
from pymongo import MongoClient

from edgar_config import SEC_XBRL_DIR, DATA_DIR
from edgar_utilities import gotem

# "C:\Program Files\MongoDB\Server\3.4\bin\mongod.exe" --dbpath=C:\Users\ryan\PycharmProjects\sec-edgars\sec-edgars\data\mongo\db
# from celery import chain

try:
    from edgars_celery_download import r2_download_htmls_files_from_edgars
    from edgars_celery_download import r4_download_htmls_files_from_edgars
    from edgars_celery_download import r6_process_htmls_files_from_edgars
except:
    # from financial.edgar_celery_tasks import r4_download_htmls_files_from_edgars
    # from financial.edgar_celery_tasks import r6_process_htmls_files_from_edgars
    print("none")

app = Celery('tasks', broker='amqp://localhost/', backend='redis://localhost/')

r0 = redis.StrictRedis(host='localhost', port=6379, db=0)  # edgar_rss_feed_urls_ 10-K and 20-F
r1 = redis.StrictRedis(host='localhost', port=6379, db=1)  # Error DB
r2 = redis.StrictRedis(host='localhost', port=6379, db=2)  # Error DB
r3 = redis.StrictRedis(host='localhost', port=6379, db=3)  # Error DB
r6 = redis.StrictRedis(host='localhost', port=6379, db=6)  # urls from the raw html from sec edgar alternative urls


def download_single(edgfilename):
    try:
        download_queue = {}
        directory = os.path.join("B:\\SEC\\" + edgfilename[0:15])
        item_directory = os.path.join(directory, edgfilename)
        zip_filename = os.path.join(item_directory + ".zip")
        download_queue['zip'] = zip_filename
        html_zip_filename = os.path.join(item_directory + "_html.zip")
        download_queue["html"] = html_zip_filename
        # dfiletype, dfilename = list(download_queue.items())[0]
        for dfiletype, dfilename in download_queue.items():
            try:
                htempfolder = item_directory + "_h"
                download_queue['htemp'] = htempfolder
                if not os.path.exists(htempfolder):
                    os.makedirs(htempfolder)
                xtempfolder = item_directory + "_x"
                download_queue['xtemp'] = xtempfolder
                if not os.path.exists(xtempfolder):
                    os.makedirs(xtempfolder)

                hfileExt = (".htm", ".txt")
                xfileExt = (".xml", ".xsd")
                # zfh = zipfile.ZipFile(html_zip_filename, "w")
                # zfx = zipfile.ZipFile(zip_filename, "w")
                items = json.loads(r6.get(edgfilename).decode())
                # ditem = list(items.values())[0]
                for ditem in list(items.values()):

                    if ditem['URLS'].endswith(hfileExt):
                        htargetfname = os.path.join(htempfolder, ditem['URLS'].split('/')[-1])
                        celery_download_edgars_alternative_files.delay(ditem['URLS'], htargetfname)
                        # zfh.write(htargetfname, ditem['URLS'].split('/')[-1], zipfile.ZIP_DEFLATED)
                        # os.remove(htargetfname)

                    if ditem['URLS'].endswith(xfileExt):
                        xtargetfname = os.path.join(xtempfolder, ditem['URLS'].split('/')[-1])
                        celery_download_edgars_alternative_files.delay(ditem['URLS'], xtargetfname)
                        # zfx.write(xtargetfname, ditem['URLS'].split('/')[-1], zipfile.ZIP_DEFLATED)
                        # os.remove(xtargetfname)
            except:
                print('error zipping')

    except:
        if retry:
            download_single(edgfilename)
        else:
            print('problem')
    return download_queue


def zip_all_files(download_queue):
    files = []
    zfh = zipfile.ZipFile(download_queue["html"], "w")
    [files.append(os.path.join(download_queue["htemp"], file)) for file in os.listdir(download_queue["htemp"])]
    for f in files:
        zfh.write(download_queue["htemp"], f, zipfile.ZIP_DEFLATED)
        os.remove(f)
        zfh.close()
    os.rmdir(download_queue["htemp"])
    print('removed ' + download_queue["htemp"])

    files = []
    zfx = zipfile.ZipFile(download_queue["zip"], "w")
    [files.append(os.path.join(download_queue["xtemp"], file)) for file in os.listdir(download_queue["xtemp"])]
    for f in files:
        zfx.write(download_queue["xtemp"], f, zipfile.ZIP_DEFLATED)
        os.remove(f)
        zfx.close()
    os.rmdir(xtempfolder)
    print('removed ' + download_queue["xtemp"])
    # shutil.move(list(item.values())[0], list(item.values())[0])


def download_alternative_html_and_zip_files():
    all_folders = []
    df = pd.read_excel(r'C:\gcloud-repos\secdata-repo\annual_html.xlsx')
    edgfilename = r'xbrlrss-2012-03_xml#2_001-31987_#3_2012-03-09TZ00-00-00_#4_0001265131_#5_Hilltop_Holdings_Inc_#6_10-K_#7_20111231'
    for i in df['_id'].values:
        download_queue = download_single(i)
        all_folders.append(download_queue)
    for download_queue in all_folders:
        zip_all_files(download_queue)

mongo_HOST = "localhost"
mongo_PORT = 27017
mongo_DATABASE = "EDGARS"
mongo_COLLECTION = "edgar_alt_html"
mdb3 = MongoClient(mongo_HOST, mongo_PORT)[mongo_DATABASE][mongo_COLLECTION]


def main(argv):
    # argv = [4, 2017]
    month = argv[0]
    year = argv[1]
    basename, edgurl = edgar_filings_feed(year=year, month=month)
    # edgar_urls = pickle.load(open(r'C:\gcloud-repos\secdata-repo\financial\data\sec_edgars_rss_feed_urls.pickle', "rb"))
    directory = os.path.join(DATA, basename)
    if not os.path.exists(directory):
        os.makedirs(directory)
    print("grabbing feeds from " + edgurl)
    # edgurl = r'https://www.sec.gov/Archives/edgar/monthly/xbrlrss-2015-01.xml'
    sec_edgars_rss_feed_urls, problem_list = load_edgar_monthy_xml_files(months=3, filter_urls=None,
                                                                         seperate_zips_and_htmls=True,
                                                                         save_to_redis=False)
    # feed = read_xml_feedparser(edgurl)
    # item = feed.entries[0]
    filename = os.path.join(DATA_DIR, 'dict_of_edgar_filings_urls_html_files.pickle')
    # sec_edgars_rss_feed_urls = pickle.load(open(os.path.join(data_dir, 'dict_of_edgar_filings_urls_html_files.pickle'), "rb"))

    # edgfilename, json_data = list(sec_edgars_rss_feed_urls.items())[0]
    for edgfilename, json_data in sec_edgars_rss_feed_urls.items():
        item = json.loads(json_data)
        if ("10-K" in item[
            "edgar_formtype"]):  # or ("S-1" in item["edgar_formtype"]) or ("20-F" in item["edgar_formtype"]):
            # edgfilename = create_edgarfilename(basename, item)
            try:
                # setting up for downloading zip file and html files from edgars
                download_queue = {}
                item_directory = os.path.join(directory, edgfilename)
                zip_filename = os.path.join(item_directory + ".zip")
                download_queue['zip'] = zip_filename
                html_zip_filename = os.path.join(item_directory + "_html.zip")
                download_queue["html"] = html_zip_filename
                # dfiletype, dfilename = list(download_queue.items())[0]
                for dfiletype, dfilename in download_queue.items():
                    filename = check_if_file_exists(directory, dfilename)
                    # basename = r'C:\SEC\IN\xbrlrss-2017-03'
                    if filename:
                        try:
                            zip_url, html_url = check_if_urls_already_availible(edgfilename)
                            download_queue['html_url'] = html_url
                            download_queue['zip_url'] = zip_url
                            r4_download_htmls_files_from_edgars.delay(html_url, edgfilename)
                            # r6_process_htmls_files_from_edgars(edgfilename)
                            # r8_download_all_files_from_single_edgars_filings()

                        except:
                            print("Not in Redis")

                    # xf = xbrlFiles[0]
                    if dfiletype == "zip":
                        if zip_url:
                            download_file(zip_url, zip_filename)
                            print('downloaded ', zip_url, ' ', zip_filename)
            except:
                print("Not in Redis")
            finally:
                print("----------")


if __name__ == "__main__":

    if len(sys.argv[1:]) > 1:
        if sys.argv[1:][0] == "--date":
            argv = sys.argv[2:]
            print("month = ", argv[0], "year = ", argv[1])
            main(argv)
    else:
        main([4, 2017])
        sys.exit(parser.print_help())
