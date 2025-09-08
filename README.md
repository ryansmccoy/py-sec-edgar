# py-sec-edgar: Professional SEC EDGAR Filing Processor

<div align="center">

[![PyPI version](https://badge.fury.io/py/py-sec-edgar.svg)](https://badge.fury.io/py/py-sec-edgar)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Documentation Status](https://readthedocs.org/projects/py-sec-edgar/badge/?version=latest)](https://py-sec-edgar.readthedocs.io/en/latest/?badge=latest)
[![Code style: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Tests](https://github.com/ryansmccoy/py-sec-edgar/workflows/Tests/badge.svg)](https://github.com/ryansmccoy/py-sec-edgar/actions)
[![Coverage](https://codecov.io/gh/ryansmccoy/py-sec-edgar/branch/master/graph/badge.svg)](https://codecov.io/gh/ryansmccoy/py-sec-edgar)
[![GitHub stars](https://img.shields.io/github/stars/ryansmccoy/py-sec-edgar.svg)](https://github.com/ryansmccoy/py-sec-edgar/stargazers)

**A powerful, modern Python application for downloading, processing, and analyzing SEC EDGAR filings with professional-grade workflow automation.**

[🚀 Quick Start](#-quick-start) • [📖 Documentation](#-documentation) • [💼 Examples](#-comprehensive-examples) • [🔧 Installation](#-installation) • [⚡ Workflows](#-powerful-workflows)

</div>

---

py-sec-edgar transforms complex SEC filing data into accessible, structured information with enterprise-grade reliability and ease of use:

### 🎯 **Key Features**
- **🏗️ Professional Workflow System**: Four specialized workflows for different data collection needs
- **⚡ High-Performance Processing**: Efficient bulk download and processing of SEC archives
- **🎛️ Advanced Filtering**: Filter by ticker symbols, form types, date ranges, and more
- **🔄 Real-Time Monitoring**: RSS feed integration for live filing notifications
- **📊 Structured Data Extraction**: Extract and parse filing contents automatically
- **🛡️ Enterprise-Ready**: Robust error handling, logging, and configuration management
- **🐍 Modern Python**: Built with Python 3.10+, type hints, and modern best practices

### 🎪 **Use Cases**
- **📈 Investment Research**: Download 10-K/10-Q filings for fundamental analysis
- **🔍 Compliance Monitoring**: Track insider trading (Form 4) and ownership changes
- **📰 News & Events**: Monitor 8-K filings for material corporate events
- **🏫 Academic Research**: Bulk download historical filing data for studies
- **🤖 Machine Learning**: Create datasets for NLP and financial prediction models
- **📊 Portfolio Management**: Automated due diligence for investment portfolios

---

## 🚀 Quick Start

Get up and running with py-sec-edgar in under 2 minutes:

### 1. Install with uv (Recommended)
```bash
# Install uv if you haven't already
pip install uv

# Clone and setup the project
git clone https://github.com/ryansmccoy/py-sec-edgar.git
cd py-sec-edgar

# Install dependencies
uv sync

# Verify installation
uv run python -m py_sec_edgar --help
```

### 2. Your First Filing Download
```bash
# First, explore what's available without downloading (safe exploration)
uv run python -m py_sec_edgar workflows rss --show-entries --count 10 --list-only

# See what Apple filings are available without downloading
uv run python -m py_sec_edgar workflows daily --tickers AAPL --days-back 7 --forms "8-K" --no-download

# When ready, download Apple's latest 10-K annual report (includes 2025Q3 data)
uv run python -m py_sec_edgar workflows full-index --tickers AAPL --forms "10-K" --download --extract

# Process the latest quarterly data (2025Q3)
uv run python -m py_sec_edgar workflows full-index --quarter 2025Q3 --download --extract

# Monitor recent filings for your portfolio (explore first, then download)
uv run python -m py_sec_edgar workflows daily --tickers AAPL --tickers MSFT --tickers GOOGL --days-back 7 --forms "8-K" --no-download
# When satisfied, add --download flag to actually download files

# Monitor Apple's earnings announcement from August 1, 2024
uv run python -m py_sec_edgar workflows daily --tickers AAPL --start-date 2024-08-01 --end-date 2024-08-01 --forms "8-K" --download --extract

# Real-time RSS monitoring (list mode for exploration)
uv run python -m py_sec_edgar workflows rss --show-entries --count 10 --list-only
```

### 3. Explore Your Data
```bash
# Your downloaded filings are organized like this:
sec_data/
├── Archives/edgar/data/
│   └── 320193/                    # Apple's CIK
│       └── 000032019324000123/    # Specific filing
│           ├── aapl-20240930.htm  # Main 10-K document
│           ├── exhibits/          # All exhibits
│           └── Financial_Report.xlsx  # Structured financial data
```

---

## 🔧 Installation

### Prerequisites
- **Python 3.10+** (Required)
- **uv package manager** (Recommended) or pip
- **5GB+ disk space** for substantial data collection

### Method 1: Development Installation (Recommended)
```bash
# Clone the repository
git clone https://github.com/ryansmccoy/py-sec-edgar.git
cd py-sec-edgar

# Install with uv (handles everything automatically)
uv sync

# Install with pip (alternative)
pip install -e .
```

### Method 2: Direct Installation
```bash
# Install from PyPI
pip install py-sec-edgar

# Or with uv
uv pip install py-sec-edgar
```

### Method 3: Production Installation
```bash
# For production environments
uv pip install py-sec-edgar[prod]

# For development with all tools
uv sync --extra dev
```

---

## ⚡ Powerful Workflows

py-sec-edgar provides four specialized workflows, each optimized for different use cases. Each workflow has **comprehensive documentation** with dozens of real-world examples:

<div align="center">

| Workflow | Best For | Data Source | Time Range | Full Documentation |
|----------|----------|-------------|------------|-------------------|
| **📚 Full Index** | Historical research, bulk analysis | Quarterly archives | All historical data | **[📖 Complete Guide](docs/workflows/FULL_INDEX_WORKFLOW.md)** |
| **📅 Daily** | Recent monitoring, current events | Daily index feeds | Last 1-90 days | **[📖 Complete Guide](docs/workflows/DAILY_WORKFLOW.md)** |
| **📊 Monthly** | XBRL structured data | Monthly XBRL archives | Monthly intervals | **[📖 Complete Guide](docs/workflows/MONTHLY_WORKFLOW.md)** |
| **📡 RSS** | Real-time monitoring | Live RSS feeds | Real-time updates | **[📖 Complete Guide](docs/workflows/RSS_WORKFLOW.md)** |

</div>

### 📅 **SEC Data Availability & Update Schedule**

Understanding when SEC data is available helps you choose the right workflow for your needs:

<div align="center">

| Data Type | Update Frequency | Availability | Best Workflow | Notes |
|-----------|------------------|--------------|---------------|--------|
| **🔴 Live Filings** | Real-time | As filed | **RSS** | Immediate access to new filings |
| **📊 Daily Index** | Nightly at 10 PM ET | Previous business day | **Daily** | Complete daily filing lists |
| **📈 Full Index** | Updated throughout quarter | Current quarter + historical | **Full Index** | Comprehensive quarterly data |
| **📋 Quarterly Index** | End of quarter | Complete quarter (static) | **Full Index** | Final quarterly archives |
| **🔄 Weekly Rebuild** | Saturday mornings | All corrected data | **All workflows** | Post-acceptance corrections included |

</div>

**Key Update Schedule Details:**
- **🌙 Daily Index Files**: Updated nightly starting around 10:00 PM ET with the previous business day's filings
- **📊 Full Index Files**: Updated continuously throughout the current quarter, including all filings from quarter start through the previous business day
- **📅 Quarterly Index Files**: Static archives created at quarter-end containing the complete, final quarterly data
- **🔧 Weekly Rebuilds**: Every Saturday morning, all full and quarterly index files are rebuilt to incorporate post-acceptance corrections and amendments
- **⚡ Real-time RSS**: Live feed updated immediately as filings are accepted by the SEC

**📖 Data Currency Best Practices:**
- **For current events**: Use RSS workflow for immediate access to breaking filings
- **For recent activity**: Use Daily workflow for systematic monitoring of the last 1-90 days
- **For historical research**: Use Full Index workflow for comprehensive quarterly archives
- **For completeness**: Wait until Saturday morning rebuild for the most accurate quarterly data

> 💡 **Pro Tip**: Each workflow documentation contains 20+ practical examples, from basic usage to advanced enterprise patterns. Start with the [Workflow Documentation Hub](docs/workflows/) for complete coverage!

### 📚 Full Index Workflow
*Perfect for comprehensive historical analysis and bulk data collection*

```bash
# First, explore what's available for Apple without downloading
uv run python -m py_sec_edgar workflows full-index --tickers AAPL --no-download

# When ready, download all Apple filings from quarterly archives
uv run python -m py_sec_edgar workflows full-index --tickers AAPL --download

# Process the latest quarterly data (2025Q3) with extraction
uv run python -m py_sec_edgar workflows full-index --quarter 2025Q3 --download --extract

# Investment research: Explore tech giants first, then download
uv run python -m py_sec_edgar workflows full-index \
    --tickers AAPL --tickers MSFT --tickers GOOGL --tickers AMZN --tickers META \
    --forms "10-K" \
    --no-download  # Remove this flag when ready to download

# Academic research: Fortune 500 analysis with latest data
uv run python -m py_sec_edgar workflows full-index \
    --ticker-file examples/fortune500.csv \
    --forms "10-K" "10-Q" \
    --quarter 2025Q3 \
    --download --extract
```

### 📅 Daily Workflow
*Ideal for monitoring recent activity and staying current*

```bash
# Explore yesterday's filings without downloading first
uv run python -m py_sec_edgar workflows daily --days-back 1 --no-download

# When ready, download yesterday's filings
uv run python -m py_sec_edgar workflows daily --days-back 1 --download

# Weekly portfolio monitoring (explore first)
uv run python -m py_sec_edgar workflows daily \
    --ticker-file examples/portfolio.csv \
    --days-back 7 \
    --forms "8-K" "4" \
    --no-download  # Remove this flag when ready to download

# Monitor Apple's specific earnings announcement (August 1, 2024)
uv run python -m py_sec_edgar workflows daily \
    --tickers AAPL \
    --start-date 2024-08-01 \
    --end-date 2024-08-01 \
    --forms "8-K" \
    --download --extract  # Direct download since we know what we want
```

### 📊 Monthly Workflow
*Specialized for XBRL structured financial data*

```bash
# Explore what structured financial data is available (6 months)
uv run python -m py_sec_edgar workflows monthly --months-back 6 --no-download

# Download structured financial data when ready
uv run python -m py_sec_edgar workflows monthly --months-back 6 --download

# Focus on specific companies with extraction
uv run python -m py_sec_edgar workflows monthly \
    --tickers AAPL --tickers MSFT \
    --months-back 12 \
    --download --extract
```

### 📡 RSS Workflow
*Real-time monitoring and live feed processing*

```bash
# Explore latest filings in real-time (safe exploration)
uv run python -m py_sec_edgar workflows rss --show-entries --count 20 --list-only

# Monitor specific companies (list mode first)
uv run python -m py_sec_edgar workflows rss \
    --query-ticker AAPL \
    --count 10 \
    --show-entries --list-only

# When ready to process/download, remove --list-only flag
uv run python -m py_sec_edgar workflows rss \
    --query-ticker AAPL \
    --count 10 \
    --download

# Save RSS data for analysis (no download, just save feed data)
uv run python -m py_sec_edgar workflows rss \
    --save-file rss_filings.json \
    --count 100 \
    --list-only
```

---

## 💼 Comprehensive Examples

### 🏢 Investment Research Workflow

**Scenario**: You're analyzing potential investments in the renewable energy sector.

```bash
# Step 1: Use the provided renewable energy ticker list
# File: examples/renewable_energy.csv (already created)

# Step 2: Explore historical annual reports first (no download)
uv run python -m py_sec_edgar workflows full-index \
    --ticker-file examples/renewable_energy.csv \
    --forms "10-K" \
    --no-download

# Step 3: When ready, get historical annual reports with extraction
uv run python -m py_sec_edgar workflows full-index \
    --ticker-file examples/renewable_energy.csv \
    --forms "10-K" \
    --download --extract

# Step 4: Process specific quarterly filings (2025Q3)
uv run python -m py_sec_edgar workflows full-index \
    --ticker-file examples/renewable_energy.csv \
    --quarter 2025Q3 \
    --forms "10-Q" \
    --download --extract

# Step 5: Monitor recent Tesla activity (last 30 days for better data coverage)
uv run python -m py_sec_edgar workflows daily \
    --tickers TSLA \
    --days-back 30 \
    --forms "8-K" \
    --no-download  # Explore first, then add --download when ready

# Step 6: Set up real-time monitoring (exploration mode)
uv run python -m py_sec_edgar workflows rss \
    --query-ticker TSLA \
    --count 10 \
    --show-entries --list-only
```

**Result**: Complete dataset with historical context, recent activity, and real-time monitoring setup.

### 📊 Academic Research Pipeline

**Scenario**: Studying CEO compensation trends across S&P 500 companies.

```bash
# Step 1: Explore proxy statements availability (no download)
uv run python -m py_sec_edgar workflows full-index \
    --ticker-file examples/sp500_tickers.csv \
    --forms "DEF 14A" \
    --no-download

# Step 2: Download proxy statements when ready
uv run python -m py_sec_edgar workflows full-index \
    --ticker-file examples/sp500_tickers.csv \
    --forms "DEF 14A" \
    --download --extract

# Step 3: Process latest quarterly data (2025Q3) for comprehensive analysis
uv run python -m py_sec_edgar workflows full-index \
    --ticker-file examples/sp500_tickers.csv \
    --quarter 2025Q3 \
    --forms "10-Q" "DEF 14A" \
    --download --extract

# Step 4: Get recent quarterly filings (last 60 days for good data coverage)
uv run python -m py_sec_edgar workflows daily \
    --ticker-file examples/sp500_tickers.csv \
    --days-back 60 \
    --forms "10-Q" \
    --no-download  # Explore first

# Step 5: Extract structured financial data for analysis
uv run python -m py_sec_edgar workflows monthly \
    --ticker-file examples/sp500_tickers.csv \
    --months-back 12 \
    --download --extract
```

### 🔍 Compliance Monitoring System

**Scenario**: Monitor insider trading and ownership changes for your portfolio.

```bash
# Step 1: Explore recent insider trading (Form 4) - last 7 days
uv run python -m py_sec_edgar workflows daily \
    --ticker-file examples/portfolio.csv \
    --days-back 7 \
    --forms "4" \
    --no-download  # Explore first

# Step 2: When ready, download recent insider trading data
uv run python -m py_sec_edgar workflows daily \
    --ticker-file examples/portfolio.csv \
    --days-back 14 \
    --forms "4" \
    --download --extract

# Step 3: Track large ownership changes (last 30 days)
uv run python -m py_sec_edgar workflows daily \
    --ticker-file examples/portfolio.csv \
    --days-back 30 \
    --forms "SC 13G" "SC 13D" \
    --download --extract

# Step 4: Set up real-time insider trading alerts (exploration mode)
uv run python -m py_sec_edgar workflows rss \
    --query-form "4" \
    --count 25 \
    --show-entries --list-only
```

### 📰 News & Events Monitoring

**Scenario**: Stay ahead of market-moving news with automated 8-K monitoring.

```bash
# Monitor Apple's recent activity (last 30 days for good coverage)
uv run python -m py_sec_edgar workflows daily \
    --tickers AAPL \
    --days-back 30 \
    --forms "8-K" \
    --no-download  # Explore first, then add --download

# Monitor Tesla's recent activity (last 30 days)
uv run python -m py_sec_edgar workflows daily \
    --tickers TSLA \
    --days-back 30 \
    --forms "8-K" \
    --no-download  # Explore first

# When ready to download Apple's recent annual reports
uv run python -m py_sec_edgar workflows daily \
    --tickers AAPL \
    --days-back 90 \
    --forms "10-K" \
    --download --extract

# Set up comprehensive current events monitoring (exploration mode)
uv run python -m py_sec_edgar workflows rss \
    --query-form "8-K" \
    --show-entries \
    --count 25 \
    --list-only

# Advanced: Monitor multiple companies for 8-K filings
uv run python -m py_sec_edgar workflows daily \
    --ticker-file examples/portfolio.csv \
    --days-back 14 \
    --forms "8-K" \
    --no-download
```

---

## 🗂️ Understanding SEC Filings

py-sec-edgar makes it easy to work with SEC filings, but understanding what each form contains helps you choose the right data:

### 📋 Essential Form Types

| Form | Description | Frequency | Key Content |
|------|-------------|-----------|-------------|
| **10-K** | Annual Report | Yearly | Complete business overview, audited financials, risk factors |
| **10-Q** | Quarterly Report | Quarterly | Unaudited quarterly financials, updates since last 10-K |
| **8-K** | Current Events | As needed | Material corporate events, breaking news |
| **DEF 14A** | Proxy Statement | Annually | Executive compensation, board elections, shareholder proposals |
| **4** | Insider Trading | Within 2 days | Executive stock transactions |
| **SC 13G/D** | Beneficial Ownership | When threshold crossed | Large shareholder positions (>5%) |

### 🏗️ How SEC Data is Organized

**SEC Website Structure:**
```
https://www.sec.gov/Archives/edgar/data/[CIK]/[AccessionNumber]/[Filename]
```

**py-sec-edgar Local Structure:**
```
sec_data/
├── Archives/edgar/
│   ├── full-index/           # Downloaded quarterly archives
│   │   ├── 2024/QTR1/
│   │   ├── 2024/QTR2/
│   │   └── 2025/QTR3/        # Latest quarterly data
│   └── data/                 # Extracted filing contents
│       └── [CIK]/            # Company folders (e.g., 320193 for Apple)
│           └── [Filing]/     # Individual filing folders
│               ├── main_document.htm
│               ├── exhibits/
│               └── Financial_Report.xlsx
```

### 🔍 Understanding Company Identifiers

**Central Index Key (CIK)**: Unique numerical identifier assigned by SEC
- Example: Apple Inc. = 320193
- Permanent, never recycled
- Used in all SEC filings and URLs

**Ticker Symbol**: Stock exchange trading symbol
- Example: AAPL for Apple Inc.
- Can change due to rebranding, mergers
- py-sec-edgar handles ticker-to-CIK mapping automatically

### 📊 Filing Statistics (Historical Context)

| Form Type | Total Filings | Average per Year | Primary Use Case |
|-----------|---------------|------------------|------------------|
| Form 4 | 6,420,154 | ~800,000 | Insider trading monitoring |
| 8-K | 1,473,193 | ~180,000 | Breaking news and events |
| 10-Q | 552,059 | ~70,000 | Quarterly earnings analysis |
| 10-K | 180,787 | ~22,000 | Annual comprehensive analysis |
| 13F-HR | 224,996 | ~28,000 | Institutional holdings tracking |

---

## 🎛️ Advanced Configuration

### ⚙️ Environment Configuration

py-sec-edgar works out of the box with sensible defaults from `.env.example`. For custom configuration, create a `.env` file:

```bash
# Copy the example file and customize
cp .env.example .env
```

Key environment variables:

```bash
# SEC Data Directory (cross-platform)
SEC_DATA_DIR=./sec_data

# User Agent (Required by SEC)
USER_AGENT="YourCompany AdminContact@yourcompany.com"

# Request Settings (Conservative defaults)
REQUEST_DELAY=5.5
MAX_RETRIES=3

# Logging Configuration
LOG_LEVEL=WARNING
DEBUG=false
```

> 💡 **Important**: You must update `USER_AGENT` with your contact information for production use, as required by SEC guidelines.

### 📝 Ticker File Format

Create CSV files with ticker symbols (or use the provided examples):

```csv
# examples/portfolio.csv
TICKER
AAPL
MSFT
GOOGL
AMZN
TSLA

# Or simple format
AAPL
MSFT
GOOGL
```

### 🔧 Programmatic Usage

```python
from py_sec_edgar.workflows import (
    run_full_index_workflow,
    run_daily_workflow,
    run_monthly_workflow,
    run_rss_workflow
)

# Configure and run workflows programmatically
config = {
    "tickers": ["AAPL", "MSFT"],
    "forms": ["10-K", "10-Q"],
    "extract": True
}

# Run full index workflow
run_full_index_workflow(
    tickers=config["tickers"],
    forms=config["forms"],
    extract=config["extract"]
)

# Monitor recent filings
run_daily_workflow(
    tickers=config["tickers"],
    days_back=7,
    forms=["8-K"],
    extract=True
)
```

---

## 🔨 Development & Contribution

### 🏗️ Development Setup

```bash
# Clone repository
git clone https://github.com/ryansmccoy/py-sec-edgar.git
cd py-sec-edgar

# Setup development environment
uv sync --extra dev

# Install pre-commit hooks
uv run pre-commit install

# Run tests
uv run pytest

# Run linting
uv run ruff check
uv run ruff format

# Type checking
uv run mypy src/
```

### 🧪 Testing

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=py_sec_edgar --cov-report=html

# Run specific test categories
uv run pytest -m "not slow"          # Skip slow tests
uv run pytest -m integration         # Integration tests only
uv run pytest tests/test_filing.py   # Specific test file
```

### 📊 Performance Testing

```bash
# Test with small dataset
uv run python -m py_sec_edgar workflows full-index \
    --tickers AAPL \
    --forms "10-K" \
    --no-extract

# Benchmark larger operations
time uv run python -m py_sec_edgar workflows daily \
    --tickers AAPL --tickers MSFT --tickers GOOGL \
    --days-back 30 \
    --extract
```

---

## 📖 Documentation

### 📚 Comprehensive Guides

- **[Full Documentation](https://py-sec-edgar.readthedocs.io)**: Complete API reference and guides
- **[Workflow Documentation Hub](docs/workflows/)**: Detailed workflow guides with comprehensive examples
  - **[📚 Full Index Workflow](docs/workflows/FULL_INDEX_WORKFLOW.md)**: Complete quarterly archive processing for historical research
  - **[📅 Daily Workflow](docs/workflows/DAILY_WORKFLOW.md)**: Recent filings monitoring and systematic updates
  - **[📊 Monthly Workflow](docs/workflows/MONTHLY_WORKFLOW.md)**: XBRL structured data processing for quantitative analysis
  - **[📡 RSS Workflow](docs/workflows/RSS_WORKFLOW.md)**: Real-time RSS feed processing with advanced querying

### 🔗 Quick References

- **[CLI Reference](docs/cli-reference.md)**: Complete command-line interface documentation
- **[Configuration Guide](docs/configuration.md)**: Environment and settings configuration
- **[API Reference](docs/api-reference.md)**: Programmatic usage documentation
- **[Troubleshooting](docs/troubleshooting.md)**: Common issues and solutions

---

## 🚨 Important Notes

### ⚖️ SEC Compliance
- **User Agent Required**: The SEC requires a proper User-Agent header with your contact information
- **Rate Limiting**: py-sec-edgar includes respectful rate limiting (0.1s delay by default)
- **Fair Use**: Please be respectful of SEC resources and don't overwhelm their servers

### 💾 Storage Requirements
- **Full Index Processing**: Can generate several GB of data per quarter
- **Extracted Content**: Individual filings can be 10-100MB when extracted
- **Recommendation**: Start with specific tickers/forms, then scale up

### 🔒 Data Privacy
- **Public Data Only**: All data accessed is publicly available SEC filings
- **No Personal Info**: py-sec-edgar only accesses corporate disclosure documents
- **Compliance Ready**: Suitable for professional and academic use

---

## 🤝 Contributing

We welcome contributions! Here's how to get started:

### 🐛 Reporting Issues
1. Check existing [issues](https://github.com/ryansmccoy/py-sec-edgar/issues)
2. Create detailed bug reports with examples
3. Include system information and error logs

### 🔧 Contributing Code
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes with tests
4. Run the test suite: `uv run pytest`
5. Submit a pull request

### 📝 Contributing Documentation
- Improve existing documentation
- Add new examples and use cases
- Create tutorials for specific workflows

---

## 📄 License

py-sec-edgar is dual-licensed:

- **Personal Use**: MIT License (free for personal, educational, and research use)
- **Commercial Use**: GNU AGPLv3 License (free with copyleft requirements)
- **Business Licensing**: Contact [github@ryansmccoy.com](mailto:github@ryansmccoy.com) for commercial licensing options

See [LICENSE](LICENSE) for full details.

---

## 📞 Support & Community

### 💬 Getting Help
- **[GitHub Issues](https://github.com/ryansmccoy/py-sec-edgar/issues)**: Bug reports and feature requests
- **[Discussions](https://github.com/ryansmccoy/py-sec-edgar/discussions)**: Questions and community support
- **[Documentation](https://py-sec-edgar.readthedocs.io)**: Comprehensive guides and API reference

### 📧 Professional Support
- **Business Inquiries**: [github@ryansmccoy.com](mailto:github@ryansmccoy.com)
- **Commercial Licensing**: Available for enterprise use
- **Custom Development**: Professional services available

---

## 🙏 Acknowledgments

- **SEC EDGAR System**: For providing free access to corporate filing data
- **Python Community**: For the excellent libraries that make this project possible
- **Contributors**: Everyone who has contributed code, documentation, and feedback
- **Users**: The community that drives continuous improvement

---

<div align="center">

**⭐ Star this repository if py-sec-edgar helps your financial analysis! ⭐**

**Built with ❤️ for the financial analysis and research community**

[🏠 Homepage](https://github.com/ryansmccoy/py-sec-edgar) • [📖 Docs](https://py-sec-edgar.readthedocs.io) • [🐛 Issues](https://github.com/ryansmccoy/py-sec-edgar/issues) • [💬 Discussions](https://github.com/ryansmccoy/py-sec-edgar/discussions)

</div>
