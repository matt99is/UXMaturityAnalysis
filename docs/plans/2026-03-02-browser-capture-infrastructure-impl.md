# Browser Capture Infrastructure Implementation Plan

> **Alignment Note (2026-03-04):** This plan now reflects the unified CLI flow:
> `./run.sh` -> `cli.py` (menus/automation routing) -> `main.py` (orchestration and capture execution).

**Goal:** Build unified browser capture infrastructure supporting both interactive (human-in-the-loop via VNC) and automated (unattended with bot evasion) screenshot capture on headless Ubuntu server.

**Architecture:** Xvfb provides virtual display, x11vnc exposes it via VNC, websockify bridges to WebSocket, noVNC provides HTML5 client. Patchright replaces Playwright for stealth automation. Session pool manages browser lifecycles.

**Tech Stack:** Python 3.9+, Patchright, Xvfb, x11vnc, websockify, noVNC, systemd

---

## Phase 1: Infrastructure Setup

### Task 1.1: Install System Packages

**Files:** None (system-level)

**Step 1: Update apt and install packages**

```bash
sudo apt-get update
sudo apt-get install -y \
    xvfb x11vnc websockify novnc \
    libgbm1 libnss3 libatk-bridge2.0-0 libdrm2 \
    fonts-liberation fonts-dejavu fonts-noto
```

**Step 2: Verify installations**

```bash
which xvfb-run x11vnc websockify
# Expected: /usr/bin/xvfb-run, /usr/bin/x11vnc, /usr/bin/websockify

ls /usr/share/novnc/vnc.html
# Expected: file exists
```

**Step 3: Create browser profiles directory**

```bash
cd /home/matt99is/projects/UXMaturityAnalysis
mkdir -p browser_profiles/desktop browser_profiles/mobile
```

---

### Task 1.2: Install Patchright

**Files:**
- Modify: `requirements.txt`

**Step 1: Update requirements.txt**

Add to `requirements.txt`:
```
patchright>=0.1.0
```

Remove from `requirements.txt` (if present):
```
playwright-stealth
```

**Step 2: Install Python dependencies**

```bash
cd /home/matt99is/projects/UXMaturityAnalysis
pip install patchright
```

**Step 3: Install Google Chrome via Patchright**

```bash
patchright install chrome
```

**Step 4: Verify Chrome installation**

```bash
ls ~/.cache/patchright/chrome/
# Expected: Chrome executable present
```

---

### Task 1.3: Create Xvfb Systemd Service

**Files:**
- Create: `/etc/systemd/system/xvfb.service`

**Step 1: Create service file**

```bash
sudo tee /etc/systemd/system/xvfb.service << 'EOF'
[Unit]
Description=X Virtual Framebuffer
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/Xvfb :99 -screen 0 1920x1080x24 -ac +extension GLX
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
```

**Step 2: Enable and start service**

```bash
sudo systemctl daemon-reload
sudo systemctl enable xvfb
sudo systemctl start xvfb
```

**Step 3: Verify Xvfb is running**

```bash
sudo systemctl status xvfb
# Expected: active (running)

DISPLAY=:99 xdpyinfo | head -5
# Expected: Display info showing 1920x1080
```

---

### Task 1.4: Create x11vnc Systemd Service

**Files:**
- Create: `/etc/systemd/system/x11vnc.service`

**Step 1: Create service file**

```bash
sudo tee /etc/systemd/system/x11vnc.service << 'EOF'
[Unit]
Description=VNC Server for Xvfb
After=xvfb.service
Requires=xvfb.service

[Service]
Type=simple
Environment=DISPLAY=:99
ExecStart=/usr/bin/x11vnc -display :99 -forever -shared -rfbport 5900 -nopw
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
```

**Step 2: Enable and start service**

```bash
sudo systemctl daemon-reload
sudo systemctl enable x11vnc
sudo systemctl start x11vnc
```

**Step 3: Verify x11vnc is running**

```bash
sudo systemctl status x11vnc
# Expected: active (running)

ss -tlnp | grep 5900
# Expected: LISTEN on port 5900
```

---

### Task 1.5: Create VNC Bridge Systemd Service

**Files:**
- Create: `/etc/systemd/system/vnc-bridge.service`

**Step 1: Create service file**

```bash
sudo tee /etc/systemd/system/vnc-bridge.service << 'EOF'
[Unit]
Description=VNC to WebSocket Bridge
After=xvfb.service x11vnc.service network.target
Requires=x11vnc.service

[Service]
Type=simple
ExecStart=/usr/bin/websockify --web /usr/share/novnc 6080 localhost:5900
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
```

**Step 2: Enable and start service**

```bash
sudo systemctl daemon-reload
sudo systemctl enable vnc-bridge
sudo systemctl start vnc-bridge
```

**Step 3: Verify websockify is running**

```bash
sudo systemctl status vnc-bridge
# Expected: active (running)

ss -tlnp | grep 6080
# Expected: LISTEN on port 6080
```

---

### Task 1.6: Verify Infrastructure End-to-End

**Files:** None

**Step 1: Test noVNC is accessible**

```bash
curl -s http://localhost:6080/vnc.html | head -10
# Expected: HTML content with noVNC title
```

