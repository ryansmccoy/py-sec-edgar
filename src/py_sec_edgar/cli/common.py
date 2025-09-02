"""
Common CLI utilities and helpers for parsing options.
"""

import csv
from pathlib import Path

import click

from ..settings import settings


# Standard option decorators for consistency across commands
def standard_ticker_options(func):
    """Standard ticker filtering options."""
    func = click.option(
        "--no-ticker-filter",
        is_flag=True,
        help="Disable ticker filtering (process all tickers)"
    )(func)
    func = click.option(
        "--ticker-file",
        type=click.Path(exists=True, path_type=Path),
        help="CSV or text file containing ticker symbols"
    )(func)
    func = click.option(
        "-t", "--tickers",
        multiple=True,
        help="Ticker symbols to filter (space or comma separated). Example: --tickers NVDA AAPL or --tickers \"NVDA,AAPL\""
    )(func)
    return func


def standard_form_options(func):
    """Standard form type filtering options."""
    func = click.option(
        "--no-form-filter",
        is_flag=True,
        help="Disable form type filtering (process all forms)"
    )(func)
    func = click.option(
        "--form",
        type=str,
        help="Single form type to filter. Example: --form \"10-K\""
    )(func)
    func = click.option(
        "-f", "--forms",
        multiple=True,
        help="Form types to filter (space or comma separated). Example: --forms \"10-K\" \"10-Q\" or --forms \"10-K,8-K\""
    )(func)
    return func


def standard_date_options(func):
    """Standard date range options."""
    func = click.option(
        "--end-date",
        type=str,
        help="End date for processing (YYYY-MM-DD format)"
    )(func)
    func = click.option(
        "--start-date", 
        type=str,
        help="Start date for processing (YYYY-MM-DD format)"
    )(func)
    return func


def standard_processing_options(func):
    """Standard processing behavior options."""
    func = click.option(
        "--skip-if-exists/--no-skip-if-exists",
        default=True,
        show_default=True,
        help="Skip download if files already exist"
    )(func)
    func = click.option(
        "--extract/--no-extract",
        default=False,
        show_default=True,
        help="Extract filing contents"
    )(func)
    func = click.option(
        "--download/--no-download",
        default=True,
        show_default=True,
        help="Download filing files"
    )(func)
    return func


def standard_output_options(func):
    """Standard output and limiting options."""
    func = click.option(
        "--output-dir",
        type=click.Path(path_type=Path),
        help="Custom output directory (defaults to configured data directory)"
    )(func)
    func = click.option(
        "--limit",
        type=int,
        help="Maximum number of items to process"
    )(func)
    return func


# Combined decorators for common use cases
def common_filter_options(func):
    """Combined ticker and form filtering options."""
    func = standard_form_options(func)
    func = standard_ticker_options(func)
    return func


def standard_workflow_options(func):
    """Standard options for workflow commands."""
    func = standard_output_options(func)
    func = standard_processing_options(func)
    func = standard_date_options(func)
    func = standard_form_options(func)
    func = standard_ticker_options(func)
    return func


def parse_tickers(
    tickers: list[str] | None = None,
    ticker_file: Path | None = None,
    no_ticker_filter: bool = False
) -> list[str] | None:
    """
    Parse ticker input from various sources.
    
    Args:
        tickers: List of ticker strings (can contain comma-separated values)
        ticker_file: Path to CSV/TXT file containing tickers
        no_ticker_filter: If True, disable ticker filtering entirely
        
    Returns:
        List of ticker symbols, or None if no filtering should be applied
    """
    if no_ticker_filter:
        return None

    # If specific tickers provided via command line
    if tickers:
        ticker_list = []
        for ticker_arg in tickers:
            # Handle comma-separated values in single arguments
            if ',' in ticker_arg:
                ticker_list.extend([t.strip().upper() for t in ticker_arg.split(',')])
            else:
                ticker_list.append(ticker_arg.strip().upper())
        return list(set(ticker_list))  # Remove duplicates

    # If ticker file provided
    if ticker_file:
        return load_tickers_from_file(ticker_file)

    # Use defaults from settings if available
    if settings.default_tickers:
        return settings.default_tickers.copy()

    # If no tickers specified and no defaults, load from default file if it exists
    if settings.ticker_list_filepath.exists():
        return load_tickers_from_file(settings.ticker_list_filepath)

    return None


