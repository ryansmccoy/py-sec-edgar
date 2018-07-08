# -*- coding: utf-8 -*-

"""Console script for py_sec_edgar."""
import sys
sys.path.append('..')

import click
import py_sec_edgar

@click.command()
def main():

    py_sec_edgar.feeds.full_index.download(save_idx_as_csv=True, skip_if_exists=True)
    py_sec_edgar.download.filings()

if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
