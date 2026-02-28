#!/usr/bin/env python3
"""
Reanalyze existing screenshots without re-capturing.

Usage:
    python3 scripts/reanalyze_screenshots.py <audit_folder>
    python3 scripts/reanalyze_screenshots.py <audit_folder> --force-observe
    python3 scripts/reanalyze_screenshots.py <audit_folder> --force

Example:
    python3 scripts/reanalyze_screenshots.py output/audits/2025-11-24_basket_pages
"""

import asyncio
import sys
import os
import json
from pathlib import Path
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
from rich.console import Console

# Add parent directory to path so we can import from main and src
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from main import UXAnalysisOrchestrator
from src.config_loader import AnalysisConfig

# Load environment variables from .env file
load_dotenv()

async def reanalyze_audit(
    audit_path: str,
    force_observe: bool = False,
    force: bool = False,
):
    """Reanalyze all competitors in an existing audit folder."""

    audit_dir = Path(audit_path)
    console = Console()
    if not audit_dir.exists():
        console.print(f"Error: Audit directory not found: {audit_path}")
        return

    # Load audit summary if exists, otherwise create minimal one
    summary_path = audit_dir / "_audit_summary.json"
    if summary_path.exists():
        with open(summary_path, 'r') as f:
            audit_summary = json.load(f)
        analysis_type = audit_summary.get('analysis_type', 'basket_pages')
    else:
        # Infer analysis type from folder name
        folder_name = audit_dir.name
        if 'basket' in folder_name or 'cart' in folder_name:
            analysis_type = 'basket_pages'
        elif 'product' in folder_name:
            analysis_type = 'product_pages'
        elif 'checkout' in folder_name:
            analysis_type = 'checkout_pages'
        elif 'homepage' in folder_name:
            analysis_type = 'homepage_pages'
        else:
            analysis_type = 'basket_pages'  # Default

        console.print(f"No audit summary found. Inferring analysis type from folder name: {analysis_type}")

        # Create minimal audit summary
        audit_summary = {
            'analysis_type': analysis_type,
            'timestamp': folder_name.split('_')[0] if '_' in folder_name else 'unknown',
            'created_by': 'reanalysis_script'
        }

    console.print(f"Analysis type: {analysis_type}")

    # Load config for analysis type
    config = AnalysisConfig()
    analysis_type_config = config.get_analysis_type(analysis_type)

    if not analysis_type_config:
        console.print(f"Error: Analysis type '{analysis_type}' not found in config")
        return

    # Find all competitor folders
    competitor_folders = [d for d in audit_dir.iterdir() if d.is_dir() and not d.name.startswith('_')]

    console.print(f"Found {len(competitor_folders)} competitors to reanalyze\n")

    # Get API key from environment
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        console.print("Error: ANTHROPIC_API_KEY environment variable not set")
        return

    # Create orchestrator
    orchestrator = UXAnalysisOrchestrator(
        api_key=api_key,
        analysis_type=analysis_type
    )

    # Build competitor data from existing screenshots
    competitors_data = []
    for comp_folder in competitor_folders:
        screenshots_dir = comp_folder / "screenshots"
        if not screenshots_dir.exists():
            console.print(f"Skipping {comp_folder.name}: No screenshots folder")
            continue

        # Find screenshot files
        desktop_shot = screenshots_dir / "desktop.png"
        mobile_shot = screenshots_dir / "mobile.png"

        screenshots = []
        if desktop_shot.exists():
            screenshots.append(str(desktop_shot))
        if mobile_shot.exists():
            screenshots.append(str(mobile_shot))

        if not screenshots:
            console.print(f"Skipping {comp_folder.name}: No screenshots found")
            continue

        competitors_data.append({
            "success": True,
            "site_name": comp_folder.name,
            "url": f"https://{comp_folder.name}",  # Reconstruct URL
            "screenshot_paths": screenshots,
            "timestamp": audit_summary.get('timestamp', 'unknown')
        })

    # Reuse the existing audit structure (match format from create_audit_directory_structure)
    competitor_paths = {}
    for comp in competitors_data:
        comp_name = comp['site_name']
        comp_root = audit_dir / comp_name
        comp_screenshots = comp_root / "screenshots"

        competitor_paths[comp_name] = {
            'root': comp_root,
            'screenshots': comp_screenshots
        }

    audit_structure = {
        'audit_root': audit_dir,  # Keep as Path object, not string
        'competitors': competitor_paths
    }

    for comp in competitors_data:
        comp['competitor_paths'] = competitor_paths.get(comp['site_name'])

    # Check which competitors need (re)analysis
    needs_analysis = []
    existing_results = []

    for comp_data in competitors_data:
        comp_dir = audit_dir / comp_data['site_name']
        analysis_path = comp_dir / "analysis.json"
        observation_path = comp_dir / "observation.json"

        if not force and analysis_path.exists():
            # Load existing analysis (skip both passes)
            with open(analysis_path, 'r') as f:
                existing_analysis = json.load(f)

            # Mark as successful for report generator
            existing_analysis["success"] = True

            # Inject competitor_root so report generators can resolve relative observation_file
            existing_analysis["competitor_root"] = str(comp_dir)

            if not existing_analysis.get('screenshot_metadata') and existing_analysis.get('screenshots_analyzed'):
                screenshot_metadata = []
                for screenshot_path in existing_analysis['screenshots_analyzed']:
                    screenshot_file = Path(screenshot_path)
                    viewport = 'mobile' if 'mobile' in screenshot_file.name else 'desktop'
                    screenshot_metadata.append({
                        'filepath': str(screenshot_path),
                        'viewport': viewport
                    })
                existing_analysis['screenshot_metadata'] = screenshot_metadata

            existing_results.append(existing_analysis)
            console.print(f"  [↻] {comp_data['site_name']}: Using existing analysis")
        else:
            comp_data['_skip_observe'] = (not force_observe) and observation_path.exists()
            if comp_data['_skip_observe']:
                console.print(
                    f"  [→] {comp_data['site_name']}: Will skip observation "
                    "(observation.json exists)"
                )
            elif force_observe and observation_path.exists():
                console.print(f"  [→] {comp_data['site_name']}: Will re-observe (--force-observe)")
            needs_analysis.append(comp_data)

    console.print(f"\nFound {len(existing_results)} existing analyses, need to analyze {len(needs_analysis)} competitors\n")

    results = existing_results.copy()

    # Only run AI analysis for competitors that don't have analysis.json
    if needs_analysis:
        # Delay between analyses to respect 8,000 output tokens/min rate limit
        ANALYSIS_DELAY = 90  # Two-pass: ~9000 output tokens per competitor, 8000/min limit

        console.print("\n[bold cyan]═══ Phase 2: AI Analysis (Sequential) ═══[/bold cyan]")
        console.print(f"[bold]Analyzing {len(needs_analysis)} competitors sequentially...[/bold]")
        console.print(f"[dim]Rate limit protection: {ANALYSIS_DELAY}s delay between analyses[/dim]\n")

        with Progress(
            SpinnerColumn(),
            TextColumn("[bold cyan]Analyzing competitors[/bold cyan]"),
            BarColumn(),
            TextColumn("{task.completed}/{task.total}"),
            TextColumn("[dim]{task.description}[/dim]"),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            task_id = progress.add_task("", total=len(needs_analysis))

            for idx, comp_data in enumerate(needs_analysis, 1):
                progress.console.print(
                    f"[cyan]Analyzing {idx}/{len(needs_analysis)}:[/cyan] {comp_data['site_name']}"
                )

                try:
                    analysis_result = await orchestrator.analyze_competitor_from_screenshots(
                        comp_data, progress=progress, task_id=task_id
                    )
                except Exception as e:
                    progress.console.print(f"  [red]✗ {str(e)}[/red]")
                    results.append({
                        "success": False,
                        "site_name": comp_data['site_name'],
                        "url": comp_data['url'],
                        "error": str(e)
                    })
                    progress.update(task_id, advance=1)
                    continue

                if analysis_result.get("success"):
                    progress.console.print(f"  [green]✓ {comp_data['site_name']}[/green]")
                else:
                    progress.console.print(
                        f"  [yellow]⚠ {analysis_result.get('error', 'Unknown error')}[/yellow]"
                    )

                results.append(analysis_result)
                progress.update(task_id, advance=1)

                if idx < len(needs_analysis):
                    next_name = needs_analysis[idx]['site_name']
                    await orchestrator._wait_with_countdown(
                        ANALYSIS_DELAY, next_name, progress=progress, task_id=task_id
                    )
    else:
        console.print("All competitors already have analysis.json - skipping AI analysis")

    console.print(f"\n✓ Reanalysis complete!")

    # Generate reports
    console.print("\nGenerating reports...")
    report_paths = orchestrator.generate_reports(
        results=results,
        audit_structure=audit_structure,
        audit_summary=audit_summary
    )

    console.print(f"\n✓ Reports generated:")
    for report_type, path in report_paths.items():
        console.print(f"  - {report_type}: {path}")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("audit_folder", help="Path to the audit folder to reanalyze")
    parser.add_argument(
        "--force-observe",
        action="store_true",
        help="Re-run pass 1 (observation) even if observation.json exists",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-run both passes even if analysis.json exists",
    )
    args = parser.parse_args()

    asyncio.run(
        reanalyze_audit(
            args.audit_folder,
            force_observe=args.force_observe,
            force=args.force,
        )
    )
