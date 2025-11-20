"""
Screenshot capture using Playwright with stealth mode.

EXTENSIBILITY NOTE: This module is designed to handle various screenshot
scenarios. Future enhancements can include:
- Multi-step navigation (homepage -> product -> basket)
- Interaction-based captures (click, scroll, form fill)
- Different page states (loading, error, success)

STEALTH MODE: Includes bot detection evasion techniques to avoid being blocked
by sites with anti-bot protection (Cloudflare, DataDome, etc.)
"""

import asyncio
import random
from pathlib import Path
from typing import Dict, List, Optional
from playwright.async_api import async_playwright, Browser, Page
from playwright_stealth import Stealth
import base64
from datetime import datetime


class ScreenshotCapture:
    """
    Handles browser automation and screenshot capture with stealth mode.

    EXTENSIBILITY NOTE: This class is structured to support future
    multi-step journeys and complex interactions beyond simple URL capture.
    """

    # Realistic user agents (rotated to appear more human)
    USER_AGENTS = [
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    ]

    def __init__(self, output_dir: str = "screenshots"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.browser: Optional[Browser] = None
        self.stealth_mode = True  # Enable by default

    async def initialize_browser(self, headless: bool = True):
        """
        Initialize Playwright browser with stealth settings.

        Stealth features:
        - Realistic browser args to avoid detection
        - Disabled automation flags
        - Realistic window size
        """
        self.playwright = await async_playwright().start()

        # Launch args to appear more human-like
        launch_args = [
            '--disable-blink-features=AutomationControlled',  # Hide automation
            '--disable-dev-shm-usage',
            '--disable-setuid-sandbox',
            '--no-sandbox',
            '--disable-web-security',
            '--disable-features=IsolateOrigins,site-per-process',
            '--window-size=1920,1080',
        ]

        self.browser = await self.playwright.chromium.launch(
            headless=headless,
            args=launch_args
        )

    async def close_browser(self):
        """Close browser and cleanup."""
        if self.browser:
            await self.browser.close()
        if hasattr(self, 'playwright'):
            await self.playwright.stop()

    async def _create_stealth_context(self, viewport_width: int, viewport_height: int):
        """
        Create a browser context with stealth settings to avoid bot detection.

        Returns:
            Browser context configured for stealth
        """
        # Pick a random realistic user agent
        user_agent = random.choice(self.USER_AGENTS)

        # Create context with stealth settings
        context = await self.browser.new_context(
            viewport={"width": viewport_width, "height": viewport_height},
            user_agent=user_agent,
            locale='en-US',
            timezone_id='America/New_York',
            # Add realistic browser features
            extra_http_headers={
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
        )

        return context

    async def _human_like_scroll(self, page: Page):
        """
        Scroll the page in a human-like manner to trigger lazy loading
        and appear more natural to bot detection systems.
        """
        try:
            # Get page height
            page_height = await page.evaluate("document.body.scrollHeight")

            # Scroll in chunks with random delays
            scroll_position = 0
            scroll_increment = random.randint(300, 500)

            while scroll_position < page_height:
                scroll_position += scroll_increment
                await page.evaluate(f"window.scrollTo(0, {scroll_position})")

                # Random delay between scrolls (human-like)
                await asyncio.sleep(random.uniform(0.1, 0.3))

            # Scroll back to top
            await page.evaluate("window.scrollTo(0, 0)")
            await asyncio.sleep(0.5)

        except Exception as e:
            # If scrolling fails, continue anyway
            pass

    async def _random_delay(self, min_seconds: float = 0.5, max_seconds: float = 2.0):
        """Add a random delay to appear more human-like."""
        await asyncio.sleep(random.uniform(min_seconds, max_seconds))

    async def _check_if_blocked(self, page: Page) -> Dict[str, any]:
        """
        Check if the page shows signs of bot blocking.

        Returns:
            Dictionary with 'blocked' boolean and 'reason' if blocked
        """
        try:
            title = (await page.title()).lower()
            content = await page.content()
            content_lower = content.lower()

            # Check for blocking indicators in title (more reliable)
            title_indicators = [
                'access denied',
                '403 forbidden',
                'captcha',
                'challenge',
                'blocked',
                'security check',
                'attention required',
                'bot detection',
            ]

            for indicator in title_indicators:
                if indicator in title:
                    return {
                        'blocked': True,
                        'reason': f'{indicator.title()} detected',
                        'title': title,
                    }

            # Check for strong blocking indicators in content (avoid false positives)
            # Only match if they appear near the beginning of the page
            content_start = content_lower[:2000]  # First 2000 chars

            strong_indicators = [
                ('access denied</h1>', 'Access Denied error page'),
                ('403 forbidden</h1>', 'HTTP 403 Forbidden'),
                ('just a moment', 'Cloudflare challenge'),
                ('checking your browser', 'Bot challenge page'),
                ('why have i been blocked', 'Explicit block message'),
                ('enable javascript and cookies', 'Security check'),
            ]

            for indicator, reason in strong_indicators:
                if indicator in content_start:
                    return {
                        'blocked': True,
                        'reason': reason,
                        'title': title,
                    }

            return {'blocked': False}

        except Exception as e:
            return {'blocked': False, 'error': str(e)}

    async def capture_url(
        self,
        url: str,
        site_name: str,
        viewport_width: int = 1920,
        viewport_height: int = 1080,
        full_page: bool = True,
        wait_time: int = 3000,
        custom_output_dir: Path = None,
        custom_filename: str = None
    ) -> Dict[str, any]:
        """
        Capture screenshot of a URL with stealth mode.

        Args:
            url: URL to capture
            site_name: Name/identifier for the site
            viewport_width: Viewport width in pixels
            viewport_height: Viewport height in pixels
            full_page: Whether to capture full page or just viewport
            wait_time: Time to wait after page load (ms)

        Returns:
            Dictionary with screenshot path and metadata

        EXTENSIBILITY NOTE: This method can be extended to support:
        - Navigation steps (clicks, scrolls)
        - Form interactions (filling baskets)
        - State verification (checking elements exist)
        """
        if not self.browser:
            await self.initialize_browser()

        # Create stealth context
        context = await self._create_stealth_context(viewport_width, viewport_height)
        page = await context.new_page()

        # Apply stealth mode to hide automation
        if self.stealth_mode:
            try:
                # Use basic anti-detection scripts
                await page.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                    Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
                    Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
                    window.chrome = {runtime: {}};
                """)
            except Exception as e:
                # If stealth mode fails, continue anyway
                pass

        try:
            # Random delay before navigation (appear more human)
            await self._random_delay(0.5, 1.5)

            # Navigate to URL
            response = await page.goto(url, wait_until="networkidle", timeout=30000)

            # Wait for page to settle
            await asyncio.sleep(wait_time / 1000)

            # Check if we got blocked
            block_check = await self._check_if_blocked(page)
            if block_check['blocked']:
                return {
                    "success": False,
                    "error": f"Bot detection: {block_check['reason']}",
                    "blocked": True,
                    "block_reason": block_check['reason'],
                    "url": url,
                    "viewport": {"width": viewport_width, "height": viewport_height}
                }

            # Human-like scrolling (triggers lazy loading, appears natural)
            await self._human_like_scroll(page)

            # Random delay before screenshot
            await self._random_delay(0.5, 1.0)

            # Generate timestamp (always needed for metadata)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Generate filename and filepath
            if custom_filename:
                filename = custom_filename
            else:
                viewport_suffix = "desktop" if viewport_width > 768 else "mobile"
                filename = f"{site_name}_{viewport_suffix}_{timestamp}.png"

            if custom_output_dir:
                filepath = custom_output_dir / filename
            else:
                filepath = self.output_dir / filename

            # Capture screenshot
            await page.screenshot(path=str(filepath), full_page=full_page)

            # Get page metadata
            title = await page.title()
            final_url = page.url

            # EXTENSIBILITY NOTE: Future enhancement - capture HTML/DOM
            # html_content = await page.content()
            # This can be useful for detecting specific patterns or elements

            result = {
                "success": True,
                "filepath": str(filepath),
                "filename": filename,
                "url": url,
                "final_url": final_url,
                "title": title,
                "viewport": {"width": viewport_width, "height": viewport_height},
                "timestamp": timestamp,
                "http_status": response.status if response else None,
                "stealth_mode": self.stealth_mode
            }

            return result

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "url": url,
                "viewport": {"width": viewport_width, "height": viewport_height}
            }

        finally:
            await context.close()

    async def capture_multiple_viewports(
        self,
        url: str,
        site_name: str,
        viewports: List[Dict[str, int]],
        full_page: bool = True,
        custom_output_dir: Path = None
    ) -> List[Dict[str, any]]:
        """
        Capture screenshots across multiple viewports.

        Args:
            url: URL to capture
            site_name: Name/identifier for the site
            viewports: List of viewport configs [{"name": "desktop", "width": 1920, "height": 1080}]
            full_page: Whether to capture full page
            custom_output_dir: Optional custom directory for screenshots

        Returns:
            List of capture results

        EXTENSIBILITY NOTE: This is useful for responsive analysis.
        Can be extended to test different device types automatically.
        """
        results = []

        for viewport in viewports:
            # Use simple filename for audit structure: desktop.png, mobile.png
            custom_filename = f"{viewport['name']}.png" if custom_output_dir else None

            result = await self.capture_url(
                url=url,
                site_name=site_name,
                viewport_width=viewport["width"],
                viewport_height=viewport["height"],
                full_page=full_page,
                custom_output_dir=custom_output_dir,
                custom_filename=custom_filename
            )
            result["viewport_name"] = viewport["name"]
            results.append(result)

        return results

    async def capture_with_interaction(
        self,
        url: str,
        site_name: str,
        viewports: List[Dict[str, int]],
        interaction_prompt: str,
        interaction_instructions: str = None,
        timeout: int = 120,
        full_page: bool = True,
        custom_output_dir: Path = None
    ) -> List[Dict[str, any]]:
        """
        Capture screenshots with human-in-the-loop interaction.

        Opens browser in visible mode, navigates to URL, waits for user
        to interact (e.g., add items to basket), then captures screenshots.

        Args:
            url: URL to navigate to
            site_name: Name/identifier for the site
            viewports: List of viewport configs
            interaction_prompt: Message to display to user
            interaction_instructions: Detailed instructions for user
            timeout: Maximum seconds to wait for user input
            full_page: Whether to capture full page

        Returns:
            List of capture results

        EXTENSIBILITY NOTE: This enables manual setup for pages that need it
        (e.g., adding items to basket, logging in, etc.)
        """
        import sys
        from rich.console import Console
        from rich.panel import Panel

        console = Console()

        # Browser should already be initialized in visible mode by caller
        if not self.browser:
            raise RuntimeError("Browser not initialized. Call initialize_browser() first.")

        # Create a persistent stealth context (won't close between viewports)
        context = await self._create_stealth_context(
            viewports[0]["width"],
            viewports[0]["height"]
        )

        page = await context.new_page()

        # Apply stealth mode to hide automation
        if self.stealth_mode:
            try:
                # Use basic anti-detection scripts
                await page.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                    Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
                    Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
                    window.chrome = {runtime: {}};
                """)
            except Exception as e:
                # If stealth mode fails, continue anyway
                pass

        try:
            # Random delay before navigation
            await self._random_delay(0.5, 1.5)

            # Navigate to URL with lenient wait condition
            # Use "domcontentloaded" instead of "networkidle" to avoid timeout on sites with persistent connections
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            except Exception as e:
                # If navigation fails, continue anyway - user can manually navigate
                console.print(f"[yellow]⚠ Initial navigation issue: {str(e)[:100]}...[/yellow]")
                console.print("[yellow]You can manually navigate in the browser window[/yellow]")

            await asyncio.sleep(3)  # Let page settle and resources load

            # Check if blocked
            block_check = await self._check_if_blocked(page)
            blocked_instructions = ""
            if block_check['blocked']:
                console.print(f"\n[yellow]⚠ Bot Detection Triggered: {block_check['reason']}[/yellow]")
                blocked_instructions = (
                    "\n[bold red]🤖 BOT DETECTED - Manual Navigation Required:[/bold red]\n"
                    "1. The visible browser may show CAPTCHA or 'Access Denied'\n"
                    "2. Manually navigate to the correct page\n"
                    "3. Complete any CAPTCHAs or verification steps\n"
                    "4. Set up the page as needed (add items, navigate, etc.)\n"
                    "5. Press Enter below when page is ready\n"
                )

            # Display instructions to user
            console.print()
            console.print(Panel.fit(
                f"[bold cyan]{interaction_prompt}[/bold cyan]\n\n"
                + (f"{interaction_instructions}\n\n" if interaction_instructions else "")
                + blocked_instructions
                + ("\n" if blocked_instructions else "")
                + "[yellow]Browser window is open - interact with the page as needed.[/yellow]\n"
                + f"[dim]Timeout: {timeout} seconds[/dim]",
                title=f"🔧 Interactive Mode: {site_name}",
                border_style="red" if block_check['blocked'] else "cyan"
            ))

            # Wait for user to press Enter (using synchronous input - simpler and more reliable)
            try:
                console.print()
                input("[Press Enter when ready to capture screenshots...] ")
                console.print("[green]✓ Proceeding with capture...[/green]")
            except (EOFError, KeyboardInterrupt):
                console.print("[yellow]⚠ Input cancelled - skipping capture[/yellow]")
                return [{
                    "success": False,
                    "error": "User cancelled",
                    "url": url,
                    "interactive_mode": True
                }]

            # Capture screenshots in all viewports
            results = []

            for i, viewport in enumerate(viewports):
                # Set viewport size
                await page.set_viewport_size({
                    "width": viewport["width"],
                    "height": viewport["height"]
                })
                await asyncio.sleep(1)  # Let page adjust

                # Generate timestamp (always needed for metadata)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

                # Generate filename and filepath
                viewport_suffix = viewport["name"]

                if custom_output_dir:
                    # Use simple filename for audit structure: desktop.png, mobile.png
                    filename = f"{viewport_suffix}.png"
                    filepath = custom_output_dir / filename
                else:
                    # Use timestamped filename for legacy structure
                    filename = f"{site_name}_{viewport_suffix}_{timestamp}.png"
                    filepath = self.output_dir / filename

                # Capture screenshot
                await page.screenshot(path=str(filepath), full_page=full_page)

                # Get metadata
                title = await page.title()
                final_url = page.url

                result = {
                    "success": True,
                    "filepath": str(filepath),
                    "filename": filename,
                    "url": url,
                    "final_url": final_url,
                    "title": title,
                    "viewport": {"width": viewport["width"], "height": viewport["height"]},
                    "viewport_name": viewport["name"],
                    "timestamp": timestamp,
                    "interactive_mode": True
                }

                results.append(result)
                console.print(f"  [green]✓[/green] Captured {viewport['name']} ({viewport['width']}x{viewport['height']})")

            return results

        except Exception as e:
            console.print(f"[red]✗ Error during interactive capture: {e}[/red]")
            return [{
                "success": False,
                "error": str(e),
                "url": url,
                "interactive_mode": True
            }]

        finally:
            await context.close()

    def get_screenshot_base64(self, filepath: str) -> str:
        """
        Convert screenshot to base64 for API transmission.

        Args:
            filepath: Path to screenshot file

        Returns:
            Base64 encoded image string
        """
        with open(filepath, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")


    def load_screenshots_from_directory(
        self,
        screenshots_dir: Path,
        site_name: str,
        viewports: List[Dict[str, any]] = None
    ) -> List[Dict[str, any]]:
        """
        Load pre-captured screenshots from a directory (manual mode).

        This bypasses browser automation entirely and loads screenshots
        that were manually captured by the user. Perfect for sites with
        heavy bot detection or requiring authentication.

        Expected directory structure:
          screenshots_dir/
            ├── {site_name}_desktop.png
            ├── {site_name}_mobile.png
          OR:
            ├── desktop.png
            ├── mobile.png

        Args:
            screenshots_dir: Path to directory containing screenshots
            site_name: Name/identifier for the site
            viewports: Optional viewport list for naming (default: desktop/mobile)

        Returns:
            List of screenshot results with file paths

        Usage:
            python main.py --manual-mode --screenshots-dir ./my-screenshots
        """
        screenshots_dir = Path(screenshots_dir)

        if not screenshots_dir.exists():
            return [{
                "success": False,
                "error": f"Screenshots directory not found: {screenshots_dir}",
                "filepath": None,
                "viewport": "unknown"
            }]

        results = []

        # Try to find screenshots with various naming patterns
        viewport_names = ["desktop", "mobile"] if not viewports else [vp["name"] for vp in viewports]

        for viewport_name in viewport_names:
            screenshot_found = False
            tried_paths = []

            # Try different naming patterns
            possible_names = [
                f"{site_name}_{viewport_name}.png",
                f"{viewport_name}.png",
                f"{site_name}-{viewport_name}.png",
            ]

            for filename in possible_names:
                filepath = screenshots_dir / filename
                tried_paths.append(str(filepath))

                if filepath.exists():
                    results.append({
                        "success": True,
                        "filepath": str(filepath),
                        "viewport": viewport_name,
                        "mode": "manual",
                        "timestamp": datetime.now().isoformat()
                    })
                    screenshot_found = True
                    break

            if not screenshot_found:
                results.append({
                    "success": False,
                    "error": f"Screenshot not found for {viewport_name}. Tried: {', '.join(possible_names)}",
                    "filepath": None,
                    "viewport": viewport_name,
                    "tried_paths": tried_paths
                })

        return results


# EXTENSIBILITY NOTE: Future enhancement class for multi-step journeys
class JourneyCapture(ScreenshotCapture):
    """
    Extended capture class for multi-step user journeys.

    Example future usage:
    journey = JourneyCapture()
    await journey.start_journey("https://example.com")
    await journey.navigate_to_product("product-link")
    await journey.add_to_basket()
    screenshots = await journey.capture_basket_page()

    This class is a placeholder for future extensibility.
    """

    async def execute_journey(self, steps: List[Dict[str, any]]) -> List[Dict[str, any]]:
        """
        Execute a multi-step journey with screenshots at each step.

        Args:
            steps: List of step definitions with actions and selectors

        Returns:
            Screenshots captured at each step

        EXTENSIBILITY NOTE: Not implemented in POC, but structure
        is ready for future multi-step journey analysis.
        """
        raise NotImplementedError(
            "Multi-step journeys will be implemented in future iteration. "
            "Current POC supports single-URL capture."
        )


if __name__ == "__main__":
    # Test screenshot capture
    async def test_capture():
        capturer = ScreenshotCapture()
        await capturer.initialize_browser()

        result = await capturer.capture_url(
            url="https://www.example.com",
            site_name="example"
        )

        print(f"Capture result: {result}")
        await capturer.close_browser()

    asyncio.run(test_capture())
