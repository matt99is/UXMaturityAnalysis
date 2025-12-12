"""
Audit organization utilities for structured output management.

This module handles the hierarchical organization of audit outputs:
- Audit run folders (grouped by date and analysis type)
- Competitor subfolders
- Screenshots and analysis files

Directory structure:
    output/audits/{date}_{analysis_type}/{competitor}/screenshots/
                                                     /analysis.json
                                        /_comparison_report.md
                                        /_audit_summary.json
"""

import re
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from urllib.parse import urlparse


def get_resources_config() -> Optional[Dict]:
    """
    Load Resources integration configuration if it exists.

    Returns:
        Config dict or None if not configured
    """
    try:
        config_path = Path(__file__).parent.parent.parent / "resources_integration_config.json"
        if config_path.exists():
            with open(config_path, 'r') as f:
                return json.load(f)
    except Exception:
        pass
    return None


def get_output_base_dir(default_base: str = "output") -> Path:
    """
    Get the output base directory, using Resources project if configured.

    Args:
        default_base: Default output directory if Resources not configured

    Returns:
        Path object for the base output directory
    """
    config = get_resources_config()
    if config and config.get('resources_project_path'):
        resources_path = Path(config['resources_project_path'])
        output_subfolder = config.get('output_subfolder', 'ux-analysis')
        return resources_path / output_subfolder
    return Path(default_base) / "audits"


def extract_competitor_name(url: str) -> str:
    """
    Extract a clean competitor name from a URL.

    Examples:
        https://www.amazon.com/basket → amazon
        https://m.asos.com/bag → asos
        https://www.zooplus.co.uk/cart → zooplus
        https://shop.petco.com → petco

    Args:
        url: Full URL of the competitor site

    Returns:
        Clean, sanitized competitor name (lowercase, no special chars)
    """
    try:
        # Parse the URL to get the hostname
        parsed = urlparse(url)
        hostname = parsed.netloc or parsed.path

        # Remove common prefixes (www., m., shop., store., etc.)
        hostname = re.sub(r'^(www\.|m\.|shop\.|store\.|secure\.)', '', hostname)

        # Get the main domain name (before first dot)
        # e.g., amazon.com → amazon, zooplus.co.uk → zooplus
        parts = hostname.split('.')
        if parts:
            name = parts[0]
        else:
            name = hostname

        # Sanitize: lowercase, remove special characters, keep alphanumeric and hyphens
        name = re.sub(r'[^a-z0-9-]', '', name.lower())

        # Remove leading/trailing hyphens
        name = name.strip('-')

        return name if name else 'competitor'

    except Exception:
        # Fallback: use a generic name
        return 'competitor'


def create_audit_directory_structure(
    base_dir: str,
    analysis_type: str,
    competitors: List[Dict[str, str]],
    audit_date: str = None
) -> Dict[str, Path]:
    """
    Create the hierarchical directory structure for an audit run.

    Args:
        base_dir: Base output directory (e.g., "output")
        analysis_type: Type of analysis (e.g., "basket_pages")
        competitors: List of competitor dicts with 'name' and 'url'
        audit_date: Optional custom date (YYYY-MM-DD), defaults to today

    Returns:
        Dictionary mapping keys to Path objects:
        {
            'audit_root': Path to audit root folder,
            'competitors': {
                'competitor_name': {
                    'root': Path to competitor folder,
                    'screenshots': Path to screenshots subfolder
                }
            }
        }
    """
    # Use today's date if not provided
    if audit_date is None:
        audit_date = datetime.now().strftime("%Y-%m-%d")

    # Create audit root directory: use Resources path if configured
    audit_folder_name = f"{audit_date}_{analysis_type}"
    base_output_dir = get_output_base_dir(base_dir)
    audit_root = base_output_dir / audit_folder_name
    audit_root.mkdir(parents=True, exist_ok=True)

    # Create competitor subfolders
    competitor_paths = {}
    for competitor in competitors:
        comp_name = competitor['name']
        comp_root = audit_root / comp_name
        comp_screenshots = comp_root / "screenshots"

        # Create directories
        comp_root.mkdir(exist_ok=True)
        comp_screenshots.mkdir(exist_ok=True)

        competitor_paths[comp_name] = {
            'root': comp_root,
            'screenshots': comp_screenshots
        }

    return {
        'audit_root': audit_root,
        'competitors': competitor_paths
    }


def get_screenshot_path(
    competitor_paths: Dict,
    competitor_name: str,
    viewport_name: str
) -> Path:
    """
    Get the path for a screenshot file.

    Args:
        competitor_paths: Dictionary from create_audit_directory_structure
        competitor_name: Clean competitor name
        viewport_name: 'desktop' or 'mobile'

    Returns:
        Path object for the screenshot file
    """
    if competitor_name not in competitor_paths:
        raise ValueError(f"Competitor '{competitor_name}' not in paths")

    screenshots_dir = competitor_paths[competitor_name]['screenshots']
    filename = f"{viewport_name}.png"
    return screenshots_dir / filename


def get_analysis_path(
    competitor_paths: Dict,
    competitor_name: str
) -> Path:
    """
    Get the path for a competitor's analysis JSON file.

    Args:
        competitor_paths: Dictionary from create_audit_directory_structure
        competitor_name: Clean competitor name

    Returns:
        Path object for analysis.json
    """
    if competitor_name not in competitor_paths:
        raise ValueError(f"Competitor '{competitor_name}' not in paths")

    comp_root = competitor_paths[competitor_name]['root']
    return comp_root / "analysis.json"


def get_comparison_report_path(audit_root: Path) -> Path:
    """
    Get the path for the audit-level comparison report.

    Args:
        audit_root: Root path of the audit

    Returns:
        Path object for _comparison_report.md
    """
    return audit_root / "_comparison_report.md"


def get_audit_summary_path(audit_root: Path) -> Path:
    """
    Get the path for the audit-level summary JSON.

    Args:
        audit_root: Root path of the audit

    Returns:
        Path object for _audit_summary.json
    """
    return audit_root / "_audit_summary.json"


def generate_audit_summary(
    analysis_type: str,
    analysis_type_name: str,
    competitors: List[Dict[str, str]],
    successful_count: int,
    failed_count: int,
    start_time: datetime,
    end_time: datetime
) -> Dict:
    """
    Generate audit summary metadata.

    Args:
        analysis_type: Analysis type ID (e.g., "basket_pages")
        analysis_type_name: Human-readable name
        competitors: List of competitor dicts
        successful_count: Number of successful analyses
        failed_count: Number of failed analyses
        start_time: When audit started
        end_time: When audit ended

    Returns:
        Dictionary with audit metadata
    """
    runtime_seconds = (end_time - start_time).total_seconds()

    return {
        "audit_date": start_time.strftime("%Y-%m-%d"),
        "audit_timestamp": start_time.isoformat(),
        "analysis_type": analysis_type,
        "analysis_type_name": analysis_type_name,
        "total_competitors": len(competitors),
        "successful_analyses": successful_count,
        "failed_analyses": failed_count,
        "runtime_seconds": round(runtime_seconds, 2),
        "competitors": [
            {
                "name": comp['name'],
                "url": comp['url']
            }
            for comp in competitors
        ]
    }


if __name__ == "__main__":
    # Test the functions
    print("Testing URL extraction:")
    test_urls = [
        "https://www.amazon.com/basket",
        "https://m.asos.com/bag",
        "https://www.zooplus.co.uk/cart",
        "https://shop.petco.com",
        "https://www.ebay.co.uk",
    ]

    for url in test_urls:
        name = extract_competitor_name(url)
        print(f"  {url} → {name}")
