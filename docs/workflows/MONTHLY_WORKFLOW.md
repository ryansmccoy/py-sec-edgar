# Monthly Workflow Commands

The Monthly workflow processes SEC EDGAR's monthly XBRL data archives, providing access to structured financial data in machine-readable XBRL format. This workflow is specialized for quantitative financial analysis and automated data processing.

## Overview

The Monthly workflow downloads and processes monthly XBRL (eXtensible Business Reporting Language) archives from SEC EDGAR. XBRL provides structured, standardized financial data that's perfect for quantitative analysis, financial modeling, automated data processing, and building financial datasets for machine learning.

**Key Capabilities:**
- 🔢 **Structured Data**: Access machine-readable XBRL financial data  
- 📊 **Standardized Format**: Consistent data structure across all companies
- 🎯 **Quantitative Analysis**: Perfect for financial modeling and analytics
- 📈 **Time Series Data**: Build comprehensive historical financial datasets
- 🤖 **ML-Ready**: Ideal for machine learning and algorithmic analysis

## Basic Monthly Processing

### Recent Monthly Data
```console
# Process last month's XBRL data with default settings
$ uv run python -m py_sec_edgar workflows monthly

# Process last 3 months of XBRL data
$ uv run python -m py_sec_edgar workflows monthly --months-back 3

# Process last 6 months of XBRL data
$ uv run python -m py_sec_edgar workflows monthly --months-back 6
```

### Ticker-Based Filtering
```console
# Process XBRL data for specific companies
$ uv run python -m py_sec_edgar workflows monthly --tickers AAPL MSFT GOOGL --months-back 6

# Process portfolio from file
$ uv run python -m py_sec_edgar workflows monthly --ticker-file portfolio.csv --months-back 12

# Process all companies (no ticker filter)
$ uv run python -m py_sec_edgar workflows monthly --no-ticker-filter --months-back 3
```

### Form Type Filtering
```console
# Process only 10-K XBRL data (annual reports)
$ uv run python -m py_sec_edgar workflows monthly --forms "10-K" --months-back 12

# Process quarterly and annual XBRL reports
$ uv run python -m py_sec_edgar workflows monthly --forms "10-K" "10-Q" --months-back 6

# Process all XBRL form types
$ uv run python -m py_sec_edgar workflows monthly --no-form-filter --months-back 3
```

## Processing Control Options

### Download and Extract Control
```console
# Download XBRL files but don't extract contents
$ uv run python -m py_sec_edgar workflows monthly --tickers AAPL --months-back 6 --no-extract

# Download and extract XBRL contents for analysis
$ uv run python -m py_sec_edgar workflows monthly --tickers AAPL --months-back 6 --extract

# Skip downloading if files already exist
$ uv run python -m py_sec_edgar workflows monthly --tickers AAPL --months-back 6 --no-download
```

## Quantitative Analysis Examples

### Financial Ratio Analysis
```console
# Download structured financial data for ratio analysis
$ uv run python -m py_sec_edgar workflows monthly \
    --tickers AAPL MSFT GOOGL AMZN \
    --forms "10-K" "10-Q" \
    --months-back 12 \
    --extract

# Perfect for calculating: P/E ratios, debt-to-equity, ROE, etc.
```

### Sector Comparison Analysis
```console
# Technology sector financial comparison
$ uv run python -m py_sec_edgar workflows monthly \
    --tickers AAPL MSFT GOOGL AMZN META NFLX NVDA CRM ORCL \
    --forms "10-K" "10-Q" \
    --months-back 24 \
    --extract

# Standardized XBRL data enables direct financial comparisons
```

### Time Series Financial Analysis
```console
# Multi-year financial trend analysis
$ uv run python -m py_sec_edgar workflows monthly \
    --tickers AAPL \
    --forms "10-K" "10-Q" \
    --months-back 36 \
    --extract

# XBRL structure enables automated trend analysis
```

### Portfolio Performance Analysis
```console
# Comprehensive portfolio financial analysis
$ uv run python -m py_sec_edgar workflows monthly \
    --ticker-file diversified_portfolio.csv \
    --forms "10-K" "10-Q" \
    --months-back 24 \
    --extract

# Structured data for portfolio optimization models
```

## Research and Academic Use Cases

### Financial Modeling Research
```console
# Large-scale financial modeling dataset
$ uv run python -m py_sec_edgar workflows monthly \
    --ticker-file sp500_tickers.csv \
    --forms "10-K" \
    --months-back 60 \
    --extract

# 5 years of standardized annual financial data
```

### Industry Analysis
```console
# Banking sector financial analysis
$ uv run python -m py_sec_edgar workflows monthly \
    --tickers JPM BAC WFC C GS MS \
    --forms "10-K" "10-Q" \
    --months-back 36 \
    --extract

# Standardized banking metrics for industry comparison
```

