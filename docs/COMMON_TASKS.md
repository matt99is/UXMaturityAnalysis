# Common Developer Tasks

Quick reference for frequently performed tasks in this project.

---

## Add a New Analysis Type (Page Type)

**When:** You want to analyze a new type of page (e.g., search results, product listing, account page)

**Steps:**
1. Create new criteria file:
   ```bash
   cp criteria_config/basket_pages.yaml criteria_config/your_new_page_type.yaml
   ```

2. Edit the criteria file:
   ```yaml
   name: "Your Page Type Analysis"
   requires_interaction: true  # or false depending on page
   viewports:
     - name: "desktop"
       width: 1920
       height: 1080
     - name: "mobile"
       width: 375
       height: 812
   criteria:
     - id: "criterion_id"
       name: "Criterion Name"
       weight: 10
       description: "What this criterion evaluates"
       evaluation_points:
         - "Good implementation looks like..."
       benchmarks:
         source: "Research Source"
           finding: "Research finding here"
   ```

3. Run analysis:
   ```bash
   python3 main.py --config competitors.json --analysis-type your_new_page_type
   ```

**No code changes needed** - the system automatically loads and uses your new YAML config.

---

## Change Design Colors

**When:** You want to change the color scheme

**Files to edit:**
- `css/_variables.scss` - This contains all color definitions

**Color categories:**
- Dark theme: `$bg-dark`, `$surface-dark`, `$text-dark`, etc.
- Light theme: `$bg-light`, `$surface-light`, `$text-light`, etc.
- Accents: `$teal`, `$green`, `$amber`, `$red`

**Workflow:**
1. Edit `css/_variables.scss`
2. Rebuild CSS: `python3 scripts/build_css.py`
3. Test: `python3 scripts/regenerate_example_report.py`
4. Open report in browser to verify

**Example - Changing teal color:**
```scss
// Old
$teal: #14b8a6;

// New
$teal: #0ea5e9;
$teal-light: #0d9488;
```

---

## Change Font Sizes

**When:** Text is too small or too large

**Files to edit:**
- `css/_variables.scss` - Font scale section

**Current scale:**
```scss
$font-size-xs: 12px;
$font-size-sm: 13px;
$font-size-base: 16px;
$font-size-md: 18px;
$font-size-lg: 20px;
$font-size-xl: 24px;
$font-size-2xl: 28px;
$font-size-3xl: 42px;
```

**Example - Increase base font:**
```scss
// Old
$font-size-base: 16px;

// New
$font-size-base: 18px;
```

**Remember to rebuild CSS after changes.**

---

## Add New Section to HTML Report

**When:** You want to add a new section to the generated HTML reports

**Files to edit:**
1. `src/utils/html_report_generator.py` - Generate data for the section
2. `templates/report.html.jinja2` - Add the HTML for the section

**Steps:**

1. Add data in `generate_report()` function:
   ```python
   # Example for a new insights section
   context['new_insights'] = {
       'title': 'My New Section',
       'items': [...]  # Your data here
   }
   ```

2. Add to report template:
   ```html
   {% if new_insights %}
   <section id="new-insights" class="section">
     <div class="section-header">
       <h2 class="section-title">{{ new_insights.title }}</h2>
     </div>
     <!-- Your content here -->
   </section>
   {% endif %}
   ```

3. Regenerate to test:
   ```bash
   python3 scripts/regenerate_example_report.py
   ```

---

## Modify Chart Configuration

**When:** You want to change chart colors, layout, or behavior

**File to edit:** `src/utils/html_report_generator.py`

**Functions:**
- `_create_radar_chart()` - Radar/spider chart
- `_create_heatmap()` - Feature matrix heatmap

**Example - Change radar chart colors:**
```python
# Old
colors = ['#14b8a6', '#22c55e', '#f59e0b']

# New
colors = ['#0ea5e9', '#22c55e', '#f59e0b', '#6366f1']
```

**Example - Move radar legend below chart:**
```python
# Old
fig.update_layout(
    legend={'bgcolor': 'rgba(0,0,0,0)', 'orientation': 'v', 'y': 0.5}
)

# New
fig.update_layout(
    legend={'bgcolor': 'rgba(0,0,0,0)', 'orientation': 'h', 'y': -0.05, 'x': 0.5, 'xanchor': 'center'}
)
```

---

## Regenerate Example Report

**When:** You've made template or styling changes and want to test them

**Command:**
```bash
python3 scripts/regenerate_example_report.py
```

**What it does:**
- Uses latest templates
- Uses latest CSS
- Regenerates example report with current data
- No re-capturing of screenshots needed

---

## Deploy Reports

### Test Locally First
```bash
# Start local server
python3 -m http.server 8000 --directory output

# Open in browser
# http://localhost:8000/resources-basket-pages-example-report.html
```

### Deploy to Netlify
```bash
# Deploy all output to Netlify
python3 scripts/deploy_netlify.py

# Deploy specific folder
# Edit scripts/deploy_netlify.py to change the path
```

---

## Common Issues

### CSS Changes Not Applying

**Symptoms:** You edited SCSS but report looks the same

**Solution:**
```bash
# Rebuild CSS
python3 scripts/build_css.py
```

---

### Template Changes Not Appearing

**Symptoms:** You edited a template but output hasn't changed

**Solution:**
```bash
# Regenerate report to rebuild from template
python3 scripts/regenerate_example_report.py
```

---

### Screenshot Capture Issues

**Symptoms:** Browser opens but captures blank images

**Causes:**
- Page not fully loaded
- Animation still running
- Wrong viewport dimensions

**Solutions:**
1. Manually wait for page load
2. Check viewport settings in `.env`
3. Use `--manual-mode` with your own screenshots

---

## Quick Reference

### File Locations
- Templates: `templates/`
- CSS: `css/`
- Scripts: `scripts/`
- Generated reports: `output/`

### Key Commands
```bash
# Run analysis
python3 main.py --config competitors.json

# Rebuild CSS
python3 scripts/build_css.py

# Regenerate example report
python3 scripts/regenerate_example_report.py

# Test locally
python3 -m http.server 8000 --directory output

# Deploy
python3 scripts/deploy_netlify.py
```

---

## For More Help

See [Developer Onboarding Guide](ONBOARDING.md) for comprehensive documentation.
