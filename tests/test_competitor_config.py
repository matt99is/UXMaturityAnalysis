import pytest
import tempfile
from pathlib import Path
import yaml

from src.competitor_config import (
    list_competitor_sets,
    load_competitor_set,
    get_page_type_urls,
    save_url_correction,
)


@pytest.fixture
def competitors_dir(tmp_path):
    """Temporary competitors/ directory with a test YAML."""
    data = {
        "name": "Test Retail",
        "competitors": [
            {"name": "shopA", "pages": {"basket": "https://shopA.com/cart", "product": "https://shopA.com/product/1"}},
            {"name": "shopB", "pages": {"basket": "https://shopB.com/basket"}},
            {"name": "shopC", "pages": {"product": "https://shopC.com/item/1"}},
        ]
    }
    f = tmp_path / "testretail.yaml"
    f.write_text(yaml.dump(data))
    return tmp_path


def test_list_competitor_sets(competitors_dir):
    sets = list_competitor_sets(competitors_dir)
    assert sets == [("testretail", "Test Retail")]


def test_load_competitor_set(competitors_dir):
    result = load_competitor_set("testretail", competitors_dir)
    assert result["name"] == "Test Retail"
    assert len(result["competitors"]) == 3


def test_get_page_type_urls_returns_only_matching(competitors_dir):
    competitor_set = load_competitor_set("testretail", competitors_dir)
    urls = get_page_type_urls(competitor_set, "basket")
    assert urls == [
        {"name": "shopA", "url": "https://shopA.com/cart"},
        {"name": "shopB", "url": "https://shopB.com/basket"},
    ]
    # shopC has no basket URL — excluded


def test_get_page_type_urls_empty_when_none_match(competitors_dir):
    competitor_set = load_competitor_set("testretail", competitors_dir)
    urls = get_page_type_urls(competitor_set, "checkout")
    assert urls == []


def test_save_url_correction(competitors_dir):
    yaml_path = competitors_dir / "testretail.yaml"
    save_url_correction(yaml_path, "shopB", "basket", "https://shopB.com/new-basket")

    # Reload and verify
    with open(yaml_path) as f:
        data = yaml.safe_load(f)
    shopB = next(c for c in data["competitors"] if c["name"] == "shopB")
    assert shopB["pages"]["basket"] == "https://shopB.com/new-basket"


def test_save_url_correction_adds_new_page_type(competitors_dir):
    yaml_path = competitors_dir / "testretail.yaml"
    save_url_correction(yaml_path, "shopB", "product", "https://shopB.com/product/1")

    with open(yaml_path) as f:
        data = yaml.safe_load(f)
    shopB = next(c for c in data["competitors"] if c["name"] == "shopB")
    assert shopB["pages"]["product"] == "https://shopB.com/product/1"
