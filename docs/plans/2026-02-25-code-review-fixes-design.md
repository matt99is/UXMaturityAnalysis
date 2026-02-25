# Code Review Fixes Design

**Date:** 2026-02-25
**Status:** Approved
**Scope:** Fix all issues identified in two-pass pipeline code review (ChatGPT implementation). Evidence tab deferred to report visuals revisit.

---

## Issues Being Fixed

### Critical

**C1 — Redundant `analysis.json` write in `reanalyze_screenshots.py`**
`main.py` already saves `analysis.json` (correctly shaped) inside `analyze_competitor_from_screenshots`. `reanalyze_screenshots.py` then saves it again with a different shape (full result wrapper including `success`, `screenshot_paths`, `screenshot_metadata`). Delete the redundant save.

**C2 — `observation_file` stored as absolute path**
`main.py` writes the absolute filesystem path into `analysis.json["observation_file"]`. The plan specifies a relative filename only. Report generators that read this field break if the project is moved or shared. Fix: store `"observation.json"` (filename only) and thread `competitor_root` through the result dict so readers can resolve it at load time.

### Important

**I2 — `--force-observe` deletes file instead of using flag**
`reanalyze_screenshots.py` calls `observation_path.unlink()` when `--force-observe` is set. The `_skip_observe=False` flag already achieves the same effect — `main.py`'s `use_existing` check evaluates to `False` either way. The delete is redundant and fragile (silent failure if permissions error). Remove the unlink; rely on the flag alone. Update the misleading comment in `main.py`.

**I3 — `get_output_base_dir` returns `output/audits/`, not `output/`**
The function name implies it returns the base output directory but actually returns the audits subdirectory. Rename to `get_audits_dir`. Update all call sites. The one caller that needed `output/` via `.parent` continues to use `.parent` on the renamed function.

### Refactor

**JSON parsing duplication in `claude_analyzer.py`**
The `"```json"` block detection + `json.loads` pattern appears identically in both `_observe_screenshots` and `analyze_screenshots`. Extract into `_parse_json_response(response_text: str) -> dict` private method that raises `json.JSONDecodeError` on failure. Callers already catch it.

### Minor

**M1 — Test fixture uses hyphen where YAML uses em dash**
Update fixture string in `test_claude_analyzer.py` to match YAML `observation_focus` exactly.

**M3 — No tests for skip-logic state machine**
Add 4 tests covering the four states: neither file exists, observation only, both files, `--force`/`--force-observe`.

---

## What Is NOT Changing

- Evidence tab — deferred to report visuals revisit
- HTML template structure beyond the `_attach_notable_states` method signature
- `analysis.json` schema beyond `observation_file` value type (absolute → relative filename)
- Screenshot capture pipeline
- Report generator output format
