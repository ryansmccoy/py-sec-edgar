# -*- coding: utf-8 -*-

"""Console script for py_sec_edgar_data."""
import sys
import click

try:
    from py_sec_edgar_data.feeds import full_index
except:
    import feeds.full_index as full_index

@click.command()
def download_latest_filings():
    full_index.download_latest_idx()
    full_index.download_filings_from_idx()

if __name__ == "__main__":

    sys.exit(download_latest_filings())  # pragma: no cover
