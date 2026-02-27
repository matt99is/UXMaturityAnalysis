# Project State: UX Maturity Analysis

**Version:** 1.9.0
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

### [No pending tasks]

All planned work complete. Ready for new feature requests.

---

## Recently Completed

Last 10 completed items for context.

- [x] v1.9.0: New output structure (`/{type}/{date}.html`) for better URL organization
- [x] v1.9.0: Type index pages (e.g., `/basket-pages/`) showing all reports of that type
- [x] v1.9.0: Updated audit_organizer.py for new directory structure
- [x] v1.9.0: Updated html_report_generator.py with type/date parameters
- [x] v1.9.0: Updated generate_index.py for new structure + legacy support
- [x] v1.8.0: Automatic Netlify deployment (setup wizard + `deploy_reports()` in main.py)
- [x] v1.8.0: `--no-deploy` CLI flag for manual control
- [x] v1.8.0: `netlify.toml` build configuration
- [x] v1.7.0: Template partials (`_theme_toggle.jinja2`, `_brand.jinja2`)
- [x] v1.7.0: Auto-build CSS in report generation (`_build_css()` in html_report_generator.py)

---

## Architecture Decisions

Key patterns and decisions for AI context.

### Current State (Prototype)

Single-tenant, file-based static site. All reports visible to anyone with access.

**Future Direction (Documented)**

This prototype is designed to evolve into a multi-tenant SaaS:

| Aspect | Now | Future |
|--------|-----|--------|
| Tenants | Single | Multiple (agencies, brands) |
| Competitors | Global config | Per-tenant lists |
| Benchmarks | Fixed criteria | Per-tenant custom benchmarks |
| Auth | Netlify password | Per-user accounts |
| Storage | Static files | Database (Supabase) |
| URLs | `/basket-pages/` | `/{tenant}/basket-pages/` |

**Future Data Model:**
```
Tenant
├── competitors: [{ name, url, page_types[] }]
├── benchmarks: [{ name, criteria, weights }]
└── reports: [{ type, date, generated }]

User → belongs to Tenant
Report → belongs to Tenant, uses Tenant's competitors + benchmarks
```

**Migration Path:**
1. Add tenant slug to URL structure (`/{tenant}/basket-pages/`)
2. Move config files into tenant folders
3. Add Supabase for auth + metadata
4. Keep reports as static HTML (generated on demand)

See `docs/ARCHITECTURE.md` for technical details.

---

### Tech Stack
- Python 3.9+, Playwright, Claude API, Jinja2, Sass/SCSS, Plotly

### Pipeline Flow
```
Capture (Playwright) → Observe (Pass 1) → Score (Pass 2) → Generate Reports → Deploy (Netlify)
```

**Live site:** https://analysis.mattlelonek.co.uk

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

**New structure (v1.9.0+):**
```
output/
├── index.html                    # Main dashboard
├── css/main.css                  # Compiled CSS
├── basket-pages/                 # Type directory
│   ├── index.html                # List of all basket reports
│   ├── 2026-02-27.html           # Specific dated report
│   ├── 2026-02-27.json           # Report summary data
│   └── screenshots/
│       └── 2026-02-27/
│           └── {competitor}/
│               ├── desktop.png
│               ├── mobile.png
│               ├── observation.json
│               └── analysis.json
├── product-pages/
│   └── ...
└── audits/                       # Legacy structure (still supported)
    └── {date}_{type}/
        ├── _comparison_report.md
        ├── {audit}_report.html
        └── ...
```

**URL structure:**
- `/` → Main dashboard
- `/basket-pages/` → List of all basket page reports
- `/basket-pages/2026-02-27.html` → Specific report

### Code Quality
- Linters: flake8, black, isort
- Config: `pyproject.toml`, `.flake8`, `.pre-commit-config.yaml`
- Max line length: 100

---

## Quick Reference

```bash
# Run analysis (auto-deploys to Netlify)
python3 main.py --config competitors.json --analysis-type basket_pages

# Run analysis without deploying
python3 main.py --config competitors.json --no-deploy

# Regenerate reports from existing screenshots
python3 scripts/reanalyze_screenshots.py output/audits/2026-02-24_basket_pages

# Manual deploy
netlify deploy --prod --dir=output

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
