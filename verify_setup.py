#!/usr/bin/env python3
"""
Setup verification script for the UX Analysis Agent.

This script checks that all required files and configurations are in place
before running the analysis.
"""

import sys
from pathlib import Path
import importlib.util


def check_file_exists(filepath: str, description: str) -> bool:
    """Check if a file exists."""
    path = Path(filepath)
    if path.exists():
        print(f"✓ {description}: {filepath}")
        return True
    else:
        print(f"✗ {description} missing: {filepath}")
        return False


def check_directory_exists(dirpath: str, description: str) -> bool:
    """Check if a directory exists."""
    path = Path(dirpath)
    if path.exists() and path.is_dir():
        print(f"✓ {description}: {dirpath}")
        return True
    else:
        print(f"✗ {description} missing: {dirpath}")
        return False


def check_python_module(module_name: str) -> bool:
    """Check if a Python module can be imported."""
    spec = importlib.util.find_spec(module_name)
    if spec is not None:
        print(f"✓ Python module available: {module_name}")
        return True
    else:
        print(f"✗ Python module missing: {module_name}")
        return False


def main():
    """Run setup verification checks."""
    print("=" * 60)
    print("UX Analysis Agent - Setup Verification")
    print("=" * 60)
    print()

    all_checks_passed = True

    # Check project structure
    print("Checking project structure...")
    print("-" * 60)

    structure_checks = [
        ("main.py", "Main script"),
        ("config.yaml", "Configuration file"),
        ("requirements.txt", "Requirements file"),
        (".env.example", "Environment template"),
        ("competitors.example.json", "Competitors example"),
        ("README.md", "README documentation"),
        ("src/config_loader.py", "Config loader module"),
        ("src/analyzers/screenshot_capture.py", "Screenshot capture module"),
        ("src/analyzers/claude_analyzer.py", "Claude analyzer module"),
        ("src/utils/report_generator.py", "Report generator module"),
    ]

    for filepath, description in structure_checks:
        if not check_file_exists(filepath, description):
            all_checks_passed = False

    print()

    # Check directories
    print("Checking directories...")
    print("-" * 60)

    dir_checks = [
        ("src", "Source directory"),
        ("src/analyzers", "Analyzers directory"),
        ("src/utils", "Utils directory"),
    ]

    for dirpath, description in dir_checks:
        if not check_directory_exists(dirpath, description):
            all_checks_passed = False

    # Create output directories if they don't exist
    for dirpath in ["output", "screenshots"]:
        Path(dirpath).mkdir(exist_ok=True)
        print(f"✓ Created/verified: {dirpath}")

    print()

    # Check Python version
    print("Checking Python version...")
    print("-" * 60)
    py_version = sys.version_info
    print(f"Python version: {py_version.major}.{py_version.minor}.{py_version.micro}")

    if py_version.major >= 3 and py_version.minor >= 10:
        print("✓ Python version is 3.10 or higher")
    elif py_version.major >= 3 and py_version.minor >= 8:
        print("⚠ Python 3.8-3.9 detected. Python 3.10+ recommended.")
    else:
        print("✗ Python 3.10+ required")
        all_checks_passed = False

    print()

    # Check dependencies (will fail if not installed, but that's expected)
    print("Checking Python dependencies (optional check)...")
    print("-" * 60)

    dependencies = [
        "dotenv",
        "anthropic",
        "playwright",
        "pydantic",
        "yaml",
        "rich"
    ]

    missing_deps = []
    for dep in dependencies:
        module_name = dep if dep != "dotenv" else "dotenv"
        module_name = module_name if module_name != "yaml" else "yaml"
        if not check_python_module(module_name):
            missing_deps.append(dep)

    if missing_deps:
        print()
        print("⚠ Missing dependencies. Install with:")
        print("  pip install -r requirements.txt")
        print("  playwright install chromium")

    print()

    # Check environment variables
    print("Checking environment setup...")
    print("-" * 60)

    if Path(".env").exists():
        print("✓ .env file exists")

        # Try to read API key (without loading it)
        with open(".env", "r") as f:
            content = f.read()
            if "ANTHROPIC_API_KEY" in content:
                if "your_api_key_here" in content:
                    print("⚠ .env file exists but API key not set")
                else:
                    print("✓ ANTHROPIC_API_KEY appears to be configured")
            else:
                print("✗ ANTHROPIC_API_KEY not found in .env")
    else:
        print("✗ .env file not found")
        print("  Create one by copying .env.example:")
        print("  cp .env.example .env")
        print("  Then edit .env and add your ANTHROPIC_API_KEY")

    print()
    print("=" * 60)

    if all_checks_passed:
        print("✓ All critical checks passed!")
        print()
        print("Next steps:")
        print("1. Ensure dependencies are installed: pip install -r requirements.txt")
        print("2. Install Playwright browsers: playwright install chromium")
        print("3. Set your API key in .env file")
        print("4. Run the tool: python main.py --urls <url1> <url2>")
        return 0
    else:
        print("✗ Some checks failed. Please review the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
