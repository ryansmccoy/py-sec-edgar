# RSS Workflow Commands

The RSS workflow provides powerful commands for processing SEC EDGAR RSS feeds with data persistence and querying capabilities, perfect for real-time monitoring and analysis of the latest filings.

## Overview

The RSS workflow connects to SEC EDGAR's RSS feeds to fetch the most recent filings in real-time. It provides comprehensive data persistence, advanced querying capabilities, and flexible filtering options, making it ideal for monitoring breaking news, compliance tracking, and timely market analysis.

## Basic RSS Feed Processing

### Fetch Recent Filings
```console
# Fetch recent filings from RSS feed with default filtering
$ uv run python -m py_sec_edgar workflows rss

# Fetch specific number of filings without filtering
$ uv run python -m py_sec_edgar workflows rss --count 100 --no-ticker-filter --no-form-filter

# List filings without downloading them
$ uv run python -m py_sec_edgar workflows rss --list-only

# Fetch and process specific companies
$ uv run python -m py_sec_edgar workflows rss --tickers AAPL MSFT GOOGL --count 50

# Fetch specific form types
$ uv run python -m py_sec_edgar workflows rss --forms "8-K" "10-Q" --count 200
```

### Ticker-Based Filtering
```console
# Monitor specific companies for recent activity
$ uv run python -m py_sec_edgar workflows rss --tickers AAPL MSFT GOOGL --count 100

# Monitor portfolio from file
$ uv run python -m py_sec_edgar workflows rss --ticker-file portfolio.csv --count 150

# Monitor all companies (no ticker filter)
$ uv run python -m py_sec_edgar workflows rss --no-ticker-filter --count 200
```

### Form Type Filtering
```console
# Monitor only current events (8-K filings)
$ uv run python -m py_sec_edgar workflows rss --forms "8-K" --count 100

# Monitor insider trading (Form 4)
$ uv run python -m py_sec_edgar workflows rss --forms "4" --count 50

# Monitor quarterly and annual reports
$ uv run python -m py_sec_edgar workflows rss --forms "10-K" "10-Q" --count 75
```

## Data Persistence and Management

### Save RSS Data
```console
# Save RSS data to file for later use
$ uv run python -m py_sec_edgar workflows rss \
    --count 400 \
    --save-to-file rss_data.json \
    --no-ticker-filter \
    --no-form-filter

# Save specific company data
$ uv run python -m py_sec_edgar workflows rss \
    --tickers AAPL MSFT GOOGL \
    --count 200 \
    --save-to-file tech_companies.json

# Save specific form types
$ uv run python -m py_sec_edgar workflows rss \
    --forms "8-K" \
    --count 300 \
    --save-to-file current_events.json \
    --no-ticker-filter
```

### Load and View Saved Data
```console
# Load and view saved RSS data
$ uv run python -m py_sec_edgar workflows rss \
    --load-from-file rss_data.json \
    --list-only

# Pretty print RSS file content
$ uv run python -m py_sec_edgar workflows rss \
    --load-from-file rss_data.json \
    --pretty-print
```

## Advanced Querying and Search

### Query by Company Identifiers
```console
# Query by specific ticker
$ uv run python -m py_sec_edgar workflows rss \
    --load-from-file rss_data.json \
    --query-ticker AAPL \
    --list-only

# Query by specific CIK
$ uv run python -m py_sec_edgar workflows rss \
    --load-from-file rss_data.json \
    --query-cik 0000320193 \
    --list-only

# Show detailed entries with all fields for specific ticker
$ uv run python -m py_sec_edgar workflows rss \
    --load-from-file rss_data.json \
    --query-ticker TSLA \
    --show-entries \
    --list-only
```

### Query by Form Types
```console
# Query by specific form type
$ uv run python -m py_sec_edgar workflows rss \
    --load-from-file rss_data.json \
    --query-form 10-K \
    --list-only

# Find all Form 4 filings
$ uv run python -m py_sec_edgar workflows rss \
    --load-from-file rss_data.json \
    --query-form 4 \
    --show-entries \
    --list-only

# Query current events
$ uv run python -m py_sec_edgar workflows rss \
    --load-from-file rss_data.json \
    --query-form 8-K \
    --list-only
```

### Text Search Capabilities
```console
# Search for text in company names or descriptions
$ uv run python -m py_sec_edgar workflows rss \
    --load-from-file rss_data.json \
    --search-text "GARMIN" \
    --list-only

# Search for energy companies
$ uv run python -m py_sec_edgar workflows rss \
    --load-from-file rss_data.json \
    --search-text "Energy" \
    --show-entries \
    --list-only

# Search for companies with "Corp" in name
$ uv run python -m py_sec_edgar workflows rss \
    --load-from-file rss_data.json \
    --search-text "Corp" \
    --list-only
```

