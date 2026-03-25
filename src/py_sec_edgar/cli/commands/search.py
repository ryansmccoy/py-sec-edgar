"""SEC Filing Search and Analysis Commands

Professional command-line interface for SEC EDGAR filing search, download, and
AI-powered analysis. Provides intuitive access to the comprehensive py-sec-edgar
search engine with rich console output and progress tracking.

Key Features:
    🔍 **Smart Search**: Ticker-based filing discovery with fuzzy matching
    📥 **Intelligent Downloads**: Automatic filing retrieval with progress tracking
    🤖 **AI Analysis**: OpenAI-powered filing analysis (when API key configured)
    💬 **Interactive Chat**: Conversational analysis of downloaded filings
    📊 **Rich Output**: Professional console interface with tables and progress bars
    🛡️ **Error Handling**: Graceful error handling with helpful user guidance

Commands:
    search filings: Primary filing search and download interface
    search analyze: AI-powered analysis of downloaded filings
    search interactive: Start conversational AI session for filing analysis

Examples:
    Basic filing search:
    ```bash
    py-sec-edgar search filings --ticker AAPL --form-type 10-K --limit 5
    ```

    Download and analyze:
    ```bash
    py-sec-edgar search filings --ticker MSFT --download --chat
    ```

    AI analysis of specific filing:
    ```bash
    py-sec-edgar search analyze --filing-path ./downloads/filing.txt --question "What are the main risks?"
    ```

Dependencies:
    - OpenAI API key required for AI features (set OPENAI_API_KEY environment variable)
    - Rich console library for enhanced terminal output
    - Search engine data files (run `py-sec-edgar feeds update-full-index` if missing)

See Also:
    search_engine: Core filing search functionality
    ai_assistant: AI integration framework (when available)
    core.downloader: Filing download management
"""

import asyncio
import json as json_module
import os
from datetime import datetime

import click
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from py_sec_edgar.core.downloader import FilingDownloader
from py_sec_edgar.search_engine import (
    FilingSearchEngine,
    FilingSearchError,
)

# AI functionality is available when OpenAI API key is configured
AI_AVAILABLE = bool(os.getenv("OPENAI_API_KEY"))


class AIAnalysisError(Exception):
    """Exception raised when AI analysis operations fail."""

    pass


class FilingAIAssistant:
    """Placeholder for AI assistant functionality"""

    def __init__(self, openai_api_key: str = None):
        self.api_key = openai_api_key

    async def analyze_filing(self, content: str, question: str = None) -> str:
        return "AI analysis feature is not yet implemented. Please check back in future releases."


async def analyze_filing_content(content: str, question: str = None) -> str:
    """Placeholder for AI content analysis"""
    return "AI analysis feature is not yet implemented. Please check back in future releases."


console = Console()


