"""
Screenshot capture using Playwright.

EXTENSIBILITY NOTE: This module is designed to handle various screenshot
scenarios. Future enhancements can include:
- Multi-step navigation (homepage -> product -> basket)
- Interaction-based captures (click, scroll, form fill)
- Different page states (loading, error, success)
"""

import asyncio
from pathlib import Path
from typing import Dict, List, Optional
from playwright.async_api import async_playwright, Browser, Page
import base64
from datetime import datetime


class ScreenshotCapture:
    """
    Handles browser automation and screenshot capture.

    EXTENSIBILITY NOTE: This class is structured to support future
    multi-step journeys and complex interactions beyond simple URL capture.
    """

    def __init__(self, output_dir: str = "screenshots"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.browser: Optional[Browser] = None

    async def initialize_browser(self, headless: bool = True):
        """Initialize Playwright browser."""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=headless)

    async def close_browser(self):
        """Close browser and cleanup."""
        if self.browser:
            await self.browser.close()
        if hasattr(self, 'playwright'):
            await self.playwright.stop()

    async def capture_url(
        self,
        url: str,
        site_name: str,
        viewport_width: int = 1920,
        viewport_height: int = 1080,
        full_page: bool = True,
        wait_time: int = 3000
    ) -> Dict[str, any]:
        """
        Capture screenshot of a URL.

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

        # Create context with specified viewport
        context = await self.browser.new_context(
            viewport={"width": viewport_width, "height": viewport_height},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )

        page = await context.new_page()

        try:
            # Navigate to URL
            response = await page.goto(url, wait_until="networkidle", timeout=30000)

            # Wait for page to settle
            await asyncio.sleep(wait_time / 1000)

            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            viewport_suffix = "desktop" if viewport_width > 768 else "mobile"
            filename = f"{site_name}_{viewport_suffix}_{timestamp}.png"
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
                "http_status": response.status if response else None
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
        full_page: bool = True
    ) -> List[Dict[str, any]]:
        """
        Capture screenshots across multiple viewports.

        Args:
            url: URL to capture
            site_name: Name/identifier for the site
            viewports: List of viewport configs [{"name": "desktop", "width": 1920, "height": 1080}]
            full_page: Whether to capture full page

        Returns:
            List of capture results

        EXTENSIBILITY NOTE: This is useful for responsive analysis.
        Can be extended to test different device types automatically.
        """
        results = []

        for viewport in viewports:
            result = await self.capture_url(
                url=url,
                site_name=site_name,
                viewport_width=viewport["width"],
                viewport_height=viewport["height"],
                full_page=full_page
            )
            result["viewport_name"] = viewport["name"]
            results.append(result)

        return results

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
