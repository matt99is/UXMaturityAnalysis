#!/usr/bin/env python3
"""
Generate index.html using Jinja2 template.
Lists all available UX maturity analysis reports.

Supports both new structure (output/{type}/{date}.html) and legacy structure
(output/audits/{date}_{type}/).
"""

import json
from datetime import datetime
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader


def load_type_config(analysis_type_key: str) -> dict:
    """Load config for an analysis type."""
    config_file = Path("criteria_config") / f"{analysis_type_key}.yaml"
    if config_file.exists():
        try:
            with open(config_file, "r") as f:
                return yaml.safe_load(f) or {}
        except Exception:
            pass
    return {}


def get_type_display_name(analysis_type_key: str) -> str:
    """Get human-readable name for an analysis type."""
    config = load_type_config(analysis_type_key)
    return config.get("name", analysis_type_key.replace("_", " ").title())


def collect_new_structure_reports(output_dir: Path) -> dict:
    """
    Collect reports from new structure: output/{type}/{date}.html

    Returns:
        Dict mapping type_key to list of reports
    """
    reports_by_type = {}

    # Look for type directories
    for type_dir in output_dir.iterdir():
        if not type_dir.is_dir():
            continue
        if type_dir.name in ("audits", "css"):
            continue

        # Convert kebab-case to snake_case
        type_key = type_dir.name.replace("-", "_")
        type_slug = type_dir.name  # kebab-case for URLs

        reports = []
        for html_file in sorted(type_dir.glob("*.html"), key=lambda p: p.name, reverse=True):
            if html_file.name == "index.html":
                continue

            # Parse date from filename
            date_str = html_file.stem  # e.g., "2026-02-27"

            # Try to load summary JSON
            json_file = type_dir / f"{date_str}.json"
            avg_score = 0
            leader_score = 0
            competitor_count = 0

            if json_file.exists():
                try:
                    with open(json_file, "r") as f:
                        summary = json.load(f)
                        avg_score = summary.get("avg_score", 0) or 0
                        leader_score = summary.get("leader_score", 0) or 0
                        competitor_count = summary.get("total_competitors", 0) or 0
                except Exception:
                    pass

            # Count competitor folders if no summary
            if competitor_count == 0:
                screenshots_dir = type_dir / "screenshots" / date_str
                if screenshots_dir.exists():
                    competitor_count = len([d for d in screenshots_dir.iterdir() if d.is_dir()])

            # Format date
            try:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                formatted_date = date_obj.strftime("%d %B %Y")
            except ValueError:
                formatted_date = date_str

            reports.append({
                "filename": f"{type_slug}/{html_file.name}",
                "date": formatted_date,
                "sort_date": date_str,
                "avg_score": avg_score,
                "leader_score": leader_score,
                "competitors": competitor_count,
                "category": type_key,
                "full_title": get_type_display_name(type_key),
                "category_description": f"Competitive analysis of {type_dir.name.replace('-', ' ')}",
            })

        if reports:
            reports_by_type[type_key] = {
                "type_slug": type_slug,
                "type_name": get_type_display_name(type_key),
                "reports": reports,
                "latest": reports[0] if reports else None,
                "total_reports": len(reports),
            }

    return reports_by_type


def collect_legacy_reports(audits_dir: Path) -> list:
    """
    Collect reports from legacy structure: output/audits/{date}_{type}/

    Returns:
        List of report dicts
    """
    if not audits_dir.exists():
        return []

    reports = []
    for folder in sorted(audits_dir.iterdir(), key=lambda p: p.name, reverse=True):
        if not folder.is_dir() or folder.name.startswith("."):
            continue

        # Parse folder name (e.g., "2025-11-24_basket_pages")
        parts = folder.name.split("_", 1)
        if len(parts) < 2:
            continue

        date_str = parts[0]
        type_key = parts[1]

        # Find HTML report
        html_report = folder / f"{folder.name}_report.html"
        if not html_report.exists():
            html_reports = list(folder.glob("*_report.html"))
            if html_reports:
                html_report = html_reports[0]
            else:
                continue

        # Load summary
        summary_file = folder / "_audit_summary.json"
        avg_score = 0
        leader_score = 0
        competitor_count = 0

        if summary_file.exists():
            try:
                with open(summary_file, "r") as f:
                    summary = json.load(f)
                    avg_score = summary.get("avg_score", 0) or 0
                    leader_score = summary.get("leader_score", 0) or 0
                    competitor_count = summary.get("total_competitors", 0) or 0
            except Exception:
                pass

        # Count competitor folders
        if competitor_count == 0:
            comp_folders = [d for d in folder.iterdir() if d.is_dir() and not d.name.startswith("_")]
            competitor_count = len(comp_folders)

        # Format date
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            formatted_date = date_obj.strftime("%d %B %Y")
        except ValueError:
            formatted_date = date_str

        reports.append({
            "filename": f"audits/{folder.name}/{html_report.name}",
            "date": formatted_date,
            "sort_date": date_str,
            "avg_score": avg_score,
            "leader_score": leader_score,
            "competitors": competitor_count,
            "category": type_key,
            "full_title": get_type_display_name(type_key),
            "category_description": f"Competitive analysis of {type_key.replace('_', ' ')}",
        })

    return reports


