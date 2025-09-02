"""Tests for SEC Edgar filing functionality."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os
from pathlib import Path

from py_sec_edgar.edgar_filing import SecEdgarFiling


@pytest.fixture
def sample_filing_data():
    """Sample filing data for testing."""
    return {
        'CIK': 104169,
        'Company Name': 'Walmart Inc.',
        'Date Filed': '2019-03-28',
        'Filename': 'edgar/data/104169/0000104169-19-000016.txt',
        'Form Type': '10-K',
        'cik_directory': 'sec_gov\\Archives\\edgar\\data\\104169\\',
        'extracted_filing_directory': 'sec_gov\\Archives\\edgar\\data\\104169\\000010416919000016',
        'filing_filepath': 'sec_gov\\Archives\\edgar\\data\\104169\\0000104169-19-000016.txt',
        'filing_folder': '000010416919000016',
        'filing_url': 'https://www.sec.gov/Archives/edgar/data/104169/0000104169-19-000016.txt',
        'filing_zip_filepath': 'sec_gov\\Archives\\edgar\\data\\104169\\0000104169-19-000016.zip',
        'published': '2019-03-28',
        'url': 'https://www.sec.gov/Archives/edgar/data/104169/0000104169-19-000016.txt'
    }


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


class TestSecEdgarFiling:
    """Test cases for SecEdgarFiling class."""

    def test_filing_initialization(self, sample_filing_data):
        """Test filing object initialization."""
        filing = SecEdgarFiling(
            sample_filing_data, 
            download=False, 
            load=False, 
            parse_header=False, 
            process_filing=False
        )
        
        assert filing.filing_data == sample_filing_data
        assert filing.cik == 104169
        assert filing.company_name == 'Walmart Inc.'
        assert filing.form_type == '10-K'
        assert not filing.is_downloaded
        assert not filing.is_loaded
        assert not filing.is_parsed_header

    def test_filing_url_construction(self, sample_filing_data):
        """Test that filing URL is constructed correctly."""
        filing = SecEdgarFiling(
            sample_filing_data, 
            download=False, 
            load=False, 
            parse_header=False, 
            process_filing=False
        )
        
        expected_url = 'https://www.sec.gov/Archives/edgar/data/104169/0000104169-19-000016.txt'
        assert filing.filing_url == expected_url

    @patch('py_sec_edgar.edgar_filing.os.makedirs')
    @patch('py_sec_edgar.edgar_filing.os.path.exists')
    def test_check_if_exists_creates_directory(self, mock_exists, mock_makedirs, sample_filing_data):
        """Test that check_if_exists creates directory when it doesn't exist."""
        mock_exists.return_value = False
        
        filing = SecEdgarFiling(
            sample_filing_data, 
            download=False, 
            load=False, 
            parse_header=False, 
            process_filing=False
        )
        
        test_directory = "/test/directory"
        filing.check_if_exists(test_directory)
        
        mock_makedirs.assert_called_once_with(test_directory)

    @patch('py_sec_edgar.edgar_filing.os.path.exists')
    def test_check_if_exists_no_create_when_exists(self, mock_exists, sample_filing_data):
        """Test that check_if_exists doesn't create directory when it exists."""
        mock_exists.return_value = True
        
        filing = SecEdgarFiling(
            sample_filing_data, 
            download=False, 
            load=False, 
            parse_header=False, 
            process_filing=False
        )
        
        test_directory = "/test/directory"
        
        with patch('py_sec_edgar.edgar_filing.os.makedirs') as mock_makedirs:
            filing.check_if_exists(test_directory)
            mock_makedirs.assert_not_called()

    @patch('py_sec_edgar.edgar_filing.requests.get')
    @patch('py_sec_edgar.edgar_filing.os.path.exists')
    @patch('builtins.open')
    def test_download_filing_success(self, mock_open, mock_exists, mock_get, sample_filing_data):
        """Test successful filing download."""
        # Setup mocks
        mock_exists.return_value = False  # File doesn't exist
        mock_response = Mock()
        mock_response.content = b"test filing content"
        mock_get.return_value = mock_response
        
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        filing = SecEdgarFiling(
            sample_filing_data, 
            download=False, 
            load=False, 
            parse_header=False, 
            process_filing=False
        )
        
        # Call download
        filing.download()
        
        # Assertions
        mock_get.assert_called_once()
        mock_file.write.assert_called_once_with(b"test filing content")
        assert filing.is_downloaded

    def test_form_type_validation(self, sample_filing_data):
        """Test that form type is properly set."""
        filing = SecEdgarFiling(
            sample_filing_data, 
            download=False, 
            load=False, 
            parse_header=False, 
            process_filing=False
        )
        
        assert filing.form_type == '10-K'

    def test_cik_validation(self, sample_filing_data):
        """Test that CIK is properly set."""
        filing = SecEdgarFiling(
            sample_filing_data, 
            download=False, 
            load=False, 
            parse_header=False, 
            process_filing=False
        )
        
        assert filing.cik == 104169
        assert isinstance(filing.cik, int)

    @pytest.mark.parametrize("form_type", ["10-K", "10-Q", "8-K", "DEF 14A"])
    def test_different_form_types(self, sample_filing_data, form_type):
        """Test filing initialization with different form types."""
        sample_filing_data['Form Type'] = form_type
        
        filing = SecEdgarFiling(
            sample_filing_data, 
            download=False, 
            load=False, 
            parse_header=False, 
            process_filing=False
        )
        
        assert filing.form_type == form_type

    def test_filing_auto_operations(self, sample_filing_data):
        """Test that auto operations work correctly."""
        with patch.object(SecEdgarFiling, 'download') as mock_download, \
             patch.object(SecEdgarFiling, 'load') as mock_load, \
             patch.object(SecEdgarFiling, 'parse_header') as mock_parse, \
             patch.object(SecEdgarFiling, 'process_filing') as mock_process:
            
            SecEdgarFiling(
                sample_filing_data, 
                download=True, 
                load=True, 
                parse_header=True, 
                process_filing=True
            )
            
            mock_download.assert_called_once()
            mock_load.assert_called_once()
            mock_parse.assert_called_once()
            mock_process.assert_called_once()
