#!/usr/bin/env python3
"""Regenerate example UX report with latest CSS and templates."""

import json
from pathlib import Path

def main():
    print("Regenerating example report...")

    # Load sample data
    data_file = Path(__file__).parent.parent / 'sample_data' / 'basket_pages_example.json'
    with open(data_file, 'r') as f:
        data = json.load(f)

    # Import generator (add project root to path)
    import sys
    from pathlib import Path as PathLib
    sys.path.insert(0, str(PathLib(__file__).parent.parent))

    from src.utils.html_report_generator import HTMLReportGenerator

    generator = HTMLReportGenerator(output_dir='output')

    # Convert relative screenshot paths to absolute paths
    output_dir = Path(__file__).parent.parent / 'output'
    for comp in data['competitors']:
        if comp.get('screenshot_metadata'):
            for ss in comp['screenshot_metadata']:
                rel_path = ss.get('filepath', '')
                if rel_path and not Path(rel_path).is_absolute():
                    ss['filepath'] = str(output_dir / rel_path)

    # Convert sample data format to results format expected by generator
    results = [
        {
            'success': comp.get('success', True),
            'site_name': comp['name'],  # Generator expects 'site_name' not 'competitor_name'
            'competitor_id': comp['id'],
            'overall_score': comp['overall_score'],
            'criteria_scores': comp.get('criteria_scores', []),
            'evidence': comp.get('evidence_items', []),
            'screenshot_metadata': comp.get('screenshot_metadata', []),  # Generator expects 'screenshot_metadata'
        }
        for comp in data['competitors']
    ]

    output_path = generator.generate_report_page(
        results=results,
        report_title=data['report_title'],
        report_short_title=data['report_short_title'],
        category=data['category'],
        output_filename='resources-basket-pages-example-report.html'
    )

    print(f"✓ Report regenerated: {output_path}")
    output_file = Path(output_path)
    print(f"  Open in browser: file://{output_file.absolute()}")
    return str(output_path)


if __name__ == '__main__':
    main()
