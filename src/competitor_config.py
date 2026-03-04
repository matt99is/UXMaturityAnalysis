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

# Compatibility map: analysis-type keys from criteria config -> legacy competitor YAML keys
_PAGE_TYPE_ALIASES = {
    "homepage_pages": ("homepage", "home"),
    "product_pages": ("product",),
    "basket_pages": ("basket",),
    "checkout_pages": ("checkout",),
}


def _candidate_page_keys(page_type: str) -> List[str]:
    """Return page keys to try in priority order."""
    keys = [page_type]
    keys.extend(_PAGE_TYPE_ALIASES.get(page_type, ()))
    return keys


def _preferred_save_key(existing_pages: Dict[str, Any], page_type: str) -> str:
    """
    Pick the best key to write URL corrections under.

    Preference order:
    1) exact key already present
    2) alias key already present
    3) first alias for known analysis page type
    4) exact key
    """
    if page_type in existing_pages:
        return page_type

    aliases = _PAGE_TYPE_ALIASES.get(page_type, ())
    for alias in aliases:
        if alias in existing_pages:
            return alias

    if aliases:
        return aliases[0]
    return page_type


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
    candidate_keys = _candidate_page_keys(page_type)
    for competitor in competitor_set.get("competitors", []):
        pages = competitor.get("pages", {})
        url = None
        for key in candidate_keys:
            value = pages.get(key)
            if value:
                url = value
                break
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
            save_key = _preferred_save_key(competitor["pages"], page_type)
            competitor["pages"][save_key] = new_url
            break

    with open(yaml_path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
