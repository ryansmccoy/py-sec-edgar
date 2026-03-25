"""
Unified Path Management Utilities for SEC EDGAR

This module consolidates all file path and directory management patterns
that were scattered across 15+ files throughout the py-sec-edgar package.

Previously duplicated patterns:
- os.makedirs(os.path.dirname(filepath), exist_ok=True) - 6+ files
- path.parent.mkdir(parents=True, exist_ok=True) - 8+ files
- os.path.join() patterns - 15+ files
- File existence checking patterns - 10+ files
- Temporary file creation patterns - 5+ files

All path operations now follow modern pathlib patterns with proper error handling.
"""

import logging
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)


class EdgarPathManager:
    """
    Unified path and directory management for SEC EDGAR operations.

    Provides consistent, safe file and directory operations across all
    feed processing, download, and parsing operations.
    """

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def ensure_directory(self, path: str | Path) -> Path:
        """
        Ensure directory exists, creating it if necessary.

        Consolidates:
        - os.makedirs(os.path.dirname(filepath), exist_ok=True)
        - path.parent.mkdir(parents=True, exist_ok=True)
        - os.makedirs(directory, exist_ok=True)

        Args:
            path: Directory path or file path (directory will be created)

        Returns:
            Path object for the directory

        Raises:
            OSError: If directory creation fails
        """
        try:
            directory = Path(path)

            # If path has an extension, get the parent directory
            if directory.suffix:
                directory = directory.parent

            directory.mkdir(parents=True, exist_ok=True)
            self.logger.debug(f"Ensured directory exists: {directory}")
            return directory

        except OSError as e:
            self.logger.error(f"Failed to create directory {path}: {e}")
            raise OSError(f"Could not create directory {path}: {e}")

    def ensure_file_directory(self, filepath: str | Path) -> Path:
        """
        Ensure the parent directory of a file exists.

        Consolidates: os.makedirs(os.path.dirname(filepath), exist_ok=True)

        Args:
            filepath: Path to the file whose directory should be created

        Returns:
            Path object for the file
        """
        file_path = Path(filepath)
        self.ensure_directory(file_path.parent)
        return file_path

    def safe_join(self, base: str | Path, *parts: str) -> Path:
        """
        Safely join path components using pathlib.

        Consolidates: os.path.join() patterns throughout the codebase

        Args:
            base: Base directory path
            *parts: Path components to join

        Returns:
            Path object for the joined path
        """
        path = Path(base)
        for part in parts:
            path = path / part
        return path

    def create_temp_file(
        self,
        suffix: str = "",
        prefix: str = "edgar_",
        directory: str | Path | None = None,
    ) -> Path:
        """
        Create a temporary file with proper cleanup handling.

        Consolidates: Temporary file creation patterns across feed processing

        Args:
            suffix: File suffix (e.g., ".txt", ".xml")
            prefix: File prefix for identification
            directory: Optional directory for temporary file

        Returns:
            Path object for the temporary file
        """
        if directory:
            self.ensure_directory(directory)
            temp_dir = str(directory)
        else:
            temp_dir = None

        # Create temporary file and immediately close the handle
        # (we only want the path)
        with tempfile.NamedTemporaryFile(
            suffix=suffix, prefix=prefix, dir=temp_dir, delete=False
        ) as temp_file:
            temp_path = Path(temp_file.name)

        self.logger.debug(f"Created temporary file: {temp_path}")
        return temp_path

    def safe_remove(self, filepath: str | Path) -> bool:
        """
        Safely remove a file with error handling.

        Args:
            filepath: Path to file to remove

        Returns:
            True if file was removed or didn't exist, False on error
        """
        try:
            file_path = Path(filepath)
            if file_path.exists():
                file_path.unlink()
                self.logger.debug(f"Removed file: {file_path}")
            return True
        except OSError as e:
            self.logger.warning(f"Failed to remove file {filepath}: {e}")
            return False

    def file_exists(self, filepath: str | Path) -> bool:
        """
        Check if file exists with proper error handling.

        Consolidates: File existence checking patterns

        Args:
            filepath: Path to check

        Returns:
            True if file exists and is readable
        """
        try:
            return Path(filepath).exists()
        except (OSError, PermissionError):
            return False

    def get_file_size(self, filepath: str | Path) -> int | None:
        """
        Get file size safely.

        Args:
            filepath: Path to file

        Returns:
            File size in bytes, or None if error
        """
        try:
            return Path(filepath).stat().st_size
        except (OSError, FileNotFoundError):
            return None

    def list_files(self, directory: str | Path, pattern: str = "*") -> list[Path]:
        """
        List files in directory with pattern matching.

        Args:
            directory: Directory to search
            pattern: Glob pattern (e.g., "*.txt", "master.*")

        Returns:
            List of Path objects matching the pattern
        """
        try:
            dir_path = Path(directory)
            if not dir_path.exists():
                return []
            return list(dir_path.glob(pattern))
        except OSError:
            return []


# Global path manager instance
path_manager = EdgarPathManager()


# Convenience functions for common operations
def ensure_directory(path: str | Path) -> Path:
    """Ensure directory exists."""
    return path_manager.ensure_directory(path)


def ensure_file_directory(filepath: str | Path) -> Path:
    """Ensure parent directory of file exists."""
    return path_manager.ensure_file_directory(filepath)


def safe_join(base: str | Path, *parts: str) -> Path:
    """Safely join path components."""
    return path_manager.safe_join(base, *parts)


def create_temp_file(
    suffix: str = "", prefix: str = "edgar_", directory: str | Path | None = None
) -> Path:
    """Create temporary file."""
    return path_manager.create_temp_file(suffix, prefix, directory)


def safe_remove(filepath: str | Path) -> bool:
    """Safely remove file."""
    return path_manager.safe_remove(filepath)


def file_exists(filepath: str | Path) -> bool:
    """Check if file exists."""
    return path_manager.file_exists(filepath)
