"""
Competitor config loader and URL management.

Reads from competitors/*.yaml files. Each file defines a set of competitors
with per-page-type URLs. Provides URL validation and inline correction.
"""

from pathlib import Path
from typing import List, Dict, Tuple, Any
import yaml

# Default competitors directory relative to project root
_DEFAULT_DIR = Path(__file__).parent.parent / "competitors"


def list_competitor_sets(competitors_dir: Path = None) -> List[Tuple[str, str]]:
    """
    Discover all competitor YAML files.

    Returns list of (slug, display_name) tuples sorted by slug.
    slug is the filename stem (e.g. 'petfood').
    display_name is the 'name' field from the YAML.
    """
    d = competitors_dir or _DEFAULT_DIR
    results = []
    for yaml_file in sorted(d.glob("*.yaml")):
        with open(yaml_file) as f:
            data = yaml.safe_load(f)
        results.append((yaml_file.stem, data.get("name", yaml_file.stem)))
    return results


def load_competitor_set(slug: str, competitors_dir: Path = None) -> Dict[str, Any]:
    """Load a competitor YAML by slug (filename stem)."""
    d = competitors_dir or _DEFAULT_DIR
    path = d / f"{slug}.yaml"
    with open(path) as f:
        return yaml.safe_load(f)


def get_page_type_urls(competitor_set: Dict[str, Any], page_type: str) -> List[Dict[str, str]]:
    """
    Extract {name, url} pairs for a specific page type.

    Competitors with no entry for page_type are silently excluded.
    """
    results = []
    for competitor in competitor_set.get("competitors", []):
        url = competitor.get("pages", {}).get(page_type)
        if url:
            results.append({"name": competitor["name"], "url": url})
    return results


def save_url_correction(
    yaml_path: Path,
    competitor_name: str,
    page_type: str,
    new_url: str,
) -> None:
    """
    Update a competitor's page URL in-place and save the YAML.

    Creates the pages entry if the competitor has none for this page_type.
    """
    with open(yaml_path) as f:
        data = yaml.safe_load(f)

    for competitor in data.get("competitors", []):
        if competitor["name"] == competitor_name:
            if "pages" not in competitor:
                competitor["pages"] = {}
            competitor["pages"][page_type] = new_url
            break

    with open(yaml_path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
