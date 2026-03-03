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
