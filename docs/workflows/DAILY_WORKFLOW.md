# Daily Workflow Commands

The Daily workflow processes recent SEC EDGAR filings from daily index feeds, perfect for staying current with the latest corporate filings and monitoring ongoing developments in real-time.

## Overview

The Daily workflow connects to SEC EDGAR's daily index feeds to systematically process recent filing activity. It provides flexible date range selection and advanced filtering capabilities, making it the ideal tool for current market monitoring, timely analysis, and maintaining up-to-date datasets.

**Key Capabilities:**
- ⚡ **Real-Time Currency**: Access the most recent filing activity (same-day updates)
- 📅 **Flexible Time Ranges**: Process anywhere from 1-90 days of recent activity
- 🎯 **Smart Filtering**: Target specific companies and form types for focused monitoring
- 🔄 **Incremental Processing**: Efficiently update existing datasets with new filings
- 📊 **Market Intelligence**: Perfect for breaking news, earnings updates, and compliance events

## Basic Daily Processing

### Recent Filings (Default)
```console
# Process yesterday's filings with default settings
$ uv run python -m py_sec_edgar workflows daily

# Process last 3 days of filings
$ uv run python -m py_sec_edgar workflows daily --days-back 3

# Process last week of filings
$ uv run python -m py_sec_edgar workflows daily --days-back 7
```

### Ticker-Based Filtering
```console
# Monitor specific companies for recent activity
$ uv run python -m py_sec_edgar workflows daily --tickers AAPL MSFT GOOGL --days-back 5

# Monitor portfolio from file
$ uv run python -m py_sec_edgar workflows daily --ticker-file portfolio.csv --days-back 10

# Monitor all companies (no ticker filter)
$ uv run python -m py_sec_edgar workflows daily --no-ticker-filter --days-back 3
```

### Form Type Filtering
```console
# Monitor only current events (8-K filings)
$ uv run python -m py_sec_edgar workflows daily --forms "8-K" --days-back 7

# Monitor quarterly reports
$ uv run python -m py_sec_edgar workflows daily --forms "10-Q" --days-back 30

# Monitor insider trading
$ uv run python -m py_sec_edgar workflows daily --forms "4" --days-back 5
```

## Processing Control Options

### Download and Extract Control
```console
# Download recent filings but don't extract contents
$ uv run python -m py_sec_edgar workflows daily --tickers AAPL --days-back 5 --no-extract

# Download and extract filing contents
$ uv run python -m py_sec_edgar workflows daily --tickers AAPL --days-back 5 --extract

# Skip downloading if files already exist
$ uv run python -m py_sec_edgar workflows daily --tickers AAPL --days-back 5 --no-download
```

### File Management Options
```console
# Skip existing files (default behavior)
$ uv run python -m py_sec_edgar workflows daily --tickers AAPL --skip-if-exists

# Re-download even if files exist
$ uv run python -m py_sec_edgar workflows daily --tickers AAPL --no-skip-if-exists
```

## Time-Based Monitoring Examples

### Market Opening Monitoring
```console
# Check overnight filings each morning
$ uv run python -m py_sec_edgar workflows daily --days-back 1 --forms "8-K" --extract
```

### Weekly Review
```console
# Weekly portfolio review
$ uv run python -m py_sec_edgar workflows daily \
    --ticker-file portfolio.csv \
    --days-back 7 \
    --forms "8-K" "10-Q" "4" \
    --extract
```

### Monthly Catch-Up
```console
# Monthly comprehensive review
$ uv run python -m py_sec_edgar workflows daily \
    --ticker-file watchlist.csv \
    --days-back 30 \
    --no-form-filter \
    --extract
```

## Practical Workflow Examples

### Breaking News Monitoring
```console
# Monitor major tech companies for breaking news
$ uv run python -m py_sec_edgar workflows daily \
    --tickers AAPL MSFT GOOGL AMZN META TSLA NVDA \
    --forms "8-K" \
    --days-back 2 \
    --extract

# Perfect for capturing: earnings announcements, M&A activity, 
# regulatory updates, management changes
```

### Earnings Season Tracking
```console
# Monitor quarterly earnings during earnings season
$ uv run python -m py_sec_edgar workflows daily \
    --ticker-file sp500_tickers.csv \
    --forms "10-Q" "8-K" \
    --days-back 14 \
    --extract

# Captures both quarterly reports and earnings-related 8-K filings
```

### Insider Trading Surveillance
```console
# Daily insider trading monitoring
$ uv run python -m py_sec_edgar workflows daily \
    --ticker-file insider_watchlist.csv \
    --forms "4" \
    --days-back 1 \
    --extract

# Track executive and director trading activity
```

