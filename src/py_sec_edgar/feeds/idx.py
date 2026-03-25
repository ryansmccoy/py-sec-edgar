import logging
import os
from urllib.parse import urljoin

import pandas as pd
import pyarrow as pa
from pyarrow import parquet as pq

from ..settings import settings
from ..utilities import walk_dir_fullpath


def merge_idx_files(force_rebuild=False, include_daily=False, include_rss=False):
    """
    Merge all CSV index files into a unified parquet file for fast searching.

    IMPORTANT: IDX files are updated quarterly by the SEC. The most recent quarter's
    data may not be complete until the quarter ends. For the most current filings,
    use the search engine's real-time API features instead of idx file data.

    Args:
        force_rebuild: If True, rebuild even if merged file is current
        include_daily: If True, include daily feed data (future enhancement)
        include_rss: If True, include RSS feed data (future enhancement)
    """
    logger = logging.getLogger(__name__)

    # Find all CSV files in the full-index directory
    csv_files = walk_dir_fullpath(
        str(settings.edgar_data_dir / "full-index"), contains=".csv"
    )

    if len(csv_files) == 0:
        logger.warning(
            "No CSV index files found. Run feeds update-full-index --save-csv first."
        )
        logger.info(
            "ℹ️  Note: IDX files are updated quarterly by SEC - for current filings use real-time search"
        )
        return False

    # Check if rebuild is needed
    merged_path = settings.merged_idx_filepath
    if not force_rebuild and merged_path.exists():
        merged_mtime = os.path.getmtime(merged_path)
        newest_csv_mtime = max(os.path.getmtime(f) for f in csv_files)

        if merged_mtime >= newest_csv_mtime:
            logger.info("Merged index is current. Use --force to rebuild anyway.")
            return True

    logger.info(f"Merging {len(csv_files)} CSV files into unified index...")
    logger.info(
        "ℹ️  Note: IDX files contain quarterly SEC data and may not include the most recent filings"
    )

    dfs = []
    records_processed = 0

    for csv_file in csv_files:
        try:
            df = pd.read_csv(
                csv_file,
                sep=",",
                dtype={
                    "CIK": "int64",
                    "Company Name": "string",
                    "Form Type": "string",
                    "Date Filed": "string",
                    "Filename": "string",
                },
            )

            if len(df) > 0:
                dfs.append(df)
                records_processed += len(df)
                logger.debug(f"Loaded {csv_file} - {len(df):,} records")
            else:
                logger.warning(f"Empty file: {csv_file}")

        except Exception as e:
            logger.error(f"Error loading {csv_file}: {e}")
            continue

    if not dfs:
        logger.error("No valid CSV files could be loaded")
        return False

    # Combine all dataframes
    logger.info(
        f"Combining {len(dfs)} dataframes with {records_processed:,} total records..."
    )
    df_merged = pd.concat(dfs, ignore_index=True)

    # Remove duplicates and sort by date
    initial_count = len(df_merged)
    df_merged = df_merged.drop_duplicates(
        subset=["CIK", "Form Type", "Date Filed", "Filename"]
    )
    df_merged = df_merged.sort_values("Date Filed", ascending=False)
    final_count = len(df_merged)

    if initial_count != final_count:
        logger.info(f"Removed {initial_count - final_count:,} duplicate records")

    # Convert to pyarrow table and save
    pa_table = pa.Table.from_pandas(df_merged)

    # Ensure directory exists
    merged_path.parent.mkdir(parents=True, exist_ok=True)

    # Remove old file if it exists
    if merged_path.exists():
        merged_path.unlink()

    # Write new merged file
    pq.write_table(pa_table, str(merged_path), compression="snappy")

    logger.info(f"✅ Successfully merged {final_count:,} records into {merged_path}")
    logger.info(f"📁 File size: {merged_path.stat().st_size / 1024 / 1024:.1f} MB")

    return True


