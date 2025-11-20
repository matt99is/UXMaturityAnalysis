#!/usr/bin/env python3
"""
Example usage of the UX Analysis Agent as a Python library.

This shows how to use the components programmatically rather than
via the command-line interface.
"""

import asyncio
import os
from pathlib import Path
import sys
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config_loader import AnalysisConfig
from src.analyzers.screenshot_capture import ScreenshotCapture
from src.analyzers.claude_analyzer import ClaudeUXAnalyzer
from src.utils.report_generator import ReportGenerator


async def example_basic_analysis():
    """
    Example 1: Basic analysis of a single competitor.
    """
    print("Example 1: Basic Single Competitor Analysis")
    print("=" * 60)

    # Load environment
    load_dotenv()
    api_key = os.getenv("ANTHROPIC_API_KEY")

    if not api_key:
        print("Error: ANTHROPIC_API_KEY not found in .env")
        return

    # Initialize components
    config = AnalysisConfig()
    basket_config = config.get_analysis_type("basket_pages")
    capturer = ScreenshotCapture()
    analyzer = ClaudeUXAnalyzer(api_key=api_key)

    # Competitor to analyze
    competitor = {
        "name": "example_shop",
        "url": "https://www.example.com/basket"
    }

    try:
        # Initialize browser
        await capturer.initialize_browser()

        # Capture screenshots
        print(f"Capturing screenshots for {competitor['name']}...")
        viewports = [
            {"name": "desktop", "width": 1920, "height": 1080},
            {"name": "mobile", "width": 375, "height": 812}
        ]

        screenshots = await capturer.capture_multiple_viewports(
            url=competitor["url"],
            site_name=competitor["name"],
            viewports=viewports
        )

        successful_screenshots = [s for s in screenshots if s.get("success")]
        print(f"Captured {len(successful_screenshots)} screenshots")

        if not successful_screenshots:
            print("No successful screenshots captured")
            return

        # Analyze with Claude
        print("Analyzing with Claude...")
        screenshot_paths = [s["filepath"] for s in successful_screenshots]

        criteria = [
            {
                "id": c.id,
                "name": c.name,
                "weight": c.weight,
                "description": c.description,
                "evaluation_points": c.evaluation_points,
                "benchmarks": c.benchmarks
            }
            for c in basket_config.criteria
        ]

        result = await analyzer.analyze_screenshots(
            screenshot_paths=screenshot_paths,
            criteria=criteria,
            analysis_name=basket_config.name,
            site_name=competitor["name"],
            url=competitor["url"]
        )

        if result.get("success"):
            print(f"Analysis complete! Overall score: {result['analysis']['overall_score']}/10")
            print("\nTop 3 Strengths:")
            for strength in result["analysis"]["strengths"][:3]:
                print(f"  - {strength}")
        else:
            print(f"Analysis failed: {result.get('error')}")

    finally:
        await capturer.close_browser()


async def example_multiple_competitors():
    """
    Example 2: Analyze multiple competitors and generate reports.
    """
    print("\n\nExample 2: Multiple Competitors with Report Generation")
    print("=" * 60)

    # Load environment
    load_dotenv()
    api_key = os.getenv("ANTHROPIC_API_KEY")

    if not api_key:
        print("Error: ANTHROPIC_API_KEY not found in .env")
        return

    # Initialize
    config = AnalysisConfig()
    basket_config = config.get_analysis_type("basket_pages")
    capturer = ScreenshotCapture()
    analyzer = ClaudeUXAnalyzer(api_key=api_key)
    reporter = ReportGenerator()

    # Competitors list
    competitors = [
        {"name": "shop_a", "url": "https://www.shop-a.com/basket"},
        {"name": "shop_b", "url": "https://www.shop-b.com/cart"}
    ]

    results = []

    try:
        await capturer.initialize_browser()

        for competitor in competitors:
            print(f"\nAnalyzing {competitor['name']}...")

            # Capture
            screenshots = await capturer.capture_multiple_viewports(
                url=competitor["url"],
                site_name=competitor["name"],
                viewports=[
                    {"name": "desktop", "width": 1920, "height": 1080}
                ]
            )

            successful = [s for s in screenshots if s.get("success")]
            if not successful:
                results.append({
                    "success": False,
                    "site_name": competitor["name"],
                    "error": "Screenshot capture failed"
                })
                continue

            # Analyze
            criteria = [
                {
                    "id": c.id,
                    "name": c.name,
                    "weight": c.weight,
                    "description": c.description,
                    "evaluation_points": c.evaluation_points,
                    "benchmarks": c.benchmarks
                }
                for c in basket_config.criteria
            ]

            result = await analyzer.analyze_screenshots(
                screenshot_paths=[s["filepath"] for s in successful],
                criteria=criteria,
                analysis_name=basket_config.name,
                site_name=competitor["name"],
                url=competitor["url"]
            )

            results.append(result)

        # Generate reports
        print("\n\nGenerating reports...")
        json_path = reporter.save_json_report(results)
        md_path = reporter.generate_markdown_report(results)

        print(f"JSON report: {json_path}")
        print(f"Markdown report: {md_path}")

    finally:
        await capturer.close_browser()


async def example_custom_criteria():
    """
    Example 3: Using custom analysis criteria (from a custom config).
    """
    print("\n\nExample 3: Custom Analysis Type")
    print("=" * 60)

    # This example shows how you would use a different analysis type
    # if you had defined it in config.yaml

    config = AnalysisConfig()

    # List available analysis types
    available = config.list_available_analysis_types()
    print(f"Available analysis types: {', '.join(available)}")

    # Load specific type
    basket_config = config.get_analysis_type("basket_pages")
    print(f"\nUsing: {basket_config.name}")
    print(f"Criteria count: {len(basket_config.criteria)}")

    # Show criteria
    print("\nCriteria:")
    for criterion in basket_config.criteria:
        print(f"  - {criterion.name} (weight: {criterion.weight}/10)")


async def example_screenshot_only():
    """
    Example 4: Just capture screenshots without analysis.
    """
    print("\n\nExample 4: Screenshot Capture Only")
    print("=" * 60)

    capturer = ScreenshotCapture()

    try:
        await capturer.initialize_browser()

        # Capture desktop and mobile
        result = await capturer.capture_url(
            url="https://www.example.com",
            site_name="example",
            viewport_width=1920,
            viewport_height=1080,
            full_page=True
        )

        if result.get("success"):
            print(f"Screenshot saved to: {result['filepath']}")
            print(f"Page title: {result['title']}")
            print(f"Final URL: {result['final_url']}")
        else:
            print(f"Capture failed: {result.get('error')}")

    finally:
        await capturer.close_browser()


def main():
    """Run examples."""
    print("UX Analysis Agent - Usage Examples")
    print("=" * 60)
    print()
    print("These examples show how to use the tool programmatically.")
    print("Uncomment the example you want to run.\n")

    # Run examples (uncomment the one you want to try)

    # Example 1: Basic single competitor
    # asyncio.run(example_basic_analysis())

    # Example 2: Multiple competitors with reports
    # asyncio.run(example_multiple_competitors())

    # Example 3: Show custom criteria usage
    asyncio.run(example_custom_criteria())

    # Example 4: Screenshot capture only
    # asyncio.run(example_screenshot_only())


if __name__ == "__main__":
    main()