**Step 2: Test Patchright with Xvfb**

```bash
cd /home/matt99is/projects/UXMaturityAnalysis
DISPLAY=:99 python3 -c "
from patchright.sync_api import sync_playwright

with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(
        './browser_profiles/desktop',
        channel='chrome',
        headless=False
    )
    page = ctx.new_page()
    page.goto('https://example.com', timeout=30000)
    page.screenshot(path='/tmp/test_patchright.png')
    ctx.close()
    print('SUCCESS: Screenshot saved to /tmp/test_patchright.png')
"
```

**Step 3: View screenshot via VNC (optional manual check)**

```bash
# On your local machine, open browser to:
# http://<server-ip>:6080/vnc.html
# You should see the Xvfb desktop
```

---

## Phase 2: Browser Session Module

### Task 2.1: Write DisplayAllocator Tests

**Files:**
- Create: `tests/test_browser_session.py`

**Step 1: Create test file with DisplayAllocator tests**

```python
# tests/test_browser_session.py
"""Tests for browser session management."""

import pytest
from src.browser_session import DisplayAllocator


class TestDisplayAllocator:
    """Tests for Xvfb display number allocation."""

    def test_allocate_returns_int(self):
        """Allocator returns integer display number."""
        allocator = DisplayAllocator(base_display=99, max_displays=5)
        display = allocator.allocate()
        assert isinstance(display, int)

    def test_allocate_returns_base_display_first(self):
        """First allocation returns base display number."""
        allocator = DisplayAllocator(base_display=99, max_displays=5)
        display = allocator.allocate()
        assert display == 99

    def test_allocate_returns_next_display(self):
        """Subsequent allocations return incrementing display numbers."""
        allocator = DisplayAllocator(base_display=99, max_displays=5)
        first = allocator.allocate()
        second = allocator.allocate()
        assert first == 99
        assert second == 100

    def test_allocate_raises_when_exhausted(self):
        """Allocator raises error when all displays are in use."""
        allocator = DisplayAllocator(base_display=99, max_displays=2)
        allocator.allocate()  # 99
        allocator.allocate()  # 100
        with pytest.raises(RuntimeError, match="No displays available"):
            allocator.allocate()

    def test_release_allows_reallocation(self):
        """Released display can be allocated again."""
        allocator = DisplayAllocator(base_display=99, max_displays=2)
        first = allocator.allocate()  # 99
        second = allocator.allocate()  # 100
        allocator.release(first)
        third = allocator.allocate()  # Should be 99 again
        assert third == 99

    def test_release_idempotent(self):
        """Releasing same display twice is safe."""
        allocator = DisplayAllocator(base_display=99, max_displays=2)
        display = allocator.allocate()
        allocator.release(display)
        allocator.release(display)  # Should not raise
        assert True
```

**Step 2: Run tests to verify they fail**

```bash
cd /home/matt99is/projects/UXMaturityAnalysis
pytest tests/test_browser_session.py::TestDisplayAllocator -v
# Expected: FAIL - module not found
```

---

### Task 2.2: Implement DisplayAllocator

**Files:**
- Create: `src/browser_session.py`

**Step 1: Create browser_session.py with DisplayAllocator**

```python
# src/browser_session.py
"""
Browser session management for headless capture with VNC streaming.

Provides:
- DisplayAllocator: Manages Xvfb display numbers
- BrowserSession: Single browser session with VNC access
- BrowserSessionPool: Manages multiple concurrent sessions
"""

import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field


class DisplayAllocator:
    """
    Manages Xvfb display numbers for concurrent browser sessions.

    Each browser session needs its own X11 display to avoid conflicts.
    This class allocates display numbers from a pool and tracks usage.

    Example:
        allocator = DisplayAllocator(base_display=99, max_displays=5)
        display = allocator.allocate()  # Returns 99
        allocator.release(display)      # Returns 99 to pool
    """

    def __init__(self, base_display: int = 99, max_displays: int = 5):
        """
        Initialize display allocator.

        Args:
            base_display: Starting display number (e.g., 99 for :99)
            max_displays: Maximum number of concurrent displays
        """
        self.base_display = base_display
        self.max_displays = max_displays
        self._available: List[int] = list(range(base_display, base_display + max_displays))
        self._in_use: set[int] = set()

    def allocate(self) -> int:
        """
        Allocate an available display number.

        Returns:
            Display number (e.g., 99 for display :99)

        Raises:
            RuntimeError: If no displays are available
        """
        if not self._available:
            raise RuntimeError(
                f"No displays available. Max concurrent sessions: {self.max_displays}"
            )
        display = self._available.pop(0)
        self._in_use.add(display)
        return display

    def release(self, display: int) -> None:
        """
        Release a display back to the pool.

        Args:
            display: Display number to release

        Note:
            Safe to call multiple times for same display (idempotent).
        """
        if display in self._in_use:
            self._in_use.remove(display)
            self._available.append(display)
```

**Step 2: Run tests to verify they pass**

```bash
pytest tests/test_browser_session.py::TestDisplayAllocator -v
# Expected: 6 passed
```

**Step 3: Commit**

```bash
git add src/browser_session.py tests/test_browser_session.py
git commit -m "feat: add DisplayAllocator for Xvfb display management"
```

