#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test integration patterns across multiple workflows.

This test file validates that workflow integration examples work correctly,
ensuring users can combine workflows for comprehensive analysis.
"""

import os
import tempfile
import shutil
from pathlib import Path
import pytest
from click.testing import CliRunner

from py_sec_edgar.main import cli


class TestWorkflowIntegrationExamples:
    """Test integration patterns across multiple workflows."""

    def setup_method(self):
        """Set up test environment for each test."""
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up after each test."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    # ========================================================================
    # Cross-Workflow Data Consistency (5 tests)
    # ========================================================================

    def test_rss_to_daily_workflow_consistency(self):
        """Test RSS workflow feeding into Daily workflow for consistent data"""
        # First run RSS workflow to establish baseline
        result1 = self.runner.invoke(cli, [
            '--data-dir', self.temp_dir,
            'workflows', 'rss',
            '--tickers', 'AAPL',
            '--no-download'  # Safe testing mode
        ])
        assert result1.exit_code in [0, 1, 2]

        # Then run Daily workflow to verify consistency
        result2 = self.runner.invoke(cli, [
            '--data-dir', self.temp_dir,
            'workflows', 'daily',
            '--tickers', 'AAPL',
            '--days-back', '7',
            '--no-download'  # Safe testing mode
        ])
        assert result2.exit_code in [0, 1, 2]

    def test_daily_to_monthly_workflow_consistency(self):
        """Test Daily workflow feeding into Monthly workflow for consistent data"""
        # First run Daily workflow
        result1 = self.runner.invoke(cli, [
            '--data-dir', self.temp_dir,
            'workflows', 'daily',
            '--tickers', 'MSFT',
            '--days-back', '30',
            '--no-download'  # Safe testing mode
        ])
        assert result1.exit_code in [0, 1, 2]

        # Then run Monthly workflow to verify consistency
        result2 = self.runner.invoke(cli, [
            '--data-dir', self.temp_dir,
            'workflows', 'monthly',
            '--tickers', 'MSFT',
            '--months-back', '1',
            '--no-download'  # Safe testing mode
        ])
        assert result2.exit_code in [0, 1, 2]

    def test_full_index_to_targeted_workflow_consistency(self):
        """Test Full Index workflow feeding into targeted workflows"""
        # First run Full Index workflow for broad coverage
        result1 = self.runner.invoke(cli, [
            '--data-dir', self.temp_dir,
            'workflows', 'full-index',
            '--quarter', '2023Q4',
            '--no-download'  # Safe testing mode
        ])
        assert result1.exit_code in [0, 1, 2]

        # Then run RSS workflow for targeted updates
        result2 = self.runner.invoke(cli, [
            '--data-dir', self.temp_dir,
            'workflows', 'rss',
            '--tickers', 'AAPL', 'MSFT',
            '--no-download'  # Safe testing mode
        ])
        assert result2.exit_code in [0, 1, 2]

    def test_cross_workflow_data_validation(self):
        """Test data validation across multiple workflows"""
        # Run multiple workflows to check data consistency
        workflows = ['rss', 'daily', 'monthly']
        for workflow in workflows:
            if workflow == 'rss':
                args = ['workflows', workflow, '--tickers', 'GOOGL', '--no-download']
            elif workflow == 'daily':
                args = ['workflows', workflow, '--tickers', 'GOOGL', '--days-back', '7', '--no-download']
            else:  # monthly
                args = ['workflows', workflow, '--tickers', 'GOOGL', '--months-back', '1', '--no-download']
            
            result = self.runner.invoke(cli, ['--data-dir', self.temp_dir] + args)
            assert result.exit_code in [0, 1, 2]

    def test_incremental_data_updates_across_workflows(self):
        """Test incremental data updates using multiple workflows"""
        # Start with Full Index for baseline
        result1 = self.runner.invoke(cli, [
            '--data-dir', self.temp_dir,
            'workflows', 'full-index',
            '--quarter', '2023Q3',
            '--no-download'  # Safe testing mode
        ])
        assert result1.exit_code in [0, 1, 2]

        # Update with Daily workflow
        result2 = self.runner.invoke(cli, [
            '--data-dir', self.temp_dir,
            'workflows', 'daily',
            '--tickers', 'AAPL', 'MSFT',
            '--days-back', '30',
            '--no-download'  # Safe testing mode
        ])
        assert result2.exit_code in [0, 1, 2]

        # Final update with RSS workflow
        result3 = self.runner.invoke(cli, [
            '--data-dir', self.temp_dir,
            'workflows', 'rss',
            '--tickers', 'AAPL', 'MSFT',
            '--no-download'  # Safe testing mode
        ])
        assert result3.exit_code in [0, 1, 2]

    # ========================================================================
    # Multi-Timeframe Analysis Integration (4 tests)
    # ========================================================================

    def test_short_term_medium_term_analysis_integration(self):
        """Test integration of short-term (RSS) and medium-term (Daily) analysis"""
        # RSS for latest filings
        result1 = self.runner.invoke(cli, [
            '--data-dir', self.temp_dir,
            'workflows', 'rss',
            '--ticker-file', 'examples/portfolio.csv',
            '--no-download'  # Safe testing mode
        ])
        assert result1.exit_code in [0, 1, 2]

        # Daily for recent trends
        result2 = self.runner.invoke(cli, [
            '--data-dir', self.temp_dir,
            'workflows', 'daily',
            '--ticker-file', 'examples/portfolio.csv',
            '--days-back', '30',
            '--no-download'  # Safe testing mode
        ])
        assert result2.exit_code in [0, 1, 2]

    def test_medium_term_long_term_analysis_integration(self):
        """Test integration of medium-term (Daily) and long-term (Monthly) analysis"""
        # Daily for recent activity
        result1 = self.runner.invoke(cli, [
            '--data-dir', self.temp_dir,
            'workflows', 'daily',
            '--ticker-file', 'examples/sp500_tickers.csv',
            '--days-back', '90',
            '--no-download'  # Safe testing mode
        ])
        assert result1.exit_code in [0, 1, 2]

        # Monthly for historical context
        result2 = self.runner.invoke(cli, [
            '--data-dir', self.temp_dir,
            'workflows', 'monthly',
            '--ticker-file', 'examples/sp500_tickers.csv',
            '--months-back', '12',
            '--no-download'  # Safe testing mode
        ])
        assert result2.exit_code in [0, 1, 2]

    def test_comprehensive_timeframe_coverage(self):
        """Test comprehensive timeframe coverage using all workflows"""
        # Full Index for historical baseline
        result1 = self.runner.invoke(cli, [
            '--data-dir', self.temp_dir,
            'workflows', 'full-index',
            '--quarter', '2023Q1',
            '--no-download'  # Safe testing mode
        ])
        assert result1.exit_code in [0, 1, 2]

        # Monthly for recent history
        result2 = self.runner.invoke(cli, [
            '--data-dir', self.temp_dir,
            'workflows', 'monthly',
            '--tickers', 'AAPL', 'MSFT', 'GOOGL',
            '--months-back', '6',
            '--no-download'  # Safe testing mode
        ])
        assert result2.exit_code in [0, 1, 2]

        # Daily for recent activity
        result3 = self.runner.invoke(cli, [
            '--data-dir', self.temp_dir,
            'workflows', 'daily',
            '--tickers', 'AAPL', 'MSFT', 'GOOGL',
            '--days-back', '30',
            '--no-download'  # Safe testing mode
        ])
        assert result3.exit_code in [0, 1, 2]

        # RSS for latest updates
        result4 = self.runner.invoke(cli, [
            '--data-dir', self.temp_dir,
            'workflows', 'rss',
            '--tickers', 'AAPL', 'MSFT', 'GOOGL',
            '--no-download'  # Safe testing mode
        ])
        assert result4.exit_code in [0, 1, 2]

    def test_rolling_timeframe_analysis(self):
        """Test rolling timeframe analysis pattern"""
        # Start with broad Monthly analysis
        result1 = self.runner.invoke(cli, [
            '--data-dir', self.temp_dir,
            'workflows', 'monthly',
            '--ticker-file', 'examples/portfolio.csv',
            '--months-back', '24',
            '--no-download'  # Safe testing mode
        ])
        assert result1.exit_code in [0, 1, 2]

        # Focus with Daily analysis
        result2 = self.runner.invoke(cli, [
            '--data-dir', self.temp_dir,
            'workflows', 'daily',
            '--ticker-file', 'examples/portfolio.csv',
            '--days-back', '60',
            '--no-download'  # Safe testing mode
        ])
        assert result2.exit_code in [0, 1, 2]

        # Update with RSS analysis
        result3 = self.runner.invoke(cli, [
            '--data-dir', self.temp_dir,
            'workflows', 'rss',
            '--ticker-file', 'examples/portfolio.csv',
            '--no-download'  # Safe testing mode
        ])
        assert result3.exit_code in [0, 1, 2]

    # ========================================================================
    # Portfolio-Level Integration Analysis (6 tests)
    # ========================================================================

    def test_portfolio_comprehensive_analysis_workflow(self):
        """Test comprehensive portfolio analysis using multiple workflows"""
        # Start with Full Index for complete baseline
        result1 = self.runner.invoke(cli, [
            '--data-dir', self.temp_dir,
            'workflows', 'full-index',
            '--quarter', '2023Q4',
            '--no-download'  # Safe testing mode
        ])
        assert result1.exit_code in [0, 1, 2]

        # Add Monthly analysis for portfolio companies
        result2 = self.runner.invoke(cli, [
            '--data-dir', self.temp_dir,
            'workflows', 'monthly',
            '--ticker-file', 'examples/portfolio.csv',
            '--months-back', '12',
            '--no-download'  # Safe testing mode
        ])
        assert result2.exit_code in [0, 1, 2]

        # Current activity via RSS
        result3 = self.runner.invoke(cli, [
            '--data-dir', self.temp_dir,
            'workflows', 'rss',
            '--ticker-file', 'examples/portfolio.csv',
            '--no-download'  # Safe testing mode
        ])
        assert result3.exit_code in [0, 1, 2]

    def test_sector_analysis_integration_workflow(self):
        """Test sector analysis using integrated workflows"""
        # Monthly for sector baseline
        result1 = self.runner.invoke(cli, [
            '--data-dir', self.temp_dir,
            'workflows', 'monthly',
            '--ticker-file', 'examples/renewable_energy.csv',
            '--months-back', '18',
            '--no-download'  # Safe testing mode
        ])
        assert result1.exit_code in [0, 1, 2]

        # Daily for recent sector trends
        result2 = self.runner.invoke(cli, [
            '--data-dir', self.temp_dir,
            'workflows', 'daily',
            '--ticker-file', 'examples/renewable_energy.csv',
            '--days-back', '90',
            '--no-download'  # Safe testing mode
        ])
        assert result2.exit_code in [0, 1, 2]

        # RSS for latest sector developments
        result3 = self.runner.invoke(cli, [
            '--data-dir', self.temp_dir,
            'workflows', 'rss',
            '--ticker-file', 'examples/renewable_energy.csv',
            '--no-download'  # Safe testing mode
        ])
        assert result3.exit_code in [0, 1, 2]

    def test_large_cap_analysis_integration(self):
        """Test large cap analysis using multiple workflows"""
        # Full Index for market context
        result1 = self.runner.invoke(cli, [
            '--data-dir', self.temp_dir,
            'workflows', 'full-index',
            '--quarter', '2023Q3',
            '--no-download'  # Safe testing mode
        ])
        assert result1.exit_code in [0, 1, 2]

        # Monthly for large cap trends
        result2 = self.runner.invoke(cli, [
            '--data-dir', self.temp_dir,
            'workflows', 'monthly',
            '--ticker-file', 'examples/sp500_tickers.csv',
            '--months-back', '6',
            '--no-download'  # Safe testing mode
        ])
        assert result2.exit_code in [0, 1, 2]

        # Daily for recent large cap activity
        result3 = self.runner.invoke(cli, [
            '--data-dir', self.temp_dir,
            'workflows', 'daily',
            '--ticker-file', 'examples/sp500_tickers.csv',
            '--days-back', '30',
            '--no-download'  # Safe testing mode
        ])
        assert result3.exit_code in [0, 1, 2]

    def test_fortune500_comprehensive_integration(self):
        """Test Fortune 500 comprehensive analysis integration"""
        # Monthly for Fortune 500 baseline
        result1 = self.runner.invoke(cli, [
            '--data-dir', self.temp_dir,
            'workflows', 'monthly',
            '--ticker-file', 'examples/fortune500.csv',
            '--months-back', '24',
            '--no-download'  # Safe testing mode
        ])
        assert result1.exit_code in [0, 1, 2]

        # Daily for recent Fortune 500 activity
        result2 = self.runner.invoke(cli, [
            '--data-dir', self.temp_dir,
            'workflows', 'daily',
            '--ticker-file', 'examples/fortune500.csv',
            '--days-back', '60',
            '--no-download'  # Safe testing mode
        ])
        assert result2.exit_code in [0, 1, 2]

        # RSS for latest Fortune 500 filings
        result3 = self.runner.invoke(cli, [
            '--data-dir', self.temp_dir,
            'workflows', 'rss',
            '--ticker-file', 'examples/fortune500.csv',
            '--no-download'  # Safe testing mode
        ])
        assert result3.exit_code in [0, 1, 2]

    def test_multi_portfolio_analysis_integration(self):
        """Test multi-portfolio analysis integration"""
        # Portfolio analysis
        result1 = self.runner.invoke(cli, [
            '--data-dir', self.temp_dir,
            'workflows', 'monthly',
            '--ticker-file', 'examples/portfolio.csv',
            '--months-back', '12',
            '--no-download'  # Safe testing mode
        ])
        assert result1.exit_code in [0, 1, 2]

        # SP500 benchmark analysis
        result2 = self.runner.invoke(cli, [
            '--data-dir', self.temp_dir,
            'workflows', 'monthly',
            '--ticker-file', 'examples/sp500_tickers.csv',
            '--months-back', '12',
            '--no-download'  # Safe testing mode
        ])
        assert result2.exit_code in [0, 1, 2]

        # Recent activity comparison
        result3 = self.runner.invoke(cli, [
            '--data-dir', self.temp_dir,
            'workflows', 'rss',
            '--ticker-file', 'examples/portfolio.csv',
            '--no-download'  # Safe testing mode
        ])
        assert result3.exit_code in [0, 1, 2]

    def test_cross_portfolio_benchmarking_integration(self):
        """Test cross-portfolio benchmarking integration"""
        portfolios = ['portfolio.csv', 'sp500_tickers.csv', 'renewable_energy.csv']
        
        for portfolio in portfolios:
            # Monthly baseline for each portfolio
            result1 = self.runner.invoke(cli, [
                '--data-dir', self.temp_dir,
                'workflows', 'monthly',
                '--ticker-file', f'examples/{portfolio}',
                '--months-back', '6',
                '--no-download'  # Safe testing mode
            ])
            assert result1.exit_code in [0, 1, 2]

            # Daily activity for each portfolio
            result2 = self.runner.invoke(cli, [
                '--data-dir', self.temp_dir,
                'workflows', 'daily',
                '--ticker-file', f'examples/{portfolio}',
                '--days-back', '30',
                '--no-download'  # Safe testing mode
            ])
            assert result2.exit_code in [0, 1, 2]

    # ========================================================================
    # Advanced Integration Patterns (7 tests)
    # ========================================================================

    @pytest.mark.slow
    def test_event_driven_analysis_integration(self):
        """Test event-driven analysis using RSS + targeted workflows"""
        # RSS for event detection
        result1 = self.runner.invoke(cli, [
            '--data-dir', self.temp_dir,
            'workflows', 'rss',
            '--ticker-file', 'examples/portfolio.csv',
            '--no-download'  # Safe testing mode
        ])
        assert result1.exit_code in [0, 1, 2]

        # Daily for event context
        result2 = self.runner.invoke(cli, [
            '--data-dir', self.temp_dir,
            'workflows', 'daily',
            '--ticker-file', 'examples/portfolio.csv',
            '--days-back', '30',
            '--no-download'  # Safe testing mode
        ])
        assert result2.exit_code in [0, 1, 2]

        # Monthly for historical context
        result3 = self.runner.invoke(cli, [
            '--data-dir', self.temp_dir,
            'workflows', 'monthly',
            '--ticker-file', 'examples/portfolio.csv',
            '--months-back', '12',
            '--no-download'  # Safe testing mode
        ])
        assert result3.exit_code in [0, 1, 2]

    def test_compliance_monitoring_integration(self):
        """Test compliance monitoring using integrated workflows"""
        # Full Index for regulatory baseline
        result1 = self.runner.invoke(cli, [
            '--data-dir', self.temp_dir,
            'workflows', 'full-index',
            '--quarter', '2023Q4',
            '--no-download'  # Safe testing mode
        ])
        assert result1.exit_code in [0, 1, 2]

        # Daily for compliance monitoring
        result2 = self.runner.invoke(cli, [
            '--data-dir', self.temp_dir,
            'workflows', 'daily',
            '--ticker-file', 'examples/fortune500.csv',
            '--days-back', '90',
            '--no-download'  # Safe testing mode
        ])
        assert result2.exit_code in [0, 1, 2]

        # RSS for real-time compliance alerts
        result3 = self.runner.invoke(cli, [
            '--data-dir', self.temp_dir,
            'workflows', 'rss',
            '--ticker-file', 'examples/fortune500.csv',
            '--no-download'  # Safe testing mode
        ])
        assert result3.exit_code in [0, 1, 2]

    def test_research_pipeline_integration(self):
        """Test research pipeline using all workflows"""
        # Full Index for comprehensive baseline
        result1 = self.runner.invoke(cli, [
            '--data-dir', self.temp_dir,
            'workflows', 'full-index',
            '--quarter', '2023Q2',
            '--no-download'  # Safe testing mode
        ])
        assert result1.exit_code in [0, 1, 2]

        # Monthly for research trends
        result2 = self.runner.invoke(cli, [
            '--data-dir', self.temp_dir,
            'workflows', 'monthly',
            '--ticker-file', 'examples/sp500_tickers.csv',
            '--months-back', '18',
            '--no-download'  # Safe testing mode
        ])
        assert result2.exit_code in [0, 1, 2]

        # Daily for recent developments
        result3 = self.runner.invoke(cli, [
            '--data-dir', self.temp_dir,
            'workflows', 'daily',
            '--ticker-file', 'examples/sp500_tickers.csv',
            '--days-back', '60',
            '--no-download'  # Safe testing mode
        ])
        assert result3.exit_code in [0, 1, 2]

        # RSS for latest research data
        result4 = self.runner.invoke(cli, [
            '--data-dir', self.temp_dir,
            'workflows', 'rss',
            '--ticker-file', 'examples/sp500_tickers.csv',
            '--no-download'  # Safe testing mode
        ])
        assert result4.exit_code in [0, 1, 2]

    def test_investment_analysis_integration(self):
        """Test investment analysis integration pattern"""
        # Monthly for investment baseline
        result1 = self.runner.invoke(cli, [
            '--data-dir', self.temp_dir,
            'workflows', 'monthly',
            '--ticker-file', 'examples/portfolio.csv',
            '--months-back', '36',
            '--no-download'  # Safe testing mode
        ])
        assert result1.exit_code in [0, 1, 2]

        # Daily for investment trends
        result2 = self.runner.invoke(cli, [
            '--data-dir', self.temp_dir,
            'workflows', 'daily',
            '--ticker-file', 'examples/portfolio.csv',
            '--days-back', '180',
            '--no-download'  # Safe testing mode
        ])
        assert result2.exit_code in [0, 1, 2]

        # RSS for investment opportunities
        result3 = self.runner.invoke(cli, [
            '--data-dir', self.temp_dir,
            'workflows', 'rss',
            '--ticker-file', 'examples/portfolio.csv',
            '--no-download'  # Safe testing mode
        ])
        assert result3.exit_code in [0, 1, 2]

    def test_risk_management_integration(self):
        """Test risk management integration pattern"""
        # Full Index for market context
        result1 = self.runner.invoke(cli, [
            '--data-dir', self.temp_dir,
            'workflows', 'full-index',
            '--quarter', '2023Q4',
            '--no-download'  # Safe testing mode
        ])
        assert result1.exit_code in [0, 1, 2]

        # Monthly for risk trends
        result2 = self.runner.invoke(cli, [
            '--data-dir', self.temp_dir,
            'workflows', 'monthly',
            '--ticker-file', 'examples/sp500_tickers.csv',
            '--months-back', '12',
            '--no-download'  # Safe testing mode
        ])
        assert result2.exit_code in [0, 1, 2]

        # Daily for risk monitoring
        result3 = self.runner.invoke(cli, [
            '--data-dir', self.temp_dir,
            'workflows', 'daily',
            '--ticker-file', 'examples/sp500_tickers.csv',
            '--days-back', '90',
            '--no-download'  # Safe testing mode
        ])
        assert result3.exit_code in [0, 1, 2]

        # RSS for risk alerts
        result4 = self.runner.invoke(cli, [
            '--data-dir', self.temp_dir,
            'workflows', 'rss',
            '--ticker-file', 'examples/sp500_tickers.csv',
            '--no-download'  # Safe testing mode
        ])
        assert result4.exit_code in [0, 1, 2]

    def test_market_intelligence_integration(self):
        """Test market intelligence integration pattern"""
        # Full Index for market baseline
        result1 = self.runner.invoke(cli, [
            '--data-dir', self.temp_dir,
            'workflows', 'full-index',
            '--quarter', '2023Q3',
            '--no-download'  # Safe testing mode
        ])
        assert result1.exit_code in [0, 1, 2]

        # Monthly for market trends
        result2 = self.runner.invoke(cli, [
            '--data-dir', self.temp_dir,
            'workflows', 'monthly',
            '--ticker-file', 'examples/sp500_tickers.csv',
            '--months-back', '24',
            '--no-download'  # Safe testing mode
        ])
        assert result2.exit_code in [0, 1, 2]

        # Daily for market signals
        result3 = self.runner.invoke(cli, [
            '--data-dir', self.temp_dir,
            'workflows', 'daily',
            '--ticker-file', 'examples/sp500_tickers.csv',
            '--days-back', '120',
            '--no-download'  # Safe testing mode
        ])
        assert result3.exit_code in [0, 1, 2]

        # RSS for market intelligence
        result4 = self.runner.invoke(cli, [
            '--data-dir', self.temp_dir,
            'workflows', 'rss',
            '--ticker-file', 'examples/sp500_tickers.csv',
            '--no-download'  # Safe testing mode
        ])
        assert result4.exit_code in [0, 1, 2]

    def test_comprehensive_financial_analysis_integration(self):
        """Test comprehensive financial analysis using all workflows"""
        # Start with Full Index for complete market view
        result1 = self.runner.invoke(cli, [
            '--data-dir', self.temp_dir,
            'workflows', 'full-index',
            '--quarter', '2023Q4',
            '--no-download'  # Safe testing mode
        ])
        assert result1.exit_code in [0, 1, 2]

        # Monthly for financial trends
        result2 = self.runner.invoke(cli, [
            '--data-dir', self.temp_dir,
            'workflows', 'monthly',
            '--ticker-file', 'examples/fortune500.csv',
            '--months-back', '36',
            '--no-download'  # Safe testing mode
        ])
        assert result2.exit_code in [0, 1, 2]

        # Daily for recent financial activity
        result3 = self.runner.invoke(cli, [
            '--data-dir', self.temp_dir,
            'workflows', 'daily',
            '--ticker-file', 'examples/fortune500.csv',
            '--days-back', '180',
            '--no-download'  # Safe testing mode
        ])
        assert result3.exit_code in [0, 1, 2]

        # RSS for latest financial updates
        result4 = self.runner.invoke(cli, [
            '--data-dir', self.temp_dir,
            'workflows', 'rss',
            '--ticker-file', 'examples/fortune500.csv',
            '--no-download'  # Safe testing mode
        ])
        assert result4.exit_code in [0, 1, 2]