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

### 1. Netlify Auto-Deploy
**Priority:** High | **Estimated:** 2-3 hours | **Plan:** `docs/archive/2026-02/2026-02-26-netlify-auto-deploy-implementation.md`
- One-time setup wizard (`scripts/setup_netlify.py`)
- Auto-deploy after analysis via `deploy_reports()` in main.py
- Custom domain: `analysis.mattlelonek.co.uk`
- `--no-deploy` flag for manual control
- Files: `scripts/setup_netlify.py`, `main.py`, `netlify.toml`

---

## Recently Completed

Last 10 completed items for context.

- [x] v1.7.0: Template partials (`_theme_toggle.jinja2`, `_brand.jinja2`)
- [x] v1.7.0: Auto-build CSS in report generation (`_build_css()` in html_report_generator.py)
- [x] v1.7.0: WCAG AA accessibility improvements (font sizes, contrast)
- [x] v1.7.0: Live chart resize with Plotly.Plots.resize()
- [x] v1.7.0: Theme toggle (dark/light) with localStorage persistence
- [x] v1.7.0: Code quality tooling (flake8, black, isort, pre-commit)
- [x] v1.7.0: Developer docs (ONBOARDING.md, COMMON_TASKS.md)
- [x] v1.7.0: Report card layout fixes (class naming conflicts)
- [x] v1.7.0: Index generation via Jinja2 templates
- [x] v1.6.0: Two-pass analysis pipeline (observation.json + analysis.json)

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
- Note: Sidebars are intentionally different between index and report templates

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
| `docs/archive/` | Historical design docs (see INDEX.md) |