---

### Task 2.3: Write BrowserSession Tests

**Files:**
- Modify: `tests/test_browser_session.py`

**Step 1: Add BrowserSession tests**

```python
# Add to tests/test_browser_session.py

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.browser_session import BrowserSession, BrowserSessionConfig


class TestBrowserSession:
    """Tests for BrowserSession class."""

    @pytest.fixture
    def config(self):
        """Default session configuration."""
        return BrowserSessionConfig(
            display=99,
            profile_dir=Path("/tmp/test_profile"),
            vnc_port=6080,
        )

    @pytest.fixture
    def session(self, config):
        """Create session instance."""
        return BrowserSession(config)

    def test_config_defaults(self):
        """Config has sensible defaults."""
        config = BrowserSessionConfig()
        assert config.display == 99
        assert config.vnc_port == 6080
        assert config.page_timeout == 30000

    def test_get_vnc_url(self, session):
        """VNC URL is correctly formatted."""
        url = session.get_vnc_url()
        assert "6080" in url
        assert "vnc.html" in url

    @pytest.mark.asyncio
    async def test_start_creates_browser_context(self, session):
        """Starting session creates Playwright context."""
        with patch('src.browser_session.async_playwright') as mock_pw:
            mock_browser = AsyncMock()
            mock_pw.return_value.__aenter__.return_value.chromium.launch_persistent_context = AsyncMock(
                return_value=mock_browser
            )

            await session.start("https://example.com", {"width": 1920, "height": 1080})

            assert session._context is not None

    @pytest.mark.asyncio
    async def test_capture_screenshot_returns_path(self, session, tmp_path):
        """Capture returns screenshot file path."""
        session._page = AsyncMock()
        session._page.screenshot = AsyncMock(return_value=None)

        output_dir = tmp_path / "screenshots"
        output_dir.mkdir()

        result = await session.capture_screenshot(
            viewport={"width": 1920, "height": 1080},
            output_dir=output_dir,
            filename="desktop.png"
        )

        assert result.endswith("desktop.png")

    @pytest.mark.asyncio
    async def test_close_cleanup(self, session):
        """Close cleans up browser resources."""
        session._context = AsyncMock()
        session._context.close = AsyncMock()

        await session.close()

        session._context.close.assert_called_once()
```

**Step 2: Run tests to verify they fail**

```bash
pytest tests/test_browser_session.py::TestBrowserSession -v
# Expected: FAIL - BrowserSession not implemented
```

---

### Task 2.4: Implement BrowserSession

**Files:**
- Modify: `src/browser_session.py`

**Step 1: Add imports and config dataclass**

```python
# Add to top of src/browser_session.py

import asyncio
import socket
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field

from patchright.async_api import async_playwright, BrowserContext, Page
```

**Step 2: Add BrowserSessionConfig dataclass**

```python
# Add after DisplayAllocator class

@dataclass
class BrowserSessionConfig:
    """Configuration for a browser session."""

    display: int = 99
    profile_dir: Path = field(default_factory=lambda: Path("./browser_profiles/default"))
    vnc_port: int = 6080
    page_timeout: int = 30000  # milliseconds
    channel: str = "chrome"
    viewport: Dict[str, int] = field(default_factory=lambda: {"width": 1920, "height": 1080})
```

**Step 3: Add BrowserSession class**

```python
# Add after BrowserSessionConfig

class BrowserSession:
    """
    Single browser session with VNC streaming capability.

    Manages a persistent browser context that can be viewed and interacted
    with via noVNC. Used for human-in-the-loop capture flows.

    Example:
        session = BrowserSession(config)
        await session.start("https://example.com", viewport)
        print(f"View at: {session.get_vnc_url()}")
        input("Press Enter when ready...")
        path = await session.capture_screenshot(viewport, output_dir)
        await session.close()
    """

    def __init__(self, config: Optional[BrowserSessionConfig] = None):
        """Initialize session with configuration."""
        self.config = config or BrowserSessionConfig()
        self._playwright = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        self._last_url: Optional[str] = None

    def get_vnc_url(self) -> str:
        """
        Get noVNC URL for this session.

        Returns:
            Full URL to noVNC HTML client
        """
        hostname = socket.gethostname()
        return f"http://{hostname}:{self.config.vnc_port}/vnc.html"

    async def start(self, url: str, viewport: Dict[str, int]) -> None:
        """
        Start browser session and navigate to URL.

        Args:
            url: URL to navigate to
            viewport: Viewport dimensions {"width": N, "height": N}
        """
        self._last_url = url

        # Ensure profile directory exists
        self.config.profile_dir.mkdir(parents=True, exist_ok=True)

        # Start Playwright with Patchright
        self._playwright = await async_playwright().start()

        # Launch persistent context (keeps cookies, cache, history)
        self._context = await self._playwright.chromium.launch_persistent_context(
            user_data_dir=str(self.config.profile_dir),
            channel=self.config.channel,
            headless=False,  # Must be False to appear on Xvfb display
            no_viewport=True,  # We'll set viewport manually
            args=[
                "--window-size={width},{height}".format(**viewport),
                "--disable-blink-features=AutomationControlled",
            ]
        )

        # Create page and navigate
        self._page = await self._context.new_page()
        await self._page.set_viewport_size(viewport)
        await self._page.goto(url, timeout=self.config.page_timeout, wait_until="domcontentloaded")

    async def set_viewport(self, viewport: Dict[str, int]) -> None:
        """
        Change browser viewport size.

        Args:
            viewport: New viewport dimensions
        """
        if self._page:
            await self._page.set_viewport_size(viewport)

    async def capture_screenshot(
        self,
        viewport: Dict[str, int],
        output_dir: Path,
        filename: str = "desktop.png",
        full_page: bool = True
    ) -> str:
        """
        Capture screenshot at specified viewport.

        Args:
            viewport: Viewport dimensions for this capture
            output_dir: Directory to save screenshot
            filename: Output filename
            full_page: Whether to capture full page or viewport

        Returns:
            Path to saved screenshot
        """
        if not self._page:
            raise RuntimeError("Session not started. Call start() first.")

        # Set viewport
        await self._page.set_viewport_size(viewport)

        # Wait for page to adjust
        await asyncio.sleep(0.5)

        # Capture screenshot
        output_path = output_dir / filename
        await self._page.screenshot(path=str(output_path), full_page=full_page)

        return str(output_path)

    async def close(self) -> None:
        """Close browser session and cleanup resources."""
        if self._context:
            await self._context.close()
            self._context = None
            self._page = None

        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
```

