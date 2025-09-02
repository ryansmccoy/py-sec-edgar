#!/usr/bin/env python#!/usr/bin/env python

# -*- coding: utf-8 -*-# -*- coding: utf-8 -*-



""""""

Comprehensive CLI tests for py-sec-edgar application.Comprehensive CLI tests for py-sec-edgar application.

Tests all major command groups and scenarios.Tests all major command groups and scenarios.

""""""



import jsonimport json

import osimport os

import tempfileimport tempfile

from pathlib import Pathfrom pathlib import Path

from unittest.mock import AsyncMock, MagicMock, patchfrom unittest.mock import AsyncMock, MagicMock, patch



import pytestimport pytest

from click.testing import CliRunnerfrom click.testing import CliRunner



from py_sec_edgar.main import clifrom py_sec_edgar.main import cli





class TestCLIMain:class TestCLIMain:

    """Test main CLI interface."""    """Test main CLI entry point and global options.""            # First operation: fetch some data

            result1 = runner.invoke(cli, [

    def test_cli_help(self):                '--data-dir', temp_dir,

        """Test main CLI help."""                'feeds', 'fetch-recent-rss',

        runner = CliRunner()                '--count', '1'

        result = runner.invoke(cli, ['--help'])            ])

        assert result.exit_code == 0            assert result1.exit_code == 0

        assert 'SEC EDGAR Filing Processor' in result.output            

        assert 'feeds' in result.output    def test_cli_help(self):

        assert 'workflows' in result.output        """Test main CLI help."""

        assert 'utils' in result.output        runner = CliRunner()

        result = runner.invoke(cli, ['--help'])

    def test_cli_version(self):        assert result.exit_code == 0

        """Test version option."""        assert 'SEC EDGAR Filing Processor' in result.output

        runner = CliRunner()        assert 'feeds' in result.output

        result = runner.invoke(cli, ['--version'])        assert 'workflows' in result.output

        assert result.exit_code == 0        assert 'utils' in result.output

        assert '1.1.0' in result.output

    def test_cli_version(self):

    def test_cli_log_levels(self):        """Test version option."""

        """Test different log levels."""        runner = CliRunner()

        runner = CliRunner()        result = runner.invoke(cli, ['--version'])

        for level in ['DEBUG', 'INFO', 'WARNING', 'ERROR']:        assert result.exit_code == 0

            result = runner.invoke(cli, ['--log-level', level, '--help'])        assert '1.1.0' in result.output

            assert result.exit_code == 0

    def test_cli_log_levels(self):

    def test_cli_custom_data_dir(self):        """Test different log levels."""

        """Test custom data directory option."""        runner = CliRunner()

        runner = CliRunner()        for level in ['DEBUG', 'INFO', 'WARNING', 'ERROR']:

        with tempfile.TemporaryDirectory() as temp_dir:            result = runner.invoke(cli, ['--log-level', level, '--help'])

            result = runner.invoke(cli, ['--data-dir', temp_dir, '--help'])            assert result.exit_code == 0

            assert result.exit_code == 0

    def test_cli_custom_data_dir(self):

        """Test custom data directory option."""

class TestFeedsCommands:        runner = CliRunner()

    """Test feeds command group."""        with tempfile.TemporaryDirectory() as temp_dir:

            result = runner.invoke(cli, ['--data-dir', temp_dir, '--help'])

    def test_feeds_help(self):            assert result.exit_code == 0

        """Test feeds help."""

        runner = CliRunner()

        result = runner.invoke(cli, ['feeds', '--help'])class TestFeedsCommands:

        assert result.exit_code == 0    """Test feeds command group."""

        assert 'Manage SEC EDGAR data feeds' in result.output

    def test_feeds_help(self):

    @patch('py_sec_edgar.feeds.recent_filings.fetch_recent_rss_filings')        """Test feeds help."""

    def test_fetch_recent_rss_basic(self, mock_fetch):        runner = CliRunner()

        """Test basic RSS fetch functionality."""        result = runner.invoke(cli, ['feeds', '--help'])

        mock_fetch.return_value = [        assert result.exit_code == 0

            {        assert 'Manage SEC EDGAR data feeds' in result.output

                'id': 'test_1',        assert 'fetch-recent-rss' in result.output

                'company_name': 'Test Company',        assert 'update-daily-index' in result.output

                'form_type': '10-K',        assert 'update-monthly-xbrl' in result.output

                'filed_date': '2025-01-01',

                'filing_url': 'https://example.com/filing1'    @patch('py_sec_edgar.feeds.recent_filings.fetch_recent_rss_filings')

            }    def test_fetch_recent_rss_basic(self, mock_fetch):

        ]        """Test basic RSS fetch command."""

                mock_fetch.return_value = [

        runner = CliRunner()            {

        with tempfile.TemporaryDirectory() as temp_dir:                'id': 'test_1',

            result = runner.invoke(cli, [                'company_name': 'Test Company',

                '--data-dir', temp_dir,                'form_type': '10-K',

                'feeds', 'fetch-recent-rss',                'filed_date': '2025-01-01',

                '--count', '1'                'filing_url': 'https://example.com/filing1'

            ])            }

            assert result.exit_code == 0        ]

            mock_fetch.assert_called_once()        

        runner = CliRunner()

    @patch('py_sec_edgar.feeds.recent_filings.fetch_recent_rss_filings')        with tempfile.TemporaryDirectory() as temp_dir:

    def test_fetch_recent_rss_with_form_type(self, mock_fetch):            result = runner.invoke(cli, [

        """Test RSS fetch with form type filter."""                '--data-dir', temp_dir,

        mock_fetch.return_value = []                'feeds', 'fetch-recent-rss',

                        '--count', '1'

        runner = CliRunner()            ])

        with tempfile.TemporaryDirectory() as temp_dir:            assert result.exit_code == 0

            result = runner.invoke(cli, [            mock_fetch.assert_called_once()

                '--data-dir', temp_dir,

                'feeds', 'fetch-recent-rss',    @patch('py_sec_edgar.feeds.recent_filings.fetch_recent_rss_filings')

                '--count', '5',    def test_fetch_recent_rss_with_form_type(self, mock_fetch):

                '--form-type', '8-K'        """Test RSS fetch with form type filter."""

            ])        mock_fetch.return_value = []

            assert result.exit_code == 0        

            mock_fetch.assert_called_once_with(count=5, form_type='8-K')        runner = CliRunner()

        with tempfile.TemporaryDirectory() as temp_dir:

    @patch('py_sec_edgar.feeds.recent_filings.fetch_recent_rss_filings')            result = runner.invoke(cli, [

    def test_fetch_recent_rss_save_options(self, mock_fetch):                '--data-dir', temp_dir,

        """Test RSS fetch with different save options."""                'feeds', 'fetch-recent-rss',

        mock_fetch.return_value = [                '--count', '5',

            {                '--form-type', '8-K'

                'id': 'test_1',            ])

                'company_name': 'Test Company',            assert result.exit_code == 0

                'form_type': '10-K',            mock_fetch.assert_called_once_with(count=5, form_type='8-K')

                'filed_date': '2025-01-01',

                'filing_url': 'https://example.com/filing1'    @patch('py_sec_edgar.feeds.recent_filings.fetch_recent_rss_filings')

            }    def test_fetch_recent_rss_save_options(self, mock_fetch):

        ]        """Test RSS fetch with different save options."""

                mock_fetch.return_value = [

        runner = CliRunner()            {

        with tempfile.TemporaryDirectory() as temp_dir:                'id': 'test_1',

            # Test with CSV and JSON saving                'company_name': 'Test Company',

            result = runner.invoke(cli, [                'form_type': '10-K',

                '--data-dir', temp_dir,                'filed_date': '2025-01-01',

                'feeds', 'fetch-recent-rss',                'filing_url': 'https://example.com/filing1'

                '--count', '1',            }

                '--save-csv',        ]

                '--save-json'        

            ])        runner = CliRunner()

            assert result.exit_code == 0        with tempfile.TemporaryDirectory() as temp_dir:

            # Test with CSV and JSON saving

    def test_update_daily_index_help(self):            result = runner.invoke(cli, [

        """Test daily index update help."""                '--data-dir', temp_dir,

        runner = CliRunner()                'feeds', 'fetch-recent-rss',

        result = runner.invoke(cli, ['feeds', 'update-daily-index', '--help'])                '--count', '1',

        assert result.exit_code == 0                '--save-csv',

        assert 'Download and update daily index feeds' in result.output                '--save-json'

            ])

    def test_update_monthly_xbrl_help(self):            assert result.exit_code == 0

        """Test monthly XBRL update help."""

        runner = CliRunner()    def test_update_daily_index_help(self):

        result = runner.invoke(cli, ['feeds', 'update-monthly-xbrl', '--help'])        """Test daily index update help."""

        assert result.exit_code == 0        runner = CliRunner()

        assert 'Download and update monthly XBRL feeds' in result.output        result = runner.invoke(cli, ['feeds', 'update-daily-index', '--help'])

        assert result.exit_code == 0

    def test_update_full_index_help(self):        assert 'Download and update daily index feeds' in result.output

        """Test full index update help."""

        runner = CliRunner()    def test_update_monthly_xbrl_help(self):

        result = runner.invoke(cli, ['feeds', 'update-full-index', '--help'])        """Test monthly XBRL update help."""

        assert result.exit_code == 0        runner = CliRunner()

        assert 'Download and update the full index feed' in result.output        result = runner.invoke(cli, ['feeds', 'update-monthly-xbrl', '--help'])

        assert result.exit_code == 0

    def test_fetch_recent_rss_help(self):        assert 'Download and update monthly XBRL feeds' in result.output

        """Test RSS fetch help."""

        runner = CliRunner()    def test_update_full_index_help(self):

        result = runner.invoke(cli, ['feeds', 'fetch-recent-rss', '--help'])        """Test full index update help."""

        assert result.exit_code == 0        runner = CliRunner()

        assert 'Fetch recent filings from SEC EDGAR RSS feeds' in result.output        result = runner.invoke(cli, ['feeds', 'update-full-index', '--help'])

        assert result.exit_code == 0

    def test_update_all_help(self):        assert 'Download and update the full index feed' in result.output

        """Test update all help."""

        runner = CliRunner()

        result = runner.invoke(cli, ['feeds', 'update-all', '--help'])class TestWorkflowsCommands:

        assert result.exit_code == 0    """Test workflows command group."""

        assert 'Update all SEC EDGAR data feeds' in result.output

    def test_workflows_help(self):

        """Test workflows help."""

class TestUtilsCommands:        runner = CliRunner()

    """Test utils command group."""        result = runner.invoke(cli, ['workflows', '--help'])

        assert result.exit_code == 0

    def test_utils_help(self):        assert 'Run complete workflows' in result.output

        """Test utils help."""        assert 'daily' in result.output

        runner = CliRunner()        assert 'monthly' in result.output

        result = runner.invoke(cli, ['utils', '--help'])        assert 'rss' in result.output

        assert result.exit_code == 0        assert 'full-index' in result.output



    def test_utils_status(self):    def test_daily_workflow_help(self):

        """Test status command."""        """Test daily workflow help."""

        runner = CliRunner()        runner = CliRunner()

        with tempfile.TemporaryDirectory() as temp_dir:        result = runner.invoke(cli, ['workflows', 'daily', '--help'])

            result = runner.invoke(cli, [        assert result.exit_code == 0

                '--data-dir', temp_dir,        assert 'Run the daily workflow' in result.output

                'utils', 'status'

            ])    def test_monthly_workflow_help(self):

            assert result.exit_code == 0        """Test monthly workflow help."""

        runner = CliRunner()

    def test_utils_init(self):        result = runner.invoke(cli, ['workflows', 'monthly', '--help'])

        """Test init command."""        assert result.exit_code == 0

        runner = CliRunner()        assert 'Run the monthly workflow' in result.output

        with tempfile.TemporaryDirectory() as temp_dir:

            result = runner.invoke(cli, [    def test_rss_workflow_help(self):

                '--data-dir', temp_dir,        """Test RSS workflow help."""

                'utils', 'init'        runner = CliRunner()

            ])        result = runner.invoke(cli, ['workflows', 'rss', '--help'])

            assert result.exit_code == 0        assert result.exit_code == 0

        assert 'Run the RSS workflow' in result.output



class TestWorkflowCommands:    def test_full_index_workflow_help(self):

    """Test workflow command group."""        """Test full index workflow help."""

        runner = CliRunner()

    def test_workflows_help(self):        result = runner.invoke(cli, ['workflows', 'full-index', '--help'])

        """Test workflows help."""        assert result.exit_code == 0

        runner = CliRunner()        assert 'Run the full index workflow' in result.output

        result = runner.invoke(cli, ['workflows', '--help'])

        assert result.exit_code == 0    def test_unified_workflow_help(self):

        """Test unified workflow help."""

    @patch('py_sec_edgar.feeds.recent_filings.fetch_recent_rss_filings')        runner = CliRunner()

    def test_workflow_rss_help(self, mock_fetch):        result = runner.invoke(cli, ['workflows', 'unified', '--help'])

        """Test RSS workflow help."""        assert result.exit_code == 0

        runner = CliRunner()        assert 'Run all workflows in sequence' in result.output

        result = runner.invoke(cli, ['workflows', 'rss', '--help'])

        assert result.exit_code == 0

class TestProcessCommands:

    """Test process command group."""

class TestErrorHandling:

    """Test error handling scenarios."""    def test_process_help(self):

        """Test process help."""

    @patch('py_sec_edgar.feeds.recent_filings.fetch_recent_rss_filings')        runner = CliRunner()

    def test_rss_fetch_with_exception(self, mock_fetch):        result = runner.invoke(cli, ['process', '--help'])

        """Test RSS fetch with exception handling."""        assert result.exit_code == 0

        mock_fetch.side_effect = Exception("Network error")        assert 'Process SEC EDGAR filings' in result.output

        

        runner = CliRunner()    def test_process_filings_help(self):

        with tempfile.TemporaryDirectory() as temp_dir:        """Test process filings help."""

            result = runner.invoke(cli, [        runner = CliRunner()

                '--data-dir', temp_dir,        result = runner.invoke(cli, ['process', 'filings', '--help'])

                'feeds', 'fetch-recent-rss',        assert result.exit_code == 0

                '--count', '1'

            ])    def test_process_daily_help(self):

            assert result.exit_code != 0        """Test process daily help."""

        runner = CliRunner()

        result = runner.invoke(cli, ['process', 'daily', '--help'])

class TestIntegrationScenarios:        assert result.exit_code == 0

    """Test complete integration scenarios."""



    @patch('py_sec_edgar.feeds.recent_filings.fetch_recent_rss_filings')class TestFiltersCommands:

    def test_complete_rss_workflow(self, mock_fetch):    """Test filters command group."""

        """Test complete RSS workflow from fetch to save."""

        mock_filings = [    def test_filters_help(self):

            {        """Test filters help."""

                'id': 'test_filing_1',        runner = CliRunner()

                'ticker': 'AAPL',        result = runner.invoke(cli, ['filters', '--help'])

                'cik': '0000320193',        assert result.exit_code == 0

                'company_name': 'Apple Inc.',        assert 'Filter and analyze SEC EDGAR data' in result.output

                'form_type': '10-K',

                'period_reported': '2024-09-30',    def test_filter_by_ticker_help(self):

                'filing_name': 'Annual Report',        """Test filter by ticker help."""

                'filed_date': '2024-10-31',        runner = CliRunner()

                'filing_url': 'https://www.sec.gov/Archives/edgar/data/320193/test.htm',        result = runner.invoke(cli, ['filters', 'by-ticker', '--help'])

                'sec_link': 'https://www.sec.gov/Archives/edgar/data/320193/test.htm',        assert result.exit_code == 0

                'description': 'Annual Report Test',

            },    def test_filter_by_form_help(self):

            {        """Test filter by form help."""

                'id': 'test_filing_2',        runner = CliRunner()

                'ticker': 'MSFT',        result = runner.invoke(cli, ['filters', 'by-form', '--help'])

                'cik': '0000789019',        assert result.exit_code == 0

                'company_name': 'Microsoft Corporation',

                'form_type': '8-K',    def test_filter_by_date_help(self):

                'period_reported': '2024-10-30',        """Test filter by date help."""

                'filing_name': 'Current Report',        runner = CliRunner()

                'filed_date': '2024-10-30',        result = runner.invoke(cli, ['filters', 'by-date', '--help'])

                'filing_url': 'https://www.sec.gov/Archives/edgar/data/789019/test.htm',        assert result.exit_code == 0

                'sec_link': 'https://www.sec.gov/Archives/edgar/data/789019/test.htm',

                'description': 'Current Report Test',

            }class TestUtilsCommands:

        ]    """Test utils command group."""

        mock_fetch.return_value = mock_filings

            def test_utils_help(self):

        runner = CliRunner()        """Test utils help."""

        with tempfile.TemporaryDirectory() as temp_dir:        runner = CliRunner()

            result = runner.invoke(cli, [        result = runner.invoke(cli, ['utils', '--help'])

                '--data-dir', temp_dir,        assert result.exit_code == 0

                'feeds', 'fetch-recent-rss',        assert 'Utility commands for data management' in result.output

                '--count', '2',        assert 'status' in result.output

                '--save-json',        assert 'init' in result.output

                '--save-csv'        assert 'clean' in result.output

            ])        assert 'validate' in result.output

            

            assert result.exit_code == 0    def test_utils_status(self):

            assert 'Fetched 2 recent filings' in result.output        """Test utils status command."""

            assert 'Files saved: 2' in result.output        runner = CliRunner()

                    with tempfile.TemporaryDirectory() as temp_dir:

            # Check that files were created            result = runner.invoke(cli, [

            edgar_dir = Path(temp_dir) / "Archives" / "edgar" / "rss_feeds"                '--data-dir', temp_dir,

            assert edgar_dir.exists()                'utils', 'status'

                        ])

            json_files = list(edgar_dir.glob("*.json"))            assert result.exit_code == 0

            csv_files = list(edgar_dir.glob("*.csv"))            assert 'Data Directory:' in result.output

            

            assert len(json_files) >= 1    def test_utils_init(self):

            assert len(csv_files) >= 1        """Test utils init command."""

        runner = CliRunner()

    def test_data_directory_creation(self):        with tempfile.TemporaryDirectory() as temp_dir:

        """Test that data directories are created properly."""            result = runner.invoke(cli, [

        runner = CliRunner()                '--data-dir', temp_dir,

        with tempfile.TemporaryDirectory() as temp_dir:                'utils', 'init'

            test_data_dir = Path(temp_dir) / "test_sec_data"            ])

                        assert result.exit_code == 0

            result = runner.invoke(cli, [

                '--data-dir', str(test_data_dir),    def test_utils_validate(self):

                'utils', 'init'        """Test utils validate command."""

            ])        runner = CliRunner()

                    with tempfile.TemporaryDirectory() as temp_dir:

            assert result.exit_code == 0            result = runner.invoke(cli, [

            assert test_data_dir.exists()                '--data-dir', temp_dir,

                'utils', 'validate'

    @patch('py_sec_edgar.feeds.recent_filings.fetch_recent_rss_filings')            ])

    def test_multiple_operations_same_session(self, mock_fetch):            assert result.exit_code == 0

        """Test multiple operations in same session."""

        mock_fetch.return_value = []

        class TestErrorHandling:

        runner = CliRunner()    """Test error handling scenarios."""

        with tempfile.TemporaryDirectory() as temp_dir:

            # First operation: fetch some data    def test_invalid_command(self):

            result1 = runner.invoke(cli, [        """Test invalid command."""

                '--data-dir', temp_dir,        runner = CliRunner()

                'feeds', 'fetch-recent-rss',        result = runner.invoke(cli, ['invalid-command'])

                '--count', '1'        assert result.exit_code != 0

            ])        assert 'No such command' in result.output

            assert result1.exit_code == 0

                def test_invalid_option(self):

            # Second operation: check status        """Test invalid option."""

            result2 = runner.invoke(cli, [        runner = CliRunner()

                '--data-dir', temp_dir,        result = runner.invoke(cli, ['--invalid-option'])

                'utils', 'status'        assert result.exit_code != 0

            ])

            assert result2.exit_code == 0    def test_missing_required_arg(self):

        """Test missing required arguments where applicable."""

    def test_different_log_levels_same_session(self):        runner = CliRunner()

        """Test different log levels in same session."""        # Test scenarios where commands might fail due to missing args

        runner = CliRunner()        result = runner.invoke(cli, ['feeds', 'fetch-recent-rss', '--count'])

                assert result.exit_code != 0

        # Run with INFO level

        result1 = runner.invoke(cli, [    @patch('py_sec_edgar.feeds.recent_filings.fetch_recent_rss_filings')

            '--log-level', 'INFO',    def test_rss_fetch_network_error(self, mock_fetch):

            'utils', 'status'        """Test RSS fetch with network error."""

        ])        mock_fetch.side_effect = Exception("Network error")

        assert result1.exit_code == 0        

                runner = CliRunner()

        # Run with DEBUG level        with tempfile.TemporaryDirectory() as temp_dir:

        result2 = runner.invoke(cli, [            result = runner.invoke(cli, [

            '--log-level', 'DEBUG',                 '--data-dir', temp_dir,

            'utils', 'status'                'feeds', 'fetch-recent-rss',

        ])                '--count', '1'

        assert result2.exit_code == 0            ])

            assert result.exit_code != 0



if __name__ == '__main__':

    pytest.main([__file__])class TestIntegrationScenarios:
    """Test complete integration scenarios."""

    @patch('py_sec_edgar.feeds.recent_filings.fetch_recent_rss_filings')
    def test_complete_rss_workflow(self, mock_fetch):
        """Test complete RSS workflow from fetch to save."""
        mock_filings = [
            {
                'id': 'test_filing_1',
                'ticker': 'AAPL',
                'cik': '0000320193',
                'company_name': 'Apple Inc.',
                'form_type': '10-K',
                'period_reported': '2024-09-30',
                'filing_name': 'Annual Report',
                'filed_date': '2024-10-31',
                'filing_url': 'https://www.sec.gov/Archives/edgar/data/320193/test.htm',
                'sec_link': 'https://www.sec.gov/Archives/edgar/data/320193/test.htm',
                'description': 'Annual Report Test',
                'source': 'SEC RSS Feed',
                'status': 'active'
            },
            {
                'id': 'test_filing_2',
                'ticker': 'MSFT',
                'cik': '0000789019',
                'company_name': 'Microsoft Corporation',
                'form_type': '8-K',
                'period_reported': '',
                'filing_name': 'Current Report',
                'filed_date': '2024-11-01',
                'filing_url': 'https://www.sec.gov/Archives/edgar/data/789019/test.htm',
                'sec_link': 'https://www.sec.gov/Archives/edgar/data/789019/test.htm',
                'description': 'Current Report Test',
                'source': 'SEC RSS Feed',
                'status': 'active'
            }
        ]
        mock_fetch.return_value = mock_filings
        
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as temp_dir:
            result = runner.invoke(cli, [
                '--data-dir', temp_dir,
                'feeds', 'fetch-recent-rss',
                '--count', '2',
                '--save-json',
                '--save-csv'
            ])
            
            assert result.exit_code == 0
            assert 'Fetched 2 recent filings' in result.output
            assert 'Files saved: 2' in result.output
            
            # Check that files were created
            edgar_dir = Path(temp_dir) / "Archives" / "edgar" / "rss_feeds"
            assert edgar_dir.exists()
            
            json_files = list(edgar_dir.glob("*.json"))
            csv_files = list(edgar_dir.glob("*.csv"))
            
            assert len(json_files) >= 1
            assert len(csv_files) >= 1

    def test_data_directory_creation(self):
        """Test that data directories are created properly."""
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as temp_dir:
            test_data_dir = Path(temp_dir) / "test_sec_data"
            
            result = runner.invoke(cli, [
                '--data-dir', str(test_data_dir),
                'utils', 'init'
            ])
            
            assert result.exit_code == 0
            assert test_data_dir.exists()

    def test_log_level_propagation(self):
        """Test that log levels are properly set."""
        runner = CliRunner()
        
        # Test DEBUG level
        result = runner.invoke(cli, [
            '--log-level', 'DEBUG',
            'utils', 'status'
        ])
        assert result.exit_code == 0
        
        # Test ERROR level
        result = runner.invoke(cli, [
            '--log-level', 'ERROR',
            'utils', 'status'
        ])
        assert result.exit_code == 0


class TestCommandChaining:
    """Test chaining multiple commands and complex scenarios."""

    @patch('py_sec_edgar.feeds.recent_filings.fetch_recent_rss_filings')
    def test_multiple_operations_same_session(self, mock_fetch):
        """Test running multiple operations in same session."""
        mock_fetch.return_value = [
            {
                'id': 'test_1',
                'company_name': 'Test Company',
                'form_type': '10-K',
                'filed_date': '2025-01-01',
                'filing_url': 'https://example.com/filing1'
            }
        ]
        
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as temp_dir:
            # First operation: fetch RSS
            result1 = runner.invoke(cli, [
                '--data-dir', temp_dir,
                'feeds', 'fetch-recent-rss',
                '--count', '1',
                '--no-save-database'
            ])
            assert result1.exit_code == 0
            
            # Second operation: check status
            result2 = runner.invoke(cli, [
                '--data-dir', temp_dir,
                'utils', 'status'
            ])
            assert result2.exit_code == 0

    def test_different_log_levels_same_session(self):
        """Test different log levels in same session."""
        runner = CliRunner()
        
        # Run with INFO level
        result1 = runner.invoke(cli, [
            '--log-level', 'INFO',
            'utils', 'status'
        ])
        assert result1.exit_code == 0
        
        # Run with DEBUG level
        result2 = runner.invoke(cli, [
            '--log-level', 'DEBUG',
            'utils', 'status'
        ])
        assert result2.exit_code == 0


if __name__ == '__main__':
    pytest.main([__file__])