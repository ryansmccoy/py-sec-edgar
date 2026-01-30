# Feature History - py-sec-edgar

<!-- Auto-generated from commits. Run `make todos` or edit manually for major features. -->

> Track new features as they're added. Newest first.

---

## 2026-01-15 - FeedSpine Integration (v1.2.0)

- Add entry points for FeedSpine adapter discovery
- `SecRssFeedAdapter`, `SecDailyIndexAdapter`, `SecQuarterlyIndexAdapter`
- Seamless integration with feedspine pipelines

## 2026-01-10 - Workflow System (v1.1.0)

- Four specialized workflows:
  - `rss` - Real-time RSS feed monitoring
  - `daily` - Daily index processing
  - `full-index` - Quarterly archive processing
  - `bulk` - High-volume batch processing
- Safe exploration with `--list-only` and `--no-download` flags

## 2026-01-05 - Advanced Filtering

- Filter by ticker symbols (`--tickers`)
- Filter by form types (`--forms`)
- Filter by date ranges (`--start-date`, `--end-date`)
- Filter by days back (`--days-back`)

## 2026-01-01 - Core Processing (v1.0.0)

- SEC EDGAR filing download and processing
- Structured data extraction
- Enterprise-grade error handling and logging
- Modern Python 3.10+ with type hints

---

*This file documents major feature additions. For detailed changes, see [CHANGELOG.md](docs/CHANGELOG.md).*