**Step 4: Run tests to verify they pass**

```bash
pytest tests/test_browser_session.py::TestBrowserSession -v
# Expected: All tests pass
```

**Step 5: Commit**

```bash
git add src/browser_session.py tests/test_browser_session.py
git commit -m "feat: add BrowserSession for VNC-accessible browser control"
```

---

### Task 2.5: Write BrowserSessionPool Tests

**Files:**
- Modify: `tests/test_browser_session.py`

**Step 1: Add BrowserSessionPool tests**

```python
# Add to tests/test_browser_session.py

from src.browser_session import BrowserSessionPool


class TestBrowserSessionPool:
    """Tests for BrowserSessionPool class."""

    @pytest.fixture
    def pool(self):
        """Create pool with test configuration."""
        return BrowserSessionPool(max_sessions=2, base_display=99)

    def test_pool_initialization(self, pool):
        """Pool initializes with correct settings."""
        assert pool.max_sessions == 2
        assert len(pool._sessions) == 0

    @pytest.mark.asyncio
    async def test_acquire_creates_session(self, pool):
        """Acquiring creates a new session."""
        session = await pool.acquire("test_session")

        assert session is not None
        assert "test_session" in pool._sessions

    @pytest.mark.asyncio
    async def test_acquire_same_session_returns_existing(self, pool):
        """Acquiring same session ID returns existing session."""
        session1 = await pool.acquire("test_session")
        session2 = await pool.acquire("test_session")

        assert session1 is session2

    @pytest.mark.asyncio
    async def test_acquire_raises_when_full(self, pool):
        """Acquiring raises error when pool is full."""
        await pool.acquire("session1")
        await pool.acquire("session2")

        with pytest.raises(RuntimeError, match="Session pool full"):
            await pool.acquire("session3")

    @pytest.mark.asyncio
    async def test_release_closes_session(self, pool):
        """Releasing closes and removes session."""
        await pool.acquire("test_session")
        await pool.release("test_session")

        assert "test_session" not in pool._sessions

    @pytest.mark.asyncio
    async def test_release_nonexistent_is_safe(self, pool):
        """Releasing non-existent session is safe."""
        await pool.release("nonexistent")  # Should not raise
        assert True
```

**Step 2: Run tests to verify they fail**

```bash
pytest tests/test_browser_session.py::TestBrowserSessionPool -v
# Expected: FAIL - BrowserSessionPool not implemented
```

---

### Task 2.6: Implement BrowserSessionPool

**Files:**
- Modify: `src/browser_session.py`

**Step 1: Add BrowserSessionPool class**

```python
# Add to end of src/browser_session.py

class BrowserSessionPool:
    """
    Manages multiple concurrent browser sessions.

    Provides session lifecycle management with display allocation.
    Each session gets its own display number and browser profile.

    Example:
        pool = BrowserSessionPool(max_sessions=5)
        session = await pool.acquire("tesco")
        # ... use session ...
        await pool.release("tesco")
    """

    def __init__(
        self,
        max_sessions: int = 5,
        base_display: int = 99,
        base_profile_dir: Path = Path("./browser_profiles")
    ):
        """
        Initialize session pool.

        Args:
            max_sessions: Maximum concurrent sessions
            base_display: Starting display number (e.g., 99 for :99)
            base_profile_dir: Parent directory for browser profiles
        """
        self.max_sessions = max_sessions
        self.base_profile_dir = base_profile_dir
        self._display_allocator = DisplayAllocator(
            base_display=base_display,
            max_displays=max_sessions
        )
        self._sessions: Dict[str, BrowserSession] = {}

    async def acquire(self, session_id: str) -> BrowserSession:
        """
        Acquire or create a browser session.

        Args:
            session_id: Unique identifier for this session

        Returns:
            BrowserSession instance

        Raises:
            RuntimeError: If pool is at capacity
        """
        # Return existing session if available
        if session_id in self._sessions:
            return self._sessions[session_id]

        # Check capacity
        if len(self._sessions) >= self.max_sessions:
            raise RuntimeError(
                f"Session pool full. Max sessions: {self.max_sessions}"
            )

        # Allocate display
        display = self._display_allocator.allocate()

        # Create session config
        profile_dir = self.base_profile_dir / session_id
        config = BrowserSessionConfig(
            display=display,
            profile_dir=profile_dir,
        )

        # Create and store session
        session = BrowserSession(config)
        self._sessions[session_id] = session

        return session

    async def release(self, session_id: str) -> None:
        """
        Release and close a browser session.

        Args:
            session_id: Session to release

        Note:
            Safe to call for non-existent sessions (idempotent).
        """
        if session_id not in self._sessions:
            return

        session = self._sessions.pop(session_id)

        # Release display back to pool
        self._display_allocator.release(session.config.display)

        # Close browser
        await session.close()
```

