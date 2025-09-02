#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Simplified tests for utilities module functionality.
Tests actual functions available in utilities.py.
"""

import os
import tempfile
from pathlib import Path
import pandas as pd

import pytest

from src.py_sec_edgar.utilities import (
    decode_html,
    clean_text_string_func,
    format_filename,
    file_size,
    walk_dir_fullpath,
    cik_column_to_list,
)


class TestUtilityFunctions:
    """Test actual utility functions."""

    def test_decode_html_success(self):
        """Test HTML decoding."""
        test_html = b"<html><body>Test content</body></html>"
        result = decode_html(test_html)
        assert isinstance(result, str)
        assert "Test content" in result

    def test_clean_text_string_func(self):
        """Test text string cleaning."""
        test_string = "Test\r\n\tString\x92with\x93special\x94chars"
        result = clean_text_string_func(test_string)
        assert "\r" not in result
        assert "\n" not in result
        assert "\t" not in result

    def test_format_filename(self):
        """Test filename formatting."""
        test_filename = "Test File Name.txt"
        result = format_filename(test_filename)
        assert " " not in result
        assert result.endswith(".txt")

    def test_format_filename_special_chars(self):
        """Test filename formatting with special characters."""
        test_filename = "Test/File\\Name:*?.txt"
        result = format_filename(test_filename)
        # Should only contain valid filename characters
        assert "/" not in result
        assert "\\" not in result
        assert ":" not in result

    def test_file_size_success(self):
        """Test file size calculation."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test content")
            temp_path = f.name
        
        try:
            result = file_size(temp_path)
            assert isinstance(result, str)
            assert "bytes" in result or "KB" in result or "MB" in result
        finally:
            os.unlink(temp_path)

    def test_file_size_nonexistent(self):
        """Test file size with non-existent file."""
        result = file_size("/nonexistent/file.txt")
        # Should return None for non-existent files
        assert result is None

    def test_walk_dir_fullpath(self):
        """Test directory walking."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            test_files = ['test1.txt', 'test2.py']
            for filename in test_files:
                filepath = os.path.join(tmpdir, filename)
                with open(filepath, 'w') as f:
                    f.write("test content")
            
            result = walk_dir_fullpath(tmpdir)
            assert isinstance(result, list)
            assert len(result) == 2

    def test_walk_dir_fullpath_empty(self):
        """Test directory walking with empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = walk_dir_fullpath(tmpdir)
            assert isinstance(result, list)
            assert len(result) == 0

    def test_cik_column_to_list_with_dataframe(self):
        """Test CIK column conversion with proper DataFrame."""
        test_df = pd.DataFrame({'CIK': [123456, 789012, 345678]})
        result = cik_column_to_list(test_df)
        
        assert isinstance(result, list)
        assert len(result) == 3
        assert 123456 in result

    def test_cik_column_to_list_with_na_values(self):
        """Test CIK column conversion with NA values."""
        test_df = pd.DataFrame({'CIK': [123456, None, 345678]})
        result = cik_column_to_list(test_df)
        
        assert isinstance(result, list)
        assert len(result) == 2  # Should filter out NA values


if __name__ == '__main__':
    pytest.main([__file__])