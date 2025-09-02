# py-sec-edgar Workflow Documentation

This directory contains comprehensive documentation for all py-sec-edgar workflows, each designed for specific use cases and data access patterns.

## 📋 Available Workflows

| Workflow | Best For | Data Source | Time Coverage | Documentation |
|----------|----------|-------------|---------------|---------------|
| **📚 Full Index** | Historical research, bulk analysis | Quarterly archives | Complete historical data | [FULL_INDEX_WORKFLOW.md](FULL_INDEX_WORKFLOW.md) |
| **📅 Daily** | Current monitoring, recent events | Daily index feeds | Last 1-90 days | [DAILY_WORKFLOW.md](DAILY_WORKFLOW.md) |
| **📊 Monthly** | XBRL structured data, quantitative analysis | Monthly XBRL archives | Monthly intervals | [MONTHLY_WORKFLOW.md](MONTHLY_WORKFLOW.md) |
| **📡 RSS** | Real-time monitoring, breaking news | Live RSS feeds | Real-time updates | [RSS_WORKFLOW.md](RSS_WORKFLOW.md) |

## 🎯 Workflow Selection Guide

### Choose **Full Index** When:
- 📚 Conducting comprehensive historical research
- 🎓 Building academic datasets spanning multiple years
- 💼 Performing complete due diligence on companies
- 📊 Creating baseline datasets for analysis
- 🔍 Need complete quarterly filing archives

### Choose **Daily** When:
- 📅 Monitoring recent market activity (last few days/weeks)
- 🔄 Maintaining up-to-date datasets with systematic updates
- 📈 Tracking earnings seasons and quarterly filing periods
- ⚡ Need systematic coverage of recent filing activity
- 🎯 Bridging the gap between historical and real-time data

### Choose **Monthly** When:
- 🔢 Building quantitative financial models
- 📊 Creating structured datasets for machine learning
- 💹 Performing standardized financial analysis
- 🤖 Developing algorithmic trading strategies
- 📈 Need consistent XBRL data formats

### Choose **RSS** When:
- 📡 Real-time monitoring and alerts
- 📰 Tracking breaking news and current events
- 🔍 Searching and querying recent filings
- 💾 Building custom datasets with specific criteria
- ⚡ Need immediate access to latest filings

## 🚀 Quick Start Examples

### Investment Research Pipeline
```bash
# Step 1: Historical context (Full Index)
uv run python -m py_sec_edgar workflows full-index --tickers AAPL MSFT --forms "10-K" --extract

# Step 2: Recent updates (Daily)
uv run python -m py_sec_edgar workflows daily --tickers AAPL MSFT --days-back 30 --forms "8-K"

# Step 3: Real-time monitoring (RSS)
uv run python -m py_sec_edgar workflows rss --tickers AAPL MSFT --count 50 --show-entries
```

### Quantitative Analysis Setup
```bash
# Step 1: XBRL structured data (Monthly)
uv run python -m py_sec_edgar workflows monthly --ticker-file sp500.csv --months-back 24 --extract

# Step 2: Recent quarterly data (Daily)
uv run python -m py_sec_edgar workflows daily --ticker-file sp500.csv --forms "10-Q" --days-back 90

# Step 3: Current monitoring (RSS)
uv run python -m py_sec_edgar workflows rss --forms "10-Q" "10-K" --count 200 --save-to-file recent_earnings.json
```

### Compliance Monitoring System
```bash
# Step 1: Historical insider trading (Full Index)
uv run python -m py_sec_edgar workflows full-index --ticker-file portfolio.csv --forms "4" --extract

# Step 2: Recent ownership changes (Daily)
uv run python -m py_sec_edgar workflows daily --ticker-file portfolio.csv --forms "4" "SC 13G" --days-back 14

# Step 3: Real-time alerts (RSS)
uv run python -m py_sec_edgar workflows rss --ticker-file portfolio.csv --forms "4" --count 100 --show-entries
```

## 🔄 Workflow Integration Patterns

