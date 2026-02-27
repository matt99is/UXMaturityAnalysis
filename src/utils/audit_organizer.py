"""
Audit organization utilities for structured output management.

This module handles the hierarchical organization of audit outputs:
- Type-based folders containing dated reports
- Competitor subfolders with screenshots
- Screenshots organized by date

Directory structure (NEW v1.9.0):
    output/
    ├── index.html                                   # Main dashboard
    ├── css/main.css
    ├── basket-pages/
    │   ├── index.html                               # List of all basket reports
    │   ├── 2026-02-27.html                          # Specific dated report
    │   ├── 2026-02-27.json                          # Summary data
    │   └── screenshots/
    │       └── 2026-02-27/
    │           └── {competitor}/
    │               ├── desktop.png
    │               ├── mobile.png
    │               ├── observation.json
    │               └── analysis.json
    ├── product-pages/
    │   └── ...
    └── checkout/
        └── ...

Legacy structure (still supported for reading):
    output/audits/{date}_{type}/
"""

import json
import re
from datetime import datetime
from html import escape
from pathlib import Path
from typing import Any, Dict, List, Optional
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
            with open(config_path, "r") as f:
                return json.load(f)
    except Exception:
        pass
    return None


def get_output_dir(default_base: str = "output") -> Path:
    """
    Get the output directory for this project.

    Args:
        default_base: Name of the output folder (default: "output")

    Returns:
        Path to <project_root>/<default_base>/
    """
    project_root = Path(__file__).resolve().parents[2]
    return project_root / default_base


def get_audits_dir(default_base: str = "output") -> Path:
    """
    Get the legacy audits subdirectory (for backward compatibility).

    Args:
        default_base: Name of the output folder (default: "output")

    Returns:
        Path to <project_root>/<default_base>/audits/
    """
    project_root = Path(__file__).resolve().parents[2]
    return project_root / default_base / "audits"


def get_type_dir(base_dir: str, analysis_type: str) -> Path:
    """
    Get the directory for a specific analysis type.

    Args:
        base_dir: Base output directory (e.g., "output")
        analysis_type: Type of analysis (e.g., "basket_pages")

    Returns:
        Path to output/{analysis_type}/
    """
    # Convert snake_case to kebab-case for URLs
    type_slug = analysis_type.replace("_", "-")
    return get_output_dir(base_dir) / type_slug


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

    matches = sorted([p.name for p in audit_root.iterdir() if p.is_file() and p.suffix == suffix])
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


def _coerce_float(value: Any) -> Optional[float]:
    """Safely coerce score-like values to float."""
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _compute_score_stats(audit_dir: Path) -> tuple[Optional[float], Optional[float]]:
    """Compute average and leader scores from competitor analysis files."""
    scores: List[float] = []

    for analysis_file in audit_dir.glob("*/analysis.json"):
        try:
            with open(analysis_file, "r", encoding="utf-8") as f:
                payload = json.load(f)
        except (OSError, json.JSONDecodeError):
            continue

        score = _coerce_float(payload.get("overall_score"))
        if score is not None:
            scores.append(score)

    if not scores:
        return None, None

    avg_score = round(sum(scores) / len(scores), 1)
    leader_score = round(max(scores), 1)
    return avg_score, leader_score


def _extract_scores_from_report_html(
    report_path: Path,
) -> tuple[Optional[float], Optional[float], int]:
    """Estimate score stats from generated report HTML content."""
    if not report_path.exists():
        return None, None, 0

    try:
        content = report_path.read_text(encoding="utf-8")
    except OSError:
        return None, None, 0

    score_matches = re.findall(
        r'class="competitor-score[^\"]*"[^>]*>\s*([0-9]+(?:\.[0-9]+)?)\s*<',
        content,
    )

    # Fallback for older templates without competitor cards.
    if not score_matches:
        score_matches = re.findall(
            r'class="score[^\"]*"[^>]*>\s*([0-9]+(?:\.[0-9]+)?)\s*<',
            content,
        )

    if not score_matches:
        return None, None, 0

    scores = [float(match) for match in score_matches]
    avg_score = round(sum(scores) / len(scores), 1)
    leader_score = round(max(scores), 1)
    return avg_score, leader_score, len(scores)


