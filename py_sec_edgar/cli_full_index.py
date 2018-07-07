# -*- coding: utf-8 -*-

"""Console script for py_sec_edgar."""
import sys
import click

try:
    from py_sec_edgar.feeds import full_index
except:
    import feeds.full_index as full_index

@click.command()
def main():
    full_index.download_latest_idx()
    full_index.download_filings_from_idx()

if __name__ == "__main__":

    sys.exit(main())  # pragma: no cover
