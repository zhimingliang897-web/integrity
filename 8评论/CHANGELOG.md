# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased] - 2026-02-12

### Added
- **Stealth Module**: Added `utils/stealth.py` with advanced browser fingerprinting protection (navigator, webdriver, plugins mock) to improve scraping success rates.
- **Combined XHS Pipeline**: Implemented `search_and_scrape` in `searchers/xiaohongshu.py` to perform search and comment scraping within a single browser session.
- **UUID Support**: Added support for UUID-format note IDs in Xiaohongshu scraper.

### Changed
- **Xiaohongshu Architecture**:
  - Moved from failing `requests` API to **Playwright** browser interception for both search and comments.
  - Replaced direct URL navigation with **DOM Click Navigation** for note details to mimic human behavior and bypass server-side redirection (461 Anti-Spider).
  - Search and Scrape now share the same authenticated browser session to maintain `web_session` validity.
- **Douyin Search Strategy**:
  - Implemented **Homepage Pre-warming**: Visit `douyin.com` first to establish session.
  - Added **Search Input Simulation**: Type keywords into the search box instead of direct URL navigation to reduce CAPTCHA triggers.
- **Anti-Detection**:
  - Switched all Playwright instances (Douyin & XHS) to `headless=False` mode by default for better pass rates.
  - Configured `stealth` context to prioritize real Chrome browser channel if installed.
- **Robustness**:
  - Enhanced random delays (`time.sleep`) based on `speed` configuration.
  - Added cool-down periods between processing items to control access frequency.
- **Folder Cleanup**: Organized temporary debug scripts (`_debug*`, `_test*`) into `scripts/debug_archive` to declutter the project root while preserving history.

### Fixed
- **XHS API Error**: Fixed `CancelledError` in Playwright event handlers by replacing `response.json()` with `response.body()` + `json.loads()`.
- **Douyin CAPTCHA**: Resolved infinite CAPTCHA loops by using the homepage search box strategy.
- **Account Abnormal**: Fixed "账号异常" errors on XHS by using browser identifiers instead of raw HTTP requests.

## [0.1.0] - 2026-02-10

### Initial Release
- Basic support for Bilibili, Douyin, and Xiaohongshu scraping.
- LLM-based comment analysis pipeline.
