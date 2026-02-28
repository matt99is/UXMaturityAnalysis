# Changelog

All notable changes to the E-commerce UX Maturity Analysis Agent will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.10.0] - 2026-02-28

### Added
- **🖥️ Rich Progress Bar**: Persistent progress bar during analysis in both `main.py` and `reanalyze_screenshots.py`
  - Spinner, competitor count (X/Y), live pass description, elapsed time
  - Description updates: "Pass 1: Observing {name}...", "Pass 2: Scoring {name}..."
- **⏱️ Live Countdown**: 90-second waits between competitors now show live countdown
  - New `_wait_with_countdown()` helper replaces bare `asyncio.sleep()`
  - Progress description ticks each second: "Next: {name} in 87s  •  Ctrl+C to quit"

### Changed
- **🔇 Reduced CLI Noise**: Removed notable states bullet list from console output
  - Summary line (`✓ Observation saved (N notable states)`) retained
  - Removed `[DEBUG] Image dimensions OK` prints from image loader

### Improved
- **✉️ Error Messages**: Clearer, human-readable error messages for analysis failures
  - Distinguishes truncation (`stop_reason == "max_tokens"`) from malformed JSON
  - "Pass 1 truncated — response hit 8000 token limit." instead of raw exception string
  - "Pass 2 malformed JSON (char 13547)." with position for debugging
  - Debug files saved to `output/debug_malformed_json/` for malformed JSON only (not truncation)

### Technical
- `analyze_competitor_from_screenshots` accepts optional `progress` and `task_id` params
- All internal console prints routed through `_print` closure → prevents visual artifacts when called from `reanalyze_screenshots.py` (avoids two-Console conflict)
- `max_tokens` raised: Pass 1 to 8000, Pass 2 to 16000 (claude-sonnet-4-6 supports 64K output)

## [1.9.0] - 2026-02-27

### Changed
- **📁 New Output Structure**: Reports now use type-based URL structure
  - Reports at `/{type}/{date}.html` instead of `/audits/{date}_{type}/`
  - Type directories use kebab-case (e.g., `/basket-pages/`, `/product-pages/`)
  - Screenshots moved to `/{type}/screenshots/{date}/{competitor}/`
  - Legacy `/audits/` structure still supported for backward compatibility

### Added
- **📋 Type Index Pages**: Each analysis type has its own index
  - `/basket-pages/` lists all basket page reports with stats
  - Shows latest vs archived badges
  - Displays competitor count, average score, leader score per report
  - Easy navigation between historical reports

- **🔄 Backward Compatibility**: Both structures work together
  - `generate_index.py` discovers reports from both new and legacy structures
  - Main dashboard shows reports from all sources
  - Smooth migration path for existing deployments

### Technical
- Updated `audit_organizer.py`:
  - New `get_output_dir()` and `get_type_dir()` functions
  - `create_audit_directory_structure()` creates new layout
  - `collect_new_structure_runs()` discovers new format reports
  - Added `get_observation_path()` helper

- Updated `html_report_generator.py`:
  - `generate_report_page()` accepts `analysis_type` and `audit_date` params
  - New `generate_type_index_page()` for type-specific index pages
  - `_prepare_competitor_data()` handles new screenshot paths

- Updated `generate_index.py`:
  - `collect_new_structure_reports()` scans new layout
  - `generate_type_index()` creates per-type index pages
  - `generate_main_index()` combines both structures

### Documentation
- Updated `ARCHITECTURE.md` with new output layout
- Updated `PROJECT_STATE.md` to v1.9.0

## [1.8.0] - 2026-02-27

### Added
- **🚀 Automatic Netlify Deployment:** Reports deploy automatically after analysis
  - `scripts/setup_netlify.py` - One-time configuration wizard
  - Auto-deployment integrated into main.py analysis pipeline
  - Custom domain support: analysis.mattlelonek.co.uk
  - `--no-deploy` flag for manual control
  - Retry logic with exponential backoff for network issues

### Changed
- **📦 Build Configuration:** Added `netlify.toml` for Netlify configuration
  - Specifies `output` as publish directory
  - Configures local dev server

### Documentation
- Updated NETLIFY.md with automatic deployment workflow (Option 3)

## [1.7.0] - 2026-02-26

### Added
- **🎨 Template Partial System**: Jinja2 partials for shared markup
  - Created `templates/partials/` directory for reusable components
  - `_theme_toggle.jinja2`: Desktop theme toggle button
  - `_brand.jinja2`: Shared brand header markup
  - Both `index.html.jinja2` and `report.html.jinja2` now use partials
  - Reduces duplication, easier maintenance

- **📚 Developer Documentation**: Comprehensive onboarding and quick reference guides
  - `docs/ONBOARDING.md`: 40+ sections covering project structure, quick start, how to run analysis, adding new page types, modifying reports, deployment, testing, and troubleshooting
  - `docs/COMMON_TASKS.md`: Quick reference for common tasks (add report type, change colors, modify reports, deploy)
  - Quick reference links added to README.md

