#!/usr/bin/env python

"""
Simple Example Runner for py-sec-edgar

Enhanced script to run documentation examples individually or all together.
Now includes Smart Router functionality testing and numbered menu selection.

Usage:
    python run_examples_simple.py                           # Interactive menu with numbered selection
    python run_examples_simple.py --list                    # List examples with keys
    python run_examples_simple.py --list-numbered           # List examples with numbers
    def run_smart_router_tests(logger: logging.Logger = None, data_dir: str = "C:\\sec_data") -> None:
    \"\"\"Run Smart Router specific tests with a submenu.\"\"\"
    print(\"\\n🧠 Smart Router Test Suite\")
    print(\"=\" * 40)
    prin        elif args.smart_router_tests:
            logger.info("Starting Smart Router test suite")
            print("\n🧠 Smart Router Test Suite")
            print("=" * 40)
            run_smart_router_tests(logger, args.data_dir)hoose a Smart Router test:\")
    print(\"1. Run comprehensive test suite\")
    print(\"2. Test recent data routing (RSS)\")
    print(\"3. Test monthly data routing\")
    print(\"4. Test historical data routing\")
    print(\"5. Test multi-ticker search\")
    print(\"6. Test different form types\")
    print(\"7. Run all Smart Router tests\")
    print(\"8. Back to main menu\")

    examples = get_examples(data_dir)ples_simple.py --run basic_processing    # Run specific example by key
    python run_examples_simple.py --run-number 15          # Run specific example by number
    python run_examples_simple.py --run-all                 # Run all examples
    python run_examples_simple.py --smart-router-tests      # Run Smart Router test suite
"""

import argparse
import logging
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path


def setup_logging() -> tuple[logging.Logger, Path]:
    """
    Set up logging to output to the logs folder with timestamped filename.

    Returns:
        tuple: (logger instance, log file path)
    """
    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    # Create timestamped log file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = logs_dir / f"examples_runner_{timestamp}.log"

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.FileHandler(log_file, mode="w", encoding="utf-8"),
            logging.StreamHandler(sys.stdout),  # Also log to console
        ],
    )

    logger = logging.getLogger(__name__)
    logger.info(f"Examples Runner started - Log file: {log_file}")

    return logger, log_file


