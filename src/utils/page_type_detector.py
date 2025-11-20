"""
Page type auto-detection from URLs.

Automatically detects the analysis type based on URL patterns.
"""

from urllib.parse import urlparse
from typing import Optional
import re


def detect_page_type(url: str) -> Optional[str]:
    """
    Detect page type from URL patterns.

    Args:
        url: The URL to analyze

    Returns:
        Detected analysis type or None if unable to detect

    Examples:
        detect_page_type("https://example.com/cart") -> "basket_pages"
        detect_page_type("https://example.com/product/123") -> "product_pages"
        detect_page_type("https://example.com/checkout") -> "checkout_pages"
        detect_page_type("https://example.com") -> "homepage_pages"
    """
    parsed = urlparse(url)
    path = parsed.path.lower()

    # Basket/Cart pages
    basket_patterns = [
        r'/(cart|basket|bag|shopping-bag|shopping-cart|checkout/cart)(/|$)',
        r'/cart\.php',
        r'/shoppingcart',
    ]
    for pattern in basket_patterns:
        if re.search(pattern, path):
            return "basket_pages"

    # Checkout pages
    checkout_patterns = [
        r'/(checkout|payment|billing|shipping|review-order)(/|$)',
        r'/order/review',
        r'/checkout\.php',
    ]
    for pattern in checkout_patterns:
        if re.search(pattern, path):
            return "checkout_pages"

    # Product pages
    product_patterns = [
        r'/(product|item|p|dp|products)/[^/]+',  # /product/id, /p/id, /dp/id
        r'/[^/]+-p-\d+',  # product-name-p-12345
        r'/pd/',  # product detail
        r'/gp/product/',  # Amazon style
    ]
    for pattern in product_patterns:
        if re.search(pattern, path):
            return "product_pages"

    # Homepage (must be last, as it's the most general)
    if path in ['', '/'] or parsed.netloc and not path.strip('/'):
        return "homepage_pages"

    # Could not detect
    return None


def get_page_type_display_name(analysis_type: str) -> str:
    """
    Get human-readable display name for analysis type.

    Args:
        analysis_type: Analysis type key (e.g., "basket_pages")

    Returns:
        Display name (e.g., "Basket/Cart Pages")
    """
    display_names = {
        "basket_pages": "Basket/Cart Pages",
        "product_pages": "Product Pages",
        "checkout_pages": "Checkout Flow",
        "homepage_pages": "Homepage",
    }
    return display_names.get(analysis_type, analysis_type.replace("_", " ").title())