def _extract_scores_from_legacy_json(
    report_json: Path,
) -> tuple[Optional[float], Optional[float], Optional[int]]:
    """Extract score stats from legacy ux_analysis_*.json reports."""
    if not report_json.exists():
        return None, None, None

    try:
        with open(report_json, "r", encoding="utf-8") as f:
            payload = json.load(f)
    except (OSError, json.JSONDecodeError):
        return None, None, None

    analyses = payload.get("analyses") if isinstance(payload, dict) else None
    if not isinstance(analyses, list):
        return None, None, None

    scores = []
    for item in analyses:
        if not isinstance(item, dict):
            continue
        score = _coerce_float(item.get("overall_score"))
        if score is not None:
            scores.append(score)

    if not scores:
        return None, None, len(analyses)

    avg_score = round(sum(scores) / len(scores), 1)
    leader_score = round(max(scores), 1)
    return avg_score, leader_score, len(analyses)


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
                "analysis_type_key": "legacy",
                "total": None,
                "successful": None,
                "failed": None,
                "runtime_seconds": None,
                "html_report": None,
                "markdown_report": None,
                "summary_file": None,
                "json_report": None,
                "avg_score": None,
                "leader_score": None,
            }
        return run_map[ts]

    def infer_analysis_type_from_html(filename: str) -> tuple[str, str]:
        """Infer a readable analysis type and key from legacy HTML filename."""
        stem = Path(filename).stem
        cleaned = re.sub(r"(_report|-report)$", "", stem)
        cleaned = re.sub(r"^competitive_intelligence_", "", cleaned)
        cleaned = re.sub(r"_\d{8}_\d{6}$", "", cleaned)
        cleaned = cleaned.strip("_-")

        if not cleaned:
            return "Legacy (flat output)", "legacy"

        key = cleaned.replace("-", "_")
        label = cleaned.replace("_", " ").replace("-", " ").title()
        return label, key

    for html_file in output_root.glob("competitive_intelligence_*.html"):
        ts = _extract_legacy_timestamp(html_file)
        run = upsert(ts)
        run["html_report"] = html_file.name

    # Also include newer flat report naming styles used during redesign POCs.
    seen_html = {run.get("html_report") for run in run_map.values()}
    for pattern in ("*_report.html", "*-report.html"):
        for html_file in output_root.glob(pattern):
            if html_file.name == "index.html" or html_file.name in seen_html:
                continue
            ts = _extract_legacy_timestamp(html_file)
            run = upsert(ts)
            run["html_report"] = html_file.name
            label, key = infer_analysis_type_from_html(html_file.name)
            run["analysis_type"] = label
            run["analysis_type_key"] = key
            seen_html.add(html_file.name)

    for md_file in output_root.glob("ux_analysis_report_*.md"):
        ts = _extract_legacy_timestamp(md_file)
        upsert(ts)["markdown_report"] = md_file.name

    for json_file in output_root.glob("ux_analysis_*.json"):
        if json_file.name.startswith("ux_analysis_report_"):
            continue
        ts = _extract_legacy_timestamp(json_file)
        upsert(ts)["json_report"] = json_file.name

    # Enrich legacy runs with score/competitor stats when possible.
    for run in run_map.values():
        if run.get("json_report"):
            avg_score, leader_score, total = _extract_scores_from_legacy_json(
                output_root / run["json_report"]
            )
            if run.get("avg_score") is None:
                run["avg_score"] = avg_score
            if run.get("leader_score") is None:
                run["leader_score"] = leader_score
            if run.get("total") is None and total is not None:
                run["total"] = total

        if run.get("html_report") and (
            run.get("avg_score") is None or run.get("leader_score") is None
        ):
            avg_score, leader_score, count = _extract_scores_from_report_html(
                output_root / run["html_report"]
            )
            if run.get("avg_score") is None:
                run["avg_score"] = avg_score
            if run.get("leader_score") is None:
                run["leader_score"] = leader_score
            if run.get("total") is None and count:
                run["total"] = count

        if run.get("successful") is None and run.get("total") is not None:
            run["successful"] = run["total"]
        if (
            run.get("failed") is None
            and run.get("total") is not None
            and run.get("successful") is not None
        ):
            run["failed"] = max(0, int(run["total"]) - int(run["successful"]))

    return [run_map[key] for key in sorted(run_map.keys(), reverse=True)]


