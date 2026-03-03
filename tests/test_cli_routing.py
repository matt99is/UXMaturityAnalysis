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
