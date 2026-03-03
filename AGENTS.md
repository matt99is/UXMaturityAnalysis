# AGENTS.md

This is the entry point for any AI agent working on this project. Read this file first, then follow the load order below before touching any code.

---

## What this project is

UX Maturity Analysis — a Python tool that captures screenshots of competitor e-commerce pages, runs a two-pass Claude AI analysis (observe → score), and publishes interactive HTML reports to Netlify.

**Live site:** https://analysis.mattlelonek.co.uk
**Stack:** Python 3.12, Playwright/Patchright, Anthropic API (claude-sonnet-4-6), Rich, Jinja2, SCSS, Plotly, Netlify

---

## Load order

Read these files before starting any task:

| Priority | File | Why |
|---|---|---|
| 1 — always | `PROJECT_STATE.md` | Active work, architecture decisions, gotchas, quick reference |
| 2 — always | `docs/ROADMAP.md` | Where the project is going — understand the direction before changing anything |
| 3 — for commands | `docs/COMMON_TASKS.md` | Operational cheat sheet |
| 4 — for architecture | `docs/ARCHITECTURE.md` | System design and pipeline flow |
| 4 — for criteria work | `docs/criteria-authoring-guide.md` | How to write `criteria_config/*.yaml` files |
| 4 — for a specific task | `docs/plans/<plan-file>.md` | Detailed implementation plan for that task |

---

## Key commands

```bash
# Run (always use ./run.sh — it wraps in tmux so runs survive disconnects)
./run.sh                                               # interactive menu
./run.sh --reanalyze output/audits/<folder>            # silent reanalyse
./run.sh --reanalyze output/audits/<folder> --force    # re-run scoring
./run.sh --reanalyze output/audits/<folder> --force-observe --force  # redo everything
./run.sh --deploy                                      # deploy to Netlify

# Tests (PYTHONPATH=. is required — pytest can't find src/ without it)
PYTHONPATH=. .venv/bin/pytest tests/
PYTHONPATH=. .venv/bin/pytest tests/test_foo.py -v     # single file

# Linting
pre-commit run --all-files
```

---

## Critical gotchas

- **Always use `PYTHONPATH=.` with pytest.** The test suite imports from `src/`; without it you get `ModuleNotFoundError: No module named 'src'`.
- **The `.venv` is at the project root.** Use `.venv/bin/python3` and `.venv/bin/pytest` — not system Python.
- **`run.sh` uses tmux.** If you're already inside a tmux session it runs directly. Don't call `main.py` or scripts directly — use `./run.sh` or `cli.py`.
- **Uncommitted changes on `main` are intentional.** The scoring reliability overhaul is in progress. Read `PROJECT_STATE.md` → Active Work before assuming the working tree is clean.
- **`competitors/petfood.yaml` basket URLs are best-guesses.** They are validated and corrected at first run via the inline correction flow in `cli.py`.
- **`output/` contains generated reports.** The Netlify site ID lives at `output/.netlify/state.json`. If missing: `echo '{"siteId":"4cbfbfea-046c-40aa-9b5c-c40ccd59c95d"}' > output/.netlify/state.json`.
- **Two-pass pipeline.** Pass 1 (`_observe_screenshots`) produces `observation.json`. Pass 2 (`analyze_screenshots`) scores against it — text only, no images. Evidence must be cited. See `docs/ARCHITECTURE.md`.

---

## Repo structure

```
AGENTS.md               # this file — LLM entry point
PROJECT_STATE.md        # active work + architecture decisions (load second)
cli.py                  # unified entry point (interactive menus + silent flags)
run.sh                  # tmux launcher — forwards all args to cli.py
main.py                 # analysis orchestrator (UXAnalysisOrchestrator)
requirements.txt        # Python dependencies
competitors/            # competitor sets (YAML)
│   └── petfood.yaml    # 16 UK pet food retailers with basket URLs
criteria_config/        # page-type analysis criteria (YAML)
│   └── basket_pages.yaml
src/
│   ├── competitor_config.py    # load competitors/*.yaml
│   ├── config_loader.py        # load criteria_config/*.yaml
│   ├── analyzers/              # Claude + GLM analysis logic
│   └── utils/                  # report generation, HTML, audit organizer
templates/              # Jinja2 HTML report templates
css/                    # SCSS stylesheets (8 partials — entry: main.scss)
scripts/                # utility scripts (deploy_netlify.py, reanalyze_screenshots.py, build_css.py)
tests/                  # pytest test suite
output/                 # generated reports (not committed)
docs/
│   ├── ROADMAP.md              # 5-phase product direction
│   ├── COMMON_TASKS.md         # command reference
│   ├── ARCHITECTURE.md         # system design
│   ├── criteria-authoring-guide.md
│   ├── ONBOARDING.md           # setup from scratch
│   ├── research/               # research papers (bot detection, VNC streaming)
│   ├── plans/                  # detailed implementation plans
│   └── deployment/             # Netlify setup guides
```

---

## Current focus

See `PROJECT_STATE.md` → Active Work.

As of 2026-03-03: **Scoring reliability overhaul** (Phase 1 of roadmap) is in progress. Uncommitted changes exist across `main.py`, `src/analyzers/claude_analyzer.py`, `src/analyzers/glm_analyzer.py`, `src/config_loader.py`, `criteria_config/basket_pages.yaml`, and tests. Read the plan at `docs/plans/2026-03-02-scoring-reliability-overhaul.md` and diff the uncommitted changes to understand what's already done before writing new code.
