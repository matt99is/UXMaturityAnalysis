"""Regression tests for supervised capture flow in main orchestrator."""

from __future__ import annotations

import importlib
import sys
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _import_main_with_stubs(browser_session_pool_cls):
    """Import main.py with lightweight stubs for optional runtime deps."""
    playwright_stub = MagicMock()
    playwright_stealth_stub = MagicMock()
    openai_stub = MagicMock()

    modules_to_stub = {
        "playwright": playwright_stub,
        "playwright.async_api": playwright_stub,
        "playwright_stealth": playwright_stealth_stub,
        "src.analyzers.screenshot_capture": MagicMock(),
        "src.browser_session": SimpleNamespace(BrowserSessionPool=browser_session_pool_cls),
        "src.utils.report_generator": MagicMock(),
        "src.utils.html_report_generator": MagicMock(),
        "openai": openai_stub,
    }

    sys.modules.pop("main", None)
    sys.modules.pop("src.analyzers.glm_analyzer", None)
    with patch.dict(sys.modules, modules_to_stub):
        return importlib.import_module("main")


class _MockSessionPool:
    """Simple stand-in to satisfy supervised init in orchestrator tests."""

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs


def test_supervised_preflight_requires_novnc_url():
    main = _import_main_with_stubs(_MockSessionPool)
    orchestrator = main.UXAnalysisOrchestrator(
        api_key="test",
        analysis_type="basket_pages",
        interactive_mode=True,
        novnc_url=None,
    )

    ok, reason = orchestrator._run_supervised_preflight()
    assert ok is False
    assert "noVNC URL is not configured" in reason


def test_supervised_preflight_rejects_invalid_novnc_url():
    main = _import_main_with_stubs(_MockSessionPool)
    orchestrator = main.UXAnalysisOrchestrator(
        api_key="test",
        analysis_type="basket_pages",
        interactive_mode=True,
        novnc_url="localhost:6080/vnc.html",
    )

    ok, reason = orchestrator._run_supervised_preflight()
    assert ok is False
    assert "Invalid noVNC URL" in reason


@pytest.mark.asyncio
async def test_analyze_competitors_routes_supervised_capture_branch():
    main = _import_main_with_stubs(_MockSessionPool)
    orchestrator = main.UXAnalysisOrchestrator(
        api_key="test",
        analysis_type="basket_pages",
        interactive_mode=True,
        novnc_url="http://localhost:6080/vnc.html",
    )

    orchestrator._run_supervised_preflight = MagicMock(return_value=(True, "ok"))
    orchestrator._capture_with_supervised_session = AsyncMock(
        return_value=[
            {
                "success": True,
                "filepath": "desktop.png",
                "filename": "desktop.png",
                "url": "https://example.com/basket",
                "viewport": {"width": 1920, "height": 1080},
                "viewport_name": "desktop",
                "interactive_mode": True,
            }
        ]
    )
    orchestrator.analyze_competitor_from_screenshots = AsyncMock(
        return_value={
            "success": True,
            "site_name": "example",
            "url": "https://example.com/basket",
            "overall_score": 7.5,
        }
    )

    competitors = [{"name": "example", "url": "https://example.com/basket"}]
    with patch("builtins.input", return_value=""):
        results = await orchestrator.analyze_competitors(competitors)

    assert len(results) == 1
    assert results[0]["success"] is True
    orchestrator._run_supervised_preflight.assert_called_once()
    orchestrator._capture_with_supervised_session.assert_awaited()
    assert not orchestrator.screenshot_capturer.initialize_browser.called
    assert not orchestrator.screenshot_capturer.close_browser.called
