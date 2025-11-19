#!/usr/bin/env python3
"""
E-commerce Basket Page UX Analysis Agent - Main Entry Point

This is a proof-of-concept tool for systematically analyzing competitor
e-commerce basket pages and generating structured UX reports.

EXTENSIBILITY NOTE: This main script orchestrates the analysis pipeline.
The architecture is designed to support different page types and analysis
criteria through configuration files rather than code changes.

Usage:
    python main.py --urls url1 url2 url3
    python main.py --config competitors.json
    python main.py --analysis-type basket_pages --urls url1 url2

Author: UX Analysis Agent POC
"""

import asyncio
import argparse
import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any
from dotenv import load_dotenv
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.table import Table

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from src.config_loader import AnalysisConfig
from src.analyzers.screenshot_capture import ScreenshotCapture
from src.analyzers.claude_analyzer import ClaudeUXAnalyzer
from src.utils.report_generator import ReportGenerator


class UXAnalysisOrchestrator:
    """
    Main orchestrator for UX analysis pipeline.

    EXTENSIBILITY NOTE: This class coordinates the analysis workflow
    and is designed to work with any analysis type defined in config.yaml.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "claude-sonnet-4-5-20250929",
        analysis_type: str = "basket_pages",
        config_path: str = "config.yaml"
    ):
        self.console = Console()
        self.analysis_config = AnalysisConfig(config_path)
        self.analysis_type_config = self.analysis_config.get_analysis_type(analysis_type)
        self.screenshot_capturer = ScreenshotCapture()
        self.claude_analyzer = ClaudeUXAnalyzer(api_key=api_key, model=model)
        self.report_generator = ReportGenerator()

    async def analyze_competitor(
        self,
        url: str,
        site_name: str
    ) -> Dict[str, Any]:
        """
        Analyze a single competitor's page.

        Args:
            url: URL to analyze
            site_name: Identifier for the competitor

        Returns:
            Analysis result dictionary

        EXTENSIBILITY NOTE: This method follows the workflow defined
        in the analysis type config, making it adaptable to different
        page types and capture strategies.
        """
        self.console.print(f"\n[bold cyan]Analyzing:[/bold cyan] {site_name}")
        self.console.print(f"[dim]URL: {url}[/dim]")

        try:
            # Step 1: Capture screenshots
            self.console.print("  [yellow]Capturing screenshots...[/yellow]")

            screenshot_config = self.analysis_type_config.screenshot_config
            viewports = [
                {"name": vp.name, "width": vp.width, "height": vp.height}
                for vp in screenshot_config.viewports
            ]

            screenshot_results = await self.screenshot_capturer.capture_multiple_viewports(
                url=url,
                site_name=site_name,
                viewports=viewports,
                full_page=screenshot_config.full_page
            )

            # Check for capture failures
            failed_captures = [r for r in screenshot_results if not r.get("success")]
            if failed_captures:
                self.console.print(f"  [red]Warning: {len(failed_captures)} screenshot(s) failed[/red]")

            successful_captures = [r for r in screenshot_results if r.get("success")]
            if not successful_captures:
                return {
                    "success": False,
                    "site_name": site_name,
                    "url": url,
                    "error": "All screenshot captures failed"
                }

            screenshot_paths = [r["filepath"] for r in successful_captures]
            self.console.print(f"  [green]Captured {len(screenshot_paths)} screenshot(s)[/green]")

            # Step 2: Analyze with Claude
            self.console.print("  [yellow]Analyzing with Claude AI...[/yellow]")

            # Convert criteria to dict format for analyzer
            criteria_dicts = [
                {
                    "id": c.id,
                    "name": c.name,
                    "weight": c.weight,
                    "description": c.description,
                    "evaluation_points": c.evaluation_points,
                    "benchmarks": c.benchmarks
                }
                for c in self.analysis_type_config.criteria
            ]

            analysis_result = await self.claude_analyzer.analyze_screenshots(
                screenshot_paths=screenshot_paths,
                criteria=criteria_dicts,
                analysis_name=self.analysis_type_config.name,
                site_name=site_name,
                url=url
            )

            if not analysis_result.get("success"):
                self.console.print(f"  [red]Analysis failed: {analysis_result.get('error')}[/red]")
                return {
                    "success": False,
                    "site_name": site_name,
                    "url": url,
                    "error": analysis_result.get("error"),
                    "screenshots": screenshot_paths
                }

            self.console.print(f"  [green]Analysis complete![/green]")

            # Add screenshot metadata to result
            result = analysis_result.copy()
            result["screenshot_metadata"] = successful_captures

            return result

        except Exception as e:
            self.console.print(f"  [red]Error: {str(e)}[/red]")
            return {
                "success": False,
                "site_name": site_name,
                "url": url,
                "error": str(e)
            }

    async def analyze_competitors(
        self,
        competitors: List[Dict[str, str]]
    ) -> List[Dict[str, Any]]:
        """
        Analyze multiple competitors.

        Args:
            competitors: List of dicts with 'name' and 'url' keys

        Returns:
            List of analysis results

        EXTENSIBILITY NOTE: This could be extended to analyze competitors
        in parallel for faster execution, or to implement rate limiting.
        """
        # Initialize browser once for all captures
        await self.screenshot_capturer.initialize_browser()

        results = []
        total = len(competitors)

        try:
            for i, competitor in enumerate(competitors, 1):
                self.console.print(f"\n[bold]Progress: {i}/{total}[/bold]")

                result = await self.analyze_competitor(
                    url=competitor["url"],
                    site_name=competitor["name"]
                )
                results.append(result)

        finally:
            # Cleanup browser
            await self.screenshot_capturer.close_browser()

        return results

    def generate_reports(self, results: List[Dict[str, Any]]) -> Dict[str, str]:
        """
        Generate JSON and markdown reports.

        Args:
            results: List of analysis results

        Returns:
            Dictionary with paths to generated reports
        """
        self.console.print("\n[bold cyan]Generating reports...[/bold cyan]")

        # Generate JSON report
        json_path = self.report_generator.save_json_report(results)
        self.console.print(f"[green]JSON report saved:[/green] {json_path}")

        # Generate Markdown report
        md_path = self.report_generator.generate_markdown_report(results)
        self.console.print(f"[green]Markdown report saved:[/green] {md_path}")

        return {
            "json": json_path,
            "markdown": md_path
        }

    def display_summary(self, results: List[Dict[str, Any]]):
        """Display summary table in console."""
        successful = [r for r in results if r.get("success")]
        failed = [r for r in results if not r.get("success")]

        self.console.print("\n")
        self.console.print(Panel.fit(
            f"[bold green]Analysis Complete![/bold green]\n\n"
            f"Successful: {len(successful)}\n"
            f"Failed: {len(failed)}",
            title="Summary"
        ))

        if successful:
            table = Table(title="Competitor Rankings")
            table.add_column("Rank", style="cyan")
            table.add_column("Competitor", style="yellow")
            table.add_column("Overall Score", style="green")

            # Sort by score
            sorted_results = sorted(
                successful,
                key=lambda x: x["analysis"]["overall_score"],
                reverse=True
            )

            for i, result in enumerate(sorted_results, 1):
                analysis = result["analysis"]
                score = analysis["overall_score"]
                table.add_row(
                    str(i),
                    analysis["site_name"],
                    f"{score:.1f}/10"
                )

            self.console.print(table)


async def main():
    """Main entry point for the UX analysis tool."""
    parser = argparse.ArgumentParser(
        description="E-commerce Basket Page UX Analysis Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --urls https://shop1.com/basket https://shop2.com/cart
  python main.py --config competitors.json
  python main.py --analysis-type basket_pages --urls https://example.com/cart

EXTENSIBILITY NOTE: Use --analysis-type to specify different page type
analyses defined in config.yaml (e.g., product_pages, checkout_pages).
        """
    )

    parser.add_argument(
        "--urls",
        nargs="+",
        help="URLs to analyze (space-separated)"
    )

    parser.add_argument(
        "--config",
        help="JSON file with competitor configurations"
    )

    parser.add_argument(
        "--analysis-type",
        default="basket_pages",
        help="Type of analysis from config.yaml (default: basket_pages)"
    )

    parser.add_argument(
        "--model",
        default="claude-sonnet-4-5-20250929",
        help="Claude model to use (default: claude-sonnet-4-5-20250929)"
    )

    args = parser.parse_args()

    # Load environment variables
    load_dotenv()
    api_key = os.getenv("ANTHROPIC_API_KEY")

    if not api_key:
        print("Error: ANTHROPIC_API_KEY not found in environment variables")
        print("Please create a .env file with your API key (see .env.example)")
        sys.exit(1)

    # Parse competitor list
    competitors = []

    if args.config:
        # Load from config file
        with open(args.config, 'r') as f:
            config_data = json.load(f)
            competitors = config_data.get("competitors", [])

    elif args.urls:
        # Create from URLs
        for url in args.urls:
            # Extract site name from URL
            from urllib.parse import urlparse
            parsed = urlparse(url)
            site_name = parsed.netloc.replace("www.", "").split(".")[0]

            competitors.append({
                "name": site_name,
                "url": url
            })

    else:
        # Default example competitors (for demo)
        console = Console()
        console.print("[yellow]No URLs or config file provided. Using example URLs for demo.[/yellow]")
        console.print("[yellow]Note: These may not have accessible basket pages.[/yellow]\n")

        competitors = [
            {"name": "example1", "url": "https://www.asos.com/basket"},
            {"name": "example2", "url": "https://www.zara.com/cart"}
        ]

    if not competitors:
        print("Error: No competitors to analyze")
        sys.exit(1)

    # Create orchestrator and run analysis
    console = Console()
    console.print(Panel.fit(
        "[bold cyan]E-commerce UX Analysis Agent[/bold cyan]\n\n"
        f"Analysis Type: {args.analysis_type}\n"
        f"Competitors: {len(competitors)}\n"
        f"Model: {args.model}",
        title="Starting Analysis"
    ))

    orchestrator = UXAnalysisOrchestrator(
        api_key=api_key,
        model=args.model,
        analysis_type=args.analysis_type
    )

    # Run analysis
    results = await orchestrator.analyze_competitors(competitors)

    # Generate reports
    report_paths = orchestrator.generate_reports(results)

    # Display summary
    orchestrator.display_summary(results)

    console.print(f"\n[bold green]All reports saved to:[/bold green] {Path('output').absolute()}")


if __name__ == "__main__":
    asyncio.run(main())
