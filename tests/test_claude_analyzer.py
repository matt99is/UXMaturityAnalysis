"""Unit tests for ClaudeUXAnalyzer prompt builders."""

import pytest

from src.analyzers.claude_analyzer import ClaudeUXAnalyzer


@pytest.fixture
def analyzer() -> ClaudeUXAnalyzer:
    return ClaudeUXAnalyzer(api_key="test-key")


def test_build_observation_prompt_includes_universal_sections(analyzer: ClaudeUXAnalyzer) -> None:
    prompt = analyzer._build_observation_prompt(
        analysis_name="Product Page UX Maturity Analysis",
        observation_focus=[],
        site_name="example.com",
        url="https://example.com/product",
    )
    assert "PRICING & OFFERS" in prompt
    assert "INTERACTIVE STATES" in prompt
    assert "DARK PATTERNS" in prompt
    assert "notable_states" in prompt
    assert "do not evaluate" in prompt.lower() or "do not score" in prompt.lower()


def test_build_observation_prompt_includes_page_specific_focus(analyzer: ClaudeUXAnalyzer) -> None:
    focus = ["Subscription vs one-time purchase toggle - which is pre-selected"]
    prompt = analyzer._build_observation_prompt(
        analysis_name="Product Page",
        observation_focus=focus,
        site_name="example.com",
        url="https://example.com/product",
    )
    assert "Subscription vs one-time purchase toggle" in prompt


def test_build_observation_prompt_excludes_scoring_language(analyzer: ClaudeUXAnalyzer) -> None:
    prompt = analyzer._build_observation_prompt(
        analysis_name="Product Page",
        observation_focus=[],
        site_name="example.com",
        url="https://example.com/product",
    )
    assert "score" not in prompt.lower()
    assert "criterion" not in prompt.lower()
