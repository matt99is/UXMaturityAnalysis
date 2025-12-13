# Changelog

All notable changes to the E-commerce UX Maturity Analysis Agent will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.4.0] - 2025-12-12

### Added
- **🔗 Resources Project Integration**: Automatic portfolio publishing
  - New `resources_integration_config.json` for configuration
  - Reports automatically save to Resources project (`/ux-analysis/` folder)
  - Auto-updates Resources index page with new report cards
  - Seamless integration with Netlify deployment workflow
  - Created `scripts/update_resources_index.py` for index management

- **🎯 Smart Output Path Detection**:
  - Modified `audit_organizer.py` to detect Resources configuration
  - Falls back to local `output/audits/` if Resources not configured
  - Automatically creates directory structure in target location

- **📝 Automatic Index Updates**:
  - New index updater script scans for reports and extracts metadata
  - Generates properly formatted cards matching Resources design
  - Updates section count automatically (e.g., "(2)" → "(3)")
  - Preserves all existing HTML structure and content

### Changed
- **🟣 Purple Theme**: Complete color scheme update for visual distinction
  - Changed from green (#10b981, #059669) to purple (#8b5cf6, #7c3aed)
  - All gradients, buttons, badges, borders updated
  - Chart colors and accents now purple
  - Maintains brand consistency with Resources project:
    - Green = Case Studies
    - Blue = Guides
    - Purple = Analysis Reports

- **📊 Report Output Workflow**:
  - `main.py` now triggers index update after report generation
  - Post-generation confirmation shows Resources path when configured
  - Clear console output indicating integration status

### Technical
- Modified files:
  - `main.py`: Added Resources index updater call
  - `src/utils/audit_organizer.py`: Added config detection, path routing
  - `src/utils/html_report_generator.py`: Green → purple theme
  - `scripts/generate_index.py`: Green → purple theme

- New files:
  - `resources_integration_config.json`: Integration configuration
  - `scripts/update_resources_index.py`: Index updater utility

### Documentation
- Updated README.md:
  - New "Resources Integration" section with setup guide
  - Updated version to 1.4.0
  - Added integration features to feature list
  - Deployment workflow includes Resources commit/push

### Workflow
**New integrated workflow:**
1. Run analysis: `python main.py --config competitors.json`
2. Reports save to `Resources/ux-analysis/YYYY-MM-DD_page_type/`
3. Resources index auto-updates with new report card
4. Commit and push Resources project to deploy

### Compatibility
- Fully backwards compatible
- Disabling integration: Delete or modify `resources_integration_config.json`
- Reports still work standalone without Resources project

---

## [1.3.3] - 2025-11-26

### Changed
- **🎨 Rebrand to UX Maturity Analysis**: Complete rebrand from "Competitive Intelligence" to "UX Maturity Analysis"
  - All reports now titled "UX Maturity Report" instead of "Competitive Intelligence Report"
  - Project name: "E-commerce UX Maturity Analysis Agent"
  - Analysis names updated: "Basket Page UX Maturity Analysis", "Product Page UX Maturity Analysis", etc.
  - Focus shifted from competitive intelligence to UX maturity evaluation
  - All future reports automatically use new branding
  - Existing reports retain original branding

- **📁 Project Structure Reorganisation**: Consolidated all user-facing scripts and documentation
  - Moved `reanalyze_screenshots.py` to `scripts/` directory
  - Moved deployment documentation to `docs/deployment/` directory
    - `NETLIFY_DEPLOY.md` → `docs/deployment/NETLIFY.md`
    - `DEPLOY_QUICKSTART.md` → `docs/deployment/QUICKSTART.md`
  - Moved `config.yaml` to `docs/config_reference.yaml` (documentation only)
  - All scripts now in `scripts/`: `reanalyze_screenshots.py`, `generate_index.py`, `deploy_netlify.py`
  - All documentation now in `docs/` with logical subdirectories
  - Updated README to reflect new structure
  - Fixed import paths in moved scripts

### Added
- **🚀 Netlify Deployment Support**: Complete deployment infrastructure for sharing reports
  - `scripts/generate_index.py`: Auto-generates professional dashboard listing all reports
    - Beautiful card-based UI with dates, analysis types, and competitor counts
    - Report titles pulled from config YAML files (e.g., "Basket Page UX Maturity Analysis")
    - UK English formatting throughout
  - `scripts/deploy_netlify.py`: Automated deployment script with CLI support
  - `netlify.toml`: Netlify configuration with optimal caching headers
  - `docs/deployment/NETLIFY.md`: Comprehensive deployment guide (3 deployment methods)
  - `docs/deployment/QUICKSTART.md`: 30-second deployment guide
  - **Deployment Options:**
    - Drag & drop to Netlify (30 seconds, no installation)
    - CLI deployment (automated, repeatable)
    - GitHub auto-deploy (push to deploy)
  - **Dashboard Features:**
    - Lists all reports with formatted dates (e.g., "24 November 2025")
    - Shows proper analysis names from config files
    - Displays competitor counts per report
    - Mobile-responsive design

### Removed
- Deleted unused `VERSION` file (contained outdated version 1.2.1)
  - Version now maintained solely in `src/version.py` (single source of truth)
  - No code referenced the VERSION file

### Documentation
- Created `NAMING_EXPLANATION.md`: Explains how index generator derives report titles from config files
- Created `STRUCTURE_AUDIT.md`: Full audit of project structure with before/after
- Created `REORGANISATION_COMPLETE.md`: Documentation of structure changes
- Created `REBRAND_COMPLETE.md`: Complete rebrand documentation with examples
- Updated README.md:
  - New project structure section
  - Updated all script paths (`scripts/reanalyze_screenshots.py`)
  - UK English spelling (organisation, authorised, analysed)
  - Updated branding to UX Maturity Analysis

### Technical
- UK English adopted throughout codebase (organisation, analyse, authorise)
- Index generator loads analysis names from `criteria_config/*.yaml` files
- Fallback to formatted folder names if config unavailable

## [1.3.2] - 2025-11-25

### Added
- **🔄 Reanalyze Script**: New `reanalyze_screenshots.py` for report regeneration without re-capturing
  - Regenerate HTML/markdown reports from existing screenshots in seconds
  - Smart caching: Reuses existing `analysis.json` files (instant), only re-analyzes missing ones
  - Perfect for testing report design changes, refining criteria, or adding missing competitors
  - Example: `python3 reanalyze_screenshots.py output/audits/2025-11-24_basket_pages`
  - **Use Cases:**
    - Update report template/design (all analyses cached, instant regeneration)
    - Refine analysis criteria (delete analysis.json to force re-analysis)
    - Add missing competitors (only new competitor analyzed, others cached)

### Improved
- **🎨 Advanced HTML Report Filtering**: Complete filtering system overhaul
  - **Dynamic Filter Dropdown**: Only shows competitive position tiers that have competitors
    - Displays count per tier: "Strong Contender (9)", "Vulnerable (2)"
    - Eliminates confusing empty filter options
  - **Real Plotly Chart Integration**: Charts now update dynamically with filters
    - Radar chart: Trace visibility toggled via Plotly.restyle()
    - Bar chart: Trace visibility toggled via Plotly.restyle()
    - Heatmap: Data filtered and redrawn via Plotly.react()
    - Instant visual feedback as you filter
  - **Rankings Table Never Filtered**: Overall Rankings always shows all competitors
    - Filters now only apply to: Competitor cards, Visual charts
    - Rankings provide full competitive landscape view regardless of active filters
  - Combined improvements create seamless, intuitive filtering experience

### Changed
- **📝 Complete README Rewrite**: Comprehensive documentation reflecting full reality
  - Added extensive `reanalyze_screenshots.py` documentation with use cases and examples
  - Updated filtering section to reflect new competitive position-based filtering
  - Clarified what gets filtered (cards, charts) vs what doesn't (rankings table)
  - Added "Why This Tool?" section highlighting key differentiators
  - Reorganized sections for better flow and findability
  - Updated project structure to show reanalyze script
  - Enhanced HTML report documentation with v1.3.2 filtering features

### Removed
- **Code Cleanup**: Removed legacy and redundant code
  - Removed unused `detect_page_type()` function (was imported but never called)
  - Removed stub `HTMLReportGenerator` class from `report_generator.py`
    - Real implementation exists in `html_report_generator.py`
  - Updated imports to reflect removed functions
  - No functional changes, pure code quality improvements

### Technical
- Filter dropdown building logic now scans actual data to populate options
- Plotly filtering uses native API methods for performance
- README reduced from 934 to 900 lines while adding comprehensive reanalyze documentation

## [1.3.1] - 2025-11-24

### Performance
- **⚡ Parallel AI Analysis**: Phase 2 now analyzes all competitors concurrently
  - Changed from sequential to parallel execution using `asyncio.gather()`
  - **8-10x faster** for multi-competitor analyses
  - Example: 10 competitors now analyzed in ~30-45 seconds vs 5 minutes
  - Real-time progress indicators show which competitors completed (✓/✗/⚠)
  - Maintains same quality and error handling
  - No configuration changes needed - automatic speedup

### Added
- **Analysis Context for All Page Types**: Completed dynamic context implementation
  - `homepage_pages.yaml`: E-commerce homepage optimization context
  - `product_pages.yaml`: Product detail page (PDP) conversion context
  - `checkout_pages.yaml`: Checkout optimization & cart abandonment context
  - Each config now has tailored market/domain expertise for AI analysis

### Documentation
- Updated README.md with parallel analysis feature
- Removed "Sequential Analysis" limitation (now resolved)
- Updated roadmap to reflect completed parallel analysis

## [1.3.0] - 2025-11-24

### Added
- **Dynamic Analysis Context System**: AI prompts now adapt to analysis type
  - Added `analysis_context` field to criteria YAML configs
  - Market and domain-specific context injected dynamically into prompts
  - No more hardcoded basket/pet food language - works for any analysis type
  - Example: Homepage analysis gets homepage-specific context, product pages get product-specific context
  - Enables easy creation of new analysis types without code changes
- **Strategic Insights Section**: New executive-focused analysis in HTML reports
  - **Market Leaders**: Top 3 performers with key differentiators
  - **Top 3 Opportunities**: Industry-wide weaknesses (60%+ scoring below 6) with potential gains
  - **Competitive Threats**: Standout strengths from market leaders (9+ scores) with recommended actions
  - **Quick Wins**: Common gaps across competitors with 30-day implementation estimates
  - Positioned before charts section for immediate strategic visibility
- **Overall Rankings Table**: Complete competitive ranking with positioning
  - Rank badges (gold/silver/bronze for top 3)
  - Color-coded scores (green 8+, orange 6-8, red <6)
  - Competitive position labels (Market Leader 8+, Strong Contender 6.5-7.9, Competitive 5-6.4, Vulnerable <5)
  - Key differentiator showing each competitor's strongest criterion
  - Sortable and filterable within HTML report

### Changed
- **Claude Analyzer Architecture**: Completely refactored for flexibility
  - `claude_analyzer.py` now accepts `analysis_context` parameter
  - Removed hardcoded UK pet food/basket-specific language from prompts
  - Generic prompt template that adapts to any page type
  - `analysis_context` passed from config → main.py → analyzer
- **Configuration System**: Enhanced for per-analysis-type customization
  - `config_loader.py` now parses `analysis_context` from YAML files
  - Each analysis type can have its own market/domain expertise context
  - `basket_pages.yaml` updated with UK pet food retail context as example
- **HTML Report Structure**: Reorganized for better strategic flow
  - Executive Summary → Key Insights → **Strategic Insights (NEW)** → **Rankings (NEW)** → Charts → Filters → Competitor Profiles
  - Strategic insights appear before charts for immediate actionability
  - Rankings table provides quick competitive landscape overview

### Removed
- **Score Distribution Chart**: Removed box plot from HTML reports
  - Redundant with existing heatmap visualization
  - Limited additional insight vs other charts
  - Simplifies report and improves load time

### Technical
- Added `_get_strategic_insights()` method to calculate market leaders, opportunities, threats, and quick wins
- Added `_get_rankings_data()` method to generate competitive positioning table
- Updated `AnalysisType` Pydantic model with optional `analysis_context` field
- Updated HTML template with new CSS for strategic insights cards and rankings table
- All strategic calculations based on actual analysis data (no hardcoded samples)

### Documentation
- `config.yaml` is now purely documentation (no longer loaded)
- All active configuration in `criteria_config/*.yaml` files
- Added comprehensive comments explaining `analysis_context` usage

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
