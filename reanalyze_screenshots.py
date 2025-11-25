#!/usr/bin/env python3
"""
Reanalyze existing screenshots without re-capturing.

Usage:
    python3 reanalyze_screenshots.py <audit_folder>

Example:
    python3 reanalyze_screenshots.py output/audits/2025-11-24_basket_pages
"""

import asyncio
import sys
import os
import json
from pathlib import Path
from dotenv import load_dotenv
from main import UXAnalysisOrchestrator
from src.config_loader import AnalysisConfig

# Load environment variables from .env file
load_dotenv()

async def reanalyze_audit(audit_path: str):
    """Reanalyze all competitors in an existing audit folder."""

    audit_dir = Path(audit_path)
    if not audit_dir.exists():
        print(f"Error: Audit directory not found: {audit_path}")
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

        print(f"No audit summary found. Inferring analysis type from folder name: {analysis_type}")

        # Create minimal audit summary
        audit_summary = {
            'analysis_type': analysis_type,
            'timestamp': folder_name.split('_')[0] if '_' in folder_name else 'unknown',
            'created_by': 'reanalysis_script'
        }

    print(f"Analysis type: {analysis_type}")

    # Load config for analysis type
    config = AnalysisConfig()
    analysis_type_config = config.get_analysis_type(analysis_type)

    if not analysis_type_config:
        print(f"Error: Analysis type '{analysis_type}' not found in config")
        return

    # Find all competitor folders
    competitor_folders = [d for d in audit_dir.iterdir() if d.is_dir() and not d.name.startswith('_')]

    print(f"Found {len(competitor_folders)} competitors to reanalyze\n")

    # Get API key from environment
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable not set")
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
            print(f"Skipping {comp_folder.name}: No screenshots folder")
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
            print(f"Skipping {comp_folder.name}: No screenshots found")
            continue

        competitors_data.append({
            "success": True,
            "site_name": comp_folder.name,
            "url": f"https://{comp_folder.name}",  # Reconstruct URL
            "screenshot_paths": screenshots,
            "timestamp": audit_summary.get('timestamp', 'unknown')
        })

    # Reuse the existing audit structure
    audit_structure = {
        'audit_root': audit_dir,  # Keep as Path object, not string
        'competitors': {comp['site_name']: audit_dir / comp['site_name'] for comp in competitors_data}
    }

    # Check which competitors already have analysis.json
    needs_analysis = []
    existing_results = []

    for comp_data in competitors_data:
        analysis_path = audit_dir / comp_data['site_name'] / "analysis.json"
        if analysis_path.exists():
            # Load existing analysis
            with open(analysis_path, 'r') as f:
                existing_analysis = json.load(f)
            existing_results.append(existing_analysis)
            print(f"  [↻] {comp_data['site_name']}: Using existing analysis")
        else:
            needs_analysis.append(comp_data)

    print(f"\nFound {len(existing_results)} existing analyses, need to analyze {len(needs_analysis)} competitors\n")

    results = existing_results.copy()

    # Only run AI analysis for competitors that don't have analysis.json
    if needs_analysis:
        print("═══ Phase 2: AI Analysis (Parallel) ═══")
        print(f"Analyzing {len(needs_analysis)} competitors concurrently...\n")

        analysis_tasks = [
            orchestrator.analyze_competitor_from_screenshots(comp_data)
            for comp_data in needs_analysis
        ]

        # Run in parallel
        analysis_results = await asyncio.gather(*analysis_tasks, return_exceptions=True)

        # Process results
        for comp_data, analysis_result in zip(needs_analysis, analysis_results):
            if isinstance(analysis_result, Exception):
                print(f"  [✗] {comp_data['site_name']}: {str(analysis_result)}")
                results.append({
                    "success": False,
                    "site_name": comp_data['site_name'],
                    "url": comp_data['url'],
                    "error": str(analysis_result)
                })
            else:
                if analysis_result.get("success"):
                    print(f"  [✓] {comp_data['site_name']}")

                    # Save analysis to individual folder
                    analysis_path = Path(audit_structure['competitors'][comp_data['site_name']]) / "analysis.json"
                    with open(analysis_path, 'w') as f:
                        json.dump(analysis_result, f, indent=2)
                else:
                    print(f"  [⚠] {comp_data['site_name']}: {analysis_result.get('error', 'Unknown error')}")

                results.append(analysis_result)
    else:
        print("All competitors already have analysis.json - skipping AI analysis")

    print(f"\n✓ Reanalysis complete!")

    # Generate reports
    print("\nGenerating reports...")
    report_paths = orchestrator.generate_reports(
        results=results,
        audit_structure=audit_structure,
        audit_summary=audit_summary
    )

    print(f"\n✓ Reports generated:")
    for report_type, path in report_paths.items():
        print(f"  - {report_type}: {path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    audit_path = sys.argv[1]
    asyncio.run(reanalyze_audit(audit_path))
