# Architecture & Extensibility Guide

This document describes the current (v1.6.x) architecture for the UX Maturity Analysis Agent.

## System Overview

```text
main.py (orchestrator)
├─ config_loader.py
│  └─ criteria_config/*.yaml
├─ screenshot_capture.py
│  └─ Playwright capture (desktop/mobile)
├─ claude_analyzer.py
│  ├─ Pass 1: observation from screenshots -> observation.json
│  └─ Pass 2: scoring from observation text -> analysis.json
└─ report generators
   ├─ report_generator.py (markdown + summary json)
   ├─ html_report_generator.py (interactive html)
   └─ audit_organizer.py (output layout + output/index.html)
```

## Pipeline Flow

### 1. Capture
- The orchestrator captures screenshots for each competitor (desktop + mobile viewport).
- Screenshots are stored under each competitor folder.

### 2. Two-Pass Analysis
- Pass 1 (observe):
  - `ClaudeUXAnalyzer._observe_screenshots(...)`
  - Produces structured visual evidence and `notable_states`
  - Saved as `observation.json`

- Pass 2 (score):
  - `ClaudeUXAnalyzer.analyze_screenshots(..., observation=...)`
  - Sends text-only content (observation + criteria)
  - Requires evidence citation per criterion
  - Saved as `analysis.json`

### 3. Reports
- Markdown comparison report
- Interactive HTML report
- Audit summary JSON
- Project-level index generated at `output/index.html`

## Configuration Model

Configuration is sourced from `criteria_config/*.yaml` (not from a monolithic runtime `config.yaml`).

Each analysis YAML typically includes:
- `name`
- `requires_interaction`, `interaction_prompt`, `interaction_timeout`
- `analysis_context`
- `viewports`
- `observation_focus` (pass 1 guidance)
- `criteria`

`config_loader.py` maps each file to an `AnalysisType` model.

## Output Layout

```text
output/
├─ index.html
└─ audits/
   └─ {YYYY-MM-DD}_{analysis_type}/
      ├─ _comparison_report.md
      ├─ {audit_folder}_report.html
      ├─ _audit_summary.json
      └─ {competitor}/
         ├─ screenshots/
         │  ├─ desktop.png
         │  └─ mobile.png
         ├─ observation.json
         └─ analysis.json
```

## Key Runtime Settings

- Model selection precedence:
  1. `--model`
  2. `CLAUDE_MODEL` (or `claude_model`) in `.env`
  3. hard fallback

- Rate-limit control:
  - Sequential analysis
  - `ANALYSIS_DELAY = 90` seconds between competitors

## Extending the System

### Add a New Page Type
1. Add `criteria_config/<new_type>.yaml`
2. Define `viewports`, `observation_focus`, and `criteria`
3. Run with `--analysis-type <new_type>`

No orchestrator code changes are required for standard criteria-only additions.

### Add/Adjust Reporting
- Markdown: `src/utils/report_generator.py`
- HTML: `src/utils/html_report_generator.py`
- Indexing and discovery: `src/utils/audit_organizer.py`

### Reanalysis Flow
- `scripts/reanalyze_screenshots.py`
- Supports:
  - `--force-observe` (rerun pass 1)
  - `--force` (rerun both passes)

## Design Notes

- Two-pass analysis exists to improve scoring consistency and create an auditable evidence trail.
- `notable_states` is treated as a first-class forcing function and surfaced in console + reports.
- Output is intentionally project-local so report artifacts remain discoverable and versionable.
