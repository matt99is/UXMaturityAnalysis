"""Tests for vault note validator."""

from scripts.check_vault import validate_note_text


def _valid_note() -> str:
    return """# UX Maturity Analysis

## What it is
AI workflow that captures and scores ecommerce UX against configured criteria.

## Current status
- Unified CLI is the single entrypoint.
- Supervised capture is available for smoke runs.
- Automated capture remains gated in CLI.

## Active decisions
- Keep smoke set at one competitor for preflight checks.
- Keep the vault note as startup context only.

## Known gotchas
- Always run pytest with PYTHONPATH=.
- Use ./run.sh for normal runs.

## Next steps
- Complete canary validation on the 3-competitor set.

## References
- AGENTS.md
- PROJECT_STATE.md
- docs/ROADMAP.md
"""


def test_valid_note_passes():
    errors = validate_note_text(_valid_note())
    assert errors == []


def test_missing_required_section_fails():
    active_decisions_block = (
        "## Active decisions\n"
        "- Keep smoke set at one competitor for preflight checks.\n"
        "- Keep the vault note as startup context only.\n\n"
    )
    note = _valid_note().replace(active_decisions_block, "")
    errors = validate_note_text(note)
    assert any(
        "Missing required section: '## Active decisions'." in error
        for error in errors
    )


def test_changelog_style_current_status_fails():
    note = _valid_note().replace(
        "- Unified CLI is the single entrypoint.",
        "- 2026-03-04: Unified CLI shipped in v1.14.0 (commit 85baa40).",
    )
    errors = validate_note_text(note)
    assert any(
        "Changelog-style bullet detected in '## Current status'" in error
        for error in errors
    )


def test_line_limit_fails():
    note = _valid_note() + ("\nplaceholder line" * 50)
    errors = validate_note_text(note, max_lines=25, max_chars=99999)
    assert any("Line limit exceeded" in error for error in errors)
