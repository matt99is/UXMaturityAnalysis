#!/usr/bin/env python3
"""
Generate index.html using Jinja2 template.
Lists all available UX maturity analysis reports.
"""

import json
import yaml
from pathlib import Path
from datetime import datetime
from jinja2 import Environment, FileSystemLoader


def generate_index_html(audits_dir: Path = Path("output/audits")):
    """Generate index.html using Jinja2 template."""

    # Find all audit directories
    audit_folders = [
        d for d in audits_dir.iterdir()
        if d.is_dir() and not d.name.startswith('.')
    ]

    # Sort by date (newest first)
    audit_folders.sort(reverse=True)

    # Build report metadata matching template expectations
    reports = []
    for folder in audit_folders:
        # Parse folder name (e.g., "2025-11-24_basket_pages")
        folder_name = folder.name
        parts = folder_name.split('_', 1)

        if len(parts) >= 2:
            date_str = parts[0]
            analysis_type_key = parts[1]  # e.g., "basket_pages"

            # Try to load proper name from config file
            config_file = Path("criteria_config") / f"{analysis_type_key}.yaml"
            analysis_type_display = analysis_type_key.replace('_', ' ').title()  # Default fallback
            category_description = f"Competitive analysis of {analysis_type_display.lower()}"

            if config_file.exists():
                try:
                    with open(config_file, 'r') as f:
                        config = yaml.safe_load(f)
                        analysis_type_display = config.get('name', analysis_type_display)
                except:
                    pass  # Use fallback if config load fails
        else:
            date_str = "Unknown"
            analysis_type_display = folder_name
            category_description = f"Analysis of {folder_name}"

        # Find HTML report
        html_report = folder / f"{folder_name}_report.html"

        if not html_report.exists():
            # Try alternative naming
            html_reports = list(folder.glob("*_report.html"))
            if html_reports:
                html_report = html_reports[0]
            else:
                continue

        # Determine competitor count and scores from summary
        summary_file = folder / "_audit_summary.json"
        competitor_count = 0
        avg_score = 0
        leader_score = 0

        if summary_file.exists():
            try:
                with open(summary_file, 'r') as f:
                    summary = json.load(f)
                    competitor_count = summary.get('successful_count', 0)
                    avg_score = summary.get('average_score', 0)
                    leader_score = summary.get('leader_score', 0)
            except:
                pass

        # If not in summary, count competitor folders
        if competitor_count == 0:
            comp_folders = [d for d in folder.iterdir() if d.is_dir() and not d.name.startswith('_')]
            competitor_count = len(comp_folders)

        # Format date nicely (e.g., "24 November 2025")
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            formatted_date = date_obj.strftime("%d %B %Y")
        except:
            formatted_date = date_str

        # Derive category from analysis type for filtering
        category = analysis_type_key if len(parts) >= 2 else 'other'

        reports.append({
            'filename': f"audits/{folder_name}/{html_report.name}",
            'category': category,
            'date': formatted_date,
            'full_title': analysis_type_display,
            'avg_score': avg_score,
            'leader_score': leader_score,
            'competitors': competitor_count,
            'category_description': category_description
        })

    # Load Jinja2 template
    template_dir = Path("templates")
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template("index.html.jinja2")

    # Render template
    html_content = template.render(reports=reports)

    # Save index.html to output/audits directory (not nested inside)
    output_path = Path("output") / "index.html"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"✓ Generated index.html with {len(reports)} reports")
    print(f"  Location: {output_path}")
    return str(output_path)


if __name__ == "__main__":
    generate_index_html()
