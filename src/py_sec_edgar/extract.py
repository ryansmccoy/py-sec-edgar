"""
SEC Filing Content Extraction

Simplified extraction module that provides essential filing content extraction
functionality while the comprehensive parse module is being redesigned.

This module replaces the complex parse module dependencies with streamlined
extraction capabilities for the current release.
"""

import logging
import os
import re

import chardet

from .core.path_utils import ensure_directory, safe_join
from .utilities import file_size, format_filename, uudecode

logger = logging.getLogger(__name__)


def extract(filing_json: dict, force: bool = False) -> dict:
    """
    Extract filing contents from complete submission files.

    Simplified version of the parse module extract functionality for
    essential filing processing workflows.

    Args:
        filing_json: Dictionary with filing information including:
            - extracted_filing_directory: Target directory
            - filing_filepath: Path to submission file
        force: If True, re-extract even if directory already exists

    Returns:
        Dictionary with filing contents (legacy format)
    """
    filing_contents = {}

    if not os.path.exists(filing_json["extracted_filing_directory"]) or force:
        if force and os.path.exists(filing_json["extracted_filing_directory"]):
            logger.info("FORCE: Re-extraction enabled - overwriting existing directory")

        logger.info("Extracting Filing Documents")

        try:
            filing_contents = extract_complete_submission_filing(
                filing_json["filing_filepath"],
                output_directory=filing_json["extracted_filing_directory"],
            )
        except UnicodeDecodeError as e:
            logger.error(f"Error Decoding: {e}")
        except Exception as e:
            logger.error(f"Extraction failed: {e}")

        logger.info("Extraction Complete")
    else:
        logger.info(
            f"WARNING: Extraction directory already exists - skipping extraction: {filing_json['extracted_filing_directory']}"
        )

    return filing_contents


def extract_complete_submission_filing(
    filepath: str, output_directory: str = None
) -> dict:
    """
    Extract documents from SEC complete submission filing.

    Simplified version of complete submission processing that handles
    basic document extraction without advanced parsing features.

    Args:
        filepath: Path to complete submission file
        output_directory: Directory to save extracted documents

    Returns:
        Dictionary with extracted documents (legacy format)
    """
    if not os.path.exists(filepath):
        logger.error(f"Filing file not found: {filepath}")
        return {}

    try:
        # Load and decode file
        with open(filepath, "rb") as f:
            raw_bytes = f.read()

        # Detect encoding
        encoding_result = chardet.detect(raw_bytes)
        encoding = encoding_result.get("encoding", "utf-8")

        try:
            content = raw_bytes.decode(encoding)
        except UnicodeDecodeError:
            logger.warning(f"Failed to decode with {encoding}, trying UTF-8")
            content = raw_bytes.decode("utf-8", errors="replace")

        # Create output directory if specified
        if output_directory:
            ensure_directory(output_directory)

        # Extract documents using simplified regex approach
        filing_documents = _extract_documents_simple(
            content, output_directory, encoding
        )

        logger.info(f"Extracted {len(filing_documents)} documents")
        return filing_documents

    except Exception as e:
        logger.error(f"Failed to extract complete submission filing: {e}")
        return {}