### Combined Query Examples
```console
# Find all Form 4 filings containing "Energy" in company name
$ uv run python -m py_sec_edgar workflows rss \
    --load-from-file rss_data.json \
    --query-form 4 \
    --search-text "Energy" \
    --show-entries \
    --list-only

# Get detailed view of specific company's quarterly reports
$ uv run python -m py_sec_edgar workflows rss \
    --load-from-file rss_data.json \
    --query-ticker AAPL \
    --query-form 10-Q \
    --show-entries \
    --list-only

# Search for acquisition-related 8-K filings
$ uv run python -m py_sec_edgar workflows rss \
    --load-from-file rss_data.json \
    --query-form 8-K \
    --search-text "acquisition" \
    --show-entries \
    --list-only
```

## Processing Control Options

### Download and Extract Control
```console
# Download filings and extract contents
$ uv run python -m py_sec_edgar workflows rss \
    --tickers AAPL \
    --count 50 \
    --extract

# List only without downloading
$ uv run python -m py_sec_edgar workflows rss \
    --tickers AAPL \
    --count 50 \
    --list-only

# Download without extracting
$ uv run python -m py_sec_edgar workflows rss \
    --tickers AAPL \
    --count 50 \
    --no-extract
```

## Complete RSS Workflow Examples

### Comprehensive Data Collection and Analysis
```console
# Step 1: Fetch and save comprehensive dataset
$ uv run python -m py_sec_edgar workflows rss \
    --count 400 \
    --save-to-file large_dataset.json \
    --no-ticker-filter \
    --no-form-filter

# Step 2: Query specific company filings from saved data
$ uv run python -m py_sec_edgar workflows rss \
    --load-from-file large_dataset.json \
    --query-ticker MSFT \
    --show-entries \
    --list-only

# Step 3: Filter by form type from saved data
$ uv run python -m py_sec_edgar workflows rss \
    --load-from-file large_dataset.json \
    --query-form 8-K \
    --list-only

# Step 4: Process specific filings (download and extract)
$ uv run python -m py_sec_edgar workflows rss \
    --load-from-file large_dataset.json \
    --query-ticker AAPL \
    --query-form 10-Q \
    --extract
```

## Practical Workflow Examples

### 📰 Breaking News Monitoring
```console
# Real-time monitoring of current events
$ uv run python -m py_sec_edgar workflows rss \
    --forms "8-K" \
    --count 50 \
    --show-entries \
    --list-only

# Save breaking news for analysis
$ uv run python -m py_sec_edgar workflows rss \
    --forms "8-K" \
    --count 200 \
    --save-to-file breaking_news.json \
    --no-ticker-filter
```

### 🔍 Investment Research Pipeline
```console
# Step 1: Collect recent data for analysis
$ uv run python -m py_sec_edgar workflows rss \
    --count 400 \
    --save-to-file investment_data.json \
    --no-ticker-filter \
    --no-form-filter

# Step 2: Find all Apple (AAPL) filings
$ uv run python -m py_sec_edgar workflows rss \
    --load-from-file investment_data.json \
    --query-ticker AAPL \
    --show-entries \
    --list-only

# Step 3: Get Apple's quarterly reports specifically
$ uv run python -m py_sec_edgar workflows rss \
    --load-from-file investment_data.json \
    --query-ticker AAPL \
    --query-form 10-Q \
    --extract
```

### 🏢 Sector Analysis
```console
# Step 1: Collect comprehensive dataset
$ uv run python -m py_sec_edgar workflows rss \
    --count 400 \
    --save-to-file sector_analysis.json \
    --no-ticker-filter \
    --no-form-filter

# Step 2: Find all energy company insider trading
$ uv run python -m py_sec_edgar workflows rss \
    --load-from-file sector_analysis.json \
    --query-form 4 \
    --search-text "Energy" \
    --show-entries \
    --list-only

# Step 3: Find energy sector current events
$ uv run python -m py_sec_edgar workflows rss \
    --load-from-file sector_analysis.json \
    --query-form 8-K \
    --search-text "Energy" \
    --list-only
```

