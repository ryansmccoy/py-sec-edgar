import logging
import os
from urllib.parse import urljoin

import pandas as pd
import pyarrow as pa
from pyarrow import parquet as pq

from ..settings import settings
from ..utilities import walk_dir_fullpath


def merge_idx_files():

    files = walk_dir_fullpath(str(settings.full_index_data_dir), contains='.csv')

    if len(files) == 0:
        print('No Index files found')
        return

    dfs = []

    for f in files:
        try:
            df = pd.read_csv(f, sep=',', dtype={"CIK": int, "Company Name": "string", "Form Type": "string", "Date Filed": "string", "Filename": "string"})
            dfs.append(df)
            print(f'Loaded {f} - {len(df)} records')
        except Exception as e:
            print(f'Error loading {f}: {e}')
            continue

    df_idx = pd.concat(dfs)

    pa_filings = pa.Table.from_pandas(df_idx)

    # out_path = os.path.join(str(settings.ref_dir), 'merged_idx_files.csv')
    # df_idx.to_csv(out_path)

    pq_filepath = str(settings.merged_idx_filepath)

    if os.path.exists(pq_filepath):
        os.remove(pq_filepath)

    pq.write_table(pa_filings, pq_filepath, compression='snappy')

    # arrow_table = pa.Table.from_pandas(df_idx)
    # pq.write_table(arrow_table, out_path, compression='GZIP')

    print(f'\\n\\n\\tMerged {len(files)} files into {pq_filepath}\\n\\n')


def convert_idx_to_csv(file_path: str) -> None:
    """Convert .idx file to .csv format."""

    # Determine the output path by replacing .idx with .csv
    csv_path = file_path.replace('.idx', '.csv')

    try:
        # First, read the file to find where the data starts
        with open(file_path, encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()

        # Find the line that contains the column headers
        header_line_idx = -1
        data_start_idx = -1

        for i, line in enumerate(lines):
            # Look for the header line containing "CIK"
            if 'CIK' in line and 'Company Name' in line and 'Form Type' in line:
                header_line_idx = i
                # Data starts after the separator line (usually dashes)
                for j in range(i + 1, len(lines)):
                    if lines[j].strip().startswith('----'):
                        data_start_idx = j + 1
                        break
                break

        if data_start_idx == -1:
            # Fallback: skip common number of header lines
            data_start_idx = 11

        # Read the .idx file starting from the data section
        df = pd.read_csv(file_path, sep='|', skiprows=data_start_idx,
                        names=["CIK", "Company Name", "Form Type", "Date Filed", "Filename"],
                        dtype={"CIK": "string", "Company Name": "string", "Form Type": "string",
                               "Date Filed": "string", "Filename": "string"})

        # Clean the data - remove any rows that don't have proper CIK values
        df = df.dropna(subset=['CIK'])
        df = df[df['CIK'].str.strip() != '']

        # Convert CIK to integer, but handle errors gracefully
        def safe_int_convert(val):
            try:
                return int(str(val).strip())
            except (ValueError, TypeError):
                return None

        df['CIK'] = df['CIK'].apply(safe_int_convert)
        df = df.dropna(subset=['CIK'])  # Remove rows where CIK conversion failed
        df['CIK'] = df['CIK'].astype(int)

        # Clean other columns
        for col in ["Company Name", "Form Type", "Date Filed", "Filename"]:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()

        # Remove any rows with empty or invalid data
        df = df[df['Company Name'].str.len() > 0]
        df = df[df['Form Type'].str.len() > 0]

        # Save as CSV
        df.to_csv(csv_path, index=False)
        print(f'Converted {file_path} to {csv_path} - {len(df)} records')

    except Exception as e:
        print(f'Error converting {file_path}: {e}')
        import traceback
        traceback.print_exc()


def load_local_idx_filing_list(ticker_list_filter=True, form_list_filter=True):

    df_cik_tickers = pd.read_csv(str(settings.cik_tickers_csv))

    logging.info('\\n\\n\\n\\tLoaded IDX files\\n\\n\\n')

    df_merged_idx_filings = pq.read_table(str(settings.merged_idx_filepath)).to_pandas().sort_values("Date Filed", ascending=False)
    # df_merged_idx_filings = pd.read_csv(str(settings.merged_idx_filepath), index_col=0,  dtype={"CIK": int}, encoding='latin-1')

    if ticker_list_filter:
        ticker_list = pd.read_csv(str(settings.ticker_list_filepath), header=None).iloc[:, 0].tolist()
        df_cik_tickers = df_cik_tickers[df_cik_tickers['SYMBOL'].isin(ticker_list)]

    if form_list_filter:
        logging.info('\\n\\n\\n\\tLoading Forms Filter\\n\\n\\n')
        df_merged_idx_filings = df_merged_idx_filings[df_merged_idx_filings['Form Type'].isin(settings.forms_list)]

    df_cik_tickers = df_cik_tickers.dropna(subset=['CIK'])

    df_cik_tickers['CIK'] = df_cik_tickers['CIK'].astype(int)

    cik_list = df_cik_tickers['CIK'].tolist()

    df_merged_idx_filings = df_merged_idx_filings[df_merged_idx_filings['CIK'].isin(cik_list)]

    df_filings = df_merged_idx_filings.assign(url=df_merged_idx_filings['Filename'].apply(lambda x: urljoin(settings.edgar_archives_url, x)))

    return df_filings
