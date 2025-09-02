# py-sec-edgar CLI Testing Guide

## 🎯 **Overview**

This document provides comprehensive examples to test all CLI functionality before committing to GitHub. Each section includes multiple test scenarios to verify the application works correctly with different parameter combinations.

## 🚀 **Quick Setup**

```bash
# Navigate to project directory
cd b:\github\py-sec-edgar

# Install in development mode
uv pip install -e .

# Verify installation
uv run py-sec-edgar --help
```

## 📊 **1. FEEDS COMMANDS** - Data Feed Management

### **1.1 Individual Feed Updates**

```bash
# Test daily index updates
uv run py-sec-edgar feeds update-daily-index --days-back 1
uv run py-sec-edgar feeds update-daily-index --days-back 3 --no-skip-if-exists

# Test full index updates  
uv run py-sec-edgar feeds update-full-index --skip-if-exists
uv run py-sec-edgar feeds update-full-index --no-skip-if-exists --no-save-csv

# Test monthly XBRL updates
uv run py-sec-edgar feeds update-monthly-xbrl --months-back 1
uv run py-sec-edgar feeds update-monthly-xbrl --months-back 2 --no-skip-if-exists

# Test RSS feed fetching
uv run py-sec-edgar feeds fetch-recent-rss --count 50
uv run py-sec-edgar feeds fetch-recent-rss --count 100 --form-type "8-K"
```

### **1.2 Comprehensive Feed Updates**

```bash
# Test update-all command (NEW FEATURE)
uv run py-sec-edgar feeds update-all
uv run py-sec-edgar feeds update-all --skip-if-exists
uv run py-sec-edgar feeds update-all --skip-rss --days-back 2
uv run py-sec-edgar feeds update-all --skip-daily --skip-monthly
uv run py-sec-edgar feeds update-all --no-skip-if-exists --rss-count 200
```

## 🔄 **2. WORKFLOWS COMMANDS** - Complete Processing Pipelines

### **2.1 RSS Workflow** (Recent Filings)

```bash
# Basic RSS workflow tests
uv run py-sec-edgar workflows rss --count 50
uv run py-sec-edgar workflows rss --count 100 --download --no-extract

# Ticker filtering tests
uv run py-sec-edgar workflows rss --tickers AAPL --count 50
uv run py-sec-edgar workflows rss --tickers "AAPL,NVDA,MSFT" --count 100
uv run py-sec-edgar workflows rss --tickers AAPL NVDA MSFT --count 75
uv run py-sec-edgar workflows rss --no-ticker-filter --count 200

# Form filtering tests  
uv run py-sec-edgar workflows rss --forms "8-K" --count 100
uv run py-sec-edgar workflows rss --forms "10-K,10-Q" --count 50
uv run py-sec-edgar workflows rss --forms "8-K" "10-K" --count 75
uv run py-sec-edgar workflows rss --form "8-K" --count 100
uv run py-sec-edgar workflows rss --no-form-filter --count 50

# Combined filtering tests
uv run py-sec-edgar workflows rss --tickers AAPL --forms "8-K" --count 50
uv run py-sec-edgar workflows rss --tickers "AAPL,NVDA" --forms "10-K,8-K" --count 100
uv run py-sec-edgar workflows rss --no-ticker-filter --forms "8-K" --count 200

# File-based filtering tests (create test files first)
echo -e "AAPL\nNVDA\nMSFT" > test_tickers.txt
uv run py-sec-edgar workflows rss --ticker-file test_tickers.txt --count 50
uv run py-sec-edgar workflows rss --ticker-file test_tickers.txt --forms "8-K" --count 75

# Processing options tests
uv run py-sec-edgar workflows rss --tickers AAPL --count 25 --no-download
uv run py-sec-edgar workflows rss --tickers AAPL --count 25 --extract
uv run py-sec-edgar workflows rss --tickers AAPL --count 25 --download --extract
```

### **2.2 Daily Workflow** (Recent Business Days)

