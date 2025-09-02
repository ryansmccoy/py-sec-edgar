#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Comprehensive tests for database module functionality.
Targets 85% test coverage for database/manager.py.
"""

import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from py_sec_edgar.database.manager import DatabaseManager, get_database


class TestDatabaseManager:
    """Test DatabaseManager class functionality."""

    def test_init_with_custom_path(self):
        """Test DatabaseManager initialization with custom database path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            db_manager = DatabaseManager(db_path)
            assert db_manager.db_path == db_path
            assert db_manager.db_path.exists()

    def test_init_default_path(self):
        """Test DatabaseManager initialization with default path."""
        with patch('py_sec_edgar.database.manager.settings') as mock_settings:
            mock_settings.database_path = Path(tempfile.gettempdir()) / "test_default.db"
            db_manager = DatabaseManager()
            assert db_manager.db_path == mock_settings.database_path

    def test_init_database_creates_tables(self):
        """Test that _init_database creates required tables."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test_init.db"
            db_manager = DatabaseManager(db_path)
            
            # Check that filings table exists
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='filings'")
            result = cursor.fetchone()
            conn.close()
            
            assert result is not None
            assert result[0] == 'filings'

    def test_store_filings_basic(self):
        """Test storing filings to database."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test_store.db"
            db_manager = DatabaseManager(db_path)
            
            test_filings = [
                {
                    'id': 'test_1',
                    'ticker': 'AAPL',
                    'cik': '0000320193',
                    'company_name': 'Apple Inc.',
                    'form_type': '10-K',
                    'period_reported': '2024-09-30',
                    'filing_name': 'Annual Report',
                    'filed_date': '2024-10-31',
                    'filing_url': 'https://example.com/filing1',
                    'sec_link': 'https://example.com/filing1',
                    'description': 'Annual Report',
                    'source': 'RSS Feed',
                    'status': 'active'
                }
            ]
            
            new_filings = db_manager.store_filings(test_filings)
            assert new_filings == 1
            
            # Verify filing was stored
            filings = db_manager.get_filings(limit=10)
            assert len(filings) == 1
            assert filings[0]['ticker'] == 'AAPL'

    def test_store_filings_with_cik_lookup(self):
        """Test storing filings with CIK lookup functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test_cik.db"
            db_manager = DatabaseManager(db_path)
            
            test_filings = [
                {
                    'id': 'test_2',
                    'company_name': 'Microsoft Corporation',
                    'form_type': '8-K',
                    'filed_date': '2024-11-01',
                    'filing_url': 'https://example.com/filing2'
                }
            ]
            
            with patch.object(db_manager, '_lookup_cik_for_company', return_value='0000789019'):
                new_filings = db_manager.store_filings(test_filings)
                assert new_filings == 1
                
                # Verify CIK was populated
                filings = db_manager.get_filings(limit=10)
                assert len(filings) == 1
                assert filings[0]['cik'] == '0000789019'

    def test_store_filings_duplicate_handling(self):
        """Test that duplicate filings are handled correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test_duplicates.db"
            db_manager = DatabaseManager(db_path)
            
            test_filing = {
                'id': 'test_duplicate',
                'ticker': 'AAPL',
                'company_name': 'Apple Inc.',
                'form_type': '10-K',
                'filed_date': '2024-10-31',
                'filing_url': 'https://example.com/filing_duplicate'
            }
            
            # Store filing first time
            new_filings_1 = db_manager.store_filings([test_filing])
            assert new_filings_1 == 1
            
            # Store same filing again
            new_filings_2 = db_manager.store_filings([test_filing])
            assert new_filings_2 == 0  # Should be 0 new filings
            
            # Verify only one filing exists
            filings = db_manager.get_filings()
            assert len(filings) == 1

    def test_get_filings_with_filters(self):
        """Test get_filings with various filters."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test_filters.db"
            db_manager = DatabaseManager(db_path)
            
            # Store test data
            test_filings = [
                {
                    'id': 'test_aapl_10k',
                    'ticker': 'AAPL',
                    'form_type': '10-K',
                    'company_name': 'Apple Inc.',
                    'filed_date': '2024-10-31',
                    'filing_url': 'https://example.com/aapl'
                },
                {
                    'id': 'test_msft_8k',
                    'ticker': 'MSFT',
                    'form_type': '8-K',
                    'company_name': 'Microsoft Corporation',
                    'filed_date': '2024-11-01',
                    'filing_url': 'https://example.com/msft'
                }
            ]
            db_manager.store_filings(test_filings)
            
            # Test ticker filter
            aapl_filings = db_manager.get_filings(ticker='AAPL')
            assert len(aapl_filings) == 1
            assert aapl_filings[0]['ticker'] == 'AAPL'
            
            # Test form_type filter
            tenk_filings = db_manager.get_filings(form_type='10-K')
            assert len(tenk_filings) == 1
            assert tenk_filings[0]['form_type'] == '10-K'
            
            # Test limit
            limited_filings = db_manager.get_filings(limit=1)
            assert len(limited_filings) == 1

    def test_get_filings_count(self):
        """Test get_filings_count method."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test_count.db"
            db_manager = DatabaseManager(db_path)
            
            # Initially should be 0
            count = db_manager.get_filings_count()
            assert count == 0
            
            # Store some filings
            test_filings = [
                {
                    'id': f'test_{i}',
                    'ticker': 'TEST',
                    'form_type': '10-K',
                    'company_name': 'Test Company',
                    'filed_date': '2024-10-31',
                    'filing_url': f'https://example.com/filing{i}'
                }
                for i in range(3)
            ]
            db_manager.store_filings(test_filings)
            
            # Should now be 3
            count = db_manager.get_filings_count()
            assert count == 3
            
            # Test with filters
            count_with_ticker = db_manager.get_filings_count(ticker='TEST')
            assert count_with_ticker == 3
            
            count_with_wrong_ticker = db_manager.get_filings_count(ticker='NONEXISTENT')
            assert count_with_wrong_ticker == 0

    def test_delete_filing(self):
        """Test delete_filing method."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test_delete.db"
            db_manager = DatabaseManager(db_path)
            
            # Store a filing
            test_filing = {
                'id': 'test_delete_me',
                'ticker': 'DELETE',
                'company_name': 'Delete Company',
                'form_type': '8-K',
                'filed_date': '2024-10-31',
                'filing_url': 'https://example.com/delete'
            }
            db_manager.store_filings([test_filing])
            
            # Verify it exists
            assert db_manager.get_filings_count() == 1
            
            # Delete it
            success = db_manager.delete_filing('test_delete_me')
            assert success is True
            
            # Verify it's gone
            assert db_manager.get_filings_count() == 0
            
            # Try to delete non-existent filing
            success = db_manager.delete_filing('nonexistent')
            assert success is False

    def test_clear_all_filings(self):
        """Test clear_all_filings method."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test_clear.db"
            db_manager = DatabaseManager(db_path)
            
            # Store some filings
            test_filings = [
                {
                    'id': f'clear_test_{i}',
                    'ticker': 'CLEAR',
                    'form_type': '10-K',
                    'company_name': 'Clear Company',
                    'filed_date': '2024-10-31',
                    'filing_url': f'https://example.com/clear{i}'
                }
                for i in range(5)
            ]
            db_manager.store_filings(test_filings)
            
            # Verify they exist
            assert db_manager.get_filings_count() == 5
            
            # Clear all
            cleared_count = db_manager.clear_all_filings()
            assert cleared_count == 5
            
            # Verify they're gone
            assert db_manager.get_filings_count() == 0

    def test_get_database_stats(self):
        """Test get_database_stats method."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test_stats.db"
            db_manager = DatabaseManager(db_path)
            
            # Get stats for empty database
            stats = db_manager.get_database_stats()
            assert stats['total_filings'] == 0
            assert stats['unique_tickers'] == 0
            assert stats['unique_form_types'] == 0
            
            # Store some diverse filings
            test_filings = [
                {
                    'id': 'stats_1',
                    'ticker': 'AAPL',
                    'form_type': '10-K',
                    'company_name': 'Apple Inc.',
                    'filed_date': '2024-10-31',
                    'filing_url': 'https://example.com/stats1'
                },
                {
                    'id': 'stats_2',
                    'ticker': 'AAPL',
                    'form_type': '8-K',
                    'company_name': 'Apple Inc.',
                    'filed_date': '2024-11-01',
                    'filing_url': 'https://example.com/stats2'
                },
                {
                    'id': 'stats_3',
                    'ticker': 'MSFT',
                    'form_type': '10-K',
                    'company_name': 'Microsoft Corporation',
                    'filed_date': '2024-10-31',
                    'filing_url': 'https://example.com/stats3'
                }
            ]
            db_manager.store_filings(test_filings)
            
            # Get updated stats
            stats = db_manager.get_database_stats()
            assert stats['total_filings'] == 3
            assert stats['unique_tickers'] == 2  # AAPL, MSFT
            assert stats['unique_form_types'] == 2  # 10-K, 8-K

    def test_context_manager(self):
        """Test DatabaseManager as context manager."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test_context.db"
            
            with DatabaseManager(db_path) as db_manager:
                assert isinstance(db_manager, DatabaseManager)
                assert db_manager.db_path == db_path
                
                # Test that we can use it normally
                test_filing = {
                    'id': 'context_test',
                    'ticker': 'CTX',
                    'company_name': 'Context Company',
                    'form_type': '10-K',
                    'filed_date': '2024-10-31',
                    'filing_url': 'https://example.com/context'
                }
                db_manager.store_filings([test_filing])
                
                count = db_manager.get_filings_count()
                assert count == 1

    def test_get_database_singleton(self):
        """Test get_database singleton function."""
        # Test that get_database returns the same instance
        db1 = get_database()
        db2 = get_database()
        assert db1 is db2
        assert isinstance(db1, DatabaseManager)

    def test_migration_handling(self):
        """Test database migration handling."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test_migration.db"
            
            # Create old database without expected schema
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE old_table (id TEXT)")
            conn.commit()
            conn.close()
            
            # Initialize DatabaseManager - should handle migration
            db_manager = DatabaseManager(db_path)
            
            # Check that filings table now exists
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='filings'")
            result = cursor.fetchone()
            conn.close()
            
            assert result is not None

    def test_error_handling(self):
        """Test error handling in database operations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test_errors.db"
            db_manager = DatabaseManager(db_path)
            
            # Test with invalid filing data
            invalid_filing = {}  # Missing required fields
            
            # Should handle gracefully
            new_filings = db_manager.store_filings([invalid_filing])
            assert new_filings == 0


if __name__ == '__main__':
    pytest.main([__file__])