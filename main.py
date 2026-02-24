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
from datetime import datetime
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
from src.utils.html_report_generator import HTMLReportGenerator
from src.utils.audit_organizer import (
    extract_competitor_name,
    create_audit_directory_structure,
    get_screenshot_path,
    get_analysis_path,
    get_comparison_report_path,
    get_audit_summary_path,
    generate_audit_summary
)
from src.utils.page_type_detector import get_page_type_display_name
from src.version import __version__, __title__


class UXAnalysisOrchestrator:
    """
    Main orchestrator for UX analysis pipeline.

    EXTENSIBILITY NOTE: This class coordinates the analysis workflow
    and is designed to work with any analysis type defined in config.yaml.
    """

    def __init__(
        self,
        api_key: str,
        model: str = None,
        analysis_type: str = "basket_pages",
        config_path: str = "config.yaml",
        manual_mode: bool = False,
        screenshots_dir: str = None
    ):
        resolved_model = (
            model
            or os.getenv("CLAUDE_MODEL")
            or os.getenv("claude_model")
            or "claude-sonnet-4-5-20250929"
        )
        self.console = Console()
        self.analysis_config = AnalysisConfig(config_path)
        self.analysis_type_config = self.analysis_config.get_analysis_type(analysis_type)
        self.screenshot_capturer = ScreenshotCapture()
        self.claude_analyzer = ClaudeUXAnalyzer(api_key=api_key, model=resolved_model)
        self.report_generator = ReportGenerator()
        self.html_report_generator = HTMLReportGenerator()
        self.manual_mode = manual_mode
        self.screenshots_dir = screenshots_dir

    async def capture_competitor_screenshots(
        self,
        url: str,
        site_name: str,
        competitor_paths: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Capture screenshots for a single competitor.

        Args:
            url: URL to analyze
            site_name: Identifier for the competitor
            competitor_paths: Optional dict with screenshot and analysis paths

        Returns:
            Dictionary with screenshot paths and metadata, or error info
        """
        self.console.print(f"\n[bold cyan]Capturing:[/bold cyan] {site_name}")
        self.console.print(f"[dim]URL: {url}[/dim]")

        try:
            # Get screenshots (capture or load from directory)
            screenshot_config = self.analysis_type_config.screenshot_config
            interaction_config = self.analysis_type_config.interaction

            viewports = [
                {"name": vp.name, "width": vp.width, "height": vp.height}
                for vp in screenshot_config.viewports
            ]

            # Determine output directory for screenshots
            screenshots_dir = None
            if competitor_paths:
                screenshots_dir = competitor_paths['screenshots']

            # Screenshot capture with retry loop
            screenshot_retry = True
            screenshot_results = None
            successful_captures = None

            while screenshot_retry:
                # Manual mode: Load pre-captured screenshots
                if self.manual_mode:
                    self.console.print(f"  [magenta]📁 Manual mode: Loading screenshots from {self.screenshots_dir}[/magenta]")
                    screenshot_results = self.screenshot_capturer.load_screenshots_from_directory(
                        screenshots_dir=self.screenshots_dir,
                        site_name=site_name,
                        viewports=viewports
                    )
                else:
                    # Interactive mode - always use visible browser with user control
                    prompt_text = f"Navigate to the {self.analysis_type_config.name.lower()} and prepare for screenshot"
                    screenshot_results = await self.screenshot_capturer.capture_with_interaction(
                        url=url,
                        site_name=site_name,
                        viewports=viewports,
                        interaction_prompt=prompt_text,
                        interaction_instructions="Close popups, accept cookies, and ensure page is fully loaded",
                        timeout=300,  # 5 minutes
                        full_page=screenshot_config.full_page,
                        custom_output_dir=screenshots_dir
                    )

                # Check for capture failures
                failed_captures = [r for r in screenshot_results if not r.get("success")]
                blocked_captures = [r for r in failed_captures if r.get("blocked")]

                if blocked_captures:
                    # Site was blocked by bot detection
                    block_reason = blocked_captures[0].get("block_reason", "Unknown")
                    self.console.print(f"  [yellow]⚠ Bot detection: {block_reason}[/yellow]")

                if failed_captures:
                    self.console.print(f"  [red]Warning: {len(failed_captures)} screenshot(s) failed[/red]")

                successful_captures = [r for r in screenshot_results if r.get("success")]

                if not successful_captures:
                    error_msg = "All screenshot captures failed"
                    if blocked_captures:
                        error_msg = f"Site blocked by bot detection: {blocked_captures[0].get('block_reason', 'Unknown')}"

                    return {
                        "success": False,
                        "site_name": site_name,
                        "url": url,
                        "error": error_msg,
                        "blocked": bool(blocked_captures)
                    }

                screenshot_paths = [r["filepath"] for r in successful_captures]
                self.console.print(f"  [green]✓ Captured {len(screenshot_paths)} screenshot(s)[/green]")

                # Prompt user: Continue, Retry, or Skip
                if not self.manual_mode:
                    self.console.print()
                    while True:
                        try:
                            response = input("  Continue? ([Y]es / [r]etry / [s]kip): ").strip().lower()
                            if response in ['', 'y', 'yes']:
                                screenshot_retry = False
                                break
                            elif response in ['r', 'retry']:
                                self.console.print("  [yellow]↻ Retrying screenshot capture...[/yellow]\n")
                                break  # Continue retry loop
                            elif response in ['s', 'skip']:
                                self.console.print("  [yellow]⊘ Skipping this competitor[/yellow]")
                                return {
                                    "success": False,
                                    "site_name": site_name,
                                    "url": url,
                                    "error": "Skipped by user",
                                    "skipped": True
                                }
                            else:
                                self.console.print("  [red]Please enter 'y', 'r', or 's'[/red]")
                        except (EOFError, KeyboardInterrupt):
                            self.console.print("\n  [yellow]⊘ Cancelling entire analysis...[/yellow]")
                            raise  # Re-raise to break out of main loop
                else:
                    # Manual mode doesn't need retry
                    screenshot_retry = False

            # Return capture data for later analysis
            return {
                "success": True,
                "site_name": site_name,
                "url": url,
                "screenshot_paths": screenshot_paths,
                "screenshot_metadata": successful_captures,
                "competitor_paths": competitor_paths
            }

        except Exception as e:
            self.console.print(f"  [red]Error: {str(e)}[/red]")
            return {
                "success": False,
                "site_name": site_name,
                "url": url,
                "error": str(e)
            }

    async def _retry_failed_competitors(
        self,
        results: List[Dict[str, Any]],
        audit_structure: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Prompt user to retry failed competitor analyses using existing screenshots.

        Args:
            results: Current analysis results (including failures)
            audit_structure: Audit directory structure with screenshot locations

        Returns:
            Updated results list (with retried analyses if user accepted)
        """
        from rich.panel import Panel

        failed = [r for r in results if not r.get('success')]

        if not failed:
            return results

        # Show failure summary
        self.console.print()
        self.console.print(Panel.fit(
            f"[bold yellow]⚠️  {len(failed)} competitor(s) failed analysis:[/bold yellow]\n\n" +
            "\n".join([f"  • [bold]{r['site_name']}[/bold] - {r.get('error', 'Unknown error')}" for r in failed]),
            title="Analysis Failures",
            border_style="yellow"
        ))

        # Prompt for retry
        try:
            self.console.print()
            retry_input = input("Retry failed competitors now? ([Y]es / [n]o): ").strip().lower()
            if retry_input not in ['y', 'yes', '']:
                self.console.print("[dim]Proceeding without retry...[/dim]")
                return results
        except (EOFError, KeyboardInterrupt):
            self.console.print("\n[dim]Proceeding without retry...[/dim]")
            return results

        # Retry failed competitors sequentially
        self.console.print("\n[bold cyan]═══ Retrying Failed Analyses (Sequential) ═══[/bold cyan]")
        self.console.print(f"[dim]Using existing screenshots from audit folder[/dim]\n")

        # Separate successful from failed
        successful_results = [r for r in results if r.get('success')]

        # Delay between retries
        RETRY_DELAY = 60  # Wait 60 seconds between retries

        self.console.print(f"[bold]Retrying {len(failed)} failed competitor(s) sequentially...[/bold]")
        self.console.print(f"[dim]Rate limit protection: {RETRY_DELAY}s delay between retries[/dim]\n")

        retry_results = []
        skipped_failures = []

        for idx, result in enumerate(failed, 1):
            self.console.print(f"[cyan]Retry {idx}/{len(failed)}:[/cyan] {result['site_name']}")

            # Load screenshots from audit folder
            competitor_info = audit_structure['competitors'].get(result['site_name'])
            if not competitor_info:
                self.console.print(f"  [red]✗ Could not find competitor directory[/red]")
                skipped_failures.append(result)
                continue

            screenshots_dir = competitor_info['screenshots']
            screenshot_paths = [
                str(screenshots_dir / 'desktop.png'),
                str(screenshots_dir / 'mobile.png')
            ]

            # Check if screenshots exist
            from pathlib import Path
            if not all(Path(p).exists() for p in screenshot_paths):
                self.console.print(f"  [red]✗ Screenshots not found[/red]")
                skipped_failures.append(result)
                continue

            # Prepare capture data for retry
            capture_data = {
                'site_name': result['site_name'],
                'url': result['url'],
                'screenshot_paths': screenshot_paths,
                'screenshot_metadata': result.get('screenshot_metadata', [])
            }

            # Retry analysis
            try:
                retry_result = await self.analyze_competitor_from_screenshots(capture_data)
            except Exception as e:
                self.console.print(f"  [red]✗ {str(e)}[/red]")
                retry_results.append({
                    "success": False,
                    "site_name": result['site_name'],
                    "url": result['url'],
                    "error": str(e)
                })
                continue

            # Process retry result
            if retry_result.get("success"):
                self.console.print(f"  [green]✓ Success![/green]")

                # Save retry result
                if audit_structure:
                    try:
                        analysis_path = get_analysis_path(
                            audit_structure['competitors'],
                            result['site_name']
                        )
                        self.report_generator.save_competitor_analysis(
                            retry_result,
                            analysis_path
                        )
                    except Exception as e:
                        self.console.print(f"  [yellow]Warning: Could not save analysis: {e}[/yellow]")
            else:
                self.console.print(f"  [yellow]⚠ {retry_result.get('error', 'Unknown error')}[/yellow]")

            retry_results.append(retry_result)

            # Wait between retries (except for last one)
            if idx < len(failed):
                self.console.print(f"[dim]Waiting {RETRY_DELAY}s before next retry...[/dim]\n")
                await asyncio.sleep(RETRY_DELAY)

        # Combine all results
        updated_results = successful_results + retry_results + skipped_failures

        # Show retry summary
        retry_success_count = sum(1 for r in updated_results if r.get('success'))
        original_success_count = sum(1 for r in results if r.get('success'))
        new_successes = retry_success_count - original_success_count

        if new_successes > 0:
            self.console.print(f"\n[green]✓ {new_successes} competitor(s) successfully analyzed on retry![/green]")
        else:
            self.console.print(f"\n[yellow]No additional successes from retry[/yellow]")

        return updated_results

    async def analyze_competitor_from_screenshots(
        self,
        capture_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze a competitor using two-pass pipeline:
        - Pass 1: Observe screenshots → observation.json
        - Pass 2: Score against criteria using observation text (no images)

        If observation.json already exists for this competitor, pass 1 is skipped.
        """
        site_name = capture_data["site_name"]
        url = capture_data["url"]
        screenshot_paths = capture_data["screenshot_paths"]
        competitor_paths = capture_data.get("competitor_paths")

        self.console.print(f"\n[bold cyan]Analyzing:[/bold cyan] {site_name}")

        try:
            # Determine observation file path (if competitor_paths available)
            observation_path = None
            if competitor_paths:
                observation_path = Path(competitor_paths['root']) / "observation.json"

            # --- Pass 1: Observe ---
            observation = None

            # _skip_observe=True means reuse existing observation.json (set by reanalyze --force-observe=False)
            # _skip_observe=False means re-run pass 1 even if observation.json exists (--force-observe)
            # Default (not set): reuse if observation.json exists
            use_existing = (
                observation_path is not None
                and observation_path.exists()
                and capture_data.get('_skip_observe', True)
            )

            if use_existing:
                self.console.print(f"  [dim]↻ Loading existing observation from {observation_path.name}[/dim]")
                try:
                    with open(observation_path, 'r') as f:
                        observation = json.load(f)
                except (json.JSONDecodeError, OSError) as exc:
                    self.console.print(
                        f"  [yellow]⚠ Existing observation invalid ({exc}); re-running pass 1[/yellow]"
                    )
                    use_existing = False

            if not use_existing:
                self.console.print(f"  [cyan]Pass 1: Observing screenshots...[/cyan]")
                observation_focus = list(getattr(self.analysis_type_config, 'observation_focus', []))

                observe_result = await self.claude_analyzer._observe_screenshots(
                    screenshot_paths=screenshot_paths,
                    analysis_name=self.analysis_type_config.name,
                    observation_focus=observation_focus,
                    site_name=site_name,
                    url=url
                )

                if not observe_result.get("success"):
                    self.console.print(f"  [red]Observation failed: {observe_result.get('error')}[/red]")
                    return {
                        "success": False,
                        "site_name": site_name,
                        "url": url,
                        "error": f"Pass 1 observation failed: {observe_result.get('error')}",
                        "screenshots": screenshot_paths
                    }

                observation = observe_result["observation"]

                # Save observation.json
                if observation_path:
                    observation_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(observation_path, 'w') as f:
                        json.dump(observation, f, indent=2)
                    self.console.print(f"  [green]✓ Observation saved ({len(observation.get('notable_states', []))} notable states)[/green]")
                else:
                    self.console.print(f"  [green]✓ Observation complete ({len(observation.get('notable_states', []))} notable states)[/green]")

            # Surface notable states to console
            notable = observation.get("notable_states", [])
            if notable:
                self.console.print(f"  [yellow]Notable states:[/yellow]")
                for state in notable:
                    self.console.print(f"    [yellow]• {state}[/yellow]")

            # --- Pass 2: Score ---
            self.console.print(f"  [cyan]Pass 2: Scoring against criteria...[/cyan]")

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
                url=url,
                analysis_context=self.analysis_type_config.analysis_context,
                observation=observation
            )

            if not analysis_result.get("success"):
                self.console.print(f"  [red]Scoring failed: {analysis_result.get('error')}[/red]")
                return {
                    "success": False,
                    "site_name": site_name,
                    "url": url,
                    "error": analysis_result.get("error"),
                    "screenshots": screenshot_paths
                }

            # Add observation reference to analysis result
            result_data = analysis_result["analysis"]
            result_data["observation_file"] = str(observation_path) if observation_path else None
            result_data["screenshots_analyzed"] = screenshot_paths
            result_data["model_used"] = self.claude_analyzer.model

            self.console.print(f"  [green]✓ Analysis complete[/green]")

            # Save analysis.json if competitor_paths available
            if competitor_paths:
                analysis_file_path = Path(competitor_paths['root']) / "analysis.json"
                with open(analysis_file_path, 'w') as f:
                    json.dump(result_data, f, indent=2)

            return {
                "success": True,
                "site_name": site_name,
                "url": url,
                "screenshot_paths": screenshot_paths,
                "screenshot_metadata": capture_data.get("screenshot_metadata", []),
                **result_data
            }

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
        competitors: List[Dict[str, str]],
        audit_structure: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Analyze multiple competitors with organized output structure.

        Args:
            competitors: List of dicts with 'name' and 'url' keys
            audit_structure: Optional audit directory structure from audit_organizer

        Returns:
            List of analysis results

        EXTENSIBILITY NOTE: This could be extended to analyze competitors
        in parallel for faster execution, or to implement rate limiting.
        """
        # Initialize browser in visible mode for interactive capture
        # Skip browser initialization if in manual mode
        if not self.manual_mode:
            await self.screenshot_capturer.initialize_browser(headless=False)

        total = len(competitors)

        # PHASE 1: Capture all screenshots
        self.console.print("\n[bold cyan]═══ Phase 1: Screenshot Capture ═══[/bold cyan]")
        self.console.print("[dim]You'll interact with each competitor site to capture screenshots[/dim]\n")

        captured_data = []

        try:
            for i, competitor in enumerate(competitors, 1):
                mode_str = "manual" if self.manual_mode else "interactive"
                self.console.print(f"\n[bold]Progress: {i}/{total}[/bold] [dim]({mode_str})[/dim]")

                # Get competitor-specific paths if audit structure provided
                competitor_paths = None
                if audit_structure:
                    comp_name = competitor['name']
                    if comp_name in audit_structure['competitors']:
                        competitor_paths = audit_structure['competitors'][comp_name]

                # Capture screenshots
                capture_result = await self.capture_competitor_screenshots(
                    url=competitor["url"],
                    site_name=competitor["name"],
                    competitor_paths=competitor_paths
                )

                captured_data.append(capture_result)

            # Close browser after all captures complete
            if not self.manual_mode:
                await self.screenshot_capturer.close_browser()

            # PHASE 2: Analyze all screenshots sequentially
            self.console.print("\n[bold cyan]═══ Phase 2: AI Analysis (Sequential) ═══[/bold cyan]")
            self.console.print("[dim]Claude will analyze screenshots one at a time[/dim]\n")

            # Separate successful captures from failed ones
            successful_captures = [d for d in captured_data if d.get("success")]
            failed_captures = [d for d in captured_data if not d.get("success")]

            # Delay between analyses to respect 8,000 output tokens/min rate limit
            # With max_tokens=6000, we need 1 per minute minimum (60s delay)
            ANALYSIS_DELAY = 90  # Two-pass: ~9000 output tokens per competitor, 8000/min limit

            self.console.print(f"[bold]Analyzing {len(successful_captures)} competitors sequentially...[/bold]")
            self.console.print(f"[dim]Rate limit protection: {ANALYSIS_DELAY}s delay between analyses[/dim]\n")

            # Analyze competitors sequentially
            processed_results = []
            if successful_captures:
                try:
                    for idx, capture_data in enumerate(successful_captures, 1):
                        self.console.print(f"[cyan]Analyzing {idx}/{len(successful_captures)}:[/cyan] {capture_data['site_name']}")

                        # Analyze this competitor
                        try:
                            analysis_result = await self.analyze_competitor_from_screenshots(capture_data)
                        except Exception as e:
                            self.console.print(f"  [red]✗ {capture_data['site_name']}: {str(e)}[/red]")
                            processed_results.append({
                                "success": False,
                                "site_name": capture_data['site_name'],
                                "url": capture_data['url'],
                                "error": str(e)
                            })
                            continue

                        # Process result
                        if analysis_result.get("success"):
                            self.console.print(f"  [green]✓ {capture_data['site_name']}[/green]")
                        else:
                            self.console.print(f"  [yellow]⚠ {capture_data['site_name']}: {analysis_result.get('error', 'Unknown error')}[/yellow]")

                        processed_results.append(analysis_result)

                        # Save individual competitor analysis if audit structure provided
                        if audit_structure and analysis_result.get("success"):
                            try:
                                analysis_path = get_analysis_path(
                                    audit_structure['competitors'],
                                    capture_data['site_name']
                                )
                                self.report_generator.save_competitor_analysis(
                                    analysis_result,
                                    analysis_path
                                )
                            except Exception as e:
                                self.console.print(f"  [yellow]Warning: Could not save {capture_data['site_name']}: {e}[/yellow]")

                        # Wait between analyses (except for last one)
                        if idx < len(successful_captures):
                            self.console.print(f"[dim]Waiting {ANALYSIS_DELAY}s before next analysis...[/dim]\n")
                            await asyncio.sleep(ANALYSIS_DELAY)

                    # Combine failed captures with processed analysis results
                    results = failed_captures + processed_results

                except (EOFError, KeyboardInterrupt):
                    self.console.print("\n\n[bold yellow]⚠ Analysis cancelled by user[/bold yellow]")
                    # Return partial results up to this point
                    results = failed_captures + processed_results
                    raise  # Re-raise to be caught by outer handler

            else:
                # No successful captures to analyze
                results = failed_captures

            self.console.print(f"\n[bold green]✓ Sequential analysis complete![/bold green]")

            # PHASE 2.5: Retry failed analyses if any
            failed_results = [r for r in results if not r.get('success')]
            if failed_results and audit_structure:
                results = await self._retry_failed_competitors(results, audit_structure)

        finally:
            # Ensure browser is closed
            if not self.manual_mode:
                try:
                    await self.screenshot_capturer.close_browser()
                except:
                    pass

        return results

    def generate_reports(
        self,
        results: List[Dict[str, Any]],
        audit_structure: Dict[str, Any] = None,
        audit_summary: Dict[str, Any] = None
    ) -> Dict[str, str]:
        """
        Generate JSON, markdown, and HTML reports with new audit structure.

        Args:
            results: List of analysis results
            audit_structure: Optional audit directory structure
            audit_summary: Optional audit summary data

        Returns:
            Dictionary with paths to generated reports
        """
        self.console.print("\n[bold cyan]Generating reports...[/bold cyan]")

        # If audit structure provided, use new organized format
        if audit_structure:
            audit_root = audit_structure['audit_root']

            # Generate comparison markdown report
            md_path = self.report_generator.generate_markdown_report(
                results,
                filepath=get_comparison_report_path(audit_root)
            )
            self.console.print(f"[green]Comparison report:[/green] {md_path}")

            # Generate interactive HTML report
            try:
                html_filename = f"{audit_root.name}_report.html"
                html_output_path = audit_root / html_filename

                # Temporarily override output_dir to write to audit_root
                original_output_dir = self.html_report_generator.output_dir
                self.html_report_generator.output_dir = audit_root

                html_path = self.html_report_generator.generate_html_report(
                    results=results,
                    analysis_type=self.analysis_type_config.name,
                    output_filename=html_filename
                )

                # Restore original output_dir
                self.html_report_generator.output_dir = original_output_dir

                self.console.print(f"[green]📊 Interactive HTML report:[/green] {html_path}")
            except Exception as e:
                self.console.print(f"[yellow]Warning: Could not generate HTML report: {e}[/yellow]")
                html_path = None

            # Save audit summary
            if audit_summary:
                summary_path = self.report_generator.save_audit_summary(
                    audit_summary,
                    get_audit_summary_path(audit_root)
                )
                self.console.print(f"[green]Audit summary:[/green] {summary_path}")

            return {
                "markdown": md_path,
                "html": html_path,
                "summary": summary_path if audit_summary else None,
                "audit_root": str(audit_root)
            }
        else:
            # Legacy flat structure (backward compatibility)
            json_path = self.report_generator.save_json_report(results)
            self.console.print(f"[green]JSON report saved:[/green] {json_path}")

            md_path = self.report_generator.generate_markdown_report(results)
            self.console.print(f"[green]Markdown report saved:[/green] {md_path}")

            # Generate HTML report
            try:
                html_path = self.html_report_generator.generate_html_report(
                    results=results,
                    analysis_type="UX Analysis"
                )
                self.console.print(f"[green]📊 Interactive HTML report:[/green] {html_path}")
            except Exception as e:
                self.console.print(f"[yellow]Warning: Could not generate HTML report: {e}[/yellow]")
                html_path = None

            return {
                "json": json_path,
                "markdown": md_path,
                "html": html_path
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

            # Sort by score (data is now flattened)
            sorted_results = sorted(
                successful,
                key=lambda x: x.get("overall_score", 0),
                reverse=True
            )

            for i, result in enumerate(sorted_results, 1):
                score = result.get("overall_score", 0)
                table.add_row(
                    str(i),
                    result.get("site_name", "Unknown"),
                    f"{score:.1f}/10"
                )

            self.console.print(table)


async def main():
    """Main entry point for the UX analysis tool."""
    parser = argparse.ArgumentParser(
        description=f"{__title__} v{__version__}",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --urls https://shop1.com/basket https://shop2.com/cart
  python main.py --config competitors.json
  python main.py --analysis-type homepage_pages --urls https://example.com

For more examples and documentation, see README.md
        """
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"{__title__} v{__version__}"
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
        default=None,
        help="Type of analysis (prompt if not specified). Options: homepage_pages, product_pages, basket_pages, checkout_pages"
    )

    parser.add_argument(
        "--model",
        default=None,
        help=(
            "Claude model to use (default: CLAUDE_MODEL/claude_model from .env, "
            "then claude-sonnet-4-5-20250929)"
        )
    )

    parser.add_argument(
        "--manual-mode",
        action="store_true",
        help="Manual mode: Load pre-captured screenshots instead of browser automation"
    )

    parser.add_argument(
        "--screenshots-dir",
        default="./manual-screenshots",
        help="Directory containing manually captured screenshots (used with --manual-mode)"
    )

    args = parser.parse_args()

    # Load environment variables
    load_dotenv()
    api_key = os.getenv("ANTHROPIC_API_KEY")

    if not api_key:
        print("Error: ANTHROPIC_API_KEY not found in environment variables")
        print("Please create a .env file with your API key (see .env.example)")
        sys.exit(1)

    selected_model = (
        args.model
        or os.getenv("CLAUDE_MODEL")
        or os.getenv("claude_model")
        or "claude-sonnet-4-5-20250929"
    )

    # Parse competitor list
    competitors = []

    if args.config:
        # Load from config file
        with open(args.config, 'r') as f:
            config_data = json.load(f)
            competitors = config_data.get("competitors", [])

    elif args.urls:
        # Create from URLs using improved name extraction
        for url in args.urls:
            site_name = extract_competitor_name(url)

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

    # Always prompt user for analysis type (auto-detection removed for reliability)
    console = Console()
    analysis_type = args.analysis_type

    # Function to prompt user for analysis type
    def prompt_for_analysis_type(config: AnalysisConfig) -> str:
        """Display interactive menu to select analysis type."""
        available_types = config.list_available_analysis_types()

        console.print()
        console.print("[bold cyan]📋 Select Analysis Type:[/bold cyan]\n")

        # Create table of options
        table = Table(show_header=True, header_style="bold cyan", box=None)
        table.add_column("#", style="dim", width=3)
        table.add_column("Analysis Type", style="cyan")
        table.add_column("Description", style="dim")

        type_map = {
            "homepage_pages": ("Homepage", "Analyze homepage UX and layout"),
            "product_pages": ("Product Pages", "Analyze product detail pages"),
            "basket_pages": ("Basket/Cart", "Analyze shopping cart pages"),
            "checkout_pages": ("Checkout Flow", "Analyze checkout process")
        }

        for idx, analysis_type_key in enumerate(available_types, 1):
            display_name, description = type_map.get(
                analysis_type_key,
                (get_page_type_display_name(analysis_type_key), "Custom analysis type")
            )
            table.add_row(str(idx), display_name, description)

        console.print(table)
        console.print()

        # Get user input
        while True:
            try:
                choice = input("Select analysis type (1-{}): ".format(len(available_types)))
                choice_idx = int(choice) - 1

                if 0 <= choice_idx < len(available_types):
                    selected = available_types[choice_idx]
                    display_name = get_page_type_display_name(selected)
                    console.print(f"[green]✓ Selected:[/green] {display_name}\n")
                    return selected
                else:
                    console.print(f"[red]Please enter a number between 1 and {len(available_types)}[/red]")
            except ValueError:
                console.print("[red]Please enter a valid number[/red]")
            except KeyboardInterrupt:
                console.print("\n[yellow]Analysis cancelled[/yellow]")
                sys.exit(0)

    # Always prompt for analysis type unless explicitly provided via CLI
    if not analysis_type:
        temp_config = AnalysisConfig()
        analysis_type = prompt_for_analysis_type(temp_config)

    # Create orchestrator and run analysis
    mode_desc = "Manual Screenshots" if args.manual_mode else "Interactive Mode"
    console.print(Panel.fit(
        "[bold cyan]E-commerce UX Analysis Agent[/bold cyan]\n\n"
        f"Analysis Type: {get_page_type_display_name(analysis_type)}\n"
        f"Competitors: {len(competitors)}\n"
        f"Mode: {mode_desc}\n"
        f"Model: {selected_model}"
        + (f"\n[magenta]Screenshots Dir: {args.screenshots_dir}[/magenta]" if args.manual_mode else ""),
        title="Starting Analysis"
    ))

    if not args.manual_mode:
        console.print("[cyan]🌐 Interactive Mode:[/cyan] Browser will open for each site")
        console.print("[dim]Navigate to the page, close popups, then press Enter to capture[/dim]\n")

    if args.manual_mode:
        console.print(f"\n[magenta]📁 Manual Mode Enabled:[/magenta]")
        console.print(f"[dim]Loading screenshots from: {args.screenshots_dir}[/dim]")
        console.print(f"[dim]Expected files: {{competitor}}_desktop.png, {{competitor}}_mobile.png[/dim]\n")

    orchestrator = UXAnalysisOrchestrator(
        api_key=api_key,
        model=selected_model,
        analysis_type=analysis_type,
        manual_mode=args.manual_mode,
        screenshots_dir=args.screenshots_dir
    )

    # Create audit directory structure
    start_time = datetime.now()
    audit_structure = create_audit_directory_structure(
        base_dir="output",
        analysis_type=analysis_type,
        competitors=competitors
    )

    try:
        # Run analysis
        results = await orchestrator.analyze_competitors(competitors, audit_structure)

        # Calculate timing for audit summary
        end_time = datetime.now()
        successful = [r for r in results if r.get("success")]
        failed = [r for r in results if not r.get("success")]

        # Generate audit summary metadata
        audit_summary = generate_audit_summary(
            analysis_type=analysis_type,
            analysis_type_name=orchestrator.analysis_type_config.name,
            competitors=competitors,
            successful_count=len(successful),
            failed_count=len(failed),
            start_time=start_time,
            end_time=end_time
        )

        # Generate reports
        report_paths = orchestrator.generate_reports(results, audit_structure, audit_summary)

        # Display summary
        orchestrator.display_summary(results)

        # Update Resources index if configured
        try:
            from src.utils.audit_organizer import get_resources_config
            import subprocess

            resources_config = get_resources_config()
            if resources_config and resources_config.get('update_index', True):
                console.print("\n[cyan]🔄 Updating Resources index...[/cyan]")
                update_script = Path(__file__).parent / "scripts" / "update_resources_index.py"
                result = subprocess.run([sys.executable, str(update_script)], capture_output=True, text=True)
                if result.returncode == 0:
                    console.print("[green]✅ Resources index updated![/green]")
                else:
                    console.print(f"[yellow]⚠️  Index update had issues: {result.stderr}[/yellow]")
        except Exception as e:
            console.print(f"[dim]Note: Could not update Resources index: {e}[/dim]")

        # Show new organized output structure
        audit_root = audit_structure['audit_root']
        console.print(f"\n[bold green]✅ Analysis complete![/bold green]\n")
        console.print(f"[bold]Results saved to:[/bold] [cyan]{audit_root}[/cyan]\n")

        if successful:
            console.print("[bold]Competitors analyzed:[/bold]")
            for comp in successful:
                comp_name = comp.get('site_name', 'unknown')
                comp_path = audit_root / comp_name
                console.print(f"  • {comp_name} [dim]({comp_path})[/dim]")

        console.print(f"\n[bold]Comparison report:[/bold] [cyan]{audit_root / '_comparison_report.md'}[/cyan]")

    except (EOFError, KeyboardInterrupt):
        console.print("\n\n[bold yellow]⚠ Analysis cancelled by user[/bold yellow]")
        console.print(f"[dim]Partial results (if any) saved to: {audit_structure['audit_root']}[/dim]")
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