def collect_new_structure_runs(output_root: Path) -> List[Dict[str, Any]]:
    """
    Collect runs from the new structure: output/{type}/{date}.html

    Args:
        output_root: Path to output/

    Returns:
        List of dictionaries sorted newest-first by date.
    """
    if not output_root.exists():
        return []

    runs: List[Dict[str, Any]] = []

    # Look for type directories (basket-pages, product-pages, checkout)
    for type_dir in output_root.iterdir():
        if not type_dir.is_dir():
            continue
        if type_dir.name in ("audits", "css"):
            continue

        # Convert kebab-case back to snake_case for the key
        analysis_type_key = type_dir.name.replace("-", "_")

        # Look for dated HTML reports in this type directory
        for html_file in sorted(type_dir.glob("*.html"), key=lambda p: p.name, reverse=True):
            if html_file.name == "index.html":
                continue

            # Extract date from filename (e.g., 2026-02-27.html -> 2026-02-27)
            date_match = re.match(r"(\d{4}-\d{2}-\d{2})\.html", html_file.name)
            if not date_match:
                continue

            date_str = date_match.group(1)

            # Try to load summary JSON if it exists
            json_path = type_dir / f"{date_str}.json"
            summary = _load_summary(json_path) if json_path.exists() else {}

            # Compute scores from competitor analysis files
            screenshots_dir = type_dir / "screenshots" / date_str
            avg_score = _coerce_float(summary.get("avg_score"))
            leader_score = _coerce_float(summary.get("leader_score"))
            total_competitors = summary.get("total_competitors")

            if avg_score is None or leader_score is None:
                # Count competitor directories and compute scores
                if screenshots_dir.exists():
                    competitor_dirs = [d for d in screenshots_dir.iterdir() if d.is_dir()]
                    if total_competitors is None:
                        total_competitors = len(competitor_dirs)

                    scores = []
                    for comp_dir in competitor_dirs:
                        analysis_file = comp_dir / "analysis.json"
                        if analysis_file.exists():
                            try:
                                with open(analysis_file, "r", encoding="utf-8") as f:
                                    data = json.load(f)
                                score = _coerce_float(data.get("overall_score"))
                                if score is not None:
                                    scores.append(score)
                            except (OSError, json.JSONDecodeError):
                                pass

                    if scores:
                        if avg_score is None:
                            avg_score = round(sum(scores) / len(scores), 1)
                        if leader_score is None:
                            leader_score = round(max(scores), 1)

            # Build human-readable type name
            analysis_type_name = type_dir.name.replace("-", " ").title()
            if "basket" in analysis_type_name.lower():
                analysis_type_name = "Basket Pages"
            elif "product" in analysis_type_name.lower():
                analysis_type_name = "Product Pages"
            elif "checkout" in analysis_type_name.lower():
                analysis_type_name = "Checkout"

            # URL path to the report
            html_url = f"{type_dir.name}/{html_file.name}"

            runs.append({
                "folder": f"{date_str}_{analysis_type_key}",
                "date": date_str,
                "analysis_type": analysis_type_name,
                "analysis_type_key": analysis_type_key,
                "total": total_competitors,
                "successful": total_competitors,
                "failed": 0,
                "runtime_seconds": summary.get("runtime_seconds"),
                "html_report": html_url,
                "markdown_report": None,
                "summary_file": f"{type_dir.name}/{date_str}.json" if json_path.exists() else None,
                "avg_score": avg_score,
                "leader_score": leader_score,
                "_is_new_structure": True,
            })

    # Sort by date descending
    runs.sort(key=lambda r: r.get("date", ""), reverse=True)
    return runs


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
    audit_dirs = sorted(
        [d for d in audits_root.iterdir() if d.is_dir()], key=lambda p: p.name, reverse=True
    )

    for audit_dir in audit_dirs:
        summary = _load_summary(get_audit_summary_path(audit_dir))
        parts = audit_dir.name.split("_", 1)
        date_from_name = parts[0] if parts else "unknown"
        type_from_name = parts[1] if len(parts) > 1 else "unknown"

        avg_score = _coerce_float(summary.get("avg_score"))
        leader_score = _coerce_float(summary.get("leader_score"))
        if avg_score is None or leader_score is None:
            computed_avg, computed_leader = _compute_score_stats(audit_dir)
            if avg_score is None:
                avg_score = computed_avg
            if leader_score is None:
                leader_score = computed_leader

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
                "analysis_type": summary.get("analysis_type_name")
                or summary.get("analysis_type")
                or type_from_name,
                "analysis_type_key": summary.get("analysis_type") or type_from_name,
                "total": summary.get("total_competitors"),
                "successful": summary.get("successful_analyses"),
                "failed": summary.get("failed_analyses"),
                "runtime_seconds": summary.get("runtime_seconds"),
                "html_report": f"audits/{audit_dir.name}/{html_report}" if html_report else None,
                "markdown_report": f"audits/{audit_dir.name}/{md_report}" if md_report else None,
                "summary_file": f"audits/{audit_dir.name}/{summary_file}" if summary_file else None,
                "avg_score": avg_score,
                "leader_score": leader_score,
            }
        )

    return runs


