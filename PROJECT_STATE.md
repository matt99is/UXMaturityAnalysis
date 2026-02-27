# Project State: UX Maturity Analysis

**Version:** 1.7.0
**Status:** Production Ready
**Last Updated:** 2026-02-27
**Context Load Priority:** HIGH (load this file first)

---

## Active Work

Items currently in progress. Move to Completed when done.

### [None Currently Active]

> When starting work, add item here with:
> - What you're doing
> - Key files involved
> - Any blockers

---

## Next Up

Prioritized backlog. Top items = highest priority.

### 1. Auto-build CSS in Report Generation
**Priority:** High | **Estimated:** 1 hour
- Currently: manual `python3 scripts/build_css.py` step
- Need: auto-build when generating reports
- Files: `src/utils/html_report_generator.py`, `scripts/build_css.py`

### 2. Create `_sidebar.jinja2` Partial
**Priority:** Medium | **Estimated:** 30 min
- Extract sidebar markup from templates
- Files: `templates/partials/`, `templates/index.html.jinja2`

### 3. Create `_header.jinja2` Partial
**Priority:** Medium | **Estimated:** 20 min
- Extract header markup from templates
- Files: `templates/partials/`

### 4. Create `_footer.jinja2` Partial
**Priority:** Low | **Estimated:** 20 min
- Extract footer markup if present
- Files: `templates/partials/`

### 5. Remove Orphaned CSS Rules
**Priority:** Low | **Estimated:** 1 hour
- Audit CSS for unused rules
- Files: `css/`

### 6. GitHub Actions Auto-Deploy
**Priority:** Future | **Estimated:** 2 hours
- Create `.github/workflows/deploy.yml`
- Configure Netlify deployment
- Files: `.github/workflows/`

---

## Recently Completed

Last 10 completed items for context.

- [x] v1.7.0: Template partials (`_theme_toggle.jinja2`, `_brand.jinja2`)
- [x] v1.7.0: WCAG AA accessibility improvements (font sizes, contrast)
- [x] v1.7.0: Live chart resize with Plotly.Plots.resize()
- [x] v1.7.0: Theme toggle (dark/light) with localStorage persistence
- [x] v1.7.0: Code quality tooling (flake8, black, isort, pre-commit)
- [x] v1.7.0: Developer docs (ONBOARDING.md, COMMON_TASKS.md)
- [x] v1.7.0: Report card layout fixes (class naming conflicts)
- [x] v1.7.0: Index generation via Jinja2 templates
- [x] v1.6.0: Two-pass analysis pipeline (observation.json + analysis.json)
- [x] v1.6.0: Project-level reports index at output/index.html

---

## Architecture Decisions

Key patterns and decisions for AI context.

### Tech Stack
- Python 3.9+, Playwright, Claude API, Jinja2, Sass/SCSS, Plotly

### Pipeline Flow
```
Capture (Playwright) → Observe (Pass 1) → Score (Pass 2) → Generate Reports
```

### Key Patterns

**Config-driven criteria:** `criteria_config/*.yaml` defines page types (no code changes needed)

**Template partials:** `templates/partials/` for shared markup
- `_brand.jinja2` - brand header
- `_theme_toggle.jinja2` - theme switcher
- (Pending: sidebar, header, footer)

**Design tokens:** `css/_variables.scss` for theming
- Dark/light theme support
- WCAG AA compliant colors

**Sequential AI analysis:** 90s delay between competitors (rate limit compliance)

### Output Structure
```
output/
├── index.html              # Master index (auto-generated)
└── audits/{date}_{type}/   # Per-audit folder
    ├── _comparison_report.md
    ├── {audit}_report.html
    ├── _audit_summary.json
    └── {competitor}/
        ├── screenshots/
        ├── observation.json
        └── analysis.json
```

### Code Quality
- Linters: flake8, black, isort
- Config: `pyproject.toml`, `.flake8`, `.pre-commit-config.yaml`
- Max line length: 100

---

## Quick Reference

```bash
# Run analysis
python3 main.py --config competitors.json --analysis-type basket_pages

# Regenerate reports from existing screenshots
python3 scripts/reanalyze_screenshots.py output/audits/2026-02-24_basket_pages

# Build CSS (manual until auto-build implemented)
python3 scripts/build_css.py

# Run linters
pre-commit run --all-files

# View reports locally
python3 -m http.server 8000 --directory output
```

---

## Key Files

| Path | Purpose |
|------|---------|
| `main.py` | Entry point & orchestration |
| `src/analyzers/` | Screenshot capture, Claude analysis |
| `src/utils/` | Report generation, HTML output |
| `criteria_config/*.yaml` | Page-type criteria definitions |
| `templates/*.jinja2` | HTML report templates |
| `templates/partials/*.jinja2` | Reusable template components |
| `css/*.scss` | Sass stylesheets (8 partials) |
| `scripts/` | Utility scripts (build, deploy, reanalyze) |
| `docs/` | Documentation |

---

## Documentation Index

| File | Purpose |
|------|---------|
| `README.md` | Full project documentation |
| `CHANGELOG.md` | Version history |
| `docs/ARCHITECTURE.md` | Technical architecture |
| `docs/ONBOARDING.md` | Developer onboarding guide |
| `docs/COMMON_TASKS.md` | Quick reference for frequent tasks |
| `docs/deployment/` | Netlify deployment guides |
