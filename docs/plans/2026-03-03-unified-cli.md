# Unified CLI Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace scattered entry points with a single `./run.sh` that guides users through an interactive menu while preserving silent flags for automation.

**Architecture:** New `cli.py` handles all menu logic and routes to existing `main.py`, `reanalyze_screenshots.py`, and `deploy_netlify.py` via subprocess. New `src/competitor_config.py` owns YAML loading, URL validation, and inline correction. `run.sh` is simplified to tmux layer only.

**Tech Stack:** Python 3.12, questionary (new), PyYAML (existing), Rich (existing), subprocess

**Design doc:** `docs/plans/2026-03-03-unified-cli-design.md`

---

## Task 1: Add questionary, create competitors/ structure, migrate config

**Files:**
- Modify: `requirements.txt`
- Create: `competitors/petfood.yaml`
- Keep: `competitors.petfood.json` (don't delete — it's a git-tracked reference)

**Step 1: Add questionary to requirements.txt**

Add after the `rich` line:
```
questionary==2.0.1
```

**Step 2: Install it**

```bash
cd /home/matt99is/projects/UXMaturityAnalysis
.venv/bin/pip install questionary==2.0.1
```

Expected: `Successfully installed questionary-2.0.1`

**Step 3: Create competitors/petfood.yaml**

Create `/home/matt99is/projects/UXMaturityAnalysis/competitors/petfood.yaml`:

```yaml
name: "UK Pet Food Retail"
competitors:
  - name: zooplus
    pages:
      basket: https://www.zooplus.co.uk/shop/cart
  - name: jollyes
    pages:
      basket: https://www.jollyes.co.uk/basket
  - name: chewy
    pages:
      basket: https://www.chewy.com/cart
  - name: pet supermarket
    pages:
      basket: https://pet-supermarket.co.uk/basket
  - name: petshop.co.uk
    pages:
      basket: https://www.petshop.co.uk/basket
  - name: pet drugs online
    pages:
      basket: https://www.petdrugsonline.co.uk/basket
  - name: animed
    pages:
      basket: https://www.animed.co.uk/basket
  - name: tesco
    pages:
      basket: https://www.tesco.com/groceries/en-GB/trolley
  - name: sainsburys
    pages:
      basket: https://www.sainsburys.co.uk/webapp/wcs/stores/servlet/gb/groceries/trolley
  - name: morrisons
    pages:
      basket: https://groceries.morrisons.com/checkout/trolley
  - name: amazon
    pages:
      basket: https://www.amazon.co.uk/gp/cart/view.html
  - name: lords and labradors
    pages:
      basket: https://www.lordsandlabradors.co.uk/basket
  - name: pooch and mutt
    pages:
      basket: https://www.poochandmutt.co.uk/cart
  - name: pet planet
    pages:
      basket: https://petplanet.co.uk/basket
  - name: viovet
    pages:
      basket: https://www.viovet.co.uk/basket
  - name: pets corner
    pages:
      basket: https://www.petscorner.co.uk/basket
```

Note: These basket URLs are best-guess based on the homepage URLs in `competitors.petfood.json`. They will be validated and corrected at first run via the inline correction flow.

**Step 4: Commit**

```bash
git add requirements.txt competitors/petfood.yaml
git commit -m "feat: add questionary dependency and competitors/petfood.yaml config"
```

---

## Task 2: Create src/competitor_config.py

**Files:**
- Create: `src/competitor_config.py`
- Create: `tests/test_competitor_config.py`

**Step 1: Write the failing tests**

Create `tests/test_competitor_config.py`:

