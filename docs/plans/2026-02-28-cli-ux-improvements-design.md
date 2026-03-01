# CLI UX Improvements — Design

**Date:** 2026-02-28
**Status:** Approved

## Problem

The current CLI output is noisy and gives poor feedback during long runs:
- No overall progress indication
- No spinners during API calls (passes 1 and 2 feel like dead time)
- The 90s wait between competitors outputs a single line then goes silent
- Notable states are printed in full, adding significant noise
- Debug messages (`[DEBUG] Image dimensions OK`) leak into output
- Error messages are raw Python exceptions — unhelpful and printed twice

## Design

### Approach: Rich Progress + Status (Approach A)

Use Rich's `Progress` as a persistent bar at the bottom of the terminal throughout the analysis loop. All existing log output continues scrolling above it. No structural overhaul — targeted changes only.

### Progress bar layout

```
⠋ Analyzing competitors  ━━━━━━━━━━  3/16  Pass 1: Observing viovet...  0:04:32
```

During wait periods:
```
⠋ Analyzing competitors  ━━━━━━━━━━  3/16  Next: animed in 87s  •  Ctrl+C to quit  0:04:32
```

Columns (left to right): spinner, label, bar, `X/Y`, status description, elapsed time.

### Changes to `main.py`

**`analyze_competitor_from_screenshots`**
- Add optional `progress` and `task_id` parameters
- When provided, update `task.description` at each stage:
  - `Pass 1: Observing {name}...`
  - `Pass 2: Scoring {name}...`
- Remove the full notable states bullet list (keep the count line: `✓ Observation saved (N notable states)`)
- Remove `[DEBUG] Image dimensions OK` prints

**`_wait_with_countdown(delay, next_name, progress, task_id)`** — new helper
- Replaces `asyncio.sleep(ANALYSIS_DELAY)` in analysis loops
- Ticks 1s at a time, updates progress description each tick:
  `Next: {next_name} in {remaining}s  •  Ctrl+C to quit`

**Analysis loops (orchestrator `run()` and `reanalyze_screenshots.py`)**
- Wrap the competitor loop in a `Progress` context
- Create one task: `progress.add_task('', total=len(competitors))`
- Pass `progress` and `task_id` into each `analyze_competitor_from_screenshots` call
- Replace `asyncio.sleep(ANALYSIS_DELAY)` with `_wait_with_countdown(...)`
- Use `progress.console.print()` for all output within the loop

### Improved error messaging

JSON parse failures in `_observe_screenshots` and `analyze_screenshots` currently surface the raw `json.JSONDecodeError` text and print it twice (once inside the method, once by the caller).

**Root cause detection** — check `response.stop_reason` before attempting to parse:
- `stop_reason == "max_tokens"` → truncation error
- anything else + `JSONDecodeError` → malformed JSON from model

**New error messages:**
```
✗ Pass 1 failed — response truncated (hit 4000 token limit). Debug file saved.
✗ Pass 1 failed — model returned malformed JSON (char 13547). Debug file saved.
✗ Pass 2 failed — response truncated (hit 8000 token limit). Debug file saved.
```

**Fix double-printing** — methods return the error string; the caller prints it once. Remove the internal `console.print` for errors from `_observe_screenshots` and `analyze_screenshots`.

### What does not change

- All existing success/fail/warning output lines
- The `✓ Observation saved (N notable states)` line
- Competitor score output
- Error handling and retry logic

## Files affected


- `main.py` — orchestrator loop + `analyze_competitor_from_screenshots` + new helper
- `scripts/reanalyze_screenshots.py` — analysis loop wrapped in Progress context