- **✅ Code Quality Tooling**: Automated linting and formatting
  - Configured `flake8` for PEP 8 style checking (max-line-length=100)
  - Configured `black` for consistent code formatting
  - Configured `isort` for import organization
  - Pre-commit hooks configured in `.pre-commit-config.yaml`
  - Config files: `.flake8`, `pyproject.toml`

- **📋 Task Tracking System**: PROJECT_TODO.md for API limit recovery
  - Tracks active work with sections, priorities, and estimates
  - Recovery instructions for another AI instance
  - Completed today section for context

### Changed
- **♿ Accessibility Improvements**: WCAG AA compliance
  - Base font size increased to 16px (from smaller)
  - Small text increased to 12px, extra-small to 12px
  - Light theme accent colors darkened for better contrast:
    - Green light: `#16a34a` → `#15803d`
    - Amber light: `#ea580c` → `#c2410c`
    - Red light: `#dc2626` → `#b91c1c`

- **📊 Chart Responsiveness**: Live resize with Plotly.Plots.resize()
  - JavaScript event listener with 100ms debounce
  - Charts automatically resize when window resizes
  - Radar chart legend repositioned (orientation horizontal, below chart)
  - Proper aspect ratios: radar `1/1`, heatmap `4/3`

- **🧱 Report Card Layout**: Fixed class naming conflicts
  - Created `.index-report-card` class for index page
  - Kept `.report-card` for report details pages
  - Separate layouts: index uses flex column, reports use grid

- **🔧 Template System Integration**: generate_index.py now uses Jinja2
  - Replaced hardcoded HTML generation with template rendering
  - Reports properly formatted with expected fields (filename, category, date, scores)
  - Consistent design across all generated pages

### Improved
- **📖 Architecture Documentation**: Comprehensive v1.7.0 section added
  - Theme toggle implementation details
  - Template partials location and usage
  - Responsive design patterns
  - Live chart resize mechanism
  - Accessibility improvements (WCAG AA compliance)

### Technical
- CSS architecture: 8 SCSS partials organised by concern
  - `_variables.scss`: Design tokens (colors, fonts, spacing, breakpoints)
  - `_base.scss`: Reset and base element styles
  - `_layout.scss`: Grid and layout patterns
  - `_components.scss`: Reusable UI components
  - `_sections.scss`: Page sections (charts, metrics, insights, rankings)
  - `_competitors.scss`: Competitor-specific styles
  - `_mobile.scss`: Mobile responsive overrides
  - `main.scss`: Entry point importing all partials

- Theme toggle pattern:
  - Jinja2 partial: `templates/partials/_theme_toggle.jinja2`
  - Usage: `{% include 'partials/_theme_toggle.jinja2' %}`
  - JavaScript persistence with localStorage

- Linting workflow:
  - Pre-commit hooks run flake8, black, isort before commit
  - `pyproject.toml` ensures consistent formatting
  - Max line length: 100 (accommodates JSON-heavy code)

### Documentation
- Updated `ARCHITECTURE.md` with v1.7.0 features and patterns
- Updated `README.md` with onboarding links and new development workflow
- Added comprehensive developer onboarding documentation
- Added quick reference for common tasks

## [1.6.0] - 2026-02-24

### Added
- **🧭 Two-pass analysis pipeline** for auditable evidence-first scoring
  - Pass 1 observes screenshots and stores `observation.json` per competitor
  - Pass 2 scores criteria from observation text (no image payload), with evidence citation per criterion
  - `notable_states` from observation are surfaced in console output and enforced in scoring prompts

- **📑 Observation metadata in reports**
  - HTML competitor profiles now show flagged anomalies and per-criterion evidence callouts
  - Markdown competitor sections now include a "Flagged anomalies (observation pass)" block

- **🗂️ Project-level reports index**
  - New auto-generated `output/index.html` lists all audit runs and links to report files
  - Index also includes legacy flat report files when present

### Changed
- **📁 Output location is now project-local by default and enforced**
  - Audit runs are written to `output/audits/` under this repository
  - Report discovery/index generation now reflects in-repo output layout

- **🔌 Resources auto-publish runtime integration retired from default flow**
  - Runtime output no longer redirects to external Resources project paths
  - Legacy helper scripts remain in `scripts/` for historical/manual use

- **🤖 Model selection defaults now respect environment config**
  - `--model` remains highest priority
  - If omitted, `CLAUDE_MODEL` (or `claude_model`) from `.env` is used
  - Falls back to `claude-sonnet-4-5-20250929` only when not configured

- **⏱️ Two-pass rate-limit timing**
  - Delay between sequential analyses increased from 60s to 90s to accommodate two-pass token budget

