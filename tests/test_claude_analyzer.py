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


def test_parse_json_response_plain_json(analyzer: ClaudeUXAnalyzer) -> None:
    data = {"key": "value"}
    result = analyzer._parse_json_response(json.dumps(data))
    assert result == data


def test_parse_json_response_fenced_json_block(analyzer: ClaudeUXAnalyzer) -> None:
    data = {"key": "value"}
    response = f"```json\n{json.dumps(data)}\n```"
    result = analyzer._parse_json_response(response)
    assert result == data


def test_parse_json_response_generic_fence(analyzer: ClaudeUXAnalyzer) -> None:
    data = {"key": "value"}
    response = f"```\n{json.dumps(data)}\n```"
    result = analyzer._parse_json_response(response)
    assert result == data


def test_parse_json_response_raises_on_invalid(analyzer: ClaudeUXAnalyzer) -> None:
    with pytest.raises(json.JSONDecodeError):
        analyzer._parse_json_response("not json at all")


@pytest.mark.asyncio
async def test_analyze_competitor_stores_relative_observation_file(tmp_path) -> None:
    """observation_file in result must be a plain filename, not an absolute path."""
    import json as _json
    import sys
    from pathlib import Path
    from unittest.mock import AsyncMock, MagicMock, patch
    from PIL import Image

    # Stub out playwright so main.py can be imported without the package installed
    playwright_stub = MagicMock()
    playwright_stealth_stub = MagicMock()
    modules_to_stub = {
        "playwright": playwright_stub,
        "playwright.async_api": playwright_stub,
        "playwright_stealth": playwright_stealth_stub,
        "src.analyzers.screenshot_capture": MagicMock(),
    }
    # Remove 'main' from sys.modules so the stubbed import is fresh
    sys.modules.pop("main", None)

    with patch.dict(sys.modules, modules_to_stub):
        from main import UXAnalysisOrchestrator

        # Create fake screenshots
        screenshots_dir = tmp_path / "amazon" / "screenshots"
        screenshots_dir.mkdir(parents=True)
        img = Image.new("RGB", (10, 10))
        desktop = screenshots_dir / "desktop.png"
        mobile = screenshots_dir / "mobile.png"
        img.save(desktop)
        img.save(mobile)

        # Fake observation response (pass 1)
        mock_obs = {
            "site_name": "amazon", "url": "https://amazon.com",
            "analysis_name": "Basket Page", "desktop": {}, "mobile": {},
            "notable_states": []
        }
        # Fake analysis response (pass 2)
        mock_analysis = {
            "site_name": "amazon", "url": "https://amazon.com",
            "analysis_type": "Basket Page", "overall_score": 7,
            "competitive_position": {"tier": "strong_contender", "positioning": "ok", "key_differentiator": "ok"},
            "criteria_scores": [], "strengths": [], "competitive_advantages": [],
            "weaknesses": [], "exploitable_vulnerabilities": [], "unmet_user_needs": [], "key_findings": []
        }

        call_count = 0
        async def mock_create(**kwargs):
            nonlocal call_count
            call_count += 1
            resp = MagicMock()
            resp.content = [MagicMock(text=_json.dumps(mock_obs if call_count == 1 else mock_analysis))]
            return resp

        orchestrator = UXAnalysisOrchestrator(api_key="test", analysis_type="basket_pages")
        competitor_paths = {
            'root': tmp_path / "amazon",
            'screenshots': screenshots_dir,
        }
        capture_data = {
            "site_name": "amazon",
            "url": "https://amazon.com",
            "screenshot_paths": [str(desktop), str(mobile)],
            "competitor_paths": competitor_paths,
        }

        with patch.object(orchestrator.claude_analyzer.client.messages, "create", new=mock_create):
            result = await orchestrator.analyze_competitor_from_screenshots(capture_data)

    assert result["success"] is True
    assert result["observation_file"] == "observation.json", (
        f"Expected 'observation.json', got {result['observation_file']!r}"
    )
    assert "competitor_root" in result
    assert Path(result["competitor_root"]) == tmp_path / "amazon"

    # Verify the on-disk file stores only the portable relative reference
    # (competitor_root must NOT be persisted — it is injected at read time)
    import json as _json_check
    written = _json_check.loads((tmp_path / "amazon" / "analysis.json").read_text())
    assert "competitor_root" not in written, (
        "competitor_root must not be persisted to analysis.json"
    )
    assert written["observation_file"] == "observation.json"