```bash
# Basic daily workflow tests
uv run py-sec-edgar workflows daily --days-back 1
uv run py-sec-edgar workflows daily --days-back 3 --download --no-extract

# Ticker filtering tests
uv run py-sec-edgar workflows daily --tickers AAPL --days-back 1
uv run py-sec-edgar workflows daily --tickers "AAPL,NVDA" --days-back 2
uv run py-sec-edgar workflows daily --no-ticker-filter --days-back 1

# Form filtering tests
uv run py-sec-edgar workflows daily --forms "8-K" --days-back 1
uv run py-sec-edgar workflows daily --forms "10-K,8-K" --days-back 2
uv run py-sec-edgar workflows daily --no-form-filter --days-back 1

# Combined filtering tests
uv run py-sec-edgar workflows daily --tickers AAPL --forms "8-K" --days-back 1
uv run py-sec-edgar workflows daily --no-ticker-filter --forms "8-K" --days-back 2

# Skip options tests (NEW FEATURE)
uv run py-sec-edgar workflows daily --tickers AAPL --days-back 1 --skip-if-exists
uv run py-sec-edgar workflows daily --tickers AAPL --days-back 1 --no-skip-if-exists

# Processing options tests
uv run py-sec-edgar workflows daily --tickers AAPL --days-back 1 --no-download
uv run py-sec-edgar workflows daily --tickers AAPL --days-back 1 --extract
uv run py-sec-edgar workflows daily --tickers AAPL --days-back 1 --no-extract
```

### **2.3 Monthly Workflow** (XBRL Processing)

```bash
# Basic monthly workflow tests
uv run py-sec-edgar workflows monthly --months-back 1
uv run py-sec-edgar workflows monthly --months-back 2 --download --no-extract

# Filtering tests
uv run py-sec-edgar workflows monthly --tickers AAPL --months-back 1
uv run py-sec-edgar workflows monthly --no-ticker-filter --months-back 1
uv run py-sec-edgar workflows monthly --forms "10-K" --months-back 1
```

### **2.4 Full-Index Workflow** (Quarterly Processing)

```bash
# Basic full-index workflow tests
uv run py-sec-edgar workflows full-index --download --no-extract

# Filtering tests
uv run py-sec-edgar workflows full-index --tickers AAPL NVDA
uv run py-sec-edgar workflows full-index --forms "10-K,8-K" 
uv run py-sec-edgar workflows full-index --no-ticker-filter --forms "8-K"
```

### **2.5 Unified Workflow** (All Workflows)

```bash
# Test unified workflow (runs all workflows in sequence)
uv run py-sec-edgar workflows unified
uv run py-sec-edgar workflows unified --skip-rss
uv run py-sec-edgar workflows unified --skip-daily --skip-monthly
```

## ⚙️ **3. FILTERS COMMANDS** - Data Analysis & Preview

### **3.1 Daily Index Filtering**

```bash
# Basic daily filtering
uv run py-sec-edgar filters daily --days-back 5
uv run py-sec-edgar filters daily --start-date "2025-08-25" --end-date "2025-08-29"

# Ticker filtering
uv run py-sec-edgar filters daily --tickers AAPL --days-back 3
uv run py-sec-edgar filters daily --tickers "AAPL,NVDA" --days-back 5
uv run py-sec-edgar filters daily --no-ticker-filter --days-back 2

# Form filtering
uv run py-sec-edgar filters daily --forms "8-K" --days-back 3
uv run py-sec-edgar filters daily --forms "10-K,8-K" --days-back 5
uv run py-sec-edgar filters daily --no-form-filter --days-back 2

# Output options
uv run py-sec-edgar filters daily --tickers AAPL --json-output --days-back 2
uv run py-sec-edgar filters daily --tickers AAPL --include-urls --days-back 2
uv run py-sec-edgar filters daily --tickers AAPL --limit 25 --days-back 2
uv run py-sec-edgar filters daily --tickers AAPL --save-csv daily_results.csv --days-back 2

# Interactive mode
uv run py-sec-edgar filters daily --interactive
```