def _extract_documents_simple(
    content: str, output_directory: str = None, encoding: str = "utf-8"
) -> dict:
    """
    Simple document extraction using regex patterns.

    Args:
        content: Complete submission content
        output_directory: Directory to save files (optional)
        encoding: Text encoding

    Returns:
        Dictionary with document information
    """
    filing_documents = {}

    # Document boundary patterns
    document_pattern = re.compile(
        r"<DOCUMENT>\s*<TYPE>([^<\n]+)\s*<SEQUENCE>([^<\n]+)\s*<FILENAME>([^<\n]+)(?:\s*<DESCRIPTION>([^<\n]+))?",
        re.IGNORECASE | re.MULTILINE,
    )

    # Text content pattern
    text_pattern = re.compile(
        r"<(TEXT|text)>(.*?)</(TEXT|text)>", re.MULTILINE | re.DOTALL
    )

    # Find all document matches
    doc_matches = list(document_pattern.finditer(content))

    for i, match in enumerate(doc_matches, start=1):
        try:
            # Extract document metadata
            doc_type = match.group(1).strip()
            sequence = match.group(2).strip()
            filename = match.group(3).strip()
            description = match.group(4).strip() if match.group(4) else ""

            # Find document content boundaries
            start_pos = match.end()

            # Find next document or end of content
            if i < len(doc_matches):
                end_pos = doc_matches[i].start()
            else:
                # Look for end document tag or end of content
                end_match = re.search(
                    r"</DOCUMENT>", content[start_pos:], re.IGNORECASE
                )
                if end_match:
                    end_pos = start_pos + end_match.start()
                else:
                    end_pos = len(content)

            # Extract document content
            doc_content = content[start_pos:end_pos].strip()

            # Extract text content if present
            text_match = text_pattern.search(doc_content)
            if text_match:
                processed_content = text_match.group(2)
            else:
                processed_content = doc_content

            # Save document if output directory specified
            output_filepath = None
            if output_directory and processed_content:
                output_filepath = _save_document_simple(
                    processed_content,
                    doc_type,
                    sequence,
                    filename,
                    description,
                    output_directory,
                    encoding,
                )

            # Create document entry
            filing_documents[i] = {
                "TYPE": doc_type,
                "SEQUENCE": sequence,
                "FILENAME": filename,
                "DESCRIPTION": description,
                "RELATIVE_FILEPATH": output_filepath,
                "DESCRIPTIVE_FILEPATH": os.path.basename(output_filepath)
                if output_filepath
                else filename,
                "FILE_SIZE": file_size(output_filepath) if output_filepath else "N/A",
                "FILE_SIZE_BYTES": len(processed_content),
            }

            logger.debug(f"Extracted document {sequence}: {doc_type} - {filename}")

        except Exception as e:
            logger.error(f"Error processing document {i}: {e}")
            continue

    return filing_documents


def _save_document_simple(
    content: str,
    doc_type: str,
    sequence: str,
    filename: str,
    description: str,
    output_directory: str,
    encoding: str,
) -> str:
    """
    Save document content to file with simplified approach.

    Args:
        content: Document content
        doc_type: Document type
        sequence: Document sequence number
        filename: Original filename
        description: Document description
        output_directory: Output directory
        encoding: Text encoding

    Returns:
        Path to saved file
    """
    try:
        # Handle UUE encoded files
        if content.lower().startswith("begin"):
            uue_filepath = safe_join(output_directory, filename + ".uue")
            output_filepath = safe_join(output_directory, filename)

            # Save UUE content
            with open(uue_filepath, "w", encoding=encoding) as f:
                f.write(content)

            # Try to decode UUE file
            try:
                uudecode(str(uue_filepath), out_file=str(output_filepath))
                os.remove(uue_filepath)  # Clean up UUE file
                return output_filepath
            except Exception as e:
                logger.error(f"UUE decoding failed for {filename}: {e}")
                return uue_filepath

        # Handle regular text files
        else:
            # Create descriptive filename
            doc_num = f"{int(sequence):04d}"

            if description:
                output_filename = f"{doc_num}-({doc_type}) {description} {filename}"
            else:
                output_filename = f"{doc_num}-({doc_type}) {filename}"

            # Clean filename
            output_filename = format_filename(output_filename)
            output_filepath = safe_join(output_directory, output_filename)

            # Save content
            with open(output_filepath, "w", encoding=encoding) as f:
                f.write(content)

            return output_filepath

    except Exception as e:
        logger.error(f"Failed to save document {filename}: {e}")
        return None


# Legacy compatibility functions removed - functionality moved to parse module
