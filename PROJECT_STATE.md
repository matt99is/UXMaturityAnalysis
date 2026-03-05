# Project State: UX Maturity Analysis

**Version:** 1.13.0
**Status:** Production Ready
**Last Updated:** 2026-03-05
**Context Load Priority:** HIGH (load this file first)

---

## Active Work

Items currently in progress. Move to Completed when done.

### No Active Phase 1 Work (as of 2026-03-04)

Scoring reliability overhaul is complete on `main` (commit `85baa40`, 2026-03-03).

Smoke competitor set is available at `competitors/petfood-smoke.yaml` (1 competitor) for fast checks.
Canary competitor set is available at `competitors/petfood-test.yaml` (3 competitors) for vertical-slice validation.
CLI status: `Supervised` routes to interactive capture and `Automated` now routes to unattended capture (`main.py --auto`).
Automated defaults: headed browser with `DISPLAY=:99`, no per-site prompts, retry/backoff + pacing controls via env vars.
Supervised hardening: startup preflight now validates noVNC URL/reachability, and Enter-wait uses timeout + heartbeat (`SUPERVISED_READY_TIMEOUT_SEC`, `SUPERVISED_HEARTBEAT_SEC`).

---

## Next Up

### Focus Shift After Phase 1 Completion

Scoring reliability overhaul is complete (commit `85baa40`, 2026-03-03). Next implementation focus is browser capture infrastructure (Phase 2 and Phase 3 items below).

---

### Web GUI: Human-in-the-Loop Browser Capture

**Goal:** Enable web GUI users to see and interact with browser sessions running on the remote headless server. Critical for bot-protected sites (CAPTCHA solving), login-gated flows, and complex page setup (adding items to basket).

**Research doc:** `docs/research/remote-human-in-the-loop-browser-capture-2026.md`

**Recommended approach:** VNC + noVNC
- Xvfb provides virtual display (`:99`, `1920x1080x24`)
- x11vnc exposes display via VNC protocol
- websockify bridges VNC to WebSockets
- noVNC (HTML5 client) embedded in web GUI via iframe

**Implementation phases:**
1. Session pool manager (allocate/release browser sessions)
2. Display allocator (manage Xvfb display numbers)
3. Web GUI integration (iframe + "Ready to Capture" flow)

**Effort:** 2-3 days for MVP

---

### Full Automation: Bot-Bypass Screenshot Capture

**Goal:** Run the full capture pipeline unattended on the remote Ubuntu server — no interactive prompts, no manual screenshot upload — while reliably loading real ecom sites that use Cloudflare, DataDome, etc.

**Research doc:** `/home/matt99is/projects/Resources/ux-analysis/bot-detection-ecom-screenshots-2026.md`

#### Why vanilla Playwright + headless won't work

Six layers of bot detection exist on major ecom sites. The critical ones for this project:
- **IP reputation** — VPS/cloud IPs (Hetzner, DigitalOcean) are flagged before JS even runs
- **CDP detection** — standard Playwright's `Runtime.enable` command is a known bot signal
- **Browser fingerprint** — headless Chrome returns SwiftShader WebGL renderer, empty plugin list
- **Consistency checks** — timezone/locale must match proxy IP, every signal must be internally coherent

`headless=True` is a non-starter for anything above basic Cloudflare. Headed mode via Xvfb is required.

#### Recommended stack (from research)

| Component | Choice |
|-----------|--------|
| Browser automation | **Patchright** — drop-in Playwright, patches CDP `Runtime.enable` leak |
| Browser | **Google Chrome** (via `patchright install chrome`) — better fingerprint than open-source Chromium |
| Virtual display | **Xvfb** as persistent systemd service — enables headed mode on server |
| HTTP headers | **BrowserForge** (header generation only) — statistically realistic headers |
| IP layer | **ISP or residential proxy** — essential if server is a VPS on a datacenter ASN |
| Session management | **Persistent user data dir** — reuse browser profiles (fresh profile = bot signal) |

#### Implementation steps

1. **Server setup**
   - Install Xvfb, Chrome dependencies, MS core fonts (`ttf-mscorefonts-installer`)
   - Create persistent Xvfb systemd service (`DISPLAY=:99`, `1920x1080x24`)
   - `pip install patchright browserforge && patchright install chrome`

2. **Replace Playwright with Patchright in `screenshot_capture.py`**
   - `from patchright.async_api import async_playwright`
   - Use `launch_persistent_context()` with `channel="chrome"`, `headless=False`, `no_viewport=True`
   - Separate persistent profile dirs for desktop and mobile (`browser_profiles/desktop/`, `browser_profiles/mobile/`)
   - Set `timezone_id` and `locale` to match proxy exit location

3. **Add proxy support**
   - Pass `proxy={"server": ..., "username": ..., "password": ...}` to `launch_persistent_context()`
   - Config via environment variables or `config.py`
   - ISP proxies (static residential) preferred over rotating residential for session consistency

