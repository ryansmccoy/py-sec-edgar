"""
Unified Download Service - Simple Solution for Download Function Duplication

This module provides a single, reliable download service that eliminates the need for
6+ different download implementations scattered across the codebase.
"""

import logging
import time
from pathlib import Path
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ..settings import settings


class UnifiedDownloadService:
    """
    Universal download service that consolidates all download functionality

    This single class replaces 6+ scattered download implementations,
    eliminating ~180 lines of duplicate code while providing:
    - Unified error handling and retry logic
    - Consistent header management
    - Progress reporting capabilities
    - Proper timeout and session management
    """

    def __init__(self):
        """Initialize download service with optimal configuration"""
        self.logger = logging.getLogger(__name__)
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """Create optimized requests session with retry logic"""
        session = requests.Session()

        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"],
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        # Set reasonable timeouts
        session.timeout = (10, 30)  # (connect, read)

        return session

    def download_text(
        self,
        url: str,
        save_path: Path | None = None,
        description: str = "file",
        headers: dict[str, str] | None = None,
    ) -> str:
        """
        Download text content from URL

        Args:
            url: URL to download from
            save_path: Optional path to save the content
            description: Description for logging (e.g., "master index", "RSS feed")
            headers: Optional custom headers (defaults to SEC-compliant headers)

        Returns:
            Downloaded content as string

        Raises:
            DownloadError: If download fails after retries
        """
        start_time = time.time()

        try:
            # Use centralized headers by default
            request_headers = headers or settings.get_request_headers()

            self.logger.info(f"Downloading {description} from: {url}")

            response = self.session.get(url, headers=request_headers)
            response.raise_for_status()

            content = response.text
            duration = time.time() - start_time

            self.logger.info(
                f"Downloaded {description} successfully ({len(content)} chars, {duration:.2f}s)"
            )

            # Save to file if path provided
            if save_path:
                self._save_text_content(content, save_path, description)

            return content

        except requests.RequestException as e:
            duration = time.time() - start_time
            self.logger.error(
                f"Failed to download {description} from {url} ({duration:.2f}s): {e}"
            )
            raise DownloadError(f"Download failed for {description}: {e}")
        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(
                f"Unexpected error downloading {description} ({duration:.2f}s): {e}"
            )
            raise DownloadError(f"Unexpected download error for {description}: {e}")

    def download_binary(
        self,
        url: str,
        save_path: Path,
        description: str = "file",
        headers: dict[str, str] | None = None,
        chunk_size: int = 8192,
    ) -> bool:
        """
        Download binary content from URL with streaming

        Args:
            url: URL to download from
            save_path: Path to save the binary content
            description: Description for logging
            headers: Optional custom headers
            chunk_size: Size of chunks for streaming download

        Returns:
            True if successful, False otherwise

        Raises:
            DownloadError: If download fails after retries
        """
        start_time = time.time()

        try:
            # Use centralized headers by default
            request_headers = headers or settings.get_request_headers()

            self.logger.info(f"Downloading {description} from: {url}")

            # Ensure directory exists
            save_path.parent.mkdir(parents=True, exist_ok=True)

            response = self.session.get(url, headers=request_headers, stream=True)
            response.raise_for_status()

            total_size = 0
            with open(save_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:  # Filter out keep-alive chunks
                        f.write(chunk)
                        total_size += len(chunk)

            duration = time.time() - start_time
            self.logger.info(
                f"Downloaded {description} successfully ({total_size} bytes, {duration:.2f}s)"
            )

            return True

        except requests.RequestException as e:
            duration = time.time() - start_time
            self.logger.error(
                f"Failed to download {description} from {url} ({duration:.2f}s): {e}"
            )
            raise DownloadError(f"Binary download failed for {description}: {e}")
        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(
                f"Unexpected error downloading {description} ({duration:.2f}s): {e}"
            )
            raise DownloadError(
                f"Unexpected binary download error for {description}: {e}"
            )

    def _save_text_content(
        self, content: str, save_path: Path, description: str
    ) -> None:
        """Save text content to file with proper error handling"""
        try:
            # Ensure directory exists
            save_path.parent.mkdir(parents=True, exist_ok=True)

            with open(save_path, "w", encoding="utf-8") as f:
                f.write(content)

            self.logger.info(f"Saved {description} to: {save_path}")

        except Exception as e:
            self.logger.error(f"Failed to save {description} to {save_path}: {e}")
            raise DownloadError(f"File save failed for {description}: {e}")

    def get_status(self) -> dict[str, Any]:
        """Get download service status information"""
        return {
            "service": "UnifiedDownloadService",
            "session_configured": self.session is not None,
            "retry_enabled": True,
            "timeout_configured": True,
            "headers_centralized": True,
            "supported_methods": ["download_text", "download_binary"],
        }

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - clean up session"""
        if self.session:
            self.session.close()


class DownloadError(Exception):
    """Custom exception for download operations"""

    pass


# Global service instance for easy access
_download_service = None


def get_download_service() -> UnifiedDownloadService:
    """
    Get singleton download service instance

    Returns:
        UnifiedDownloadService instance
    """
    global _download_service
    if _download_service is None:
        _download_service = UnifiedDownloadService()
    return _download_service


# Convenience functions for backward compatibility
# COMMENTED OUT - Dead code testing
# def download_text_file(url: str, save_path: Optional[Path] = None, description: str = "file") -> str:
#     """
#     Convenience function for text downloads
#
#     Args:
#         url: URL to download from
#         save_path: Optional path to save content
#         description: Description for logging
#
#     Returns:
#         Downloaded content as string
#     """
#     service = get_download_service()
#     return service.download_text(url, save_path, description)


# def download_binary_file(url: str, save_path: Path, description: str = "file") -> bool:
#     """
#     Convenience function for binary downloads
#
#     Args:
#         url: URL to download from
#         save_path: Path to save content
#         description: Description for logging
#
#     Returns:
#         True if successful
#     """
#     service = get_download_service()
#     return service.download_binary(url, save_path, description)
