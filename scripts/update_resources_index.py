#!/usr/bin/env python3
"""
Update Resources project index.html with UX Analysis reports.

This script adds/updates the "Analysis Reports" section in the Resources index page
using the design system standards defined in Resources/docs/PAGE_STRUCTURE.md.
"""

import json
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict

def load_config() -> Dict:
    """Load the resources integration configuration."""
    config_path = Path(__file__).parent.parent / "resources_integration_config.json"

    if not config_path.exists():
        # Return default configuration
        print("WARNING: resources_integration_config.json not found, using defaults")
        return {
            'resources_project_path': '../Resources',
            'output_subfolder': 'ux-analysis',
            'index_section_title': 'Analysis Reports',
            'update_index': True
        }

    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_audit_reports(ux_analysis_dir: Path) -> List[Dict]:
    """
    Scan ux-analysis directory for reports and extract metadata.

    Returns:
        List of dicts with report metadata, sorted by date (newest first)
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
        })

    return reports

def generate_analysis_cards_html(reports: List[Dict]) -> str:
    """
    Generate HTML for analysis report cards using Resources design system.

    Follows the pattern defined in Resources/docs/PAGE_STRUCTURE.md:
    - Uses card card--interactive for interactive cards
    - Uses overline for "Analysis" label
    - Uses card__title, card__description, card__meta
    - Meta items separated by bullet (•)
    """
    if not reports:
        return ""

    cards_html = []

    for report in reports:
        # Build meta items with bullet separators
        meta_items = [
            f"{report['competitor_count']} Competitors",
            "E-commerce"
        ]
        meta_html = "\n            <span>•</span>\n            ".join(
            f'<span>{item}</span>' for item in meta_items
        )

        card = f'''          <a href="{report['path']}" class="card card--interactive">
            <span class="overline">Analysis</span>
            <h3 class="card__title">{report['title']}</h3>
            <p class="card__description">Competitive UX maturity analysis across {report['competitor_count']} competitors.</p>
            <div class="card__meta">
            {meta_html}
            </div>
          </a>'''

        cards_html.append(card)

    return '\n\n'.join(cards_html)

def update_index_html(resources_path: Path, reports: List[Dict], config: Dict):
    """
    Update the Resources index.html with Analysis Reports section.

    Maintains the structure defined in Resources/docs/PAGE_STRUCTURE.md:
    - Section with id="analysis"
    - Class "section"
    - h2 with class "overline mb-4"
    - card-grid wrapper
    """
    index_path = resources_path / "index.html"

    if not index_path.exists():
        print(f"ERROR: index.html not found at {index_path}")
        return False

    with open(index_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Generate cards HTML
    cards_html = generate_analysis_cards_html(reports)

    # Generate the complete analysis section following Resources design system pattern
    section_html = f'''      <!-- Analysis Reports -->
      <section class="section" id="analysis">
        <h2 class="overline mb-4">{config['index_section_title']}</h2>

        <div class="card-grid">
{cards_html}
        </div>
      </section>'''

    # Pattern to match existing analysis section
    # Matches from <!-- Analysis Reports --> through the closing </section>
    analysis_section_pattern = r'(\s*<!-- Analysis Reports -->.*?</section>)'

    if re.search(analysis_section_pattern, content, flags=re.DOTALL):
        # Replace existing section
        content = re.sub(
            analysis_section_pattern,
            '\n' + section_html,
            content,
            flags=re.DOTALL
        )
        print("[+] Updated existing Analysis Reports section")
    else:
        # Insert new section after "Guides & Resources" section
        guides_section_pattern = r'(<!-- Guides & Resources -->.*?</section>)'

        if re.search(guides_section_pattern, content, flags=re.DOTALL):
            # Insert after guides section
            content = re.sub(
                guides_section_pattern,
                r'\1\n\n' + section_html,
                content,
                flags=re.DOTALL,
                count=1
            )
            print("[+] Added new Analysis Reports section after Guides")
        else:
            # Insert before footer as fallback
            footer_pattern = r'(\s*</main>)'
            content = re.sub(
                footer_pattern,
                '\n\n' + section_html + r'\1',
                content,
                count=1
            )
            print("[+] Added new Analysis Reports section before footer")

    # Write updated content
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"[+] Successfully updated {index_path}")
    print(f"    Added {len(reports)} report(s) to index")
    return True

def main():
    """Main execution."""
    print("==> Updating Resources index with UX Analysis reports...")
    print()

    # Load configuration
    config = load_config()
    resources_path = Path(config['resources_project_path']).resolve()
    ux_analysis_dir = resources_path / config['output_subfolder']

    print(f"Resources path: {resources_path}")
    print(f"UX Analysis dir: {ux_analysis_dir}")
    print()

    # Verify Resources path exists
    if not resources_path.exists():
        print(f"ERROR: Resources path not found: {resources_path}")
        print(f"       Update 'resources_project_path' in resources_integration_config.json")
        return

    # Get all reports
    reports = get_audit_reports(ux_analysis_dir)
    print(f"Found {len(reports)} report(s):")
    for report in reports:
        print(f"  * {report['title']} ({report['date']}) - {report['competitor_count']} competitors")
    print()

    if not reports:
        print("WARNING: No reports found. Run an analysis first!")
        print(f"         Expected reports in: {ux_analysis_dir}")
        return

    # Update index
    if config.get('update_index', True):
        success = update_index_html(resources_path, reports, config)
        if success:
            print()
            print("SUCCESS: Index updated!")
            print()
            print("Next steps:")
            print("  1. Review changes in Resources/index.html")
            print("  2. cd ../Resources")
            print("  3. git add index.html")
            print("  4. git commit -m 'Update analysis reports index'")
            print("  5. git push")
    else:
        print("WARNING: Index update disabled in config")

if __name__ == "__main__":
    main()
