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


def test_build_analysis_prompt_with_observation_cites_evidence(
    analyzer: ClaudeUXAnalyzer,
) -> None:
    """Prompt with observation must require evidence citation and notable state handling."""
    observation = {
        "notable_states": ["Annual subscription pre-selected by default"],
        "desktop": {"dark_patterns": "Annual plan radio button is pre-selected"},
        "mobile": {"dark_patterns": "Annual plan radio button is pre-selected"},
    }
    criteria = [
        {
            "id": "subscription_purchase_options",
            "name": "Subscription/Auto-Delivery Options",
            "weight": 1.2,
            "description": "Test",
            "evaluation_points": ["Check default selection"],
            "benchmarks": ["Baymard: pre-selected options increase abandonment"],
        }
    ]
    prompt = analyzer._build_analysis_prompt(
        criteria=criteria,
        analysis_name="Product Page",
        site_name="example.com",
        url="https://example.com",
        observation=observation,
    )
    assert "notable_states" in prompt
    assert "Annual subscription pre-selected by default" in prompt
    assert "evidence" in prompt.lower()
    assert "cite" in prompt.lower() or "quote" in prompt.lower()


def test_build_analysis_prompt_without_observation_unchanged(
    analyzer: ClaudeUXAnalyzer,
) -> None:
    """Without observation, prompt remains backward-compatible."""
    criteria = [
        {
            "id": "test",
            "name": "Test",
            "weight": 1.0,
            "description": "Test",
            "evaluation_points": [],
            "benchmarks": [],
        }
    ]
    prompt = analyzer._build_analysis_prompt(
        criteria=criteria,
        analysis_name="Product Page",
        site_name="example.com",
        url="https://example.com",
    )
    assert "example.com" in prompt
    assert "Product Page" in prompt


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
    assert result["observation"]["screenshots_analyzed"] == [str(screenshot)]
    assert result["observation"]["model_used"] == analyzer.model


@pytest.mark.asyncio
async def test_analyze_screenshots_with_observation_sends_no_images(
    analyzer: ClaudeUXAnalyzer,
) -> None:
    """When observation is provided, analyze_screenshots sends text-only content."""
    observation = {
        "notable_states": ["Test state"],
        "desktop": {},
        "mobile": {},
    }
    criteria = [
        {
            "id": "test",
            "name": "Test Criterion",
            "weight": 1.0,
            "description": "Test",
            "evaluation_points": [],
            "benchmarks": [],
        }
    ]
    mock_result = {
        "site_name": "example.com",
        "url": "https://example.com",
        "analysis_type": "Product Page",
        "overall_score": 7,
        "competitive_position": {
            "tier": "strong_contender",
            "positioning": "test",
            "key_differentiator": "test",
        },
        "criteria_scores": [
            {
                "criterion_id": "test",
                "criterion_name": "Test Criterion",
                "score": 7,
                "evidence": "test",
                "observations": "test",
                "comparison_to_benchmarks": "test",
                "competitive_status": "parity",
            }
        ],
        "strengths": [],
        "competitive_advantages": [],
        "weaknesses": [],
        "exploitable_vulnerabilities": [],
        "unmet_user_needs": [],
        "key_findings": [],
    }

    mock_response = MagicMock()
    mock_response.content = [MagicMock(text=json.dumps(mock_result))]

    captured_calls = []

    async def mock_create(**kwargs):
        captured_calls.append(kwargs)
        return mock_response

    with patch.object(analyzer.client.messages, "create", new=mock_create):
        result = await analyzer.analyze_screenshots(
            screenshot_paths=[],
            criteria=criteria,
            analysis_name="Product Page",
            site_name="example.com",
            url="https://example.com",
            observation=observation,
        )

    assert result["success"] is True
    call_content = captured_calls[0]["messages"][0]["content"]
    assert all(item["type"] == "text" for item in call_content)
    assert len(call_content) == 1
    assert "notable_states" in call_content[0]["text"]
