"""SEC Filing Processing Engine

This module provides the FilingProcessor class for automated downloading and
extraction of SEC EDGAR filings. It handles the complete workflow from filing
metadata to downloaded and extracted filing documents.

The FilingProcessor manages:
    - File path generation for organized storage
    - SEC EDGAR Archive downloads with proper rate limiting
    - Filing extraction and document processing
    - Post-processing hooks for custom analysis

Example:
    Basic filing processor setup:

    ```python
    from py_sec_edgar.process import FilingProcessor

    processor = FilingProcessor(
        filing_data_dir="/data/filings/CIK/FOLDER",
        edgar_Archives_url="https://www.sec.gov/Archives/",
        download=True,
        extract=True
    )

    # Process a filing from feed data
    filing_meta = {
        'CIK': '0000320193',
        'Filename': 'edgar/data/320193/0000320193-23-000006.txt'
    }
    processor.process(filing_meta)
    ```

See Also:
    extract: Filing content extraction utilities
    utilities.download: Low-level download functions
    core.path_utils: Safe file path utilities
"""

import logging
import os
from urllib.parse import urljoin

from .core.path_utils import safe_join
from .extract import extract
from .utilities import download

logger = logging.getLogger(__name__)


class FilingProcessor:
    """SEC Filing Processor for automated download and extraction workflows.

    This class manages the complete lifecycle of SEC filing processing from
    metadata to extracted documents. It provides configurable options for
    downloading and extracting filing content with proper path management.

    Attributes:
        filing_data_dir (str): Directory template for storing filing data.
            Uses placeholders 'CIK' and 'FOLDER' for dynamic path generation.
        edgar_Archives_url (str): Base URL for SEC EDGAR Archives.
        download_enabled (bool): Whether to download filing files.
        extract_enabled (bool): Whether to extract filing documents.

    Example:
        ```python
        processor = FilingProcessor(
            filing_data_dir="/data/filings/CIK/FOLDER",
            edgar_Archives_url="https://www.sec.gov/Archives/",
            download=True,
            extract=True
        )
        ```
    """

    def __init__(
        self,
        filing_data_dir: str,
        edgar_Archives_url: str,
        download: bool = True,
        extract: bool = False,
    ) -> None:
        """Initialize the FilingProcessor with configuration options.

        Args:
            filing_data_dir: Directory template with CIK and FOLDER placeholders.
            edgar_Archives_url: Base URL for SEC EDGAR Archives.
            download: Enable automatic filing downloads.
            extract: Enable automatic filing extraction.
        """
        logger.info("Initializing FilingProcessor...")

        self.filing_data_dir = filing_data_dir
        self.edgar_Archives_url = edgar_Archives_url

        self.download_enabled = download
        self.extract_enabled = extract

    def generate_filepaths(self, sec_filing: dict) -> dict:
        """Generate standardized file paths for SEC filing storage.

        Creates a complete set of file paths for organizing filing data including
        directories, file paths, URLs, and extracted content locations. Uses the
        configured directory template with CIK and folder substitutions.

        Args:
            sec_filing: Dictionary containing SEC filing metadata with keys:
                - CIK: Company Central Index Key
                - Filename: SEC filing filename from feed data

        Returns:
            Enhanced filing dictionary with additional path fields:
                - cik_directory: Company-specific directory path
                - filing_filepath: Path to downloaded filing file
                - filing_zip_filepath: Path to compressed filing file
                - filing_folder: Folder name for extracted content
                - extracted_filing_directory: Directory for extracted documents
                - filing_url: Complete URL for SEC filing download

        Example:
            ```python
            filing_meta = {
                'CIK': '0000320193',
                'Filename': 'edgar/data/320193/0000320193-23-000006.txt'
            }
            paths = processor.generate_filepaths(filing_meta)
            # Returns enhanced dict with all file paths populated
            ```
        """

        feed_item = dict(sec_filing)
        feed_item["cik_directory"] = self.filing_data_dir.replace(
            "CIK", str(feed_item["CIK"])
        ).replace("FOLDER", "")
        feed_item["filing_filepath"] = safe_join(
            feed_item["cik_directory"], os.path.basename(feed_item["Filename"])
        )
        feed_item["filing_zip_filepath"] = safe_join(
            feed_item["cik_directory"],
            os.path.basename(feed_item["Filename"]).replace(".txt", ".zip"),
        )
        feed_item["filing_folder"] = (
            os.path.basename(feed_item["Filename"]).split(".")[0].replace("-", "")
        )
        feed_item["extracted_filing_directory"] = self.filing_data_dir.replace(
            "CIK", str(feed_item["CIK"])
        ).replace("FOLDER", feed_item["filing_folder"])
        feed_item["filing_url"] = urljoin(
            self.edgar_Archives_url, feed_item["Filename"]
        )

        return feed_item

    def process(self, filing_meta: dict) -> None:
        """Process a single SEC filing through the complete workflow.

        Manages the end-to-end processing of a SEC filing including path generation,
        downloading (if enabled), extraction (if enabled), and post-processing.
        Each step is logged and can be individually controlled via configuration.

        Args:
            filing_meta: Dictionary containing SEC filing metadata from feeds.
                Must include CIK and Filename at minimum.

        Note:
            The process respects the download_enabled and extract_enabled flags
            set during initialization. Disabled steps will be logged and skipped.

        Example:
            ```python
            filing_data = {
                'CIK': '0000320193',
                'Filename': 'edgar/data/320193/0000320193-23-000006.txt',
                'Date Filed': '2023-01-03',
                'Form Type': '10-K'
            }
            processor.process(filing_data)
            ```
        """

        filing_filepaths = self.generate_filepaths(filing_meta)

        if self.download_enabled:
            logger.info(
                f"Downloading filing: {filing_filepaths.get('filing_url', 'N/A')}"
            )
            filing_filepaths = download(filing_filepaths)
        else:
            logger.info("⚠️  Download disabled - skipping file download")

        if self.extract_enabled:
            logger.info(
                f"Extracting filing: {filing_filepaths.get('filing_filepath', 'N/A')}"
            )
            filing_content = extract(filing_filepaths)
            self.post_process(filing_content)
        else:
            logger.info("⚠️  Extract disabled - skipping file extraction")

    def post_process(self, filing_contents: dict) -> None:
        """Hook for custom post-processing of extracted filing contents.

        This method is called after successful filing extraction and provides
        a customization point for implementing domain-specific analysis, data
        transformation, or additional processing steps.

        Override this method in subclasses to implement custom processing logic
        such as:
            - Financial data extraction and analysis
            - Document classification and tagging
            - Database storage or API integration
            - Report generation and notifications

        Args:
            filing_contents: Dictionary containing extracted filing documents
                and metadata from the extraction process.

        Example:
            ```python
            class CustomProcessor(FilingProcessor):
                def post_process(self, filing_contents):
                    # Custom analysis logic
                    for doc_id, document in filing_contents.items():
                        if document['TYPE'] == '10-K':
                            self.analyze_10k_document(document)
            ```
        """
        pass
