# E-commerce UX Maturity Analysis Agent

**Version:** 1.6.0
**Status:** Production Ready
**Python:** 3.9+

A Python tool that systematically analyses competitor e-commerce pages and generates UX maturity reports using Claude AI and browser automation.

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Quick Start](#quick-start)
- [How It Works](#how-it-works)
- [Usage Examples](#usage-examples)
- [Reanalyze Script](#reanalyze-script)
- [Configuration](#configuration)
- [Output Structure](#output-structure)
- [Interactive HTML Reports](#interactive-html-reports)
- [Reports Index](#reports-index)
- [Architecture & Extensibility](#architecture--extensibility)
- [Technical Details](#technical-details)
- [Roadmap](#roadmap)
- [Versioning](#versioning)
- [License](#license)

---

## Overview

This tool automates competitive UX analysis for e-commerce sites by:

1. **Capturing screenshots** of competitor pages (desktop & mobile viewports) in interactive mode
2. **Analyzing UX** against research-backed criteria (Baymard Institute, Nielsen Norman Group)
3. **Generating UX maturity reports** focused on threats, opportunities, and market positioning
4. **Providing strategic insights** for competitive differentiation

### Why This Tool?

- **🎯 Strategic Focus**: Reports frame findings as competitive advantages vs vulnerabilities
- **🔄 Reanalysis Ready**: Regenerate reports from cached screenshots without re-capturing
- **📊 Interactive Reports**: Rich HTML reports with charts, filtering, and annotated screenshots
- **🎤 Interactive Control**: You control the browser - navigate, close popups, then capture
- **🔧 Extensible**: Add new page types via YAML config (no code changes needed)
- **🤖 AI-powered**: Claude Sonnet with environment-configurable model defaults
- **⚖️ Rate Limit Compliant**: Sequential analysis ensures reliable operation within API limits

---

## Key Features

### Core Capabilities
- ✨ **Multi-Page-Type Support**: Analyze homepages, product pages, basket pages, and checkout flows
- ⚖️ **Sequential AI Analysis**: Rate limit compliant processing (~1 minute per competitor)
- 🎤 **Interactive Capture Mode**: You control the browser - navigate, close popups, then capture
- 🔄 **Retry Option**: Not happy with screenshots? Retry before analyzing
- 📁 **Manual Mode**: Upload your own screenshots for heavily bot-protected sites
- ⌨️ **Cancel Anytime**: Press Ctrl+C or skip individual competitors

### Analysis & Reports
- 🎯 **UX Maturity Focus**: Evaluate UX maturity across multiple dimensions
- 📊 **Research-backed Evaluation**: Baymard Institute and Nielsen Norman Group criteria
- 📱 **Desktop & Mobile Analysis**: Multi-viewport screenshot capture
- 🧪 **Two-Pass Pipeline**: Observe first, score second, with explicit evidence trail
- 🔄 **Reanalyze Capability**: Regenerate reports from existing screenshots (NEW in v1.3.2)

### Output & Indexing
- 📁 **Project-Local Storage**: Reports are written to `output/` inside this repository
- 🗂️ **Audit History Index**: Auto-generated `output/index.html` lists all report runs
- 🧾 **Evidence Preservation**: Each competitor now stores `observation.json` + `analysis.json`

### HTML Reports
- 📈 **Interactive Charts**: Radar, heatmap, and bar charts with Plotly
- 🔍 **Dynamic Filtering**: Filter by competitive position, score, or search
- 🖼️ **Annotated Screenshots**: Visual badges showing strengths/weaknesses
- 💡 **Strategic Insights**: Market leaders, opportunities, threats at-a-glance
- 🟣 **Purple Theme**: Professional color scheme for visual distinction

## Quick Start

### Prerequisites

- Python 3.9 or higher
- Anthropic API key ([get one here](https://console.anthropic.com/))

### Installation

1. **Clone the repository:**
```bash
git clone <repository-url>
cd UXMaturityAnalysis
```

2. **Install dependencies:**
```bash
pip3 install -r requirements.txt
```

3. **Install Playwright browsers:**
```bash
python3 -m playwright install chromium
```

4. **Set up environment variables:**
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

**Expected Timing:**
- Screenshot capture: ~30 seconds per competitor (your manual interaction time)
- AI analysis: ~1.5 minutes per competitor (two-pass processing + rate-limit delays)
- Total for 10 competitors: ~20-25 minutes end-to-end (site/page complexity dependent)

**Specify analysis type** (skip the prompt):

```bash
python3 main.py --config competitors.json --analysis-type basket_pages

# Available types: homepage_pages, product_pages, basket_pages, checkout_pages
```

**Manual mode** (for heavily bot-protected sites):

```bash
# Provide your own screenshots
python3 main.py --manual-mode --screenshots-dir ./screenshots --config competitors.json
```

---

## How It Works

The tool follows a reliable two-phase workflow with a two-pass AI analysis stage:

### Phase 1: Screenshot Capture (Interactive)

1. **Select Analysis Type** - Interactive prompt shows all available types
   - Homepage analysis
   - Product page analysis
   - Basket/cart analysis
   - Checkout flow analysis

2. **For Each Competitor:**
   - Browser opens to the URL (visible mode)
   - You navigate, close popups, accept cookies
   - Press Enter when ready → Captures desktop & mobile screenshots
   - Choose: **Y** (Continue) / **R** (Retry) / **S** (Skip)

### Phase 2: AI Analysis (Sequential, Two-Pass)

3. **Pass 1: Observation**
   - Claude receives screenshots and returns structured visual observations
   - Output is saved as `observation.json` per competitor
   - `notable_states` capture anomalies/defaults that must be addressed in scoring

4. **Pass 2: Scoring from Evidence (Text-only)**
   - Claude scores criteria against the observation JSON (no image payload)
   - Each criterion includes an evidence citation
   - More stable scoring because attention is focused on criteria, not visual scanning

5. **Sequential Execution & Rate Limits**
   - ~1.5 minutes per competitor (rate limit compliant)
   - Real-time progress indicators (✓/✗/⚠)
   - Research-backed criteria evaluation
   - 90-second delays between analyses to respect API limits

6. **Report Generation** - Generates multiple output formats:
   - Interactive HTML report with charts
   - Markdown UX maturity report
   - Individual JSON analyses per competitor

### Two Modes Available

- 🌐 **Interactive Mode** (default): Browser opens, you control, tool captures
- 📁 **Manual Mode** (`--manual-mode`): You provide pre-captured screenshots

### Control Options

- Press **Ctrl+C** anytime to exit
- Type **R** to retry screenshot capture
- Type **S** to skip a competitor

---

## Usage Examples

### Basic Analysis (Interactive Mode)

Run the analysis - you'll be prompted to select the type:

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

3. **Analysis & Report** - Claude analyzes all screenshots sequentially and generates reports

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

### Specify Claude Model

```bash
python3 main.py --model claude-sonnet-4-6 --config competitors.json
```

### Manual Mode (For Bot-Protected Sites)

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

---

## Reanalyze Script

🆕 **NEW in v1.3.2**: Regenerate reports from existing screenshots without re-capturing!

### Why Use Reanalyze?

- **No Browser Interaction**: Skip the screenshot capture phase entirely
- **Faster Iteration**: Regenerate reports in seconds, not minutes
- **Cost Efficient**: Reuse existing screenshots, only pay for AI analysis
- **Perfect For**:
  - Testing prompt changes
  - Refining criteria weights
  - Updating report designs
  - Re-running failed analyses

### Usage

```bash
python3 scripts/reanalyze_screenshots.py <audit_folder>

# Optional flags
python3 scripts/reanalyze_screenshots.py <audit_folder> --force-observe
python3 scripts/reanalyze_screenshots.py <audit_folder> --force
```

**Example:**

```bash
# Regenerate report from existing basket pages audit
python3 scripts/reanalyze_screenshots.py output/audits/2025-11-24_basket_pages
```

### How It Works

1. **Loads existing audit** from the specified folder
2. **Finds all competitor folders** with screenshots
3. **Checks for existing analyses**:
   - Reuses `analysis.json` if present (instant)
   - Reuses `observation.json` by default when available
   - Re-runs pass 1 with `--force-observe`
   - Re-runs both passes with `--force`
4. **Generates fresh reports** with current template and logic

### Smart Caching

The script intelligently reuses existing analysis results:

```
Found 11 competitors to reanalyze

  [↻] amazon: Using existing analysis
  [↻] zooplus: Using existing analysis
  [✓] petshop.co.uk: Running new analysis
  ...

Found 10 existing analyses, need to analyze 1 competitor

═══ Phase 2: AI Analysis (Sequential) ═══
Analyzing 1 competitor sequentially...
Rate limit protection: 90s delay between analyses

  [✓] petshop.co.uk

✓ Reanalysis complete!
✓ Reports generated:
  - markdown: output/audits/2025-11-24_basket_pages/_comparison_report.md
  - html: output/audits/2025-11-24_basket_pages/2025-11-24_basket_pages_report.html
```

### Use Cases

**Scenario 1: Update Report Design**
You've made filtering improvements to the HTML report template. Regenerate:

```bash
python3 scripts/reanalyze_screenshots.py output/audits/2025-11-24_basket_pages
```
All 11 analyses reused instantly, new HTML report generated in seconds.

**Scenario 2: Refine Analysis Criteria**
You've updated `basket_pages.yaml` with new evaluation points. Delete old `analysis.json` files:

```bash
# Remove existing analyses to force re-analysis
rm output/audits/2025-11-24_basket_pages/*/analysis.json

# Reanalyze with new criteria
python3 scripts/reanalyze_screenshots.py output/audits/2025-11-24_basket_pages
```

**Scenario 3: Add Missing Competitor**
One competitor failed during capture. Add screenshots manually, then:

```bash
python3 scripts/reanalyze_screenshots.py output/audits/2025-11-24_basket_pages
```
Only the new competitor gets analyzed; others reused.

### Output

Same structure as main script:
- Updated `{audit_folder}_report.html` (interactive)
- Updated `_comparison_report.md` (markdown)
- Individual `analysis.json` files (if re-analyzed)

---

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

# Analysis Context - Market/domain-specific context for AI prompts
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

observation_focus:
  - "Cart contents and totals visible"
  - "Default state of subscription/one-time options"
  - "Coupon field visibility and state"

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
- **Dynamic AI Context**: The `analysis_context` field provides market-specific expertise
- **Two-pass Focus Control**: `observation_focus` steers pass 1 evidence capture per page type
- **Automatic Integration**: No code changes needed - just edit YAML and run
- Each criterion is evaluated against Baymard Institute and Nielsen Norman Group benchmarks

---

## Output Structure

The tool organizes output by audit run with hierarchical structure:

```
output/
├── index.html                           # Master index for all audit runs
└── audits/
    └── 2026-02-24_basket_pages/         # Audit folder
        ├── _comparison_report.md         # Markdown UX maturity report
        ├── 2026-02-24_basket_pages_report.html  # Interactive HTML report
        ├── _audit_summary.json           # Audit metadata
        ├── nike/                         # Competitor folder
        │   ├── screenshots/
        │   │   ├── desktop.png           # Desktop viewport screenshot
        │   │   └── mobile.png            # Mobile viewport screenshot
        │   ├── observation.json          # Pass 1 observation evidence
        │   └── analysis.json             # Pass 2 scored analysis
        └── ...
```

### File Descriptions

- **`output/index.html`**: Master index listing all audit runs and report links
- **`{audit_folder}_report.html`**: Interactive report with charts, filtering, annotations
- **`_comparison_report.md`**: Markdown report with strategic insights and competitive analysis
- **`_audit_summary.json`**: Metadata about the audit (timestamp, analysis type, competitors)
- **`screenshots/`**: Desktop and mobile PNG screenshots for each competitor
- **`observation.json`**: Pass 1 visual state observations + notable states
- **`analysis.json`**: Pass 2 scoring with evidence citations, strengths, vulnerabilities

---

## Interactive HTML Reports

The tool generates **rich, interactive HTML reports** (`{audit_folder}_report.html`) with visualizations and filtering capabilities.

### Report Sections

#### 1. Executive Summary

Four key metrics at the top:
- **Competitors Analyzed**: Total number successfully analyzed
- **Average Score**: Mean UX score across all competitors (0-10 scale)
- **Top Score**: Highest performing competitor and their score
- **Lowest**: Weakest performing competitor and their score

**Key Insights Box** highlights:
- 🏆 **Market Leader**: Competitor with highest overall score
- 📊 **Most Consistent**: Competitor with most balanced performance
- 💪 **Industry Strength**: Criterion where market performs best
- ⚠️ **Market Vulnerability**: Criterion where all competitors struggle

#### 2. Strategic Insights

Three executive-focused insight cards:

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

#### 3. Overall Rankings

Complete competitive ranking table showing all competitors:

**Columns:**
- **Rank**: Badge (🥇 Gold, 🥈 Silver, 🥉 Bronze for top 3)
- **Competitor**: Company name
- **Overall Score**: Color-coded (🟢 Green 8+, 🟠 Orange 6-8, 🔴 Red <6)
- **Competitive Position**: Automatic classification
  - **Market Leader** (8.0+): Significantly above average
  - **Strong Contender** (6.5-7.9): At or near average
  - **Competitive** (5.0-6.4): Below average but viable
  - **Vulnerable** (<5.0): Significantly behind
- **Key Differentiator**: Each competitor's strongest criterion

**Note**: Rankings table is **never filtered** - always shows all competitors for full competitive landscape view.

#### 4. Filter & Search Panel 🆕 v1.3.2

Interactive controls to explore competitor profiles (not rankings):

- **Search Competitor**: Type name to filter competitor cards
- **Minimum Score**: Slider (0-10) to show only high-performing competitors
- **Competitive Position**: Filter by tier (Market Leader, Strong Contender, Competitive, Vulnerable)
  - **Dynamic dropdown**: Only shows tiers that have competitors
  - **Shows counts**: e.g., "Strong Contender (9)"
- **Reset Filters**: Clear all filters to see full dataset

Filter count shows: "Showing X of Y competitors"

**What gets filtered:**
- ✅ Competitor profile cards
- ✅ Visual analysis charts (radar, bar, heatmap)
- ❌ Rankings table (always shows all competitors)

#### 5. Visual Analysis Charts 🆕 v1.3.2

All charts update dynamically based on active filters!

**Radar Chart - Competitive UX Comparison**
- Shows all (or filtered) competitors overlaid on same axes
- Each axis = one UX criterion
- Larger area = better overall performance
- Traces hide/show based on filters

**Heatmap - Feature Adoption Matrix**
- Rows = Competitors, Columns = Criteria
- Color coding: 🟢 Green (8-10) → 🟡 Yellow (4-7) → 🔴 Red (0-3)
- Numbers show exact scores
- Dynamically filters rows based on competitive position filter

**Bar Chart - Criteria Performance**
- Grouped bars showing scores across all evaluation criteria
- Each competitor = one color
- Traces hide/show based on filters

#### 6. Competitor Profiles

Each competitor card shows:

**Observation callout (two-pass evidence):**
- Flagged anomalies from pass 1 (`notable_states`) shown at top of each profile
- Per-criterion evidence citations surfaced directly below criterion bars

**Competitive Position Tier** (badge at top):
- 🟢 **Market Leader**: Score significantly above average
- 🟡 **Strong Contender**: Score at or near average
- 🔴 **Vulnerable**: Score below average

**Performance by Criteria** table:
1. **Criterion Name**: The UX element being evaluated
2. **Status Badge**: Competitive intelligence label
   - 🟢 **Advantage**: Scores above market average (competitive threat)
   - 🟡 **Parity**: Scores at market average (table stakes)
   - 🔴 **Vulnerability**: Scores below market average (exploitable weakness)
3. **Score**: Numerical score (0-10) with color coding

**Understanding Status Labels:**
- **Status is relative to the competitive set**, not absolute benchmarks
- **Advantage** = "better than competitors" (even 7/10 can be advantage if others score 5/10)
- **Vulnerability** = "worse than competitors" (even 7/10 can be vulnerability if others score 9/10)

**Screenshots Section**:
- Desktop and mobile viewport screenshots
- Click any screenshot to open **lightbox** (full-screen view)
- ESC key or click outside to close lightbox
- Annotated screenshots show top strengths (green badges) and weaknesses (red badges)

#### 7. Interactive Features

**Lightbox Gallery**:
- Click any screenshot → Full-screen modal opens
- Shows competitor name and viewport (desktop/mobile)
- ESC key or click backdrop to close
- Prevents page scroll when open

**Real-time Filtering**:
- All filters work instantly (no page reload)
- Combine multiple filters (search + score + position)
- Charts update dynamically using Plotly.restyle() API
- Results update live as you type/adjust sliders

**Responsive Design**:
- Report adapts to screen size
- Mobile-friendly layout
- Charts resize for readability

### How to Use the Report

**For Strategic Planning:**
1. Start with Strategic Insights → Immediate actionable intelligence
2. Review Top Opportunities → Identify differentiation areas
3. Check Overall Rankings → Understand competitive landscape
4. Use Heatmap → Spot patterns and white space

**For UX Maturity Analysis:**
1. Check Overall Rankings table → See relative positions
2. Review Market Leaders card → Identify who to benchmark
3. Look at Competitive Threats → Understand what you're up against
4. Use filter to focus on specific tier or competitor

**For Executive Presentations:**
1. Strategic Insights 3-card summary → Concise strategic story
2. Overall Rankings table → Competitive position at a glance
3. Radar Chart → Visual competitive positioning
4. Screenshots with annotations → Specific examples

---

## Reports Index

The tool now maintains a project-local report index automatically.

### Where reports are saved

- Audit runs: `output/audits/{date}_{analysis_type}/`
- Master index: `output/index.html`

### What the index includes

- All structured audit runs under `output/audits/`
- Links to available HTML, Markdown, and summary JSON files per run
- Legacy flat reports (if present) so historical exports remain discoverable

### How it updates

- `output/index.html` is regenerated automatically after report generation
- No separate indexing step is required for normal analysis or reanalysis workflows

### Viewing locally

```bash
python3 -m http.server 8000 --directory output
# Open http://localhost:8000
```

---

## Architecture & Extensibility

This tool is designed for easy extension to other page types and analysis scenarios.

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
- Generates UX maturity reports using your criteria

#### 2. Project Structure

```
UXMaturityAnalysis/
├── main.py                          # Main entry point & orchestration
│
├── scripts/                         # 📜 User-facing utilities
│   ├── reanalyze_screenshots.py    #    🆕 Regenerate reports from existing screenshots
│   ├── generate_index.py           #    (Legacy) create audits-only index for deployment
│   ├── deploy_netlify.py           #    Deploy reports to Netlify
│   └── update_resources_index.py   #    (Legacy) Resources-site index updater
│
├── criteria_config/                 # ✨ Page-type-specific criteria
│   ├── homepage_pages.yaml         #    Homepage UX criteria
│   ├── product_pages.yaml          #    Product page criteria
│   ├── basket_pages.yaml           #    Basket/cart criteria
│   └── checkout_pages.yaml         #    Checkout flow criteria
│
├── src/                            # 📦 Core library code
│   ├── config_loader.py            #    Load criteria from YAML files
│   ├── analyzers/
│   │   ├── screenshot_capture.py   #    Playwright browser automation
│   │   └── claude_analyzer.py      #    Claude API + prompts
│   └── utils/
│       ├── report_generator.py     #    Markdown report generation
│       ├── audit_organizer.py      #    Hierarchical output organisation
│       ├── html_report_generator.py #   Interactive HTML reports with charts
│       └── screenshot_annotator.py  #   Screenshot annotations
│
├── docs/                            # 📚 Documentation
│   ├── deployment/                 #    Deployment guides
│   │   ├── NETLIFY.md             #    Full Netlify deployment guide
│   │   └── QUICKSTART.md          #    30-second deployment
│   ├── ARCHITECTURE.md             #    System architecture
│   ├── BOT_DETECTION_GUIDE.md      #    Handling bot protection
│   └── config_reference.yaml       #    Config structure reference
│
├── requirements.txt                 # Python dependencies
├── .env.example                     # Environment variables template
├── competitors.example.json         # Example competitor config
│
└── output/
    ├── index.html                   #    Master index of all audits
    └── audits/                      #    Organised by audit run
        └── {date}_{analysis_type}/  #    Audit folder
            ├── _comparison_report.md
            ├── {audit_folder}_report.html
            ├── _audit_summary.json
            └── {competitor}/
                ├── screenshots/
                ├── observation.json
                └── analysis.json
```

---

## Technical Details

### Dependencies

- **playwright**: Browser automation for screenshot capture
- **anthropic**: Claude API client for AI analysis
- **pydantic**: Data validation and settings management
- **pyyaml**: Configuration file parsing
- **python-dotenv**: Environment variable management
- **rich**: Enhanced console output
- **plotly**: Interactive charts in HTML reports
- **pillow**: Image processing and annotation
- **jinja2**: HTML template rendering

### Environment Variables

Configure in `.env`:

```bash
# Required
ANTHROPIC_API_KEY=your_api_key_here

# Optional (defaults provided)
CLAUDE_MODEL=claude-sonnet-4-6
VIEWPORT_WIDTH=1920
VIEWPORT_HEIGHT=1080
MOBILE_VIEWPORT_WIDTH=375
MOBILE_VIEWPORT_HEIGHT=812
```

Model selection precedence:
1. `--model` CLI argument
2. `CLAUDE_MODEL` (or `claude_model`) from `.env`
3. Built-in fallback (`claude-sonnet-4-5-20250929`)

### Performance

- **Sequential AI Analysis**: Rate limit compliant processing
  - ~1.5 minutes per competitor for two-pass analysis
  - 90-second delays between analyses to respect 8,000 output tokens/min limit
  - Trade-off: Reliability over speed (prevents API rate limit errors)
- **Smart Caching**: Reanalyze script reuses existing analyses/observations where possible
- **Optimized Images**: Automatic JPEG compression for Claude API
- **API Rate Limits**:
  - Input: 30,000 tokens/min (rarely limiting)
  - Output: 8,000 tokens/min (primary constraint)
  - Two-pass output budget per competitor is typically higher than single-pass

---

## Roadmap

**Recently Completed** ✅
- [x] 🧭 Two-pass analysis pipeline with `observation.json` evidence (v1.6.0)
- [x] 🗂️ Project-level reports index at `output/index.html` (v1.6.0)
- [x] 📁 Enforced in-project report output under `output/audits/` (v1.6.0)
- [x] 🤖 Environment-based default Claude model selection (v1.6.0)
- [x] 🛡️ Dark pattern detection enhancements (v1.5.0)
- [x] 📦 Product page criteria enhancements with 2025-2026 research (v1.5.0)
- [x] 💳 Express payment options criterion (v1.5.0)
- [x] ⚖️ Sequential analysis for API rate limit compliance (v1.5.0)
- [x] 🔄 Reanalyze script for report regeneration (v1.3.2)
- [x] 🎨 Advanced filtering with dynamic dropdowns and chart updates (v1.3.2)
- [x] 🎯 Strategic insights and rankings (v1.3.0)
- [x] 📊 Interactive HTML reports with charts (v1.2.0)

**Future Enhancements Planned:**
- [ ] Multi-step journey support (homepage → product → add to cart → basket)
- [ ] HTML/DOM analysis alongside screenshots
- [ ] Time-series analysis (track competitor changes over time)
- [ ] Export to CSV/Excel formats
- [ ] Integration with analytics tools (GA4, ContentSquare)
- [ ] API endpoints for programmatic access
- [ ] Scheduled automated audits

---

## Versioning

This project uses [Semantic Versioning](https://semver.org/):
- **MAJOR** version for incompatible API changes
- **MINOR** version for added functionality in a backward compatible manner
- **PATCH** version for backward compatible bug fixes

**Current Version:** 1.6.0

See [CHANGELOG.md](CHANGELOG.md) for detailed release notes and upgrade instructions.

### Checking Version

```bash
python3 main.py --version
```

Or programmatically:

```python
from src.version import __version__, get_version_info
print(f"Version: {__version__}")  # 1.6.0
print(f"Version Info: {get_version_info()}")  # (1, 6, 0)
```

---

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

---

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

---

## Support

### Documentation

- **Main README**: This file (comprehensive guide)
- **CHANGELOG**: [CHANGELOG.md](CHANGELOG.md) - Version history and upgrade notes
- **Architecture**: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) - Technical design

### Getting Help

1. **Check Documentation**: Review README and docs folder
2. **View Demo Report**: Open `docs/DEMO_REPORT.html` in browser to see example output
3. **Run Diagnostics**: `python3 tests/verify_setup.py`
4. **Check Version**: `python3 main.py --version`
5. **Open Issue**: GitHub Issues with version info and details

---

## Acknowledgments

**Built with:**
- Python 3.9+
- [Playwright](https://playwright.dev/) - Browser automation
- [Claude AI (Anthropic)](https://www.anthropic.com/) - AI-powered analysis
- [Plotly](https://plotly.com/) - Interactive charts
- [Pydantic](https://pydantic-docs.helpmanual.io/) - Data validation
- [Rich](https://rich.readthedocs.io/) - Terminal UI

**Research Sources:**
- [Baymard Institute](https://baymard.com/) - E-commerce UX research
- [Nielsen Norman Group](https://www.nngroup.com/) - Usability guidelines

**Author:** Matthew Lelonek

---

**⭐ If you find this tool useful, please star the repository!**
