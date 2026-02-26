#!/usr/bin/env python3
"""
CSS Build Script for UX Analysis Reports

Compiles Sass modular stylesheets into a single optimized CSS file.
"""

import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime


def check_sass_installed():
    """Check if Sass is installed."""
    try:
        result = subprocess.run(
            ['sass', '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def install_sass():
    """Install Sass via npm if not available."""
    print("Sass not found. Installing...")
    try:
        subprocess.run(
            ['npm', 'install', '-g', 'sass'],
            check=True,
            timeout=120
        )
        print("✓ Sass installed successfully")
        return True
    except subprocess.CalledProcessError:
        print("✗ Failed to install Sass. Please install manually:")
        print("  npm install -g sass")
        print("  Or: pip install libsass")
        return False
    except FileNotFoundError:
        print("✗ npm not found. Please install Node.js first.")
        return False


def build_css(watch=False):
    """
    Build CSS from Sass source.

    Args:
        watch: If True, run in watch mode for development
    """
    project_root = Path(__file__).resolve().parent.parent
    css_dir = project_root / 'css'
    output_dir = project_root / 'output' / 'css'

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Source and destination
    source_file = css_dir / 'main.scss'
    output_file = output_dir / 'main.css'

    if not source_file.exists():
        print(f"✗ Source file not found: {source_file}")
        return False

    # Check if Sass is installed
    if not check_sass_installed():
        if not install_sass():
            return False

    print("Building CSS...")

    # Build command
    if watch:
        print("Watching for changes (Ctrl+C to stop)...")
        cmd = [
            'sass',
            '--watch',
            str(css_dir) + ':' + str(output_dir),
            '--style=compressed',
            '--no-source-map'
        ]
        try:
            subprocess.run(cmd)
            return True
        except KeyboardInterrupt:
            print("\nWatch mode stopped.")
            return True
    else:
        cmd = [
            'sass',
            str(source_file),
            str(output_file),
            '--style=compressed',
            '--no-source-map'
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                file_size = output_file.stat().st_size
                print(f"✓ CSS built: {output_file.relative_to(project_root)} ({file_size:,} bytes)")
                return True
            else:
                print(f"✗ Sass error:\n{result.stderr}")
                return False
        except subprocess.CalledProcessError as e:
            print(f"✗ Build failed: {e}")
            return False


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Build CSS for UX Analysis Reports')
    parser.add_argument('--watch', '-w', action='store_true',
                       help='Watch mode - rebuild on file changes')
    args = parser.parse_args()

    return build_css(watch=args.watch)


if __name__ == '__main__':
    sys.exit(0 if main() else 1)
