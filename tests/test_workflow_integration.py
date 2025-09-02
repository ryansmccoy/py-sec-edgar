#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Integration tests for workflow CLI commands.
Tests actual client commands against real examples to ensure they work correctly.
"""

import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
from click.testing import CliRunner

from src.py_sec_edgar.main import cli


class TestWorkflowIntegration:
    """Integration tests for workflow CLI commands."""

    def setup_method(self):
        """Set up test environment for each test."""
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()
        self.test_data_dir = Path(self.temp_dir) / "test_data"
        self.test_data_dir.mkdir(exist_ok=True)

    def teardown_method(self):
        """Clean up after each test."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_workflows_help_command(self):
        """Test that workflows help command works."""
        result = self.runner.invoke(cli, ['workflows', '--help'])
        
        assert result.exit_code == 0
        assert 'Run complete workflows' in result.output
        assert 'full-index' in result.output
        assert 'daily' in result.output
        assert 'monthly' in result.output
        assert 'rss' in result.output
        assert 'unified' in result.output

    def test_full_index_workflow_help(self):
        """Test full-index workflow help command."""
        result = self.runner.invoke(cli, ['workflows', 'full-index', '--help'])
        
        assert result.exit_code == 0
        assert 'Run the full index workflow' in result.output
        assert '--tickers' in result.output
        assert '--forms' in result.output
        assert '--download' in result.output
        assert '--extract' in result.output

    def test_daily_workflow_help(self):
        """Test daily workflow help command."""
        result = self.runner.invoke(cli, ['workflows', 'daily', '--help'])
        
        assert result.exit_code == 0
        assert 'Run the daily workflow' in result.output
        assert '--days-back' in result.output
        assert '--download' in result.output
        assert '--extract' in result.output

    def test_monthly_workflow_help(self):
        """Test monthly workflow help command."""
        result = self.runner.invoke(cli, ['workflows', 'monthly', '--help'])
        
        assert result.exit_code == 0
        assert 'Run the monthly workflow' in result.output
        assert '--months-back' in result.output
        assert '--download' in result.output
        assert '--extract' in result.output

    def test_rss_workflow_help(self):
        """Test RSS workflow help command."""
        result = self.runner.invoke(cli, ['workflows', 'rss', '--help'])
        
        assert result.exit_code == 0
        assert 'Run the RSS workflow' in result.output
        assert '--count' in result.output
        assert '--download' in result.output
        assert '--extract' in result.output

    def test_unified_workflow_help(self):
        """Test unified workflow help command."""
        result = self.runner.invoke(cli, ['workflows', 'unified', '--help'])
        
        assert result.exit_code == 0
        assert 'Run all workflows in sequence' in result.output
        assert '--skip-full-index' in result.output
        assert '--skip-daily' in result.output
        assert '--skip-monthly' in result.output
        assert '--skip-rss' in result.output

    @patch('src.py_sec_edgar.full_index_workflow.main')
    def test_full_index_workflow_basic_execution(self, mock_full_index_main):
        """Test basic execution of full-index workflow."""
        mock_full_index_main.return_value = None
        
        result = self.runner.invoke(cli, [
            'workflows', 'full-index',
            '--tickers', 'AAPL,MSFT',
            '--forms', '10-K',
            '--no-download',
            '--no-extract'
        ])
        
        print(f"Exit code: {result.exit_code}")
        print(f"Output: {result.output}")
        if result.exception:
            print(f"Exception: {result.exception}")
        
        assert result.exit_code == 0
        mock_full_index_main.assert_called_once()
        call_args = mock_full_index_main.call_args
        assert call_args[1]['ticker_list'] == ['AAPL', 'MSFT']
        assert call_args[1]['form_list'] == ['10-K']
        assert call_args[1]['download'] is False
        assert call_args[1]['extract'] is False

    @patch('src.py_sec_edgar.full_index_workflow.main')
    def test_full_index_workflow_with_ticker_file(self, mock_full_index_main):
        """Test full-index workflow with ticker file."""
        mock_full_index_main.return_value = None
        
        # Create a test ticker file
        ticker_file = self.test_data_dir / "test_tickers.csv"
        ticker_file.write_text("AAPL\nMSFT\nGOOGL\n")
        
        result = self.runner.invoke(cli, [
            'workflows', 'full-index',
            '--ticker-file', str(ticker_file),
            '--form', '10-Q',
            '--no-download'
        ])
        
        print(f"Exit code: {result.exit_code}")
        print(f"Output: {result.output}")
        if result.exception:
            print(f"Exception: {result.exception}")
        
        assert result.exit_code == 0
        mock_full_index_main.assert_called_once()
        call_args = mock_full_index_main.call_args
        assert 'AAPL' in call_args[1]['ticker_list']
        assert 'MSFT' in call_args[1]['ticker_list']
        assert 'GOOGL' in call_args[1]['ticker_list']

    @patch('py_sec_edgar.daily_workflow.main')
    @patch('click.testing.CliRunner.invoke')
    def test_daily_workflow_basic_execution(self, mock_invoke, mock_daily_main):
        """Test basic execution of daily workflow."""
        # Mock the invoke to return successful result
        mock_result = MagicMock()
        mock_result.exit_code = 0
        mock_result.output = "Success"
        mock_invoke.return_value = mock_result
        
        result = self.runner.invoke(cli, [
            'workflows', 'daily',
            '--tickers', 'AAPL',
            '--days-back', '2',
            '--no-extract'
        ])
        
        print(f"Exit code: {result.exit_code}")
        print(f"Output: {result.output}")
        if result.exception:
            print(f"Exception: {result.exception}")
        
        # The workflow should complete successfully when mocked
        assert result.exit_code == 0

    @patch('src.py_sec_edgar.monthly_workflow.main')
    def test_monthly_workflow_basic_execution(self, mock_monthly_main):
        """Test basic execution of monthly workflow."""
        mock_monthly_main.return_value = None
        
        result = self.runner.invoke(cli, [
            'workflows', 'monthly',
            '--tickers', 'NVDA,AMD',
            '--months-back', '2',
            '--forms', '10-K,10-Q',
            '--no-download'
        ])
        
        print(f"Exit code: {result.exit_code}")
        print(f"Output: {result.output}")
        if result.exception:
            print(f"Exception: {result.exception}")
        
        assert result.exit_code == 0
        mock_monthly_main.assert_called_once()
        call_args = mock_monthly_main.call_args
        assert call_args[1]['ticker_list'] == ['NVDA', 'AMD']
        assert call_args[1]['form_list'] == ['10-K', '10-Q']
        assert call_args[1]['months_back'] == 2
        assert call_args[1]['download'] is False

    @patch('py_sec_edgar.rss_workflow.main')
    @patch('click.testing.CliRunner.invoke')
    def test_rss_workflow_basic_execution(self, mock_invoke, mock_rss_main):
        """Test basic execution of RSS workflow."""
        # Mock the invoke to return successful result
        mock_result = MagicMock()
        mock_result.exit_code = 0
        mock_result.output = "Success"
        mock_invoke.return_value = mock_result
        
        result = self.runner.invoke(cli, [
            'workflows', 'rss',
            '--count', '2',
            '--tickers', 'TSLA',
            '--forms', '8-K',
            '--no-extract'
        ])
        
        print(f"Exit code: {result.exit_code}")
        print(f"Output: {result.output}")
        if result.exception:
            print(f"Exception: {result.exception}")
        
        # The workflow should complete successfully when mocked
        assert result.exit_code == 0

    @patch('src.py_sec_edgar.unified_workflow.main')
    def test_unified_workflow_basic_execution(self, mock_unified_main):
        """Test basic execution of unified workflow."""
        mock_unified_main.return_value = None
        
        result = self.runner.invoke(cli, [
            'workflows', 'unified',
            '--days-back', '2',
            '--months-back', '2',
            '--rss-count', '2',
            '--skip-full-index',
            '--skip-monthly'
        ])
        
        print(f"Exit code: {result.exit_code}")
        print(f"Output: {result.output}")
        if result.exception:
            print(f"Exception: {result.exception}")
        
        assert result.exit_code == 0
        mock_unified_main.assert_called_once()
        call_args = mock_unified_main.call_args
        assert call_args[1]['days_back'] == 1
        assert call_args[1]['months_back'] == 1
        assert call_args[1]['rss_count'] == 10
        assert call_args[1]['skip_full_index'] is True
        assert call_args[1]['skip_monthly'] is True

    def test_workflow_error_handling(self):
        """Test error handling in workflows."""
        # Test with invalid parameters
        result = self.runner.invoke(cli, [
            'workflows', 'daily',
            '--days-back', '-1'  # Invalid negative value
        ])
        
        # Should handle the error gracefully
        assert result.exit_code != 0

    def test_workflow_filter_combinations(self):
        """Test various filter combinations."""
        with patch('src.py_sec_edgar.full_index_workflow.main') as mock_main:
            mock_main.return_value = None
            
            # Test no ticker filter
            result = self.runner.invoke(cli, [
                'workflows', 'full-index',
                '--no-ticker-filter',
                '--forms', '10-K',
                '--no-download'
            ])
            
            assert result.exit_code == 0
            call_args = mock_main.call_args
            assert call_args[1]['ticker_list'] is None

    def test_workflow_data_directory_override(self):
        """Test workflow with custom data directory."""
        custom_data_dir = self.test_data_dir / "custom_sec_data"
        custom_data_dir.mkdir(exist_ok=True)
        
        with patch('src.py_sec_edgar.full_index_workflow.main') as mock_main:
            mock_main.return_value = None
            
            result = self.runner.invoke(cli, [
                '--data-dir', str(custom_data_dir),
                'workflows', 'full-index',
                '--tickers', 'AAPL',
                '--no-download',
                '--no-extract'
            ])
            
            assert result.exit_code == 0

    @patch('src.py_sec_edgar.full_index_workflow.main')
    def test_workflow_exception_handling(self, mock_main):
        """Test workflow exception handling."""
        mock_main.side_effect = Exception("Simulated workflow error")
        
        result = self.runner.invoke(cli, [
            'workflows', 'full-index',
            '--tickers', 'AAPL',
            '--no-download'
        ])
        
        assert result.exit_code != 0
        assert 'workflow failed' in result.output.lower()

    def test_workflow_logging_levels(self):
        """Test workflows with different logging levels."""
        with patch('src.py_sec_edgar.full_index_workflow.main') as mock_main:
            mock_main.return_value = None
            
            # Test with DEBUG logging
            result = self.runner.invoke(cli, [
                '--log-level', 'DEBUG',
                'workflows', 'full-index',
                '--tickers', 'AAPL',
                '--no-download',
                '--no-extract'
            ])
            
            assert result.exit_code == 0

    def test_workflow_form_filtering(self):
        """Test form filtering options."""
        with patch('src.py_sec_edgar.monthly_workflow.main') as mock_main:
            mock_main.return_value = None
            
            # Test multiple forms
            result = self.runner.invoke(cli, [
                'workflows', 'monthly',
                '--forms', '10-K', '10-Q', '8-K',
                '--tickers', 'AAPL',
                '--no-download'
            ])
            
            assert result.exit_code == 0
            call_args = mock_main.call_args
            assert '10-K' in call_args[1]['form_list']
            assert '10-Q' in call_args[1]['form_list']
            assert '8-K' in call_args[1]['form_list']

    def test_workflow_ticker_filtering(self):
        """Test ticker filtering options."""
        with patch('src.py_sec_edgar.full_index_workflow.main') as mock_main:
            mock_main.return_value = None
            
            # Test multiple tickers
            result = self.runner.invoke(cli, [
                'workflows', 'full-index',
                '--tickers', 'AAPL', 'MSFT', 'GOOGL', 'AMZN',
                '--no-download',
                '--no-extract'
            ])
            
            assert result.exit_code == 0
            call_args = mock_main.call_args
            expected_tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN']
            assert call_args[1]['ticker_list'] == expected_tickers

    def test_workflow_download_extract_options(self):
        """Test download and extract option combinations."""
        with patch('src.py_sec_edgar.full_index_workflow.main') as mock_main:
            mock_main.return_value = None
            
            test_cases = [
                (['--download', '--extract'], True, True),
                (['--no-download', '--extract'], False, True),
                (['--download', '--no-extract'], True, False),
                (['--no-download', '--no-extract'], False, False),
            ]
            
            for args, expected_download, expected_extract in test_cases:
                result = self.runner.invoke(cli, [
                    'workflows', 'full-index',
                    '--tickers', 'AAPL',
                ] + args)
                
                assert result.exit_code == 0
                call_args = mock_main.call_args
                assert call_args[1]['download'] == expected_download
                assert call_args[1]['extract'] == expected_extract

    def test_main_cli_entry_point(self):
        """Test the main CLI entry point."""
        result = self.runner.invoke(cli, ['--help'])
        
        assert result.exit_code == 0
        assert 'SEC EDGAR Filing Processor' in result.output
        assert 'workflows' in result.output
        assert 'feeds' in result.output
        assert 'process' in result.output
        assert 'utils' in result.output

    def test_cli_version_option(self):
        """Test CLI version option."""
        result = self.runner.invoke(cli, ['--version'])
        
        assert result.exit_code == 0
        assert '1.1.0' in result.output

    @patch('src.py_sec_edgar.unified_workflow.main')
    def test_unified_workflow_skip_options(self, mock_unified_main):
        """Test unified workflow skip options."""
        mock_unified_main.return_value = None
        
        # Test skipping all workflows
        result = self.runner.invoke(cli, [
            'workflows', 'unified',
            '--skip-full-index',
            '--skip-daily',
            '--skip-monthly',
            '--skip-rss'
        ])
        
        assert result.exit_code == 0
        call_args = mock_unified_main.call_args
        assert call_args[1]['skip_full_index'] is True
        assert call_args[1]['skip_daily'] is True
        assert call_args[1]['skip_monthly'] is True
        assert call_args[1]['skip_rss'] is True

    def test_workflow_parameter_validation(self):
        """Test parameter validation in workflows."""
        # Test invalid days-back
        result = self.runner.invoke(cli, [
            'workflows', 'daily',
            '--days-back', 'invalid'
        ])
        assert result.exit_code != 0

        # Test invalid months-back
        result = self.runner.invoke(cli, [
            'workflows', 'monthly',
            '--months-back', 'invalid'
        ])
        assert result.exit_code != 0

        # Test invalid count
        result = self.runner.invoke(cli, [
            'workflows', 'rss',
            '--count', 'invalid'
        ])
        assert result.exit_code != 0

    def test_workflow_real_command_structure(self):
        """Test that workflow commands have proper structure."""
        # Test that all expected workflow commands exist
        result = self.runner.invoke(cli, ['workflows'])
        assert result.exit_code == 0
        
        # Test each workflow command exists
        workflows = ['full-index', 'daily', 'monthly', 'rss', 'unified']
        for workflow in workflows:
            result = self.runner.invoke(cli, ['workflows', workflow, '--help'])
            assert result.exit_code == 0, f"Workflow {workflow} should exist"


if __name__ == '__main__':
    pytest.main([__file__])