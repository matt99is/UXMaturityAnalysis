"""
Page type display utilities.
"""


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
