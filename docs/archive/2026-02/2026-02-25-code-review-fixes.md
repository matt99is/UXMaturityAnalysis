# Code Review Fixes Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix all issues identified in the two-pass pipeline code review: two critical bugs, two important issues, one refactor, and two minor test gaps.

**Architecture:** Surgical fixes across five files (`main.py`, `reanalyze_screenshots.py`, `claude_analyzer.py`, `html_report_generator.py`, `report_generator.py`, `audit_organizer.py`). No structural changes. Evidence tab deferred.

**Tech Stack:** Python 3.9+, pytest, pytest-asyncio, unittest.mock

---

### Task 1: Refactor — extract `_parse_json_response` helper

**Files:**
- Modify: `src/analyzers/claude_analyzer.py`
- Modify: `tests/test_claude_analyzer.py`

The same ~10-line JSON block-detection + parse pattern appears in both `_observe_screenshots` (lines 357-368) and `analyze_screenshots` (lines 520-529). Extract it into a private method.

**Step 1: Write failing tests for the new helper**

Add to `tests/test_claude_analyzer.py`:

```python
def test_parse_json_response_plain_json(analyzer: ClaudeUXAnalyzer) -> None:
    data = {"key": "value"}
    result = analyzer._parse_json_response(json.dumps(data))
    assert result == data


def test_parse_json_response_fenced_json_block(analyzer: ClaudeUXAnalyzer) -> None:
    data = {"key": "value"}
    response = f"```json\n{json.dumps(data)}\n```"
    result = analyzer._parse_json_response(response)
    assert result == data


def test_parse_json_response_generic_fence(analyzer: ClaudeUXAnalyzer) -> None:
    data = {"key": "value"}
    response = f"```\n{json.dumps(data)}\n```"
    result = analyzer._parse_json_response(response)
    assert result == data


def test_parse_json_response_raises_on_invalid(analyzer: ClaudeUXAnalyzer) -> None:
    with pytest.raises(json.JSONDecodeError):
        analyzer._parse_json_response("not json at all")
```

**Step 2: Run tests to verify they fail**

```bash
cd /home/matt99is/projects/UXMaturityAnalysis
pytest tests/test_claude_analyzer.py::test_parse_json_response_plain_json -v
```

Expected: `FAILED` — `AttributeError: 'ClaudeUXAnalyzer' object has no attribute '_parse_json_response'`

**Step 3: Add `_parse_json_response` method to `ClaudeUXAnalyzer`**

In `src/analyzers/claude_analyzer.py`, add this method after `_build_observation_prompt` (before `_observe_screenshots`, around line 306):

```python
def _parse_json_response(self, response_text: str) -> dict:
    """
    Extract and parse JSON from a Claude response.

    Handles plain JSON and markdown-fenced blocks (```json or ```).
    Raises json.JSONDecodeError if the extracted text is not valid JSON.
    """
    if "```json" in response_text:
        json_start = response_text.find("```json") + 7
        json_end = response_text.find("```", json_start)
        json_text = response_text[json_start:json_end].strip()
    elif "```" in response_text:
        json_start = response_text.find("```") + 3
        json_end = response_text.find("```", json_start)
        json_text = response_text[json_start:json_end].strip()
    else:
        json_text = response_text
    return json.loads(json_text)
```

**Step 4: Replace duplicate parsing in `_observe_screenshots`**

In `_observe_screenshots`, replace lines 357–368 (the block from `if "```json"` through `observation = json.loads(json_text)`) with:

```python
            observation = self._parse_json_response(response_text)
```

The `except json.JSONDecodeError` at line 374 already catches any parse failure — no change needed there.

**Step 5: Replace duplicate parsing in `analyze_screenshots`**

In `analyze_screenshots`, replace lines 520–529 (the block from `if "```json"` through `analysis_result = json.loads(json_text)`) with:

```python
            try:
                analysis_result = self._parse_json_response(response_text)
            except json.JSONDecodeError as json_error:
```

Note: the debug file save block (lines 536–547) follows the `except` — leave it in place, just remove the `json_text` local variable references since `_parse_json_response` no longer exposes it. Update the `except json.JSONDecodeError` handler below (around line 559) that references `json_text` in its error message — change to use `response_text` instead:

```python
        except json.JSONDecodeError as e:
            error_msg = f"Failed to parse Claude response as JSON: {e}"
            return {
                "success": False,
                "error": error_msg,
                "raw_response": response_text if 'response_text' in locals() else None
            }