**Step 2: Run tests to verify they pass**

```bash
pytest tests/test_browser_session.py::TestBrowserSessionPool -v
# Expected: All tests pass
```

**Step 3: Commit**

```bash
git add src/browser_session.py tests/test_browser_session.py
git commit -m "feat: add BrowserSessionPool for concurrent session management"
```

---

## Phase 3: Screenshot Capture Migration

### Task 3.1: Update ScreenshotCapture Imports

**Files:**
- Modify: `src/analyzers/screenshot_capture.py`

**Step 1: Replace Playwright with Patchright**

Find:
```python
from playwright.async_api import Browser, Page, async_playwright
from playwright_stealth import Stealth
```

Replace with:
```python
from patchright.async_api import Browser, Page, async_playwright
# playwright_stealth removed - Patchright handles stealth internally
```

**Step 2: Remove stealth_mode flag and related code**

Find and remove:
```python
self.stealth_mode = True  # Enable by default
```

And in `capture_url` method, remove:
```python
# Apply stealth mode to hide automation
if self.stealth_mode:
    try:
        # Use basic anti-detection scripts
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            ...
        """)
    except Exception as e:
        # If stealth mode fails, continue anyway
        pass
```

**Step 3: Update initialize_browser for persistent context**

Find `initialize_browser` method and replace with:

```python
async def initialize_browser(
    self,
    headless: bool = True,
    profile_dir: Path = None,
    channel: str = "chrome"
):
    """
    Initialize Patchright browser with stealth settings.

    Args:
        headless: Whether to run headless (ignored on Xvfb - always "headed")
        profile_dir: Directory for persistent browser profile
        channel: Browser channel ("chrome" recommended)
    """
    self.playwright = await async_playwright().start()

    # Default profile directory
    if profile_dir is None:
        profile_dir = Path("./browser_profiles/default")

    profile_dir.mkdir(parents=True, exist_ok=True)

    # Launch args for stealth
    launch_args = [
        "--disable-blink-features=AutomationControlled",
    ]

    # For Xvfb, we use headed mode but on virtual display
    # Patchright handles CDP patching automatically
    self.browser = await self.playwright.chromium.launch(
        headless=headless,
        channel=channel,
        args=launch_args
    )
```

**Step 4: Commit**

```bash
git add src/analyzers/screenshot_capture.py
git commit -m "refactor: migrate from Playwright to Patchright for stealth"
```

---

### Task 3.2: Add Persistent Context Support

**Files:**
- Modify: `src/analyzers/screenshot_capture.py`

**Step 1: Add method for persistent context capture**

Add new method to ScreenshotCapture class:

```python
async def capture_with_persistent_context(
    self,
    url: str,
    site_name: str,
    viewports: List[Dict[str, int]],
    profile_dir: Path,
    full_page: bool = True,
    custom_output_dir: Path = None,
    channel: str = "chrome",
) -> List[Dict[str, any]]:
    """
    Capture screenshots using persistent browser context.

    Uses Patchright with persistent profile for better bot evasion.
    Profile maintains cookies, cache, and browsing history across sessions.

    Args:
        url: URL to capture
        site_name: Identifier for the site
        viewports: List of viewport configs
        profile_dir: Directory for persistent profile
        full_page: Whether to capture full page
        custom_output_dir: Output directory for screenshots
        channel: Browser channel ("chrome" recommended)

    Returns:
        List of capture results
    """
    from patchright.async_api import async_playwright

    results = []
    profile_dir.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=str(profile_dir),
            channel=channel,
            headless=False,  # Headed on Xvfb
            no_viewport=True,
            args=["--disable-blink-features=AutomationControlled"]
        )

        try:
            page = await context.new_page()

            # Navigate
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(3)  # Let page settle

            # Check for blocks
            block_check = await self._check_if_blocked(page)
            if block_check["blocked"]:
                return [{
                    "success": False,
                    "error": f"Bot detection: {block_check['reason']}",
                    "blocked": True,
                    "url": url,
                }]

            # Scroll to trigger lazy content
            await self._human_like_scroll(page)

            # Capture each viewport
            for viewport in viewports:
                await page.set_viewport_size({
                    "width": viewport["width"],
                    "height": viewport["height"]
                })
                await asyncio.sleep(0.5)

                filename = f"{viewport['name']}.png"
                filepath = custom_output_dir / filename if custom_output_dir else self.output_dir / filename

                await page.screenshot(path=str(filepath), full_page=full_page)

                results.append({
                    "success": True,
                    "filepath": str(filepath),
                    "filename": filename,
                    "url": url,
                    "viewport_name": viewport["name"],
                    "viewport": viewport,
                })

        except Exception as e:
            results.append({
                "success": False,
                "error": str(e),
                "url": url,
            })

        finally:
            await context.close()

    return results
```

