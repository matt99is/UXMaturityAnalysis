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
