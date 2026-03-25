"""
Logging utilities for SEC EDGAR applications.

This module provides standardized logging configuration and utilities
following Python best practices for error handling and logging.
"""

import logging
import shutil
import sys
from datetime import datetime, timedelta
from pathlib import Path


def get_project_root() -> Path:
    """Get the project root directory."""
    current_file = Path(__file__).resolve()
    # Go up to find the project root (where pyproject.toml or setup.py exists)
    for parent in current_file.parents:
        if (parent / "pyproject.toml").exists() or (parent / "setup.py").exists():
            return parent
    # Fallback to 3 levels up from this file
    return current_file.parents[2]


def archive_old_log_files(
    current_log_file: str, max_keep: int = 5, archive_older_than_days: int = 1
) -> None:
    """
    Archive old log files to keep directory clean.

    Args:
        current_log_file: Path to the current log file
        max_keep: Maximum number of archived files to keep
        archive_older_than_days: Archive files older than this many days
    """
    try:
        log_path = Path(current_log_file)
        log_dir = log_path.parent
        log_name = log_path.stem
        # log_ext = log_path.suffix  # Commented: unused variable

        # Create archive directory
        archive_dir = log_dir / "archive"
        archive_dir.mkdir(exist_ok=True)

        # Find old log files with timestamp patterns
        patterns = [f"{log_name}_*.log", f"{log_name}*.log", f"*{log_name}*.log"]

        cutoff_time = datetime.now() - timedelta(days=archive_older_than_days)
        archived_count = 0

        for pattern in patterns:
            for old_log in log_dir.glob(pattern):
                if old_log.name == log_path.name:
                    continue  # Don't archive the current log file

                try:
                    # Check if file is old enough to archive
                    file_time = datetime.fromtimestamp(old_log.stat().st_mtime)
                    if file_time < cutoff_time:
                        archive_path = archive_dir / old_log.name
                        shutil.move(str(old_log), str(archive_path))
                        archived_count += 1
                        print(f"📁 Archived old log: {old_log.name} → archive/")
                except OSError as e:
                    print(f"⚠️ Could not archive {old_log.name}: {e}")

        # Clean up old archived files (keep only max_keep newest)
        cleanup_old_archives(archive_dir, max_keep)

        if archived_count > 0:
            print(f"✅ Archived {archived_count} old log files to archive/ directory")

    except Exception as e:
        print(f"⚠️ Error during log archiving: {e}")


def archive_project_log_files(
    max_keep: int = 10, archive_older_than_days: int = 1
) -> None:
    """
    Archive old log files from common project locations.

    Args:
        max_keep: Maximum archived files to keep per location
        archive_older_than_days: Archive files older than this many days
    """
    try:
        project_root = get_project_root()

        # Common log file locations and patterns
        log_locations = [
            (project_root, ["*.log"]),  # Root directory log files
            (project_root / "logs", ["*.log"]),  # Logs directory
        ]

        total_archived = 0

        for log_dir, patterns in log_locations:
            if not log_dir.exists():
                continue

            # Create archive directory
            archive_dir = log_dir / "archive"
            archive_dir.mkdir(exist_ok=True)

            cutoff_time = datetime.now() - timedelta(days=archive_older_than_days)
            location_archived = 0

            for pattern in patterns:
                for log_file in log_dir.glob(pattern):
                    if log_file.is_file() and not log_file.name.startswith("."):
                        try:
                            # Check if file is old enough to archive
                            file_time = datetime.fromtimestamp(log_file.stat().st_mtime)
                            if file_time < cutoff_time:
                                # Skip if it's the current day's file (keep most recent)
                                if is_current_session_log(log_file):
                                    continue

                                archive_path = archive_dir / log_file.name
                                shutil.move(str(log_file), str(archive_path))
                                location_archived += 1

                        except OSError as e:
                            print(f"⚠️ Could not archive {log_file.name}: {e}")

            if location_archived > 0:
                print(f"📁 Archived {location_archived} log files from {log_dir.name}/")

            # Clean up old archived files
            cleanup_old_archives(archive_dir, max_keep)
            total_archived += location_archived

        if total_archived > 0:
            print(
                f"✅ Total archived: {total_archived} log files moved to archive directories"
            )

    except Exception as e:
        print(f"⚠️ Error during project log archiving: {e}")


