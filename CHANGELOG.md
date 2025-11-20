# Changelog

All notable changes to the E-commerce UX Competitive Intelligence Agent will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2025-11-20

### Breaking Changes
- **Removed Auto-Detection**: URL pattern matching removed for reliability
  - Tool now always prompts user to select analysis type
  - Can still skip prompt with `--analysis-type` flag
- **Removed Automated/Headless Mode**: All analysis now runs in interactive mode
  - Browser always opens in visible mode
  - User controls navigation for every site
  - More reliable with bot-protected sites

### Added
- **Interactive Analysis Type Prompt**: Always shown unless `--analysis-type` specified
  - Nice formatted table with descriptions
  - Clear indication of analysis mode for each type
  - Keyboard interrupt handling (Ctrl+C to cancel)
- **Screenshot Retry Option**: After each capture, user can:
  - Press **Y** to continue to next competitor
  - Press **R** to retry screenshot capture
  - Press **S** to skip this competitor
  - Visual confirmation of captured screenshots
- **Two-Phase Workflow**: Dramatically improved UX
  - **Phase 1**: Capture all competitor screenshots (browser interactions)
  - **Phase 2**: AI analysis of all screenshots (run in batch)
  - No more waiting for slow AI between captures
  - Clear phase indicators in console output
- **Automatic Image Compression**: Screenshots compressed if > 5MB
  - Progressive JPEG compression (85%, 75%, 65%, 55%, 45%)
  - Automatic resize if still too large (30% reduction)
  - Maintains visual quality while staying under Claude API limit
  - Transparent to user (happens automatically)

### Fixed
- **Timestamp Bug**: Fixed `local variable 'timestamp' referenced before assignment` in interactive capture
- **Navigation Timeout**: Changed from `networkidle` to `domcontentloaded` wait condition
  - Prevents timeouts on sites with persistent connections (analytics, chat widgets)
  - Better error handling if initial navigation fails
- **Input Prompts Not Showing**: Simplified async input handling
  - Removed complex ThreadPoolExecutor approach
  - Direct synchronous `input()` calls with proper error handling
  - EOF and KeyboardInterrupt properly caught

### Improved
- **Better Timeout Handling**: Pages that fail initial navigation can be manually navigated
- **Clear Phase Separation**: Visual indicators for capture vs analysis phases
- **Progress Tracking**: Shows X/Y for both phases independently
- **Error Messages**: More helpful error output with context

### Changed
- All analysis types now run in interactive mode (product, homepage, basket, checkout)
- Browser always visible (no headless mode)
- User controls every capture with Enter key
- Pillow added as dependency for image processing

### Documentation
- Updated README to reflect new interactive-only workflow
- Removed auto-detection documentation
- Added retry option instructions
- Updated "How It Works" section with two-phase workflow
- Clarified interactive mode behavior

## [1.1.0] - 2025-11-20

### Added
- **Manual Screenshot Mode**: New `--manual-mode` flag to analyze pre-captured screenshots
  - Bypasses browser automation entirely for heavily protected sites
  - Upload your own screenshots: `python main.py --manual-mode --screenshots-dir ./my-screenshots`
  - Supports flexible naming: `{competitor}_desktop.png`, `desktop.png`, etc.
  - Perfect for sites with strong bot detection (Amazon, eBay, etc.)
- **Enhanced Interactive Mode Bot Detection Handling**:
  - Improved prompts when bot detection is triggered
  - Clear step-by-step instructions for manual navigation
  - Red border panel alert when CAPTCHA or blocking detected
  - Guidance for solving CAPTCHAs and completing verification steps
- **Hybrid Workflow**: Automated where possible, manual assist when blocked

### Improved
- Interactive mode now provides better guidance when sites block automation
- Bot detection warnings include actionable steps
- Manual mode fallback for production use cases

### Documentation
- Added bot detection handling guide
- Manual mode usage instructions
- When to use automated vs manual vs hybrid approaches

## [1.0.0] - 2025-11-20

### Added
- **Multi-Page-Type Support**: Analyze 4 page types out of the box
  - Homepage pages (8 criteria)
  - Product pages (9 criteria)
  - Basket/cart pages (10 criteria)
  - Checkout flows (8 criteria with interaction)
- **Smart Auto-Detection**: Automatically detects page type from URL patterns
- **Competitive Intelligence Framework**: Reports frame findings as competitive advantages vs exploitable vulnerabilities
- **Competitive Intelligence Reports** with strategic insights:
  - Market landscape analysis with feature adoption rates
  - Feature adoption heatmap (visual matrix)
  - White space opportunities identification
  - Best-in-class reference by criteria
  - Market trends analysis (high variance features)
  - Competitive positioning map (UX maturity spectrum)
  - Strategic recommendations (table stakes, differentiation, emerging threats)
- **Hierarchical Output Structure**: Organized by audit run and competitor
- **Criteria Config System**: YAML-based extensible configuration
- **Page Type Auto-Detector**: Automatic URL pattern recognition
- **Interactive Mode**: Human-in-the-loop for basket and checkout pages
- **Automated Mode**: Headless operation for homepages and product pages
- **Bot Detection Evasion**: Stealth mode with rotating user agents
- **Claude Vision Analysis**: AI-powered UX evaluation
- **Research-Backed Criteria**: Based on Baymard Institute and Nielsen Norman Group

### Changed
- Restructured reports from "recommendations" to "competitive intelligence"
- Moved from flat output to hierarchical audit structure
- Changed from `config.yaml` to modular `criteria_config/` directory
- Updated Claude prompts to competitive analyst perspective

### Technical
- Python 3.9+ support
- Playwright for browser automation
- Claude Sonnet 4.5 for AI analysis
- Pydantic for configuration validation
- Rich for enhanced console output

---

## Version Format

This project uses [Semantic Versioning](https://semver.org/):
- **MAJOR** version for incompatible API changes
- **MINOR** version for added functionality in a backward compatible manner
- **PATCH** version for backward compatible bug fixes

## Upcoming Features

Future releases may include:
- HTML/DOM analysis alongside screenshots
- Time-series tracking (monitor competitor changes)
- Parallel competitor analysis for speed
- Additional page types (search results, category pages, account pages)
- Export to CSV/Excel formats
- Integration APIs for analytics tools

---

## Release Notes

### How to Upgrade

When upgrading between versions:

1. Check this CHANGELOG for breaking changes
2. Update dependencies: `pip install -r requirements.txt --upgrade`
3. Review new configuration options in `criteria_config/`
4. Run tests: `python tests/verify_setup.py`

### Support

For issues or questions about specific versions:
- Check the documentation in `docs/`
- Review examples in `tests/`
- Open an issue on GitHub with version information
