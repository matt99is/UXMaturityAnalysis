# Quick Start Guide

Get up and running with the UX Analysis Agent in 5 minutes.

## Installation

### 1. Install Dependencies

```bash
# Install Python packages
pip install -r requirements.txt

# Install Playwright browsers (required for screenshots)
playwright install chromium
```

### 2. Configure API Key

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your Anthropic API key
# Get your API key from: https://console.anthropic.com/
```

Edit `.env` file:
```bash
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxx
```

### 3. Verify Setup

```bash
python verify_setup.py
```

If all checks pass, you're ready to go!

## Running Your First Analysis

### Option 1: Analyze specific URLs

```bash
python main.py --urls https://www.asos.com/bag https://www.zara.com/cart
```

### Option 2: Use a configuration file

1. Create `competitors.json`:
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

2. Run analysis:
```bash
python main.py --config competitors.json
```

## What Happens During Analysis

1. **Screenshot Capture**: The tool captures desktop and mobile screenshots of each competitor's basket page
2. **AI Analysis**: Claude analyzes the screenshots against 10 UX criteria
3. **Report Generation**: JSON and Markdown reports are generated

## Output

After analysis completes, you'll find:

- **Screenshots**: `screenshots/competitor_desktop_timestamp.png`
- **JSON Report**: `output/ux_analysis_timestamp.json`
- **Markdown Report**: `output/ux_analysis_report_timestamp.md`

## Example Output

The markdown report includes:
- Executive summary with scores
- Competitor rankings
- Detailed analysis for each criterion
- Strengths and weaknesses
- Actionable recommendations (prioritized by impact)
- Comparative insights

## Customizing Analysis

### Change which criteria are evaluated

Edit `config.yaml` to:
- Add new criteria
- Modify evaluation points
- Change criterion weights
- Update benchmarks

### Analyze different page types

1. Add a new analysis type to `config.yaml`:
```yaml
analysis_types:
  product_pages:
    name: "Product Page Analysis"
    # ... configure criteria
```

2. Run with the new type:
```bash
python main.py --analysis-type product_pages --urls https://example.com/product
```

## Troubleshooting

### "ANTHROPIC_API_KEY not found"
- Make sure you've created a `.env` file
- Verify your API key is correct

### "playwright not found"
- Run: `playwright install chromium`

### Screenshots are blank
- The URL might redirect or require cookies
- Try visiting the URL manually to verify it's accessible

### Analysis takes a long time
- Each competitor takes ~30-60 seconds
- This includes screenshot capture + AI analysis
- Be patient, or reduce the number of competitors

## Next Steps

- Read the full [README.md](README.md) for architecture details
- Explore extensibility options in the code comments
- Customize criteria in `config.yaml` for your needs

## Tips

1. **Start small**: Test with 1-2 competitors first
2. **Check URLs**: Verify basket pages are publicly accessible
3. **Review criteria**: Customize `config.yaml` for your industry
4. **Save results**: Keep JSON reports for historical tracking
5. **Iterate**: Use findings to refine your analysis criteria

---

**Need help?** Check the [README.md](README.md) or review the code comments marked with "EXTENSIBILITY NOTE"
