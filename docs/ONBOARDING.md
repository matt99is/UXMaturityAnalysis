# Developer Onboarding Guide

**Last Updated:** 2026-02-28
**Project:** UX Maturity Analysis Agent v1.10.0

---

## Quick Start

1. **Clone repository:**
   ```bash
   git clone <repository-url>
   cd UXMaturityAnalysis
   ```

2. **Install dependencies:**
   ```bash
   pip3 install -r requirements.txt
   python3 -m playwright install chromium
   ```

3. **Set up environment:**
   ```bash
   cp .env.example .env
   # Edit .env and add your ANTHROPIC_API_KEY
   ```

4. **Verify setup:**
   ```bash
   python3 main.py --version
   python3 tests/verify_setup.py
   ```

---

## Project Structure

```
UXMaturityAnalysis/
├── main.py                    # Main entry point
├── requirements.txt             # Python dependencies
├── css/                       # SCSS stylesheets (8 partials)
│   ├── main.scss              # Main entry (imports partials)
│   ├── _variables.scss         # Design tokens
│   ├── _base.scss              # Reset & base styles
│   ├── _layout.scss           # Layout & grid
│   ├── _components.scss        # Reusable components
│   ├── _sections.scss          # Page sections (charts, metrics, etc.)
│   ├── _competitors.scss       # Competitor-specific styles
│   └── _mobile.scss            # Mobile responsive overrides
├── src/                       # Core library
│   ├── config_loader.py        # Load YAML configs
│   ├── analyzers/             # Analysis logic
│   └── utils/                 # Utilities
│       ├── html_report_generator.py   # HTML report generation
│       ├── report_generator.py       # Markdown report generation
│       ├── audit_organizer.py       # Output organization
│       └── screenshot_annotator.py   # Screenshot annotations
├── templates/                  # Jinja2 templates
│   ├── index.html.jinja2       # Reports index page
│   ├── report.html.jinja2      # Individual report page
│   └── partials/             # Reusable template components
│       ├── _brand.jinja2       # Shared brand markup
│       └── _theme_toggle.jinja2 # Shared theme toggle
├── criteria_config/            # Page-type criteria (YAML)
├── scripts/                   # Utility scripts
└── output/                    # Generated reports
```

---

## How to Run Analysis

### Interactive Mode (Default)
```bash
python3 main.py --config competitors.json
```

You'll be prompted to:
1. Select analysis type (homepage, product, basket, checkout)
2. Browser opens for each competitor
3. Navigate, close popups, press Enter to capture

### Specify Analysis Type (Skip Prompt)
```bash
python3 main.py --config competitors.json --analysis-type basket_pages
```

### Manual Mode (For Bot-Protected Sites)
```bash
# Step 1: Capture screenshots manually
# Save as: competitor_desktop.png, competitor_mobile.png

# Step 2: Analyze
python3 main.py --manual-mode --screenshots-dir ./my-screenshots --config competitors.json
```

---

## Adding New Page Types

### Quick Add (Criteria Only)

1. Create YAML in `criteria_config/`:
   ```bash
   cp criteria_config/basket_pages.yaml criteria_config/landing_pages.yaml
   ```

2. Edit the new YAML file:
   - Update `name` (page type name)
   - Update `criteria` list with your criteria
   - Adjust `viewports` if needed

3. Run analysis:
   ```bash
   python3 main.py --config competitors.json --analysis-type landing_pages
   ```

No code changes needed - the system automatically loads your new config!

---

## Modifying Reports

### Adding New Features to HTML Reports

**File:** `src/utils/html_report_generator.py`

Key functions:
- `generate_report()` - Main orchestration
- `_create_radar_chart()` - Radar chart
- `_create_heatmap()` - Feature heatmap
- `_get_executive_summary()` - Metrics
- `_create_rankings_section()` - Rankings table

**Adding a new section:**
1. Create data for the section (e.g., `insights: {...}`)
2. Add to template context in `generate_report()`
3. Create section in `templates/report.html.jinja2`
4. Test with: `python3 scripts/regenerate_example_report.py`