### Academic Research Dataset
```console
# Comprehensive research dataset
$ uv run python -m py_sec_edgar workflows monthly \
    --ticker-file research_universe.csv \
    --no-form-filter \
    --months-back 120 \
    --extract

# 10 years of structured financial data for academic research
```

## Investment Analysis Examples

### Value Investing Screening
```console
# Value stock screening data
$ uv run python -m py_sec_edgar workflows monthly \
    --ticker-file value_candidates.csv \
    --forms "10-K" "10-Q" \
    --months-back 24 \
    --extract

# XBRL data perfect for automated value metrics calculation
```

### Growth Analysis
```console
# Growth company financial analysis
$ uv run python -m py_sec_edgar workflows monthly \
    --tickers NVDA AMD TSLA NFLX SHOP \
    --forms "10-K" "10-Q" \
    --months-back 18 \
    --extract

# Track growth metrics over time using structured data
```

### Dividend Analysis
```console
# Dividend stock financial analysis
$ uv run python -m py_sec_edgar workflows monthly \
    --ticker-file dividend_aristocrats.csv \
    --forms "10-K" "10-Q" \
    --months-back 36 \
    --extract

# XBRL data for dividend sustainability analysis
```

## Regulatory and Compliance Analysis

### Financial Institution Analysis
```console
# Bank regulatory compliance monitoring
$ uv run python -m py_sec_edgar workflows monthly \
    --tickers JPM BAC WFC C \
    --forms "10-K" "10-Q" \
    --months-back 24 \
    --extract

# Structured data for regulatory ratio calculations
```

### ESG Reporting Analysis
```console
# ESG metrics from financial filings
$ uv run python -m py_sec_edgar workflows monthly \
    --ticker-file esg_focused_companies.csv \
    --forms "10-K" \
    --months-back 36 \
    --extract

# XBRL enables automated ESG metric extraction
```

## Monthly Workflow Options

**Time Range Options:**
- `--months-back` - Number of months back to process (default: 1)

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

## XBRL Data Structure

The Monthly workflow processes XBRL files that contain structured financial data:

```
XBRL Filing Components:
├── Instance Document (.xml)     # Actual financial facts and figures
├── Taxonomy Files              # Data element definitions
├── Schema Files (.xsd)         # Data structure definitions
├── Linkbase Files (.xml)       # Relationships and presentations
└── Calculation Files          # Mathematical relationships
```

## File Organization

```
sec_data/
├── Archives/
│   └── edgar/
│       ├── monthly/             # Monthly XBRL archives
│       │   └── YYYY/
│       │       └── QTR[1-4]/
│       │           └── YYYYMM.zip
│       └── data/                # Extracted XBRL contents
│           └── [CIK]/           # Company-specific folders
│               └── [Filing]/     # Individual XBRL filings
```

## Performance Considerations

**Data Volume:**
- Monthly archives contain XBRL files for all companies
- Larger file sizes due to structured XML format
- Consider disk space for extracted XBRL content

**Processing Time:**
- XBRL parsing is more intensive than text extraction
- Benefits from specific ticker and form filtering
- Extract option significantly impacts processing time

**Optimal Time Ranges:**
- 1-6 months: Excellent performance
- 6-24 months: Good performance for most analyses
- 24+ months: Consider chunking for very large analyses

## Integration with Other Workflows

### Combined with Full Index
```console
# XBRL structured data + full text content
$ uv run python -m py_sec_edgar workflows monthly --tickers AAPL --months-back 12 --extract
$ uv run python -m py_sec_edgar workflows full-index --tickers AAPL --forms "10-K" --extract
```

### Combined with Daily
```console
# Historical XBRL + recent unstructured filings
$ uv run python -m py_sec_edgar workflows monthly --tickers AAPL --months-back 24
$ uv run python -m py_sec_edgar workflows daily --tickers AAPL --days-back 30
```

## XBRL Form Types

**Primary XBRL Forms:**
- **10-K**: Annual reports with complete financial statements
- **10-Q**: Quarterly reports with interim financials
- **8-K**: Current events (limited XBRL content)
- **20-F**: Foreign company annual reports
- **40-F**: Canadian company annual reports

**XBRL Data Elements:**
- Financial statements (Income Statement, Balance Sheet, Cash Flow)
- Financial ratios and metrics
- Segment reporting data
- Notes to financial statements (structured portions)

## Common Analysis Applications

### Automated Financial Analysis
- Calculate financial ratios programmatically
- Build financial models from structured data
- Create automated screening algorithms
- Generate comparative financial analyses

### Research Applications
- Academic financial research
- Industry trend analysis
- Regulatory compliance studies
- Market efficiency research

### Investment Applications
- Quantitative investment strategies
- Portfolio optimization models
- Risk assessment algorithms
- Value and growth screening

The Monthly workflow is essential for any analysis requiring structured, standardized financial data that can be processed programmatically for quantitative analysis and automated financial modeling.