def convert_idx_to_csv(file_path, skip_if_exists=True) -> None:
    """Convert .idx file to .csv format.

    Args:
        file_path: Path to the .idx file
        skip_if_exists: If True, skip conversion if CSV already exists
    """

    # Ensure file_path is a string (handle both str and Path objects)
    file_path = str(file_path)

    # Determine the output path by replacing .idx with .csv
    csv_path = file_path.replace(".idx", ".csv")

    # Skip if CSV already exists and skip_if_exists is True
    if skip_if_exists and os.path.exists(csv_path):
        # Quick check if CSV is newer than IDX
        if os.path.getmtime(csv_path) >= os.path.getmtime(file_path):
            return

    try:
        # First, read the file to find where the data starts
        with open(file_path, encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()

        # Find the line that contains the column headers
        # UNUSED: header_line_idx = -1  # Dead code - variable assigned but never used
        data_start_idx = -1

        for i, line in enumerate(lines):
            # Look for the header line containing "CIK"
            if "CIK" in line and "Company Name" in line and "Form Type" in line:
                # UNUSED: header_line_idx = i  # Dead code - variable assigned but never used
                # Data starts after the separator line (usually dashes)
                for j in range(i + 1, len(lines)):
                    if lines[j].strip().startswith("----"):
                        data_start_idx = j + 1
                        break
                break

        if data_start_idx == -1:
            # Fallback: skip common number of header lines
            data_start_idx = 11

        # Read the .idx file starting from the data section
        df = pd.read_csv(
            file_path,
            sep="|",
            skiprows=data_start_idx,
            names=["CIK", "Company Name", "Form Type", "Date Filed", "Filename"],
            dtype={
                "CIK": "string",
                "Company Name": "string",
                "Form Type": "string",
                "Date Filed": "string",
                "Filename": "string",
            },
        )

        # Clean the data - remove any rows that don't have proper CIK values
        df = df.dropna(subset=["CIK"])
        df = df[df["CIK"].str.strip() != ""]

        # Convert CIK to integer, but handle errors gracefully
        def safe_int_convert(val):
            try:
                return int(str(val).strip())
            except (ValueError, TypeError):
                return None

        df["CIK"] = df["CIK"].apply(safe_int_convert)
        df = df.dropna(subset=["CIK"])  # Remove rows where CIK conversion failed
        df["CIK"] = df["CIK"].astype(int)

        # Clean other columns
        for col in ["Company Name", "Form Type", "Date Filed", "Filename"]:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()

        # Remove any rows with empty or invalid data
        df = df[df["Company Name"].str.len() > 0]
        df = df[df["Form Type"].str.len() > 0]

        # Save as CSV
        df.to_csv(csv_path, index=False)

        # Calculate file sizes for logging
        idx_size = os.path.getsize(file_path) / 1024  # KB
        csv_size = os.path.getsize(csv_path) / 1024  # KB

        logger = logging.getLogger(__name__)
        logger.debug(
            f"✅ Converted {os.path.basename(file_path)} → CSV: {len(df):,} records ({idx_size:.1f}KB → {csv_size:.1f}KB)"
        )

    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"❌ Error converting {os.path.basename(file_path)}: {e}")
        logger.debug(f"Full path: {file_path}")
        # Still include traceback for debugging but through logging
        import traceback

        logger.debug(f"Conversion error traceback: {traceback.format_exc()}")


def load_local_idx_filing_list(ticker_list_filter=True, form_list_filter=True):
    """
    Load filing list from local IDX files.

    IMPORTANT DATA CURRENCY NOTICE:
    - IDX files are updated quarterly by the SEC
    - Current quarter data may be incomplete until quarter-end
    - For real-time filing data, use FilingSearchEngine with API calls
    - Full and quarterly index files are rebuilt weekly (Saturday mornings)

    Args:
        ticker_list_filter: If True, filter by configured ticker list
        form_list_filter: If True, filter by configured form types

    Returns:
        DataFrame with historical filing data from IDX files
    """

    df_cik_tickers = pd.read_csv(str(settings.cik_tickers_csv))

    logging.info("\\n\\n\\n\\tLoaded IDX files\\n\\n\\n")

    df_merged_idx_filings = (
        pq.read_table(str(settings.merged_idx_filepath))
        .to_pandas()
        .sort_values("Date Filed", ascending=False)
    )
    # df_merged_idx_filings = pd.read_csv(str(settings.merged_idx_filepath), index_col=0,  dtype={"CIK": int}, encoding='latin-1')

    if ticker_list_filter:
        ticker_list = (
            pd.read_csv(str(settings.ticker_list_filepath), header=None)
            .iloc[:, 0]
            .tolist()
        )
        df_cik_tickers = df_cik_tickers[df_cik_tickers["SYMBOL"].isin(ticker_list)]

    if form_list_filter:
        logging.info("\\n\\n\\n\\tLoading Forms Filter\\n\\n\\n")
        df_merged_idx_filings = df_merged_idx_filings[
            df_merged_idx_filings["Form Type"].isin(settings.forms_list)
        ]

    df_cik_tickers = df_cik_tickers.dropna(subset=["CIK"])

    df_cik_tickers["CIK"] = df_cik_tickers["CIK"].astype(int)

    cik_list = df_cik_tickers["CIK"].tolist()

    df_merged_idx_filings = df_merged_idx_filings[
        df_merged_idx_filings["CIK"].isin(cik_list)
    ]

    df_filings = df_merged_idx_filings.assign(
        url=df_merged_idx_filings["Filename"].apply(
            lambda x: urljoin(settings.edgar_archives_url, x)
        )
    )

    return df_filings