### **3.2 Full Index Filtering**

```bash
# Basic full index filtering
uv run py-sec-edgar filters full-index
uv run py-sec-edgar filters full-index --limit 100

# Ticker filtering
uv run py-sec-edgar filters full-index --tickers AAPL
uv run py-sec-edgar filters full-index --tickers "AAPL,NVDA,MSFT"
uv run py-sec-edgar filters full-index --no-ticker-filter

# Form filtering
uv run py-sec-edgar filters full-index --forms "10-K"
uv run py-sec-edgar filters full-index --forms "10-K,8-K"
uv run py-sec-edgar filters full-index --no-form-filter

# Output options
uv run py-sec-edgar filters full-index --tickers AAPL --json-output
uv run py-sec-edgar filters full-index --tickers AAPL --include-urls
uv run py-sec-edgar filters full-index --tickers AAPL --save-csv full_results.csv
```

### **3.3 Monthly XBRL Filtering**

```bash
# Basic monthly XBRL filtering
uv run py-sec-edgar filters monthly-xbrl --months-back 6
uv run py-sec-edgar filters monthly-xbrl --months-back 12 --limit 0

# Filtering options
uv run py-sec-edgar filters monthly-xbrl --tickers AAPL --months-back 6
uv run py-sec-edgar filters monthly-xbrl --forms "10-K" --months-back 6
uv run py-sec-edgar filters monthly-xbrl --no-form-filter --months-back 3

# Output options
uv run py-sec-edgar filters monthly-xbrl --tickers AAPL --json-output --months-back 6
uv run py-sec-edgar filters monthly-xbrl --tickers AAPL --include-urls --months-back 6
uv run py-sec-edgar filters monthly-xbrl --tickers AAPL --save-csv xbrl_results.csv --months-back 6

# Advanced options
uv run py-sec-edgar filters monthly-xbrl --interactive
uv run py-sec-edgar filters monthly-xbrl --log-level DEBUG --months-back 3
```

## ⚙️ **4. PROCESS COMMANDS** - Data Processing

### **3.1 General Filing Processing**

```bash
# Basic processing tests
uv run py-sec-edgar process filings --limit 50
uv run py-sec-edgar process filings --ticker-list test_tickers.txt --limit 25

# Form type filtering
uv run py-sec-edgar process filings --form-types "8-K" --limit 50
uv run py-sec-edgar process filings --form-types "10-K" --form-types "8-K" --limit 75

# CIK-specific processing
uv run py-sec-edgar process filings --cik "0000320193" --limit 25  # Apple's CIK

# Processing options
uv run py-sec-edgar process filings --no-download --extract --limit 25
uv run py-sec-edgar process filings --no-parse-header --limit 25
```

### **3.2 Daily Filing Processing**

```bash
# Test daily processing
uv run py-sec-edgar process daily-filings --days-back 1
uv run py-sec-edgar process daily-filings --days-back 2 --no-download
```

### **3.3 Monthly XBRL Processing**

```bash
# Test monthly XBRL processing
uv run py-sec-edgar process monthly-xbrl --months-back 1
uv run py-sec-edgar process monthly-xbrl --months-back 1 --extract
```

## 🛠️ **5. UTILS COMMANDS** - Utility Operations

```bash
# Test utility commands (check what's available)
uv run py-sec-edgar utils --help

# Test any available utility commands
# (Add specific tests based on what utils are available)
```

## 🎯 **6. EDGE CASE TESTING**

### **5.1 Error Handling Tests**

```bash
# Test invalid parameters
uv run py-sec-edgar workflows rss --count 0        # Should handle gracefully
uv run py-sec-edgar workflows daily --days-back 0  # Should handle gracefully
uv run py-sec-edgar workflows rss --tickers ""     # Should handle empty tickers

# Test invalid files
uv run py-sec-edgar workflows rss --ticker-file nonexistent.txt  # Should error gracefully

# Test invalid forms
uv run py-sec-edgar workflows rss --forms "INVALID-FORM" --count 10
```

