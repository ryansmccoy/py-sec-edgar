# py-sec-edgar Examples Runner

This directory contains scripts to run all the examples from the py-sec-edgar documentation. You can run examples individually or all together.

## Files

- `run_examples_simple.py` - Main Python script with interactive menu
- `scripts/run_examples.py` - Full-featured script with categorized examples
- `run_examples.bat` - Windows batch script for easy execution

## Quick Start

### Option 1: Interactive Menu (Recommended)
```bash
# Run the interactive menu
python run_examples_simple.py
```

### Option 2: Windows Batch Script
```cmd
# Double-click or run from command line
run_examples.bat
```

### Option 3: Command Line Options
```bash
# List all available examples
python run_examples_simple.py --list

# Run a specific example
python run_examples_simple.py --run basic_processing

# Run all examples sequentially
python run_examples_simple.py --run-all

# Use different data directory
python run_examples_simple.py --data-dir "D:\my_sec_data" --run basic_processing
```

## Available Examples

### Basic Examples
- `basic_processing` - Basic full index processing
- `specific_tickers` - Process specific ticker symbols (AAPL, MSFT, GOOGL)
- `ticker_file` - Process tickers from CSV file
- `form_10k_only` - Process only 10-K annual reports
- `quarterly_annual` - Process 10-K and 10-Q forms
- `current_events` - Process 8-K current event reports

### Processing Control
- `with_extraction` - Download and extract filing contents
- `no_extraction` - Download files without extraction
- `no_download` - Process only local files (no downloads)

### Research Use Cases
- `tech_sector` - Technology sector analysis
- `investment_analysis` - Investment analysis workflow
- `bulk_processing` - Bulk processing setup

## Example Output

```
🚀 Basic Full Index Processing
💻 Command: uv run python -m py_sec_edgar --data-dir C:\sec_data workflows full-index
────────────────────────────────────────────────────────────
2025-09-02 14:30:00 - py_sec_edgar.main - INFO - py-sec-edgar v1.1.0 - Log level: INFO
2025-09-02 14:30:00 - py_sec_edgar.cli.commands.workflows - INFO - Starting full index workflow...
...
────────────────────────────────────────────────────────────
✅ Completed successfully in 45.67 seconds
```

## Data Directory

By default, examples use `C:\sec_data` as the data directory. You can change this:

```bash
# Use custom data directory
python run_examples_simple.py --data-dir "D:\my_sec_data"
```

## Requirements

- `uv` package manager installed
- py-sec-edgar project set up with `uv sync`
- Example CSV files in the `examples/` directory

## Troubleshooting

### uv command not found
Install uv from: https://docs.astral.sh/uv/getting-started/installation/

### Missing example CSV files
Some examples reference CSV files like:
- `examples/portfolio.csv`
- `examples/sp500_tickers.csv`
- `examples/fortune500.csv`

Create these files or modify the examples to use existing ticker lists.

### Data directory issues
Ensure the data directory exists and has write permissions:
```bash
mkdir C:\sec_data
```

## Advanced Usage

For more detailed control and categorized examples, use the full script:

```bash
# List all categories
python scripts/run_examples.py --list-categories

# Run all examples in a category
python scripts/run_examples.py --run-category basic

# List all examples with descriptions
python scripts/run_examples.py --list
```

## Integration with Tests

These scripts complement the test suite in `tests/workflows/test_full_index_workflow_examples.py`. The tests validate that commands work correctly, while these scripts let you actually run the examples and see the output.