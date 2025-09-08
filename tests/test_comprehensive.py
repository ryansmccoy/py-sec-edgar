"""
Comprehensive test coverage for py-sec-edgar

This simplified test suite focuses on testing actual public interfaces
and functionality rather than internal implementation details.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch

# Basic unit tests for core models
from py_sec_edgar.core.models import FilingInfo, CompanyInfo, SearchResult

# Basic integration tests for public interfaces
from py_sec_edgar.search_engine import FilingSearchEngine, FilingSearchError


class TestCoreModels:
    """Test core data models."""

    def test_filing_info_creation(self):
        """Test creating FilingInfo with required fields."""
        filing = FilingInfo(
            cik="320193",
            form_type="10-K",
            filing_date="2024-10-31",
            accession_number="0000320193-24-000123",
        )
        assert filing.cik == "320193"  # Leading zeros stripped
        assert filing.form_type == "10-K"
        assert filing.filing_date == "2024-10-31"
        assert filing.accession_number == "0000320193-24-000123"

    def test_filing_info_from_search_result(self):
        """Test creating FilingInfo from search result data."""
        filing = FilingInfo.from_search_result(
            ticker="AAPL",
            company_name="Apple Inc.",
            cik="320193",
            form_type="10-K",
            filing_date="2024-10-31",
            document_url="https://www.sec.gov/Archives/edgar/data/320193/000032019324000123/aapl-20240930.htm",
            filename="aapl-20240930.htm",
        )
        assert filing.ticker == "AAPL"
        assert filing.company_name == "Apple Inc."
        assert filing.cik == "320193"
        assert filing.accession_number == "0000320193-24-000123"  # Extracted from URL

    def test_company_info_creation(self):
        """Test creating CompanyInfo with CIK formatting."""
        company = CompanyInfo(
            cik="0000320193", ticker="aapl", company_name="Apple Inc."
        )
        assert company.cik == "320193"  # Leading zeros stripped
        assert company.ticker == "AAPL"  # Converted to uppercase
        assert company.company_name == "Apple Inc."

    def test_search_result_creation(self):
        """Test creating SearchResult container."""
        filings = [
            FilingInfo(
                cik="320193",
                form_type="10-K",
                filing_date="2024-10-31",
                accession_number="acc1",
            ),
            FilingInfo(
                cik="320193",
                form_type="10-Q",
                filing_date="2024-07-31",
                accession_number="acc2",
            ),
        ]

        result = SearchResult(query="AAPL", total_results=2, filings=filings)

        assert result.query == "AAPL"
        assert result.total_results == 2
        assert len(result.filings) == 2


class TestSearchEngineBasics:
    """Test search engine initialization and error handling."""

    def test_search_engine_init(self):
        """Test search engine initialization."""
        # This will fail if required data files don't exist, which is expected
        try:
            engine = FilingSearchEngine()
            # If we get here, the data files exist
            assert hasattr(engine, "ticker_map_path")
            assert hasattr(engine, "filing_index_path")
        except FilingSearchError as e:
            # Expected when data files are missing
            assert "Missing required data files" in str(e)
            assert "uv run py-sec-edgar feeds update-full-index" in str(e)

    def test_filing_search_error(self):
        """Test custom exception creation."""
        error = FilingSearchError("Test error message")
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)


class TestUtilityFunctions:
    """Test utility functions that don't require external data."""

    def test_filename_formatting(self):
        """Test filename formatting utility."""
        from py_sec_edgar.utilities import format_filename

        # Test basic filename
        result = format_filename("test_file.txt")
        assert result == "test_file.txt"

        # Test with spaces
        result = format_filename("test file.txt")
        assert result == "test_file.txt"

        # Test with invalid characters
        result = format_filename("test<>file?.txt")
        assert "?" not in result
        assert "<" not in result
        assert ">" not in result

    def test_text_cleaning(self):
        """Test text cleaning utility."""
        from py_sec_edgar.utilities import clean_text_string_func

        dirty_text = "test\r\n\ttext"
        cleaned = clean_text_string_func(dirty_text)

        assert "\r" not in cleaned
        assert "\n" not in cleaned
        assert "\t" not in cleaned
        assert "test" in cleaned
        assert "text" in cleaned

    def test_byte_conversion(self):
        """Test byte size conversion utility."""
        from py_sec_edgar.utilities import convert_bytes

        # Test various sizes
        result_kb = convert_bytes(1024)
        assert "KB" in result_kb

        result_mb = convert_bytes(1024 * 1024)
        assert "MB" in result_mb

        result_bytes = convert_bytes(500)
        assert "bytes" in result_bytes


