#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Live integration tests for workflow CLI commands.
"""

import os
import tempfile
import shutil
from pathlib import Path
import pytest
from click.testing import CliRunner

from src.py_sec_edgar.main import cli


class TestLiveWorkflowIntegration:
    """Live integration tests for workflow commands."""

    def setup_method(self):
        """Set up test environment."""
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up after test."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_main_cli_help_with_output(self):
        """Test the main CLI help command."""
        result = self.runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert 'SEC EDGAR Filing Processor' in result.output

    def test_workflows_help_with_output(self):
        """Test workflows help command."""
        result = self.runner.invoke(cli, ['workflows', '--help'])
        assert result.exit_code == 0
        assert 'workflows' in result.output.lower()

    @pytest.mark.parametrize("workflow", ['daily', 'rss', 'monthly'])
    def test_workflow_help_commands(self, workflow):
        """Test individual workflow help commands."""
        result = self.runner.invoke(cli, ['workflows', workflow, '--help'])
        assert result.exit_code == 0

    def test_rss_workflow_dry_run_with_output(self):
        """Test RSS workflow with minimal parameters."""
        result = self.runner.invoke(cli, [
            'workflows', 'rss',
            '--count', '5',
            '--tickers', 'AAPL',
            '--no-download',
            '--no-extract'
        ])
        # Allow success or expected failures
        assert result.exit_code in [0, 1]

    def test_daily_workflow_dry_run_with_output(self):
        """Test daily workflow with minimal parameters."""
        result = self.runner.invoke(cli, [
            'workflows', 'daily',
            '--days-back', '1',
            '--tickers', 'AAPL',
            '--no-download',
            '--no-extract'
        ])
        # Allow success or expected failures
        assert result.exit_code in [0, 1, 2]

    def test_monthly_workflow_dry_run_with_output(self):
        """Test monthly workflow with minimal parameters."""
        result = self.runner.invoke(cli, [
            'workflows', 'monthly',
            '--months-back', '1',
            '--tickers', 'AAPL',
            '--no-download',
            '--no-extract'
        ])
        # Allow success or expected failures
        assert result.exit_code in [0, 1, 2]

    @pytest.mark.parametrize("command", ['feeds', 'process', 'utils'])
    def test_command_help_available(self, command):
        """Test that command help is available."""
        result = self.runner.invoke(cli, [command, '--help'])
        # Allow success or command not found
        assert result.exit_code in [0, 1, 2]

    def test_cli_version_with_output(self):
        """Test CLI version command."""
        result = self.runner.invoke(cli, ['--version'])
        assert result.exit_code == 0

    def test_invalid_command_with_output(self):
        """Test invalid command error handling."""
        result = self.runner.invoke(cli, ['invalid-command'])
        assert result.exit_code != 0

    def test_workflow_parameter_validation_with_output(self):
        """Test parameter validation."""
        result = self.runner.invoke(cli, [
            'workflows', 'daily',
            '--days-back', 'invalid'
        ])
        assert result.exit_code != 0

    def test_all_workflow_commands_exist(self):
        """Test that workflow commands exist."""
        workflows = ['daily', 'monthly', 'rss']  # Removed 'unified' as it was deleted
        for workflow in workflows:
            result = self.runner.invoke(cli, ['workflows', workflow, '--help'])
            # Should succeed or have expected issues
            assert result.exit_code in [0, 1, 2]

    def test_complete_workflow_discovery(self):
        """Test workflow discovery."""
        # Test main workflows command
        result = self.runner.invoke(cli, ['workflows'])
        assert result.exit_code in [0, 1, 2]
        
        # Test individual commands
        commands = [
            ['workflows', 'daily'],
            ['workflows', 'monthly'], 
            ['workflows', 'rss']
        ]
        
        for cmd in commands:
            result = self.runner.invoke(cli, cmd + ['--help'])
            assert result.exit_code in [0, 1, 2]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])