def generate_type_index(type_key: str, type_data: dict, output_dir: Path):
    """Generate index.html for a specific analysis type."""
    type_slug = type_data["type_slug"]
    type_name = type_data["type_name"]
    reports = type_data["reports"]

    type_dir = output_dir / type_slug
    type_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    for report in reports:
        is_latest = rows == []
        badge_class = "latest" if is_latest else "old"
        badge_text = "LATEST" if is_latest else "ARCHIVED"

        rows.append(f'''
        <div class="report-card {"latest" if is_latest else ""}" onclick="window.location.href='{report['filename'].split('/')[-1]}'">
            <div class="report-header">
                <div class="report-date">{report['date']}</div>
                <span class="report-badge {badge_class}">{badge_text}</span>
            </div>
            <div class="report-stats">
                <div class="stat">
                    <div class="stat-value">{report['competitors']}</div>
                    <div class="stat-label">Competitors</div>
                </div>
                <div class="stat">
                    <div class="stat-value">{report['avg_score']:.1f}</div>
                    <div class="stat-label">Avg Score</div>
                </div>
                <div class="stat">
                    <div class="stat-value">{report['leader_score']:.1f}</div>
                    <div class="stat-label">Leader</div>
                </div>
            </div>
        </div>
        ''')

    empty_state = """
    <div class="empty-state">
        <h3>No reports yet</h3>
        <p>Run an analysis to generate the first report</p>
    </div>
    """ if not reports else ""

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{type_name} | UX Analytics</title>
    <link rel="stylesheet" href="/css/main.css">
</head>
<body>
    <div class="app">
        <aside class="sidebar">
            <a href="../index.html" class="back-link">← Back to Dashboard</a>
            <div class="brand">UX Analytics</div>
        </aside>
        <main class="main">
            <h1 class="title">{type_name}</h1>
            <p class="subtitle">All analysis runs for {type_name.lower()}</p>
            <div class="url-box">/{type_slug}/</div>
            {"".join(rows) if rows else empty_state}
        </main>
    </div>
</body>
</html>
"""

    output_path = type_dir / "index.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    return str(output_path)


def generate_main_index(output_dir: Path, reports_by_type: dict, legacy_reports: list):
    """Generate the main index.html dashboard."""

    # Build combined list for template
    # Group by type, show summary stats
    type_summaries = []

    # Add new structure types
    for type_key, type_data in reports_by_type.items():
        latest = type_data.get("latest")
        type_summaries.append({
            "filename": f"{type_data['type_slug']}/",
            "category": type_key,
            "date": latest["date"] if latest else "",
            "sort_date": latest["sort_date"] if latest else "",
            "full_title": type_data["type_name"],
            "avg_score": latest["avg_score"] if latest else 0,
            "leader_score": latest["leader_score"] if latest else 0,
            "competitors": latest["competitors"] if latest else 0,
            "category_description": f"{type_data['total_reports']} reports available",
            "total_reports": type_data["total_reports"],
        })

    # Add legacy reports (ungrouped, shown individually)
    all_reports = type_summaries + legacy_reports

    # Sort by date
    all_reports.sort(key=lambda r: r.get("sort_date", ""), reverse=True)

    # Load Jinja2 template
    template_dir = Path("templates")
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template("index.html.jinja2")

    # Render template
    html_content = template.render(reports=all_reports)

    # Save index.html
    output_path = output_dir / "index.html"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    return str(output_path)


def generate_index_html(output_dir: Path = Path("output")):
    """Generate all index files for the site."""

    # Collect reports from both structures
    reports_by_type = collect_new_structure_reports(output_dir)
    legacy_reports = collect_legacy_reports(output_dir / "audits")

    # Generate type index pages
    type_indices = []
    for type_key, type_data in reports_by_type.items():
        type_index_path = generate_type_index(type_key, type_data, output_dir)
        type_indices.append(type_index_path)
        print(f"  Generated: {type_index_path}")

    # Generate main index
    main_index_path = generate_main_index(output_dir, reports_by_type, legacy_reports)

    total_new = sum(t["total_reports"] for t in reports_by_type.values())
    total_legacy = len(legacy_reports)

    print(f"✓ Generated index.html")
    print(f"  New structure: {total_new} reports across {len(reports_by_type)} types")
    print(f"  Legacy structure: {total_legacy} reports")
    print(f"  Location: {main_index_path}")

    return main_index_path


if __name__ == "__main__":
    generate_index_html()
