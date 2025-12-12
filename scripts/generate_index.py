#!/usr/bin/env python3
"""
Generate index.html for Netlify deployment.
Lists all available competitive intelligence reports.
"""

import json
import yaml
from pathlib import Path
from datetime import datetime


def generate_index_html(audits_dir: Path = Path("output/audits")):
    """Generate index.html listing all reports."""

    if not audits_dir.exists():
        print(f"Error: {audits_dir} does not exist")
        return

    # Find all audit directories
    audit_folders = [
        d for d in audits_dir.iterdir()
        if d.is_dir() and not d.name.startswith('.')
    ]

    # Sort by date (newest first)
    audit_folders.sort(reverse=True)

    # Build report metadata
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

        # Find HTML report
        html_report = folder / f"{folder_name}_report.html"

        if not html_report.exists():
            # Try alternative naming
            html_reports = list(folder.glob("*_report.html"))
            if html_reports:
                html_report = html_reports[0]
            else:
                continue

        # Determine competitor count
        # First try audit summary, then count folders
        summary_file = folder / "_audit_summary.json"
        competitor_count = None

        if summary_file.exists():
            try:
                with open(summary_file, 'r') as f:
                    summary = json.load(f)
                    competitor_count = summary.get('successful_count')
            except:
                pass

        # If not in summary, count competitor folders
        if competitor_count is None:
            comp_folders = [d for d in folder.iterdir() if d.is_dir() and not d.name.startswith('_')]
            competitor_count = len(comp_folders)

        # Format date nicely (e.g., "24 November 2025")
        try:
            from datetime import datetime
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            formatted_date = date_obj.strftime("%d %B %Y")
        except:
            formatted_date = date_str

        reports.append({
            'date': formatted_date,
            'date_raw': date_str,  # Keep for sorting
            'analysis_type': analysis_type_display,
            'folder_name': folder_name,
            'html_path': f"{folder_name}/{html_report.name}",
            'competitor_count': competitor_count
        })

    # Generate HTML
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>UX Maturity Reports</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
            min-height: 100vh;
            padding: 40px 0;
        }}
        .container {{
            max-width: 1200px;
        }}
        .header {{
            background: white;
            border-radius: 20px;
            padding: 40px;
            margin-bottom: 30px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            text-align: center;
        }}
        .header h1 {{
            color: #2d3748;
            font-weight: 700;
            margin-bottom: 10px;
        }}
        .header .subtitle {{
            color: #718096;
            font-size: 1.1rem;
        }}
        .report-card {{
            background: white;
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 20px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            transition: all 0.3s ease;
            text-decoration: none;
            display: block;
            color: inherit;
        }}
        .report-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 8px 25px rgba(16, 185, 129, 0.3);
            border: 2px solid #8b5cf6;
        }}
        .report-date {{
            color: #8b5cf6;
            font-weight: 600;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .report-title {{
            color: #2d3748;
            font-size: 1.5rem;
            font-weight: 700;
            margin: 10px 0;
        }}
        .report-meta {{
            color: #718096;
            font-size: 0.9rem;
        }}
        .badge-custom {{
            background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
            color: white;
            padding: 5px 12px;
            border-radius: 15px;
            font-size: 0.85rem;
            font-weight: 600;
        }}
        .no-reports {{
            background: white;
            border-radius: 15px;
            padding: 60px;
            text-align: center;
            color: #718096;
        }}
        .footer {{
            text-align: center;
            color: white;
            margin-top: 40px;
            font-size: 0.9rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1><i class="fas fa-chart-line"></i> UX Maturity Reports</h1>
            <div class="subtitle">E-commerce UX Maturity Dashboard</div>
            <div class="mt-3">
                <span class="badge-custom"><i class="fas fa-file-alt"></i> {len(reports)} Reports Available</span>
            </div>
        </div>

        <div class="reports-list">
"""

    if reports:
        for report in reports:
            html_content += f"""
            <a href="{report['html_path']}" class="report-card">
                <div class="report-date">
                    <i class="fas fa-calendar"></i> {report['date']}
                </div>
                <div class="report-title">{report['analysis_type']}</div>
                <div class="report-meta">
                    <i class="fas fa-users"></i> {report['competitor_count']} Competitors Analysed
                </div>
            </a>
"""
    else:
        html_content += """
            <div class="no-reports">
                <i class="fas fa-inbox" style="font-size: 4rem; color: #e2e8f0; margin-bottom: 20px;"></i>
                <h3 style="color: #2d3748;">No Reports Yet</h3>
                <p>Run your first analysis to see reports here.</p>
                <code style="background: #f7fafc; padding: 10px 20px; border-radius: 8px; display: inline-block; margin-top: 10px;">
                    python main.py --urls https://example.com
                </code>
            </div>
"""

    html_content += f"""
        </div>

        <div class="footer">
            <p>Generated by <strong>E-commerce UX Maturity Analysis Agent</strong></p>
            <p>Last updated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        </div>
    </div>
</body>
</html>
"""

    # Save index.html
    output_path = audits_dir / "index.html"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"✓ Generated index.html with {len(reports)} reports")
    print(f"  Location: {output_path}")
    return str(output_path)


if __name__ == "__main__":
    generate_index_html()