def parse_forms(
    forms: list[str] | None = None,
    form: str | None = None,
    no_form_filter: bool = False
) -> list[str] | None:
    """
    Parse form type input from various sources.
    
    Args:
        forms: List of form type strings (can contain comma-separated values)
        form: Single form type string
        no_form_filter: If True, disable form filtering entirely
        
    Returns:
        List of form types, or None if no filtering should be applied
    """
    if no_form_filter:
        return None

    # If specific forms provided via command line
    if forms:
        form_list = []
        for form_arg in forms:
            # Handle comma-separated values in single arguments
            if ',' in form_arg:
                form_list.extend([f.strip().upper() for f in form_arg.split(',')])
            else:
                form_list.append(form_arg.strip().upper())
        return list(set(form_list))  # Remove duplicates

    # If single form provided
    if form:
        return [form.strip().upper()]

    # Use defaults from settings
    if settings.forms_list:
        return settings.forms_list.copy()

    return None


def load_tickers_from_file(file_path: Path) -> list[str]:
    """
    Load ticker symbols from a CSV or text file.
    
    Args:
        file_path: Path to the file containing ticker symbols
        
    Returns:
        List of ticker symbols
    """
    tickers = []

    try:
        with open(file_path, encoding='utf-8') as f:
            # Try to detect if it's a CSV file
            if file_path.suffix.lower() == '.csv':
                reader = csv.reader(f)
                for row in reader:
                    # Skip empty rows
                    if row:
                        # Take the first column, or all columns if they're all tickers
                        tickers.extend([cell.strip().upper() for cell in row if cell.strip()])
            else:
                # Treat as plain text file with one ticker per line
                for line in f:
                    ticker = line.strip().upper()
                    if ticker and not ticker.startswith('#'):  # Skip comments
                        tickers.append(ticker)

    except Exception as e:
        raise click.ClickException(f"Error reading ticker file {file_path}: {e}")

    return list(set(tickers))  # Remove duplicates


def validate_tickers(tickers: list[str]) -> list[str]:
    """
    Validate and clean ticker symbols.
    
    Args:
        tickers: List of ticker symbols
        
    Returns:
        List of validated ticker symbols
    """
    valid_tickers = []

    for ticker in tickers:
        # Basic validation - should be alphanumeric and reasonable length
        clean_ticker = ticker.strip().upper()
        if clean_ticker and clean_ticker.isalnum() and len(clean_ticker) <= 10:
            valid_tickers.append(clean_ticker)
        else:
            click.echo(f"Warning: Skipping invalid ticker symbol: {ticker}", err=True)

    return valid_tickers


def validate_forms(forms: list[str]) -> list[str]:
    """
    Validate and clean form types.
    
    Args:
        forms: List of form types
        
    Returns:
        List of validated form types
    """
    valid_forms = []
    common_forms = {
        '10-K', '10-Q', '8-K', 'DEF 14A', '13F-HR', 'SC 13G', 'SC 13D',
        '10-K/A', '10-Q/A', '8-K/A', '20-F', '6-K', 'S-1', 'S-3', 'S-4'
    }

    for form in forms:
        clean_form = form.strip().upper()
        if clean_form:
            valid_forms.append(clean_form)
            if clean_form not in common_forms:
                click.echo(f"Info: Using non-standard form type: {clean_form}", err=True)

    return valid_forms


# Common Click options that can be reused across commands
def ticker_options(f):
    """Decorator to add common ticker filtering options."""
    f = click.option(
        '--tickers', '-t',
        multiple=True,
        help='Ticker symbols to filter (space or comma separated). Example: --tickers NVDA AAPL or --tickers "NVDA,AAPL"'
    )(f)
    f = click.option(
        '--ticker-file',
        type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path),
        help='CSV or text file containing ticker symbols'
    )(f)
    f = click.option(
        '--no-ticker-filter',
        is_flag=True,
        help='Disable ticker filtering (process all tickers)'
    )(f)
    return f


def form_options(f):
    """Decorator to add common form filtering options."""
    f = click.option(
        '--forms', '-f',
        multiple=True,
        help='Form types to filter (space or comma separated). Example: --forms "10-K" "10-Q" or --forms "10-K,8-K"'
    )(f)
    f = click.option(
        '--form',
        help='Single form type to filter. Example: --form "10-K"'
    )(f)
    f = click.option(
        '--no-form-filter',
        is_flag=True,
        help='Disable form type filtering (process all forms)'
    )(f)
    return f


def common_filter_options(f):
    """Decorator to add both ticker and form filtering options."""
    f = form_options(f)
    f = ticker_options(f)
    return f
