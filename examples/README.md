# py-sec-edgar Examples

This directory contains examples demonstrating how to use py-sec-edgar for various SEC filing analysis tasks. The examples are organized by complexity and use case to help you get started quickly.

## ⚠️ Important Notice

**Some examples may be outdated** and may require updates to work with the current project structure. The py-sec-edgar library has evolved significantly, and some examples might reference:

- Old import paths that have been reorganized
- Modules that have been renamed or moved
- Dependencies that are no longer required
- API methods that have changed

**Status of Examples:**
- ✅ **Working Examples**: Tested and confirmed to work with current structure
- 🔄 **Needs Updates**: May have import/structure issues but core concept is valid
- ❌ **Deprecated**: Based on old architecture, needs significant rework

We're actively working through each example to update them for the current project structure. If you encounter issues:

1. Check if the example has been updated recently
2. Try the setup commands listed in the example header
3. Look for similar working examples in the same category
4. Report issues or contribute fixes via GitHub

## 📚 Getting Started

Before running any examples, you need to download the SEC data:

```bash
# Download the essential data files (company tickers and filing index)
uv run py-sec-edgar feeds update-full-index

# Optional: Download recent filings for more comprehensive examples
uv run py-sec-edgar feeds update-daily-index
```

## 📁 Example Categories

### 01_getting_started
Simple examples for first-time users to understand basic concepts.
**Status**: ✅ **Working Examples**
- ✅ `consolidated_parser_demo.py` - Demonstrates unified parsing interface
- ✅ `list_company_filings.py` - Core filing lookup functionality

### 02_filing_lookup
Examples for finding and listing SEC filings by company, date, or filing type.
**Status**: ✅ **All Working** - Clean, user-friendly examples with real SEC data

### 03_data_extraction
Examples for extracting specific data and sections from SEC filings.
**Status**: 🔄 **Mixed**
- ✅ `extract_sections_basic.py` - Working with real SEC data (slower but functional)
- ❌ `extract_sections_demo.py` - Import issues with transformers module

### 04_financial_analysis
Examples for financial analysis, growth calculations, and comparative studies.
**Status**: ✅ **Excellent Working Examples**
- ✅ `quarterly_growth_extractor.py` - Comprehensive revenue analysis with Excel export
- ✅ `quarterly_growth_analyzer.py` - Advanced automated growth analysis
- ✅ `financial_statement_analyzer.py` - Growth rates, ratios, and insights

### 05_advanced_parsing
Advanced parsing techniques for complex filing structures and data extraction.
**Status**: ✅ **Core Examples Working**
- ✅ `focused_parser_examples.py` - Multi-parser demonstration
- ✅ `comprehensive_analysis_suite.py` - Cross-filing type analysis (10-K, 10-Q, 8-K, DEF 14A, Form 4)
- ❌ `comprehensive_sec_analysis.py` - Issues with large file processing

### 06_llm_analysis
AI/LLM-powered analysis examples for insights and automated processing.
**Status**: ❓ *Not yet tested*

## 🚀 Quick Start - Verified Working Examples

1. **Setup data** (required for all examples):
   ```bash
   uv run py-sec-edgar feeds update-full-index
   ```

2. **Try confirmed working examples**:
   ```bash
   # Basic filing lookup (great for beginners)
   uv run examples/01_getting_started/list_company_filings.py AAPL 10-K

   # Advanced financial analysis with real data
   uv run examples/04_financial_analysis/quarterly_growth_extractor.py AAPL

   # Comprehensive parsing demonstration
   uv run examples/01_getting_started/consolidated_parser_demo.py

   # Advanced multi-filing analysis
   uv run examples/05_advanced_parsing/comprehensive_analysis_suite.py
   ```

3. **Financial Analysis Examples** (excellent for investment research):
   ```bash
   # Quarterly revenue growth analysis with Excel export
   uv run examples/04_financial_analysis/quarterly_growth_extractor.py MSFT

   # Comprehensive financial statement analysis
   uv run examples/04_financial_analysis/financial_statement_analyzer.py
   ```

## 📋 Data Requirements

| Example Category | Required Data | Command to Get Data | Status |
|-----------------|---------------|---------------------|--------|
| 01_getting_started | Company tickers | `uv run py-sec-edgar feeds update-full-index` | ✅ **Working** |
| 02_filing_lookup | Company tickers + Filing index | `uv run py-sec-edgar feeds update-full-index` | ✅ **Working** |
| 03_data_extraction | Filing index + Downloaded filings | `uv run py-sec-edgar workflows download-and-parse` | 🔄 **Mixed** |
| 04_financial_analysis | Full data + Downloaded filings | `uv run py-sec-edgar workflows download-and-parse` | ✅ **Excellent** |
| 05_advanced_parsing | Full data + Downloaded filings | `uv run py-sec-edgar workflows download-and-parse` | ✅ **Core Examples Working** |
| 06_llm_analysis | Full data + AI models | See individual example requirements | ❓ **Not Tested** |

## 🛠️ Troubleshooting

### Common Issues with Older Examples

1. **Import Errors**:
   ```
   ModuleNotFoundError: No module named 'py_sec_edgar.transformers'
   ```
   - The module structure has changed
   - Check for updated examples or file an issue

2. **Missing Dependencies**:
   ```
   ImportError: No module named 'html2text'
   ```
   - Run: `uv add html2text lxml_html_clean chardet`

3. **Data Not Found**:
   ```
   FileNotFoundError: ticker mapping file not found
   ```
   - Run: `uv run py-sec-edgar feeds update-full-index`

### Getting Help

If you encounter issues:
```bash
# Check what CLI commands are available
uv run py-sec-edgar --help

# Check what workflows are available
uv run py-sec-edgar workflows --help

# Full data setup (takes longer but enables most examples)
uv run py-sec-edgar workflows download-and-parse --ticker AAPL --forms 10-K,10-Q --limit 5
```

## 🔄 Contributing Example Updates

We welcome help updating outdated examples! When updating an example:

1. Test it works with the current py-sec-edgar structure
2. Update imports to use current module paths
3. Add clear user-focused documentation in the header
4. Include setup commands for required data
5. Update the status in this README

## 📖 Additional Resources

- [py-sec-edgar Documentation](https://py-sec-edgar.readthedocs.io)
- [SEC EDGAR Database](https://www.sec.gov/edgar)
- [Filing Types Reference](https://www.sec.gov/forms)
