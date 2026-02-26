#!/usr/bin/env python3
"""Generate a modern example report from a legacy Resources audit folder."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List


def _load_competitor_result(
    competitor_dir: Path,
    copied_assets_dir: Path | None = None,
) -> Dict[str, Any] | None:
    analysis_path = competitor_dir / "analysis.json"
    if not analysis_path.exists():
        return None

    try:
        with open(analysis_path, "r", encoding="utf-8") as f:
            result = json.load(f)
    except (OSError, json.JSONDecodeError):
        return None

    if not isinstance(result, dict):
        return None

    # Rebuild screenshot metadata from raw screenshots only.
    screenshot_metadata: List[Dict[str, str]] = []
    screenshot_dir = competitor_dir / "screenshots"
    for viewport_name, filename in (("Desktop", "desktop.png"), ("Mobile", "mobile.png")):
        screenshot_path = screenshot_dir / filename
        if screenshot_path.exists():
            resolved_path = screenshot_path
            if copied_assets_dir is not None:
                target_dir = copied_assets_dir / competitor_dir.name / "screenshots"
                target_dir.mkdir(parents=True, exist_ok=True)
                target_path = target_dir / filename
                shutil.copy2(screenshot_path, target_path)
                resolved_path = target_path

            screenshot_metadata.append(
                {
                    "viewport_name": viewport_name,
                    "filepath": str(resolved_path),
                }
            )

    result["screenshot_metadata"] = screenshot_metadata
    result["success"] = bool(result.get("success", True))

    return result


def build_results_from_audit(
    audit_dir: Path,
    copied_assets_dir: Path | None = None,
) -> List[Dict[str, Any]]:
    """Load all competitor analysis results from a Resources audit directory."""
    results: List[Dict[str, Any]] = []

    if not audit_dir.exists():
        raise FileNotFoundError(f"Audit directory not found: {audit_dir}")

    for entry in sorted(audit_dir.iterdir()):
        if not entry.is_dir() or entry.name.startswith("_"):
            continue
        result = _load_competitor_result(entry, copied_assets_dir=copied_assets_dir)
        if result:
            results.append(result)

    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-audit",
        default="../Resources/ux-analysis/2025-11-24_basket_pages",
        help="Path to legacy Resources audit folder",
    )
    parser.add_argument(
        "--output-filename",
        default="resources-basket-pages-example-report.html",
        help="Output HTML filename inside UXMaturityAnalysis/output",
    )
    parser.add_argument(
        "--report-title",
        default="Basket Pages Analysis (Reference Dataset)",
        help="Report title displayed on page",
    )
    parser.add_argument(
        "--report-short-title",
        default="Basket Pages",
        help="Short report title for breadcrumb",
    )
    parser.add_argument(
        "--category",
        default="Basket Pages",
        help="Category label shown under the title",
    )
    parser.add_argument(
        "--copy-assets",
        action="store_true",
        help="Copy source screenshots into UXMaturityAnalysis/output/example-assets for a self-contained preview",
    )
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(project_root))
    source_audit = (project_root / args.source_audit).resolve()

    from src.utils.audit_organizer import build_frontend_report_cards
    from src.utils.html_report_generator import HTMLReportGenerator

    copied_assets_dir = None
    if args.copy_assets:
        copied_assets_dir = project_root / "output" / "example-assets" / source_audit.name
        if copied_assets_dir.exists():
            shutil.rmtree(copied_assets_dir)

    results = build_results_from_audit(source_audit, copied_assets_dir=copied_assets_dir)
    if not results:
        raise RuntimeError(f"No analysis results found in: {source_audit}")

    output_root = project_root / "output"
    generator = HTMLReportGenerator(output_dir=str(output_root))

    report_path = generator.generate_report_page(
        results=results,
        report_title=args.report_title,
        report_short_title=args.report_short_title,
        category=args.category,
        output_filename=args.output_filename,
    )

    cards = build_frontend_report_cards(output_root)
    index_path = generator.generate_index_page(cards)

    print(f"Generated report: {report_path}")
    print(f"Updated index: {index_path}")
    print(f"Source audit: {source_audit}")
    print(f"Competitors loaded: {len(results)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
