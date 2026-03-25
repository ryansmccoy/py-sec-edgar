"""
Unified filing download manager for py-sec-edgar

This module consolidates all download functionality that was previously
scattered across search_engine.py, client.py, cli commands, and utilities.
"""

import asyncio
import logging
import time
from collections.abc import Callable
from pathlib import Path

import aiofiles
import aiohttp
from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)

from ..core.models import FilingInfo
from ..settings import settings

logger = logging.getLogger(__name__)

__all__ = ["FilingDownloader", "download_filing", "download_filings"]


class DownloadError(Exception):
    """Custom exception for download operations"""

    pass


class FilingDownloader:
    """
    Unified filing download manager

    Consolidates all download functionality with features:
    - Async/await support for concurrent operations
    - Progress tracking with rich console integration
    - SEC rate limiting compliance (10 req/sec max)
    - Automatic retry with exponential backoff
    - Local file management and caching
    - Batch download optimization
    """

    def __init__(
        self,
        max_concurrent: int = 5,
        rate_limit_delay: float = 0.1,  # 10 req/sec compliance
        max_retries: int = 3,
        console: Console | None = None,
    ):
        self.max_concurrent = max_concurrent
        self.rate_limit_delay = rate_limit_delay
        self.max_retries = max_retries
        self.console = console or Console()

        # Rate limiting
        self._last_request_time = 0.0
        self._request_semaphore = asyncio.Semaphore(max_concurrent)

    async def fetch_content(
        self, url: str, headers: dict | None = None, timeout: int = 30
    ) -> str:
        """
        Fetch content from any URL (general purpose method)

        Args:
            url: URL to fetch content from
            headers: Optional additional headers
            timeout: Request timeout in seconds

        Returns:
            Content as string

        Raises:
            DownloadError: If fetch fails after retries
        """
        default_headers = settings.get_request_headers()

        # Merge headers
        if headers:
            default_headers.update(headers)

        async with self._request_semaphore:
            await self._rate_limit()

            for attempt in range(self.max_retries + 1):
                try:
                    client_timeout = aiohttp.ClientTimeout(total=timeout, connect=10)

                    async with aiohttp.ClientSession(
                        timeout=client_timeout, headers=default_headers
                    ) as session:
                        async with session.get(url) as response:
                            if response.status == 200:
                                content = await response.text()
                                logger.debug(
                                    f"Fetched {len(content)} characters from {url}"
                                )
                                return content
                            else:
                                raise DownloadError(
                                    f"HTTP {response.status}: {response.reason}"
                                )

                except asyncio.TimeoutError:
                    if attempt < self.max_retries:
                        wait_time = (2**attempt) * self.rate_limit_delay
                        logger.warning(
                            f"Timeout fetching {url}, retrying in {wait_time:.1f}s"
                        )
                        await asyncio.sleep(wait_time)
                        continue
                    raise DownloadError(f"Timeout fetching content from {url}")

                except Exception as e:
                    if attempt < self.max_retries:
                        wait_time = (2**attempt) * self.rate_limit_delay
                        logger.warning(
                            f"Error fetching {url}: {e}, retrying in {wait_time:.1f}s"
                        )
                        await asyncio.sleep(wait_time)
                        continue
                    raise DownloadError(f"Failed to fetch content from {url}: {e}")

            raise DownloadError(f"Max retries exceeded for {url}")

    async def download_filing(
        self, filing: FilingInfo, save_to_disk: bool = False, show_progress: bool = True
    ) -> str:
        """
        Download a single filing with progress tracking

        Args:
            filing: Filing information including document URL
            save_to_disk: Whether to save content to local storage
            show_progress: Whether to show download progress

        Returns:
            Filing content as string

        Raises:
            DownloadError: If download fails after retries
        """
        # Use submission_url for downloading actual filing text, fallback to document_url
        download_url = filing.submission_url or filing.document_url
        if not download_url:
            raise DownloadError(f"No download URL provided for filing {filing.ticker}")

        # Check if file exists locally first
        if save_to_disk:
            local_path = self._get_local_path(filing)
            if local_path.exists():
                try:
                    async with aiofiles.open(local_path, encoding="utf-8") as f:
                        content = await f.read()
                    if show_progress:
                        self.console.print(
                            f"[green]✅ Found local: {local_path.name} ({len(content):,} chars)[/green]"
                        )
                    return content
                except Exception as e:
                    logger.warning(f"Failed to read local file {local_path}: {e}")

        # Download from SEC
        async with self._request_semaphore:
            await self._rate_limit()

            for attempt in range(self.max_retries + 1):
                try:
                    content = await self._download_with_progress(filing, show_progress)

                    # Save to disk if requested
                    if save_to_disk:
                        await self._save_content(filing, content)

                    return content

                except Exception as e:
                    if attempt == self.max_retries:
                        raise DownloadError(
                            f"Failed to download {filing.ticker} after {self.max_retries + 1} attempts: {e}"
                        )

                    delay = (2**attempt) + (
                        time.time() % 1
                    )  # Exponential backoff with jitter
                    if show_progress:
                        self.console.print(
                            f"[yellow]⚠️ Attempt {attempt + 1} failed, retrying in {delay:.1f}s...[/yellow]"
                        )
                    await asyncio.sleep(delay)

    async def download_filings(
        self,
        filings: list[FilingInfo],
        save_to_disk: bool = True,
        progress_callback: Callable[[int, int, FilingInfo], None] | None = None,
    ) -> list[str]:
        """
        Download multiple filings with batch optimization

        Args:
            filings: List of filing information
            save_to_disk: Whether to save content to local storage
            progress_callback: Optional callback for progress updates

        Returns:
            List of filing contents as strings
        """
        if not filings:
            return []

        results = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=self.console,
        ) as progress:
            task = progress.add_task(
                f"Downloading {len(filings)} filings...", total=len(filings)
            )

            # Process in batches to respect rate limits
            batch_size = min(self.max_concurrent, len(filings))

            for i in range(0, len(filings), batch_size):
                batch = filings[i : i + batch_size]

                # Download batch concurrently
                tasks = [
                    self.download_filing(
                        filing, save_to_disk=save_to_disk, show_progress=False
                    )
                    for filing in batch
                ]

                batch_results = await asyncio.gather(*tasks, return_exceptions=True)

                # Process results and update progress
                for j, (filing, result) in enumerate(
                    zip(batch, batch_results, strict=False)
                ):
                    if isinstance(result, Exception):
                        logger.error(f"Failed to download {filing.ticker}: {result}")
                        results.append("")  # Empty content for failed downloads
                    else:
                        results.append(result)

                    if progress_callback:
                        progress_callback(i + j + 1, len(filings), filing)

                    progress.update(task, advance=1)

        return results

    async def _download_with_progress(
        self, filing: FilingInfo, show_progress: bool
    ) -> str:
        """Download filing content with optional progress display"""
        # Use submission_url for downloading actual filing text, fallback to document_url
        download_url = filing.submission_url or filing.document_url

        headers = settings.get_request_headers()

        timeout = aiohttp.ClientTimeout(total=60, connect=10)

        async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
            async with session.get(download_url) as response:
                if response.status == 200:
                    content = await response.text()

                    if show_progress:
                        size_mb = len(content) / (1024 * 1024)
                        self.console.print(
                            f"[green]✅ Downloaded: {filing.ticker} {filing.form_type} ({size_mb:.1f}MB)[/green]"
                        )

                    return content
                else:
                    raise DownloadError(f"HTTP {response.status}: {response.reason}")

    async def _rate_limit(self):
        """Ensure SEC rate limiting compliance (10 req/sec max)"""
        current_time = time.time()
        elapsed = current_time - self._last_request_time

        if elapsed < self.rate_limit_delay:
            await asyncio.sleep(self.rate_limit_delay - elapsed)

        self._last_request_time = time.time()

    def _get_local_path(self, filing: FilingInfo) -> Path:
        """Get local storage path for filing"""
        # Extract year from filing date
        try:
            year = filing.filing_date.split("-")[0] if filing.filing_date else "unknown"
        except (AttributeError, IndexError):
            year = "unknown"

        # Create organized directory structure
        base_dir = settings.sec_data_directory / "downloads" / "filings"
        filing_dir = base_dir / filing.ticker.upper() / year

        # Use filename from URL or create one
        if filing.filename:
            filename = Path(filing.filename).name
        else:
            # Create filename from accession number
            acc_num = filing.accession_number.replace("-", "")
            filename = f"{acc_num}.txt"

        return filing_dir / filename

    async def _save_content(self, filing: FilingInfo, content: str):
        """Save filing content to local storage"""
        local_path = self._get_local_path(filing)

        # Create directories if they don't exist
        local_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            async with aiofiles.open(local_path, "w", encoding="utf-8") as f:
                await f.write(content)

            logger.info(f"Saved filing to {local_path}")

        except Exception as e:
            logger.error(f"Failed to save filing to {local_path}: {e}")
            raise DownloadError(f"Failed to save filing: {e}")

    def get_local_status(self, filing: FilingInfo) -> dict:
        """Get local file status for a filing"""
        local_path = self._get_local_path(filing)

        if local_path.exists():
            try:
                size = local_path.stat().st_size
                return {
                    "is_local": True,
                    "path": str(local_path),
                    "size": size,
                    "display": f"✅ Local ({size / (1024 * 1024):.1f}MB)"
                    if size > 1024 * 1024
                    else f"✅ Local ({size:,} bytes)",
                }
            except Exception:
                pass

        return {"is_local": False, "path": None, "size": None, "display": "🌐 Remote"}


# Convenience functions for backward compatibility
async def download_filing(filing: FilingInfo, save_to_disk: bool = False) -> str:
    """Download a single filing (convenience function)"""
    downloader = FilingDownloader()
    return await downloader.download_filing(filing, save_to_disk=save_to_disk)


async def download_filings(
    filings: list[FilingInfo], save_to_disk: bool = True
) -> list[str]:
    """Download multiple filings (convenience function)"""
    downloader = FilingDownloader()
    return await downloader.download_filings(filings, save_to_disk=save_to_disk)
