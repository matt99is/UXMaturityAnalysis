"""Tests for browser session management."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.browser_session import (
    BrowserSession,
    BrowserSessionConfig,
    BrowserSessionPool,
    DisplayAllocator,
)


class TestDisplayAllocator:
    def test_allocate_returns_base_display_first(self):
        allocator = DisplayAllocator(base_display=99, max_displays=2)
        assert allocator.allocate() == 99

    def test_allocate_returns_next_display(self):
        allocator = DisplayAllocator(base_display=99, max_displays=2)
        allocator.allocate()
        assert allocator.allocate() == 100

    def test_allocate_raises_when_exhausted(self):
        allocator = DisplayAllocator(base_display=99, max_displays=1)
        allocator.allocate()
        with pytest.raises(RuntimeError, match="No displays available"):
            allocator.allocate()

    def test_release_allows_reallocation(self):
        allocator = DisplayAllocator(base_display=99, max_displays=2)
        first = allocator.allocate()
        allocator.allocate()
        allocator.release(first)
        assert allocator.allocate() == 99

    def test_release_idempotent(self):
        allocator = DisplayAllocator(base_display=99, max_displays=1)
        d = allocator.allocate()
        allocator.release(d)
        allocator.release(d)


class TestBrowserSession:
    @pytest.fixture
    def session(self, tmp_path):
        config = BrowserSessionConfig(
            display=99,
            profile_dir=tmp_path / "profile",
            novnc_url="http://127.0.0.1:6080/vnc.html",
        )
        return BrowserSession(config)

    def test_get_vnc_url_prefers_config(self, session):
        assert session.get_vnc_url() == "http://127.0.0.1:6080/vnc.html"

    @pytest.mark.asyncio
    async def test_start_creates_context_and_navigates(self, session):
        mock_page = AsyncMock()
        mock_context = AsyncMock()
        mock_context.pages = []
        mock_context.new_page = AsyncMock(return_value=mock_page)

        mock_pw_driver = AsyncMock()
        mock_pw_driver.chromium.launch_persistent_context = AsyncMock(return_value=mock_context)

        mock_pw_factory = MagicMock()
        mock_pw_factory.start = AsyncMock(return_value=mock_pw_driver)

        with patch("src.browser_session.async_playwright", return_value=mock_pw_factory):
            await session.start("https://example.com", {"width": 1920, "height": 1080})

        assert session._context is not None
        assert session._page is not None
        mock_page.goto.assert_called_once()

    @pytest.mark.asyncio
    async def test_capture_screenshot_returns_path(self, session, tmp_path):
        session._page = AsyncMock()
        output_dir = tmp_path / "screens"
        result = await session.capture_screenshot(
            viewport={"width": 1920, "height": 1080},
            output_dir=output_dir,
            filename="desktop.png",
        )
        assert result.endswith("desktop.png")
        session._page.screenshot.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_cleans_resources(self, session):
        mock_context = AsyncMock()
        mock_playwright = AsyncMock()
        session._context = mock_context
        session._playwright = mock_playwright
        await session.close()
        mock_context.close.assert_called_once()
        mock_playwright.stop.assert_called_once()


class TestBrowserSessionPool:
    @pytest.mark.asyncio
    async def test_acquire_returns_existing_session(self, tmp_path):
        pool = BrowserSessionPool(max_sessions=2, base_profile_dir=tmp_path)
        first = await pool.acquire("one")
        second = await pool.acquire("one")
        assert first is second

    @pytest.mark.asyncio
    async def test_acquire_raises_when_full(self, tmp_path):
        pool = BrowserSessionPool(max_sessions=1, base_profile_dir=tmp_path)
        await pool.acquire("one")
        with pytest.raises(RuntimeError, match="Session pool full"):
            await pool.acquire("two")

    @pytest.mark.asyncio
    async def test_release_is_idempotent(self, tmp_path):
        pool = BrowserSessionPool(max_sessions=1, base_profile_dir=tmp_path)
        await pool.acquire("one")
        with patch.object(BrowserSession, "close", new=AsyncMock()) as mock_close:
            await pool.release("one")
            await pool.release("one")
        mock_close.assert_called_once()
