#!/usr/bin/env python3
"""Validate vault project note size and structure."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

DEFAULT_NOTE_PATH = Path("/home/matt99is/vault/Projects/UXMaturityAnalysis.md")

REQUIRED_SECTIONS = (
    "What it is",
    "Current status",
    "Active decisions",
    "Known gotchas",
    "Next steps",
    "References",
)

SECTION_BULLET_LIMITS = {
    "Current status": 12,
    "Active decisions": 8,
    "Known gotchas": 8,
    "Next steps": 6,
    "References": 12,
}

BANNED_HISTORY_HEADINGS = (
    "recently completed",
    "changelog",
    "history",
    "updates log",
)

DATE_PATTERN = re.compile(r"\b20\d{2}-\d{2}-\d{2}\b")
VERSION_PATTERN = re.compile(r"\bv\d+\.\d+(?:\.\d+)?\b", re.IGNORECASE)
COMMIT_PATTERN = re.compile(r"\b[0-9a-f]{7,40}\b")


def _extract_sections(
    lines: Sequence[str],
) -> Tuple[List[str], Dict[str, List[str]], List[str]]:
    """Return section headings, section content map, and duplicate headings."""
    headings: List[str] = []
    sections: Dict[str, List[str]] = {}
    duplicates: List[str] = []
    current_key = ""

    for raw_line in lines:
        line = raw_line.rstrip("\n")
        if line.startswith("## "):
            heading = line[3:].strip()
            key = heading.lower()
            headings.append(heading)
            if key in sections:
                duplicates.append(heading)
            else:
                sections[key] = []
            current_key = key
            continue

        if current_key:
            sections[current_key].append(line)

    return headings, sections, duplicates


def _is_changelog_style_bullet(line: str) -> bool:
    """Detect dated/versioned status bullets that read like history logs."""
    return bool(
        DATE_PATTERN.search(line)
        or VERSION_PATTERN.search(line)
        or COMMIT_PATTERN.search(line)
    )


def validate_note_text(
    note_text: str,
    max_lines: int = 220,
    max_chars: int = 14000,
) -> List[str]:
    """Validate note text and return a list of human-readable errors."""
    errors: List[str] = []
    lines = note_text.splitlines()

    if len(lines) > max_lines:
        errors.append(f"Line limit exceeded: {len(lines)} > {max_lines}.")

    char_count = len(note_text)
    if char_count > max_chars:
        errors.append(f"Character limit exceeded: {char_count} > {max_chars}.")

    headings, sections, duplicates = _extract_sections(lines)

    for duplicate in duplicates:
        errors.append(f"Duplicate section heading: '{duplicate}'.")

    lower_headings = [heading.lower() for heading in headings]
    for banned in BANNED_HISTORY_HEADINGS:
        if any(banned in heading for heading in lower_headings):
            errors.append(
                f"Banned history heading detected ('{banned}'). "
                "Vault note must be current-state only."
            )

    for section_name in REQUIRED_SECTIONS:
        section_key = section_name.lower()
        if section_key not in sections:
            errors.append(f"Missing required section: '## {section_name}'.")

    for section_name, bullet_limit in SECTION_BULLET_LIMITS.items():
        section_key = section_name.lower()
        content = sections.get(section_key, [])
        bullet_count = sum(
            1 for line in content if line.strip().startswith("- ")
        )
        if bullet_count > bullet_limit:
            errors.append(
                f"Section '## {section_name}' has {bullet_count} bullets "
                f"(limit: {bullet_limit})."
            )

    current_status_lines = sections.get("current status", [])
    for line in current_status_lines:
        stripped = line.strip()
        if not stripped.startswith("- "):
            continue
        if _is_changelog_style_bullet(stripped):
            errors.append(
                "Changelog-style bullet detected in '## Current status': "
                f"'{stripped}'. Replace with present-tense current truth."
            )

    return errors


def validate_note_file(
    note_path: Path,
    max_lines: int = 220,
    max_chars: int = 14000,
    strict_missing: bool = False,
) -> List[str]:
    """Read and validate a note file."""
    if not note_path.exists():
        if strict_missing:
            return [f"Vault note not found: {note_path}"]
        return []

    try:
        note_text = note_path.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"Failed to read vault note '{note_path}': {exc}"]

    return validate_note_text(
        note_text,
        max_lines=max_lines,
        max_chars=max_chars,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate vault project note size and structure"
    )
    parser.add_argument(
        "--note-path",
        type=Path,
        default=DEFAULT_NOTE_PATH,
        help=f"Path to vault note (default: {DEFAULT_NOTE_PATH})",
    )
    parser.add_argument(
        "--max-lines",
        type=int,
        default=220,
        help="Maximum allowed lines",
    )
    parser.add_argument(
        "--max-chars",
        type=int,
        default=14000,
        help="Maximum allowed characters",
    )
    parser.add_argument(
        "--strict-missing",
        action="store_true",
        help="Fail if the vault note does not exist",
    )
    args = parser.parse_args()

    errors = validate_note_file(
        note_path=args.note_path,
        max_lines=args.max_lines,
        max_chars=args.max_chars,
        strict_missing=args.strict_missing,
    )

    if errors:
        print("Vault note check failed:")
        for error in errors:
            print(f"- {error}")
        print(
            "Fix the note to match AGENTS.md -> "
            "Vault Note Contract (Anti-Bloat), then re-run this check."
        )
        return 1

    print(f"Vault note check passed: {args.note_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