```python
import pytest
import tempfile
from pathlib import Path
import yaml

from src.competitor_config import (
    list_competitor_sets,
    load_competitor_set,
    get_page_type_urls,
    save_url_correction,
)


@pytest.fixture
def competitors_dir(tmp_path):
    """Temporary competitors/ directory with a test YAML."""
    data = {
        "name": "Test Retail",
        "competitors": [
            {"name": "shopA", "pages": {"basket": "https://shopA.com/cart", "product": "https://shopA.com/product/1"}},
            {"name": "shopB", "pages": {"basket": "https://shopB.com/basket"}},
            {"name": "shopC", "pages": {"product": "https://shopC.com/item/1"}},
        ]
    }
    f = tmp_path / "testretail.yaml"
    f.write_text(yaml.dump(data))
    return tmp_path


def test_list_competitor_sets(competitors_dir):
    sets = list_competitor_sets(competitors_dir)
    assert sets == [("testretail", "Test Retail")]


def test_load_competitor_set(competitors_dir):
    result = load_competitor_set("testretail", competitors_dir)
    assert result["name"] == "Test Retail"
    assert len(result["competitors"]) == 3


def test_get_page_type_urls_returns_only_matching(competitors_dir):
    competitor_set = load_competitor_set("testretail", competitors_dir)
    urls = get_page_type_urls(competitor_set, "basket")
    assert urls == [
        {"name": "shopA", "url": "https://shopA.com/cart"},
        {"name": "shopB", "url": "https://shopB.com/basket"},
    ]
    # shopC has no basket URL — excluded


def test_get_page_type_urls_empty_when_none_match(competitors_dir):
    competitor_set = load_competitor_set("testretail", competitors_dir)
    urls = get_page_type_urls(competitor_set, "checkout")
    assert urls == []


def test_save_url_correction(competitors_dir):
    yaml_path = competitors_dir / "testretail.yaml"
    save_url_correction(yaml_path, "shopB", "basket", "https://shopB.com/new-basket")

    # Reload and verify
    with open(yaml_path) as f:
        data = yaml.safe_load(f)
    shopB = next(c for c in data["competitors"] if c["name"] == "shopB")
    assert shopB["pages"]["basket"] == "https://shopB.com/new-basket"


def test_save_url_correction_adds_new_page_type(competitors_dir):
    yaml_path = competitors_dir / "testretail.yaml"
    save_url_correction(yaml_path, "shopB", "product", "https://shopB.com/product/1")

    with open(yaml_path) as f:
        data = yaml.safe_load(f)
    shopB = next(c for c in data["competitors"] if c["name"] == "shopB")
    assert shopB["pages"]["product"] == "https://shopB.com/product/1"
```

**Step 2: Run to verify they fail**

```bash
cd /home/matt99is/projects/UXMaturityAnalysis
.venv/bin/pytest tests/test_competitor_config.py -v
```

Expected: `ModuleNotFoundError: No module named 'src.competitor_config'`

**Step 3: Implement src/competitor_config.py**

Create `src/competitor_config.py`:

```python
"""
Competitor config loader and URL management.

Reads from competitors/*.yaml files. Each file defines a set of competitors
with per-page-type URLs. Provides URL validation and inline correction.
"""

from pathlib import Path
from typing import List, Dict, Tuple, Any
import yaml

# Default competitors directory relative to project root
_DEFAULT_DIR = Path(__file__).parent.parent / "competitors"


def list_competitor_sets(competitors_dir: Path = None) -> List[Tuple[str, str]]:
    """
    Discover all competitor YAML files.

    Returns list of (slug, display_name) tuples sorted by slug.
    slug is the filename stem (e.g. 'petfood').
    display_name is the 'name' field from the YAML.
    """
    d = competitors_dir or _DEFAULT_DIR
    results = []
    for yaml_file in sorted(d.glob("*.yaml")):
        with open(yaml_file) as f:
            data = yaml.safe_load(f)
        results.append((yaml_file.stem, data.get("name", yaml_file.stem)))
    return results


def load_competitor_set(slug: str, competitors_dir: Path = None) -> Dict[str, Any]:
    """Load a competitor YAML by slug (filename stem)."""
    d = competitors_dir or _DEFAULT_DIR
    path = d / f"{slug}.yaml"
    with open(path) as f:
        return yaml.safe_load(f)


def get_page_type_urls(competitor_set: Dict[str, Any], page_type: str) -> List[Dict[str, str]]:
    """
    Extract {name, url} pairs for a specific page type.

    Competitors with no entry for page_type are silently excluded.
    """
    results = []
    for competitor in competitor_set.get("competitors", []):
        url = competitor.get("pages", {}).get(page_type)
        if url:
            results.append({"name": competitor["name"], "url": url})
    return results


def save_url_correction(
    yaml_path: Path,
    competitor_name: str,
    page_type: str,
    new_url: str,
) -> None:
    """
    Update a competitor's page URL in-place and save the YAML.

    Creates the pages entry if the competitor has none for this page_type.
    """
    with open(yaml_path) as f:
        data = yaml.safe_load(f)

    for competitor in data.get("competitors", []):
        if competitor["name"] == competitor_name:
            if "pages" not in competitor:
                competitor["pages"] = {}
            competitor["pages"][page_type] = new_url
            break

    with open(yaml_path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
```