4. **Add `--auto` mode to `main.py`**
   - No interactive prompts, no Y/R/S confirmation
   - Random delay (3–10s) between URL requests — `asyncio.sleep(random.uniform(3, 10))`
   - Max concurrency: 2–3 URLs, never parallel on same domain
   - Idempotent: skip URLs where screenshot already exists
   - Scroll simulation before screenshot (triggers lazy-loaded content)

5. **Validation before going live**
   - Test against `bot.sannysoft.com` (CDP/webdriver flags)
   - Test against `pixelscan.net` (fingerprint consistency)
   - Test against `abrahamjuliot.github.io/creepjs` (target trust score >85%)

#### Realistic success rates by site type

| Site type | Expectation |
|-----------|-------------|
| No serious protection (small/mid UK retailers) | ✓ Works easily |
| Cloudflare normal (Next, M&S, Boots, Currys) | ✓ Works with Patchright + residential IP |
| Cloudflare Bot Management / DataDome (ASOS, Farfetch) | ~80–90% with correct setup |
| Kasada (JD Sports) | Occasional failures expected — build retry logic |

#### Interim workaround (current)

`reanalyze_screenshots.py` + manual screenshot upload. Keeps analysis pipeline working while automation is being built.

---

### Headless auto-capture mode (`--headless` flag) — Interim/simpler option

Interactive mode requires a visible browser, which doesn't work on a headless remote server (VS Code Remote SSH). Add a `--headless` flag that:
- Launches Playwright with `headless=True`
- Uses `capture_multiple_viewports` instead of `capture_with_interaction` (no user prompts, no display needed)
- Skips the Y/R/S confirmation prompt after each capture
- Bot-protected sites will fail silently — document this limitation

**Files:** `main.py` (add `--headless` CLI arg, branch capture path), `screenshot_capture.py` (no changes needed, already supports headless)

**Note:** This is a simpler but weaker option. Fine for unprotected or lightly-protected sites. For full ecom coverage, see the full automation item above.

---

## Recently Completed

Last 10 completed items for context.

- [x] 2026-03-05: Automated capture mode enabled in unified CLI (`Automated` -> `main.py --auto`) with unattended screenshot flow, retry/backoff, and capture pacing controls
- [x] v1.13.0: Competitor card redesign — attributed evidence cards, strengths/vulnerabilities split (html_report_generator.py + _components.scss + report.html.jinja2)
- [x] v1.13.0: Radar chart — all competitors included, top 3 visible, rest legendonly (html_report_generator.py)
- [x] v1.13.0: Rankings — uniform score colour, tier badge CSS classes, colour-coded by tier (_sections.scss + _components.scss)
- [x] v1.13.0: AI trope removal — decorative icons, teal glow shadow, left border on evidence items
- [x] v1.13.0: Screenshot display fixed — discovery from disk injected at regeneration time
- [x] 2026-03-03: Scoring reliability overhaul complete — token limits, criterion-aligned observation focus, scoring rubrics, and authoring guide updates (commit `85baa40`)
- [x] v1.12.0: GLM analyzer with OpenAI-compatible API support (glm_analyzer.py)
- [x] v1.12.0: Added openai>=1.0.0 dependency for alternative LLM providers
- [x] v1.11.0: Index direct links - cards link directly to reports (not type index)
- [x] v1.11.0: Fixed reanalyze_screenshots.py - all 16 competitors now included
- [x] v1.11.0: Moved competitor folders to proper basket-pages/ structure
- [x] v1.10.0: Rich progress bar + live countdown in analysis loops (main.py + reanalyze_screenshots.py)
- [x] v1.10.0: Improved error messages (truncation vs malformed JSON, no double-printing)
- [x] v1.10.0: Raised max_tokens — Pass 1: 8000, Pass 2: 16000
- [x] v1.10.0: Removed notable states bullet list and [DEBUG] image prints
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
# Interactive menu (fresh analysis / reanalyse / deploy)
./run.sh

# Silent modes (for automation / Telegram bot)
./run.sh --reanalyze output/audits/<folder>
./run.sh --reanalyze output/audits/<folder> --force
./run.sh --reanalyze output/audits/<folder> --force-observe --force
./run.sh --deploy

# Run tests
PYTHONPATH=. .venv/bin/pytest tests/

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
| `PROJECT_STATE.md` | **This file — LLM context entry point. Load first.** |
| `docs/ROADMAP.md` | Phases, goals, and current direction |
| `docs/COMMON_TASKS.md` | Command reference — the operational cheat sheet |
| `docs/ARCHITECTURE.md` | System design and pipeline |
| `docs/criteria-authoring-guide.md` | How to write criteria YAML files |
| `docs/ONBOARDING.md` | Setup from scratch (new developer) |
| `README.md` | Public-facing overview (GitHub) |
| `CHANGELOG.md` | Version history |
| `docs/deployment/` | Netlify deployment setup |
| `docs/research/` | Research papers (bot detection, VNC streaming) |
| `docs/plans/` | Detailed implementation plans |
| `docs/archive/` | Historical design docs |
