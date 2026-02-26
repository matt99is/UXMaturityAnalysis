#!/usr/bin/env python3
"""
Prepare reports for Netlify deployment.
Generates index.html and prepares the audits directory.
"""

import sys
import subprocess
from pathlib import Path


def generate_frontend_index(project_root: Path) -> str:
    """Generate the modern reports frontend index at output/index.html."""
    # Late imports keep this script runnable even if project deps are partially missing.
    from src.utils.audit_organizer import build_frontend_report_cards
    from src.utils.html_report_generator import HTMLReportGenerator

    output_root = project_root / 'output'
    report_cards = build_frontend_report_cards(output_root)
    generator = HTMLReportGenerator(output_dir=str(output_root))
    return generator.generate_index_page(report_cards)


def check_netlify_cli():
    """Check if Netlify CLI is installed."""
    try:
        result = subprocess.run(
            ['netlify', '--version'],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def deploy_to_netlify(draft=False):
    """Deploy to Netlify."""

    print("🚀 Netlify Deployment Preparation\n")

    project_root = Path(__file__).resolve().parent.parent

    # Step 1: Generate index.html
    print("[1/3] Generating index.html...")
    sys.path.insert(0, str(project_root))

    try:
        index_path = generate_frontend_index(project_root)
        print(f"✓ Index generated: {index_path}")
    except Exception as e:
        print(f"✗ Error generating index: {e}")
        return False

    # Step 2: Check Netlify CLI
    print("\n[2/3] Checking Netlify CLI...")

    if not check_netlify_cli():
        print("✗ Netlify CLI not found")
        print("\nTo install Netlify CLI:")
        print("  npm install -g netlify-cli")
        print("\nOr deploy manually:")
        print("  1. Go to https://app.netlify.com/drop")
        print("  2. Drag the 'output' folder")
        print("  3. Done! Get your shareable link")
        return False

    print("✓ Netlify CLI installed")

    # Step 3: Deploy
    print("\n[3/3] Deploying to Netlify...")

    deploy_cmd = ['netlify', 'deploy']

    if not draft:
        deploy_cmd.append('--prod')
        print("  Deploying to production...")
    else:
        print("  Creating draft deployment...")

    try:
        # Check if site is linked
        link_check = subprocess.run(
            ['netlify', 'status'],
            capture_output=True,
            cwd=str(project_root / 'output')
        )

        if link_check.returncode != 0:
            print("\n⚠️  Site not linked yet. Linking now...")
            print("  Follow the prompts to create/link a Netlify site\n")

        # Deploy
        result = subprocess.run(
            deploy_cmd,
            cwd=str(project_root / 'output'),
            text=True
        )

        if result.returncode == 0:
            print("\n✅ Deployment successful!")
            print("\nNext steps:")
            print("  • View your site: netlify open:site")
            print("  • Check deployment: netlify open:admin")
            return True
        else:
            print("\n✗ Deployment failed")
            return False

    except Exception as e:
        print(f"\n✗ Deployment error: {e}")
        return False


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Deploy reports to Netlify")
    parser.add_argument(
        '--draft',
        action='store_true',
        help='Create draft deployment (not production)'
    )

    args = parser.parse_args()

    success = deploy_to_netlify(draft=args.draft)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