**Step 4: Run tests to verify they pass**

```bash
.venv/bin/pytest tests/test_competitor_config.py -v
```

Expected: 6 passed

**Step 5: Commit**

```bash
git add src/competitor_config.py tests/test_competitor_config.py
git commit -m "feat: add competitor_config module with YAML loading and URL correction"
```

---

## Task 3: Create cli.py — silent flag bypass

The first responsibility of `cli.py` is to detect silent flags (`--reanalyze`, `--deploy`) and route directly to the existing scripts without showing any menus. This preserves backwards compatibility for the Telegram bot and any automation.

**Files:**
- Create: `cli.py`
- Create: `tests/test_cli_routing.py`

**Step 1: Write failing tests**

Create `tests/test_cli_routing.py`:

```python
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from cli import parse_silent_args, SilentArgs


def test_parse_reanalyze_flag():
    args = parse_silent_args(["--reanalyze", "output/audits/2026-03-02_basket_pages"])
    assert args is not None
    assert args.mode == "reanalyze"
    assert args.audit_folder == "output/audits/2026-03-02_basket_pages"
    assert args.force is False
    assert args.force_observe is False


def test_parse_reanalyze_with_force():
    args = parse_silent_args(["--reanalyze", "output/audits/2026-03-02_basket_pages", "--force"])
    assert args.force is True


def test_parse_reanalyze_with_force_observe():
    args = parse_silent_args(["--reanalyze", "output/audits/2026-03-02_basket_pages", "--force-observe"])
    assert args.force_observe is True


def test_parse_deploy_flag():
    args = parse_silent_args(["--deploy"])
    assert args is not None
    assert args.mode == "deploy"


def test_parse_deploy_draft():
    args = parse_silent_args(["--deploy", "--draft"])
    assert args.draft is True


def test_no_silent_flags_returns_none():
    args = parse_silent_args([])
    assert args is None


def test_no_silent_flags_with_other_args_returns_none():
    args = parse_silent_args(["--help"])
    assert args is None
```

**Step 2: Run to verify they fail**

```bash
.venv/bin/pytest tests/test_cli_routing.py -v
```

Expected: `ModuleNotFoundError: No module named 'cli'`

**Step 3: Implement parse_silent_args in cli.py**

Create `cli.py` (project root):