def run_command(
    cmd: list[str], description: str, logger: logging.Logger = None
) -> bool:
    """Run a command and return success status."""
    print(f"\n🚀 {description}")
    print(f"💻 Command: {' '.join(cmd)}")
    print("─" * 60)

    try:
        start_time = time.time()
        result = subprocess.run(cmd, text=True)
        end_time = time.time()

        duration = end_time - start_time
        print("─" * 60)

        if result.returncode == 0:
            print(f"✅ Completed successfully in {duration:.2f} seconds")
            return True
        else:
            print(f"❌ Failed with exit code {result.returncode}")
            return False

    except KeyboardInterrupt:
        print("\n⏹️ Interrupted by user")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def get_examples(data_dir: str = "C:\\sec_data") -> dict[str, dict[str, any]]:
    """Get all examples with their commands covering all workflows from documentation."""
    base = ["uv", "run", "python", "-m", "py_sec_edgar", "--data-dir", data_dir]

    return {
        # Full Index Workflow Examples (from FULL_INDEX_WORKFLOW.md)
        "basic_processing": {
            "name": "Basic Full Index Processing",
            "cmd": base + ["workflows", "full-index"],
            "category": "Full Index",
        },
        "specific_tickers": {
            "name": "Specific Tickers (AAPL, MSFT, GOOGL)",
            "cmd": base
            + [
                "workflows",
                "full-index",
                "--tickers",
                "AAPL",
                "--tickers",
                "MSFT",
                "--tickers",
                "GOOGL",
            ],
            "category": "Full Index",
        },
        "quarterly_processing": {
            "name": "Latest Quarter Processing",
            "cmd": base + ["workflows", "full-index", "--download", "--extract"],
            "category": "Full Index",
        },
        "tech_giants_annual": {
            "name": "Tech Giants Annual Reports",
            "cmd": base
            + [
                "workflows",
                "full-index",
                "--tickers",
                "AAPL",
                "--tickers",
                "MSFT",
                "--tickers",
                "GOOGL",
                "--tickers",
                "AMZN",
                "--tickers",
                "META",
                "--forms",
                "10-K",
                "--no-extract",
            ],
            "category": "Full Index",
        },
        "fortune500_analysis": {
            "name": "Fortune 500 Analysis",
            "cmd": base
            + [
                "workflows",
                "full-index",
                "--ticker-file",
                "examples/fortune500.csv",
                "--forms",
                "10-K",
                "--forms",
                "10-Q",
                "--no-extract",
            ],
            "category": "Full Index",
        },
        # Daily Workflow Examples (from DAILY_WORKFLOW.md)
        "daily_recent_filings": {
            "name": "Yesterday's Filings",
            "cmd": base + ["workflows", "daily", "--days-back", "1"],
            "category": "Daily",
        },
        "daily_portfolio_monitoring": {
            "name": "Weekly Portfolio Monitoring",
            "cmd": base
            + [
                "workflows",
                "daily",
                "--ticker-file",
                "examples/portfolio.csv",
                "--days-back",
                "7",
                "--forms",
                "8-K",
                "--forms",
                "4",
            ],
            "category": "Daily",
        },
        "daily_breaking_news": {
            "name": "Breaking News Monitoring (8-K)",
            "cmd": base
            + [
                "workflows",
                "daily",
                "--tickers",
                "AAPL",
                "--tickers",
                "MSFT",
                "--tickers",
                "GOOGL",
                "--tickers",
                "AMZN",
                "--tickers",
                "META",
                "--tickers",
                "TSLA",
                "--tickers",
                "NVDA",
                "--forms",
                "8-K",
                "--days-back",
                "2",
                "--extract",
            ],
            "category": "Daily",
        },
        "daily_insider_trading": {
            "name": "Daily Insider Trading (Form 4)",
            "cmd": base
            + [
                "workflows",
                "daily",
                "--ticker-file",
                "examples/portfolio.csv",
                "--forms",
                "4",
                "--days-back",
                "1",
                "--extract",
            ],
            "category": "Daily",
        },
        "daily_apple_earnings": {
            "name": "Apple Earnings (Aug 1, 2024)",
            "cmd": base
            + [
                "workflows",
                "daily",
                "--tickers",
                "AAPL",
                "--start-date",
                "2024-08-01",
                "--end-date",
                "2024-08-01",
                "--forms",
                "8-K",
                "--extract",
            ],
            "category": "Daily",
        },
        # Monthly Workflow Examples (from MONTHLY_WORKFLOW.md)
        "monthly_xbrl_data": {
            "name": "Last Month XBRL Data",
            "cmd": base + ["workflows", "monthly", "--months-back", "1"],
            "category": "Monthly",
        },
        "monthly_financial_ratio": {
            "name": "Financial Ratio Analysis Data",
            "cmd": base
            + [
                "workflows",
                "monthly",
                "--tickers",
                "AAPL",
                "--tickers",
                "MSFT",
                "--tickers",
                "GOOGL",
                "--tickers",
                "AMZN",
                "--forms",
                "10-K",
                "--forms",
                "10-Q",
                "--months-back",
                "12",
                "--extract",
            ],
            "category": "Monthly",
        },
        "monthly_sector_comparison": {
            "name": "Tech Sector Financial Comparison",
            "cmd": base
            + [
                "workflows",
                "monthly",
                "--tickers",
                "AAPL",
                "--tickers",
                "MSFT",
                "--tickers",
                "GOOGL",
                "--tickers",
                "AMZN",
                "--tickers",
                "META",
                "--tickers",
                "NFLX",
                "--tickers",
                "NVDA",
                "--tickers",
                "CRM",
                "--tickers",
                "ORCL",
                "--forms",
                "10-K",
                "--forms",
                "10-Q",
                "--months-back",
                "24",
                "--extract",
            ],
            "category": "Monthly",
        },
        # RSS Workflow Examples (from RSS_WORKFLOW.md)
        "rss_recent_filings": {
            "name": "RSS Recent Filings (Explore)",
            "cmd": base + ["workflows", "rss", "--count", "20", "--list-only"],
            "category": "RSS",
        },
        "rss_portfolio_monitoring": {
            "name": "RSS Portfolio Monitoring",
            "cmd": base
            + [
                "workflows",
                "rss",
                "--ticker-file",
                "examples/portfolio.csv",
                "--count",
                "100",
                "--list-only",
            ],
            "category": "RSS",
        },
        "rss_breaking_news": {
            "name": "RSS Breaking News (8-K)",
            "cmd": base
            + ["workflows", "rss", "--forms", "8-K", "--count", "50", "--list-only"],
            "category": "RSS",
        },
        "rss_save_data": {
            "name": "RSS Recent Filings (No Filtering)",
            "cmd": base
            + [
                "workflows",
                "rss",
                "--count",
                "100",
                "--no-ticker-filter",
                "--no-form-filter",
                "--list-only",
            ],
            "category": "RSS",
        },
        # Search Engine Examples (AI-Powered Filing Search & Analysis)
        "search_basic_apple": {
            "name": "Basic Apple Filing Search (10-K)",
            "cmd": base
            + ["search", "filings", "--ticker", "AAPL", "--form-type", "10-K"],
            "category": "Search",
        },
        "search_basic_apple_quarterly": {
            "name": "Apple Quarterly Reports (10-Q)",
            "cmd": base
            + [
                "search",
                "filings",
                "--ticker",
                "AAPL",
                "--form-type",
                "10-Q",
                "--limit",
                "5",
            ],
            "category": "Search",
        },
        "search_multi_ticker": {
            "name": "Multi-Company Search (AAPL, MSFT, GOOGL)",
            "cmd": base
            + [
                "search",
                "filings",
                "--ticker",
                "AAPL,MSFT,GOOGL",
                "--form-type",
                "10-K",
                "--limit",
                "6",
            ],
            "category": "Search",
        },
        "search_tech_giants_quarterly": {
            "name": "Tech Giants Quarterly Reports",
            "cmd": base
            + [
                "search",
                "filings",
                "--ticker",
                "AAPL,MSFT,GOOGL,AMZN,META",
                "--form-type",
                "10-Q",
                "--per-ticker-limit",
                "2",
            ],
            "category": "Search",
        },
        "search_with_download": {
            "name": "Search & Download Apple Filing",
            "cmd": base
            + [
                "search",
                "filings",
                "--ticker",
                "AAPL",
                "--form-type",
                "10-K",
                "--download",
            ],
            "category": "Search",
        },
        "search_batch_download": {
            "name": "Search & Download All Results",
            "cmd": base
            + [
                "search",
                "filings",
                "--ticker",
                "AAPL,MSFT",
                "--form-type",
                "10-Q",
                "--limit",
                "4",
                "--download-all",
            ],
            "category": "Search",
        },
        "search_json_output": {
            "name": "JSON Output for Programmatic Use",
            "cmd": base
            + [
                "search",
                "filings",
                "--ticker",
                "AAPL",
                "--form-type",
                "10-K",
                "--limit",
                "3",
                "--json",
            ],
            "category": "Search",
        },
        "search_multi_json": {
            "name": "Multi-Company JSON Analysis Data",
            "cmd": base
            + [
                "search",
                "filings",
                "--ticker",
                "AAPL,MSFT,GOOGL",
                "--form-type",
                "10-Q",
                "--limit",
                "9",
                "--json",
            ],
            "category": "Search",
        },
        "search_summary_apple": {
            "name": "Apple Filing Types Summary",
            "cmd": base + ["search", "summary", "--ticker", "AAPL"],
            "category": "Search",
        },
        "search_summary_microsoft": {
            "name": "Microsoft Filing Types Summary",
            "cmd": base + ["search", "summary", "--ticker", "MSFT"],
            "category": "Search",
        },
        # README.md Examples
        "readme_first_download": {
            "name": "Your First Filing Download (README)",
            "cmd": base
            + [
                "workflows",
                "full-index",
                "--tickers",
                "AAPL",
                "--forms",
                "10-K",
                "--download",
                "--extract",
            ],
            "category": "README",
        },
        "readme_portfolio_explore": {
            "name": "Portfolio Exploration (README)",
            "cmd": base
            + [
                "workflows",
                "daily",
                "--tickers",
                "AAPL",
                "--tickers",
                "MSFT",
                "--tickers",
                "GOOGL",
                "--days-back",
                "7",
                "--forms",
                "8-K",
                "--no-download",
            ],
            "category": "README",
        },
        "readme_investment_research": {
            "name": "Investment Research (README)",
            "cmd": base
            + [
                "workflows",
                "full-index",
                "--ticker-file",
                "examples/renewable_energy.csv",
                "--forms",
                "10-K",
                "--no-download",
            ],
            "category": "README",
        },
        # Processing Control Examples
        "with_extraction": {
            "name": "With File Extraction",
            "cmd": base
            + [
                "workflows",
                "full-index",
                "--tickers",
                "AAPL",
                "--forms",
                "10-K",
                "--extract",
            ],
            "category": "Control",
        },
        "no_extraction": {
            "name": "No File Extraction",
            "cmd": base
            + [
                "workflows",
                "full-index",
                "--tickers",
                "AAPL",
                "--forms",
                "10-K",
                "--no-extract",
            ],
            "category": "Control",
        },
        "no_download": {
            "name": "No Download (Local Only)",
            "cmd": base
            + [
                "workflows",
                "full-index",
                "--tickers",
                "AAPL",
                "--forms",
                "10-K",
                "--no-download",
            ],
            "category": "Control",
        },
        # CLI Help and Utility Commands
        "main_help": {
            "name": "Main CLI Help",
            "cmd": base + ["--help"],
            "category": "CLI Help",
        },
        "workflows_help": {
            "name": "Workflows Command Help",
            "cmd": base + ["workflows", "--help"],
            "category": "CLI Help",
        },
        "search_help": {
            "name": "Search Command Help",
            "cmd": base + ["search", "--help"],
            "category": "CLI Help",
        },
        "feeds_help": {
            "name": "Feeds Command Help",
            "cmd": base + ["feeds", "--help"],
            "category": "CLI Help",
        },
        "process_help": {
            "name": "Process Command Help",
            "cmd": base + ["process", "--help"],
            "category": "CLI Help",
        },
        "filters_help": {
            "name": "Filters Command Help",
            "cmd": base + ["filters", "--help"],
            "category": "CLI Help",
        },
        "utils_help": {
            "name": "Utils Command Help",
            "cmd": base + ["utils", "--help"],
            "category": "CLI Help",
        },
        # Core Workflow Help Commands
        "workflow_full_index_help": {
            "name": "Full Index Workflow Help",
            "cmd": base + ["workflows", "full-index", "--help"],
            "category": "CLI Help",
        },
        "workflow_daily_help": {
            "name": "Daily Workflow Help",
            "cmd": base + ["workflows", "daily", "--help"],
            "category": "CLI Help",
        },
        "workflow_monthly_help": {
            "name": "Monthly Workflow Help",
            "cmd": base + ["workflows", "monthly", "--help"],
            "category": "CLI Help",
        },
        "workflow_rss_help": {
            "name": "RSS Workflow Help",
            "cmd": base + ["workflows", "rss", "--help"],
            "category": "CLI Help",
        },
        # Search Command Help
        "search_filings_help": {
            "name": "Search Filings Help",
            "cmd": base + ["search", "filings", "--help"],
            "category": "CLI Help",
        },
        "search_summary_help": {
            "name": "Search Summary Help",
            "cmd": base + ["search", "summary", "--help"],
            "category": "CLI Help",
        },
        # Smart Router Test Examples - NEW!
        "smart_router_basic_test": {
            "name": "Smart Router Basic Functionality Test",
            "cmd": ["uv", "run", "python", "test_smart_router.py"],
            "category": "Smart Router",
        },
        "smart_router_demo_recent": {
            "name": "Smart Router Demo - Recent Data (RSS)",
            "cmd": [
                "uv",
                "run",
                "python",
                "-c",
                "from src.py_sec_edgar.core.smart_router import smart_search; filings, route = smart_search('AAPL', limit=3); print(f'Route: {route.feed_type.value}, Found: {len(filings)} filings')",
            ],
            "category": "Smart Router",
        },
        "smart_router_demo_monthly": {
            "name": "Smart Router Demo - Monthly Data (2025 Q2)",
            "cmd": [
                "uv",
                "run",
                "python",
                "-c",
                "from src.py_sec_edgar.core.smart_router import smart_search; filings, route = smart_search('AAPL', start_date='2025-04-01', end_date='2025-06-30', limit=3); print(f'Route: {route.feed_type.value}, Found: {len(filings)} filings')",
            ],
            "category": "Smart Router",
        },
        "smart_router_demo_historical": {
            "name": "Smart Router Demo - Historical Data (2024)",
            "cmd": [
                "uv",
                "run",
                "python",
                "-c",
                "from src.py_sec_edgar.core.smart_router import smart_search; filings, route = smart_search('AAPL', start_date='2024-01-01', end_date='2024-12-31', limit=5); print(f'Route: {route.feed_type.value}, Found: {len(filings)} filings')",
            ],
            "category": "Smart Router",
        },
        "smart_router_multi_ticker": {
            "name": "Smart Router Demo - Multi-Ticker Search",
            "cmd": [
                "uv",
                "run",
                "python",
                "-c",
                "from src.py_sec_edgar.core.smart_router import smart_search; filings, route = smart_search(['AAPL', 'MSFT', 'GOOGL'], limit=9); print(f'Route: {route.feed_type.value}, Found: {len(filings)} filings for 3 companies')",
            ],
            "category": "Smart Router",
        },
        "smart_router_form_types": {
            "name": "Smart Router Demo - Different Form Types",
            "cmd": [
                "uv",
                "run",
                "python",
                "-c",
                "from src.py_sec_edgar.core.smart_router import smart_search; filings, route = smart_search('AAPL', form_type='8-K', limit=5); print(f'Route: {route.feed_type.value}, Found: {len(filings)} 8-K filings')",
            ],
            "category": "Smart Router",
        },
    }


