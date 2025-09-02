#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Comprehensive tests for process module functionality.
Targets 85% test coverage for process.py.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from urllib.parse import urljoin

import pytest

from src.py_sec_edgar.process import FilingProcessor


class TestFilingProcessor:
    """Test FilingProcessor class functionality."""

    def test_filing_processor_init(self):
        """Test FilingProcessor initialization."""
        filing_data_dir = "/test/data/CIK/FOLDER"
        edgar_url = "https://www.sec.gov/Archives/"
        
        processor = FilingProcessor(filing_data_dir, edgar_url)
        
        assert processor.filing_data_dir == filing_data_dir
        assert processor.edgar_Archives_url == edgar_url
        assert hasattr(processor, 'download')
        assert hasattr(processor, 'extract')

    def test_generate_filepaths_basic(self):
        """Test basic filepath generation."""
        filing_data_dir = "/test/data/CIK/FOLDER"
        edgar_url = "https://www.sec.gov/Archives/"
        processor = FilingProcessor(filing_data_dir, edgar_url)
        
        mock_filing = {
            'CIK': '0000320193',
            'Filename': 'edgar/data/320193/0000320193-23-000077/aapl-20230930.txt'
        }
        
        result = processor.generate_filepaths(mock_filing)
        
        assert result is not None
        assert isinstance(result, dict)
        assert 'cik_directory' in result
        assert 'filing_filepath' in result
        assert 'filing_zip_filepath' in result
        assert 'filing_folder' in result
        assert 'extracted_filing_directory' in result
        assert 'filing_url' in result

    def test_generate_filepaths_cik_replacement(self):
        """Test CIK replacement in directory paths."""
        filing_data_dir = "/test/data/CIK/FOLDER"
        edgar_url = "https://www.sec.gov/Archives/"
        processor = FilingProcessor(filing_data_dir, edgar_url)
        
        mock_filing = {
            'CIK': '0000320193',
            'Filename': 'edgar/data/320193/0000320193-23-000077/aapl-20230930.txt'
        }
        
        result = processor.generate_filepaths(mock_filing)
        
        # CIK should be replaced in the directory path
        assert '0000320193' in result['cik_directory']
        assert 'CIK' not in result['cik_directory']

    def test_generate_filepaths_folder_replacement(self):
        """Test FOLDER replacement in directory paths."""
        filing_data_dir = "/test/data/CIK/FOLDER"
        edgar_url = "https://www.sec.gov/Archives/"
        processor = FilingProcessor(filing_data_dir, edgar_url)
        
        mock_filing = {
            'CIK': '0000320193',
            'Filename': 'edgar/data/320193/0000320193-23-000077/aapl-20230930.txt'
        }
        
        result = processor.generate_filepaths(mock_filing)
        
        # FOLDER should be replaced with filing folder name
        assert 'FOLDER' not in result['extracted_filing_directory']
        assert 'aapl20230930' in result['extracted_filing_directory']

    def test_generate_filepaths_url_construction(self):
        """Test filing URL construction."""
        filing_data_dir = "/test/data/CIK/FOLDER"
        edgar_url = "https://www.sec.gov/Archives/"
        processor = FilingProcessor(filing_data_dir, edgar_url)
        
        mock_filing = {
            'CIK': '0000320193',
            'Filename': 'edgar/data/320193/0000320193-23-000077/aapl-20230930.txt'
        }
        
        result = processor.generate_filepaths(mock_filing)
        
        # URL should be properly constructed
        expected_url = urljoin(edgar_url, mock_filing['Filename'])
        assert result['filing_url'] == expected_url
        assert result['filing_url'].startswith('https://')

    def test_generate_filepaths_file_extensions(self):
        """Test file extension handling."""
        filing_data_dir = "/test/data/CIK/FOLDER"
        edgar_url = "https://www.sec.gov/Archives/"
        processor = FilingProcessor(filing_data_dir, edgar_url)
        
        mock_filing = {
            'CIK': '0000320193',
            'Filename': 'edgar/data/320193/0000320193-23-000077/aapl-20230930.txt'
        }
        
        result = processor.generate_filepaths(mock_filing)
        
        # Zip filepath should have .zip extension
        assert result['filing_zip_filepath'].endswith('.zip')
        assert '.txt' not in result['filing_zip_filepath']

    def test_generate_filepaths_filing_folder_normalization(self):
        """Test filing folder name normalization."""
        filing_data_dir = "/test/data/CIK/FOLDER"
        edgar_url = "https://www.sec.gov/Archives/"
        processor = FilingProcessor(filing_data_dir, edgar_url)
        
        mock_filing = {
            'CIK': '0000320193',
            'Filename': 'edgar/data/320193/0000320193-23-000077/aapl-20230930.txt'
        }
        
        result = processor.generate_filepaths(mock_filing)
        
        # Filing folder should normalize hyphens
        assert '-' not in result['filing_folder']
        assert result['filing_folder'] == 'aapl20230930'

    def test_generate_filepaths_preserves_original_data(self):
        """Test that original filing data is preserved."""
        filing_data_dir = "/test/data/CIK/FOLDER"
        edgar_url = "https://www.sec.gov/Archives/"
        processor = FilingProcessor(filing_data_dir, edgar_url)
        
        mock_filing = {
            'CIK': '0000320193',
            'Filename': 'edgar/data/320193/0000320193-23-000077/aapl-20230930.txt',
            'form_type': '10-K',
            'company_name': 'APPLE INC'
        }
        
        result = processor.generate_filepaths(mock_filing)
        
        # Original data should be preserved
        assert result['CIK'] == mock_filing['CIK']
        assert result['Filename'] == mock_filing['Filename']
        assert result['form_type'] == mock_filing['form_type']
        assert result['company_name'] == mock_filing['company_name']

    def test_generate_filepaths_different_ciks(self):
        """Test filepath generation with different CIKs."""
        filing_data_dir = "/test/data/CIK/FOLDER"
        edgar_url = "https://www.sec.gov/Archives/"
        processor = FilingProcessor(filing_data_dir, edgar_url)
        
        test_cases = [
            ('0000320193', 'apple'),
            ('0000789019', 'microsoft'),
            ('0001652044', 'google')
        ]
        
        for cik, company in test_cases:
            mock_filing = {
                'CIK': cik,
                'Filename': f'edgar/data/{cik.lstrip("0")}/filing.txt'
            }
            
            result = processor.generate_filepaths(mock_filing)
            
            assert cik in result['cik_directory']
            assert cik in result['extracted_filing_directory']

    @patch('src.py_sec_edgar.process.download')
    @patch('src.py_sec_edgar.process.extract')
    def test_process_filing_flow(self, mock_extract, mock_download):
        """Test the complete filing processing flow."""
        filing_data_dir = "/test/data/CIK/FOLDER"
        edgar_url = "https://www.sec.gov/Archives/"
        processor = FilingProcessor(filing_data_dir, edgar_url)
        
        # Setup mocks
        mock_download.return_value = {'downloaded': True}
        mock_extract.return_value = {'extracted': True}
        
        mock_filing = {
            'CIK': '0000320193',
            'Filename': 'edgar/data/320193/0000320193-23-000077/aapl-20230930.txt'
        }
        
        # Mock post_process to track if it's called
        with patch.object(processor, 'post_process') as mock_post_process:
            processor.process(mock_filing)
            
            # Verify the flow
            mock_download.assert_called_once()
            mock_extract.assert_called_once()
            mock_post_process.assert_called_once()

    def test_post_process_default_implementation(self):
        """Test the default post_process implementation."""
        filing_data_dir = "/test/data/CIK/FOLDER"
        edgar_url = "https://www.sec.gov/Archives/"
        processor = FilingProcessor(filing_data_dir, edgar_url)
        
        # Default implementation should do nothing (pass)
        filing_contents = {'test': 'data'}
        result = processor.post_process(filing_contents)
        
        # Should return None (default for pass)
        assert result is None

    def test_filing_processor_attributes_access(self):
        """Test that processor attributes are accessible."""
        filing_data_dir = "/test/data/CIK/FOLDER"
        edgar_url = "https://www.sec.gov/Archives/"
        processor = FilingProcessor(filing_data_dir, edgar_url)
        
        # Test attribute access
        assert processor.filing_data_dir == filing_data_dir
        assert processor.edgar_Archives_url == edgar_url
        
        # Test that download and extract are callable
        assert callable(processor.download)
        assert callable(processor.extract)

    def test_generate_filepaths_edge_cases(self):
        """Test edge cases in filepath generation."""
        filing_data_dir = "/test/data/CIK/FOLDER"
        edgar_url = "https://www.sec.gov/Archives/"
        processor = FilingProcessor(filing_data_dir, edgar_url)
        
        # Test with minimal filename
        mock_filing = {
            'CIK': '123',
            'Filename': 'file.txt'
        }
        
        result = processor.generate_filepaths(mock_filing)
        
        assert result is not None
        assert 'cik_directory' in result
        assert 'filing_url' in result

    def test_generate_filepaths_filename_variations(self):
        """Test with different filename patterns."""
        filing_data_dir = "/test/data/CIK/FOLDER"
        edgar_url = "https://www.sec.gov/Archives/"
        processor = FilingProcessor(filing_data_dir, edgar_url)
        
        test_filenames = [
            'edgar/data/320193/file-name.txt',
            'edgar/data/320193/filename.txt',
            'edgar/data/320193/file_name.txt',
            'edgar/data/320193/file123.txt'
        ]
        
        for filename in test_filenames:
            mock_filing = {
                'CIK': '0000320193',
                'Filename': filename
            }
            
            result = processor.generate_filepaths(mock_filing)
            
            # Should handle all filename patterns
            assert result is not None
            assert 'filing_folder' in result
            assert len(result['filing_folder']) > 0

    def test_generate_filepaths_memory_efficiency(self):
        """Test that filepath generation doesn't use excessive memory."""
        import sys
        
        filing_data_dir = "/test/data/CIK/FOLDER"
        edgar_url = "https://www.sec.gov/Archives/"
        processor = FilingProcessor(filing_data_dir, edgar_url)
        
        mock_filing = {
            'CIK': '0000320193',
            'Filename': 'edgar/data/320193/0000320193-23-000077/aapl-20230930.txt'
        }
        
        # Check memory usage doesn't grow excessively
        initial_size = sys.getsizeof(mock_filing)
        result = processor.generate_filepaths(mock_filing)
        result_size = sys.getsizeof(result)
        
        # Result shouldn't be excessively larger than input
        assert result_size < initial_size * 5

    def test_filing_processor_consistency(self):
        """Test that processor generates consistent results."""
        filing_data_dir = "/test/data/CIK/FOLDER"
        edgar_url = "https://www.sec.gov/Archives/"
        processor = FilingProcessor(filing_data_dir, edgar_url)
        
        mock_filing = {
            'CIK': '0000320193',
            'Filename': 'edgar/data/320193/0000320193-23-000077/aapl-20230930.txt'
        }
        
        # Generate filepaths multiple times
        result1 = processor.generate_filepaths(mock_filing.copy())
        result2 = processor.generate_filepaths(mock_filing.copy())
        
        # Results should be identical
        assert result1 == result2

    def test_filing_processor_different_configurations(self):
        """Test processor with different configuration parameters."""
        test_configs = [
            ("/data/CIK/FOLDER", "https://www.sec.gov/Archives/"),
            ("/other/CIK/FOLDER", "https://example.com/"),
            ("./local/CIK/FOLDER", "http://localhost/")
        ]
        
        for data_dir, edgar_url in test_configs:
            processor = FilingProcessor(data_dir, edgar_url)
            
            assert processor.filing_data_dir == data_dir
            assert processor.edgar_Archives_url == edgar_url
            
            # Should be able to generate filepaths
            mock_filing = {
                'CIK': '123',
                'Filename': 'test.txt'
            }
            
            result = processor.generate_filepaths(mock_filing)
            assert result is not None


if __name__ == '__main__':
    pytest.main([__file__])