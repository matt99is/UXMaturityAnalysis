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
from pathlib import Path
from main import UXAnalysisOrchestrator
from src.config_loader import AnalysisConfig
import json

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

    # Create orchestrator
    orchestrator = UXAnalysisOrchestrator(
        analysis_type=analysis_type,
        output_dir=str(audit_dir.parent)
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

    print(f"Reanalyzing {len(competitors_data)} competitors...\n")

    # Reuse the existing audit structure
    audit_structure = {
        'audit_root': str(audit_dir),
        'competitors': {comp['site_name']: str(audit_dir / comp['site_name']) for comp in competitors_data}
    }

    # Run Phase 2 analysis only
    print("═══ Phase 2: AI Analysis (Parallel) ═══")
    print("Claude will now analyze all captured screenshots concurrently\n")

    results = []
    analysis_tasks = [
        orchestrator.analyze_competitor_from_screenshots(comp_data)
        for comp_data in competitors_data
    ]

    # Run in parallel
    analysis_results = await asyncio.gather(*analysis_tasks, return_exceptions=True)

    # Process results
    for comp_data, analysis_result in zip(competitors_data, analysis_results):
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
