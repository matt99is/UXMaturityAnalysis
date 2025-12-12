#!/usr/bin/env python3
"""
Update Resources project index.html with UX Analysis reports.

This script adds/updates the "UX Analysis Reports" section in the Resources index page.
"""

import json
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict

def load_config() -> Dict:
    """Load the resources integration configuration."""
    config_path = Path(__file__).parent.parent / "resources_integration_config.json"
    with open(config_path, 'r') as f:
        return json.load(f)

def get_audit_reports(ux_analysis_dir: Path) -> List[Dict]:
    """
    Scan ux-analysis directory for reports and extract metadata.

    Returns:
        List of dicts with report metadata
    """
    reports = []

    if not ux_analysis_dir.exists():
        return reports

    # Find all report HTML files
    for audit_dir in sorted(ux_analysis_dir.iterdir(), reverse=True):
        if not audit_dir.is_dir() or audit_dir.name.startswith('.'):
            continue

        # Look for main report HTML file
        report_files = list(audit_dir.glob("*_report.html"))
        if not report_files:
            continue

        report_file = report_files[0]

        # Parse directory name: YYYY-MM-DD_page_type
        dir_name = audit_dir.name
        parts = dir_name.split('_', 1)

        if len(parts) < 2:
            continue

        date_str = parts[0]
        page_type = parts[1].replace('_', ' ').title()

        # Parse date
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            formatted_date = date_obj.strftime("%b %Y")
        except ValueError:
            formatted_date = date_str

        # Count competitors by counting subdirectories (excluding hidden and special dirs)
        competitor_count = len([
            d for d in audit_dir.iterdir()
            if d.is_dir() and not d.name.startswith(('_', '.'))
        ])

        # Construct relative path from Resources root
        relative_path = f"ux-analysis/{audit_dir.name}/{report_file.name}"

        reports.append({
            'title': f"{page_type} UX Analysis",
            'date': formatted_date,
            'date_raw': date_str,
            'competitor_count': competitor_count,
            'path': relative_path,
            'reading_time': '10 min read'  # Estimate
        })

    return reports

def generate_analysis_cards_html(reports: List[Dict], config: Dict) -> str:
    """Generate HTML for analysis report cards."""
    if not reports:
        return ""

    cards_html = []

    for report in reports:
        card = f'''                <a href="{report['path']}" class="doc-card">
                    <div class="card-header">
                        <span class="tag analysis">Analysis</span>
                        <span class="reading-time">{report['reading_time']}</span>
                    </div>
                    <h3>{report['title']}</h3>
                    <p class="description">Competitive UX maturity analysis across {report['competitor_count']} competitors.</p>
                    <div class="meta">
                        <span class="meta-item">{report['date']}</span>
                        <span class="meta-item">{report['competitor_count']} Competitors</span>
                        <span class="meta-item">E-commerce</span>
                    </div>
                </a>'''
        cards_html.append(card)

    return '\n'.join(cards_html)

def update_index_html(resources_path: Path, reports: List[Dict], config: Dict):
    """Update the Resources index.html with UX Analysis section."""
    index_path = resources_path / "index.html"

    if not index_path.exists():
        print(f"Error: index.html not found at {index_path}")
        return False

    with open(index_path, 'r') as f:
        content = f.read()

    # Generate the new analysis section
    section_html = f'''
        <section>
            <div class="section-header">
                <h2 class="section-label">{config['index_section_title']}</h2>
                <span class="section-count">({len(reports)})</span>
            </div>
            <div class="doc-list">
{generate_analysis_cards_html(reports, config)}
            </div>
        </section>
'''

    # Check if analysis section already exists
    analysis_section_pattern = r'<section>\s*<div class="section-header">\s*<h2 class="section-label">UX Analysis Reports<'

    if re.search(analysis_section_pattern, content):
        # Replace existing section
        # Find the section and replace it
        # Pattern to match the entire section including closing tag
        section_replace_pattern = r'(<section>\s*<div class="section-header">\s*<h2 class="section-label">UX Analysis Reports.*?</section>)'
        content = re.sub(section_replace_pattern, section_html, content, flags=re.DOTALL)
        print("✅ Updated existing UX Analysis Reports section")
    else:
        # Insert new section after "Guides & Resources"
        guides_section_pattern = r'(</section>\s*<!-- End Guides & Resources -->|</section>\s*\n\s*<footer)'

        # Try to find after guides section
        if re.search(r'Guides & Resources', content):
            # Insert after guides section
            insert_pattern = r'(Guides & Resources.*?</section>)'
            content = re.sub(
                insert_pattern,
                r'\1\n' + section_html,
                content,
                flags=re.DOTALL,
                count=1
            )
            print("✅ Added new UX Analysis Reports section after Guides")
        else:
            # Insert before footer as fallback
            content = re.sub(
                r'(\s*<footer)',
                '\n' + section_html + r'\1',
                content,
                count=1
            )
            print("✅ Added new UX Analysis Reports section before footer")

    # Add analysis tag CSS if not present
    if '.tag.analysis' not in content:
        tag_css = f'''
        .tag.analysis {{
            background: {config['tag_color_bg']};
            color: {config['tag_color_text']};
        }}'''

        # Insert before closing </style>
        content = content.replace('</style>', tag_css + '\n    </style>')
        print("✅ Added analysis tag CSS")

    # Write updated content
    with open(index_path, 'w') as f:
        f.write(content)

    print(f"✅ Successfully updated {index_path}")
    return True

def main():
    """Main execution."""
    print("🔄 Updating Resources index with UX Analysis reports...")

    # Load configuration
    config = load_config()
    resources_path = Path(config['resources_project_path'])
    ux_analysis_dir = resources_path / config['output_subfolder']

    print(f"📁 Resources path: {resources_path}")
    print(f"📊 UX Analysis dir: {ux_analysis_dir}")

    # Get all reports
    reports = get_audit_reports(ux_analysis_dir)
    print(f"📈 Found {len(reports)} reports")

    if not reports:
        print("⚠️  No reports found. Run an analysis first!")
        return

    # Update index
    if config.get('update_index', True):
        update_index_html(resources_path, reports, config)

    print("✅ Done!")

if __name__ == "__main__":
    main()