### Historical + Current Pattern
Combine historical depth with current monitoring:
```bash
# Historical foundation
uv run python -m py_sec_edgar workflows full-index --tickers NVDA --forms "10-K" "10-Q"

# Current updates
uv run python -m py_sec_edgar workflows daily --tickers NVDA --days-back 30 --forms "8-K"
```

### Systematic + Real-time Pattern
Systematic data collection with real-time alerts:
```bash
# Systematic daily processing
uv run python -m py_sec_edgar workflows daily --ticker-file watchlist.csv --days-back 7

# Real-time RSS monitoring
uv run python -m py_sec_edgar workflows rss --ticker-file watchlist.csv --count 50 --list-only
```

### Structured + Narrative Pattern
Combine structured XBRL data with narrative filings:
```bash
# Structured financial data
uv run python -m py_sec_edgar workflows monthly --tickers AAPL --months-back 12 --extract

# Narrative disclosures
uv run python -m py_sec_edgar workflows full-index --tickers AAPL --forms "10-K" --extract
```

## 📊 Performance and Scale Considerations

### Full Index Workflow
- **Scale**: Processes millions of filings per quarter
- **Storage**: Can generate several GB per quarter
- **Time**: Hours for comprehensive processing
- **Use**: One-time historical collection, periodic updates

### Daily Workflow  
- **Scale**: Hundreds to thousands of filings per day
- **Storage**: Moderate (MB to GB range)
- **Time**: Minutes to hours depending on range
- **Use**: Regular systematic updates, recent monitoring

### Monthly Workflow
- **Scale**: Structured datasets, moderate file counts
- **Storage**: Depends on extraction, typically moderate
- **Time**: Moderate processing time
- **Use**: Regular quantitative data updates

### RSS Workflow
- **Scale**: Latest 100-400 filings from RSS feeds
- **Storage**: Minimal to moderate
- **Time**: Seconds to minutes
- **Use**: Real-time monitoring, frequent updates

## 🛠️ Advanced Usage Patterns

### Data Pipeline Architecture
```bash
# 1. Foundation: Historical data collection
uv run python -m py_sec_edgar workflows full-index --ticker-file universe.csv --forms "10-K" "10-Q"

# 2. Updates: Daily systematic processing  
uv run python -m py_sec_edgar workflows daily --ticker-file universe.csv --days-back 1

# 3. Alerts: RSS monitoring for specific events
uv run python -m py_sec_edgar workflows rss --forms "8-K" --count 100 --save-to-file alerts.json

# 4. Analysis: XBRL data for modeling
uv run python -m py_sec_edgar workflows monthly --ticker-file analysis_targets.csv --months-back 24
```

### Custom Filtering Strategies
```bash
# Sector-specific monitoring
uv run python -m py_sec_edgar workflows daily --ticker-file tech_sector.csv --forms "8-K" "4"

# Event-specific tracking
uv run python -m py_sec_edgar workflows rss --forms "8-K" --search-text "acquisition" --count 200

# Regulatory filing focus
uv run python -m py_sec_edgar workflows full-index --forms "DEF 14A" "SC 13G" --ticker-file large_caps.csv
```

## 📚 Additional Resources

- **[Main README](../../README.md)**: Project overview and quick start
- **[CLI Reference](../cli-reference.md)**: Complete command-line documentation
- **[Configuration Guide](../configuration.md)**: Settings and environment setup
- **[API Documentation](../api-reference.md)**: Programmatic usage examples

## 🔗 External Documentation

- **[SEC EDGAR System](https://www.sec.gov/edgar)**: Official SEC EDGAR documentation
- **[Form Types Guide](https://www.sec.gov/forms)**: Official SEC form descriptions
- **[XBRL Information](https://www.sec.gov/structureddata/osd-inline-xbrl.html)**: SEC XBRL documentation

---

**💡 Pro Tip**: Start with RSS workflow for immediate results, then use Daily for systematic monitoring, and Full Index for comprehensive historical analysis. Combine workflows for complete coverage of your research needs!