def is_current_session_log(log_file: Path) -> bool:
    """
    Check if a log file is from the current session (today).

    Args:
        log_file: Path to the log file

    Returns:
        bool: True if it's a current session log file
    """
    try:
        # Check if filename contains today's date
        today = datetime.now().strftime("%Y%m%d")
        if today in log_file.name:
            return True

        # Check file modification time (if modified today, likely current)
        file_time = datetime.fromtimestamp(log_file.stat().st_mtime)
        if file_time.date() == datetime.now().date():
            return True

        return False

    except Exception:
        return False


def cleanup_old_archives(archive_dir: Path, max_keep: int) -> None:
    """
    Clean up old archived files, keeping only the newest ones.

    Args:
        archive_dir: Directory containing archived files
        max_keep: Maximum number of files to keep
    """
    try:
        if not archive_dir.exists():
            return

        # Get all archived log files sorted by modification time (newest first)
        archived_files = [f for f in archive_dir.glob("*.log") if f.is_file()]
        archived_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

        # Remove excess files
        removed_count = 0
        for old_file in archived_files[max_keep:]:
            try:
                old_file.unlink()
                removed_count += 1
            except OSError as e:
                print(f"⚠️ Could not remove old archive {old_file.name}: {e}")

        if removed_count > 0:
            print(f"🗑️ Cleaned up {removed_count} old archived log files")

    except Exception as e:
        print(f"⚠️ Error during archive cleanup: {e}")


def setup_logging(
    log_level: int = logging.INFO, log_file: str | None = None
) -> logging.Logger:
    """
    Set up logging configuration with best practices and automatic log rotation.

    Args:
        log_level: Logging level (default: INFO)
        log_file: Optional log file path

    Returns:
        logging.Logger: Configured logger instance

    Example:
        >>> logger = setup_logging(logging.DEBUG, 'my_app.log')
        >>> logger.info("Application started")
    """
    # Archive old log files before setting up new logging
    if log_file:
        archive_old_log_files(log_file)

    # Archive old log files in common locations
    archive_project_log_files()

    # Create formatters
    console_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        try:
            # Ensure log directory exists
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
            file_handler.setLevel(logging.DEBUG)  # More detailed for file
            file_handler.setFormatter(file_formatter)
            root_logger.addHandler(file_handler)

        except OSError as e:
            logging.warning(f"Could not create log file {log_file}: {e}")

    return logging.getLogger(__name__)


def configure_module_logger(
    module_name: str, log_level: int = logging.INFO
) -> logging.Logger:
    """
    Configure a logger for a specific module.

    Args:
        module_name: Name of the module (usually __name__)
        log_level: Logging level for this module

    Returns:
        logging.Logger: Configured module logger
    """
    logger = logging.getLogger(module_name)
    logger.setLevel(log_level)
    return logger


def log_exception(
    logger: logging.Logger,
    message: str,
    exception: Exception,
    log_level: int = logging.ERROR,
) -> None:
    """
    Log an exception with consistent formatting.

    Args:
        logger: Logger instance to use
        message: Custom message to include
        exception: Exception to log
        log_level: Logging level to use
    """
    logger.log(
        log_level, f"{message}: {type(exception).__name__}: {exception}", exc_info=True
    )


def cleanup_logging() -> None:
    """
    Clean up logging handlers and shutdown logging system.
    Also archives old log files during cleanup.

    Should be called at program exit to ensure proper cleanup.
    """
    try:
        # Archive old log files before shutdown
        archive_project_log_files()
        logging.shutdown()
    except Exception:
        # Suppress any errors during cleanup
        pass


def manual_log_cleanup(
    archive_older_than_days: int = 1, max_archived_files: int = 10
) -> None:
    """
    Manually trigger log file cleanup and archiving.

    Args:
        archive_older_than_days: Archive files older than this many days
        max_archived_files: Maximum number of archived files to keep
    """
    print("🧹 Starting manual log cleanup...")
    archive_project_log_files(
        max_keep=max_archived_files, archive_older_than_days=archive_older_than_days
    )
    print("✅ Manual log cleanup completed!")


