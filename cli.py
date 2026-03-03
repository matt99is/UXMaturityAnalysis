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


if __name__ == "__main__":
    main()
