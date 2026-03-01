# CLI UX Improvements Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a persistent Rich progress bar, live countdown between analyses, suppressed noise, and clear error messages to the CLI.

**Architecture:** All display changes go through `UXAnalysisOrchestrator` in `main.py`. A `Progress` context wraps the analysis loop in both `main.py` and `reanalyze_screenshots.py`. `analyze_competitor_from_screenshots` accepts optional `progress`/`task_id` params to update descriptions. Error messaging improvements go in `claude_analyzer.py`.

**Tech Stack:** Python, Rich 13.9.2 (`rich.progress`, `rich.console`)

---

### Task 1: Improve error messaging in `claude_analyzer.py`

**Files:**
- Modify: `src/analyzers/claude_analyzer.py:373-395` (`_observe_screenshots`)
- Modify: `src/analyzers/claude_analyzer.py:520-570` (`analyze_screenshots`)

**Context:** Both methods currently catch `json.JSONDecodeError` and return a raw Python exception string. They don't distinguish between truncation (`stop_reason == "max_tokens"`) and genuinely malformed JSON. The error string is also printed twice — once internally by the orchestrator, once by the caller in `reanalyze_screenshots.py`.

**Step 1: Update `_observe_screenshots` error handling**

Replace the `except` blocks at the end of `_observe_screenshots` (around line 388):

```python
        except json.JSONDecodeError as e:
            error_msg = (
                f"Pass 1 truncated — response hit {8000} token limit. Debug file saved."
                if response.stop_reason == "max_tokens"
                else f"Pass 1 malformed JSON (char {e.pos}). Debug file saved."
            )
            return {
                "success": False,
                "error": error_msg,
                "raw_response": response_text if "response_text" in locals() else None,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
```

Note: `response` is in scope at the `except json.JSONDecodeError` point because it's assigned before `_parse_json_response` is called. `response.stop_reason` is the Anthropic API field.

**Step 2: Update `analyze_screenshots` error handling**

Replace the `except json.JSONDecodeError` block inside `analyze_screenshots` (the one that re-raises, around line 534):

```python
            except json.JSONDecodeError as json_error:
                debug_path = Path("output/debug_malformed_json")
                debug_path.mkdir(parents=True, exist_ok=True)
                timestamp = (
                    Path(screenshot_paths[0]).parent.parent.name if screenshot_paths else "unknown"
                )
                debug_file = debug_path / f"{site_name.replace(' ', '_')}_{timestamp}.txt"
                with open(debug_file, "w") as f:
                    f.write(f"=== MALFORMED JSON DEBUG ===\n")
                    f.write(f"Site: {site_name}\n")
                    f.write(f"Error: {json_error}\n\n")
                    f.write(f"=== RAW RESPONSE ===\n")
                    f.write(response_text)
                raise
```

Replace the outer `except json.JSONDecodeError` (around line 556):

```python
        except json.JSONDecodeError as e:
            error_msg = (
                f"Pass 2 truncated — response hit {16000} token limit. Debug file saved."
                if response.stop_reason == "max_tokens"
                else f"Pass 2 malformed JSON (char {getattr(e, 'pos', '?')}). Debug file saved."
            )
            return {
                "success": False,
                "error": error_msg,
                "raw_response": response_text if "response_text" in locals() else None,
            }
```

**Step 3: Verify manually**

Run a quick test by temporarily setting `max_tokens=10` in `_observe_screenshots`, running one competitor, and confirming the error reads "Pass 1 truncated — response hit 10 token limit." Revert after.

**Step 4: Commit**

```bash
git add src/analyzers/claude_analyzer.py
git commit -m "fix: clear error messages for truncation vs malformed JSON in analyzer"
```

---

### Task 2: Add `progress`/`task_id` params to `analyze_competitor_from_screenshots`

**Files:**
- Modify: `main.py:487-620` (`analyze_competitor_from_screenshots`)

**Context:** This method currently prints its own pass status using `self.console.print`. We need it to also update a `Progress` task description when a progress context is passed in from the caller. The method signature and internal prints stay otherwise unchanged — we're adding optional params only.

**Step 1: Update method signature**

Change:
```python
async def analyze_competitor_from_screenshots(
    self,
    capture_data: Dict[str, Any]
) -> Dict[str, Any]:
```

To:
```python
async def analyze_competitor_from_screenshots(
    self,
    capture_data: Dict[str, Any],
    progress=None,
    task_id=None,
) -> Dict[str, Any]:
```

**Step 2: Add a helper at the top of the method body**

After the `site_name`/`url`/`screenshot_paths` assignments, add:

```python
def _update(desc: str):
    if progress is not None and task_id is not None:
        progress.update(task_id, description=desc)
```

**Step 3: Insert `_update` calls at each pass stage**

Just before the `self.console.print(f"  [cyan]Pass 1: Observing screenshots...[/cyan]")` line, add:
```python
_update(f"Pass 1: Observing {site_name}...")
```

Just before the `self.console.print(f"  [cyan]Pass 2: Scoring against criteria...[/cyan]")` line, add:
```python
_update(f"Pass 2: Scoring {site_name}...")
```

**Step 4: Remove the notable states bullet list**

Delete these lines (around line 569-574):
```python
# Surface notable states to console
notable = observation.get("notable_states", [])
if notable:
    self.console.print(f"  [yellow]Notable states:[/yellow]")
    for state in notable:
        self.console.print(f"    [yellow]• {state}[/yellow]")
```

The `✓ Observation saved (N notable states)` line above it stays.

**Step 5: Remove `[DEBUG]` prints**

Delete these lines from `_load_image_as_base64` (around line 428-432):
```python
print(f"  [DEBUG] Resized image from {original_size} to ({new_width}, {new_height})")
```
and:
```python
print(f"  [DEBUG] Image dimensions OK: {original_size}")
```

**Step 6: Commit**

```bash
git add main.py
git commit -m "feat: add progress params to analyze_competitor_from_screenshots, remove noise"
```

---

### Task 3: Add `_wait_with_countdown` helper to orchestrator

**Files:**
- Modify: `main.py` — add method to `UXAnalysisOrchestrator`

**Context:** The current `await asyncio.sleep(ANALYSIS_DELAY)` gives no feedback during the 90s wait. This helper replaces it, ticking 1s at a time and updating the progress description with a countdown.

**Step 1: Add the method to `UXAnalysisOrchestrator`**

Add after `analyze_competitor_from_screenshots`:

```python
async def _wait_with_countdown(
    self,
    delay: int,
    next_name: str,
    progress=None,
    task_id=None,
):
    """Waits `delay` seconds, updating progress description each second."""
    for remaining in range(delay, 0, -1):
        if progress is not None and task_id is not None:
            progress.update(
                task_id,
                description=f"Next: {next_name} in {remaining}s  •  Ctrl+C to quit",
            )
        await asyncio.sleep(1)
```

**Step 2: Commit**

```bash
git add main.py
git commit -m "feat: add _wait_with_countdown helper to orchestrator"
```

---

### Task 4: Wrap orchestrator's internal analysis loop with Progress

**Files:**
- Modify: `main.py:700-790` — the Phase 2 analysis loop inside `run()`

**Context:** The orchestrator's own `run()` method has a sequential analysis loop at Phase 2. This is used when running `main.py` directly (not via `reanalyze_screenshots.py`). We wrap it in a `Progress` context and thread `progress`/`task_id` through.

**Step 1: Add imports at top of `main.py` if not already present**

Check that these are imported (they already are):
```python
from rich.progress import Progress, SpinnerColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn, TextColumn
```

**Step 2: Replace the Phase 2 loop**

Find the block starting `self.console.print("\n[bold cyan]═══ Phase 2: AI Analysis (Sequential) ═══[/bold cyan]")` (around line 706).

Replace `ANALYSIS_DELAY = 90` comment and the entire `for idx, capture_data in enumerate(...)` loop with:

```python
ANALYSIS_DELAY = 90

with Progress(
    SpinnerColumn(),
    TextColumn("[bold cyan]Analyzing competitors[/bold cyan]"),
    BarColumn(),
    TextColumn("{task.completed}/{task.total}"),
    TextColumn("[dim]{task.description}[/dim]"),
    TimeElapsedColumn(),
    console=self.console,
) as progress:
    task_id = progress.add_task("", total=len(successful_captures))

    for idx, capture_data in enumerate(successful_captures, 1):
        progress.console.print(
            f"[cyan]Analyzing {idx}/{len(successful_captures)}:[/cyan] {capture_data['site_name']}"
        )

        try:
            analysis_result = await self.analyze_competitor_from_screenshots(
                capture_data, progress=progress, task_id=task_id
            )
        except Exception as e:
            progress.console.print(f"  [red]✗ {capture_data['site_name']}: {str(e)}[/red]")
            processed_results.append({
                "success": False,
                "site_name": capture_data['site_name'],
                "url": capture_data['url'],
                "error": str(e)
            })
            progress.update(task_id, advance=1)
            continue

        if analysis_result.get("success"):
            progress.console.print(f"  [green]✓ {capture_data['site_name']}[/green]")
        else:
            progress.console.print(
                f"  [yellow]⚠ {capture_data['site_name']}: {analysis_result.get('error', 'Unknown error')}[/yellow]"
            )

        processed_results.append(analysis_result)

        if audit_structure and analysis_result.get("success"):
            try:
                analysis_path = get_analysis_path(
                    audit_structure['competitors'],
                    capture_data['site_name']
                )
                self.report_generator.save_competitor_analysis(
                    analysis_result, analysis_path
                )
            except Exception as e:
                progress.console.print(
                    f"  [yellow]Warning: Could not save {capture_data['site_name']}: {e}[/yellow]"
                )

        progress.update(task_id, advance=1)

        if idx < len(successful_captures):
            next_name = successful_captures[idx]['site_name']
            await self._wait_with_countdown(
                ANALYSIS_DELAY, next_name, progress=progress, task_id=task_id
            )
```