### Improved
- **♻️ Reanalysis controls**
  - `scripts/reanalyze_screenshots.py` supports `--force-observe` (rerun pass 1) and `--force` (rerun both passes)
  - Existing `observation.json` can be reused or regenerated per run intent

### Fixed
- **🧾 Index/report discoverability**
  - Legacy flat-output report files are now represented in generated index output
  - Legacy index generation points to the same directory legacy reports are written to

### Documentation
- Updated README, deployment docs, and environment examples to reflect:
  - two-pass analysis flow
  - local output/index behavior
  - model configuration precedence
  - current delay and reanalysis flags

## [1.5.0] - 2026-01-12

### Changed
- **⏱️ Sequential Analysis**: Reverted to sequential processing to respect API rate limits
  - Changed from batched parallel back to one-at-a-time analysis
  - Rate limit: 8,000 output tokens/minute (each analysis generates ~6,000 tokens)
  - 60-second delay between analyses to stay within limits
  - Reliable execution without rate limit errors
  - Trade-off: ~1 minute per competitor vs instant parallel (but parallel was hitting limits)

### Improved
- **🎯 Dark Pattern Detection**: Significantly enhanced subscription pre-selection detection
  - Added explicit visual indicator checks (filled radio buttons, checked boxes)
  - CRITICAL scoring guidance: Dark patterns now score 0-3/10 (severe penalty)
  - Enhanced evaluation points with specific UI state detection
  - Added UK CMA dark pattern guidance and regulatory context
  - Subscription criterion description emphasizes dark pattern detection
  - Claude explicitly instructed to look for filled circles (•) vs empty circles (○)
  - Flagged as severe vulnerabilities that may violate consumer protection law

- **📊 Product Page Criteria Enhancement**: Updated all criteria with 2025-2026 research
  - **Product Imagery**: Added descriptive text/graphics, in-use imagery, mobile gesture support
  - **Add to Cart**: Added unique styling check, minimal clutter check, post-add feedback
  - **Pricing Clarity**: Added price per unit, shipping cost visibility
  - **Product Information**: Added 3-5 feature highlights, specs table, use cases, avoids horizontal tabs
  - **Reviews & Social Proof**: Added ratings distribution, verification badges, site responses, reviewer context
  - **Trust & Security**: Completely overhauled with badge counts, HTTPS checks, design quality, third-party ratings
  - **Mobile Optimization**: Added gesture support, touch target sizes, above-fold critical info
  - All criteria weights adjusted for competitive exploitation strategy

- **🆕 Express Payment Criterion**: Added new criterion for product page express checkout
  - Weight: 1.7 (high priority - most sites don't offer this)
  - Evaluates Apple Pay, Google Pay, PayPal Express, Amazon Pay, Shop Pay buttons
  - Checks for "Buy Now" immediate purchase options (bypasses cart)
  - Focuses only on product page elements (not checkout flow)
  - Research-backed: 2x faster purchase completion with express payment

### Added
- **Sequential Retry Logic**: Failed analyses now retry sequentially
  - 60-second delays between retries
  - Clear progress indicators: "Retry 1/7: competitor_name"
  - Saves successful retries to analysis.json
  - Same rate-limit-safe approach as main analysis

### Fixed
- **🐛 HTML Report Path Issue**: Fixed HTML reports not generating in Resources folder
  - HTML generator now correctly writes to audit_root directory
  - Works with both local output and Resources integration paths
  - Temporary output_dir override ensures correct file placement

- **🐛 Plotly Heatmap Not Showing**: Fixed missing Plotly CDN in HTML reports
  - Changed from `include_plotlyjs=False` to `include_plotlyjs='cdn'`
  - Heatmap now loads correctly in all browsers
  - No longer requires separate Plotly script tag

- **🐛 Retry Logic Structure**: Fixed TypeError when retrying failed competitors
  - Updated to correctly access nested competitor_info dictionary
  - Now uses `competitor_info['screenshots']` instead of direct path concatenation
  - Matches structure from `create_audit_directory_structure()`

### Technical
- Reduced `max_tokens` from 8192 to 6000 to stay within output token limits
- Updated `claude_analyzer.py` to use `AsyncAnthropic` for true async support
- All retry logic now uses sequential processing with 60s delays
- Updated `reanalyze_screenshots.py` to match sequential processing pattern
- BATCH_SIZE = 1, DELAY = 60s across all analysis paths

### Documentation
- Updated CHANGELOG.md with v1.5.0 changes
- README.md updated to reference report regeneration script
- Clarified rate limit constraints and performance expectations

### Performance Notes
**Timing for 10 Competitors:**
- Sequential: ~15-17 minutes (1 min per competitor + 60s delays)
- Previously attempted parallel: Rate limit errors
- Trade-off accepted: Reliability over speed

**Rate Limit Compliance:**
- Input tokens: 30,000/min (plenty of headroom)
- Output tokens: 8,000/min (1 analysis per minute = 6,000 tokens, safe)

---

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
