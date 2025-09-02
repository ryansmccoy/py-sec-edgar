# Full Index Workflow Commands

The Full Index workflow processes quarterly SEC EDGAR archives, providing comprehensive access to historical filing data. This workflow is the powerhouse for bulk data processing and research requiring complete quarterly datasets.

## Overview

The Full Index workflow downloads and processes complete quarterly filing archives from SEC EDGAR, spanning years of historical data. It provides sophisticated filtering capabilities by ticker symbols and form types, making it the perfect foundation for comprehensive financial analysis, academic research, and compliance monitoring.

**Key Capabilities:**
- 🏗️ **Bulk Processing**: Handle entire quarterly archives (potentially millions of filings)
- 📊 **Historical Depth**: Access complete historical filing datasets
- 🎯 **Precision Filtering**: Target specific companies and form types
- 💾 **Content Extraction**: Extract individual documents and structured data
- 🔄 **Incremental Updates**: Skip existing files for efficient re-runs

## Basic Full Index Processing

### Default Processing
```console
# Process with default settings (uses settings.forms_list and settings.ticker_list_filepath)
$ uv run python -m py_sec_edgar workflows full-index

# Process all filings without any filtering
$ uv run python -m py_sec_edgar workflows full-index --no-ticker-filter --no-form-filter
```

### Ticker-Based Filtering
```console
# Process specific companies
$ uv run python -m py_sec_edgar workflows full-index --tickers AAPL MSFT GOOGL

# Process from ticker file
$ uv run python -m py_sec_edgar workflows full-index --ticker-file my_portfolio.csv

# Combine multiple tickers with command line
$ uv run python -m py_sec_edgar workflows full-index --tickers NVDA TSLA AMD --ticker-file tech_stocks.csv
```

### Form Type Filtering
```console
# Process only 10-K annual reports
$ uv run python -m py_sec_edgar workflows full-index --forms "10-K"

# Process quarterly and annual reports
$ uv run python -m py_sec_edgar workflows full-index --forms "10-K" "10-Q"

# Process insider trading and ownership forms
$ uv run python -m py_sec_edgar workflows full-index --forms "4" "SC 13G" "SC 13D"

# Process current events reports
$ uv run python -m py_sec_edgar workflows full-index --forms "8-K"
```

### Combined Filtering Examples
```console
# Apple and Microsoft annual reports only
$ uv run python -m py_sec_edgar workflows full-index --tickers AAPL MSFT --forms "10-K"

# Tech portfolio quarterly reports
$ uv run python -m py_sec_edgar workflows full-index --ticker-file tech_portfolio.csv --forms "10-Q"

# Energy sector current events
$ uv run python -m py_sec_edgar workflows full-index --ticker-file energy_stocks.csv --forms "8-K"
```

## Processing Control Options

### Download and Extract Control
```console
# Download filings but don't extract contents
$ uv run python -m py_sec_edgar workflows full-index --tickers AAPL --no-extract

# Download and extract filing contents
$ uv run python -m py_sec_edgar workflows full-index --tickers AAPL --extract

# Skip downloading (process only if files already exist)
$ uv run python -m py_sec_edgar workflows full-index --tickers AAPL --no-download
```

## Workflow Configuration Examples

### Research Use Cases

**Academic Research - Fortune 500 Analysis:**
```console
# Step 1: Create Fortune 500 ticker file
# fortune500_tickers.csv contains major company symbols

# Step 2: Process annual reports for comprehensive analysis
$ uv run python -m py_sec_edgar workflows full-index \
    --ticker-file fortune500_tickers.csv \
    --forms "10-K" \
    --extract
```

**Investment Analysis - Sector Focus:**
```console
# Technology sector comprehensive analysis
$ uv run python -m py_sec_edgar workflows full-index \
    --tickers AAPL MSFT GOOGL AMZN META NFLX NVDA \
    --forms "10-K" "10-Q" "8-K" \
    --extract
```

