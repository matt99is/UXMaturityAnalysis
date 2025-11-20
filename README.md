# E-commerce UX Competitive Intelligence Agent

**Version:** 1.1.0
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
- [Bot Detection Handling](#bot-detection-handling-v110)
- [Interactive vs Automated Mode](#interactive-vs-automated-mode)
- [Output Structure](#output-structure)
- [Supported Page Types](#supported-page-types)
- [Architecture & Extensibility](#architecture--extensibility)
- [Versioning](#versioning)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

This tool automates competitive UX analysis for e-commerce sites by:

1. **Auto-detecting page types** from URLs (homepage, product, basket, checkout)
2. Capturing screenshots of competitor pages (desktop & mobile viewports)
3. Analyzing UX against research-backed criteria (Baymard Institute, Nielsen Norman Group)
4. **Generating competitive intelligence reports** focused on threats, opportunities, and market positioning
5. Providing strategic insights for competitive differentiation

**Key Features:**
- ✨ **Multi-Page-Type Support**: Analyze homepages, product pages, basket pages, and checkout flows
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

See [Bot Detection Guide](docs/BOT_DETECTION_GUIDE.md) for complete details.

## Bot Detection Handling 🤖

The tool is designed to work reliably with bot-protected sites through **interactive mode**:

### **Interactive Mode** (Default) ⭐
- **How it works:**
  - Browser opens in visible mode (you control it)
  - Navigate to the page yourself
  - Solve CAPTCHAs, close popups, login if needed
  - Press Enter when ready → Tool captures screenshots
  - Choose to retry if something went wrong

- **When to use:** All analyses (default mode)
- **Advantages:**
  - Works around bot detection naturally
  - You verify the page loaded correctly
  - Retry option if screenshots aren't right

### **Manual Screenshot Mode** (Backup)
- **How it works:**
  - You manually capture screenshots (any method)
  - Save as: `sitename_desktop.png`, `sitename_mobile.png`
  - Tool loads your screenshots and analyzes

```bash
python3 main.py --manual-mode --screenshots-dir ./my-screenshots --urls https://amazon.com
```

- **When to use:** Sites with extremely aggressive bot detection (Amazon, eBay)
- **Advantages:**
  - Complete control over capture
  - Use browser extensions, login states, etc.

**No automated/headless mode:** Removed for reliability - interactive mode works better for modern bot detection.

## Interactive Mode Workflow

**All analyses now run in interactive mode for maximum reliability:**

### How Interactive Mode Works
- **Browser opens in visible mode** for each competitor
- **You control the interaction:**
  - Navigate to the correct page
  - Close cookie banners and popups
  - Solve CAPTCHAs if needed
  - Wait for page to fully load
  - For basket pages: Add 1-2 items first
  - For checkout: Progress to checkout flow

- **Press Enter** when ready to capture

- **Review & Choose:**
  - ✓ Captured X screenshots
  - Continue? ([Y]es / [r]etry / [s]kip):
    - **Y** → Move to next competitor
    - **R** → Retry this one (browser reopens)
    - **S** → Skip this competitor

### Example Workflow
```
📋 Select Analysis Type:
[You select: 4. Product Pages]

🌐 Interactive Mode: Browser will open for each site
Navigate to the page, close popups, then press Enter to capture

Progress: 1/3 (interactive)

Analyzing: zooplus
URL: https://www.zooplus.co.uk/shop/...

Navigate to the product page analysis and prepare for screenshot
Close popups, accept cookies, and ensure page is fully loaded

[Press Enter when ready...]

✓ Captured 2 screenshot(s)

Continue? ([Y]es / [r]etry / [s]kip): y

Analyzing with Claude AI...
✓ Analysis complete!

Progress: 2/3 (interactive)
...
```

### Benefits
- ✅ **Works with any site** - you bypass bot detection naturally
- ✅ **Visual verification** - you see what gets captured
- ✅ **Retry option** - fix issues before analysis
- ✅ **Complete control** - handle any edge case

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

Edit `config.yaml` to customize analysis criteria. The POC includes 10 criteria:

1. **Discount Code Field** (Weight: 9/10)
   - Placement, visibility, messaging clarity
   - Code application vs activation clarity

2. **Shipping Cost Transparency** (Weight: 10/10)
   - Visibility before checkout
   - Free shipping thresholds

3. **Delivery Estimates** (Weight: 8/10)
   - Time estimates shown
   - Dispatch cutoff times

4. **Payment Methods** (Weight: 7/10)
   - Early visibility of accepted methods
   - Security indicators

5. **Express Checkout Options** (Weight: 8/10)
   - Apple Pay, Google Pay, PayPal availability
   - Prominence and positioning

6. **Trust Signals** (Weight: 7/10)
   - Security badges
   - Return policy visibility
   - Guarantees

7. **Basket Summary Clarity** (Weight: 9/10)
   - Cost breakdown clarity
   - Subtotals, taxes, discounts

8. **CTA Buttons** (Weight: 8/10)
   - Copy clarity
   - Visual prominence

9. **Basket Saving Features** (Weight: 6/10)
   - Save for later
   - Wishlist integration

10. **Mobile Responsiveness** (Weight: 8/10)
    - Responsive design indicators
    - Touch target sizing

Each criterion is evaluated against Baymard Institute and Nielsen Norman Group benchmarks.

## Output Structure

The tool organizes output by audit run with hierarchical structure:

```
output/audits/
└── 2025-11-20_homepage_pages/          # Audit folder
    ├── _comparison_report.md            # Competitive intelligence report
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

2. Run analysis (auto-detected or manual):
```bash
# Auto-detection (if URL pattern added to detector)
python3 main.py --urls https://example.com/campaign

# Manual specification
python3 main.py --analysis-type landing_pages --urls https://example.com/campaign
```

**No code changes required!** The system automatically:
- Loads your new YAML config
- Makes it available as an analysis type
- Generates competitive intelligence reports using your criteria

#### 2. Supported Page Types

Out of the box, the tool includes:

- **`homepage_pages`**: Homepage analysis (8 criteria)
- **`product_pages`**: Product detail pages (9 criteria)
- **`basket_pages`**: Shopping cart pages (10 criteria)
- **`checkout_pages`**: Checkout flow (8 criteria, requires interaction)

Each optimized with page-specific UX criteria and benchmarks.

#### 2. Adding Multi-Step Journeys

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

#### 3. Customizing Analysis Prompts

The `ClaudeUXAnalyzer` class (`src/analyzers/claude_analyzer.py`) builds prompts dynamically from config criteria, making it work with any analysis type.

#### 4. Adding New Output Formats

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
│       └── page_type_detector.py   # ✨ Auto-detect page types from URLs
└── output/audits/                   # ✨ Organized by audit run
    └── {date}_{analysis_type}/      #    Audit folder
        ├── _comparison_report.md    #    Competitive intelligence report
        ├── _audit_summary.json      #    Audit metadata
        └── {competitor}/            #    Competitor folders
            ├── screenshots/         #    Screenshots
            └── analysis.json        #    Individual analysis
```

## Current Limitations (POC)

This is a proof-of-concept with some intentional limitations:

1. **Empty Basket Pages**: The POC captures whatever state the basket page is in. If a basket requires items to be added first, it will capture the empty state. Future iterations will add automated item addition.

2. **Single URL per Competitor**: Currently analyzes one URL per competitor. Multi-step journeys are architecturally supported but not yet implemented.

3. **Sequential Analysis**: Competitors are analyzed one at a time. Could be parallelized for faster execution.

4. **Screenshot-Only Analysis**: Currently analyzes screenshots. Could be enhanced to include DOM/HTML analysis for additional insights.

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

Future enhancements planned:

- [ ] Multi-step journey support (homepage → product → add to cart → basket)
- [ ] HTML/DOM analysis alongside screenshots
- [ ] Parallel competitor analysis for speed
- [ ] Interactive HTML reports with embedded screenshots
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

**Current Version:** 1.1.0

### Version History

**v1.1.0 (2025-11-20)** - Bot Detection Handling
- ✨ Manual screenshot mode for heavily protected sites
- ✨ Enhanced interactive mode with better bot detection prompts
- ✨ Hybrid workflow: automated where possible, manual assist when blocked

**v1.0.0 (2025-11-20)** - Initial Release
- Multi-page-type support (homepage, product, basket, checkout)
- Competitive intelligence reporting framework
- Smart auto-detection
- Hierarchical output structure

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
3. Add URL patterns to `src/utils/page_type_detector.py`
4. Test with sample URLs
5. Submit PR with examples

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
- **Sample Output**: [docs/SAMPLE_OUTPUT.md](docs/SAMPLE_OUTPUT.md) - Example reports
- **Architecture**: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) - Technical design
- **Tests**: `tests/` directory - Setup verification and examples

### Getting Help

1. **Check Documentation**: Review README and docs folder
2. **Run Diagnostics**: `python3 tests/verify_setup.py`
3. **Check Version**: `python3 main.py --version`
4. **Review Examples**: See usage examples in README
5. **Open Issue**: GitHub Issues with version info and details

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
