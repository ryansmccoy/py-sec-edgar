# -*- coding: utf-8 -*-

"""Top-level package for Python SEC Edgar Data."""

__author__ = """Ryan S. McCoy"""
__email__ = 'ryan413@users.noreply.github.com'
__version__ = '0.1.0'

from py_sec_edgar.settings import Config

CONFIG = Config()

from .feeds import daily_index, full_index, monthly