def list_examples(data_dir: str, numbered: bool = False) -> dict[int, str]:
    """List all available examples with optional numbering.

    Args:
        data_dir: Data directory for examples
        numbered: If True, show numbered list and return mapping

    Returns:
        Dict mapping numbers to example keys (if numbered=True)
    """
    examples = get_examples(data_dir)

    if numbered:
        print("\n🎯 Available Examples (enter number to run):\n")
        number_to_key = {}
        current_number = 1

        categories = {}
        for key, example in examples.items():
            category = example["category"]
            if category not in categories:
                categories[category] = []
            categories[category].append((key, example["name"]))

        for category, items in categories.items():
            print(f"📁 {category.upper()}:")
            for key, name in items:
                print(f"  {current_number:2d}. {name}")
                number_to_key[current_number] = key
                current_number += 1
            print()

        print(f"Total: {len(examples)} examples available")
        return number_to_key
    else:
        print("Available examples:\n")

        categories = {}
        for key, example in examples.items():
            category = example["category"]
            if category not in categories:
                categories[category] = []
            categories[category].append((key, example["name"]))

        for category, items in categories.items():
            print(f"📁 {category.upper()}:")
            for key, name in items:
                print(f"  • {key}: {name}")
            print()

        return {}


def interactive_menu(data_dir: str, logger: logging.Logger = None) -> None:
    """Show interactive menu for selecting examples."""
    examples = get_examples(data_dir)

    if logger:
        logger.info(f"Starting interactive menu with data directory: {data_dir}")

    print("\n🎯 py-sec-edgar Examples Runner")
    print("=" * 50)
    print("Choose an option:")
    print("1. List all examples (with keys)")
    print("2. Run specific example by number")
    print("3. Run specific example by key")
    print("4. Run all examples")
    print("5. Test Smart Router functionality")
    print("6. Exit")

    while True:
        try:
            choice = input("\nEnter your choice (1-6): ").strip()

            if choice == "1":
                list_examples(data_dir, numbered=False)
                continue

            elif choice == "2":
                # Numbered selection
                number_to_key = list_examples(data_dir, numbered=True)
                try:
                    selection = input(
                        "\nEnter example number (or 'back' to return): "
                    ).strip()
                    if selection.lower() == "back":
                        continue

                    example_number = int(selection)
                    if example_number in number_to_key:
                        example_key = number_to_key[example_number]
                        example = examples[example_key]

                        print(f"\n🎯 Selected: {example['name']}")
                        print(f"📁 Category: {example['category']}")
                        print(f"💻 Command: {' '.join(example['cmd'])}")

                        confirm = input("\nRun this example? (y/N): ").strip().lower()
                        if confirm in ["y", "yes"]:
                            if logger:
                                logger.info(
                                    f"User selected example #{example_number}: {example_key}"
                                )
                            run_command(example["cmd"], example["name"], logger)
                        else:
                            print("❌ Cancelled")
                    else:
                        print(f"❌ Invalid number. Please enter 1-{len(number_to_key)}")
                except ValueError:
                    print("❌ Invalid input. Please enter a number.")
                continue

            elif choice == "3":
                # Key-based selection (original method)
                list_examples(data_dir, numbered=False)
                example_key = input("\nEnter example key: ").strip()
                if example_key in examples:
                    if logger:
                        logger.info(f"User selected example: {example_key}")
                    run_command(
                        examples[example_key]["cmd"],
                        examples[example_key]["name"],
                        logger,
                    )
                else:
                    error_msg = f"❌ Example '{example_key}' not found"
                    print(error_msg)
                    if logger:
                        logger.warning(f"Invalid example key selected: {example_key}")
                continue

            elif choice == "4":
                confirm = (
                    input(
                        f"\nRun all {len(examples)} examples? This may take a while. (y/N): "
                    )
                    .strip()
                    .lower()
                )
                if confirm in ["y", "yes"]:
                    run_all_examples(examples, logger)
                else:
                    print("❌ Cancelled")
                continue

            elif choice == "5":
                # Smart Router testing submenu
                run_smart_router_tests(logger, data_dir)
                continue

            elif choice == "6":
                print("👋 Goodbye!")
                break

            else:
                print("❌ Invalid choice. Please enter 1-6.")

        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break