**Step 2: Commit**

```bash
git add src/analyzers/screenshot_capture.py
git commit -m "feat: add persistent context capture method to ScreenshotCapture"
```

---

## Phase 4: CLI + Orchestrator Integration

### Task 4.1: Add CLI Arguments

**Files:**
- Modify: `main.py`

**Step 1: Add new arguments to argparse**

Find the argument parser section and add:

```python
# Capture mode arguments
capture_group = parser.add_mutually_exclusive_group()
capture_group.add_argument(
    "--interactive",
    action="store_true",
    help="Interactive mode: open browser with VNC access for human-in-the-loop capture"
)
capture_group.add_argument(
    "--auto",
    action="store_true",
    help="Automated mode: run unattended with delays between captures"
)
```

**Step 2: Commit**

```bash
git add main.py
git commit -m "feat: add --interactive and --auto CLI arguments"
```

---

### Task 4.2: Update UXAnalysisOrchestrator Init

**Files:**
- Modify: `main.py`

**Step 1: Add mode flags to __init__**

Find `UXAnalysisOrchestrator.__init__` and add parameters:

```python
def __init__(
    self,
    api_key: str,
    model: str = None,
    analysis_type: str = "basket_pages",
    config_path: str = "config.yaml",
    manual_mode: bool = False,
    screenshots_dir: str = None,
    llm_provider: str = None,
    interactive_mode: bool = False,  # NEW
    auto_mode: bool = False,         # NEW
):
    # ... existing init code ...

    self.interactive_mode = interactive_mode
    self.auto_mode = auto_mode

    # Initialize session pool for interactive mode
    if interactive_mode:
        from src.browser_session import BrowserSessionPool
        self.session_pool = BrowserSessionPool(max_sessions=1)
    else:
        self.session_pool = None
```

**Step 2: Commit**

```bash
git add main.py
git commit -m "feat: add interactive/auto mode flags to orchestrator"
```

---

### Task 4.3: Implement Interactive Capture Flow

**Files:**
- Modify: `main.py`

**Step 1: Add interactive capture method to orchestrator**

```python
async def _interactive_capture(
    self,
    url: str,
    site_name: str,
    viewports: List[Dict[str, int]],
    screenshots_dir: Path
) -> Dict[str, Any]:
    """
    Capture screenshots with human-in-the-loop via VNC.

    Opens browser, prints VNC URL, waits for user, then captures.
    """
    from src.browser_session import BrowserSession

    self.console.print(f"\n[bold cyan]Opening browser for: {site_name}[/bold cyan]")
    self.console.print(f"[dim]URL: {url}[/dim]")

    # Create session
    session = await self.session_pool.acquire(site_name)

    try:
        # Start browser and navigate
        await session.start(url, viewports[0])

        # Print VNC URL
        vnc_url = session.get_vnc_url()
        self.console.print(f"\n[green]→ View/interact at:[/green] {vnc_url}")
        self.console.print("[yellow]Solve CAPTCHAs, log in, set up page as needed.[/yellow]")

        # Wait for user
        self.console.print("\n[dim]Press Enter when ready to capture screenshots...[/dim]")
        input()

        # Capture all viewports
        results = []
        for viewport in viewports:
            filepath = await session.capture_screenshot(
                viewport=viewport,
                output_dir=screenshots_dir,
                filename=f"{viewport['name']}.png"
            )
            results.append({
                "success": True,
                "filepath": filepath,
                "viewport_name": viewport["name"],
            })
            self.console.print(f"  [green]✓[/green] Captured {viewport['name']}.png")

        return {
            "success": True,
            "site_name": site_name,
            "url": url,
            "screenshots": results,
        }

    except Exception as e:
        return {
            "success": False,
            "site_name": site_name,
            "url": url,
            "error": str(e),
        }

    finally:
        await self.session_pool.release(site_name)
```

**Step 2: Commit**

```bash
git add main.py
git commit -m "feat: add interactive capture method with VNC URL display"
```

---

### Task 4.4: Implement Automated Capture Flow

**Files:**
- Modify: `main.py`

**Step 1: Add automated capture method to orchestrator**

