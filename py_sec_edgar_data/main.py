# -*- coding: utf-8 -*-

"""Console script for py_sec_edgar_data."""
import sys
import click
from py_sec_edgar_data.settings import Config
CONFIG = Config()

@click.command()
def main(args=None):
    """Console script for py_sec_edgar_data."""
    click.echo("Replace this message by putting your code into "
               "py_sec_edgar_data.cli.main")
    click.echo("See click documentation at http://click.pocoo.org/")
    return 0

@click.command()
def main(args=None):
    """Console script for py_sec_edgar_data."""
    click.echo("Replace this message by putting your code into "
               "py_sec_edgar_data.cli.main")
    click.echo("See click documentation at http://click.pocoo.org/")
    return 0

if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