def run_smart_router_tests(logger: logging.Logger = None) -> None:
    """Run Smart Router specific tests with a submenu."""
    print("\n🧠 Smart Router Test Suite")
    print("=" * 40)
    print("Choose a Smart Router test:")
    print("1. Run comprehensive test suite")
    print("2. Test recent data routing (RSS)")
    print("3. Test monthly data routing")
    print("4. Test historical data routing")
    print("5. Test multi-ticker search")
    print("6. Test different form types")
    print("7. Run all Smart Router tests")
    print("8. Back to main menu")

    examples = get_examples()
    smart_router_examples = {
        "1": "smart_router_basic_test",
        "2": "smart_router_demo_recent",
        "3": "smart_router_demo_monthly",
        "4": "smart_router_demo_historical",
        "5": "smart_router_multi_ticker",
        "6": "smart_router_form_types",
    }

    while True:
        try:
            choice = input("\nEnter your choice (1-8): ").strip()

            if choice in smart_router_examples:
                example_key = smart_router_examples[choice]
                example = examples[example_key]
                print(f"\n🚀 Running: {example['name']}")
                if logger:
                    logger.info(f"Smart Router test selected: {example_key}")
                run_command(example["cmd"], example["name"], logger)

            elif choice == "7":
                # Run all Smart Router tests
                print("\n🚀 Running all Smart Router tests...")
                for i, example_key in enumerate(smart_router_examples.values(), 1):
                    example = examples[example_key]
                    print(f"\n[{i}/6] {example['name']}")
                    success = run_command(example["cmd"], example["name"], logger)
                    if not success:
                        print("⚠️ Test failed, continuing with next test...")
                    if i < 6:
                        print("⏳ Waiting 2 seconds...")
                        time.sleep(2)
                print("\n✅ All Smart Router tests completed!")

            elif choice == "8":
                break

            else:
                print("❌ Invalid choice. Please enter 1-8.")

        except KeyboardInterrupt:
            print("\n↩️ Returning to main menu...")
            break


