"""
Lightweight SQLite database manager for SEC EDGAR application
Handles task persistence, caching, and data management
"""

import json
import logging
import os
import sqlite3
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Lightweight SQLite database manager with connection pooling"""

    def __init__(self, db_path: str = "sec_edgar.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._local = threading.local()
        self._initialize_database()

    def _get_connection(self) -> sqlite3.Connection:
        """Get thread-local database connection"""
        if not hasattr(self._local, 'connection'):
            self._local.connection = sqlite3.connect(
                str(self.db_path),
                check_same_thread=False,
                timeout=30.0
            )
            self._local.connection.row_factory = sqlite3.Row
            # Enable WAL mode for better concurrency
            self._local.connection.execute("PRAGMA journal_mode=WAL")
            self._local.connection.execute("PRAGMA synchronous=NORMAL")
            self._local.connection.execute("PRAGMA cache_size=10000")
            self._local.connection.execute("PRAGMA temp_store=MEMORY")

        return self._local.connection

    def _initialize_database(self):
        """Initialize database schema"""
        conn = self._get_connection()

        # Tasks table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                priority TEXT NOT NULL DEFAULT 'normal',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                progress REAL DEFAULT 0.0,
                result TEXT,
                error TEXT,
                parameters TEXT DEFAULT '{}',
                duration REAL,
                estimated_completion TIMESTAMP
            )
        ''')

        # Cache table for API responses
        conn.execute('''
            CREATE TABLE IF NOT EXISTS cache (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Filings data table - core filing information from SEC EDGAR
        conn.execute('''
            CREATE TABLE IF NOT EXISTS filings (
                id TEXT PRIMARY KEY,
                ticker TEXT,
                cik TEXT,
                company_name TEXT,
                form_type TEXT NOT NULL,
                period_reported TEXT,
                filing_name TEXT,
                filed_date DATE,
                filing_url TEXT,
                sec_link TEXT,
                description TEXT,
                source TEXT DEFAULT 'SEC EDGAR',
                status TEXT DEFAULT 'active',
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(cik, form_type, filed_date)
            )
        ''')

        # Task logs table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS task_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                level TEXT NOT NULL DEFAULT 'INFO',
                message TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (task_id) REFERENCES tasks (id) ON DELETE CASCADE
            )
        ''')
        
        # Handle database migrations for existing installations
        self._migrate_database(conn)

        # Create indexes for better performance
        conn.execute('CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_tasks_created ON tasks(created_at)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_cache_expires ON cache(expires_at)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_filings_ticker ON filings(ticker)')
        # Only create cik index if column exists
        try:
            conn.execute('CREATE INDEX IF NOT EXISTS idx_filings_cik ON filings(cik)')
        except sqlite3.OperationalError:
            pass  # Column doesn't exist yet
        conn.execute('CREATE INDEX IF NOT EXISTS idx_filings_form_type ON filings(form_type)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_filings_filed_date ON filings(filed_date)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_task_logs_task_id ON task_logs(task_id)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_task_logs_timestamp ON task_logs(timestamp)')

        conn.commit()
        logger.info(f"Database initialized at {self.db_path}")

    def _migrate_database(self, conn: sqlite3.Connection):
        """Handle database schema migrations"""
        try:
            # Check if filings table exists and get its columns
            cursor = conn.execute("PRAGMA table_info(filings)")
            columns = [row[1] for row in cursor.fetchall()]
            
            if 'filings' in [row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]:
                # Add missing columns to existing filings table
                if 'cik' not in columns:
                    logger.info("Adding cik column to filings table")
                    conn.execute('ALTER TABLE filings ADD COLUMN cik TEXT')
                
                if 'sec_link' not in columns:
                    logger.info("Adding sec_link column to filings table")
                    conn.execute('ALTER TABLE filings ADD COLUMN sec_link TEXT')
                
                if 'description' not in columns:
                    logger.info("Adding description column to filings table")
                    conn.execute('ALTER TABLE filings ADD COLUMN description TEXT')
                
                if 'source' not in columns:
                    logger.info("Adding source column to filings table")
                    conn.execute('ALTER TABLE filings ADD COLUMN source TEXT DEFAULT "SEC EDGAR"')
                
                # Update UNIQUE constraint if needed (this requires recreating the table)
                # Check current constraints
                cursor = conn.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='filings'")
                table_sql = cursor.fetchone()
                if table_sql and 'UNIQUE(ticker, form_type, filed_date)' in table_sql[0]:
                    logger.info("Updating filings table unique constraint to use CIK instead of ticker")
                    self._recreate_filings_table_with_cik_constraint(conn)
            
            # Remove earnings table if it exists (cleanup legacy)
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='earnings'")
            if cursor.fetchone():
                logger.info("Removing legacy earnings table")
                conn.execute('DROP TABLE earnings')
                
        except Exception as e:
            logger.warning(f"Database migration warning: {e}")

    def _recreate_filings_table_with_cik_constraint(self, conn: sqlite3.Connection):
        """Recreate filings table with CIK-based unique constraint"""
        try:
            # Create new table with correct schema
            conn.execute('''
                CREATE TABLE filings_new (
                    id TEXT PRIMARY KEY,
                    ticker TEXT,
                    cik TEXT,
                    company_name TEXT,
                    form_type TEXT NOT NULL,
                    period_reported TEXT,
                    filing_name TEXT,
                    filed_date DATE,
                    filing_url TEXT,
                    sec_link TEXT,
                    description TEXT,
                    source TEXT DEFAULT 'SEC EDGAR',
                    status TEXT DEFAULT 'active',
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(cik, form_type, filed_date)
                )
            ''')
            
            # Copy data from old table
            conn.execute('''
                INSERT INTO filings_new (
                    id, ticker, cik, company_name, form_type, period_reported,
                    filing_name, filed_date, filing_url, sec_link, description, source, status, added_at
                )
                SELECT 
                    id, ticker, cik, company_name, form_type, period_reported,
                    filing_name, filed_date, filing_url, sec_link, description, source, status, added_at
                FROM filings
            ''')
            
            # Drop old table and rename new one
            conn.execute('DROP TABLE filings')
            conn.execute('ALTER TABLE filings_new RENAME TO filings')
            
            logger.info("Successfully migrated filings table schema")
        except Exception as e:
            logger.error(f"Failed to migrate filings table: {e}")
            # Roll back by dropping the new table if it exists
            try:
                conn.execute('DROP TABLE IF EXISTS filings_new')
            except:
                pass

    def close(self):
        """Close database connections"""
        if hasattr(self._local, 'connection'):
            self._local.connection.close()

    # =====================
    # TASK MANAGEMENT
    # =====================

    def create_task(self, task_id: str, name: str, parameters: dict[str, Any] | None = None,
                   priority: str = 'normal') -> bool:
        """Create a new task"""
        try:
            conn = self._get_connection()
            conn.execute('''
                INSERT INTO tasks (id, name, parameters, priority)
                VALUES (?, ?, ?, ?)
            ''', (task_id, name, json.dumps(parameters or {}), priority))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            logger.warning(f"Task {task_id} already exists")
            return False
        except Exception as e:
            logger.error(f"Error creating task {task_id}: {e}")
            return False

    def update_task(self, task_id: str, **kwargs) -> bool:
        """Update task fields"""
        try:
            conn = self._get_connection()

            # Convert parameters dict to JSON if provided
            if 'parameters' in kwargs and isinstance(kwargs['parameters'], dict):
                kwargs['parameters'] = json.dumps(kwargs['parameters'])

            # Build dynamic update query
            fields = []
            values = []
            for key, value in kwargs.items():
                if key in ['status', 'priority', 'started_at', 'completed_at',
                          'progress', 'result', 'error', 'parameters', 'duration']:
                    fields.append(f"{key} = ?")
                    values.append(value)

            if not fields:
                return False

            values.append(task_id)
            query = f"UPDATE tasks SET {', '.join(fields)} WHERE id = ?"

            cursor = conn.execute(query, values)
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error updating task {task_id}: {e}")
            return False

    def get_task(self, task_id: str) -> dict[str, Any] | None:
        """Get task by ID"""
        try:
            conn = self._get_connection()
            cursor = conn.execute('SELECT * FROM tasks WHERE id = ?', (task_id,))
            row = cursor.fetchone()

            if row:
                task = dict(row)
                # Parse JSON parameters
                try:
                    task['parameters'] = json.loads(task['parameters'] or '{}')
                except json.JSONDecodeError:
                    task['parameters'] = {}

                # Parse JSON result
                try:
                    if task.get('result'):
                        task['result'] = json.loads(task['result'])
                    else:
                        task['result'] = None
                except json.JSONDecodeError:
                    task['result'] = None

                return task
            return None
        except Exception as e:
            logger.error(f"Error getting task {task_id}: {e}")
            return None

    def list_tasks(self, status: list[str] | None = None,
                  priority: list[str] | None = None,
                  limit: int = 50, offset: int = 0) -> dict[str, Any]:
        """List tasks with filtering"""
        try:
            conn = self._get_connection()

            # Build WHERE clause
            where_conditions = []
            params = []

            if status:
                placeholders = ','.join(['?' for _ in status])
                where_conditions.append(f"status IN ({placeholders})")
                params.extend(status)

            if priority:
                placeholders = ','.join(['?' for _ in priority])
                where_conditions.append(f"priority IN ({placeholders})")
                params.extend(priority)

            where_clause = ' AND '.join(where_conditions)
            if where_clause:
                where_clause = f"WHERE {where_clause}"

            # Get total count
            count_query = f"SELECT COUNT(*) as total FROM tasks {where_clause}"
            cursor = conn.execute(count_query, params)
            total_count = cursor.fetchone()['total']

            # Get tasks
            query = f'''
                SELECT * FROM tasks {where_clause}
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            '''
            cursor = conn.execute(query, params + [limit, offset])

            tasks = []
            for row in cursor.fetchall():
                task = dict(row)
                try:
                    task['parameters'] = json.loads(task['parameters'] or '{}')
                except json.JSONDecodeError:
                    task['parameters'] = {}

                # Parse JSON result
                try:
                    if task.get('result'):
                        task['result'] = json.loads(task['result'])
                    else:
                        task['result'] = None
                except json.JSONDecodeError:
                    task['result'] = None

                tasks.append(task)

            return {
                'tasks': tasks,
                'total_count': total_count
            }
        except Exception as e:
            logger.error(f"Error listing tasks: {e}")
            return {'tasks': [], 'total_count': 0}

    def delete_task(self, task_id: str) -> bool:
        """Delete a task"""
        try:
            conn = self._get_connection()
            cursor = conn.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error deleting task {task_id}: {e}")
            return False

    def clear_completed_tasks(self, older_than_hours: int = 24) -> int:
        """Clear completed tasks older than specified hours"""
        try:
            conn = self._get_connection()
            cutoff_time = datetime.utcnow() - timedelta(hours=older_than_hours)

            cursor = conn.execute('''
                DELETE FROM tasks 
                WHERE status IN ('completed', 'failed', 'cancelled')
                AND completed_at < ?
            ''', (cutoff_time,))
            conn.commit()
            return cursor.rowcount
        except Exception as e:
            logger.error(f"Error clearing completed tasks: {e}")
            return 0

    def get_task_stats(self) -> dict[str, Any]:
        """Get task statistics"""
        try:
            conn = self._get_connection()

            # Status counts
            cursor = conn.execute('''
                SELECT status, COUNT(*) as count
                FROM tasks
                GROUP BY status
            ''')
            by_status = {row['status']: row['count'] for row in cursor.fetchall()}

            # Priority counts
            cursor = conn.execute('''
                SELECT priority, COUNT(*) as count
                FROM tasks
                GROUP BY priority
            ''')
            by_priority = {row['priority']: row['count'] for row in cursor.fetchall()}

            # Other stats
            cursor = conn.execute('''
                SELECT 
                    COUNT(*) as total_tasks,
                    AVG(duration) as avg_duration,
                    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_count,
                    COUNT(CASE WHEN status IN ('pending', 'running') THEN 1 END) as active_tasks
                FROM tasks
            ''')
            stats = dict(cursor.fetchone())

            success_rate = 0.0
            if stats['total_tasks'] > 0:
                success_rate = stats['completed_count'] / stats['total_tasks']

            return {
                'total_tasks': stats['total_tasks'],
                'by_status': by_status,
                'by_priority': by_priority,
                'avg_duration': stats['avg_duration'],
                'success_rate': success_rate,
                'active_tasks': stats['active_tasks'],
                'queue_length': by_status.get('pending', 0)
            }
        except Exception as e:
            logger.error(f"Error getting task stats: {e}")
            return {}

    # =====================
    # CACHE MANAGEMENT
    # =====================

    def cache_set(self, key: str, value: Any, ttl_seconds: int = 3600):
        """Set cache value with TTL"""
        try:
            conn = self._get_connection()
            expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds)

            conn.execute('''
                INSERT OR REPLACE INTO cache (key, value, expires_at)
                VALUES (?, ?, ?)
            ''', (key, json.dumps(value), expires_at))
            conn.commit()
        except Exception as e:
            logger.error(f"Error setting cache key {key}: {e}")

    def cache_get(self, key: str) -> Any | None:
        """Get cache value if not expired"""
        try:
            conn = self._get_connection()
            cursor = conn.execute('''
                SELECT value FROM cache
                WHERE key = ? AND expires_at > CURRENT_TIMESTAMP
            ''', (key,))

            row = cursor.fetchone()
            if row:
                return json.loads(row['value'])
            return None
        except Exception as e:
            logger.error(f"Error getting cache key {key}: {e}")
            return None

    def cache_delete(self, key: str) -> bool:
        """Delete cache key"""
        try:
            conn = self._get_connection()
            cursor = conn.execute('DELETE FROM cache WHERE key = ?', (key,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error deleting cache key {key}: {e}")
            return False

    def cache_clear_expired(self) -> int:
        """Clear expired cache entries"""
        try:
            conn = self._get_connection()
            cursor = conn.execute('DELETE FROM cache WHERE expires_at <= CURRENT_TIMESTAMP')
            conn.commit()
            return cursor.rowcount
        except Exception as e:
            logger.error(f"Error clearing expired cache: {e}")
            return 0

    # =====================
    # DATA STORAGE
    # =====================

    def store_filings(self, filings_data: list[dict[str, Any]]) -> int:
        """Store filings data in database with deduplication."""
        if not filings_data:
            return 0

        try:
            conn = self._get_connection()
            stored_count = 0

            for filing in filings_data:
                try:
                    conn.execute('''
                        INSERT OR IGNORE INTO filings (
                            id, ticker, cik, company_name, form_type, period_reported,
                            filing_name, filed_date, filing_url, sec_link, description, source, status
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        filing.get('id', ''),
                        filing.get('ticker', ''),
                        filing.get('cik', ''),
                        filing.get('company_name', ''),
                        filing.get('form_type', ''),
                        filing.get('period_reported', ''),
                        filing.get('filing_name', ''),
                        filing.get('filed_date', ''),
                        filing.get('filing_url', ''),
                        filing.get('sec_link', filing.get('filing_url', '')),
                        filing.get('description', ''),
                        filing.get('source', 'SEC EDGAR'),
                        filing.get('status', 'active')
                    ))
                    if conn.total_changes > 0:
                        stored_count += 1
                except sqlite3.IntegrityError:
                    continue  # Skip duplicates

            conn.commit()
            logger.info(f"Stored {stored_count} new filing records to database")
            return stored_count
        except Exception as e:
            logger.error(f"Error storing filings data: {e}")
            return 0

    def get_filings(self, limit: int = 100, ticker: str | None = None, 
                   form_type: str | None = None, cik: str | None = None) -> list[dict[str, Any]]:
        """Get filings data with optional filtering."""
        try:
            conn = self._get_connection()
            
            # Build WHERE clause dynamically
            where_conditions = []
            params = []
            
            if ticker:
                where_conditions.append("ticker = ?")
                params.append(ticker)
            
            if form_type:
                where_conditions.append("form_type = ?")
                params.append(form_type)
                
            if cik:
                where_conditions.append("cik = ?")
                params.append(cik)
            
            where_clause = ""
            if where_conditions:
                where_clause = "WHERE " + " AND ".join(where_conditions)
            
            query = f'''
                SELECT * FROM filings {where_clause}
                ORDER BY filed_date DESC, added_at DESC 
                LIMIT ?
            '''
            params.append(limit)
            
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting filings data: {e}")
            return []

    def count_filings(self, ticker: str | None = None, form_type: str | None = None) -> int:
        """Count total filings with optional filtering."""
        try:
            conn = self._get_connection()
            
            where_conditions = []
            params = []
            
            if ticker:
                where_conditions.append("ticker = ?")
                params.append(ticker)
            
            if form_type:
                where_conditions.append("form_type = ?")
                params.append(form_type)
            
            where_clause = ""
            if where_conditions:
                where_clause = "WHERE " + " AND ".join(where_conditions)
            
            query = f"SELECT COUNT(*) as count FROM filings {where_clause}"
            cursor = conn.execute(query, params)
            return cursor.fetchone()['count']
        except Exception as e:
            logger.error(f"Error counting filings: {e}")
            return 0

    def add_task_log(self, task_id: str, level: str, message: str, timestamp: datetime | None = None) -> bool:
        """Add a log entry for a task"""
        try:
            conn = self._get_connection()
            log_timestamp = timestamp or datetime.utcnow()

            conn.execute('''
                INSERT INTO task_logs (task_id, timestamp, level, message)
                VALUES (?, ?, ?, ?)
            ''', (task_id, log_timestamp, level, message))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error adding task log for {task_id}: {e}")
            return False

    def get_task_logs(self, task_id: str, limit: int = 100) -> list[dict[str, Any]]:
        """Get logs for a specific task"""
        try:
            conn = self._get_connection()
            cursor = conn.execute('''
                SELECT timestamp, level, message
                FROM task_logs
                WHERE task_id = ?
                ORDER BY timestamp ASC
                LIMIT ?
            ''', (task_id, limit))

            logs = []
            for row in cursor.fetchall():
                logs.append({
                    'timestamp': row['timestamp'],
                    'level': row['level'],
                    'message': row['message']
                })
            return logs
        except Exception as e:
            logger.error(f"Error getting task logs for {task_id}: {e}")
            return []

    def clear_task_logs(self, task_id: str) -> bool:
        """Clear all logs for a specific task"""
        try:
            conn = self._get_connection()
            cursor = conn.execute('DELETE FROM task_logs WHERE task_id = ?', (task_id,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error clearing task logs for {task_id}: {e}")
            return False


# Global database instance
_db_instance = None
_db_lock = threading.Lock()


def get_database() -> DatabaseManager:
    """Get singleton database instance"""
    global _db_instance

    if _db_instance is None:
        with _db_lock:
            if _db_instance is None:
                # Default to data directory in project root
                db_path = os.getenv('SEC_EDGAR_DB_PATH', 'data/sec_edgar.db')
                _db_instance = DatabaseManager(db_path)

    return _db_instance


def cleanup_database():
    """Cleanup database connections"""
    global _db_instance
    if _db_instance:
        _db_instance.close()
        _db_instance = None
