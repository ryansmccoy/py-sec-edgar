#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Simple Example Runner for py-sec-edgar

Quick script to run documentation examples individually or all together.

Usage:
    python run_examples_simple.py                           # Interactive menu
    python run_examples_simple.py --list                    # List examples
    python run_examples_simple.py --run basic_processing    # Run specific example
    python run_examples_simple.py --run-all                 # Run all examples
"""

import argparse
import subprocess
import sys
import time
from typing import Dict, List


def run_command(cmd: List[str], description: str) -> bool:
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


def get_examples(data_dir: str = "C:\\sec_data") -> Dict[str, Dict[str, any]]:
    """Get all examples with their commands covering all workflows from documentation."""
    base = ["uv", "run", "python", "-m", "py_sec_edgar", "--data-dir", data_dir]
    
    return {
        # Full Index Workflow Examples (from FULL_INDEX_WORKFLOW.md)
        "basic_processing": {
            "name": "Basic Full Index Processing",
            "cmd": base + ["workflows", "full-index"],
            "category": "Full Index"
        },
        "specific_tickers": {
            "name": "Specific Tickers (AAPL, MSFT, GOOGL)",
            "cmd": base + ["workflows", "full-index", "--tickers", "AAPL", "MSFT", "GOOGL"],
            "category": "Full Index"
        },
        "quarterly_processing": {
            "name": "Latest Quarter Processing (2025Q3)",
            "cmd": base + ["workflows", "full-index", "--quarter", "2025Q3", "--download", "--extract"],
            "category": "Full Index"
        },
        "tech_giants_annual": {
            "name": "Tech Giants Annual Reports",
            "cmd": base + ["workflows", "full-index", "--tickers", "AAPL", "MSFT", "GOOGL", "AMZN", "META", "--forms", "10-K", "--no-extract"],
            "category": "Full Index"
        },
        "fortune500_analysis": {
            "name": "Fortune 500 Analysis",
            "cmd": base + ["workflows", "full-index", "--ticker-file", "examples/fortune500.csv", "--forms", "10-K", "10-Q", "--no-extract"],
            "category": "Full Index"
        },
        
        # Daily Workflow Examples (from DAILY_WORKFLOW.md)
        "daily_recent_filings": {
            "name": "Yesterday's Filings",
            "cmd": base + ["workflows", "daily", "--days-back", "1"],
            "category": "Daily"
        },
        "daily_portfolio_monitoring": {
            "name": "Weekly Portfolio Monitoring",
            "cmd": base + ["workflows", "daily", "--ticker-file", "examples/portfolio.csv", "--days-back", "7", "--forms", "8-K", "4"],
            "category": "Daily"
        },
        "daily_breaking_news": {
            "name": "Breaking News Monitoring (8-K)",
            "cmd": base + ["workflows", "daily", "--tickers", "AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA", "--forms", "8-K", "--days-back", "2", "--extract"],
            "category": "Daily"
        },
        "daily_insider_trading": {
            "name": "Daily Insider Trading (Form 4)",
            "cmd": base + ["workflows", "daily", "--ticker-file", "examples/portfolio.csv", "--forms", "4", "--days-back", "1", "--extract"],
            "category": "Daily"
        },
        "daily_apple_earnings": {
            "name": "Apple Earnings (Aug 1, 2024)",
            "cmd": base + ["workflows", "daily", "--tickers", "AAPL", "--start-date", "2024-08-01", "--end-date", "2024-08-01", "--forms", "8-K", "--extract"],
            "category": "Daily"
        },
        
        # Monthly Workflow Examples (from MONTHLY_WORKFLOW.md)
        "monthly_xbrl_data": {
            "name": "Last Month XBRL Data",
            "cmd": base + ["workflows", "monthly", "--months-back", "1"],
            "category": "Monthly"
        },
        "monthly_financial_ratio": {
            "name": "Financial Ratio Analysis Data",
            "cmd": base + ["workflows", "monthly", "--tickers", "AAPL", "MSFT", "GOOGL", "AMZN", "--forms", "10-K", "10-Q", "--months-back", "12", "--extract"],
            "category": "Monthly"
        },
        "monthly_sector_comparison": {
            "name": "Tech Sector Financial Comparison",
            "cmd": base + ["workflows", "monthly", "--tickers", "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NFLX", "NVDA", "CRM", "ORCL", "--forms", "10-K", "10-Q", "--months-back", "24", "--extract"],
            "category": "Monthly"
        },
        
        # RSS Workflow Examples (from RSS_WORKFLOW.md)
        "rss_recent_filings": {
            "name": "RSS Recent Filings (Explore)",
            "cmd": base + ["workflows", "rss", "--show-entries", "--count", "20", "--list-only"],
            "category": "RSS"
        },
        "rss_portfolio_monitoring": {
            "name": "RSS Portfolio Monitoring",
            "cmd": base + ["workflows", "rss", "--ticker-file", "examples/portfolio.csv", "--count", "100", "--show-entries", "--list-only"],
            "category": "RSS"
        },
        "rss_breaking_news": {
            "name": "RSS Breaking News (8-K)",
            "cmd": base + ["workflows", "rss", "--forms", "8-K", "--count", "50", "--show-entries", "--list-only"],
            "category": "RSS"
        },
        "rss_save_data": {
            "name": "RSS Save Data for Analysis",
            "cmd": base + ["workflows", "rss", "--count", "400", "--save-to-file", "rss_data.json", "--no-ticker-filter", "--no-form-filter"],
            "category": "RSS"
        },
        
        # README.md Examples
        "readme_first_download": {
            "name": "Your First Filing Download (README)",
            "cmd": base + ["workflows", "full-index", "--tickers", "AAPL", "--forms", "10-K", "--download", "--extract"],
            "category": "README"
        },
        "readme_portfolio_explore": {
            "name": "Portfolio Exploration (README)",
            "cmd": base + ["workflows", "daily", "--tickers", "AAPL", "MSFT", "GOOGL", "--days-back", "7", "--forms", "8-K", "--no-download"],
            "category": "README"
        },
        "readme_investment_research": {
            "name": "Investment Research (README)",
            "cmd": base + ["workflows", "full-index", "--ticker-file", "examples/renewable_energy.csv", "--forms", "10-K", "--no-download"],
            "category": "README"
        },
        
        # Processing Control Examples
        "with_extraction": {
            "name": "With File Extraction",
            "cmd": base + ["workflows", "full-index", "--tickers", "AAPL", "--forms", "10-K", "--extract"],
            "category": "Control"
        },
        "no_extraction": {
            "name": "No File Extraction",
            "cmd": base + ["workflows", "full-index", "--tickers", "AAPL", "--forms", "10-K", "--no-extract"],
            "category": "Control"
        },
        "no_download": {
            "name": "No Download (Local Only)",
            "cmd": base + ["workflows", "full-index", "--tickers", "AAPL", "--forms", "10-K", "--no-download"],
            "category": "Control"
        }
    }


def list_examples(data_dir: str) -> None:
    """List all available examples."""
    examples = get_examples(data_dir)
    
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


def interactive_menu(data_dir: str) -> None:
    """Show interactive menu for selecting examples."""
    examples = get_examples(data_dir)
    
    print("🎯 py-sec-edgar Examples Runner")
    print("=" * 40)
    print("Choose an option:")
    print("1. List all examples")
    print("2. Run specific example")
    print("3. Run all examples")
    print("4. Exit")
    
    while True:
        try:
            choice = input("\nEnter your choice (1-4): ").strip()
            
            if choice == "1":
                list_examples(data_dir)
                continue
                
            elif choice == "2":
                list_examples(data_dir)
                example_key = input("\nEnter example key: ").strip()
                if example_key in examples:
                    run_command(examples[example_key]["cmd"], examples[example_key]["name"])
                else:
                    print(f"❌ Example '{example_key}' not found")
                continue
                
            elif choice == "3":
                run_all_examples(examples)
                break
                
            elif choice == "4":
                print("👋 Goodbye!")
                break
                
            else:
                print("❌ Invalid choice. Please enter 1-4.")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break


def run_all_examples(examples: Dict[str, Dict[str, any]]) -> Dict[str, bool]:
    """Run all examples sequentially."""
    print(f"🚀 Running all {len(examples)} examples")
    print("=" * 60)
    
    results = {}
    
    for i, (key, example) in enumerate(examples.items(), 1):
        print(f"\n[{i}/{len(examples)}] Running: {key}")
        results[key] = run_command(example["cmd"], example["name"])
        
        if i < len(examples):
            print("\n⏳ Waiting 3 seconds before next example...")
            time.sleep(3)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    successful = sum(1 for success in results.values() if success)
    print(f"✅ Successful: {successful}/{len(results)}")
    print(f"❌ Failed: {len(results) - successful}/{len(results)}")
    
    return results


def main():
    parser = argparse.ArgumentParser(description="Run py-sec-edgar examples")
    
    parser.add_argument(
        "--data-dir",
        default="C:\\sec_data",
        help="Data directory for SEC filings (default: C:\\sec_data)"
    )
    
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all available examples"
    )
    
    parser.add_argument(
        "--run",
        type=str,
        help="Run a specific example by key"
    )
    
    parser.add_argument(
        "--run-all",
        action="store_true",
        help="Run all examples sequentially"
    )
    
    args = parser.parse_args()
    
    examples = get_examples(args.data_dir)
    
    if args.list:
        list_examples(args.data_dir)
    elif args.run:
        if args.run in examples:
            success = run_command(examples[args.run]["cmd"], examples[args.run]["name"])
            sys.exit(0 if success else 1)
        else:
            print(f"❌ Example '{args.run}' not found.")
            print("Available examples:")
            for key in examples.keys():
                print(f"  • {key}")
            sys.exit(1)
    elif args.run_all:
        results = run_all_examples(examples)
        failed = sum(1 for success in results.values() if not success)
        sys.exit(0 if failed == 0 else 1)
    else:
        # Interactive mode
        interactive_menu(args.data_dir)


if __name__ == "__main__":
    main()