### **5.2 Combination Tests**

```bash
# Test multiple parameter combinations
uv run py-sec-edgar workflows rss --tickers AAPL --forms "8-K" --count 25 --extract --no-download

# Test conflicting parameters
uv run py-sec-edgar workflows rss --no-ticker-filter --tickers AAPL  # Should prioritize no-filter

# Test file + command line combinations
uv run py-sec-edgar workflows rss --ticker-file test_tickers.txt --tickers MSFT --count 50
```

## 📝 **7. OUTPUT VALIDATION**

For each test command, verify:

### **6.1 Expected Behaviors**

- ✅ **Logging**: Proper log messages with timestamps
- ✅ **Progress**: Clear progress indicators
- ✅ **Success Messages**: Confirmation of completed operations
- ✅ **Error Handling**: Graceful error messages (not crashes)
- ✅ **File Creation**: Files created in expected locations
- ✅ **Data Validation**: Downloaded data appears valid

### **6.2 Key Log Messages to Look For**

```
✅ Success indicators:
"✅ RSS workflow completed successfully"
"✅ Daily workflow completed successfully"  
"Request successful: ... (Status: 200)"
"Successfully downloaded new file: ..."

⚠️ Expected warnings:
"File unchanged: ..." (when skip-if-exists works)
"No ticker filtering (processing all tickers)"

❌ Should NOT see:
"403 Forbidden" (SEC compliance working)
"ModuleNotFoundError" (imports fixed)
"AttributeError" (missing methods)
```

## 🔍 **8. TESTING SCHEDULE**

### **Phase 1: Basic Functionality** (15 mins)
```bash
# Verify core commands work
uv run py-sec-edgar --help
uv run py-sec-edgar feeds update-daily-index --days-back 1
uv run py-sec-edgar workflows rss --tickers AAPL --count 10
```

### **Phase 2: Filter Testing** (20 mins)
```bash
# Test data analysis commands
uv run py-sec-edgar filters daily --tickers AAPL --days-back 2
uv run py-sec-edgar filters full-index --tickers AAPL --limit 25
uv run py-sec-edgar filters monthly-xbrl --tickers AAPL --months-back 3
```

### **Phase 3: Workflow Testing** (20 mins)
```bash
# Test all filter combinations
uv run py-sec-edgar workflows rss --tickers AAPL --forms "8-K" --count 25
uv run py-sec-edgar workflows daily --no-ticker-filter --forms "8-K" --days-back 1
uv run py-sec-edgar workflows rss --ticker-file test_tickers.txt --count 50
```

### **Phase 4: New Features** (15 mins)
```bash
# Test new additions
uv run py-sec-edgar feeds update-all
uv run py-sec-edgar workflows daily --skip-if-exists --days-back 1
uv run py-sec-edgar feeds update-all --skip-rss --days-back 2
```

### **Phase 5: Edge Cases** (10 mins)
```bash
# Test error handling
uv run py-sec-edgar workflows rss --count 0
uv run py-sec-edgar workflows rss --ticker-file nonexistent.txt
```

## ✅ **9. SUCCESS CRITERIA**

Before committing to GitHub, ensure:

- [ ] All basic commands execute without crashes
- [ ] SEC API returns 200 status codes (not 403 Forbidden)
- [ ] Flexible filtering works (tickers, forms, files, disable options)
- [ ] New features work (update-all, skip-if-exists)
- [ ] Error handling is graceful (no Python tracebacks for user errors)
- [ ] Log messages are clear and informative
- [ ] Files are created in expected locations
- [ ] CLI help text is accurate and helpful

## 🎉 **Ready for GitHub!**

Once all tests pass, the application will be ready for commit with:
- ✅ Modern CLI structure
- ✅ SEC compliance
- ✅ Flexible filtering options
- ✅ Proper error handling
- ✅ Comprehensive functionality

Clean up test files:
```bash
rm test_tickers.txt
```