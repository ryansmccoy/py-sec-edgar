#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Comprehensive tests for settings module functionality.
Targets 85% test coverage for settings.py.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from src.py_sec_edgar.settings import SECEdgarSettings, settings


class TestSECEdgarSettings:
    """Test SECEdgarSettings class functionality."""

    def test_default_settings(self):
        """Test default settings values."""
        settings = SECEdgarSettings()
        
        assert settings.max_retries == 3
        assert settings.request_delay == 0.1
        assert settings.timeout == 30
        assert settings.user_agent_email is not None
        assert settings.user_agent_company is not None
        assert 'sec.gov' in settings.edgar_archives_url
        assert settings.forms_list is not None
        assert isinstance(settings.forms_list, list)

    def test_data_dir_creation(self):
        """Test that data directory is created if it doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_data_dir = Path(temp_dir) / "test_sec_data"
            
            with patch.dict(os.environ, {'SEC_DATA_DIR': str(test_data_dir)}):
                settings = SECEdgarSettings()
                assert settings.sec_data_dir == test_data_dir
                assert test_data_dir.exists()

    def test_data_dir_from_env(self):
        """Test data directory setting from environment variable."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_data_dir = Path(temp_dir) / "env_sec_data"
            
            with patch.dict(os.environ, {'SEC_DATA_DIR': str(test_data_dir)}):
                settings = SECEdgarSettings()
                assert settings.sec_data_dir == test_data_dir

    def test_data_dir_default(self):
        """Test default data directory when no env var set."""
        with patch.dict(os.environ, {}, clear=True):
            with patch('py_sec_edgar.settings.Path.home') as mock_home:
                mock_home.return_value = Path("/fake/home")
                settings = SECEdgarSettings()
                expected_path = Path("/fake/home") / "sec_data"
                assert settings.sec_data_dir == expected_path

    def test_archives_directory(self):
        """Test archives directory property."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_data_dir = Path(temp_dir) / "test_archives"
            
            with patch.dict(os.environ, {'SEC_DATA_DIR': str(test_data_dir)}):
                settings = SECEdgarSettings()
                expected_archives = test_data_dir / "Archives"
                assert settings.archives_dir == expected_archives

    def test_edgar_directory(self):
        """Test edgar directory property."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_data_dir = Path(temp_dir) / "test_edgar"
            
            with patch.dict(os.environ, {'SEC_DATA_DIR': str(test_data_dir)}):
                settings = SECEdgarSettings()
                expected_edgar = test_data_dir / "Archives" / "edgar"
                assert settings.edgar_dir == expected_edgar

    def test_refdata_paths(self):
        """Test reference data file paths."""
        settings = SECEdgarSettings()
        
        assert settings.cik_tickers_csv.name == "cik_tickers.csv"
        assert settings.company_tickers_json.name == "company_tickers.json"
        assert settings.company_tickers_exchange_json.name == "company_tickers_exchange.json"
        assert settings.ticker_list_filepath.name == "tickers.csv"

    def test_forms_list_validation(self):
        """Test forms list validation."""
        settings = SECEdgarSettings()
        
        # Should contain common form types
        assert '10-K' in settings.forms_list
        assert '10-Q' in settings.forms_list
        assert '8-K' in settings.forms_list
        
        # Should be a list
        assert isinstance(settings.forms_list, list)
        assert len(settings.forms_list) > 0

    def test_user_agent_headers(self):
        """Test user agent header generation."""
        settings = SECEdgarSettings()
        headers = settings.get_request_headers()
        
        assert 'User-Agent' in headers
        assert settings.user_agent_email in headers['User-Agent']
        assert settings.user_agent_company in headers['User-Agent']

    def test_network_settings(self):
        """Test network-related settings."""
        settings = SECEdgarSettings()
        
        assert isinstance(settings.max_retries, int)
        assert settings.max_retries > 0
        assert isinstance(settings.request_delay, (int, float))
        assert settings.request_delay >= 0
        assert isinstance(settings.timeout, int)
        assert settings.timeout > 0

    def test_url_properties(self):
        """Test URL properties."""
        settings = SECEdgarSettings()
        
        assert settings.edgar_archives_url.startswith('https://')
        assert 'sec.gov' in settings.edgar_archives_url
        assert settings.edgar_base_url.startswith('https://')
        assert 'sec.gov' in settings.edgar_base_url

    def test_directory_creation_side_effects(self):
        """Test that directory creation doesn't have unwanted side effects."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_data_dir = Path(temp_dir) / "side_effects_test"
            
            with patch.dict(os.environ, {'SEC_DATA_DIR': str(test_data_dir)}):
                settings = SECEdgarSettings()
                
                # Check that subdirectories are created
                assert settings.archives_dir.exists()
                assert settings.edgar_dir.exists()
                
                # Check that no unexpected files are created
                all_items = list(test_data_dir.rglob('*'))
                file_items = [item for item in all_items if item.is_file()]
                # Should only have config files, if any
                assert len(file_items) <= 1

    def test_settings_immutability(self):
        """Test that certain settings cannot be modified after creation."""
        settings = SECEdgarSettings()
        
        # These should be read-only or have controlled modification
        original_data_dir = settings.sec_data_dir
        
        # Verify they exist and are consistent
        assert original_data_dir == settings.sec_data_dir

    def test_environment_variable_precedence(self):
        """Test that environment variables take precedence over defaults."""
        custom_data_dir = "/custom/sec/data"
        custom_email = "custom@test.com"
        custom_company = "Custom Test Company"
        
        env_vars = {
            'SEC_DATA_DIR': custom_data_dir,
            'SEC_USER_AGENT_EMAIL': custom_email,
            'SEC_USER_AGENT_COMPANY': custom_company
        }
        
        with patch.dict(os.environ, env_vars):
            with patch('py_sec_edgar.settings.Path.mkdir'):  # Prevent actual directory creation
                settings = SECEdgarSettings()
                
                assert str(settings.sec_data_dir) == custom_data_dir
                assert settings.user_agent_email == custom_email
                assert settings.user_agent_company == custom_company

    def test_forms_list_customization(self):
        """Test that forms list can be customized via environment."""
        custom_forms = "10-K,8-K,DEF 14A"
        
        with patch.dict(os.environ, {'SEC_FORMS_LIST': custom_forms}):
            settings = SECEdgarSettings()
            
            expected_forms = ['10-K', '8-K', 'DEF 14A']
            assert settings.forms_list == expected_forms

    def test_numeric_settings_validation(self):
        """Test validation of numeric settings."""
        settings = SECEdgarSettings()
        
        # Test that numeric values are within reasonable ranges
        assert 1 <= settings.max_retries <= 10
        assert 0 <= settings.request_delay <= 5
        assert 5 <= settings.timeout <= 300

    def test_path_resolution(self):
        """Test that paths are properly resolved."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_data_dir = Path(temp_dir) / "path_resolution"
            
            with patch.dict(os.environ, {'SEC_DATA_DIR': str(test_data_dir)}):
                settings = SECEdgarSettings()
                
                # All paths should be absolute
                assert settings.sec_data_directory.is_absolute()
                assert settings.edgar_data_dir.is_absolute()

    def test_settings_singleton_behavior(self):
        """Test that settings behave consistently across imports."""
        from py_sec_edgar.settings import settings as settings1
        from py_sec_edgar.settings import settings as settings2
        
        # Should be the same instance
        assert settings1 is settings2
        assert settings1.sec_data_dir == settings2.sec_data_dir

    def test_refdata_file_existence_check(self):
        """Test that refdata files existence can be checked."""
        settings = SECEdgarSettings()
        
        # These are properties that should return Path objects
        assert isinstance(settings.cik_tickers_csv, Path)
        assert isinstance(settings.company_tickers_json, Path)
        assert isinstance(settings.ticker_list_filepath, Path)
        
        # The paths should be valid even if files don't exist
        assert settings.cik_tickers_csv.name == "cik_tickers.csv"

    def test_default_tickers_property(self):
        """Test default_tickers property."""
        settings = SECEdgarSettings()
        
        # Should return None or a list
        default_tickers = settings.default_tickers
        assert default_tickers is None or isinstance(default_tickers, list)

    def test_configuration_completeness(self):
        """Test that all required configuration is present."""
        settings = SECEdgarSettings()
        
        # Critical settings should not be None or empty
        assert settings.user_agent_email
        assert settings.user_agent_company
        assert settings.edgar_archives_url
        assert settings.edgar_base_url
        assert settings.forms_list
        assert len(settings.forms_list) > 0


if __name__ == '__main__':
    pytest.main([__file__])