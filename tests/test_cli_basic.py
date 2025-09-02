#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Basic CLI tests to validate core functionality after database removal.
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from py_sec_edgar.main import cli


class TestCLIBasic:
    """Test basic CLI functionality."""

    def test_cli_help(self):
        """Test main CLI help."""
        runner = CliRunner()
        result = runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert 'SEC EDGAR Filing Processor' in result.output

    def test_cli_version(self):
        """Test version option."""
        runner = CliRunner()
        result = runner.invoke(cli, ['--version'])
        assert result.exit_code == 0

    @patch('py_sec_edgar.feeds.recent_filings.fetch_recent_rss_filings')
    def test_fetch_recent_rss_basic(self, mock_fetch):
        """Test basic RSS fetch functionality."""
        mock_fetch.return_value = []
        
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as temp_dir:
            result = runner.invoke(cli, [
                '--data-dir', temp_dir,
                'feeds', 'fetch-recent-rss',
                '--count', '1'
            ])
            assert result.exit_code == 0

    def test_utils_status(self):
        """Test status command."""
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as temp_dir:
            result = runner.invoke(cli, [
                '--data-dir', temp_dir,
                'utils', 'status'
            ])
            assert result.exit_code == 0


if __name__ == '__main__':
    pytest.main([__file__])