# Changelog

All notable changes to the E-commerce UX Competitive Intelligence Agent will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.1] - 2025-11-21

### Added
- **Retry Failed Analyses**: Interactive prompt after all analyses complete
  - If any competitors fail analysis, user is prompted to retry before report generation
  - Reuses existing screenshots from audit folder (no browser interaction needed)
  - One retry attempt per failed competitor
  - Shows retry summary with success count
  - Only generates reports after retry decision is made

### Fixed
- **Image Format Consistency**: All images now sent to Claude API as JPEG
  - Simplified from conditional PNG/JPEG logic to always JPEG
  - Small files use quality=95 (near-lossless)
  - Large files use progressive compression (85→75→65→55→45)
  - Eliminates media type mismatch errors
- **Data Structure Flattening**: Fixed nested analysis structure issues
  - Claude's response data now properly flattened at top level
  - All report generators updated to handle flattened structure
  - Markdown report generator now accesses fields directly (not via `analysis` key)
  - HTML report filtering now works correctly with flattened data
  - Display summary table now uses flattened structure
- **HTML Report Image Paths**: Screenshots now use relative paths
  - Paths converted from absolute to relative based on HTML file location
  - Images load correctly in lightbox gallery
  - Works when opening HTML file from any location
- **HTML Report Generation**: Fixed crash when no competitors succeed
  - Added complete fallback data structure for zero-success scenarios
  - Report generates with "N/A" placeholders instead of crashing
  - Handles missing `overall_score` gracefully

### Changed
- Image compression always converts to JPEG (previously conditional PNG preservation)
- Report generation now happens after retry prompt (previously before)

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
- **Interactive HTML Reports**: Rich, interactive reports with visualizations
  - Radar chart comparing all competitors across criteria
  - Heatmap showing feature adoption matrix with color coding
  - Bar chart displaying top performers by criterion
  - Box plot showing score distribution and consistency
  - Executive summary with key metrics and insights
  - Generated automatically alongside markdown reports
- **Screenshot Annotations**: Visual findings overlaid on screenshots
  - Automatic badges for top 2 advantages (green) and vulnerabilities (red)
  - PIL-based annotation system with rounded rectangles
  - Annotations based on competitive status (advantage/parity/vulnerability)
  - Scales properly for desktop and mobile viewports
- **Lightbox Gallery**: Full-screen screenshot viewing
  - Click any screenshot to open in full-screen modal
  - ESC key or click outside to close
  - Shows competitor name and viewport (desktop/mobile)
  - Prevents body scroll when lightbox is active
- **Real-time Filtering**: Interactive search and filtering in HTML reports
  - Search competitors by name (instant results)
  - Minimum score slider (0-10 range)
  - Competitive status filter (advantages/vulnerabilities/parity)
  - Live results counter showing X of Y competitors
  - Reset filters button
- **Competitive Status Labeling**: Automatic relative performance indicators
  - Advantage: Scores above market average on criterion
  - Parity: Scores at market average
  - Vulnerability: Scores below market average
  - Status is context-aware based on competitive set
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
- **Image Compression for Claude API**: Fixed base64 encoding overhead calculation
  - Previously checked if raw file < 5MB, but base64 adds ~33% overhead
  - Now uses ~3.65MB threshold for raw files to ensure encoded data < 5MB
  - Prevents "image exceeds 5 MB maximum" errors from Claude API
  - 4.8MB screenshots now automatically compress to ~2MB before encoding
- **HTML Report Generation Error**: Fixed crash when all competitors fail analysis
  - Added complete fallback data structure when no successful results
  - Report now generates with "N/A" placeholders instead of crashing
  - Handles missing `average_score`, `leader`, `weakest` keys gracefully
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
- Report output now includes both markdown and HTML formats
- Dependencies added: Pillow (image processing), Plotly (charts), Jinja2 (HTML templates), NumPy (Plotly requirement)

### Documentation
- Updated README to reflect new interactive-only workflow
- Removed auto-detection documentation
- Added retry option instructions
- Updated "How It Works" section with two-phase workflow
- Clarified interactive mode behavior
- Added comprehensive HTML report explainer section (charts, filters, competitive status labels)
- Updated configuration section to reference YAML files instead of config.yaml
- Consolidated redundant sections and removed ~100 lines of outdated content
- Updated project structure to show new utilities (html_report_generator, screenshot_annotator)
- Updated version to 1.2.0 throughout documentation

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
- Multi-step journey support (homepage → product → add to cart → basket)
- HTML/DOM analysis alongside screenshots (for accessibility, performance metrics)
- Time-series tracking (monitor competitor changes over time)
- Parallel competitor analysis for speed
- Additional page types (search results, category pages, account pages)
- Export to CSV/Excel formats
- PowerPoint export with charts and screenshots
- Integration APIs for analytics tools (GA4, ContentSquare)

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
