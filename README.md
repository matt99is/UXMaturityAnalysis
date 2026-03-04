# UX Maturity Analysis

**Version:** 1.13.0
**Status:** Production ready (Phase 1 scoring reliability complete)
**Last verified:** 2026-03-04

UX Maturity Analysis is a Python tool that captures competitor e-commerce pages, runs a two-pass AI analysis (observe -> score), and publishes interactive HTML reports to Netlify.

## What It Does

1. Captures desktop + mobile screenshots per competitor URL.
2. Runs Pass 1 observation to create `observation.json`.
3. Runs Pass 2 scoring against criteria to create `analysis.json`.
4. Generates markdown + interactive HTML reports and index pages.

## Current State (Important)

- Unified entrypoint is `./run.sh` (tmux wrapper) -> `cli.py`.
- Scoring reliability overhaul is complete on `main` (commit `85baa40`, 2026-03-03).
- Browser-capture infrastructure (Patchright/Xvfb/noVNC) is still planned, not fully implemented.
- `Supervised` mode is now wired to interactive capture (`main.py --interactive`) and can show noVNC URL guidance.
- `Supervised` mode now runs fail-fast noVNC preflight and uses timeout/heartbeat while waiting for operator readiness.
- `Automated` remains unavailable in the unified CLI until Patchright/Xvfb flow is implemented.

## Quick Start

### Prerequisites

- Python 3.12+ recommended
- `tmux` installed
- Anthropic API key

### Install

```bash
git clone <repository-url>
cd UXMaturityAnalysis

# Preferred (creates/updates .venv)
uv sync

# Fallback
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m playwright install chromium
```

### Configure Environment

```bash
cp .env.example .env
# set ANTHROPIC_API_KEY=...
```

## Run Commands

Always use `./run.sh` for normal operation.

```bash
# Guided menu
./run.sh

# Reanalyse existing audit
./run.sh --reanalyze output/audits/<folder>
./run.sh --reanalyze output/audits/<folder> --force
./run.sh --reanalyze output/audits/<folder> --force-observe --force

# Deploy reports
./run.sh --deploy
./run.sh --deploy --verbose  # full Netlify CLI logs
```

`run.sh` tmux quality-of-life defaults:
- Enables tmux mouse scrolling for the `analysis` session.
- Raises scrollback history limit for easier review.
- Captures run output to `output/logs/analysis_YYYYMMDD_HHMMSS.log`.

## Fresh Analysis Flow

`./run.sh` -> `Fresh analysis` -> select page type -> select competitor set.

Competitor sets come from `competitors/*.yaml` (for example `competitors/petfood.yaml`) and are URL-validated in the CLI.
If a URL fails validation during interactive runs, the corrected URL is written back to that YAML file for future runs.

For capture rollout, use a 2-stage gate:
- `petfood-smoke` (1 competitor) for fast smoke checks.
- `petfood-test` (3 competitors) as canary before the full 16-site `petfood` set.

## Advanced / Direct Entry (Debug Only)

`main.py` is still callable directly for low-level debugging.

```bash
.venv/bin/python3 main.py --analysis-type basket_pages --config competitors.example.json
.venv/bin/python3 main.py --manual-mode --screenshots-dir ./screenshots --config competitors.example.json
```

## Two-Pass Pipeline

- Pass 1 (`_observe_screenshots`) writes `observation.json`.
- Pass 2 (`analyze_screenshots`) scores from observation text and writes `analysis.json`.
- Evidence is criterion-level and explicit in output.

## Output Structure

```text
output/
├── index.html
├── css/main.css
├── basket-pages/
│   ├── index.html
│   ├── YYYY-MM-DD.html
│   ├── YYYY-MM-DD.json
│   └── screenshots/YYYY-MM-DD/{competitor}/
│       ├── desktop.png
│       ├── mobile.png
│       ├── observation.json
│       └── analysis.json
└── audits/  # legacy layout still supported
```

## Development Commands

```bash
# Tests (PYTHONPATH=. is required)
PYTHONPATH=. .venv/bin/pytest tests/

# Lint
pre-commit run --all-files
```

## Key Project Files

- `AGENTS.md` - mandatory startup/load order for agents
- `PROJECT_STATE.md` - active state and implementation priorities
- `docs/ROADMAP.md` - phased roadmap
- `cli.py` - unified CLI
- `main.py` - orchestration and analysis flow
- `src/analyzers/screenshot_capture.py` - screenshot capture
- `src/utils/html_report_generator.py` - HTML reports

## Documentation

- [Developer Onboarding](docs/ONBOARDING.md)
- [Common Tasks](docs/COMMON_TASKS.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Roadmap](docs/ROADMAP.md)
- [Criteria Authoring Guide](docs/criteria-authoring-guide.md)

## License

MIT