```python
#!/usr/bin/env python3
"""
UX Maturity Analysis — unified CLI entry point.

Interactive mode (no args):  guided menus for all operations
Silent mode (with flags):    non-interactive, for automation and Telegram bot

Usage:
    ./run.sh                                              # interactive
    ./run.sh --reanalyze output/audits/<folder>           # silent
    ./run.sh --reanalyze output/audits/<folder> --force   # silent, re-run all
    ./run.sh --reanalyze output/audits/<folder> --force-observe
    ./run.sh --deploy                                     # silent
    ./run.sh --deploy --draft                             # silent, draft deploy
"""

import sys
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List

PROJECT_ROOT = Path(__file__).parent
VENV_PYTHON = PROJECT_ROOT / ".venv" / "bin" / "python3"


# ---------------------------------------------------------------------------
# Silent arg parsing
# ---------------------------------------------------------------------------

@dataclass
class SilentArgs:
    mode: str                    # "reanalyze" | "deploy"
    audit_folder: str = ""
    force: bool = False
    force_observe: bool = False
    draft: bool = False


def parse_silent_args(argv: List[str]) -> Optional[SilentArgs]:
    """
    Parse silent (non-interactive) flags from argv.

    Returns SilentArgs if a silent mode is detected, None otherwise.
    """
    if "--reanalyze" in argv:
        idx = argv.index("--reanalyze")
        folder = argv[idx + 1] if idx + 1 < len(argv) and not argv[idx + 1].startswith("--") else ""
        return SilentArgs(
            mode="reanalyze",
            audit_folder=folder,
            force="--force" in argv,
            force_observe="--force-observe" in argv,
        )

    if "--deploy" in argv:
        return SilentArgs(
            mode="deploy",
            draft="--draft" in argv,
        )

    return None


# ---------------------------------------------------------------------------
# Script runners
# ---------------------------------------------------------------------------

def run_reanalyze(args: SilentArgs) -> int:
    cmd = [str(VENV_PYTHON), "scripts/reanalyze_screenshots.py", args.audit_folder]
    if args.force:
        cmd.append("--force")
    if args.force_observe:
        cmd.append("--force-observe")
    result = subprocess.run(cmd, cwd=PROJECT_ROOT)
    return result.returncode


def run_deploy(args: SilentArgs) -> int:
    cmd = [str(VENV_PYTHON), "scripts/deploy_netlify.py"]
    if args.draft:
        cmd.append("--draft")
    result = subprocess.run(cmd, cwd=PROJECT_ROOT)
    return result.returncode


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    argv = sys.argv[1:]
    silent = parse_silent_args(argv)

    if silent:
        if silent.mode == "reanalyze":
            sys.exit(run_reanalyze(silent))
        elif silent.mode == "deploy":
            sys.exit(run_deploy(silent))

    # Interactive mode — implemented in Tasks 4-7
    print("Interactive mode coming soon.")


if __name__ == "__main__":
    main()
```

**Step 4: Run tests to verify they pass**

```bash
.venv/bin/pytest tests/test_cli_routing.py -v
```

Expected: 7 passed

**Step 5: Commit**

```bash
git add cli.py tests/test_cli_routing.py
git commit -m "feat: cli.py entry point with silent flag parsing and subprocess routing"
```

---

## Task 4: cli.py — discover_audits()

The reanalyse menu needs to list existing audits sorted newest-first with competitor count.

**Files:**
- Modify: `cli.py`
- Modify: `tests/test_cli_routing.py`

**Step 1: Add tests to test_cli_routing.py**

Append to `tests/test_cli_routing.py`:

```python
from cli import discover_audits


def test_discover_audits(tmp_path):
    # Create fake audit structure
    (tmp_path / "2026-03-02_basket_pages" / "amazon").mkdir(parents=True)
    (tmp_path / "2026-03-02_basket_pages" / "zooplus").mkdir(parents=True)
    (tmp_path / "2026-03-02_basket_pages" / "css").mkdir(parents=True)  # non-competitor dir
    (tmp_path / "2026-02-24_basket_pages" / "amazon").mkdir(parents=True)

    audits = discover_audits(tmp_path)

    assert len(audits) == 2
    # Newest first
    assert audits[0]["folder"] == str(tmp_path / "2026-03-02_basket_pages")
    assert audits[0]["label"] == "2026-03-02  basket_pages  (2 competitors)"
    assert audits[1]["label"] == "2026-02-24  basket_pages  (1 competitor)"


def test_discover_audits_empty(tmp_path):
    assert discover_audits(tmp_path) == []
```

**Step 2: Run to verify they fail**

```bash
.venv/bin/pytest tests/test_cli_routing.py::test_discover_audits -v
```

Expected: `ImportError: cannot import name 'discover_audits'`

**Step 3: Add discover_audits to cli.py**

Add after the `run_deploy` function:

```python
# ---------------------------------------------------------------------------
# Audit discovery
# ---------------------------------------------------------------------------

_SKIP_DIRS = {"css", "index.html", "_audit_summary.json", "_comparison_report.md"}


def discover_audits(audits_dir: Path = None) -> List[dict]:
    """
    Scan output/audits/ and return audit metadata sorted newest-first.

    Each entry: {"folder": str, "label": str, "name": str}
    """
    d = audits_dir or (PROJECT_ROOT / "output" / "audits")
    if not d.exists():
        return []

    results = []
    for audit_dir in sorted(d.iterdir(), reverse=True):
        if not audit_dir.is_dir():
            continue
        # Count competitor dirs (skip utility dirs)
        competitors = [
            p for p in audit_dir.iterdir()
            if p.is_dir() and p.name not in _SKIP_DIRS and not p.name.startswith("_")
        ]
        count = len(competitors)
        noun = "competitor" if count == 1 else "competitors"
        # "2026-03-02_basket_pages" → "2026-03-02  basket_pages"
        display_name = audit_dir.name.replace("_", "  ", 1)
        label = f"{display_name}  ({count} {noun})"
        results.append({
            "folder": str(audit_dir),
            "label": label,
            "name": audit_dir.name,
        })
    return results
```

