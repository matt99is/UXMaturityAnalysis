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