def _format_frontend_date(value: Any) -> str:
    """Format audit date for card UI."""
    if value is None:
        return "Unknown"

    text = str(value).strip()
    for fmt in ("%Y-%m-%d", "%Y%m%d"):
        try:
            return datetime.strptime(text, fmt).strftime("%b %d, %Y")
        except ValueError:
            continue
    return text


def _sortable_frontend_date(value: Any) -> str:
    """Return a YYYYMMDD-like key for stable descending date sort."""
    if value is None:
        return "00000000"

    text = str(value).strip()
    for fmt in ("%Y-%m-%d", "%Y%m%d"):
        try:
            return datetime.strptime(text, fmt).strftime("%Y%m%d")
        except ValueError:
            continue
    return text


def _categorize_analysis(analysis_type_key: str, analysis_type_name: str) -> str:
    """Map analysis types to index filter categories."""
    label = f"{analysis_type_key} {analysis_type_name}".lower()
    if "basket" in label or "cart" in label:
        return "basket"
    if "product" in label:
        return "product"
    if "checkout" in label:
        return "checkout"
    return "other"


def build_frontend_report_cards(base_path: Path) -> List[Dict[str, Any]]:
    """
    Build card metadata for the modern index frontend.

    Args:
        base_path: Path to output/ or output/audits

    Returns:
        List of report card dictionaries for templates/index.html.jinja2
    """
    output_root, audits_root = _resolve_output_and_audits_roots(base_path)

    # Collect runs from all three sources: new structure, legacy audits, and flat legacy
    runs = (
        collect_new_structure_runs(output_root) +
        collect_audit_runs(audits_root) +
        collect_legacy_runs(output_root)
    )

    cards: List[Dict[str, Any]] = []
    for run in runs:
        filename = run.get("html_report")
        if not filename:
            continue

        total_competitors = run.get("successful")
        if total_competitors is None:
            total_competitors = run.get("total")
        if total_competitors is None:
            total_competitors = 0

        avg_score = _coerce_float(run.get("avg_score"))
        if avg_score is None:
            avg_score = 0.0

        leader_score = _coerce_float(run.get("leader_score"))
        if leader_score is None:
            leader_score = 0.0

        analysis_type_name = str(run.get("analysis_type") or "UX Analysis")
        analysis_type_key = str(run.get("analysis_type_key") or analysis_type_name)

        cards.append(
            {
                "filename": filename,
                "title": analysis_type_name,
                "full_title": analysis_type_name,
                "date": _format_frontend_date(run.get("date")),
                "competitors": int(total_competitors),
                "category": _categorize_analysis(analysis_type_key, analysis_type_name),
                "category_description": f"{analysis_type_name} across {int(total_competitors)} competitors",
                "avg_score": avg_score,
                "leader_score": leader_score,
                "icon": "bar-chart-3",
                "published": True,
                "_sort_key": _sortable_frontend_date(run.get("date")),
            }
        )

    cards.sort(key=lambda item: (item.get("_sort_key", ""), item.get("filename", "")), reverse=True)
    for card in cards:
        card.pop("_sort_key", None)
    return cards


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
        hostname = re.sub(r"^(www\.|m\.|shop\.|store\.|secure\.)", "", hostname)

        # Get the main domain name (before first dot)
        # e.g., amazon.com → amazon, zooplus.co.uk → zooplus
        parts = hostname.split(".")
        if parts:
            name = parts[0]
        else:
            name = hostname

        # Sanitize: lowercase, remove special characters, keep alphanumeric and hyphens
        name = re.sub(r"[^a-z0-9-]", "", name.lower())

        # Remove leading/trailing hyphens
        name = name.strip("-")

        return name if name else "competitor"

    except Exception:
        # Fallback: use a generic name
        return "competitor"