---

### Changing Colors, Fonts, Layout

**Files to edit:**
- `css/_variables.scss` - Design tokens (colors, spacing, typography)
- `css/_base.scss` - Reset and base styles
- `css/_layout.scss` - Layout patterns

**Workflow:**
1. Edit CSS file
2. Rebuild: `python3 scripts/build_css.py`
3. Test: `python3 scripts/regenerate_example_report.py`
4. Open `output/resources-basket-pages-example-report.html` to verify

---

## Common Troubleshooting

### Screenshot Capture Issues

**Problem:** "Playwright not installed"
```bash
python3 -m playwright install chromium
```

**Problem:** "Playwright browsers not installed"
```bash
python3 -m playwright install --with-deps chromium
```

**Problem:** Browser opens but captures blank screenshots
- Check viewport dimensions in `.env`
- Verify page has fully loaded (wait for animations)
- Try `--manual-mode` with your own screenshots

---

### API Rate Limits

**Problem:** "Rate limit exceeded" during analysis

**Current behavior:**
- System automatically waits 90 seconds between competitors
- Analysis continues when rate limit resets

**No action needed** - this is handled automatically.

---

### Template Errors

**Problem:** "Template not found" or "Undefined variable"

1. Check template syntax:
   ```bash
   python3 -c "from jinja2 import Environment; print(Environment().get_template('templates/report.html.jinja2'))"
   ```

2. Verify template includes:
   - `{% include 'partials/_brand.jinja2' %}`
   - Variables exist in context passed to template

---

### CSS Not Updating

**Problem:** Changes to SCSS files not appearing

**Cause:** SCSS needs to be compiled to CSS

**Solution:**
```bash
# Rebuild CSS
python3 scripts/build_css.py

# Or using dart-sass directly
~/.local/bin/sass css/main.scss output/css/main.css
```

---

### Report Not Generating

**Problem:** "No reports generated" or empty output

**Check:**
1. Did screenshot capture complete? Check `output/audits/{folder}/`
2. Are observation.json files present? They're required for scoring
3. Any error messages in console during analysis?

**Reanalyze from existing:**
```bash
python3 scripts/reanalyze_screenshots.py output/audits/{folder}
```

---

## Testing

### Run All Tests
```bash
pytest tests/
```

### Verify Setup
```bash
python3 tests/verify_setup.py
```

### Regenerate Example Report
```bash
python3 scripts/regenerate_example_report.py
```

---

## Deployment

### Test Locally
```bash
# Start local server
python3 -m http.server 8000 --directory output

# Open in browser
# http://localhost:8000/resources-basket-pages-example-report.html
```

### Deploy to Netlify
```bash
python3 scripts/deploy_netlify.py
```

---

## Key Concepts

### Two-Pass Analysis

1. **Pass 1 (Observe):** Claude analyzes screenshots, returns `observation.json`
2. **Pass 2 (Score):** Claude scores against `observation.json`, returns `analysis.json`

### Evidence Citations

Each criterion score includes an `evidence` field showing exactly which observation supported the score.

### Project-Local Output

Reports are written to `output/` inside the repository - not to a separate location. This keeps everything versionable together.

---

## Getting Help

### Check Documentation
- `README.md` - Full feature documentation
- `docs/ARCHITECTURE.md` - System design
- `PROJECT_TODO.md` - Active work tracking

### Version Check
```bash
python3 main.py --version
```

### Report Issues
Include in your report:
- Version from `python3 main.py --version`
- Steps to reproduce
- Error message (if any)
- Screenshot of issue

---

## Further Reading

- [Architecture & Extensibility Guide](ARCHITECTURE.md)
- [Quick Start Deployment Guide](docs/deployment/QUICKSTART.md)
- [Netlify Deployment Guide](docs/deployment/NETLIFY.md)
- [Bot Detection Guide](docs/BOT_DETECTION_GUIDE.md)
