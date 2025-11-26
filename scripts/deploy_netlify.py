#!/usr/bin/env python3
"""
Prepare reports for Netlify deployment.
Generates index.html and prepares the audits directory.
"""

import sys
import subprocess
from pathlib import Path


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

    # Step 1: Generate index.html
    print("[1/3] Generating index.html...")
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from scripts.generate_index import generate_index_html

    try:
        generate_index_html()
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
        print("  2. Drag the 'output/audits' folder")
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
            cwd='output/audits'
        )

        if link_check.returncode != 0:
            print("\n⚠️  Site not linked yet. Linking now...")
            print("  Follow the prompts to create/link a Netlify site\n")

        # Deploy
        result = subprocess.run(
            deploy_cmd,
            cwd='output/audits',
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