**Step 3: Commit**

```bash
git add main.py
git commit -m "feat: wrap orchestrator Phase 2 loop with Rich progress bar and countdown"
```

---

### Task 5: Wrap `reanalyze_screenshots.py` loop with Progress

**Files:**
- Modify: `scripts/reanalyze_screenshots.py:194-232`

**Context:** The reanalyze script has its own loop with bare `print()` calls. Replace with a `Progress` context using the same layout as the orchestrator loop. Also remove the now-redundant success/fail prints inside the loop (the orchestrator method handles those).

**Step 1: Add imports to `reanalyze_screenshots.py`**

Add after the existing imports:
```python
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
from rich.console import Console
```

**Step 2: Add a console instance**

After `load_dotenv()` at the top of `reanalyze_audit`, add:
```python
console = Console()
```

**Step 3: Replace the analysis loop**

Replace the entire block from `print("═══ Phase 2: AI Analysis (Sequential) ═══")` through `await asyncio.sleep(ANALYSIS_DELAY)` with:

```python
        console.print("\n[bold cyan]═══ Phase 2: AI Analysis (Sequential) ═══[/bold cyan]")

        ANALYSIS_DELAY = 90

        with Progress(
            SpinnerColumn(),
            TextColumn("[bold cyan]Analyzing competitors[/bold cyan]"),
            BarColumn(),
            TextColumn("{task.completed}/{task.total}"),
            TextColumn("[dim]{task.description}[/dim]"),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            task_id = progress.add_task("", total=len(needs_analysis))

            for idx, comp_data in enumerate(needs_analysis, 1):
                progress.console.print(
                    f"[cyan]Analyzing {idx}/{len(needs_analysis)}:[/cyan] {comp_data['site_name']}"
                )

                try:
                    analysis_result = await orchestrator.analyze_competitor_from_screenshots(
                        comp_data, progress=progress, task_id=task_id
                    )
                except Exception as e:
                    progress.console.print(f"  [red]✗ {str(e)}[/red]")
                    results.append({
                        "success": False,
                        "site_name": comp_data['site_name'],
                        "url": comp_data['url'],
                        "error": str(e)
                    })
                    progress.update(task_id, advance=1)
                    continue

                if analysis_result.get("success"):
                    progress.console.print(f"  [green]✓ {comp_data['site_name']}[/green]")
                else:
                    progress.console.print(
                        f"  [yellow]⚠ {analysis_result.get('error', 'Unknown error')}[/yellow]"
                    )

                results.append(analysis_result)
                progress.update(task_id, advance=1)

                if idx < len(needs_analysis):
                    next_name = needs_analysis[idx]['site_name']
                    await orchestrator._wait_with_countdown(
                        ANALYSIS_DELAY, next_name, progress=progress, task_id=task_id
                    )
```

**Step 4: Replace remaining bare `print()` calls in `reanalyze_audit`**

Change `print(...)` → `console.print(...)` for all remaining calls in the function (the setup prints at the top, the "Reanalysis complete" and report generation prints at the bottom).

**Step 5: Test the full flow**

```bash
cd /home/matt99is/projects/UXMaturityAnalysis
.venv/bin/python scripts/reanalyze_screenshots.py output/example-assets/2025-11-24_basket_pages
```

Verify:
- Progress bar appears at bottom
- Pass 1/Pass 2 descriptions update in-place
- Countdown runs during wait periods
- No `[DEBUG]` lines
- No notable states bullet lists
- Error messages are human-readable if any failures occur

**Step 6: Commit**

```bash
git add scripts/reanalyze_screenshots.py
git commit -m "feat: add Rich progress bar and countdown to reanalyze_screenshots script"
```
