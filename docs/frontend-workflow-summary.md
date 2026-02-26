# UX Maturity Analysis - HTML Frontend Development Summary

## Project Overview

Building a professional, production-grade HTML/CSS frontend for displaying UX maturity analysis reports. The system generates competitor analysis reports with visualizations, screenshots, annotations, and evidence.

**Current Status:** In development - working on example report until visuals are finalized, then will integrate with pipeline and deploy to Netlify via GitHub Actions.

---

## Architecture

### Tech Stack
- **Templates:** Jinja2 (`templates/index.html.jinja2`, `templates/report.html.jinja2`)
- **Styling:** Sass/SCSS with build pipeline (not inline CSS)
- **Data Generator:** `src/utils/html_report_generator.py`
- **Charts:** Plotly.js (CDN)
- **Deployment Target:** Netlify via GitHub Actions

### CSS Architecture (Modular Sass)
Location: `css/`

```
css/
├── main.scss           # Entry point (imports all partials)
├── _variables.scss     # Design tokens (colors, spacing, typography, breakpoints)
├── _base.scss          # CSS reset, custom properties, theme switching
├── _layout.scss        # Grid layout (sidebar + main content)
├── _components.scss    # Reusable UI components (cards, badges, lozenges)
├── _sections.scss      # Specialized sections (metrics, insights, rankings)
├── _competitors.scss   # Screenshot previews, lightbox, annotations
└── _mobile.scss        # All responsive styles with breakpoints
```

### Build Pipeline

**CSS Build:**
```bash
# Python script (recommended)
python3 scripts/build_css.py

# Or shell alternative
bash scripts/build_css.sh

# Output: output/css/main.css (currently ~20KB compressed)
```

**Report Generation:**
```bash
# Generate example report for visual iteration
python3 scripts/regenerate_example_report.py

# Output: output/resources-basket-pages-example-report.html
```

---

## Key Design Decisions

### 1. External CSS (Not Inline)
- Templates reference: `<link rel="stylesheet" href="css/main.css">`
- CSS copied to output directory by `HTMLReportGenerator._copy_css()`
- Allows easy design iteration without touching Python code

### 2. Design Token System
Colors defined in `css/_variables.scss`:
```scss
$teal: #14b8a6;
$green: #22c55e;
$amber: #f59e0b;
$red: #ef4444;
```

Applied via CSS custom properties for theme switching (dark/light mode)

### 3. Responsive Breakpoints
```scss
$breakpoint-tablet: 1024px;
$breakpoint-mobile: 768px;
$breakpoint-mobile-sm: 480px;
```

### 4. Smooth Transitions
- `.app`: `transition: grid-template-columns .2s`
- `.sidebar`: `transition: opacity .2s, transform .2s`
- Prevents "snap" effect when crossing breakpoints

---

## Data Structure

### Sample Data Location
`sample_data/basket_pages_example.json`

### Key Fields
```json
{
  "competitors": [
    {
      "id": "competitor-id",
      "name": "Competitor Name",
      "overall_score": 7.5,
      "color": "#14b8a6",
      "color_dim": "rgba(20, 184, 166, 0.1)",
      "initial": "C",
      "success": true,
      "criteria_scores": [...],
      "evidence_items": [...],
      "screenshot_metadata": [
        {
          "filepath": "screenshots/desktop.png",  // In sample_data: relative to output/
                                                   // Generator converts to absolute internally
          "annotations": [
            {
              "type": "strength|weakness|opportunity",
              "icon": "icon-name",
              "text": "Annotation text"
            }
          ]
        }
      ]
    }
  ],
  "report_title": "Full Report Title",
  "report_short_title": "Short Title",
  "category": "Industry Category"
}
```

---

## Current Issues (Need Fixing)

### 1. Screenshot Visibility - RESOLVED ✓
**Problem:** Screenshots not appearing in report despite files existing

**Root Cause:**
- Regeneration script was using `competitor_name` instead of `site_name` (generator expects `site_name`)
- Script was using `screenshots` key instead of `screenshot_metadata`
- Relative paths in sample data need to be converted to absolute paths

**Fix Applied:**
Updated `scripts/regenerate_example_report.py`:
- Changed `competitor_name` → `site_name`
- Changed `screenshots` → `screenshot_metadata`
- Added path conversion: relative → absolute before passing to generator

**Current State:**
- Screenshots now render correctly in report
- Paths are `screenshots/desktop.png` relative to output directory

---

### 2. Visual Analysis Section Width
**Problem:** Section labels may be truncated, charts may need better sizing

**Location:** `templates/report.html.jinja2` (visual analysis section, ~lines 290-340)

**CSS Files:** `css/_sections.scss`

---

### 3. Plotly Graph Labeling
**Problem:** Chart labels may need improvement for clarity