**Step 4: Run tests to verify they pass**

```bash
.venv/bin/pytest tests/test_cli_routing.py -v
```

Expected: all pass

**Step 5: Commit**

```bash
git add cli.py tests/test_cli_routing.py
git commit -m "feat: discover_audits() scans output/audits/ for reanalyse menu"
```

---

## Task 5: cli.py — reanalyse interactive menu

**Files:**
- Modify: `cli.py`

**Step 1: Add reanalyse_menu to cli.py**

Add after `discover_audits`:

```python
# ---------------------------------------------------------------------------
# Interactive menus
# ---------------------------------------------------------------------------

def reanalyse_menu() -> int:
    """Guided reanalyse flow. Returns exit code."""
    import questionary

    audits = discover_audits()
    if not audits:
        print("No existing audits found in output/audits/")
        return 1

    choices = [a["label"] for a in audits]
    selected_label = questionary.select(
        "Which audit?",
        choices=choices,
    ).ask()

    if selected_label is None:
        return 0  # user pressed Ctrl+C

    selected = next(a for a in audits if a["label"] == selected_label)

    depth = questionary.select(
        "What to re-run?",
        choices=[
            "Report only   (no AI — regenerate HTML from existing scores)",
            "Re-score      (keep observations, rerun scoring pass only)",
            "Full          (redo everything — observations + scoring)",
        ],
    ).ask()

    if depth is None:
        return 0

    args = SilentArgs(mode="reanalyze", audit_folder=selected["folder"])
    if depth.startswith("Re-score"):
        args.force = True
    elif depth.startswith("Full"):
        args.force = True
        args.force_observe = True

    return run_reanalyze(args)
```

**Step 2: Wire into main()**

Replace `# Interactive mode — implemented in Tasks 4-7` block in `main()`:

```python
    # Interactive mode
    import questionary

    action = questionary.select(
        "What do you want to do?",
        choices=[
            "Fresh analysis   (capture screenshots → analyse → report)",
            "Reanalyse        (work with existing screenshots)",
            "Deploy",
        ],
    ).ask()

    if action is None:
        sys.exit(0)

    if action.startswith("Reanalyse"):
        sys.exit(reanalyse_menu())
    elif action.startswith("Deploy"):
        sys.exit(run_deploy(SilentArgs(mode="deploy")))
    elif action.startswith("Fresh"):
        print("Fresh analysis menu coming in next task.")
        sys.exit(0)
```

**Step 3: Smoke test manually**

```bash
cd /home/matt99is/projects/UXMaturityAnalysis
.venv/bin/python cli.py
```

Navigate: choose "Reanalyse" → pick an audit → pick "Report only". Verify `reanalyze_screenshots.py` runs with no flags.

Try again → pick "Full". Verify it runs with `--force --force-observe`.

**Step 4: Commit**

```bash
git add cli.py
git commit -m "feat: reanalyse interactive menu with depth selection"
```

---

## Task 6: cli.py — URL validation flow

**Files:**
- Modify: `cli.py`
- Modify: `tests/test_cli_routing.py`

**Step 1: Add tests**

Append to `tests/test_cli_routing.py`:

```python
from unittest.mock import patch
from cli import validate_and_correct_urls


def test_validate_and_correct_urls_all_valid():
    competitors = [
        {"name": "shopA", "url": "https://shopA.com/cart"},
        {"name": "shopB", "url": "https://shopB.com/basket"},
    ]
    # Mock urllib to return 200 for all
    with patch("cli._head_check", return_value=True):
        valid, corrections = validate_and_correct_urls(competitors, interactive=False)
    assert valid == competitors
    assert corrections == {}


def test_validate_and_correct_urls_skips_invalid_when_non_interactive():
    competitors = [
        {"name": "shopA", "url": "https://shopA.com/cart"},
        {"name": "shopB", "url": "https://shopB.com/bad"},
    ]
    with patch("cli._head_check", side_effect=[True, False]):
        valid, corrections = validate_and_correct_urls(competitors, interactive=False)
    assert len(valid) == 1
    assert valid[0]["name"] == "shopA"
    assert corrections == {}
```