**Compliance Monitoring - Insider Trading:**
```console
# Monitor insider trading for key holdings
$ uv run python -m py_sec_edgar workflows full-index \
    --ticker-file portfolio_holdings.csv \
    --forms "4" "SC 13G" "SC 13D" \
    --extract
```

### Development and Testing

**Small-Scale Testing:**
```console
# Test with single company
$ uv run python -m py_sec_edgar workflows full-index \
    --tickers AAPL \
    --forms "10-K" \
    --no-extract
```

**Performance Testing:**
```console
# Test with multiple large companies
$ uv run python -m py_sec_edgar workflows full-index \
    --tickers AAPL MSFT GOOGL AMZN \
    --forms "10-K" "10-Q" \
    --extract
```

## Practical Workflow Examples

### Quarterly Earnings Analysis
```console
# Download all 10-Q forms for major tech companies
$ uv run python -m py_sec_edgar workflows full-index \
    --tickers AAPL MSFT GOOGL AMZN TSLA META \
    --forms "10-Q" \
    --extract

# This creates a comprehensive quarterly earnings dataset
```

### Annual Report Research
```console
# Comprehensive annual report analysis for energy sector
$ uv run python -m py_sec_edgar workflows full-index \
    --tickers XOM CVX COP EOG SLB \
    --forms "10-K" \
    --extract

# Perfect for year-over-year analysis and industry comparisons
```

### Current Events Monitoring
```console
# Monitor all 8-K filings for pharmaceutical companies
$ uv run python -m py_sec_edgar workflows full-index \
    --tickers JNJ PFE MRK ABT LLY \
    --forms "8-K" \
    --extract

# Captures merger announcements, clinical trial results, regulatory updates
```

### Comprehensive Portfolio Analysis
```console
# Full analysis of diversified portfolio
$ uv run python -m py_sec_edgar workflows full-index \
    --ticker-file my_portfolio.csv \
    --forms "10-K" "10-Q" "8-K" "DEF 14A" \
    --extract

# Downloads all major filing types for complete due diligence
```

## Full Index Workflow Options

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

## File Organization

The Full Index workflow organizes downloaded files in a structured directory hierarchy:

```
sec_data/
├── Archives/
│   └── edgar/
│       ├── full-index/          # Downloaded quarterly archives
│       └── data/                # Extracted filing contents
│           └── [CIK]/           # Company-specific folders
│               └── [Filing]/     # Individual filing folders
```

## Performance Considerations

**Large-Scale Processing:**
- Full Index processes complete quarterly archives (can be several GB)
- Consider disk space requirements for extracted content
- Network bandwidth requirements for initial downloads
- Processing time scales with number of companies and forms

**Optimization Tips:**
- Use specific form filtering to reduce processing time
- Limit ticker lists to companies of interest
- Consider running without extraction for initial data collection
- Use `--no-download` for reprocessing existing data

## Integration with Other Workflows

The Full Index workflow complements other py-sec-edgar workflows:

**Combined with Daily Workflow:**
```console
# Quarterly archive processing + recent updates
$ uv run python -m py_sec_edgar workflows full-index --tickers AAPL --forms "10-K"
$ uv run python -m py_sec_edgar workflows daily --tickers AAPL --days-back 30
```

**Combined with RSS Workflow:**
```console
# Historical data + real-time monitoring
$ uv run python -m py_sec_edgar workflows full-index --ticker-file portfolio.csv --forms "8-K"
$ uv run python -m py_sec_edgar workflows rss --ticker-file portfolio.csv --forms "8-K"
```

## Common Form Types for Full Index Processing

- **10-K**: Annual reports (comprehensive company overview)
- **10-Q**: Quarterly reports (quarterly financial updates)
- **8-K**: Current events (material corporate events)
- **DEF 14A**: Proxy statements (shareholder meeting information)
- **4**: Insider trading reports (executive transactions)
- **SC 13G**: Beneficial ownership (large shareholder positions)
- **SC 13D**: Beneficial ownership with control intent
- **13F-HR**: Institutional investment manager holdings

Each form type serves different analysis purposes and can be combined for comprehensive company research.