class TestDownloaderBasics:
    """Test downloader initialization and basic functionality."""

    def test_downloader_init(self):
        """Test downloader initialization."""
        from py_sec_edgar.core.downloader import FilingDownloader

        downloader = FilingDownloader()
        assert hasattr(downloader, "max_retries")
        assert hasattr(downloader, "rate_limit_delay")
        assert downloader.max_retries >= 1
        assert downloader.rate_limit_delay > 0

    def test_local_path_generation(self):
        """Test local file path generation."""
        from py_sec_edgar.core.downloader import FilingDownloader

        downloader = FilingDownloader()
        filing = FilingInfo(
            cik="320193",
            form_type="10-K",
            filing_date="2024-10-31",
            accession_number="0000320193-24-000123",
            ticker="AAPL",
            filename="aapl-20240930.htm",
        )

        local_path = downloader._get_local_path(filing)
        assert local_path.name.endswith(".htm")
        assert "AAPL" in str(local_path)
        assert "2024" in str(local_path)  # Year should be in path


class TestSettingsAndConfiguration:
    """Test settings and configuration management."""

    def test_settings_import(self):
        """Test that settings can be imported and have expected attributes."""
        from py_sec_edgar.settings import settings

        # Check core configuration exists
        assert hasattr(settings, "base_dir")
        assert hasattr(settings, "edgar_archives_url")
        assert hasattr(settings, "user_agent")
        assert hasattr(settings, "max_retries")
        assert hasattr(settings, "timeout")

        # Check URL configuration
        assert "sec.gov" in settings.edgar_archives_url
        assert settings.timeout > 0
        assert settings.max_retries >= 1

    def test_forms_list_configuration(self):
        """Test default forms list configuration."""
        from py_sec_edgar.settings import settings

        assert hasattr(settings, "forms_list")
        assert isinstance(settings.forms_list, list)
        assert len(settings.forms_list) > 0

        # Check for common form types
        common_forms = ["10-K", "10-Q", "8-K"]
        for form in common_forms:
            if form in settings.forms_list:
                assert True  # At least one common form should be present
                break
        else:
            pytest.fail("No common forms found in settings.forms_list")


class TestCLIBasics:
    """Test CLI module imports and basic structure."""

    def test_cli_imports(self):
        """Test that CLI modules can be imported."""
        from py_sec_edgar.cli.commands import search
        from py_sec_edgar.main import main

        # Check basic CLI structure exists
        assert hasattr(search, "filings")
        assert hasattr(search, "search_group")
        assert callable(main)

    def test_cli_help_availability(self):
        """Test that CLI help is available."""
        from click.testing import CliRunner
        from py_sec_edgar.cli.commands.search import search_group

        runner = CliRunner()
        result = runner.invoke(search_group, ["--help"])

        # Should not crash and should contain help text
        assert result.exit_code == 0
        assert "search" in result.output.lower()


@pytest.mark.integration
class TestMinimalIntegration:
    """Minimal integration tests that work without external data."""

    def test_filing_info_round_trip(self):
        """Test FilingInfo creation and serialization."""
        # Create filing info
        original = FilingInfo(
            cik="320193",
            form_type="10-K",
            filing_date="2024-10-31",
            accession_number="0000320193-24-000123",
            ticker="AAPL",
            company_name="Apple Inc.",
        )

        # Convert to dict and back
        data_dict = original.to_dict()

        # Verify essential fields preserved
        assert data_dict["cik"] == "320193"
        assert data_dict["form_type"] == "10-K"
        assert data_dict["ticker"] == "AAPL"
        assert data_dict["accession_number"] == "0000320193-24-000123"

    def test_search_result_aggregation(self):
        """Test search result aggregation functionality."""
        # Create multiple filings
        filings = []
        for i, form_type in enumerate(["10-K", "10-Q", "8-K"]):
            filing = FilingInfo(
                cik="320193",
                form_type=form_type,
                filing_date=f"2024-{i + 1:02d}-01",
                accession_number=f"0000320193-24-00012{i}",
            )
            filings.append(filing)

        # Create search result
        result = SearchResult(query="AAPL", total_results=len(filings), filings=filings)

        # Test basic properties
        assert result.query == "AAPL"
        assert len(result.filings) == 3
        assert result.total_results == 3

        # Test that filings contain expected form types
        form_types = {f.form_type for f in result.filings}
        assert form_types == {"10-K", "10-Q", "8-K"}

    def test_error_handling_patterns(self):
        """Test error handling patterns across modules."""
        # Test FilingSearchError
        with pytest.raises(FilingSearchError):
            raise FilingSearchError("Test error")

        # Test model validation
        with pytest.raises(TypeError):
            # Missing required fields should raise TypeError
            FilingInfo()  # No required arguments provided


if __name__ == "__main__":
    pytest.main([__file__])