def _output_json_results(
    filings: list, ticker: str, form_type: str, limit: int, per_ticker_limit: int | None
):
    """Output filing search results in JSON format for programmatic use"""
    import os

    from py_sec_edgar.settings import settings

    # Create search engine instance for status checking
    engine = FilingSearchEngine()

    # Prepare JSON data
    results = []
    local_count = 0

    for filing in filings:
        status, size = _check_local_file_status(filing, engine)
        is_local = status == "✅ Local"
        if is_local:
            local_count += 1

        # Calculate file paths
        # Create downloader to get local file path
        from py_sec_edgar.core.downloader import FilingDownloader

        downloader = FilingDownloader()
        local_path = downloader._get_local_path(filing)
        absolute_path = str(local_path.resolve()) if local_path.exists() else None
        relative_path = filing.filename

        # Get file stats if local
        file_stats = None
        file_size_bytes = None
        if absolute_path and os.path.exists(absolute_path):
            stat = os.stat(absolute_path)
            file_size_bytes = stat.st_size
            file_stats = {
                "size_bytes": stat.st_size,
                "size_human": size if size != "-" else None,
                "modified_timestamp": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "created_timestamp": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            }

        # Parse filing date components
        filing_date_parts = None
        if filing.filing_date:
            try:
                date_obj = datetime.strptime(filing.filing_date, "%Y-%m-%d")
                filing_date_parts = {
                    "year": date_obj.year,
                    "month": date_obj.month,
                    "day": date_obj.day,
                    "quarter": f"Q{(date_obj.month - 1) // 3 + 1}",
                    "fiscal_year": date_obj.year
                    if date_obj.month >= 10
                    else date_obj.year - 1,  # Assume Oct-Sep fiscal year
                }
            except ValueError:
                pass

        # Generate unique filing identifier
        filing_id = f"{filing.cik}_{filing.form_type}_{filing.filing_date}_{filing.filename.split('/')[-1].replace('.txt', '')}"

        # Convert filing to dictionary with enhanced structure
        filing_data = {
            "id": filing_id,
            "metadata": {
                "ticker": filing.ticker,
                "company_name": filing.company_name,
                "cik": filing.cik,
                "form_type": filing.form_type,
                "filing_date": filing.filing_date,
                "filing_date_parsed": filing_date_parts,
            },
            "files": {
                "local": {
                    "available": is_local,
                    "absolute_path": absolute_path,
                    "relative_path": relative_path,
                    "stats": file_stats,
                },
                "remote": {
                    "document_url": filing.document_url,
                    "sec_url": filing.document_url,
                    "downloadable": True,
                },
            },
            "processing": {
                "status": {
                    "downloaded": is_local,
                    "extracted": False,  # TODO: Check if extracted
                    "parsed": False,  # TODO: Check if parsed
                    "analyzed": False,  # TODO: Check if AI analyzed
                },
                "hints": {
                    "estimated_size_mb": round(file_size_bytes / 1024 / 1024, 2)
                    if file_size_bytes
                    else None,
                    "processing_time_estimate": "fast"
                    if file_size_bytes and file_size_bytes < 1024 * 1024
                    else "medium"
                    if file_size_bytes and file_size_bytes < 10 * 1024 * 1024
                    else "slow",
                    "recommended_memory_mb": max(
                        64, round(file_size_bytes / 1024 / 1024 * 2, 0)
                    )
                    if file_size_bytes
                    else 64,
                },
            },
            "business": {
                "quarter_info": _get_quarter_info(filing.filing_date, filing.form_type)
                if form_type == "10-Q"
                else None,
                "form_category": _categorize_form_type(filing.form_type),
                "urgency": _get_filing_urgency(filing.form_type),
                "typical_sections": _get_expected_sections(filing.form_type),
            },
        }

        results.append(filing_data)

    # Create metadata
    unique_companies = {(filing.ticker, filing.company_name) for filing in filings}

    # Calculate aggregate statistics
    total_size_bytes = sum(
        f.get("files", {}).get("local", {}).get("stats", {}).get("size_bytes", 0) or 0
        for f in results
        if f.get("files", {}).get("local", {}).get("stats")
    )
    date_ranges = [
        f["metadata"]["filing_date"] for f in results if f["metadata"]["filing_date"]
    ]

    output_data = {
        "api_version": "1.0",
        "metadata": {
            "search": {
                "timestamp": datetime.now().isoformat(),
                "form_type": form_type,
                "tickers_requested": ticker.split(",") if "," in ticker else [ticker],
                "limit_strategy": "per_ticker"
                if per_ticker_limit is not None
                else "total",
                "limit_value": per_ticker_limit
                if per_ticker_limit is not None
                else limit,
            },
            "results": {
                "total_filings": len(filings),
                "companies_found": len(unique_companies),
                "local_files": local_count,
                "remote_files": len(filings) - local_count,
                "date_range": {
                    "earliest": min(date_ranges) if date_ranges else None,
                    "latest": max(date_ranges) if date_ranges else None,
                },
            },
            "storage": {
                "local_directory": str(settings.data_dir / "downloads" / "filings"),
                "data_source": str(settings.ref_dir / "company_tickers.json"),
                "total_local_size_bytes": total_size_bytes,
                "total_local_size_mb": round(total_size_bytes / 1024 / 1024, 2)
                if total_size_bytes
                else 0,
            },
            "processing_summary": {
                "form_category": _categorize_form_type(form_type),
                "avg_urgency": _calculate_avg_urgency(
                    [f["business"]["urgency"] for f in results]
                ),
                "estimated_processing_time": _estimate_batch_processing_time(results),
                "recommended_parallel_jobs": min(4, max(1, local_count // 2))
                if local_count > 0
                else 1,
            },
        },
        "companies": [
            {
                "ticker": ticker,
                "company_name": company_name,
                "cik": next(
                    (
                        f["metadata"]["cik"]
                        for f in results
                        if f["metadata"]["ticker"] == ticker
                    ),
                    None,
                ),
                "filing_count": len(
                    [f for f in results if f["metadata"]["ticker"] == ticker]
                ),
            }
            for ticker, company_name in sorted(unique_companies)
        ],
        "filings": results,
        "download_instructions": {
            "missing_files": [
                {
                    "id": f["id"],
                    "url": f["files"]["remote"]["document_url"],
                    "local_path": f["files"]["local"]["relative_path"],
                }
                for f in results
                if not f["files"]["local"]["available"]
            ],
            "batch_download_command": f"py-sec-edgar search filings --ticker {ticker} --form-type {form_type} --download-all --limit {len(filings)}",
            "individual_download_urls": [
                f["files"]["remote"]["document_url"]
                for f in results
                if not f["files"]["local"]["available"]
            ],
        },
    }

    # Output JSON to stdout for piping
    click.echo(json_module.dumps(output_data, indent=2, default=str))


@click.group(name="search")
def search_group():
    """Search and analyze SEC filings with AI assistance"""
    pass


@search_group.command()
@click.option(
    "--ticker",
    required=True,
    help="Company ticker symbol (e.g., AAPL, MSFT)",
    metavar="SYMBOL",
)
@click.option(
    "--form-type",
    default="10-K",
    help="SEC form type to search for (default: 10-K)",
    metavar="TYPE",
)
@click.option(
    "--limit",
    default=10,
    help="Maximum number of total filings to show across all companies (default: 10)",
    type=int,
)
@click.option(
    "--per-ticker-limit",
    default=None,
    help="Maximum number of filings per company (overrides --limit behavior)",
    type=int,
)
@click.option(
    "--chat",
    is_flag=True,
    help="Start interactive AI chat session about the latest filing",
)
@click.option(
    "--analyze",
    help="Ask AI to analyze the latest filing with a specific question",
    metavar="QUESTION",
)
@click.option(
    "--download", is_flag=True, help="Download the latest filing content for analysis"
)
@click.option(
    "--download-all", is_flag=True, help="Download all found filings to local storage"
)
@click.option(
    "--json", is_flag=True, help="Output results in JSON format for programmatic use"
)
def filings(
    ticker: str,
    form_type: str,
    limit: int,
    per_ticker_limit: int | None,
    chat: bool,
    analyze: str | None,
    download: bool,
    download_all: bool,
    json: bool,
):
    """
    Search SEC filings for a company ticker

    Examples:

      # Basic search (10 total filings across all companies)
      py-sec-edgar search filings --ticker AAPL

      # Limit total results across all companies
      py-sec-edgar search filings --ticker AAPL,MSFT --limit 5

      # Limit results per company (old behavior)
      py-sec-edgar search filings --ticker AAPL,MSFT --per-ticker-limit 3

      # Search specific form type
      py-sec-edgar search filings --ticker AAPL --form-type 10-Q

      # Download all found filings
      py-sec-edgar search filings --ticker AAPL,MSFT --download-all

      # AI analysis of latest filing
      py-sec-edgar search filings --ticker AAPL --analyze "What are the main business risks?"

      # JSON output for programmatic use
      py-sec-edgar search filings --ticker AAPL --json > results.json

      # Pipe JSON to other programs
      py-sec-edgar search filings --ticker AAPL,MSFT --json | jq '.filings[].ticker'
    """
    asyncio.run(
        _search_filings_async(
            ticker,
            form_type,
            limit,
            per_ticker_limit,
            chat,
            analyze,
            download,
            download_all,
            json,
        )
    )


async def _search_filings_async(
    ticker: str,
    form_type: str,
    limit: int,
    per_ticker_limit: int | None,
    chat: bool,
    analyze: str | None,
    download: bool,
    download_all: bool,
    json: bool,
):
    """Async implementation of filing search"""

    # Suppress logging output for JSON mode to ensure clean JSON output
    if json:
        import logging

        logging.getLogger().setLevel(logging.ERROR)

    try:
        # Determine search strategy based on limit options
        if per_ticker_limit is not None:
            # Use per-ticker limit (old behavior)
            search_limit = per_ticker_limit
            use_total_limit = False
            if not json:
                console.print(
                    f"[dim]Searching up to {per_ticker_limit} filings per company...[/dim]"
                )
        else:
            # Use total limit across all companies (new default behavior)
            # For multi-ticker, use higher per-ticker limit but apply total limit after
            search_limit = max(
                50, limit * 2
            )  # Search more per ticker to ensure we have enough for total limit
            use_total_limit = True
            if not json:
                console.print(
                    f"[dim]Searching up to {limit} total filings across all companies...[/dim]"
                )

        # Initialize search engine
        if json:
            # For JSON output, suppress progress indicators to avoid piping issues
            engine = FilingSearchEngine()
            filings = engine.search_by_ticker(
                ticker=ticker,
                form_types=[form_type] if form_type else None,
                limit=search_limit,
            )

            # Apply total limit if using new behavior
            if use_total_limit and len(filings) > limit:
                filings = filings[:limit]
        else:
            # Normal rich console output for interactive use
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task(
                    f"Searching {form_type} filings for {ticker.upper()}...", total=None
                )

                engine = FilingSearchEngine()
                filings = engine.search_by_ticker(
                    ticker=ticker,
                    form_types=[form_type] if form_type else None,
                    limit=search_limit,
                )

                # Apply total limit if using new behavior
                if use_total_limit and len(filings) > limit:
                    filings = filings[:limit]

                progress.update(task, completed=1)

        if not filings:
            if json:
                # Output empty JSON result
                empty_result = {
                    "metadata": {
                        "search_timestamp": datetime.now().isoformat(),
                        "form_type": form_type,
                        "search_tickers": ticker.split(",")
                        if "," in ticker
                        else [ticker],
                        "total_results": 0,
                        "limit_strategy": "per_ticker"
                        if per_ticker_limit is not None
                        else "total",
                        "limit_value": per_ticker_limit
                        if per_ticker_limit is not None
                        else limit,
                        "companies_found": 0,
                        "local_files": 0,
                        "remote_files": 0,
                    },
                    "companies": [],
                    "filings": [],
                }
                click.echo(json_module.dumps(empty_result, indent=2, default=str))
            else:
                console.print(
                    f"[yellow]No {form_type} filings found for {ticker.upper()}[/yellow]"
                )
            return

        # Display search results
        # Display results or output JSON
        if json:
            _output_json_results(filings, ticker, form_type, limit, per_ticker_limit)
        else:
            _display_filing_results(filings, ticker, form_type, limit, per_ticker_limit)

        # Handle download-all functionality
        if download_all:
            await _download_all_filings(engine, filings)
            return

        # Handle AI analysis or chat if requested
        if chat or analyze or download:
            latest_filing = filings[0]  # Use most recent filing

            if download or chat or analyze:
                # Download filing content
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=console,
                ) as progress:
                    task = progress.add_task(
                        "Downloading filing content...", total=None
                    )

                    filing_content = await engine.download_filing_content(latest_filing)

                    progress.update(task, completed=1)

                console.print(
                    f"[green]✅ Downloaded {len(filing_content):,} characters of filing content[/green]\n"
                )

            # Handle specific analysis request
            if analyze:
                await _analyze_filing(latest_filing, filing_content, analyze)

            # Handle interactive chat session
            elif chat:
                await _start_chat_session(latest_filing, filing_content)

    except FilingSearchError as e:
        if json:
            # Output error in JSON format
            error_result = {
                "error": {
                    "type": "FilingSearchError",
                    "message": str(e),
                    "timestamp": datetime.now().isoformat(),
                }
            }
            click.echo(json_module.dumps(error_result, indent=2))
        else:
            console.print(f"[red]❌ Search Error: {e}[/red]")
        raise click.Abort()
    except Exception as e:
        if json:
            # Output error in JSON format
            error_result = {
                "error": {
                    "type": "UnexpectedError",
                    "message": str(e),
                    "timestamp": datetime.now().isoformat(),
                }
            }
            click.echo(json_module.dumps(error_result, indent=2))
        else:
            console.print(f"[red]❌ Unexpected Error: {e}[/red]")
        raise click.Abort()


async def _download_all_filings(engine: FilingSearchEngine, filings: list):
    """Download all filings with progress tracking"""

    # Create unified downloader instance
    downloader = FilingDownloader()

    console.print(f"\n[bold cyan]📥 Downloading {len(filings)} filings...[/bold cyan]")

    # Check which files are already downloaded
    local_count = 0
    remote_count = 0

    for filing in filings:
        status, _, _ = engine.get_local_filing_status(filing)
        if status == "local":
            local_count += 1
        else:
            remote_count += 1

    if local_count > 0:
        console.print(f"[blue]📁 {local_count} files already available locally[/blue]")

    if remote_count == 0:
        console.print("[green]✅ All filings are already downloaded![/green]")
        return

    console.print(f"[yellow]🌐 Downloading {remote_count} new files...[/yellow]\n")

    # Download files with progress tracking
    downloaded_count = 0
    failed_count = 0
    total_size = 0

    for i, filing in enumerate(filings, 1):
        status, _, _ = engine.get_local_filing_status(filing)

        if status == "local":
            console.print(
                f"[dim]{i:2d}. {filing.ticker} {filing.filing_date} - Already downloaded[/dim]"
            )
            continue

        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task(
                    f"Downloading {filing.ticker} {filing.form_type} ({filing.filing_date})...",
                    total=None,
                )

                content = await downloader.download_filing(
                    filing, save_to_disk=True, show_progress=False
                )

                progress.update(task, completed=1)

            # Get file size for reporting
            _, size_str, _ = engine.get_local_filing_status(filing)
            total_size += len(content)
            downloaded_count += 1

            console.print(
                f"[green]{i:2d}. ✅ {filing.ticker} {filing.filing_date} - Downloaded ({size_str})[/green]"
            )

        except Exception as e:
            failed_count += 1
            console.print(
                f"[red]{i:2d}. ❌ {filing.ticker} {filing.filing_date} - Failed: {e}[/red]"
            )

    # Summary
    console.print("\n[bold]📊 Download Summary:[/bold]")
    console.print(
        f"[green]✅ Successfully downloaded: {downloaded_count} files[/green]"
    )
    if failed_count > 0:
        console.print(f"[red]❌ Failed: {failed_count} files[/red]")

    if total_size > 0:
        if total_size < 1024 * 1024:
            size_str = f"{total_size / 1024:.1f}KB"
        else:
            size_str = f"{total_size / (1024 * 1024):.1f}MB"
        console.print(f"[blue]📁 Total downloaded: {size_str}[/blue]")


def _get_quarter_info(filing_date: str, form_type: str) -> str:
    """Extract quarter information from filing date for quarterly reports"""
    if form_type != "10-Q":
        return "-"

    try:
        date_obj = datetime.strptime(filing_date, "%Y-%m-%d")
        month = date_obj.month
        year = date_obj.year

        # Determine quarter based on filing month (approximate)
        if month in [1, 2, 3, 4]:
            quarter = "Q1"
        elif month in [5, 6, 7, 8]:
            quarter = "Q2"
        elif month in [9, 10, 11]:
            quarter = "Q3"
        else:
            quarter = "Q4"

        return f"{quarter} {year}"
    except:
        return "Unknown"


def _categorize_form_type(form_type: str) -> str:
    """Categorize SEC form types for programmatic processing"""
    form_categories = {
        "10-K": "annual_report",
        "10-Q": "quarterly_report",
        "8-K": "current_report",
        "DEF 14A": "proxy_statement",
        "13F-HR": "institutional_holdings",
        "SC 13G": "beneficial_ownership",
        "SC 13D": "beneficial_ownership_activist",
        "4": "insider_trading",
        "S-1": "ipo_registration",
        "424B2": "prospectus_supplement",
        "6-K": "foreign_issuer_report",
    }
    return form_categories.get(form_type, "other")


def _get_filing_urgency(form_type: str) -> str:
    """Get filing urgency level for processing prioritization"""
    urgency_map = {
        "8-K": "high",  # Breaking news, immediate impact
        "4": "high",  # Insider trading, time-sensitive
        "10-Q": "medium",  # Regular quarterly updates
        "10-K": "medium",  # Annual reports, comprehensive but expected
        "DEF 14A": "low",  # Proxy statements, less time-sensitive
        "13F-HR": "low",  # Quarterly holdings reports
        "SC 13G": "medium",  # Ownership changes
        "SC 13D": "high",  # Activist ownership changes
    }
    return urgency_map.get(form_type, "low")


def _get_expected_sections(form_type: str) -> list:
    """Get typical sections expected in different form types for parsing guidance"""
    sections_map = {
        "10-K": [
            "business_description",
            "risk_factors",
            "management_discussion",
            "financial_statements",
            "controls_procedures",
            "legal_proceedings",
        ],
        "10-Q": [
            "financial_statements",
            "management_discussion",
            "legal_proceedings",
            "controls_procedures",
        ],
        "8-K": ["triggering_events", "financial_statements", "exhibits"],
        "DEF 14A": [
            "executive_compensation",
            "board_information",
            "shareholder_proposals",
            "voting_procedures",
        ],
        "13F-HR": ["holdings_table", "summary_information"],
        "SC 13G": ["ownership_information", "purpose_of_transaction"],
        "4": ["transaction_details", "ownership_summary"],
    }
    return sections_map.get(form_type, ["general_content"])


def _calculate_avg_urgency(urgency_levels: list) -> str:
    """Calculate average urgency level for batch processing"""
    if not urgency_levels:
        return "low"

    urgency_weights = {"high": 3, "medium": 2, "low": 1}
    total_weight = sum(urgency_weights.get(level, 1) for level in urgency_levels)
    avg_weight = total_weight / len(urgency_levels)

    if avg_weight >= 2.5:
        return "high"
    elif avg_weight >= 1.5:
        return "medium"
    else:
        return "low"


def _estimate_batch_processing_time(results: list) -> str:
    """Estimate batch processing time based on file sizes and types"""
    if not results:
        return "minimal"

    total_mb = sum(
        f.get("processing", {}).get("hints", {}).get("estimated_size_mb", 0) or 0
        for f in results
    )

    if total_mb < 10:
        return "fast"  # < 1 minute
    elif total_mb < 50:
        return "medium"  # 1-5 minutes
    elif total_mb < 200:
        return "slow"  # 5-15 minutes
    else:
        return "very_slow"  # 15+ minutes


def _check_local_file_status(
    filing: object, engine: FilingSearchEngine
) -> tuple[str, str]:
    """Check if filing is available locally and get file info using the search engine"""
    status, size_str, file_path = engine.get_local_filing_status(filing)

    # Convert status to display format
    if status == "local":
        return "✅ Local", size_str
    elif status == "partial":
        return "⚠️ Partial", size_str
    else:
        return "🌐 Remote", "-"


def _display_filing_results(
    filings: list, ticker: str, form_type: str, limit: int, per_ticker_limit: int | None
):
    """Display filing search results in an enhanced table with more context"""
    from py_sec_edgar.settings import settings

    # Check if we have multiple companies
    unique_companies = {(filing.ticker, filing.company_name) for filing in filings}

    if len(unique_companies) > 1:
        # Multiple companies
        company_list = ", ".join([f"{t} ({c})" for t, c in sorted(unique_companies)])
        console.print(
            f"\n[bold blue]📋 {form_type} Filings for Multiple Companies[/bold blue]"
        )
        console.print(f"[dim]Companies: {company_list}[/dim]")
    else:
        # Single company (original behavior)
        console.print(
            f"\n[bold blue]📋 {form_type} Filings for {ticker.upper()}[/bold blue]"
        )
        console.print(f"[dim]Company: {filings[0].company_name}[/dim]")

    console.print(
        f"[dim]Local Storage: {settings.data_dir / 'downloads' / 'filings'}[/dim]"
    )
    console.print(
        f"[dim]Search Source: {settings.ref_dir / 'company_tickers.json'}[/dim]"
    )
    console.print(
        "[dim]Data Range: 2020-2025 (historical + recent filings via SEC APIs)[/dim]"
    )
    console.print(
        "[dim]ℹ️  Note: Historical data from quarterly IDX files + real-time API searches[/dim]"
    )

    # Show limit information
    if per_ticker_limit is not None:
        console.print(f"[dim]Limit: {per_ticker_limit} filings per company[/dim]")
    else:
        console.print(f"[dim]Limit: {limit} total filings across all companies[/dim]")

    console.print()

    # Create enhanced table with more columns
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("#", style="dim", width=3)
    table.add_column("Ticker", width=8)
    table.add_column("Company", width=20, overflow="ellipsis")
    table.add_column("CIK", width=10, style="dim")
    table.add_column("Filing Date", min_width=12)
    table.add_column("Form Type", width=10)

    # Add quarter column for 10-Q filings
    if form_type == "10-Q":
        table.add_column("Quarter", width=8)

    table.add_column("Status", width=12)
    table.add_column("Size", width=8, justify="right")
    table.add_column("Browse Filing Documents (SEC EDGAR)", overflow="fold")

    # Create search engine instance for status checking
    engine = FilingSearchEngine()

    for i, filing in enumerate(filings, 1):
        status, size = _check_local_file_status(filing, engine)

        row_data = [
            str(i),
            filing.ticker,
            filing.company_name[:18] + "..."
            if len(filing.company_name) > 20
            else filing.company_name,
            filing.cik,
            filing.filing_date,
            filing.form_type,
        ]

        # Add quarter info for 10-Q filings
        if form_type == "10-Q":
            quarter = _get_quarter_info(filing.filing_date, filing.form_type)
            row_data.append(quarter)

        row_data.extend([status, size, filing.document_url])

        table.add_row(*row_data)

    console.print(table)

    # Add helpful note about Document links
    console.print(
        f"[dim]💡 Browse links show all filing documents - click main {form_type} HTML for best readability[/dim]"
    )

    # Enhanced summary with local vs remote count
    engine = FilingSearchEngine()
    local_count = sum(
        1
        for filing in filings
        if _check_local_file_status(filing, engine)[0] == "✅ Local"
    )
    remote_count = len(filings) - local_count

    console.print(f"\n[green]✅ Found {len(filings)} {form_type} filings[/green]")

    # Show limit information and data availability context
    if per_ticker_limit is not None:
        console.print(
            f"[blue]📊 Limited to {per_ticker_limit} filings per company[/blue]"
        )
        if len(filings) < per_ticker_limit:
            console.print(
                f"[dim]💡 Only {len(filings)} filings available (data range: 2020-2025)[/dim]"
            )
    else:
        console.print(f"[blue]📊 Limited to {limit} total filings[/blue]")
        if len(filings) < limit:
            console.print(
                f"[dim]💡 Only {len(filings)} filings available (data range: 2020-2025)[/dim]"
            )

    if local_count > 0:
        console.print(f"[blue]📁 {local_count} available locally[/blue]")
    if remote_count > 0:
        console.print(f"[yellow]🌐 {remote_count} available remotely[/yellow]")

    # Show helpful context for limited results
    if len(filings) < 5 and form_type in ["10-K", "10-Q"]:
        if form_type == "10-K":
            console.print(
                f"[dim]ℹ️  Note: Companies file 10-K annually, so {len(filings)} filings in 2+ years is normal[/dim]"
            )
        elif form_type == "10-Q":
            console.print(
                "[dim]ℹ️  Note: Companies file 10-Q quarterly, expect ~8-10 in 2+ years[/dim]"
            )

    # Suggest getting more historical data if user requested more than available
    requested_limit = per_ticker_limit if per_ticker_limit is not None else limit
    if len(filings) < requested_limit and len(filings) < 10:
        _suggest_historical_data_download(
            console, form_type, len(filings), requested_limit
        )


def _suggest_historical_data_download(
    console: Console, form_type: str, found: int, requested: int
):
    """Suggest appropriate historical data download based on user needs"""

    # Estimate years needed based on form type and requested limit
    if form_type == "10-K":
        years_needed = max(5, requested)  # 10-K is annual
        suggested_years = min(10, years_needed)  # Cap at 10 years
    elif form_type == "10-Q":
        years_needed = max(3, requested // 4)  # 10-Q is quarterly
        suggested_years = min(8, years_needed)  # Cap at 8 years
    else:
        years_needed = max(3, requested // 8)  # Other forms more frequent
        suggested_years = min(5, years_needed)  # Cap at 5 years

    # Show current limitation
    console.print(
        f"[yellow]⚠️  Found only {found} filings (current data: 2020-2025)[/yellow]"
    )

    # Calculate start year for suggestion
    from datetime import datetime

    current_year = datetime.now().year
    start_year = current_year - suggested_years

    # Provide specific download suggestion
    console.print(
        f"[cyan]💡 To get ~{requested} {form_type} filings, download {suggested_years} years of data:[/cyan]"
    )
    console.print(
        f"[white]   py-sec-edgar feeds update-full-index --start-year {start_year}[/white]"
    )

    # Add educational context
    if form_type == "10-K":
        console.print(
            f"[dim]   ({form_type} filed annually → {suggested_years} years = ~{suggested_years} filings per company)[/dim]"
        )
    elif form_type == "10-Q":
        console.print(
            f"[dim]   ({form_type} filed quarterly → {suggested_years} years = ~{suggested_years * 4} filings per company)[/dim]"
        )
    else:
        console.print(
            f"[dim]   ({form_type} frequency varies → {suggested_years} years should provide sufficient history)[/dim]"
        )

    # Alternative: Quick setup for common scenarios
    if requested >= 10:
        console.print(
            "[dim]🚀 Quick setup for extensive analysis: py-sec-edgar feeds update-full-index --last-10-years[/dim]"
        )


async def _analyze_filing(filing_info, filing_content: str, question: str):
    """Analyze filing with AI"""

    if not AI_AVAILABLE:
        console.print(
            "[red]❌ AI analysis not available. Install with: pip install openai[/red]"
        )
        return

    # Check for OpenAI API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        console.print(
            "[red]❌ OpenAI API key required. Set OPENAI_API_KEY environment variable.[/red]"
        )
        return

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Analyzing filing with AI...", total=None)

            response = await analyze_filing_content(
                filing_info=filing_info,
                filing_content=filing_content,
                question=question,
                openai_api_key=api_key,
            )

            progress.update(task, completed=1)

        # Display analysis result
        console.print("\n" + "=" * 80)
        console.print(f"[bold cyan]🤖 AI Analysis: {question}[/bold cyan]")
        console.print("=" * 80)

        # Use markdown rendering for better formatting
        console.print(Markdown(response))
        console.print("\n" + "=" * 80)

    except AIAnalysisError as e:
        console.print(f"[red]❌ AI Analysis Error: {e}[/red]")
    except Exception as e:
        console.print(f"[red]❌ Analysis Failed: {e}[/red]")


async def _start_chat_session(filing_info, filing_content: str):
    """Start interactive chat session"""

    if not AI_AVAILABLE:
        console.print(
            "[red]❌ AI chat not available. Install with: pip install openai[/red]"
        )
        return

    # Check for OpenAI API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        console.print(
            "[red]❌ OpenAI API key required. Set OPENAI_API_KEY environment variable.[/red]"
        )
        return

    try:
        # Initialize AI assistant
        assistant = FilingAIAssistant(openai_api_key=api_key)

        # Start chat session
        welcome = await assistant.start_chat_session(filing_info, filing_content)

        # Display welcome message
        console.print(
            Panel(
                welcome,
                title="[bold cyan]🤖 SEC Filing AI Assistant[/bold cyan]",
                border_style="cyan",
            )
        )

        # Interactive chat loop
        console.print("\n[dim]Type your questions below. Press Ctrl+C to exit.[/dim]\n")

        while True:
            try:
                # Get user input
                user_input = console.input(
                    "[bold green]❓ Your question: [/bold green]"
                ).strip()

                if not user_input:
                    continue

                # Exit commands
                if user_input.lower() in ["exit", "quit", "bye"]:
                    console.print("[cyan]👋 Goodbye![/cyan]")
                    break

                # Get AI response
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=console,
                ) as progress:
                    task = progress.add_task("AI is thinking...", total=None)

                    response = await assistant.chat(user_input)

                    progress.update(task, completed=1)

                # Display response
                console.print("\n[bold cyan]🤖 AI Response:[/bold cyan]")
                console.print(Markdown(response))
                console.print()

            except KeyboardInterrupt:
                console.print("\n[cyan]👋 Chat session ended.[/cyan]")
                break
            except EOFError:
                console.print("\n[cyan]👋 Chat session ended.[/cyan]")
                break
            except Exception as e:
                console.print(f"[red]❌ Chat Error: {e}[/red]")
                continue

    except AIAnalysisError as e:
        console.print(f"[red]❌ AI Error: {e}[/red]")
    except Exception as e:
        console.print(f"[red]❌ Chat initialization failed: {e}[/red]")