**Step 2: Run to verify they fail**

```bash
.venv/bin/pytest tests/test_cli_routing.py::test_validate_and_correct_urls_all_valid -v
```

Expected: `ImportError: cannot import name 'validate_and_correct_urls'`

**Step 3: Add _head_check and validate_and_correct_urls to cli.py**

Add after `discover_audits`:

```python
# ---------------------------------------------------------------------------
# URL validation
# ---------------------------------------------------------------------------

import urllib.request
import urllib.error


def _head_check(url: str, timeout: int = 5) -> bool:
    """
    Returns True if URL responds with a non-4xx status.
    Treats redirects as valid (sites often redirect /basket to /cart etc.).
    """
    try:
        req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status < 400
    except (urllib.error.HTTPError, urllib.error.URLError, Exception):
        return False


def validate_and_correct_urls(
    competitors: List[dict],
    interactive: bool = True,
    yaml_path: Path = None,
    page_type: str = "",
) -> tuple:
    """
    HEAD-check all competitor URLs.

    Returns (valid_competitors, corrections) where:
    - valid_competitors: list of {name, url} that passed or were corrected
    - corrections: dict of {competitor_name: new_url} for any corrections made

    In interactive mode, prompts for replacement URL on failure.
    In non-interactive mode, silently drops failed URLs.
    """
    from rich.console import Console
    console = Console()

    valid = []
    corrections = {}

    for comp in competitors:
        name = comp["name"]
        url = comp["url"]

        if _head_check(url):
            valid.append(comp)
            continue

        console.print(f"\n[yellow]⚠ {name} URL returned 404 or failed[/yellow]")
        console.print(f"  Current: {url}")

        if not interactive:
            console.print(f"  [dim]Skipping {name} (non-interactive mode)[/dim]")
            continue

        import questionary
        new_url = questionary.text(
            f"New URL for {name} (or Enter to skip):",
        ).ask()

        if new_url and new_url.strip():
            new_url = new_url.strip()
            valid.append({"name": name, "url": new_url})
            corrections[name] = new_url
            if yaml_path and page_type:
                from src.competitor_config import save_url_correction
                save_url_correction(yaml_path, name, page_type, new_url)
                console.print(f"  [green]✓ Saved correction to config[/green]")
        else:
            console.print(f"  [dim]Skipping {name}[/dim]")

    return valid, corrections
```

**Step 4: Run tests to verify they pass**

```bash
.venv/bin/pytest tests/test_cli_routing.py -v
```

Expected: all pass

**Step 5: Commit**

```bash
git add cli.py tests/test_cli_routing.py
git commit -m "feat: URL validation with HEAD checks and inline correction"
```

---

## Task 7: cli.py — fresh analysis menu and post-run deploy logic

**Files:**
- Modify: `cli.py`

**Step 1: Add fresh_analysis_menu to cli.py**

Add after `validate_and_correct_urls`:

```python
def fresh_analysis_menu() -> int:
    """Guided fresh analysis flow. Returns exit code."""
    import questionary
    import tempfile
    import json
    from src.competitor_config import list_competitor_sets, load_competitor_set, get_page_type_urls
    from src.config_loader import AnalysisConfig
    from rich.console import Console
    console = Console()

    # Page type — read available types from criteria_config/
    config = AnalysisConfig()
    available_types = config.list_available_analysis_types()
    page_type = questionary.select(
        "Which page type?",
        choices=available_types,
    ).ask()
    if page_type is None:
        return 0

    # Competitor set
    sets = list_competitor_sets()
    if not sets:
        console.print("[red]No competitor sets found in competitors/[/red]")
        return 1
    set_choices = [f"{display}  ({slug})" for slug, display in sets]
    selected_set_label = questionary.select(
        "Which competitor set?",
        choices=set_choices,
    ).ask()
    if selected_set_label is None:
        return 0
    selected_slug = sets[set_choices.index(selected_set_label)][0]

    # Capture mode
    capture_mode = questionary.select(
        "Capture mode?",
        choices=[
            "Supervised   (watch browser via noVNC URL — for basket setup, CAPTCHAs)",
            "Automated    (fully unattended — Playwright + bot evasion)",
        ],
    ).ask()
    if capture_mode is None:
        return 0
    is_supervised = capture_mode.startswith("Supervised")

    # Load competitors and validate URLs
    competitor_set = load_competitor_set(selected_slug)
    competitors = get_page_type_urls(competitor_set, page_type)

    if not competitors:
        console.print(f"[red]No URLs configured for page type '{page_type}' in {selected_slug}[/red]")
        return 1

    console.print(f"\n[cyan]Validating {len(competitors)} URLs...[/cyan]")
    yaml_path = PROJECT_ROOT / "competitors" / f"{selected_slug}.yaml"
    valid_competitors, _corrections = validate_and_correct_urls(
        competitors,
        interactive=True,
        yaml_path=yaml_path,
        page_type=page_type,
    )

    if not valid_competitors:
        console.print("[red]No valid URLs remaining after validation.[/red]")
        return 1

    # Write temp config for main.py (expects {"competitors": [{"name": ..., "url": ...}]})
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump({"competitors": valid_competitors}, f)
        temp_config = f.name

    # Build main.py command
    cmd = [
        str(VENV_PYTHON), "main.py",
        "--config", temp_config,
        "--analysis-type", page_type,
        "--no-deploy",  # we handle deploy ourselves below
    ]
    if is_supervised:
        cmd.append("--interactive")

    console.print(f"\n[bold cyan]Starting analysis — {len(valid_competitors)} competitors[/bold cyan]\n")
    result = subprocess.run(cmd, cwd=PROJECT_ROOT)

    # Post-run deploy
    skipped = len(competitors) - len(valid_competitors)
    return _post_run_deploy(result.returncode, skipped)


def _post_run_deploy(run_exit_code: int, skipped_count: int) -> int:
    """Auto-deploy on clean run; ask if any competitors were skipped."""
    import questionary
    from rich.console import Console
    console = Console()

    if run_exit_code != 0:
        console.print("\n[yellow]Analysis exited with errors — skipping deploy.[/yellow]")
        return run_exit_code

    if skipped_count == 0:
        console.print("\n[cyan]Deploying to Netlify...[/cyan]")
        return run_deploy(SilentArgs(mode="deploy"))

    noun = "competitor" if skipped_count == 1 else "competitors"
    deploy = questionary.confirm(
        f"⚠ {skipped_count} {noun} were skipped. Deploy partial report anyway?",
        default=False,
    ).ask()

    if deploy:
        return run_deploy(SilentArgs(mode="deploy"))

    console.print("[dim]Deploy skipped.[/dim]")
    return 0
```

**Step 2: Wire fresh_analysis_menu into main()**

Replace the `elif action.startswith("Fresh"):` stub:

```python
    elif action.startswith("Fresh"):
        sys.exit(fresh_analysis_menu())
```

**Step 3: Smoke test the full interactive flow**

```bash
.venv/bin/python cli.py
```

Walk through: Fresh analysis → basket_pages → petfood → Automated.

Verify it validates URLs (will likely prompt corrections for some), then calls `main.py --config /tmp/xxx.json --analysis-type basket_pages --no-deploy`.

You don't need to let it complete — Ctrl+C after seeing the main.py output begin. The important thing is it reaches that point correctly.

**Step 4: Commit**

```bash
git add cli.py
git commit -m "feat: fresh analysis menu with URL validation, capture mode, and post-run deploy"
```

---

## Task 8: Simplify run.sh

**Files:**
- Modify: `run.sh`

**Step 1: Replace run.sh content**

The current `run.sh` has its own `--reanalyze` / `--deploy` parsing logic. Now that `cli.py` handles all of that, `run.sh` only needs to handle the tmux layer and forward everything to `cli.py`.

Replace the entire contents of `run.sh` with:

```bash
#!/usr/bin/env bash
# run.sh — UX Maturity Analysis launcher
#
# Automatically runs inside a persistent tmux session so the analysis
# survives VS Code disconnects, SSH drops, or closing your laptop.
# All arguments are forwarded to cli.py.
#
# Usage:
#   ./run.sh                                    # interactive guided menu
#   ./run.sh --reanalyze <audit_folder>         # non-interactive reanalyse
#   ./run.sh --reanalyze <audit_folder> --force
#   ./run.sh --reanalyze <audit_folder> --force-observe
#   ./run.sh --deploy                           # non-interactive deploy
#   ./run.sh --deploy --draft

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PYTHON="$SCRIPT_DIR/.venv/bin/python3"
SESSION_NAME="analysis"

if [ ! -f "$VENV_PYTHON" ]; then
    echo "Error: virtual environment not found at $SCRIPT_DIR/.venv"
    echo "Run: cd $SCRIPT_DIR && uv sync"
    exit 1
fi

CMD="$VENV_PYTHON '$SCRIPT_DIR/cli.py' $*"

# If already in tmux or screen, run directly
if [ -n "${TMUX:-}" ] || [ -n "${STY:-}" ]; then
    eval "$CMD"
    exit $?
fi

echo ""
echo "  Starting inside tmux session \"$SESSION_NAME\" so the run survives"
echo "  any connection drop. Detach with: Ctrl+B then D"
echo "  Reattach with: tmux attach -t $SESSION_NAME"
echo ""

if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
    PANE_PID=$(tmux list-panes -t "$SESSION_NAME" -F "#{pane_pid}" 2>/dev/null | head -1)
    CHILDREN=$(pgrep -P "$PANE_PID" 2>/dev/null | wc -l)
    if [ "$CHILDREN" -gt 0 ]; then
        echo "  Warning: session \"$SESSION_NAME\" already has a process running."
        echo "  Attaching to the existing session instead."
        echo ""
        tmux attach -t "$SESSION_NAME"
        exit 0
    fi
    tmux send-keys -t "$SESSION_NAME" "$CMD" Enter
else
    tmux new-session -d -s "$SESSION_NAME" -x 220 -y 50
    tmux send-keys -t "$SESSION_NAME" "$CMD" Enter
fi

tmux attach -t "$SESSION_NAME"
```

**Step 2: Verify syntax**

```bash
bash -n run.sh && echo "Syntax OK"
```

Expected: `Syntax OK`

**Step 3: Smoke test silent passthrough**

```bash
# Should bypass tmux (we're already in a session) and call cli.py --reanalyze
./run.sh --reanalyze output/audits/2026-03-02_basket_pages
```

Expected: `reanalyze_screenshots.py` runs immediately with the correct folder.

**Step 4: Commit**

```bash
git add run.sh
git commit -m "refactor: simplify run.sh to tmux layer only, all routing moved to cli.py"
```

---

## Task 9: Final wiring check and docs update

**Files:**
- Modify: `docs/COMMON_TASKS.md`

**Step 1: Read COMMON_TASKS.md**

```bash
cat docs/COMMON_TASKS.md
```

**Step 2: Replace the commands section**

Find and replace any references to `python main.py`, `python3 scripts/reanalyze_screenshots.py`, or `python3 scripts/deploy_netlify.py` with the unified `./run.sh` equivalents. Add a short section at the top:

```markdown
## Running the tool

Always use `./run.sh`. It handles tmux session protection automatically.

| What you want | Command |
|---|---|
| Full interactive menu | `./run.sh` |
| Reanalyse existing audit | `./run.sh --reanalyze output/audits/<folder>` |
| Reanalyse, re-run scoring | `./run.sh --reanalyze output/audits/<folder> --force` |
| Reanalyse, redo everything | `./run.sh --reanalyze output/audits/<folder> --force-observe --force` |
| Deploy to Netlify | `./run.sh --deploy` |
```

**Step 3: Run full test suite**

```bash
.venv/bin/pytest tests/ -v
```

Expected: all existing tests pass, no regressions.

**Step 4: Commit**

```bash
git add docs/COMMON_TASKS.md
git commit -m "docs: update COMMON_TASKS.md with unified ./run.sh commands"
```
