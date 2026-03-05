# Common Developer Tasks

Quick reference for frequently performed tasks in this project.

---

## Running the tool

Always use `./run.sh`. It handles tmux session protection automatically.

| What you want | Command |
|---|---|
| Full interactive menu | `./run.sh` |
| Reanalyse existing audit | `./run.sh --reanalyze output/audits/<folder>` |
| Reanalyse, re-run scoring | `./run.sh --reanalyze output/audits/<folder> --force` |
| Reanalyse, redo everything | `./run.sh --reanalyze output/audits/<folder> --force-observe --force` |
| Deploy to Netlify | `./run.sh --deploy` |
| Deploy to Netlify (verbose logs) | `./run.sh --deploy --verbose` |

Deploy output behavior:
- Default deploy output is concise (success/failure summary).
- Use `--verbose` to show full Netlify CLI logs.

Tmux wrapper behavior:
- Enables mouse scrolling in the `analysis` session.
- Increases tmux scrollback history (`history-limit=200000`).
- Writes run logs to `output/logs/analysis_YYYYMMDD_HHMMSS.log`.

Manual scroll keys (if needed):
- Enter scroll mode: `Ctrl+B`, then `[`
- Exit scroll mode: `q`

---

## Vault Hygiene

The vault project note is startup context only, not a changelog.

- Policy source: `AGENTS.md` -> "Vault Note Contract (Anti-Bloat)".
- Validation command:

```bash
python3 scripts/check_vault.py --strict-missing
```

What the check enforces:
- hard max size (lines + characters)
- required section structure
- per-section bullet caps
- no changelog-style dated/versioned bullets in `Current status`

This check runs in pre-commit on this repo before commit.

---

## Competitor URL Validation

During fresh analysis, competitor URLs are loaded from `competitors/*.yaml` and HEAD-checked.
If a URL is corrected in interactive mode, the new value is saved back into that YAML file.
Current status: `Supervised` is wired to interactive capture.
`Automated` now runs unattended capture (`main.py --auto`) with no per-site prompts.

Supervised preflight now fails fast if noVNC is not configured/reachable.
Required env: `NOVNC_URL` (or `NOVNC_HOST` + optional `NOVNC_PORT`).
Optional env:
- `SUPERVISED_READY_TIMEOUT_SEC` (default `900`)
- `SUPERVISED_HEARTBEAT_SEC` (default `30`)

Automated mode defaults (optional overrides):
- `AUTOMATED_DISPLAY` (default `:99`)
- `AUTOMATED_HEADLESS` (default `false`)
- `AUTOMATED_URL_VALIDATION_STRICT` (default `false`; continue with full set when HEAD checks fail)
- `DEBUG_AUTOMATED_ERRORS` (default `false`; print full low-level launch errors)
- `AUTOMATED_CAPTURE_MAX_ATTEMPTS` (default `2`)
- `AUTOMATED_CAPTURE_RETRY_BACKOFF_SEC` (default `5`)
- `AUTOMATED_CAPTURE_DELAY_MIN_SEC` / `AUTOMATED_CAPTURE_DELAY_MAX_SEC` (defaults `3` / `10`)

Automated preflight now runs before capture:
- headed mode display check (`xdpyinfo` probe when available)
- competitor hostname DNS resolution
- browser launch/close probe

UX simplification:
- The printed session URL now includes noVNC auto-connect defaults (`autoconnect=true`, `resize=remote`, `reconnect=true`).
- Supervised capture prompt is a 3-step instruction block: open session URL -> prepare page -> press Enter.

For capture rollout, use this order:
1. `petfood-smoke` (1 competitor) for smoke tests.
2. `petfood-test` (3 competitors) for canary validation.
3. `petfood` (16 competitors) only after both pass.

### Supervised smoke canary

Use this before any wider capture run:

```bash
curl -sS -I "${NOVNC_URL:-http://localhost:6080/vnc.html}" | head -n 1
./run.sh
# choose: Fresh analysis -> basket_pages -> petfood-smoke -> Supervised
```

Expected behavior:
- CLI prints `✓ Supervised preflight checks passed`
- Browser guidance URL is shown
- Terminal prints heartbeat while waiting for Enter
- If no Enter is received before timeout, the competitor fails with a clear timeout message

### Automated smoke canary

Use this before larger unattended runs:

```bash
echo "DISPLAY=${AUTOMATED_DISPLAY:-:99}"
./run.sh
# choose: Fresh analysis -> basket_pages -> petfood-smoke -> Automated
```

Expected behavior:
- No per-site `Continue? (Y/r/s)` prompt
- Capture runs unattended competitor-by-competitor
- Brief pacing delay is printed between competitors

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
   ./run.sh   # then choose "Fresh analysis" → your new page type
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
./run.sh --deploy
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
# Run analysis (interactive)
./run.sh

# Deploy
./run.sh --deploy

# Reanalyse existing audit
./run.sh --reanalyze output/audits/<folder>

# Rebuild CSS
python3 scripts/build_css.py

# Regenerate example report
python3 scripts/regenerate_example_report.py

# Test locally
python3 -m http.server 8000 --directory output
```

---

## For More Help

See [Developer Onboarding Guide](ONBOARDING.md) for comprehensive documentation.
