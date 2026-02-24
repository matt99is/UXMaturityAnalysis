"""Version information for the E-commerce UX Maturity Analysis Agent."""

__version__ = "1.6.0"
__version_info__ = tuple(int(x) for x in __version__.split("."))

# Project metadata
__title__ = "E-commerce UX Maturity Analysis Agent"
__description__ = "AI-powered UX maturity analysis for e-commerce sites"
__author__ = "Matthew Lelonek"
__license__ = "MIT"


def get_version() -> str:
    """Get the current version string."""
    return __version__


def get_version_info() -> tuple:
    """Get version as tuple (major, minor, patch)."""
    return __version_info__


def print_version():
    """Print version information."""
    print(f"{__title__} v{__version__}")
    print(f"{__description__}")