def run_all_examples(
    examples: dict[str, dict[str, any]], logger: logging.Logger = None
) -> dict[str, bool]:
    """Run all examples sequentially."""
    start_msg = f"🚀 Running all {len(examples)} examples"
    separator = "=" * 60

    print(start_msg)
    print(separator)

    if logger:
        logger.info(f"Starting batch run of {len(examples)} examples")

    results = {}

    for i, (key, example) in enumerate(examples.items(), 1):
        progress_msg = f"\n[{i}/{len(examples)}] Running: {key}"
        print(progress_msg)
        if logger:
            logger.info(
                f"Progress: {i}/{len(examples)} - Running example '{key}': {example['name']}"
            )
        results[key] = run_command(example["cmd"], example["name"], logger)

        if i < len(examples):
            print("\n⏳ Waiting 3 seconds before next example...")
            time.sleep(3)

    # Summary
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    successful = sum(1 for success in results.values() if success)
    failed = len(results) - successful

    success_msg = f"✅ Successful: {successful}/{len(results)}"
    failed_msg = f"❌ Failed: {failed}/{len(results)}"

    print(success_msg)
    print(failed_msg)

    if logger:
        logger.info(f"Batch run completed - Success: {successful}, Failed: {failed}")

        # Log details of failed examples
        failed_examples = [key for key, success in results.items() if not success]
        if failed_examples:
            logger.warning(f"Failed examples: {', '.join(failed_examples)}")

        # Log summary statistics
        success_rate = (successful / len(results)) * 100 if results else 0
        logger.info(f"Overall success rate: {success_rate:.1f}%")

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Run py-sec-edgar examples with enhanced Smart Router testing"
    )

    parser.add_argument(
        "--data-dir",
        default="C:\\sec_data",
        help="Data directory for SEC filings (default: C:\\sec_data)",
    )

    parser.add_argument(
        "--list", action="store_true", help="List all available examples with keys"
    )

    parser.add_argument(
        "--list-numbered",
        action="store_true",
        help="List all available examples with numbers",
    )

    parser.add_argument("--run", type=str, help="Run a specific example by key")

    parser.add_argument(
        "--run-number",
        type=int,
        help="Run a specific example by number (use --list-numbered to see numbers)",
    )

    parser.add_argument(
        "--run-all", action="store_true", help="Run all examples sequentially"
    )

    parser.add_argument(
        "--smart-router-tests", action="store_true", help="Run Smart Router test suite"
    )

    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Set logging level (default: INFO)",
    )

    args = parser.parse_args()

    # Set up logging
    logger, log_file = setup_logging()

    # Update logging level if specified
    if args.log_level:
        logging.getLogger().setLevel(getattr(logging, args.log_level))
        logger.info(f"Logging level set to: {args.log_level}")

    logger.info(f"Examples Runner started with arguments: {vars(args)}")

    examples = get_examples(args.data_dir)

    try:
        if args.list:
            logger.info("Listing all available examples (with keys)")
            list_examples(args.data_dir, numbered=False)

        elif args.list_numbered:
            logger.info("Listing all available examples (with numbers)")
            number_to_key = list_examples(args.data_dir, numbered=True)
            print("\\n💡 Use --run-number <NUMBER> to run a specific example")

        elif args.run:
            if args.run in examples:
                logger.info(f"Running single example by key: {args.run}")
                success = run_command(
                    examples[args.run]["cmd"], examples[args.run]["name"], logger
                )
                logger.info(f"Single example run completed - Success: {success}")
                sys.exit(0 if success else 1)
            else:
                error_msg = f"❌ Example '{args.run}' not found."
                print(error_msg)
                print("Available examples:")
                for key in examples.keys():
                    print(f"  • {key}")
                logger.error(f"Invalid example key: {args.run}")
                logger.info(f"Available examples: {list(examples.keys())}")
                sys.exit(1)

        elif args.run_number:
            logger.info(f"Running single example by number: {args.run_number}")
            number_to_key = list_examples(args.data_dir, numbered=True)
            if args.run_number in number_to_key:
                example_key = number_to_key[args.run_number]
                example = examples[example_key]
                print(f"\\n🎯 Running #{args.run_number}: {example['name']}")
                success = run_command(example["cmd"], example["name"], logger)
                logger.info(f"Numbered example run completed - Success: {success}")
                sys.exit(0 if success else 1)
            else:
                error_msg = f"❌ Example number '{args.run_number}' not found."
                print(error_msg)
                print(f"Valid numbers: 1-{len(number_to_key)}")
                logger.error(f"Invalid example number: {args.run_number}")
                sys.exit(1)

        elif args.run_all:
            logger.info("Starting run-all mode")
            results = run_all_examples(examples, logger)
            failed = sum(1 for success in results.values() if not success)
            logger.info(f"Run-all completed - Exit code: {1 if failed > 0 else 0}")
            sys.exit(0 if failed == 0 else 1)

        elif args.smart_router_tests:
            logger.info("Starting Smart Router test suite")
            print("\\n🧠 Smart Router Test Suite")
            print("=" * 40)
            run_smart_router_tests(logger)

        else:
            # Interactive mode
            logger.info("Starting enhanced interactive mode")
            interactive_menu(args.data_dir, logger)

    except KeyboardInterrupt:
        logger.warning("Examples Runner interrupted by user")
        print("\n👋 Examples Runner interrupted!")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Unexpected error in Examples Runner: {e}")
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
    finally:
        logger.info(f"Examples Runner session completed - Log saved to: {log_file}")
        print(f"\n📝 Session log saved to: {log_file}")


if __name__ == "__main__":
    main()
