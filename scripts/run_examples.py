#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Example Runner Script for py-sec-edgar

This script runs all the examples from the README and workflow documentation.
You can run individual examples or all examples sequentially.

Usage:
    python scripts/run_examples.py --list                    # List all available examples
    python scripts/run_examples.py --run basic_processing    # Run a specific example
    python scripts/run_examples.py --run-all                 # Run all examples
    python scripts/run_examples.py --run-category basic      # Run all examples in a category
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional


class ExampleRunner:
    """Runner for py-sec-edgar documentation examples."""

    def __init__(self, data_dir: str = "C:\\sec_data", log_level: str = "INFO"):
        self.data_dir = data_dir
        self.log_level = log_level
        self.base_cmd = ["uv", "run", "python", "-m", "py_sec_edgar"]
        
        # Define all examples organized by category
        self.examples = {
            # Daily Workflow Examples (from DAILY_WORKFLOW.md)
            "daily": {
                "daily_recent_filings": {
                    "name": "Yesterday's Filings",
                    "cmd": ["workflows", "daily", "--days-back", "1"],
                    "description": "Process yesterday's filings with default settings"
                },
                "daily_last_week": {
                    "name": "Last Week of Filings",
                    "cmd": ["workflows", "daily", "--days-back", "7"],
                    "description": "Process last week of recent filings"
                },
                "daily_portfolio_monitoring": {
                    "name": "Weekly Portfolio Monitoring",
                    "cmd": ["workflows", "daily", "--ticker-file", "examples/portfolio.csv", "--days-back", "7", "--forms", "8-K", "4"],
                    "description": "Monitor portfolio companies for recent activity"
                },
                "daily_breaking_news": {
                    "name": "Breaking News Monitoring (8-K)",
                    "cmd": ["workflows", "daily", "--tickers", "AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA", "--forms", "8-K", "--days-back", "2", "--extract"],
                    "description": "Monitor major tech companies for breaking news"
                },
                "daily_insider_trading": {
                    "name": "Daily Insider Trading Surveillance",
                    "cmd": ["workflows", "daily", "--ticker-file", "examples/portfolio.csv", "--forms", "4", "--days-back", "1", "--extract"],
                    "description": "Track executive and director trading activity"
                },
                "daily_apple_earnings": {
                    "name": "Apple Earnings (Aug 1, 2024)",
                    "cmd": ["workflows", "daily", "--tickers", "AAPL", "--start-date", "2024-08-01", "--end-date", "2024-08-01", "--forms", "8-K", "--extract"],
                    "description": "Monitor Apple's specific earnings announcement"
                },
                "daily_compliance_monitoring": {
                    "name": "Regulatory Compliance Monitoring",
                    "cmd": ["workflows", "daily", "--ticker-file", "examples/portfolio.csv", "--forms", "8-K", "SC 13G", "SC 13D", "--days-back", "5", "--extract"],
                    "description": "Monitor for compliance-related filings"
                },
                "daily_ma_activity": {
                    "name": "Merger & Acquisition Activity",
                    "cmd": ["workflows", "daily", "--no-ticker-filter", "--forms", "8-K", "SC 13D", "DEF 14A", "--days-back", "3", "--extract"],
                    "description": "Wide net approach to catch all M&A-related filings"
                }
            },
            
            # Monthly Workflow Examples (from MONTHLY_WORKFLOW.md)
            "monthly": {
                "monthly_recent_xbrl": {
                    "name": "Recent Monthly XBRL Data",
                    "cmd": ["workflows", "monthly", "--months-back", "1"],
                    "description": "Process last month's XBRL data with default settings"
                },
                "monthly_quarterly_data": {
                    "name": "Last 6 Months XBRL Data",
                    "cmd": ["workflows", "monthly", "--months-back", "6"],
                    "description": "Process last 6 months of XBRL data"
                },
                "monthly_financial_ratio": {
                    "name": "Financial Ratio Analysis Data",
                    "cmd": ["workflows", "monthly", "--tickers", "AAPL", "MSFT", "GOOGL", "AMZN", "--forms", "10-K", "10-Q", "--months-back", "12", "--extract"],
                    "description": "Download structured financial data for ratio analysis"
                },
                "monthly_sector_comparison": {
                    "name": "Technology Sector Financial Comparison",
                    "cmd": ["workflows", "monthly", "--tickers", "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NFLX", "NVDA", "CRM", "ORCL", "--forms", "10-K", "10-Q", "--months-back", "24", "--extract"],
                    "description": "Technology sector financial comparison"
                },
                "monthly_time_series": {
                    "name": "Multi-Year Financial Trend Analysis",
                    "cmd": ["workflows", "monthly", "--tickers", "AAPL", "--forms", "10-K", "10-Q", "--months-back", "36", "--extract"],
                    "description": "XBRL structure enables automated trend analysis"
                },
                "monthly_portfolio_analysis": {
                    "name": "Portfolio Performance Analysis",
                    "cmd": ["workflows", "monthly", "--ticker-file", "examples/portfolio.csv", "--forms", "10-K", "10-Q", "--months-back", "24", "--extract"],
                    "description": "Structured data for portfolio optimization models"
                },
                "monthly_research_dataset": {
                    "name": "Large-Scale Financial Modeling Dataset",
                    "cmd": ["workflows", "monthly", "--ticker-file", "examples/sp500_tickers.csv", "--forms", "10-K", "--months-back", "60", "--extract"],
                    "description": "5 years of standardized annual financial data"
                },
                "monthly_banking_sector": {
                    "name": "Banking Sector Financial Analysis",
                    "cmd": ["workflows", "monthly", "--tickers", "JPM", "BAC", "WFC", "C", "GS", "MS", "--forms", "10-K", "10-Q", "--months-back", "36", "--extract"],
                    "description": "Standardized banking metrics for industry comparison"
                }
            },
            
            # RSS Workflow Examples (from RSS_WORKFLOW.md)
            "rss": {
                "rss_recent_filings": {
                    "name": "Fetch Recent RSS Filings",
                    "cmd": ["workflows", "rss", "--show-entries", "--count", "20", "--list-only"],
                    "description": "Explore latest filings in real-time (safe exploration)"
                },
                "rss_portfolio_monitoring": {
                    "name": "RSS Portfolio Monitoring",
                    "cmd": ["workflows", "rss", "--ticker-file", "examples/portfolio.csv", "--count", "100", "--show-entries", "--list-only"],
                    "description": "Monitor portfolio companies in real-time"
                },
                "rss_breaking_news": {
                    "name": "RSS Breaking News (8-K)",
                    "cmd": ["workflows", "rss", "--forms", "8-K", "--count", "50", "--show-entries", "--list-only"],
                    "description": "Real-time monitoring of current events"
                },
                "rss_insider_trading": {
                    "name": "RSS Insider Trading (Form 4)",
                    "cmd": ["workflows", "rss", "--forms", "4", "--count", "50", "--show-entries", "--list-only"],
                    "description": "Monitor insider trading (Form 4)"
                },
                "rss_save_comprehensive": {
                    "name": "Save Comprehensive RSS Dataset",
                    "cmd": ["workflows", "rss", "--count", "400", "--save-to-file", "large_dataset.json", "--no-ticker-filter", "--no-form-filter"],
                    "description": "Fetch and save comprehensive dataset"
                },
                "rss_query_apple": {
                    "name": "Query Apple Filings from Saved Data",
                    "cmd": ["workflows", "rss", "--load-from-file", "large_dataset.json", "--query-ticker", "AAPL", "--show-entries", "--list-only"],
                    "description": "Query specific company filings from saved data"
                },
                "rss_text_search": {
                    "name": "RSS Text Search for Energy Companies",
                    "cmd": ["workflows", "rss", "--load-from-file", "large_dataset.json", "--search-text", "Energy", "--show-entries", "--list-only"],
                    "description": "Search for energy companies in RSS data"
                },
                "rss_combined_query": {
                    "name": "RSS Combined Query (8-K + Acquisition)",
                    "cmd": ["workflows", "rss", "--load-from-file", "large_dataset.json", "--query-form", "8-K", "--search-text", "acquisition", "--show-entries", "--list-only"],
                    "description": "Search for acquisition-related 8-K filings"
                }
            },
            
            # README Examples
            "readme": {
                "readme_first_download": {
                    "name": "Your First Filing Download (README)",
                    "cmd": ["workflows", "full-index", "--tickers", "AAPL", "--forms", "10-K", "--download", "--extract"],
                    "description": "Download Apple's latest 10-K annual report (README example)"
                },
                "readme_quarterly_processing": {
                    "name": "Process Latest Quarterly Data (README)",
                    "cmd": ["workflows", "full-index", "--quarter", "2025Q3", "--download", "--extract"],
                    "description": "Process the latest quarterly data (2025Q3) from README"
                },
                "readme_portfolio_explore": {
                    "name": "Portfolio Exploration (README)",
                    "cmd": ["workflows", "daily", "--tickers", "AAPL", "MSFT", "GOOGL", "--days-back", "7", "--forms", "8-K", "--no-download"],
                    "description": "Monitor portfolio for recent filings (README example)"
                },
                "readme_apple_earnings": {
                    "name": "Apple Earnings Aug 1 2024 (README)",
                    "cmd": ["workflows", "daily", "--tickers", "AAPL", "--start-date", "2024-08-01", "--end-date", "2024-08-01", "--forms", "8-K", "--download", "--extract"],
                    "description": "Monitor Apple's earnings announcement from August 1, 2024"
                },
                "readme_investment_research": {
                    "name": "Investment Research Workflow (README)",
                    "cmd": ["workflows", "full-index", "--ticker-file", "examples/renewable_energy.csv", "--forms", "10-K", "--no-download"],
                    "description": "Renewable energy sector analysis from README"
                },
                "readme_academic_pipeline": {
                    "name": "Academic Research Pipeline (README)",
                    "cmd": ["workflows", "full-index", "--ticker-file", "examples/sp500_tickers.csv", "--forms", "DEF 14A", "--no-download"],
                    "description": "Academic research proxy statements from README"
                },
                "readme_compliance_monitoring": {
                    "name": "Compliance Monitoring System (README)",
                    "cmd": ["workflows", "daily", "--ticker-file", "examples/portfolio.csv", "--days-back", "14", "--forms", "4", "--download", "--extract"],
                    "description": "Insider trading monitoring from README"
                }
            },
            # Basic Full Index Processing Examples
            "basic": {
                "basic_processing": {
                    "name": "Basic Full Index Processing",
                    "cmd": ["workflows", "full-index"],
                    "description": "Process all filings with default settings"
                },
                "quarterly_processing": {
                    "name": "Latest Quarter Processing (2025Q3)",
                    "cmd": ["workflows", "full-index", "--quarter", "2025Q3", "--download", "--extract"],
                    "description": "Process the latest quarterly data (2025Q3)"
                },
                "specific_tickers": {
                    "name": "Specific Tickers Processing",
                    "cmd": ["workflows", "full-index", "--tickers", "AAPL", "MSFT", "GOOGL"],
                    "description": "Process filings for specific ticker symbols"
                },
                "ticker_file": {
                    "name": "Ticker File Processing",
                    "cmd": ["workflows", "full-index", "--ticker-file", "examples/portfolio.csv"],
                    "description": "Process filings from a ticker CSV file"
                },
                "combined_tickers": {
                    "name": "Combined Tickers",
                    "cmd": ["workflows", "full-index", "--tickers", "NVDA", "TSLA", "AMD", "--ticker-file", "examples/portfolio.csv"],
                    "description": "Combine individual tickers with ticker file"
                },
                "form_10k_only": {
                    "name": "10-K Forms Only",
                    "cmd": ["workflows", "full-index", "--tickers", "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "--forms", "10-K"],
                    "description": "Process only 10-K annual reports"
                },
                "quarterly_annual": {
                    "name": "Quarterly and Annual Reports",
                    "cmd": ["workflows", "full-index", "--tickers", "AAPL", "MSFT", "--forms", "10-K", "10-Q"],
                    "description": "Process both 10-K and 10-Q forms"
                },
                "insider_forms": {
                    "name": "Insider and Ownership Forms",
                    "cmd": ["workflows", "full-index", "--tickers", "AAPL", "MSFT", "--forms", "4", "SC 13G", "SC 13D"],
                    "description": "Process insider trading and ownership forms"
                },
                "current_events": {
                    "name": "Current Events (8-K)",
                    "cmd": ["workflows", "full-index", "--tickers", "AAPL", "MSFT", "--forms", "8-K"],
                    "description": "Process current event reports"
                }
            },
            
            # Processing Control Examples
            "control": {
                "with_extraction": {
                    "name": "With File Extraction",
                    "cmd": ["workflows", "full-index", "--tickers", "AAPL", "--forms", "10-K", "--extract"],
                    "description": "Download and extract filing contents"
                },
                "no_extraction": {
                    "name": "No File Extraction",
                    "cmd": ["workflows", "full-index", "--tickers", "AAPL", "--forms", "10-K", "--no-extract"],
                    "description": "Download files without extraction"
                },
                "no_download": {
                    "name": "No Download (Local Only)",
                    "cmd": ["workflows", "full-index", "--tickers", "AAPL", "--forms", "10-K", "--no-download"],
                    "description": "Process only local files, skip downloads"
                }
            },
            
            # Research Use Cases
            "research": {
                "fortune500_setup": {
                    "name": "Fortune 500 Setup",
                    "cmd": ["workflows", "full-index", "--ticker-file", "examples/fortune500.csv", "--no-extract"],
                    "description": "Set up Fortune 500 companies analysis"
                },
                "tech_sector": {
                    "name": "Technology Sector Analysis",
                    "cmd": ["workflows", "full-index", "--tickers", "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NFLX", "NVDA", "--no-extract"],
                    "description": "Technology sector comprehensive analysis"
                },
                "academic_research": {
                    "name": "Academic Research Pipeline",
                    "cmd": ["workflows", "full-index", "--ticker-file", "examples/sp500_tickers.csv", "--forms", "10-K", "--no-extract"],
                    "description": "Academic research data collection"
                },
                "investment_analysis": {
                    "name": "Investment Analysis Workflow",
                    "cmd": ["workflows", "full-index", "--ticker-file", "examples/portfolio.csv", "--forms", "10-K", "10-Q", "--no-extract"],
                    "description": "Investment analysis workflow setup"
                },
                "compliance_monitoring": {
                    "name": "Compliance Monitoring",
                    "cmd": ["workflows", "full-index", "--ticker-file", "examples/portfolio.csv", "--forms", "4", "SC 13G", "SC 13D", "--no-extract"],
                    "description": "Compliance monitoring setup"
                },
                "sector_comparison": {
                    "name": "Sector Comparison Analysis",
                    "cmd": ["workflows", "full-index", "--ticker-file", "examples/renewable_energy.csv", "--forms", "10-K", "10-Q", "--no-extract"],
                    "description": "Sector comparison analysis"
                }
            },
            
            # Historical Analysis
            "historical": {
                "multi_year_trends": {
                    "name": "Multi-Year Trend Analysis",
                    "cmd": ["workflows", "full-index", "--tickers", "AAPL", "--forms", "10-K", "--no-extract"],
                    "description": "Historical trend analysis setup"
                },
                "performance_comparison": {
                    "name": "Historical Performance Comparison",
                    "cmd": ["workflows", "full-index", "--ticker-file", "examples/sp500_tickers.csv", "--forms", "10-K", "10-Q", "--no-extract"],
                    "description": "Performance comparison over time"
                },
                "risk_assessment": {
                    "name": "Long-term Risk Assessment",
                    "cmd": ["workflows", "full-index", "--ticker-file", "examples/fortune500.csv", "--forms", "10-K", "--no-extract"],
                    "description": "Long-term risk assessment analysis"
                },
                "economic_cycles": {
                    "name": "Economic Cycle Analysis",
                    "cmd": ["workflows", "full-index", "--ticker-file", "examples/sp500_tickers.csv", "--forms", "10-K", "8-K", "--no-extract"],
                    "description": "Economic cycle impact analysis"
                }
            },
            
            # Bulk Processing
            "bulk": {
                "large_scale_collection": {
                    "name": "Large-Scale Data Collection",
                    "cmd": ["workflows", "full-index", "--ticker-file", "examples/sp500_tickers.csv", "--forms", "10-K", "--no-extract"],
                    "description": "Large-scale data collection setup"
                },
                "performance_optimization": {
                    "name": "Performance Optimization",
                    "cmd": ["workflows", "full-index", "--ticker-file", "examples/fortune500.csv", "--no-extract"],
                    "description": "Performance optimization example"
                },
                "memory_management": {
                    "name": "Memory Management",
                    "cmd": ["workflows", "full-index", "--ticker-file", "examples/sp500_tickers.csv", "--forms", "10-K", "10-Q", "--no-extract"],
                    "description": "Memory management with large datasets"
                }
            }
        }

    def list_examples(self) -> None:
        """List all available examples."""
        print("Available examples by category:\n")
        
        for category, examples in self.examples.items():
            print(f"📁 {category.upper()} EXAMPLES:")
            for key, example in examples.items():
                print(f"  • {key}: {example['name']}")
                print(f"    {example['description']}")
            print()

    def list_categories(self) -> None:
        """List all available categories."""
        print("Available categories:")
        for category in self.examples.keys():
            example_count = len(self.examples[category])
            print(f"  • {category}: {example_count} examples")

    def run_example(self, example_key: str, category: Optional[str] = None) -> bool:
        """Run a specific example."""
        # Find the example in categories
        example = None
        found_category = None
        
        if category:
            if category in self.examples and example_key in self.examples[category]:
                example = self.examples[category][example_key]
                found_category = category
        else:
            # Search all categories
            for cat, examples in self.examples.items():
                if example_key in examples:
                    example = examples[example_key]
                    found_category = cat
                    break
        
        if not example:
            print(f"❌ Example '{example_key}' not found.")
            return False
        
        print(f"🚀 Running example: {example['name']}")
        print(f"📂 Category: {found_category}")
        print(f"📝 Description: {example['description']}")
        
        # Build full command
        cmd = (self.base_cmd + 
               ["--data-dir", self.data_dir] + 
               example["cmd"])
        
        print(f"💻 Command: {' '.join(cmd)}")
        print("─" * 60)
        
        # Run the command
        try:
            start_time = time.time()
            result = subprocess.run(cmd, capture_output=False, text=True)
            end_time = time.time()
            
            duration = end_time - start_time
            print("─" * 60)
            
            if result.returncode == 0:
                print(f"✅ Example completed successfully in {duration:.2f} seconds")
                return True
            else:
                print(f"❌ Example failed with exit code {result.returncode}")
                return False
                
        except KeyboardInterrupt:
            print("\n⏹️ Example interrupted by user")
            return False
        except Exception as e:
            print(f"❌ Error running example: {e}")
            return False

    def run_category(self, category: str) -> Dict[str, bool]:
        """Run all examples in a category."""
        if category not in self.examples:
            print(f"❌ Category '{category}' not found.")
            return {}
        
        examples = self.examples[category]
        results = {}
        
        print(f"🚀 Running all examples in category: {category.upper()}")
        print(f"📊 Total examples: {len(examples)}")
        print("=" * 60)
        
        for i, (key, example) in enumerate(examples.items(), 1):
            print(f"\n[{i}/{len(examples)}] Running: {key}")
            results[key] = self.run_example(key, category)
            
            if i < len(examples):
                print("\n⏳ Waiting 2 seconds before next example...")
                time.sleep(2)
        
        # Summary
        print("\n" + "=" * 60)
        print(f"📊 CATEGORY SUMMARY: {category.upper()}")
        successful = sum(1 for success in results.values() if success)
        print(f"✅ Successful: {successful}/{len(results)}")
        print(f"❌ Failed: {len(results) - successful}/{len(results)}")
        
        return results

    def run_all(self) -> Dict[str, Dict[str, bool]]:
        """Run all examples."""
        print("🚀 Running ALL examples from documentation")
        total_examples = sum(len(examples) for examples in self.examples.values())
        print(f"📊 Total examples: {total_examples}")
        print("=" * 60)
        
        all_results = {}
        
        for category in self.examples.keys():
            print(f"\n{'='*20} STARTING CATEGORY: {category.upper()} {'='*20}")
            all_results[category] = self.run_category(category)
            print(f"{'='*20} FINISHED CATEGORY: {category.upper()} {'='*20}")
            
            # Wait between categories
            print("\n⏳ Waiting 5 seconds before next category...")
            time.sleep(5)
        
        # Overall summary
        print("\n" + "=" * 60)
        print("📊 OVERALL SUMMARY")
        total_successful = 0
        total_run = 0
        
        for category, results in all_results.items():
            successful = sum(1 for success in results.values() if success)
            total_successful += successful
            total_run += len(results)
            print(f"{category}: {successful}/{len(results)} successful")
        
        print(f"\n🎯 TOTAL: {total_successful}/{total_run} examples successful")
        success_rate = (total_successful / total_run * 100) if total_run > 0 else 0
        print(f"📈 Success rate: {success_rate:.1f}%")
        
        return all_results


def main():
    parser = argparse.ArgumentParser(
        description="Run py-sec-edgar documentation examples",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--data-dir",
        default="C:\\sec_data",
        help="Data directory for SEC filings (default: C:\\sec_data)"
    )
    
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)"
    )
    
    group = parser.add_mutually_exclusive_group(required=True)
    
    group.add_argument(
        "--list",
        action="store_true",
        help="List all available examples"
    )
    
    group.add_argument(
        "--list-categories",
        action="store_true",
        help="List all available categories"
    )
    
    group.add_argument(
        "--run",
        type=str,
        help="Run a specific example by key"
    )
    
    group.add_argument(
        "--run-category",
        type=str,
        help="Run all examples in a specific category"
    )
    
    group.add_argument(
        "--run-all",
        action="store_true",
        help="Run all examples sequentially"
    )
    
    parser.add_argument(
        "--category",
        type=str,
        help="Specify category when running a specific example"
    )
    
    args = parser.parse_args()
    
    runner = ExampleRunner(data_dir=args.data_dir, log_level=args.log_level)
    
    if args.list:
        runner.list_examples()
    elif args.list_categories:
        runner.list_categories()
    elif args.run:
        success = runner.run_example(args.run, args.category)
        sys.exit(0 if success else 1)
    elif args.run_category:
        results = runner.run_category(args.run_category)
        failed = sum(1 for success in results.values() if not success)
        sys.exit(0 if failed == 0 else 1)
    elif args.run_all:
        all_results = runner.run_all()
        total_failed = sum(
            sum(1 for success in results.values() if not success)
            for results in all_results.values()
        )
        sys.exit(0 if total_failed == 0 else 1)


if __name__ == "__main__":
    main()