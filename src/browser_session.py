"""
Browser session management for supervised capture flows.

This module provides a small session layer that can run a headed browser on a
configured X display and expose a stable noVNC URL for human-in-the-loop work.
"""

from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional

from playwright.async_api import BrowserContext, Page, async_playwright


class DisplayAllocator:
    """Allocate and release X display numbers for concurrent sessions."""

    def __init__(self, base_display: int = 99, max_displays: int = 5):
        self.base_display = base_display
        self.max_displays = max_displays
        self._available: list[int] = list(range(base_display, base_display + max_displays))
        self._in_use: set[int] = set()

    def allocate(self) -> int:
        if not self._available:
            raise RuntimeError(f"No displays available. Max concurrent sessions: {self.max_displays}")
        display = self._available.pop(0)
        self._in_use.add(display)
        return display

    def release(self, display: int) -> None:
        if display in self._in_use:
            self._in_use.remove(display)
            self._available.append(display)
            self._available.sort()


@dataclass
class BrowserSessionConfig:
    """Runtime configuration for a supervised browser session."""

    display: int = 99
    profile_dir: Path = field(default_factory=lambda: Path("./browser_profiles/default"))
    page_timeout: int = 30000
    channel: Optional[str] = None
    novnc_url: Optional[str] = None


class BrowserSession:
    """Single persistent browser context for supervised capture."""

    def __init__(self, config: Optional[BrowserSessionConfig] = None):
        self.config = config or BrowserSessionConfig()
        self._playwright = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None

    def get_vnc_url(self) -> str:
        """Return noVNC URL for user guidance."""
        if self.config.novnc_url:
            return self.config.novnc_url
        host = os.getenv("NOVNC_HOST", "localhost")
        port = os.getenv("NOVNC_PORT", "6080")
        return f"http://{host}:{port}/vnc.html"

    async def start(self, url: str, viewport: Dict[str, int]) -> None:
        """Start browser context on configured display and navigate to URL."""
        self.config.profile_dir.mkdir(parents=True, exist_ok=True)

        self._playwright = await async_playwright().start()
        env = os.environ.copy()
        env["DISPLAY"] = f":{self.config.display}"

        launch_kwargs = {
            "user_data_dir": str(self.config.profile_dir),
            "headless": False,
            "no_viewport": True,
            "args": [
                "--window-size={width},{height}".format(**viewport),
                "--disable-blink-features=AutomationControlled",
            ],
            "env": env,
        }
        if self.config.channel:
            launch_kwargs["channel"] = self.config.channel

        self._context = await self._playwright.chromium.launch_persistent_context(**launch_kwargs)
        self._page = self._context.pages[0] if self._context.pages else await self._context.new_page()
        await self._page.set_viewport_size(viewport)
        await self._page.goto(url, timeout=self.config.page_timeout, wait_until="domcontentloaded")

    async def capture_screenshot(
        self,
        viewport: Dict[str, int],
        output_dir: Path,
        filename: str,
        full_page: bool = True,
    ) -> str:
        """Capture one screenshot from the current page."""
        if not self._page:
            raise RuntimeError("Session not started. Call start() first.")

        output_dir.mkdir(parents=True, exist_ok=True)
        await self._page.set_viewport_size(viewport)
        await asyncio.sleep(0.5)

        output_path = output_dir / filename
        await self._page.screenshot(path=str(output_path), full_page=full_page)
        return str(output_path)

    async def close(self) -> None:
        """Close browser resources for this session."""
        if self._context:
            await self._context.close()
            self._context = None
            self._page = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None


class BrowserSessionPool:
    """Manage multiple supervised browser sessions with display allocation."""

    def __init__(
        self,
        max_sessions: int = 1,
        base_display: int = 99,
        base_profile_dir: Path = Path("./browser_profiles"),
        novnc_url: Optional[str] = None,
        channel: Optional[str] = None,
    ):
        self.max_sessions = max_sessions
        self.base_profile_dir = base_profile_dir
        self.novnc_url = novnc_url
        self.channel = channel
        self._display_allocator = DisplayAllocator(
            base_display=base_display,
            max_displays=max_sessions,
        )
        self._sessions: Dict[str, BrowserSession] = {}

    async def acquire(self, session_id: str) -> BrowserSession:
        if session_id in self._sessions:
            return self._sessions[session_id]

        if len(self._sessions) >= self.max_sessions:
            raise RuntimeError(f"Session pool full. Max sessions: {self.max_sessions}")

        display = self._display_allocator.allocate()
        session = BrowserSession(
            BrowserSessionConfig(
                display=display,
                profile_dir=self.base_profile_dir / session_id,
                channel=self.channel,
                novnc_url=self.novnc_url,
            )
        )
        self._sessions[session_id] = session
        return session

    async def release(self, session_id: str) -> None:
        if session_id not in self._sessions:
            return

        session = self._sessions.pop(session_id)
        self._display_allocator.release(session.config.display)
        await session.close()
