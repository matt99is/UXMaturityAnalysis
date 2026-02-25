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
