# -*- coding: utf-8 -*-

"""Console script for py_sec_edgar_data."""
import sys
import click

import py_sec_edgar_data

from py_sec_edgar_data.settings import Config

CONFIG = Config()

@click.command()
def download_monthly_xbrl_filings_list():
    return 0

if __name__ == "__main__":
    sys.exit(download_monthly_xbrl_filings_list())  # pragma: no cover