```

**Step 6: Run all claude_analyzer tests**

```bash
pytest tests/test_claude_analyzer.py -v
```

Expected: ALL PASS

**Step 7: Commit**

```bash
git add src/analyzers/claude_analyzer.py tests/test_claude_analyzer.py
git commit -m "refactor: extract _parse_json_response helper to remove JSON parsing duplication"
```

---

### Task 2: Fix C1 — Remove redundant `analysis.json` write from `reanalyze_screenshots.py`

**Files:**
- Modify: `scripts/reanalyze_screenshots.py`

`analyze_competitor_from_screenshots` in `main.py` already saves `analysis.json` (correctly shaped, containing only `result_data`) before returning. `reanalyze_screenshots.py` then overwrites it with the full return dict (which adds `success`, `screenshot_paths`, `screenshot_metadata` — wrong shape). Delete the second save.

**Step 1: Delete the redundant save block**

In `scripts/reanalyze_screenshots.py`, delete lines 222–226:

```python
                # Save analysis to individual folder
                comp_root = audit_structure['competitors'][comp_data['site_name']]['root']
                analysis_path = comp_root / "analysis.json"
                with open(analysis_path, 'w') as f:
                    json.dump(analysis_result, f, indent=2)
```

After deletion, the `if analysis_result.get("success"):` block should contain only:

```python
            if analysis_result.get("success"):
                print(f"  [✓] Success!")
```

**Step 2: Run existing tests to confirm nothing broke**

```bash
pytest tests/ -v
```

Expected: ALL PASS

**Step 3: Commit**

```bash
git add scripts/reanalyze_screenshots.py
git commit -m "fix: remove redundant analysis.json write in reanalyze_screenshots (main.py already saves it)"
```

---

### Task 3: Fix I2 — Remove file deletion from `--force-observe`; fix misleading comment

**Files:**
- Modify: `scripts/reanalyze_screenshots.py`
- Modify: `main.py`
- Modify: `tests/test_audit_organizer.py` (or a new `tests/test_reanalyze_skip_logic.py`)

`--force-observe` currently deletes `observation.json` from disk (line 183) AND sets `_skip_observe=False`. The delete is redundant — `_skip_observe=False` already causes `main.py` to skip the `use_existing` branch. Remove the delete. The comment in `main.py` also incorrectly describes the semantics.

**Step 1: Write skip-logic tests**

Create `tests/test_reanalyze_skip_logic.py`:

```python
"""Tests for reanalyze_screenshots skip-logic state machine."""
import pytest
from pathlib import Path


def _compute_skip_observe(force_observe: bool, observation_exists: bool) -> bool:
    """Mirrors the _skip_observe logic in reanalyze_screenshots.py."""
    return (not force_observe) and observation_exists


@pytest.mark.parametrize("force_observe,obs_exists,expected_skip", [
    (False, False, False),   # Neither file: run pass 1
    (False, True,  True),    # Observation only: skip pass 1
    (True,  False, False),   # --force-observe, no file: run pass 1
    (True,  True,  False),   # --force-observe, file exists: still run pass 1
])
def test_skip_observe_logic(force_observe, obs_exists, expected_skip):
    assert _compute_skip_observe(force_observe, obs_exists) == expected_skip


def test_force_observe_does_not_delete_observation_file(tmp_path: Path):
    """When --force-observe is set, the observation file must NOT be deleted."""
    obs_file = tmp_path / "observation.json"
    obs_file.write_text('{"notable_states": []}', encoding="utf-8")

    force_observe = True
    observation_exists = obs_file.exists()
    skip_observe = (not force_observe) and observation_exists

    # The flag is False — pass 1 will re-run — but the file must still be on disk
    assert skip_observe is False
    assert obs_file.exists(), "observation.json must not be deleted; flag controls pass 1, not file presence"
```

**Step 2: Run to verify tests pass** (these test the desired behaviour, which we'll ensure survives the fix)

```bash
pytest tests/test_reanalyze_skip_logic.py -v
```

Expected: ALL PASS (the logic function matches desired behaviour)

**Step 3: Remove the `unlink()` call from `reanalyze_screenshots.py`**

In `scripts/reanalyze_screenshots.py`, delete lines 182–184:

```python
            elif force_observe and observation_path.exists():
                observation_path.unlink()
                print(f"  [→] {comp_data['site_name']}: Removed existing observation (--force-observe)")