@search_group.command()
@click.option("--ticker", required=True, help="Company ticker symbol", metavar="SYMBOL")
def summary(ticker: str):
    """Get a summary of available filing types for a company"""

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(
                f"Getting filing summary for {ticker.upper()}...", total=None
            )

            engine = FilingSearchEngine()
            filing_types = engine.get_filing_types_for_ticker(ticker)

            progress.update(task, completed=1)

        if not filing_types:
            console.print(f"[yellow]No filings found for {ticker.upper()}[/yellow]")
            return

        # Get company info
        cik, company_name = engine.get_cik_for_ticker(ticker)

        console.print(
            f"\n[bold blue]📊 Filing Summary for {ticker.upper()}[/bold blue]"
        )
        console.print(f"[dim]Company: {company_name} (CIK: {cik})[/dim]\n")

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Form Type", width=12)
        table.add_column("Count", width=8, justify="right")
        table.add_column("Description", overflow="fold")

        # Common filing type descriptions
        descriptions = {
            "10-K": "Annual comprehensive business report",
            "10-Q": "Quarterly financial update",
            "8-K": "Material event notification",
            "DEF 14A": "Proxy statement for shareholder meetings",
            "S-1": "Initial public offering registration",
            "S-3": "Securities registration statement",
            "4": "Insider trading report",
            "3": "Initial insider ownership report",
        }

        # Sort by count (descending)
        sorted_types = sorted(filing_types.items(), key=lambda x: x[1], reverse=True)

        for form_type, count in sorted_types:
            description = descriptions.get(form_type, "SEC filing")
            table.add_row(form_type, str(count), description)

        console.print(table)
        console.print(
            f"\n[green]✅ Found {len(filing_types)} different filing types[/green]"
        )

    except FilingSearchError as e:
        console.print(f"[red]❌ Search Error: {e}[/red]")
        raise click.Abort()
    except Exception as e:
        console.print(f"[red]❌ Unexpected Error: {e}[/red]")
        raise click.Abort()


# Add the search group to make it available for import
__all__ = ["search_group"]