def create_audit_directory_structure(
    base_dir: str, analysis_type: str, competitors: List[Dict[str, str]], audit_date: str = None
) -> Dict[str, Path]:
    """
    Create the hierarchical directory structure for an audit run.

    NEW STRUCTURE (v1.9.0):
        output/{type}/screenshots/{date}/{competitor}/

    Args:
        base_dir: Base output directory (e.g., "output")
        analysis_type: Type of analysis (e.g., "basket_pages")
        competitors: List of competitor dicts with 'name' and 'url'
        audit_date: Optional custom date (YYYY-MM-DD), defaults to today

    Returns:
        Dictionary mapping keys to Path objects:
        {
            'audit_root': Path to type folder (e.g., output/basket-pages/),
            'audit_date': Date string (e.g., '2026-02-27'),
            'report_html': Path to output/{type}/{date}.html,
            'report_json': Path to output/{type}/{date}.json,
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

    # Get type directory (e.g., output/basket-pages/)
    type_dir = get_type_dir(base_dir, analysis_type)
    type_dir.mkdir(parents=True, exist_ok=True)

    # Create screenshots directory for this date
    screenshots_base = type_dir / "screenshots" / audit_date
    screenshots_base.mkdir(parents=True, exist_ok=True)

    # Create competitor subfolders
    competitor_paths = {}
    for competitor in competitors:
        comp_name = competitor["name"]
        comp_root = screenshots_base / comp_name

        # Create competitor directory
        comp_root.mkdir(exist_ok=True)

        competitor_paths[comp_name] = {
            "root": comp_root,
            "screenshots": comp_root,  # Screenshots are now in the same folder
        }

    return {
        "audit_root": type_dir,
        "audit_date": audit_date,
        "report_html": type_dir / f"{audit_date}.html",
        "report_json": type_dir / f"{audit_date}.json",
        "competitors": competitor_paths,
    }


def get_screenshot_path(competitor_paths: Dict, competitor_name: str, viewport_name: str) -> Path:
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

    # Screenshots are stored directly in the competitor folder
    comp_root = competitor_paths[competitor_name]["root"]
    filename = f"{viewport_name}.png"
    return comp_root / filename


def get_analysis_path(competitor_paths: Dict, competitor_name: str) -> Path:
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

    comp_root = competitor_paths[competitor_name]["root"]
    return comp_root / "analysis.json"


def get_observation_path(competitor_paths: Dict, competitor_name: str) -> Path:
    """
    Get the path for a competitor's observation JSON file.

    Args:
        competitor_paths: Dictionary from create_audit_directory_structure
        competitor_name: Clean competitor name

    Returns:
        Path object for observation.json
    """
    if competitor_name not in competitor_paths:
        raise ValueError(f"Competitor '{competitor_name}' not in paths")

    comp_root = competitor_paths[competitor_name]["root"]
    return comp_root / "observation.json"


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
    end_time: datetime,
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
        "competitors": [{"name": comp["name"], "url": comp["url"]} for comp in competitors],
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