```

Replace with a print that clarifies intent without deleting:

```python
            elif force_observe and observation_path.exists():
                print(f"  [→] {comp_data['site_name']}: Will re-observe (--force-observe)")
```

**Step 4: Fix the misleading comment in `main.py`**

In `main.py`, replace lines 404–406:

```python
            # _skip_observe=True means reuse existing observation.json (set by reanalyze --force-observe=False)
            # _skip_observe=False means re-run pass 1 even if observation.json exists (--force-observe)
            # Default (not set): reuse if observation.json exists
```

With:

```python
            # _skip_observe=True  → reuse observation.json if it exists (default for normal runs and
            #                        reanalyze without --force-observe)
            # _skip_observe=False → always run pass 1 (set by reanalyze --force-observe)
            # Not set (main.py run): default True, so existing observation.json is reused
```

**Step 5: Run all tests**

```bash
pytest tests/ -v
```

Expected: ALL PASS

**Step 6: Commit**

```bash
git add scripts/reanalyze_screenshots.py main.py tests/test_reanalyze_skip_logic.py
git commit -m "fix: remove fragile observation.json deletion from --force-observe; rely on _skip_observe flag alone"
```

---

### Task 4: Fix I3 — Rename `get_output_base_dir` → `get_audits_dir`

**Files:**
- Modify: `src/utils/audit_organizer.py`
- Modify: `main.py`

The function returns `output/audits/` but is named `get_output_base_dir`. Rename for accuracy.

**Step 1: Write a test that imports the new name**

Add to `tests/test_audit_organizer.py`:

```python
def test_get_audits_dir_returns_audits_subdir():
    from src.utils.audit_organizer import get_audits_dir
    result = get_audits_dir("output")
    assert result.name == "audits"
    assert result.parent.name == "output"
