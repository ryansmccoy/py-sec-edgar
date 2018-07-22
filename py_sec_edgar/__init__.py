# -*- coding: utf-8 -*-

"""Top-level package for Python SEC Edgar Data."""

__author__ = """Ryan S. McCoy"""
__email__ = 'ryan413@users.noreply.github.com'
__version__ = '0.1.0'

from py_sec_edgar.settings import Config

CONFIG = Config()

from .feeds import daily_index, full_index, monthly
from . import download_and_extract

header_list = ["ACCESSION NUMBER", "CONFORMED SUBMISSION TYPE", "PUBLIC DOCUMENT COUNT",
               "CONFORMED PERIOD OF REPORT", "FILED AS OF DATE", "DATE AS OF CHANGE", "FILER", "COMPANY data",
               "COMPANY CONFORMED NAME", "CENTRAL INDEX KEY", "STANDARD INDUSTRIAL CLASSIFICATION", "IRS NUMBER",
               "STATE OF INCORPORATION", "FISCAL YEAR END", "FILING VALUES", "FORM TYPE", "SEC ACT",
               "SEC FILE NUMBER", "FILM NUMBER", "BUSINESS ADDRESS", "STREET 1", "STREET 2", "CITY", "STATE", "ZIP",
               "BUSINESS PHONE", "MAIL ADDRESS", "STREET 1", "STREET 2", "CITY", "STATE", "ZIP", "FORMER COMPANY",
               "FORMER CONFORMED NAME", "DATE OF NAME CHANGE"]
header = {
    "COMPANY data": {
        "COMPANY CONFORMED NAME": "",
        "CENTRAL INDEX KEY": "",
        "STANDARD INDUSTRIAL CLASSIFICATION": "",
        "IRS NUMBER": "",
        "STATE OF INCORPORATION": "",
        "FISCAL YEAR END": ""},
    "FILING VALUES": {
        "FORM TYPE": "",
        "SEC ACT": "",
        "SEC FILE NUMBER": "",
        "FILM NUMBER": ""},
    "BUSINESS ADDRESS": {
        "STREET 1": "",
        "STREET 2": "",
        "CITY": "",
        "STATE": "",
        "ZIP": "",
        "BUSINESS PHONE": ""},
    "MAIL ADDRESS": {
        "STREET 1": "",
        "STREET 2": "",
        "CITY": "",
        "STATE": "",
        "ZIP": ""},
    "FORMER COMPANY": {
        "FORMER CONFORMED NAME": "",
        "DATE OF NAME CHANGE": ""}
}
