#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tests for extract module functionality.
Targets improved test coverage for extract.py.
"""

import pytest
import os
import tempfile
import shutil
from unittest.mock import patch, mock_open, MagicMock

from src.py_sec_edgar.extract import extract, extract_complete_submission_filing


class TestExtractModule:
    """Test extract module functions."""

    def test_extract_filing_directory_exists(self):
        """Test extract when filing directory already exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            filing_json = {
                'extracted_filing_directory': temp_dir,
                'filing_filepath': 'dummy_path.txt'
            }
            
            # Directory exists, should return empty dict
            result = extract(filing_json)
            assert result == {}

    def test_extract_zip_file_exists(self):
        """Test extract when zip file already exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            non_existent_dir = os.path.join(temp_dir, 'non_existent')
            zip_file = non_existent_dir + ".zip"
            
            # Create the zip file
            with open(zip_file, 'w') as f:
                f.write('dummy zip content')
            
            filing_json = {
                'extracted_filing_directory': non_existent_dir,
                'filing_filepath': 'dummy_path.txt'
            }
            
            # Zip file exists, should return empty dict
            result = extract(filing_json)
            assert result == {}

    @patch('src.py_sec_edgar.extract.extract_complete_submission_filing')
    @patch('src.py_sec_edgar.extract.logger')
    def test_extract_success(self, mock_logger, mock_extract_complete):
        """Test successful extraction."""
        with tempfile.TemporaryDirectory() as temp_dir:
            non_existent_dir = os.path.join(temp_dir, 'non_existent')
            filing_json = {
                'extracted_filing_directory': non_existent_dir,
                'filing_filepath': 'test_file.txt'
            }
            
            expected_result = {'1': {'FILENAME': 'test.xml'}}
            mock_extract_complete.return_value = expected_result
            
            result = extract(filing_json)
            
            assert result == expected_result
            mock_extract_complete.assert_called_once_with(
                'test_file.txt', 
                output_directory=non_existent_dir
            )
            mock_logger.info.assert_called()

    @patch('src.py_sec_edgar.extract.extract_complete_submission_filing')
    @patch('src.py_sec_edgar.extract.logger')
    def test_extract_unicode_decode_error(self, mock_logger, mock_extract_complete):
        """Test extract with UnicodeDecodeError."""
        with tempfile.TemporaryDirectory() as temp_dir:
            non_existent_dir = os.path.join(temp_dir, 'non_existent')
            filing_json = {
                'extracted_filing_directory': non_existent_dir,
                'filing_filepath': 'test_file.txt'
            }
            
            unicode_error = UnicodeDecodeError('utf-8', b'', 0, 1, 'test error')
            mock_extract_complete.side_effect = unicode_error
            
            result = extract(filing_json)
            
            assert result == {}
            mock_logger.error.assert_called()

    def test_extract_complete_submission_filing_directory_exists(self):
        """Test extract_complete_submission_filing when directory exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Directory already exists
            with patch('src.py_sec_edgar.extract.logger') as mock_logger:
                result = extract_complete_submission_filing('dummy_file.txt', temp_dir)
                
                assert result is None
                mock_logger.info.assert_called_with(f"Folder Already Exists {temp_dir}")

    @patch('src.py_sec_edgar.extract.header_parser')
    @patch('src.py_sec_edgar.extract.chardet.detect')
    @patch('builtins.open')
    @patch('src.py_sec_edgar.extract.format_filename')
    @patch('src.py_sec_edgar.extract.file_size')
    @patch('os.stat')
    @patch('os.makedirs')
    def test_extract_complete_submission_filing_success(self, mock_makedirs, mock_stat, 
                                                       mock_file_size, mock_format_filename,
                                                       mock_open_builtin, mock_chardet, 
                                                       mock_header_parser):
        """Test successful complete submission filing extraction."""
        
        # Mock file content with simple document structure
        raw_content = """
        <DOCUMENT>
        <TYPE>10-K</TYPE>
        <SEQUENCE>1</SEQUENCE>
        <FILENAME>test.htm</FILENAME>
        <DESCRIPTION>Form 10-K</DESCRIPTION>
        <TEXT>
        Content of the document
        </TEXT>
        </DOCUMENT>
        """
        
        # Setup mocks
        mock_chardet.return_value = {'encoding': 'utf-8'}
        mock_header_parser.return_value = MagicMock()
        mock_header_parser.return_value.to_csv = MagicMock()
        mock_format_filename.return_value = "0001-(10-K)_Form_10-K_test.htm"
        mock_file_size.return_value = "1.5 KB"
        mock_stat.return_value = MagicMock(st_size=1024)
        
        # Mock file operations
        mock_file_handles = {}
        
        def mock_open_side_effect(filepath, *args, **kwargs):
            if 'rb' in args:
                # For binary read
                mock_handle = mock_open(read_data=raw_content.encode()).return_value
            else:
                # For text operations
                mock_handle = mock_open(read_data=raw_content).return_value
            
            mock_file_handles[filepath] = mock_handle
            return mock_handle
        
        mock_open_builtin.side_effect = mock_open_side_effect
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = os.path.join(temp_dir, 'extraction')
            
            result = extract_complete_submission_filing('test_file.txt', output_dir)
            
            # Verify the result structure
            assert isinstance(result, dict)
            assert 1 in result
            document = result[1]
            
            # Check document fields
            assert document['TYPE'] == '10-K'
            assert document['SEQUENCE'] == '1'
            assert document['FILENAME'] == 'test.htm'
            assert document['DESCRIPTION'] == 'Form 10-K'
            assert 'RELATIVE_FILEPATH' in document
            assert 'DESCRIPTIVE_FILEPATH' in document
            assert 'FILE_SIZE' in document
            assert 'FILE_SIZE_BYTES' in document
            
            # Verify makedirs was called
            mock_makedirs.assert_called_once_with(output_dir)

    @patch('src.py_sec_edgar.extract.header_parser')
    @patch('src.py_sec_edgar.extract.chardet.detect')
    @patch('builtins.open')
    @patch('src.py_sec_edgar.extract.uudecode')
    @patch('os.remove')
    @patch('os.makedirs')
    def test_extract_complete_submission_filing_uue_content(self, mock_makedirs, mock_remove,
                                                           mock_uudecode, mock_open_builtin, 
                                                           mock_chardet, mock_header_parser):
        """Test extraction with UUE encoded content."""
        
        # Mock file content with UUE content
        raw_content = """
        <DOCUMENT>
        <TYPE>EX-99.1</TYPE>
        <SEQUENCE>2</SEQUENCE>
        <FILENAME>exhibit.pdf</FILENAME>
        <DESCRIPTION>Exhibit</DESCRIPTION>
        <TEXT>
        begin 644 exhibit.pdf
        M'XL("%!!,#T"("@!(2$A(2$A(2$A(2$A(2$A(2$A(2$A(2$A(2$A(2$A
        end
        </TEXT>
        </DOCUMENT>
        """
        
        # Setup mocks
        mock_chardet.return_value = {'encoding': 'utf-8'}
        mock_header_parser.return_value = MagicMock()
        mock_header_parser.return_value.to_csv = MagicMock()
        
        # Mock file operations
        def mock_open_side_effect(filepath, *args, **kwargs):
            if 'rb' in args:
                return mock_open(read_data=raw_content.encode()).return_value
            else:
                return mock_open(read_data=raw_content).return_value
        
        mock_open_builtin.side_effect = mock_open_side_effect
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = os.path.join(temp_dir, 'extraction')
            
            with patch('src.py_sec_edgar.extract.file_size', return_value="2.1 KB"), \
                 patch('os.stat', return_value=MagicMock(st_size=2048)):
                
                result = extract_complete_submission_filing('test_file.txt', output_dir)
                
                # Verify uudecode was called
                mock_uudecode.assert_called()
                
                # Verify UUE file was removed
                mock_remove.assert_called()

    @patch('builtins.open')
    @patch('src.py_sec_edgar.extract.chardet.detect')
    def test_extract_complete_submission_filing_file_read_exception(self, mock_chardet, mock_open_builtin):
        """Test file reading with exception fallback to binary mode."""
        
        # Mock chardet to raise exception on first call
        mock_chardet.return_value = {'encoding': 'utf-8'}
        
        raw_content = b"""<DOCUMENT>
<TYPE>EX-99.1
<SEQUENCE>2
<FILENAME>exhibit.htm
<DESCRIPTION>Test Document
<TEXT>
<html><body><p>Test content</p></body></html>
</TEXT>
</DOCUMENT>"""
        
        def mock_open_side_effect(filepath, *args, **kwargs):
            if filepath == 'test_file.txt' and 'encoding' in kwargs:
                # Only raise exception for the initial file read with encoding
                raise UnicodeDecodeError('utf-8', b'', 0, 1, 'test error')
            elif filepath == 'test_file.txt' and 'rb' in args:
                # Binary read - should work
                return mock_open(read_data=raw_content).return_value
            else:
                # For all other file operations (writing output, etc.)
                return mock_open().return_value
        
        mock_open_builtin.side_effect = mock_open_side_effect
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = os.path.join(temp_dir, 'extraction')
            
            with patch('src.py_sec_edgar.extract.header_parser') as mock_header_parser, \
                 patch('os.makedirs'):
                
                mock_header_parser.return_value = MagicMock()
                mock_header_parser.return_value.to_csv = MagicMock()
                
                # Should not raise exception, should fallback to binary read
                result = extract_complete_submission_filing('test_file.txt', output_dir)
                
                # Should complete without error
                assert isinstance(result, dict)


if __name__ == '__main__':
    pytest.main([__file__])