**Location:**
- Template JavaScript (Plotly configuration)
- `templates/report.html.jinja2` (~lines 300-350)

---

## Workflow for Visual Iteration

### Step 1: Modify CSS
Edit files in `css/` directory

### Step 2: Rebuild CSS
```bash
python3 scripts/build_css.py
```

### Step 3: Regenerate Example Report
```bash
python3 scripts/regenerate_example_report.py
```

### Step 4: View in Browser
Open: `file:///home/matt99is/projects/UXMaturityAnalysis/output/resources-basket-pages-example-report.html`

### Step 5: Repeat until satisfied

---

## Template Updates Already Applied

### `templates/index.html.jinja2`
- Removed inline CSS (~570 lines removed)
- Added: `<link rel="stylesheet" href="css/main.css">`
- Current size: ~220 lines (was ~791)

### `templates/report.html.jinja2`
- Removed inline CSS (~1,300 lines removed)
- Added: `<link rel="stylesheet" href="css/main.css">`
- Fixed event propagation: `toggleCompetitor(id, event)` with `event.stopPropagation()`
- Evidence section removed - now only within competitor sections
- Current size: ~1,000 lines (was ~2,358)

---

## Generator Updates

### `src/utils/html_report_generator.py`
Added methods for CSS integration:
- `_CSS_DIR`: Points to `output/css/`
- `_build_css()`: Builds CSS from Sass source
- `_copy_css()`: Copies built CSS to output directory

---

## Server for Remote Development

```bash
# Find available port
python3 -m http.server 8000 2>&1 | head -1 || echo "Port 8000 in use, trying alternative..."

# Start server on available port (e.g., 37449)
cd output
python3 -m http.server 37449

# Access via SSH tunnel
# ssh -L 8888:localhost:37449 remote-host
# Then open http://localhost:8888/resources-basket-pages-example-report.html
```

---

## Future Work (After Visuals Finalized)

### 1. Integrate CSS Build into Generator
- Ensure `HTMLReportGenerator` always builds CSS on report generation
- CSS should be auto-generated, not manual step

### 2. GitHub Actions Workflow
Create `.github/workflows/deploy.yml`:
- Build CSS
- Generate report
- Deploy to Netlify

### 3. Netlify Integration
- Configure build settings
- Set up domain/URL

---

## Key File Locations

| Purpose | Path |
|---------|------|
| CSS Source | `css/` |
| CSS Output | `output/css/main.css` |
| Templates | `templates/` |
| Sample Data | `sample_data/basket_pages_example.json` |
| Generator | `src/utils/html_report_generator.py` |
| Build Scripts | `scripts/build_css.py`, `scripts/regenerate_example_report.py` |
| Example Report | `output/resources-basket-pages-example-report.html` |
| Screenshot Images | `output/screenshots/` |

---

## Quick Resume Commands

```bash
# Build CSS
python3 scripts/build_css.py

# Regenerate example report
python3 scripts/regenerate_example_report.py

# Start local server
cd output && python3 -m http.server 8888

# Open report
# http://localhost:8888/resources-basket-pages-example-report.html
```

---

## Notes for Next Session

### Documentation for Context Recovery
If context is lost, read these files in order:
1. `docs/plan.md` - Full project roadmap and phases
2. `docs/todo.md` - Active and completed task list
3. `docs/frontend-workflow-summary.md` - This file (technical details)

### Issues Resolved (Feb 25, 2026)

**Screenshot Visibility (RESOLVED ✓):**
- Problem: Screenshots not appearing in report
- Root cause: Data key mismatch between regeneration script and generator
- Fix: Updated `scripts/regenerate_example_report.py`:
  - Changed `competitor_name` → `site_name` (generator expects `site_name`)
  - Changed `screenshots` → `screenshot_metadata` (generator expects `screenshot_metadata`)
  - Added path conversion: relative → absolute before passing to generator
- Result: Screenshots now render correctly with paths `screenshots/desktop.png`

### Remaining Issues

1. **Visual analysis section width** - CSS/layout fixes needed for label truncation and chart sizing
2. **Plotly graph labeling** - JavaScript configuration improvements for clarity

### Workflow Reminder

**Visual Iteration Loop:**
1. Make CSS/HTML changes
2. Run: `python3 scripts/build_css.py`
3. Run: `python3 scripts/regenerate_example_report.py`
4. View at: `http://localhost:8888/resources-basket-pages-example-report.html`
5. Repeat until satisfied

**After Visuals Finalized:**
1. Ensure pipeline produces same output as example report
2. Set up GitHub Actions workflow
3. Deploy to Netlify

The goal is to iterate on `resources-basket-pages-example-report.html` until visuals are perfect, then lock that in as the pipeline output.