```

**Step 2: Run to verify it fails**

```bash
pytest tests/test_audit_organizer.py::test_get_audits_dir_returns_audits_subdir -v
```

Expected: `FAILED` — `ImportError: cannot import name 'get_audits_dir'`

**Step 3: Rename the function in `audit_organizer.py`**

In `src/utils/audit_organizer.py`:

- Line 42: change `def get_output_base_dir(` → `def get_audits_dir(`
- Line 372 (inside `create_audit_directory_structure`): change `get_output_base_dir(base_dir)` → `get_audits_dir(base_dir)`

**Step 4: Update `main.py` import and call sites**

In `main.py` line 45, change:

```python
    get_output_base_dir,
```

to:

```python
    get_audits_dir,
```

In `main.py` line 85, change:

```python
        project_output_dir = get_output_base_dir("output").parent
```

to:

```python
        project_output_dir = get_audits_dir("output").parent
```

In `main.py` lines 740 and 769, change both occurrences of:

```python
generate_reports_index(get_output_base_dir("output").parent)
```

to:

```python
generate_reports_index(get_audits_dir("output").parent)
```

**Step 5: Run tests**

```bash
pytest tests/ -v
```

Expected: ALL PASS

**Step 6: Commit**

```bash
git add src/utils/audit_organizer.py main.py tests/test_audit_organizer.py
git commit -m "fix: rename get_output_base_dir to get_audits_dir to match what it actually returns"
```

---

### Task 5: Fix C2 — Store `observation_file` as relative filename; thread `competitor_root`

**Files:**
- Modify: `main.py`
- Modify: `scripts/reanalyze_screenshots.py`
- Modify: `src/utils/html_report_generator.py`
- Modify: `src/utils/report_generator.py`
- Modify: `tests/test_claude_analyzer.py` (or new test file)

`analysis.json` currently stores the absolute filesystem path in `observation_file`. The design specifies `"observation.json"` (filename only). Report generators need to know the competitor directory to resolve it, so thread `competitor_root` through the result dict.

**Step 1: Write failing test for relative path storage**

Add to `tests/test_claude_analyzer.py`:

```python
@pytest.mark.asyncio
async def test_analyze_competitor_stores_relative_observation_file(tmp_path: Path) -> None:
    """observation_file in result must be a plain filename, not an absolute path."""
    from main import UXAnalysisOrchestrator
    from unittest.mock import AsyncMock, MagicMock, patch
    from PIL import Image

    # Create fake screenshots
    screenshots_dir = tmp_path / "amazon" / "screenshots"
    screenshots_dir.mkdir(parents=True)
    img = Image.new("RGB", (10, 10))
    desktop = screenshots_dir / "desktop.png"
    mobile = screenshots_dir / "mobile.png"
    img.save(desktop)
    img.save(mobile)

    # Fake observation
    mock_obs = {
        "site_name": "amazon", "url": "https://amazon.com",
        "analysis_name": "Basket Page", "desktop": {}, "mobile": {},
        "notable_states": []
    }
    # Fake analysis result
    mock_analysis = {
        "site_name": "amazon", "url": "https://amazon.com",
        "analysis_type": "Basket Page", "overall_score": 7,
        "competitive_position": {"tier": "strong_contender", "positioning": "ok", "key_differentiator": "ok"},
        "criteria_scores": [], "strengths": [], "competitive_advantages": [],
        "weaknesses": [], "exploitable_vulnerabilities": [], "unmet_user_needs": [], "key_findings": []
    }

    mock_resp_obs = MagicMock()
    mock_resp_obs.content = [MagicMock(text=json.dumps(mock_obs))]
    mock_resp_analysis = MagicMock()
    mock_resp_analysis.content = [MagicMock(text=json.dumps(mock_analysis))]

    call_count = 0
    async def mock_create(**kwargs):
        nonlocal call_count
        call_count += 1
        return mock_resp_obs if call_count == 1 else mock_resp_analysis

    orchestrator = UXAnalysisOrchestrator(api_key="test", analysis_type="basket_pages")
    competitor_paths = {
        'root': tmp_path / "amazon",
        'screenshots': screenshots_dir,
    }
    capture_data = {
        "site_name": "amazon", "url": "https://amazon.com",
        "screenshot_paths": [str(desktop), str(mobile)],
        "competitor_paths": competitor_paths,
    }

    with patch.object(orchestrator.claude_analyzer.client.messages, "create", new=mock_create):
        result = await orchestrator.analyze_competitor_from_screenshots(capture_data)

    assert result["success"] is True
    assert result["observation_file"] == "observation.json", (
        f"Expected 'observation.json', got {result['observation_file']!r}"
    )
    assert "competitor_root" in result
    assert Path(result["competitor_root"]) == tmp_path / "amazon"
```

**Step 2: Run to verify it fails**

```bash
pytest tests/test_claude_analyzer.py::test_analyze_competitor_stores_relative_observation_file -v
```

Expected: `FAILED` — `AssertionError: Expected 'observation.json', got '/home/...observation.json'`

**Step 3: Fix `main.py` — store relative filename and add `competitor_root` to return**

In `main.py`, change line 501:

```python
        result_data["observation_file"] = str(observation_path) if observation_path else None
```

to:

```python
        result_data["observation_file"] = "observation.json" if observation_path else None
```

In `main.py`, change the return statement (around line 513) to add `competitor_root`:

```python
        return {
            "success": True,
            "site_name": site_name,
            "url": url,
            "screenshot_paths": screenshot_paths,
            "screenshot_metadata": capture_data.get("screenshot_metadata", []),
            "competitor_root": str(Path(competitor_paths['root'])) if competitor_paths else None,
            **result_data
        }
```

**Step 4: Fix `reanalyze_screenshots.py` — inject `competitor_root` when loading existing analysis**

In `scripts/reanalyze_screenshots.py`, after loading an existing analysis from disk (around line 160), inject `competitor_root`:

```python
            with open(analysis_path, 'r') as f:
                existing_analysis = json.load(f)

            # Inject competitor_root so report generators can resolve relative observation_file
            existing_analysis["competitor_root"] = str(comp_dir)
```

This ensures existing analyses (loaded from disk, which lack `competitor_root`) can still resolve `observation.json`.

**Step 5: Fix `html_report_generator.py` — resolve `observation_file` relative to `competitor_root`**

In `src/utils/html_report_generator.py`, replace the `_attach_notable_states` method body (lines 455–478) with:

```python
    def _attach_notable_states(
        self,
        competitor_results: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Load notable_states from observation files into competitor payloads."""
        for result in competitor_results:
            result["notable_states"] = []
            observation_file = result.get("observation_file")
            if not observation_file:
                continue

            # Resolve relative filename against competitor_root if available,
            # otherwise fall back to treating it as an absolute path (legacy).
            competitor_root = result.get("competitor_root")
            if competitor_root:
                obs_path = Path(competitor_root) / observation_file
            else:
                obs_path = Path(observation_file)

            if not obs_path.exists():
                continue

            try:
                with open(obs_path, "r", encoding="utf-8") as f:
                    observation = json.load(f)

                notable_states = observation.get("notable_states", [])
                if isinstance(notable_states, list):
                    result["notable_states"] = [
                        str(state).strip()
                        for state in notable_states
                        if str(state).strip()
                    ]
            except (OSError, json.JSONDecodeError):
                continue

        return competitor_results
```

**Step 6: Fix `report_generator.py` — same resolution logic**

In `src/utils/report_generator.py`, replace lines 547–556 (the observation file loading block):

```python
        observation_file = analysis.get("observation_file")
        if observation_file:
            obs_path = Path(observation_file)
            if obs_path.exists():
                try:
                    with open(obs_path, "r", encoding="utf-8") as f:
                        observation = json.load(f)
                    notable = observation.get("notable_states", [])
                except (OSError, json.JSONDecodeError):
                    notable = []
```

with:

```python
        observation_file = analysis.get("observation_file")
        if observation_file:
            competitor_root = analysis.get("competitor_root")
            if competitor_root:
                obs_path = Path(competitor_root) / observation_file
            else:
                obs_path = Path(observation_file)  # legacy absolute path fallback
            if obs_path.exists():
                try:
                    with open(obs_path, "r", encoding="utf-8") as f:
                        observation = json.load(f)
                    notable = observation.get("notable_states", [])
                except (OSError, json.JSONDecodeError):
                    notable = []
```

**Step 7: Run all tests**

```bash
pytest tests/ -v
```

Expected: ALL PASS

**Step 8: Commit**

```bash
git add main.py scripts/reanalyze_screenshots.py src/utils/html_report_generator.py src/utils/report_generator.py tests/test_claude_analyzer.py
git commit -m "fix: store observation_file as relative filename and resolve via competitor_root"
```

---

### Task 6: Fix M1 — em dash in test fixture

**Files:**
- Modify: `tests/test_claude_analyzer.py`

The test fixture at line 31 uses a hyphen-minus (`-`) where the YAML uses an em dash (`—`). The test still passes because it only checks for a substring, but the fixture string doesn't match any real YAML value, which is misleading.

**Step 1: Update the fixture string**

In `tests/test_claude_analyzer.py` line 31, change:

```python
    focus = ["Subscription vs one-time purchase toggle - which is pre-selected"]
```

to match the actual YAML `observation_focus` string from `criteria_config/product_pages.yaml`:

```python
    focus = ["Subscription vs one-time purchase toggle — state explicitly which option is pre-selected (look for filled radio buttons, highlighted cards, checked checkboxes)"]
```

Also update the assertion at line 38 to check for the presence of the em dash, making the test more meaningful:

```python
    assert "Subscription vs one-time purchase toggle" in prompt
    assert "—" in prompt  # em dash from YAML must appear verbatim
```

**Step 2: Run the test**

```bash
pytest tests/test_claude_analyzer.py::test_build_observation_prompt_includes_page_specific_focus -v
```

Expected: PASS

**Step 3: Commit**

```bash
git add tests/test_claude_analyzer.py
git commit -m "test: update observation_focus fixture to match YAML em dash verbatim"
```

---

### Final verification

**Step 1: Run the full test suite**

```bash
cd /home/matt99is/projects/UXMaturityAnalysis
pytest tests/ -v
```

Expected: ALL PASS, no warnings about unknown fixtures or imports.

**Step 2: Quick smoke-check — verify analysis.json shape**

If you have an existing audit folder, run:

```bash
python3 scripts/reanalyze_screenshots.py <any_audit_folder> --force
```

Open the resulting `analysis.json` for one competitor. Verify:
- `observation_file` value is `"observation.json"` (not an absolute path)
- No top-level `success`, `screenshot_paths`, or `screenshot_metadata` keys (those belong in the result dict only, not the saved file)

**Step 3: Verify `--force-observe` no longer deletes files**

```bash
ls <audit_folder>/<competitor>/    # note observation.json is there
python3 scripts/reanalyze_screenshots.py <audit_folder> --force-observe
ls <audit_folder>/<competitor>/    # observation.json still exists (re-run writes new content)
```