```python
async def _auto_capture(
    self,
    url: str,
    site_name: str,
    viewports: List[Dict[str, int]],
    screenshots_dir: Path
) -> Dict[str, Any]:
    """
    Capture screenshots in automated mode with delays.

    No user interaction required. Includes random delays for stealth.
    """
    import random

    self.console.print(f"\n[bold cyan]Capturing:[/bold cyan] {site_name}")
    self.console.print(f"[dim]URL: {url}[/dim]")

    try:
        # Use persistent context capture
        results = await self.screenshot_capturer.capture_with_persistent_context(
            url=url,
            site_name=site_name,
            viewports=viewports,
            profile_dir=Path(f"./browser_profiles/{site_name}"),
            full_page=True,
            custom_output_dir=screenshots_dir,
        )

        # Check for blocks
        blocked = [r for r in results if r.get("blocked")]
        if blocked:
            self.console.print(f"  [yellow]⚠ Bot detection: {blocked[0].get('error')}[/yellow]")
            self.console.print(f"  [dim]Run with --interactive to handle manually[/dim]")
            return {
                "success": False,
                "site_name": site_name,
                "url": url,
                "error": blocked[0].get("error"),
                "blocked": True,
            }

        # Log success
        successful = [r for r in results if r.get("success")]
        for r in successful:
            self.console.print(f"  [green]✓[/green] Captured {r['viewport_name']}.png")

        # Random delay before next capture
        delay = random.uniform(3, 10)
        self.console.print(f"  [dim]Waiting {delay:.1f}s before next capture...[/dim]")
        await asyncio.sleep(delay)

        return {
            "success": True,
            "site_name": site_name,
            "url": url,
            "screenshots": results,
        }

    except Exception as e:
        return {
            "success": False,
            "site_name": site_name,
            "url": url,
            "error": str(e),
        }
```

**Step 2: Commit**

```bash
git add main.py
git commit -m "feat: add automated capture method with stealth delays"
```

---

### Task 4.5: Wire Capture Modes into Main Flow

**Files:**
- Modify: `main.py`

**Step 1: Update capture_competitor_screenshots method**

Find the existing `capture_competitor_screenshots` method and add mode routing:

```python
async def capture_competitor_screenshots(
    self,
    url: str,
    site_name: str,
    competitor_paths: Dict[str, Any] = None
) -> Dict[str, Any]:

    # Get viewports from config
    screenshot_config = self.analysis_type_config.screenshot_config
    viewports = [
        {"name": vp.name, "width": vp.width, "height": vp.height}
        for vp in screenshot_config.viewports
    ]

    screenshots_dir = None
    if competitor_paths:
        screenshots_dir = competitor_paths['screenshots']
    else:
        screenshots_dir = Path(self.output_dir) / "screenshots" / site_name

    screenshots_dir = Path(screenshots_dir)
    screenshots_dir.mkdir(parents=True, exist_ok=True)

    # Route to appropriate capture mode
    if self.interactive_mode:
        return await self._interactive_capture(url, site_name, viewports, screenshots_dir)

    elif self.auto_mode:
        return await self._auto_capture(url, site_name, viewports, screenshots_dir)

    else:
        # Existing flow (manual mode or default with prompts)
        # ... keep existing implementation ...
```

**Step 2: Commit**

```bash
git add main.py
git commit -m "feat: wire interactive and auto modes into capture flow"
```

---

### Task 4.6: Update main Entry Point

**Files:**
- Modify: `main.py`
- Modify: `cli.py`

**Step 1: Pass mode flags to orchestrator (`main.py`)**

Find where `UXAnalysisOrchestrator` is instantiated in `main()`:

```python
orchestrator = UXAnalysisOrchestrator(
    api_key=api_key,
    model=args.model,
    analysis_type=analysis_type,
    config_path=args.config,
    manual_mode=args.manual_mode,
    screenshots_dir=args.screenshots_dir,
    llm_provider=os.getenv("LLM_PROVIDER"),
    interactive_mode=args.interactive,  # NEW
    auto_mode=args.auto,                # NEW
)
```

**Step 2: Add mode display to startup**

```python
# After orchestrator creation
if args.interactive:
    console.print("[bold blue]━━━ Interactive Mode ━━━[/bold blue]")
    console.print("Browser will open with VNC access for human interaction.")
elif args.auto:
    console.print("[bold blue]━━━ Automated Mode ━━━[/bold blue]")
    console.print("Running unattended with stealth delays.")
```

**Step 3: Fix unified CLI capture-mode routing (`cli.py`)**

In `fresh_analysis_menu()`, update command flag mapping so menu choices route to the new capture flags:

```python
# Build main.py command
cmd = [
    str(VENV_PYTHON), "main.py",
    "--config", temp_config,
    "--analysis-type", page_type,
    "--no-deploy",
]

if is_supervised:
    cmd.append("--interactive")
else:
    cmd.append("--auto")
```

Important: remove the old `is_supervised -> --manual-mode` mapping.
`--manual-mode` remains only for explicit pre-captured screenshot workflows.

**Step 4: Commit**

```bash
git add main.py cli.py
git commit -m "feat: wire unified CLI capture menu to interactive/auto modes"
```

---

## Phase 5: Integration Testing

### Task 5.1: Test Interactive Mode Locally

**Files:** None (manual testing)

**Step 1: Run interactive capture through the real entrypoint**

```bash
cd /home/matt99is/projects/UXMaturityAnalysis
./run.sh
```

Menu path:
1. `Fresh analysis`
2. Select page type
3. Select competitor set
4. `Supervised` capture mode

**Step 2: (Optional fast dev loop) run orchestrator directly**

```bash
cd /home/matt99is/projects/UXMaturityAnalysis
python main.py --interactive --config /tmp/test_competitors.json --analysis-type basket_pages
```

