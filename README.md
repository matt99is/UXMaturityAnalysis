# E-commerce UX Competitive Intelligence Agent

**Version:** 1.3.1
**Status:** Production Ready
**Python:** 3.9+

A Python tool that systematically analyzes competitor e-commerce pages and generates competitive intelligence reports using Claude AI and browser automation.

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 📋 Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Quick Start](#quick-start)
- [How It Works](#how-it-works)
- [Usage Examples](#usage-examples)
- [Configuration](#configuration)
- [Output Structure](#output-structure)
- [Architecture & Extensibility](#architecture--extensibility)
- [Versioning](#versioning)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

This tool automates competitive UX analysis for e-commerce sites by:

1. Capturing screenshots of competitor pages (desktop & mobile viewports) in interactive mode
2. Analyzing UX against research-backed criteria (Baymard Institute, Nielsen Norman Group)
3. **Generating competitive intelligence reports** focused on threats, opportunities, and market positioning
4. Providing strategic insights for competitive differentiation

**Key Features:**
- ✨ **Multi-Page-Type Support**: Analyze homepages, product pages, basket pages, and checkout flows
- ⚡ **Blazing Fast Parallel Analysis**: Analyzes all competitors concurrently (8-10x faster than sequential)
- 🎤 **Interactive Analysis**: You control the browser - navigate, close popups, then capture
- 🔄 **Retry Option**: Not happy with screenshots? Retry before analyzing
- 🎯 **Competitive Intelligence Focus**: Reports frame findings as competitive advantages vs vulnerabilities
- 🤖 **AI-powered analysis** using Claude's vision capabilities
- 📊 **Research-backed evaluation** from Baymard Institute and Nielsen Norman Group
- 🔧 **Extensible architecture** - easily add new page types via YAML config
- 📱 Desktop and mobile viewport analysis
- 📁 **Manual mode**: Upload your own screenshots for heavily bot-protected sites
- ⌨️ **Cancel anytime**: Press Ctrl+C or skip individual competitors

## Quick Start

### Prerequisites

- Python 3.10 or higher
- Anthropic API key ([get one here](https://console.anthropic.com/))

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd BenchmarkAgent
```

2. Install dependencies:
```bash
pip3 install -r requirements.txt
```

3. Install Playwright browsers:
```bash
python3 -m playwright install chromium
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

### Basic Usage

**Run with a config file** (recommended):

```bash
python3 main.py --config competitors.json
```

You'll be prompted to select analysis type, then the tool opens a browser for each competitor site. You navigate, close popups, and press Enter to capture screenshots.

**Specify analysis type** (skip the prompt):

```bash
python3 main.py --config competitors.json --analysis-type product_pages

# Available types: homepage_pages, product_pages, basket_pages, checkout_pages
```

**Manual mode** (for heavily bot-protected sites):

```bash
# Provide your own screenshots
python3 main.py --manual-mode --screenshots-dir ./screenshots --config competitors.json
```

---

## How It Works

The tool follows this simple, reliable workflow:

1. **Select Analysis Type** - Interactive prompt shows all available types
   - Homepage analysis
   - Product page analysis
   - Basket/cart analysis
   - Checkout flow analysis

2. **Interactive Capture Mode** - For each competitor:
   - Browser opens to the URL
   - You navigate, close popups, accept cookies
   - Press Enter when ready → Captures desktop & mobile screenshots
   - Choose: Continue (Y) / Retry (R) / Skip (S)

3. **AI Analysis** - Claude analyzes screenshots against research-backed criteria

4. **Competitive Report** - Generates intelligence report with market positioning

**Two Modes Available:**
- 🌐 **Interactive Mode** (default): Browser opens, you control, tool captures
- 📁 **Manual Mode** (`--manual-mode`): You provide pre-captured screenshots

**Control Options:**
- Press `Ctrl+C` anytime to exit
- Type 'R' to retry screenshot capture
- Type 'S' to skip a competitor

---

## Usage Examples

### Basic Usage (Interactive Mode)

**Run the analysis - you'll be prompted to select the type:**

```bash
python3 main.py --config competitors.json
```

**What happens:**

1. **Analysis Type Selection Prompt:**
```
📋 Select Analysis Type:

#   Analysis Type    Description
1   Basket/Cart      Analyze shopping cart pages
2   Checkout Flow    Analyze checkout process
3   Homepage         Analyze homepage UX and layout
4   Product Pages    Analyze product detail pages

Select analysis type (1-4):
```

2. **Interactive Capture** - For each competitor:
   - Browser opens to the URL in visible mode
   - You see: *"Navigate to the page and prepare for screenshot"*
   - Close popups, accept cookies, ensure page loaded
   - Press Enter when ready
   - Tool captures desktop & mobile screenshots
   - Prompt: `Continue? ([Y]es / [r]etry / [s]kip):`
     - **Y or Enter** → Continue to next competitor
     - **R** → Retry screenshots for this site
     - **S** → Skip this competitor entirely

3. **Analysis & Report** - Claude analyzes all screenshots and generates competitive intelligence report

### Skip the Prompt (Specify Analysis Type)

If you already know which analysis type you need:

```bash
python3 main.py --analysis-type product_pages --config competitors.json

# Available types: homepage_pages, product_pages, basket_pages, checkout_pages
```

### Analyze Multiple Competitors
```bash
python3 main.py --urls \
  https://www.competitor1.com \
  https://www.competitor2.com \
  https://www.competitor3.com
```

### Custom Configuration File
```bash
python3 main.py --config competitors.json
```

### Specify Claude Model
```bash
python3 main.py --model claude-sonnet-4-5-20250929 --config competitors.json
```

### Manual Mode (For Bot-Protected Sites) 🆕 v1.1.0

For sites with strong bot detection (Amazon, eBay, etc.), use manual screenshot mode:

```bash
# Step 1: Manually capture screenshots
# - Navigate to competitor pages in your browser
# - Save screenshots as: competitor_desktop.png, competitor_mobile.png

# Step 2: Analyze
python3 main.py --manual-mode --screenshots-dir ./my-screenshots --urls https://amazon.com
```

**When to use manual mode:**
- Sites block automated browsers (Access Denied, CAPTCHA)
- Pages requiring login/authentication
- Maximum control over captured state
- One-off competitive audits

## Configuration

### Competitors Configuration

Create a `competitors.json` file:

```json
{
  "competitors": [
    {
      "name": "competitor1",
      "url": "https://www.competitor1.com/basket"
    },
    {
      "name": "competitor2",
      "url": "https://www.competitor2.com/cart"
    }
  ]
}
```

### UX Analysis Criteria

Criteria are defined in YAML files in the `criteria_config/` directory. Each page type has its own criteria tailored to that context:

**Available Page Types:**
- **`homepage_pages.yaml`** - 8 criteria (Value Proposition, Navigation, Hero Section, Trust Signals, Search, Mobile, Content Hierarchy, Performance)
- **`product_pages.yaml`** - 10 criteria (Product Imagery, Add to Cart CTA, Pricing Display, Reviews, Subscription Options, Delivery Info, Trust Signals, Cross-sell, Mobile, etc.)
- **`basket_pages.yaml`** - 11 criteria (Shipping Cost Transparency, Subscription Options, Basket Summary, Product Information, Mobile Layout, Delivery Estimates, Express Checkout, Quantity Management, CTA Buttons, Cross-sell, Payment & Trust)
- **`checkout_pages.yaml`** - 8 criteria (Form Design, Progress Indicators, Guest Checkout, Payment Variety, Error Prevention, Order Summary, Trust/Security, Mobile)

**To customize criteria for a page type:**
1. Open the relevant YAML file in `criteria_config/`
2. Edit criteria definitions, weights, evaluation points, and benchmarks
3. Optionally add `analysis_context` for market/domain-specific AI analysis
4. Run analysis - changes are applied automatically (no code changes needed!)

**Example criteria structure:**
```yaml
name: "E-commerce Basket Page Analysis - UK Retail"
requires_interaction: true
interaction_prompt: "🛒 Please add 2-3 items to the basket, then press Enter to continue..."
interaction_timeout: 300

# Analysis Context - Market/domain-specific context for AI prompts (NEW in v1.3.0)
analysis_context: |
  **MARKET CONTEXT: UK Pet Food Retail**
  This analysis focuses on basket/cart pages for UK pet food retailers. Key considerations:
  - Subscription/auto-delivery is critical (Pets at Home VIP, Chewy Autoship model)
  - Heavy products make shipping costs and free delivery thresholds highly sensitive
  - Mobile traffic dominates (65%+ of UK pet supply shopping)

  **Domain Expertise:**
  - Baymard Institute research on cart abandonment
  - UK pet retail market dynamics (subscription models, delivery expectations)

viewports:
  - name: "desktop"
    width: 1920
    height: 1080
  - name: "mobile"
    width: 375
    height: 812

criteria:
  - id: "shipping_cost_transparency"
    name: "Shipping Cost & Free Delivery Threshold"
    weight: 10
    description: "Visibility of delivery costs and free shipping thresholds on basket page"
    evaluation_points:
      - "Are delivery costs displayed on basket page (not hidden until checkout)?"
      - "Is free shipping threshold clearly shown (e.g., 'Add £5 for free delivery')?"
    benchmarks:
      - source: "Baymard Institute"
        finding: "48% abandon due to unexpected shipping costs"
```

**Key Features:**
- **Dynamic AI Context** (v1.3.0): The `analysis_context` field lets you provide market-specific expertise that adapts Claude's analysis
- **Automatic Integration**: No code changes needed - just edit YAML and run
- Each criterion is evaluated against Baymard Institute and Nielsen Norman Group benchmarks

## Output Structure

The tool organizes output by audit run with hierarchical structure:

```
output/audits/
└── 2025-11-20_homepage_pages/          # Audit folder
    ├── _comparison_report.md            # Markdown competitive intelligence report
    ├── _comparison_report.html          # Interactive HTML report with charts
    ├── _audit_summary.json              # Audit metadata
    ├── nike/                            # Competitor folder
    │   ├── screenshots/
    │   │   ├── desktop.png              # Simple filenames
    │   │   └── mobile.png
    │   └── analysis.json                # Individual analysis
    ├── adidas/
    │   ├── screenshots/
    │   │   ├── desktop.png
    │   │   └── mobile.png
    │   └── analysis.json
    └── underarmour/
        ├── screenshots/
        └── analysis.json
```

### Competitive Intelligence Report

The `_comparison_report.md` includes:

**1. Market Landscape Analysis**
- Feature adoption rates across competitors
- Competitive clusters (Leaders, Contenders, Laggards)
- Market UX maturity scoring

**2. Feature Adoption Heatmap**
- Visual matrix with ✅ Strong / ⚠️ Moderate / ❌ Weak indicators
- Quick identification of market strengths/weaknesses

**3. Strategic Insights**
- **White Space Opportunities**: Underperforming features across market
- **Best-in-Class Reference**: Market leaders by specific criteria
- **Market Trends**: High-variance features and fragmentation analysis

**4. Competitor Profiles**
Each competitor analyzed with:
- Competitive position (Market Leader / Strong Contender / Vulnerable)
- **Competitive Advantages** (threats to counter)
- **Exploitable Vulnerabilities** (opportunities to target)
- Feature performance with competitive status indicators

**5. Competitive Positioning Map**
Visual UX maturity spectrum showing relative positioning

**6. Strategic Recommendations**
- **Table Stakes**: Must-have features to remain competitive
- **Differentiation Opportunities**: Market gaps to exploit
- **Emerging Threats**: Areas where competitors are pulling ahead

**7. Methodology Appendix**

### Interactive HTML Report

The tool also generates an **interactive HTML report** (`_comparison_report.html`) with rich visualizations and filtering capabilities. Understanding the report sections:

#### **1. Executive Summary**
Four key metrics at the top of the report:
- **Competitors Analyzed**: Total number of successfully analyzed competitors
- **Average Score**: Mean UX score across all competitors (0-10 scale)
- **Top Score**: Highest performing competitor and their score
- **Lowest**: Weakest performing competitor and their score

**Key Insights Box** highlights:
- 🏆 **Market Leader**: Competitor with highest overall score
- 📊 **Most Consistent**: Competitor with most balanced performance across criteria
- 💪 **Industry Strength**: Criterion where the market performs best overall
- ⚠️ **Market Vulnerability**: Criterion where all competitors struggle (opportunity to differentiate)

#### **2. Strategic Insights** 🆕 v1.3.0

Four executive-focused insight cards positioned for immediate strategic visibility:

**Market Leaders Card**
- Top 3 competitors by overall score
- Key differentiator for each (their strongest criterion)
- Helps identify who to benchmark against

**Top Opportunities Card**
- Industry-wide weaknesses (60%+ scoring below 6)
- Percentage of market struggling with each criterion
- Potential score gain if you excel
- Example: "Subscription UX - 60% of market scores below 5. Potential: +2.5pts vs avg competitor"

**Competitive Threats Card**
- Standout strengths from market leaders (9+ scores)
- Specific competitor + their exceptional capability
- Recommended action to counter the threat
- Example: "Pets at Home: Subscription UX (9.5/10) - Action: Must match subscription prominence"

**Quick Wins Card**
- Common gaps across 60%+ of competitors
- Criteria where most competitors score below 6
- Est. 30-day implementation timeframe
- Estimated impact: "+1.5 points overall score, +8-12% conversion"

**How to Use:**
- Strategic planning: Identify differentiation opportunities (Top Opportunities)
- Competitive positioning: Understand who leads where (Market Leaders, Threats)
- Prioritization: Focus on Quick Wins for immediate gains
- Executive presentations: Use these 4 cards for concise strategic summary

#### **3. Overall Rankings** 🆕 v1.3.0

Complete competitive ranking table showing all competitors:

**Columns:**
- **Rank**: Badge (🥇 Gold, 🥈 Silver, 🥉 Bronze for top 3)
- **Competitor**: Company name
- **Overall Score**: Color-coded (🟢 Green 8+, 🟠 Orange 6-8, 🔴 Red <6)
- **Competitive Position**: Automatic classification
  - Market Leader (8.0+): Significantly above average
  - Strong Contender (6.5-7.9): At or near average
  - Competitive (5.0-6.4): Below average but viable
  - Vulnerable (<5.0): Significantly behind
- **Key Differentiator**: Each competitor's strongest criterion

**How to Use:**
- Quick competitive landscape overview
- Identify your relative position in the market
- See where competitors differentiate
- Share with stakeholders for instant understanding

#### **4. Visual Analysis Charts**

**Radar Chart - Competitive UX Comparison**
- Shows all competitors overlaid on same axes
- Each axis = one UX criterion
- Larger area = better overall performance
- Use to: Quickly identify who leads/lags on specific criteria

**Heatmap - Feature Adoption Matrix**
- Rows = Competitors, Columns = Criteria
- Color coding: 🟢 Green (8-10) → 🟡 Yellow (4-7) → 🔴 Red (0-3)
- Numbers show exact scores
- Use to: Spot patterns and gaps across the competitive landscape

**Bar Chart - Top Performers by Criteria**
- Shows which competitor scores highest on each criterion
- Use to: Identify best-in-class references for each UX element

#### **5. Filter & Search Panel**

Interactive controls to explore the data:
- **Search Competitor**: Type name to filter competitor cards
- **Minimum Score**: Slider (0-10) to show only high-performing competitors
- **Competitive Status**: Filter by advantages/vulnerabilities/parity
- **Reset Filters**: Clear all filters to see full dataset

Filter count shows: "Showing X of Y competitors"

#### **6. Competitor Profiles**

Each competitor card shows:

**Competitive Position Tier** (badge at top):
- 🟢 **Market Leader**: Score significantly above average (tier 1)
- 🟡 **Strong Contender**: Score at or near average (tier 2)
- 🔴 **Vulnerable**: Score below average (tier 3)

**Performance by Criteria** table with three columns:
1. **Criterion Name**: The UX element being evaluated
2. **Status Badge**: Competitive intelligence label
   - 🟢 **Advantage**: Scores above market average on this criterion (competitive threat)
   - 🟡 **Parity**: Scores at market average (table stakes)
   - 🔴 **Vulnerability**: Scores below market average (exploitable weakness)
3. **Score**: Numerical score (0-10) with color coding

**Understanding Status Labels:**
- **Advantage** doesn't mean "good" - it means "better than competitors" (even a 7/10 can be an advantage if everyone else scores 5/10)
- **Vulnerability** doesn't mean "bad" - it means "worse than competitors" (even a 7/10 can be a vulnerability if everyone else scores 9/10)
- **Status is relative to the competitive set**, not absolute benchmarks

**Screenshots Section**:
- Desktop and mobile viewport screenshots
- Click any screenshot to open **lightbox** (full-screen view)
- ESC key or click outside to close lightbox
- Annotated screenshots show top strengths (green badges) and weaknesses (red badges)

**Strategic Insights**:
- Competitive positioning summary
- Key differentiator (if any)
- Links to detailed findings in individual analysis JSON

#### **7. Interactive Features**

**Lightbox Gallery**:
- Click any screenshot → Full-screen modal opens
- Shows competitor name and viewport (desktop/mobile)
- ESC key or click backdrop to close
- Prevents page scroll when open

**Real-time Filtering**:
- All filters work instantly (no page reload)
- Combine multiple filters (search + score + status)
- Results update live as you type/adjust sliders

**Responsive Design**:
- Report adapts to screen size
- Mobile-friendly layout
- Charts resize for readability

#### **How to Use the Report**

**For Strategic Planning:**
1. Start with Strategic Insights → Get immediate actionable intelligence
2. Review Top Opportunities → Identify differentiation areas
3. Check Overall Rankings → Understand competitive landscape
4. Use Heatmap → Spot patterns and white space

**For Competitive Benchmarking:**
1. Check Overall Rankings table → See relative positions
2. Review Market Leaders card → Identify who to benchmark
3. Look at Competitive Threats → Understand what you're up against
4. Use Search filter → Deep dive on specific competitor

**For UX Prioritization:**
1. Quick Wins card → Immediate 30-day priorities
2. Top Opportunities card → Medium-term differentiation plays
3. Industry Strength insight → These are table stakes
4. Market Vulnerability insight → Long-term leadership areas

**For Executive Presentations:**
1. Strategic Insights 4-card summary → Concise strategic story
2. Overall Rankings table → Competitive position at a glance
3. Radar Chart → Visual competitive positioning
4. Screenshots with annotations → Specific examples

### Individual Competitor Analysis

Each competitor gets `analysis.json` with:
- Competitive position assessment
- Criterion scores with competitive status
- Competitive advantages (threats)
- Exploitable vulnerabilities (opportunities)
- Unmet user needs identified

## Architecture & Extensibility

This POC is designed for easy extension to other page types and analysis scenarios:

### Extension Points

#### 1. Adding New Page Type Analysis

To analyze different page types, simply add a YAML file to `criteria_config/`:

**Example:** `criteria_config/landing_pages.yaml`

```yaml
name: "Landing Page Analysis"
requires_interaction: false
viewports:
  - name: "desktop"
    width: 1920
    height: 1080
  - name: "mobile"
    width: 375
    height: 812

criteria:
  - id: "hero_messaging"
    name: "Hero Messaging Clarity"
    weight: 1.8
    description: "Clarity and impact of main value proposition"
    evaluation_points:
      - "Clear primary message"
      - "Benefit-focused copy"
      - "Strong call-to-action"
    benchmarks:
      - source: "Nielsen Norman Group"
        finding: "Users decide in 10 seconds if page is relevant"
  # ... add more criteria
```

2. Run analysis with `--analysis-type` flag:
```bash
python3 main.py --analysis-type landing_pages --config competitors.json
```

**No code changes required!** The system automatically:
- Loads your new YAML config
- Makes it available as an analysis type option
- Generates competitive intelligence reports using your criteria

#### 2. Supported Page Types

Out of the box, the tool includes:

- **`homepage_pages`**: Homepage analysis (8 criteria)
- **`product_pages`**: Product detail pages (9 criteria)
- **`basket_pages`**: Shopping cart pages (10 criteria)
- **`checkout_pages`**: Checkout flow (8 criteria, requires interaction)

Each optimized with page-specific UX criteria and benchmarks.

#### 3. Adding Multi-Step Journeys

Future enhancement to support navigation flows:

```yaml
navigation:
  steps:
    - url: "{homepage}"
    - action: "click"
      selector: ".product-link"
    - action: "click"
      selector: ".add-to-basket"
```

The `JourneyCapture` class in `src/analyzers/screenshot_capture.py` provides the framework for this.

#### 4. Customizing Analysis Prompts

The `ClaudeUXAnalyzer` class (`src/analyzers/claude_analyzer.py`) builds prompts dynamically from config criteria, making it work with any analysis type.

#### 5. Adding New Output Formats

Extend `ReportGenerator` class (`src/utils/report_generator.py`):

```python
class HTMLReportGenerator(ReportGenerator):
    def generate_html_report(self, analysis_results):
        # Implementation here
        pass
```

### Project Structure

```
BenchmarkAgent/
├── main.py                          # Main entry point & orchestration
├── config.yaml                      # Legacy config (backward compatibility)
├── criteria_config/                 # ✨ Page-type-specific criteria
│   ├── homepage_pages.yaml          #    Homepage UX criteria
│   ├── product_pages.yaml           #    Product page criteria
│   ├── basket_pages.yaml            #    Basket/cart criteria
│   └── checkout_pages.yaml          #    Checkout flow criteria
├── requirements.txt                 # Python dependencies
├── .env.example                     # Environment variables template
├── competitors.example.json         # Example competitor config
├── src/
│   ├── config_loader.py            # Load criteria from YAML files
│   ├── analyzers/
│   │   ├── screenshot_capture.py   # Playwright browser automation + stealth
│   │   └── claude_analyzer.py      # Claude API + competitive intelligence prompts
│   └── utils/
│       ├── report_generator.py     # Competitive intelligence reports
│       ├── audit_organizer.py      # Hierarchical output organization
│       ├── html_report_generator.py # Interactive HTML reports with charts
│       └── screenshot_annotator.py  # Screenshot annotations
└── output/audits/                   # ✨ Organized by audit run
    └── {date}_{analysis_type}/      #    Audit folder
        ├── _comparison_report.md    #    Competitive intelligence report
        ├── _audit_summary.json      #    Audit metadata
        └── {competitor}/            #    Competitor folders
            ├── screenshots/         #    Screenshots
            └── analysis.json        #    Individual analysis
```

## Current Limitations

Some intentional limitations in the current implementation:

1. **Single URL per Competitor**: Currently analyzes one URL per competitor. Multi-step journeys (e.g., homepage → product → basket) are architecturally supported but not yet implemented.

2. **Screenshot-Only Analysis**: Currently analyzes visual screenshots only. Could be enhanced to include DOM/HTML analysis for additional technical insights (accessibility, performance metrics, etc.).

## Use Cases

This tool is designed for:

- **E-commerce UX Teams**: Automate competitive UX analysis across page types
- **Conversion Optimization**: Identify competitive gaps and opportunities
- **Product Managers**: Benchmark against competitors systematically
- **UX Researchers**: Scale qualitative analysis with AI assistance
- **Agencies**: Deliver competitive intelligence audits faster
- **Strategy Teams**: Market positioning and feature gap analysis

## Technical Details

### Dependencies

- **playwright**: Browser automation for screenshot capture
- **anthropic**: Claude API client for AI analysis
- **pydantic**: Data validation and settings management
- **pyyaml**: Configuration file parsing
- **python-dotenv**: Environment variable management
- **rich**: Enhanced console output

### Environment Variables

Configure in `.env`:

```bash
# Required
ANTHROPIC_API_KEY=your_api_key_here

# Optional (defaults provided)
CLAUDE_MODEL=claude-sonnet-4-5-20250929
VIEWPORT_WIDTH=1920
VIEWPORT_HEIGHT=1080
MOBILE_VIEWPORT_WIDTH=375
MOBILE_VIEWPORT_HEIGHT=812
```

## Roadmap

**Recently Completed** ✅
- [x] ⚡ Parallel AI analysis (v1.3.1) - 8-10x faster analysis phase
- [x] Dynamic analysis context system (v1.3.0)
- [x] Strategic insights and rankings (v1.3.0)
- [x] Interactive HTML reports with embedded screenshots (v1.2.0)
- [x] Screenshot annotations with visual findings (v1.2.0)
- [x] Real-time filtering and search (v1.2.0)

**Future enhancements planned:**

- [ ] Multi-step journey support (homepage → product → add to cart → basket)
- [ ] HTML/DOM analysis alongside screenshots
- [ ] Time-series analysis (track competitor changes over time)
- [ ] Export to CSV/Excel formats
- [ ] Integration with analytics tools (GA4, ContentSquare)
- [ ] API endpoints for programmatic access
- [ ] Scheduled automated audits

## Versioning

This project uses [Semantic Versioning](https://semver.org/):
- **MAJOR** version for incompatible API changes
- **MINOR** version for added functionality in a backward compatible manner
- **PATCH** version for backward compatible bug fixes

**Current Version:** 1.3.1

### Version History

**v1.3.1 (2025-11-24)** - Performance Optimization & Context Completion
- ⚡ **Parallel AI analysis** - 8-10x faster Phase 2 execution using `asyncio.gather()`
- ⚡ Real-time progress indicators (✓/✗/⚠) for parallel analysis
- ✨ **Completed analysis context** for all page types (homepage, product, checkout)
- 📝 Removed "Sequential Analysis" limitation from documentation

**v1.3.0 (2025-11-24)** - Dynamic Analysis Context & Strategic Insights
- ✨ **Dynamic analysis context system** - AI prompts adapt to page type via `analysis_context` YAML field
- ✨ **Strategic Insights section** - Market leaders, opportunities, threats, and quick wins
- ✨ **Overall Rankings table** - Complete competitive positioning with rank badges
- 🎨 Removed score distribution chart (redundant with heatmap)
- 🔧 Refactored Claude analyzer for maximum flexibility across analysis types
- 📝 Updated configuration system for per-analysis-type context customization

**v1.2.1 (2025-11-21)** - Retry Mechanism & Bug Fixes
- ✨ Interactive retry prompt for failed analyses
- 🐛 Fixed image format consistency (always JPEG to Claude)
- 🐛 Fixed data structure flattening issues
- 🐛 Fixed HTML report image paths (now relative)
- 🐛 Fixed report generation with zero successes

**v1.2.0 (2025-11-20)** - Interactive HTML Reports & Enhanced UX
- ✨ Interactive HTML reports with Plotly charts (radar, heatmap, bar, box plot)
- ✨ Screenshot annotations with visual badges for strengths/weaknesses
- ✨ Lightbox gallery for full-screen screenshot viewing
- ✨ Real-time filtering and search in HTML reports
- 🐛 Fixed image compression for Claude API 5MB limit
- 🐛 Fixed HTML report generation when competitors fail analysis
- 📊 Automated competitive status labeling (advantage/parity/vulnerability)

**v1.1.0 (2025-11-20)** - Bot Detection Handling
- ✨ Manual screenshot mode for heavily protected sites
- ✨ Enhanced interactive mode with better bot detection prompts
- ✨ Hybrid workflow: automated where possible, manual assist when blocked

**v1.0.0 (2025-11-20)** - Initial Release
- Multi-page-type support (homepage, product, basket, checkout)
- Competitive intelligence reporting framework
- Hierarchical output structure
- Interactive browser-based screenshot capture

See [CHANGELOG.md](CHANGELOG.md) for detailed release notes and upgrade instructions.

### Checking Version

```bash
python3 main.py --version
```

Or programmatically:

```python
from src.version import __version__, get_version_info
print(f"Version: {__version__}")
print(f"Version Info: {get_version_info()}")  # (1, 0, 0)
```

## Research References

This tool's criteria are based on research from:

- **Baymard Institute**: E-commerce UX research and benchmarks
  - 48% of users abandon due to unexpected shipping costs
  - 64% abandon if discount codes are confusing
  - Express checkout can reduce friction by 30-50%

- **Nielsen Norman Group**: Usability and UX best practices
  - Trust signals reduce perceived risk
  - Users want delivery certainty early in flow
  - 61% of mobile users won't return to poorly optimized sites

## Contributing

Contributions are welcome! Here's how you can help:

### Reporting Issues

- Use GitHub Issues for bug reports and feature requests
- Include version information (`python3 main.py --version`)
- Provide steps to reproduce for bugs
- Include sample URLs (that allow scraping) if relevant

### Contributing Code

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests: `python3 tests/verify_setup.py`
5. Update CHANGELOG.md with your changes
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

### Adding New Page Types

The easiest way to contribute is adding new page types:

1. Create a new YAML file in `criteria_config/` (e.g., `search_results.yaml`)
2. Define criteria based on UX research (Baymard, Nielsen Norman)
3. Test with sample URLs using `--analysis-type search_results`
4. Submit PR with examples and documentation

### Code Style

- Follow PEP 8 guidelines
- Use type hints where appropriate
- Add docstrings to functions and classes
- Keep functions focused and modular

## License

MIT License

Copyright (c) 2025 Matthew Lelonek

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## Support

### Documentation

- **Main README**: This file (comprehensive guide)
- **CHANGELOG**: [CHANGELOG.md](CHANGELOG.md) - Version history and upgrade notes
- **Sample Output**: [docs/SAMPLE_OUTPUT.md](docs/SAMPLE_OUTPUT.md) - Example markdown report
- **Demo HTML Report**: [docs/DEMO_REPORT.html](docs/DEMO_REPORT.html) - Interactive HTML report with charts
- **Architecture**: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) - Technical design
- **Bot Detection Guide**: [docs/BOT_DETECTION_GUIDE.md](docs/BOT_DETECTION_GUIDE.md) - Handling protected sites
- **Setup Verification**: `tests/verify_setup.py` - Validate your installation

### Getting Help

1. **Check Documentation**: Review README and docs folder
2. **View Demo Report**: Open `docs/DEMO_REPORT.html` in browser to see example output
3. **Run Diagnostics**: `python3 tests/verify_setup.py`
4. **Check Version**: `python3 main.py --version`
5. **Review Examples**: See usage examples in README
6. **Open Issue**: GitHub Issues with version info and details

### Community

- Report bugs via GitHub Issues
- Request features via GitHub Issues
- Contribute via Pull Requests
- Share your use cases and results

---

## Acknowledgments

**Built with:**
- Python 3.9+
- [Playwright](https://playwright.dev/) - Browser automation
- [Claude AI (Anthropic)](https://www.anthropic.com/) - AI-powered analysis
- [Pydantic](https://pydantic-docs.helpmanual.io/) - Data validation
- [Rich](https://rich.readthedocs.io/) - Terminal UI

**Research Sources:**
- [Baymard Institute](https://baymard.com/) - E-commerce UX research
- [Nielsen Norman Group](https://www.nngroup.com/) - Usability guidelines

**Author:** Matthew Lelonek

---

**⭐ If you find this tool useful, please star the repository!**
