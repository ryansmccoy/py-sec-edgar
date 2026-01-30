# Changelog - py-sec-edgar

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- Project metadata for ecosystem documentation
- GitHub Actions CI pipeline
- Standardized Makefile

---

## [1.2.0] - 2026-01-15

### Added
- FeedSpine adapter entry points
- `SecRssFeedAdapter` for RSS feed integration
- `SecDailyIndexAdapter` for daily index integration
- `SecQuarterlyIndexAdapter` for quarterly index integration

---

## [1.1.0] - 2026-01-10

### Added
- Professional workflow system with 4 specialized workflows
- Safe exploration flags (`--list-only`, `--no-download`)
- Advanced filtering (tickers, forms, date ranges)
- `--days-back` convenience flag

### Changed
- Improved CLI with rich output

---

## [1.0.0] - 2026-01-01

### Added
- Core SEC EDGAR filing processor
- High-performance bulk download
- Structured data extraction
- Real-time RSS feed monitoring
- Enterprise-grade error handling and logging
- Modern Python 3.10+ support

---

*For feature highlights, see [docs/FEATURES.md](docs/FEATURES.md).*
