# Unified CLI Design

**Date:** 2026-03-03
**Status:** Approved

---

## Problem

The tool has multiple entry points (`main.py`, `scripts/reanalyze_screenshots.py`, `scripts/deploy_netlify.py`) with overlapping and poorly documented arguments. As a layman operating the tool remotely, the user has to ask what command to run every time. The config structure doesn't reflect the reality that competitor identities are stable but page-type URLs drift.

---

## Solution

A single entry point `./run.sh` that, with no arguments, guides the user through an interactive menu (via `questionary`). Silent flags pass through for automation and Telegram bot use. The competitor config is refactored to separate the stable competitor list from the more volatile per-page-type URLs, with inline correction of stale URLs during capture runs.

---

## Interactive Flow

### Main menu

```
What do you want to do?
  ❯ Fresh analysis   (capture screenshots → analyse → report)
    Reanalyse        (work with existing screenshots)
    Deploy
```

### Fresh analysis branch

```
Which page type?
  ❯ Basket pages
    Product pages (PDP)
    Homepage
    Checkout pages
    Product listings (PLP/SRP)

Which competitor set?
  ❯ UK Pet Food Retail  (petfood)
    [others discovered from competitors/*.yaml]

Capture mode?
  ❯ Supervised   (watch browser via noVNC URL — for basket setup, CAPTCHAs, logins)
    Automated    (fully unattended — Playwright + bot evasion, no intervention)
```

**Supervised mode** — per-competitor flow:
```
[1/16] zooplus — open this URL to watch the browser:
       http://100.105.217.56:6080/vnc.html

       Add items to basket, dismiss any popups, then...
       [Press Enter when ready to capture]

       ✓ desktop.png captured
       ✓ mobile.png captured
```

**Automated mode** — proceeds without user input, logs any bot-detection blocks.

### Reanalyse branch

```
Which audit?
  ❯ 2026-03-02 basket_pages  (Mar 2 — 16 competitors, rubric scoring)
    2026-02-24 basket_pages  (Feb 24 — 14 competitors)
    [discovered from output/audits/]

What to re-run?
  ❯ Report only   (no AI — regenerate HTML from existing scores)
    Re-score      (keep observations, rerun scoring pass only)
    Full          (redo everything — observations + scoring)
```

### Deploy behaviour

- **Clean run** (all competitors succeeded) → deploys automatically, no prompt
- **Partial run** (any competitors skipped or failed) → asks first:

```
⚠ 2 competitors were skipped (bot detection)
  Deploy partial report anyway?
  ❯ Yes    No
```

---

## Config Refactor

### New structure

```
competitors/
  petfood.yaml     # one file per competitor set
```

```yaml
# competitors/petfood.yaml
name: "UK Pet Food Retail"
competitors:
  - name: zooplus
    pages:
      basket: https://www.zooplus.co.uk/shop/cart
      product: https://www.zooplus.co.uk/shop/dogs/dog_food/royal-canin/
  - name: jollyes
    pages:
      basket: https://www.jollyes.co.uk/basket
      product: https://www.jollyes.co.uk/dogs/dog-food/
  - name: tesco
    pages:
      basket: https://www.tesco.com/groceries/en-GB/trolley
      # product: not tracked — omit to skip for that page type
```

**Rules:**
- Competitors with no entry for the selected page type are skipped with a logged note
- `criteria_config/*.yaml` files (analysis criteria, observation focus, scoring rubrics) are unchanged — they define how to analyse, not which competitors to run
- Existing `competitors.petfood.json` is migrated into this format

### URL drift detection

Before capture starts, the CLI HEAD-checks all URLs for the selected page type. Any returning 404 or redirecting to a homepage prompt inline:

```
⚠ jollyes basket URL returned 404
  Current: https://www.jollyes.co.uk/basket
  New URL (or Enter to skip this competitor): _
```

Corrections are saved back to `competitors/petfood.yaml` immediately, fixing all future runs.

---

## Architecture

```
run.sh  →  tmux wrapping  →  cli.py
                               │
                    ┌──────────┴──────────┐
                    │   Interactive menu  │
                    │   (questionary)     │
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
         main.py         reanalyze_       deploy_
         (capture        screenshots      netlify.py
         + analyse)      .py
```

### New files

| File | Purpose |
|------|---------|
| `cli.py` | Entry point — interactive menu, routes to existing scripts |
| `src/competitor_config.py` | Loads `competitors/*.yaml`, validates URLs, handles inline correction |
| `competitors/petfood.yaml` | Migrated from `competitors.petfood.json` |

### Modified files

| File | Change |
|------|--------|
| `run.sh` | Simplified — tmux layer only, forwards all args to `cli.py` |

### Unchanged files

| File | Reason |
|------|--------|
| `main.py` | Called by `cli.py` with constructed args |
| `scripts/reanalyze_screenshots.py` | Called by `cli.py` with constructed args |
| `scripts/deploy_netlify.py` | Called by `cli.py` |
| `criteria_config/*.yaml` | Analysis criteria — unaffected |

### Silent flags (automation / Telegram bot)

`cli.py` detects flags and bypasses menus entirely:

```bash
./run.sh --reanalyze output/audits/2026-03-02_basket_pages   # skips menus
./run.sh --reanalyze output/audits/2026-03-02_basket_pages --force
./run.sh --reanalyze output/audits/2026-03-02_basket_pages --force-observe
./run.sh --deploy
```

---

## Dependencies

- `questionary` — arrow-key selection menus (new, small)
- Everything else already in use

---

## Out of scope

- The VNC/noVNC infrastructure itself (covered in `2026-03-02-browser-capture-infrastructure-design.md`) — `cli.py` assumes that infrastructure exists when supervised mode is selected
- Web GUI
- Multi-user / SaaS concerns
