# E-commerce Basket Page UX Analysis Agent

A proof-of-concept Python tool that systematically analyzes competitor e-commerce basket pages and generates structured UX reports using Claude AI and browser automation.

## Overview

This tool automates competitive UX analysis for e-commerce basket/cart pages by:

1. Capturing screenshots of competitor basket pages (desktop & mobile viewports)
2. Analyzing UX against research-backed criteria (Baymard Institute, Nielsen Norman Group)
3. Generating structured JSON data and comprehensive markdown reports
4. Providing actionable recommendations prioritized by impact

**Key Features:**
- AI-powered analysis using Claude's vision capabilities
- Research-backed evaluation criteria from Baymard and Nielsen Norman
- Extensible architecture for different page types and analysis criteria
- Multiple output formats (JSON, Markdown)
- Desktop and mobile viewport analysis

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
pip install -r requirements.txt
```

3. Install Playwright browsers:
```bash
playwright install chromium
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

### Basic Usage

Analyze competitor basket pages by providing URLs:

```bash
python main.py --urls https://www.asos.com/bag https://www.zara.com/cart
```

Or use a configuration file:

```bash
python main.py --config competitors.example.json
```

## Usage Examples

### Analyze specific URLs
```bash
python main.py --urls https://shop1.com/basket https://shop2.com/cart https://shop3.com/bag
```

### Use a custom configuration file
```bash
# Create your competitors.json
python main.py --config competitors.json
```

### Specify a different Claude model
```bash
python main.py --model claude-sonnet-4-5-20250929 --urls https://example.com/cart
```

### Analyze different page types
```bash
# Basket pages (interactive mode - browser opens for you to add items)
python main.py --analysis-type basket_pages --urls https://shop.com/cart

# Homepage analysis (automated mode - runs headless, no interaction)
python main.py --analysis-type homepage_pages --urls https://shop1.com https://shop2.com
```

## Interactive vs Automated Mode

The tool supports **smart human-in-the-loop interaction** based on page type:

### Interactive Mode (Basket Pages)
- **When:** Analyzing basket/cart pages that need items added
- **How it works:**
  1. Browser opens in **visible mode**
  2. You manually add 1-2 items to the basket
  3. Navigate to the basket page
  4. Press Enter to capture screenshots
  5. Tool continues with AI analysis
- **Use case:** Pages requiring setup (baskets, checkouts, logged-in states)

Example output:
```
🔧 Interactive mode enabled - browser will be visible
You'll be prompted to interact with each competitor's page

Progress: 1/3 (interactive)
🛒 Please add 1-2 items to the basket, then press Enter to continue...
[Press Enter when ready to capture screenshots...]
```

### Automated Mode (Homepages, Product Pages)
- **When:** Analyzing pages that don't need interaction
- **How it works:**
  1. Runs in **headless mode** (faster)
  2. No pauses or prompts
  3. Fully automated screenshot + analysis
- **Use case:** Homepages, product pages, about pages, landing pages

Example output:
```
⚡ Automated mode - running headless for speed

Progress: 1/20 (automated)
Analyzing: competitor1
Capturing screenshots (automated)...
```

### Configuration
Configure interaction behavior in `config.yaml`:

```yaml
analysis_types:
  basket_pages:
    interaction:
      requires_interaction: true  # Interactive mode
      mode: "visible"
      prompt: "🛒 Please add 1-2 items to the basket..."
      timeout: 120  # seconds

  homepage_pages:
    interaction:
      requires_interaction: false  # Automated mode
      mode: "headless"
```

**Benefits:**
- Run 20 homepage analyses unattended (grab coffee ☕)
- Pause at basket pages when manual setup is needed
- Mix both in future workflows

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

## Output

The tool generates two types of reports in the `output/` directory:

### 1. JSON Report (`ux_analysis_TIMESTAMP.json`)
Structured data suitable for:
- Database import
- Further programmatic analysis
- Integration with other tools

### 2. Markdown Report (`ux_analysis_report_TIMESTAMP.md`)
Human-readable report including:
- Executive summary
- Overall rankings
- Detailed competitor analysis
- Criterion-by-criterion scoring
- Strengths and weaknesses
- Actionable recommendations (prioritized by impact)
- Comparative insights
- Methodology appendix

### Screenshots
Captured screenshots are saved to `screenshots/` directory with naming:
- `{competitor}_desktop_{timestamp}.png`
- `{competitor}_mobile_{timestamp}.png`

## Architecture & Extensibility

This POC is designed for easy extension to other page types and analysis scenarios:

### Extension Points

#### 1. Adding New Page Type Analysis

To analyze different page types (product pages, checkout, etc.):

1. Add a new section to `config.yaml` following the `basket_pages` pattern:

```yaml
analysis_types:
  product_pages:
    name: "Product Page Analysis"
    description: "UX analysis of product detail pages"
    criteria:
      - id: "product_imagery"
        name: "Product Image Quality"
        weight: 9
        # ... add criteria
```

2. Run analysis with the new type:
```bash
python main.py --analysis-type product_pages --urls https://example.com/product
```

No code changes required!

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
├── main.py                          # Main entry point
├── config.yaml                      # UX analysis criteria (extensible)
├── requirements.txt                 # Python dependencies
├── .env.example                     # Environment variables template
├── competitors.example.json         # Example competitor config
├── src/
│   ├── config_loader.py            # Load analysis configurations
│   ├── analyzers/
│   │   ├── screenshot_capture.py   # Playwright browser automation
│   │   └── claude_analyzer.py      # Claude API integration
│   └── utils/
│       └── report_generator.py     # JSON and Markdown reports
├── output/                          # Generated reports
└── screenshots/                     # Captured screenshots
```

## Current Limitations (POC)

This is a proof-of-concept with some intentional limitations:

1. **Empty Basket Pages**: The POC captures whatever state the basket page is in. If a basket requires items to be added first, it will capture the empty state. Future iterations will add automated item addition.

2. **Single URL per Competitor**: Currently analyzes one URL per competitor. Multi-step journeys are architecturally supported but not yet implemented.

3. **Sequential Analysis**: Competitors are analyzed one at a time. Could be parallelized for faster execution.

4. **Screenshot-Only Analysis**: Currently analyzes screenshots. Could be enhanced to include DOM/HTML analysis for additional insights.

## Use Cases

This tool is designed for:

- **E-commerce UX Teams**: Automate competitive basket page analysis
- **Conversion Optimization**: Identify abandonment friction points
- **Product Managers**: Benchmark against competitors systematically
- **UX Researchers**: Scale qualitative analysis with AI assistance
- **Agencies**: Deliver competitive audits faster

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
- [ ] Automated item addition to basket before capture
- [ ] HTML/DOM analysis alongside screenshots
- [ ] Parallel competitor analysis for speed
- [ ] Interactive HTML reports with embedded screenshots
- [ ] Time-series analysis (track competitor changes over time)
- [ ] A/B test screenshot comparison
- [ ] Integration with analytics tools (GA4, ContentSquare)

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

This is a proof-of-concept tool. Feedback and suggestions welcome!

## License

[Add your license here]

## Support

For issues or questions:
1. Check the examples and documentation above
2. Review the configuration files for extensibility patterns
3. Open an issue with details about your use case

---

**Built with:** Python, Playwright, Claude AI (Anthropic)

**Author:** E-commerce UX Analysis Agent POC
