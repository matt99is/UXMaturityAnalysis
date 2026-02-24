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
from html import escape
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
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
    Get the output base directory inside this project.

    Args:
        default_base: Default output directory if Resources not configured

    Returns:
        Path object for the base output directory
    """
    project_root = Path(__file__).resolve().parents[2]
    return project_root / default_base / "audits"


def _load_summary(summary_path: Path) -> Dict[str, Any]:
    """Load audit summary JSON safely."""
    if not summary_path.exists():
        return {}

    try:
        with open(summary_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _first_existing_file(audit_root: Path, candidates: List[str], suffix: str) -> Optional[str]:
    """Return the first existing filename from explicit candidates or by suffix scan."""
    for candidate in candidates:
        if (audit_root / candidate).exists():
            return candidate

    matches = sorted(
        [p.name for p in audit_root.iterdir() if p.is_file() and p.suffix == suffix]
    )
    return matches[0] if matches else None


def _resolve_output_and_audits_roots(base_path: Path) -> tuple[Path, Path]:
    """Resolve output root and audits root from a path that may be either."""
    if base_path.name == "audits":
        return base_path.parent, base_path
    return base_path, base_path / "audits"


def _extract_legacy_timestamp(path: Path) -> str:
    """Extract YYYYMMDD_HHMMSS timestamp from a legacy report filename."""
    match = re.search(r"(\d{8}_\d{6})", path.name)
    if match:
        return match.group(1)
    return datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y%m%d_%H%M%S")


def collect_legacy_runs(output_root: Path) -> List[Dict[str, Any]]:
    """Collect flat-output legacy report sets saved directly under output/."""
    if not output_root.exists():
        return []

    run_map: Dict[str, Dict[str, Any]] = {}

    def upsert(ts: str) -> Dict[str, Any]:
        if ts not in run_map:
            try:
                date_text = datetime.strptime(ts, "%Y%m%d_%H%M%S").strftime("%Y-%m-%d")
            except ValueError:
                date_text = "legacy"

            run_map[ts] = {
                "folder": f"legacy_{ts}",
                "date": date_text,
                "analysis_type": "Legacy (flat output)",
                "total": None,
                "successful": None,
                "failed": None,
                "runtime_seconds": None,
                "html_report": None,
                "markdown_report": None,
                "summary_file": None,
                "json_report": None,
            }
        return run_map[ts]

    for html_file in output_root.glob("competitive_intelligence_*.html"):
        ts = _extract_legacy_timestamp(html_file)
        upsert(ts)["html_report"] = html_file.name

    for md_file in output_root.glob("ux_analysis_report_*.md"):
        ts = _extract_legacy_timestamp(md_file)
        upsert(ts)["markdown_report"] = md_file.name

    for json_file in output_root.glob("ux_analysis_*.json"):
        if json_file.name.startswith("ux_analysis_report_"):
            continue
        ts = _extract_legacy_timestamp(json_file)
        upsert(ts)["json_report"] = json_file.name

    return [run_map[key] for key in sorted(run_map.keys(), reverse=True)]


def collect_audit_runs(audits_root: Path) -> List[Dict[str, Any]]:
    """
    Collect metadata and report links for all audit runs.

    Args:
        audits_root: Path to output/audits

    Returns:
        List of dictionaries sorted newest-first by folder name.
    """
    if not audits_root.exists():
        return []

    runs: List[Dict[str, Any]] = []
    audit_dirs = sorted([d for d in audits_root.iterdir() if d.is_dir()], key=lambda p: p.name, reverse=True)

    for audit_dir in audit_dirs:
        summary = _load_summary(get_audit_summary_path(audit_dir))
        parts = audit_dir.name.split("_", 1)
        date_from_name = parts[0] if parts else "unknown"
        type_from_name = parts[1] if len(parts) > 1 else "unknown"

        html_report = _first_existing_file(
            audit_dir,
            ["_comparison_report.html", f"{audit_dir.name}_report.html"],
            ".html",
        )
        md_report = _first_existing_file(audit_dir, ["_comparison_report.md"], ".md")
        summary_file = "_audit_summary.json" if get_audit_summary_path(audit_dir).exists() else None

        runs.append(
            {
                "folder": audit_dir.name,
                "date": summary.get("audit_date", date_from_name),
                "analysis_type": summary.get("analysis_type_name") or summary.get("analysis_type") or type_from_name,
                "total": summary.get("total_competitors"),
                "successful": summary.get("successful_analyses"),
                "failed": summary.get("failed_analyses"),
                "runtime_seconds": summary.get("runtime_seconds"),
                "html_report": f"audits/{audit_dir.name}/{html_report}" if html_report else None,
                "markdown_report": f"audits/{audit_dir.name}/{md_report}" if md_report else None,
                "summary_file": f"audits/{audit_dir.name}/{summary_file}" if summary_file else None,
            }
        )

    return runs


def generate_reports_index(base_path: Path) -> Path:
    """
    Generate/update output/index.html with links to all audit and legacy reports.

    Args:
        base_path: Path to output/ or output/audits

    Returns:
        Path to generated output/index.html
    """
    output_root, audits_root = _resolve_output_and_audits_roots(base_path)
    output_root.mkdir(parents=True, exist_ok=True)
    audits_root.mkdir(parents=True, exist_ok=True)

    runs = collect_audit_runs(audits_root) + collect_legacy_runs(output_root)
    runs = sorted(
        runs,
        key=lambda run: (str(run.get("date", "")), str(run.get("folder", ""))),
        reverse=True,
    )

    rows = []
    for run in runs:
        total = run["total"] if run["total"] is not None else "-"
        successful = run["successful"] if run["successful"] is not None else "-"
        failed = run["failed"] if run["failed"] is not None else "-"
        runtime = run["runtime_seconds"] if run["runtime_seconds"] is not None else "-"

        links = []
        if run["html_report"]:
            links.append(f'<a href="{escape(run["html_report"])}">HTML</a>')
        if run["markdown_report"]:
            links.append(f'<a href="{escape(run["markdown_report"])}">Markdown</a>')
        if run["summary_file"]:
            links.append(f'<a href="{escape(run["summary_file"])}">Summary JSON</a>')
        if run.get("json_report"):
            links.append(f'<a href="{escape(run["json_report"])}">JSON</a>')
        links_html = " | ".join(links) if links else "No reports"

        rows.append(
            "<tr>"
            f"<td>{escape(str(run['date']))}</td>"
            f"<td>{escape(str(run['analysis_type']))}</td>"
            f"<td>{escape(str(total))}</td>"
            f"<td>{escape(str(successful))}</td>"
            f"<td>{escape(str(failed))}</td>"
            f"<td>{escape(str(runtime))}</td>"
            f"<td>{links_html}</td>"
            f"<td><code>{escape(run['folder'])}</code></td>"
            "</tr>"
        )

    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    table_body = "\n".join(rows) if rows else "<tr><td colspan='8'>No audits found yet.</td></tr>"

    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>UX Analysis Reports Index</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 24px; color: #1f2937; }}
    h1 {{ margin: 0 0 8px; }}
    .meta {{ color: #6b7280; margin-bottom: 16px; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ border: 1px solid #e5e7eb; padding: 10px; text-align: left; font-size: 14px; }}
    th {{ background: #f9fafb; }}
    tr:nth-child(even) td {{ background: #fcfcfd; }}
    a {{ color: #1d4ed8; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
  </style>
</head>
<body>
  <h1>UX Analysis Reports</h1>
  <div class="meta">Generated: {escape(generated_at)} | Total audits: {len(runs)}</div>
  <table>
    <thead>
      <tr>
        <th>Date</th>
        <th>Analysis Type</th>
        <th>Total</th>
        <th>Successful</th>
        <th>Failed</th>
        <th>Runtime (s)</th>
        <th>Reports</th>
        <th>Audit Folder</th>
      </tr>
    </thead>
    <tbody>
      {table_body}
    </tbody>
  </table>
</body>
</html>
"""

    index_path = output_root / "index.html"
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(html)

    return index_path


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
