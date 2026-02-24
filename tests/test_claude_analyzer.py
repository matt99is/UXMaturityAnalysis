"""Unit tests for ClaudeUXAnalyzer prompt builders."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

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


@pytest.mark.asyncio
async def test_observe_screenshots_returns_observation_on_success(
    analyzer: ClaudeUXAnalyzer,
    tmp_path,
) -> None:
    """_observe_screenshots calls Claude and returns parsed observation dict."""
    from PIL import Image

    img = Image.new("RGB", (100, 100), color=(255, 255, 255))
    screenshot = tmp_path / "desktop.png"
    img.save(screenshot)

    mock_observation = {
        "site_name": "example.com",
        "url": "https://example.com/product",
        "analysis_name": "Product Page",
        "desktop": {"dark_patterns": "None observed"},
        "mobile": {"dark_patterns": "None observed"},
        "notable_states": ["Annual subscription pre-selected by default"],
    }

    mock_response = MagicMock()
    mock_response.content = [MagicMock(text=json.dumps(mock_observation))]

    with patch.object(
        analyzer.client.messages,
        "create",
        new=AsyncMock(return_value=mock_response),
    ):
        result = await analyzer._observe_screenshots(
            screenshot_paths=[str(screenshot)],
            analysis_name="Product Page",
            observation_focus=["Subscription toggle state"],
            site_name="example.com",
            url="https://example.com/product",
        )

    assert result["success"] is True
    assert result["observation"]["notable_states"] == [
        "Annual subscription pre-selected by default"
    ]