### 🛡️ Compliance Monitoring System
```console
# Step 1: Collect and save compliance data
$ uv run python -m py_sec_edgar workflows rss \
    --count 400 \
    --save-to-file compliance_data.json \
    --no-ticker-filter \
    --no-form-filter

# Step 2: Monitor insider trading (Form 4)
$ uv run python -m py_sec_edgar workflows rss \
    --load-from-file compliance_data.json \
    --query-form 4 \
    --show-entries \
    --list-only

# Step 3: Track large ownership changes
$ uv run python -m py_sec_edgar workflows rss \
    --load-from-file compliance_data.json \
    --search-text "13G" \
    --show-entries \
    --list-only

# Step 4: Find acquisition-related 8-K filings
$ uv run python -m py_sec_edgar workflows rss \
    --load-from-file compliance_data.json \
    --query-form 8-K \
    --search-text "acquisition" \
    --show-entries \
    --list-only
```

### 💼 Portfolio Monitoring
```console
# Step 1: Create portfolio ticker file
echo -e "AAPL\nMSFT\nGOOGL\nAMZN\nTSLA" > portfolio.csv

# Step 2: Monitor portfolio companies in real-time
$ uv run python -m py_sec_edgar workflows rss \
    --ticker-file portfolio.csv \
    --count 100 \
    --show-entries \
    --list-only

# Step 3: Save portfolio-specific data
$ uv run python -m py_sec_edgar workflows rss \
    --ticker-file portfolio.csv \
    --count 200 \
    --save-to-file portfolio_filings.json

# Step 4: Monitor portfolio current events
$ uv run python -m py_sec_edgar workflows rss \
    --load-from-file portfolio_filings.json \
    --query-form 8-K \
    --show-entries \
    --list-only
```

## RSS Workflow Options Reference

### Core Filtering Options
- `--tickers` - Specify ticker symbols directly (space-separated)
- `--ticker-file` - Path to CSV file containing ticker symbols
- `--no-ticker-filter` - Process all companies (no ticker filtering)
- `--forms` - Specify form types to process (space-separated)
- `--form` - Specify single form type
- `--no-form-filter` - Process all form types

### Data Fetching Options
- `--count` - Number of filings to fetch (default: 100)
- `--download/--no-download` - Control file downloading (default: download)
- `--extract/--no-extract` - Control content extraction (default: no extract)
- `--list-only` - Display filings without downloading

### File Operations
- `--save-to-file` - Save RSS data to JSON file for later analysis
- `--load-from-file` - Load RSS data from JSON file instead of fetching

### Query and Search Options
- `--query-ticker` - Filter by specific ticker symbol when loading from file
- `--query-form` - Filter by specific form type when loading from file
- `--query-cik` - Filter by specific CIK number when loading from file
- `--search-text` - Search for text in company names or descriptions

### Display Options
- `--show-entries` - Show detailed entries with all fields
- `--pretty-print` - Pretty print RSS file content (JSON format)

## RSS Data Structure

When saving RSS data to files, the structure includes:

```json
{
  "metadata": {
    "fetch_timestamp": "2025-01-01T12:00:00Z",
    "total_entries": 400,
    "filters_applied": {
      "forms": ["8-K"],
      "tickers": ["AAPL", "MSFT"]
    }
  },
  "entries": [
    {
      "title": "APPLE INC (0000320193) (Filer)",
      "link": "https://www.sec.gov/Archives/edgar/data/320193/...",
      "published": "2025-01-01T10:30:00Z",
      "summary": "Form 8-K filed by Apple Inc",
      "form_type": "8-K",
      "cik": "0000320193",
      "ticker": "AAPL"
    }
  ]
}
```

## Performance Considerations

**RSS Feed Processing:**
- RSS feeds provide the most recent ~100-400 filings
- Real-time data with minimal latency
- Ideal for current monitoring, not historical analysis
- Lightweight processing compared to full archives

**File-Based Operations:**
- Save large datasets for repeated analysis
- Query operations are fast on saved files
- Combine multiple RSS fetches for comprehensive datasets
- JSON format enables easy integration with other tools

**Integration Patterns:**
- Use RSS for real-time monitoring
- Combine with Full Index for comprehensive historical context
- Use Daily workflow for systematic recent coverage
- Export to databases or analytics platforms

## Integration with Other Workflows

**Combined with Daily Workflow:**
```console
# Real-time RSS monitoring + systematic daily coverage
$ uv run python -m py_sec_edgar workflows rss --forms "8-K" --count 100 --save-to-file current.json
$ uv run python -m py_sec_edgar workflows daily --forms "8-K" --days-back 7 --extract
```

**Combined with Full Index:**
```console
# Historical context + current monitoring
$ uv run python -m py_sec_edgar workflows full-index --tickers AAPL --forms "10-K"
$ uv run python -m py_sec_edgar workflows rss --tickers AAPL --count 50 --show-entries
```

The RSS workflow provides unmatched flexibility for real-time SEC filing monitoring and analysis, making it an essential tool for timely market intelligence and compliance tracking.