### Regulatory Compliance Monitoring
```console
# Monitor for compliance-related filings
$ uv run python -m py_sec_edgar workflows daily \
    --ticker-file regulated_companies.csv \
    --forms "8-K" "SC 13G" "SC 13D" \
    --days-back 5 \
    --extract

# Captures regulatory changes, ownership changes, material events
```

### Merger & Acquisition Activity
```console
# Monitor M&A activity across sectors
$ uv run python -m py_sec_edgar workflows daily \
    --no-ticker-filter \
    --forms "8-K" "SC 13D" "DEF 14A" \
    --days-back 3 \
    --extract

# Wide net approach to catch all M&A-related filings
```

## Development and Testing Examples

### Single Company Deep Dive
```console
# Comprehensive recent activity for one company
$ uv run python -m py_sec_edgar workflows daily \
    --tickers AAPL \
    --no-form-filter \
    --days-back 30 \
    --extract
```

### Sector-Specific Monitoring
```console
# Healthcare sector monitoring
$ uv run python -m py_sec_edgar workflows daily \
    --tickers JNJ PFE MRK ABT LLY GILD BMY \
    --forms "8-K" "10-Q" \
    --days-back 7 \
    --extract
```

### High-Frequency Trading Data
```console
# Very recent activity for algorithmic trading
$ uv run python -m py_sec_edgar workflows daily \
    --ticker-file algo_trading_universe.csv \
    --forms "8-K" "4" \
    --days-back 1 \
    --extract
```

## Daily Workflow Options

**Time Range Options:**
- `--days-back` - Number of days back to process (default: 1)

**Filtering Options:**
- `--tickers` - Specify ticker symbols directly (space-separated)
- `--ticker-file` - Path to CSV file containing ticker symbols  
- `--no-ticker-filter` - Process all companies (no ticker filtering)
- `--forms` - Specify form types to process (space-separated)
- `--form` - Specify single form type
- `--no-form-filter` - Process all form types

**Processing Options:**
- `--download/--no-download` - Control file downloading (default: download)
- `--extract/--no-extract` - Control content extraction (default: no extract)
- `--skip-if-exists/--no-skip-if-exists` - Skip existing files (default: skip)

## File Organization

The Daily workflow organizes files by date and company:

```
sec_data/
├── Archives/
│   └── edgar/
│       ├── daily-index/         # Daily index files by date
│       │   └── YYYY/
│       │       └── QTR[1-4]/
│       │           └── YYYYMMDD.idx
│       └── data/                # Extracted filing contents
│           └── [CIK]/           # Company-specific folders
│               └── [Filing]/     # Individual filing folders
```

## Performance Considerations

**Optimal Date Ranges:**
- 1-7 days: Excellent performance, minimal data
- 7-30 days: Good performance, moderate data volume
- 30+ days: Consider using Full Index workflow instead

**Network Efficiency:**
- Daily workflow downloads only recent index files
- Much faster than Full Index for recent data
- Ideal for incremental updates

**Processing Tips:**
- Use specific form filtering for faster processing
- Limit ticker lists for focused monitoring
- Consider skip-if-exists for repeated runs
- Extract only when content analysis is needed

## Integration Patterns

### Combined with Full Index
```console
# Historical baseline + recent updates
$ uv run python -m py_sec_edgar workflows full-index --tickers AAPL --forms "10-K" "10-Q"
$ uv run python -m py_sec_edgar workflows daily --tickers AAPL --days-back 30
```

### Combined with RSS
```console
# Recent filings + real-time feed
$ uv run python -m py_sec_edgar workflows daily --ticker-file portfolio.csv --days-back 7
$ uv run python -m py_sec_edgar workflows rss --ticker-file portfolio.csv --count 100
```

### Automated Daily Routine
```console
# Morning routine script
$ uv run python -m py_sec_edgar workflows daily --ticker-file watchlist.csv --days-back 1 --forms "8-K" --extract
```

## Common Use Cases by Days Back

**1 Day (Yesterday):**
- Breaking news monitoring
- Daily compliance checks
- Overnight filing review

**3-7 Days (Recent Week):**
- Weekly portfolio review
- Market trend analysis
- Recent insider activity

**14-30 Days (Recent Month):**
- Monthly analysis
- Earnings season review
- Comprehensive recent activity

**30+ Days:**
- Consider Full Index workflow for better performance
- Use Daily workflow for incremental updates only

## Form Types for Daily Monitoring

**High-Frequency Forms (check daily):**
- **8-K**: Current events, breaking news
- **4**: Insider trading activity

**Medium-Frequency Forms (check weekly):**
- **10-Q**: Quarterly reports (during earnings season)
- **SC 13G/13D**: Large ownership changes

**Low-Frequency Forms (check monthly):**
- **10-K**: Annual reports (during filing season)
- **DEF 14A**: Proxy statements (during proxy season)

The Daily workflow is perfect for maintaining current awareness of corporate activities and ensuring you never miss important developments in your areas of interest.