def get_log_status() -> dict:
    """
    Get current status of log files in the project.

    Returns:
        dict: Summary of log file status
    """
    try:
        project_root = get_project_root()
        status = {"project_root": str(project_root), "locations": {}}

        # Check common log locations
        locations = [("root", project_root), ("logs", project_root / "logs")]

        for name, location in locations:
            if location.exists():
                log_files = list(location.glob("*.log"))
                archive_dir = location / "archive"
                archived_files = (
                    list(archive_dir.glob("*.log")) if archive_dir.exists() else []
                )

                status["locations"][name] = {
                    "path": str(location),
                    "active_logs": len(log_files),
                    "active_files": [f.name for f in log_files],
                    "archived_logs": len(archived_files),
                    "archive_path": str(archive_dir) if archive_dir.exists() else None,
                }

        return status

    except Exception as e:
        return {"error": str(e)}


class LoggingContext:
    """
    Context manager for logging setup and cleanup.

    Example:
        >>> with LoggingContext(logging.INFO, 'app.log') as logger:
        ...     logger.info("Processing started")
        ...     # Your code here
    """

    def __init__(self, log_level: int = logging.INFO, log_file: str | None = None):
        """
        Initialize logging context.

        Args:
            log_level: Logging level
            log_file: Optional log file path
        """
        self.log_level = log_level
        self.log_file = log_file
        self.logger = None

    def __enter__(self) -> logging.Logger:
        """Set up logging and return logger."""
        self.logger = setup_logging(self.log_level, self.log_file)
        return self.logger

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up logging."""
        cleanup_logging()

        # Log any exceptions that occurred
        if exc_type and self.logger:
            self.logger.exception(f"Exception in logging context: {exc_val}")


# Pre-configured logging levels for common use cases
DEBUG_LEVEL = logging.DEBUG
INFO_LEVEL = logging.INFO
WARNING_LEVEL = logging.WARNING
ERROR_LEVEL = logging.ERROR
CRITICAL_LEVEL = logging.CRITICAL

# Common log file names
DEFAULT_LOG_FILE = "sec_edgar.log"
ERROR_LOG_FILE = "sec_edgar_errors.log"
DEBUG_LOG_FILE = "sec_edgar_debug.log"


# ======================================================================
# Centralized Workflow Logging Functions (DRY Solution)
# ======================================================================


def setup_workflow_logging(
    log_filename: str = "sec_edgar_workflow.log",
    log_level: str = "INFO",
    force_reconfigure: bool = False,
) -> logging.Logger:
    """Set up logging for workflow modules with consistent configuration.

    This is a DRY solution that all workflow files should use instead of
    setting up their own logging configuration.

    Args:
        log_filename: Name of the log file (will be created in project_root/logs/)
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        force_reconfigure: Whether to reconfigure logging even if already set up

    Returns:
        Logger instance for the calling module
    """
    # Get the project root directory using existing utility
    project_root = get_project_root()
    logs_dir = project_root / "logs"

    # Create logs directory if it doesn't exist
    logs_dir.mkdir(exist_ok=True)

    # Set up logging configuration using existing setup_logging function
    log_file = logs_dir / log_filename

    # Convert string log level to numeric
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Use the existing setup_logging function but with workflow-specific settings
    setup_logging(log_level=numeric_level, log_file=str(log_file))

    # Return a logger for the calling module
    import inspect

    frame = inspect.currentframe()
    try:
        caller_frame = frame.f_back
        caller_module = caller_frame.f_globals.get("__name__", "py_sec_edgar")
        return logging.getLogger(caller_module)
    finally:
        del frame


def get_workflow_logger(name: str = None) -> logging.Logger:
    """Get a logger instance for workflow modules.

    Args:
        name: Logger name (defaults to calling module's __name__)

    Returns:
        Logger instance
    """
    if name is None:
        import inspect

        frame = inspect.currentframe()
        try:
            caller_frame = frame.f_back
            name = caller_frame.f_globals.get("__name__", "py_sec_edgar")
        finally:
            del frame

    return logging.getLogger(name)