**Step 3: Verify VNC URL is printed**

Expected output:
```
━━━ Interactive Mode ━━━
✓ Xvfb display :99 ready

[1/N] Opening browser for: tesco
→ View/interact at: http://hostname:6080/vnc.html

Press Enter when ready to capture screenshots...
```

**Step 4: Open VNC URL in browser and verify browser is visible**

**Step 5: Press Enter and verify screenshots are captured**

```bash
ls output/basket-pages/*/screenshots/tesco/
# Expected: desktop.png, mobile.png
```

---

### Task 5.2: Test Automated Mode Locally

**Files:** None (manual testing)

**Step 1: Run automated capture through the real entrypoint**

```bash
cd /home/matt99is/projects/UXMaturityAnalysis
./run.sh
```

Menu path:
1. `Fresh analysis`
2. Select page type
3. Select competitor set
4. `Automated` capture mode

**Step 2: (Optional fast dev loop) run orchestrator directly**

```bash
cd /home/matt99is/projects/UXMaturityAnalysis
python main.py --auto --config /tmp/test_competitors.json --analysis-type basket_pages
```

**Step 3: Verify delays between captures**

Expected output:
```
━━━ Automated Mode ━━━

[1/N] Capturing: tesco
  Waiting 5.2s for page load...
  ✓ Captured desktop.png
  ✓ Captured mobile.png
  Waiting 7.3s before next capture...

[2/N] Capturing: sainsburys
  ...
```

---

### Task 5.3: Test Bot Detection Sites

**Files:** None (manual testing)

**Step 1: Test against bot detection checkers**

```bash
# Create test config with detection test sites
cat > test_sites.json << 'EOF'
{
  "competitors": [
    {"name": "sannysoft", "url": "https://bot.sannysoft.com"},
    {"name": "pixelscan", "url": "https://pixelscan.net"}
  ]
}
EOF

python main.py --auto --config test_sites.json
```

**Step 2: Verify screenshots show passing results**

Open the captured screenshots and verify:
- bot.sannysoft.com: All green checkmarks
- pixelscan.net: No red warnings

---

### Task 5.4: Run Full Test Suite

**Files:** None

**Step 1: Run all tests**

```bash
cd /home/matt99is/projects/UXMaturityAnalysis
pytest tests/ -v
```

**Step 2: Verify all tests pass**

Expected: All tests pass including new browser_session tests.

---

## Phase 6: Documentation

### Task 6.1: Update README

**Files:**
- Modify: `README.md`

**Step 1: Add unified CLI capture mode usage section**

Add this content:

```markdown
### Capture Modes

#### Interactive Mode (Human-in-the-Loop)
For bot-protected sites requiring CAPTCHA solving or login:
```

```bash
./run.sh
# choose: Fresh analysis -> Supervised
```

```markdown
Opens browser accessible via VNC at `http://<server>:6080/vnc.html`.
Solve challenges, then press Enter to capture.

#### Automated Mode (Unattended)
For batch runs on sites without heavy bot protection:
```

```bash
./run.sh
# choose: Fresh analysis -> Automated
```

```markdown
Runs with stealth delays between captures. Blocked sites are skipped and logged.

Advanced shortcut (developer/debug use):
```

```bash
python main.py --interactive --config /tmp/test_competitors.json --analysis-type basket_pages
python main.py --auto --config /tmp/test_competitors.json --analysis-type basket_pages
```

**Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add interactive and auto mode usage to README"
```

---

### Task 6.2: Update PROJECT_STATE

**Files:**
- Modify: `PROJECT_STATE.md`

**Step 1: Move infrastructure task to completed**

Update the "Web GUI: Human-in-the-Loop Browser Capture" section:

```markdown
### ~~Web GUI: Human-in-the-Loop Browser Capture~~ ✅ COMPLETE

**Implementation:** `docs/plans/2026-03-02-browser-capture-infrastructure-impl.md`

**Delivered:**
- Xvfb + x11vnc + websockify + noVNC infrastructure
- Patchright migration for stealth automation
- `--interactive` mode with VNC URL display
- `--auto` mode with stealth delays
- BrowserSessionPool for session management
```

**Step 2: Commit**

```bash
git add PROJECT_STATE.md
git commit -m "docs: mark browser capture infrastructure as complete"
```

---

## Summary

| Phase | Tasks | Key Deliverables |
|-------|-------|------------------|
| 1. Infrastructure Setup | 1.1 - 1.6 | Xvfb, x11vnc, websockify, noVNC, Patchright |
| 2. Browser Session Module | 2.1 - 2.6 | DisplayAllocator, BrowserSession, BrowserSessionPool |
| 3. Screenshot Capture Migration | 3.1 - 3.2 | Patchright integration, persistent context |
| 4. CLI + Orchestrator Integration | 4.1 - 4.6 | main.py flags + cli.py menu routing |
| 5. Integration Testing | 5.1 - 5.4 | Manual and automated verification |
| 6. Documentation | 6.1 - 6.2 | README, PROJECT_STATE updates |

**Total Tasks:** 17
**Estimated Time:** 4-6 hours

---

## Execution Handoff

Plan complete and saved to `docs/plans/2026-03-02-browser-capture-infrastructure-impl.md`.
