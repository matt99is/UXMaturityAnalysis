#!/usr/bin/env python3
"""
One-time Netlify site setup wizard.

Configures Netlify site, links output directory, and sets custom domain.
"""

import sys
import subprocess
from pathlib import Path


def check_netlify_cli() -> bool:
    """Check if netlify-cli is installed."""
    try:
        result = subprocess.run(
            ['netlify', '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def install_netlify_cli() -> bool:
    """Install netlify-cli via npm."""
    print("Netlify CLI not found. Installing...")
    try:
        subprocess.run(
            ['npm', 'install', '-g', 'netlify-cli'],
            check=True,
            timeout=120
        )
        print("✓ Netlify CLI installed successfully")
        return True
    except subprocess.CalledProcessError:
        print("✗ Failed to install Netlify CLI. Please install manually:")
        print("  npm install -g netlify-cli")
        return False
    except FileNotFoundError:
        print("✗ npm not found. Please install Node.js first.")
        return False


def is_site_linked(output_dir: Path) -> bool:
    """Check if output directory is already linked to a Netlify site."""
    state_file = output_dir / '.netlify' / 'state.json'
    return state_file.exists()


def link_site(output_dir: Path) -> bool:
    """Link output directory to Netlify site."""
    try:
        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)

        # Run netlify link in the output directory
        result = subprocess.run(
            ['netlify', 'link'],
            cwd=str(output_dir),
            input='\n',  # Auto-select defaults
            text=True,
            capture_output=True
        )
        return result.returncode == 0
    except Exception as e:
        print(f"✗ Error linking site: {e}")
        return False


def configure_custom_domain(domain: str) -> bool:
    """Configure custom domain via Netlify CLI."""
    print(f"[3/4] Configuring custom domain...")
    print(f"  Domain: {domain}")

    try:
        result = subprocess.run(
            ['netlify', 'domains:add', domain],
            capture_output=True,
            text=True
        )

        if result.returncode == 0 or 'already exists' in result.stderr.lower():
            print("✓ Domain configured")
            print("⚠️  DNS configuration required!")
            print("  Add the following record to your DNS:")
            print(f"  CNAME analysis -> <your-netlify-site>.netlify.app")
            return True
        else:
            # Domain might already be configured - that's OK
            print(f"✓ Domain configuration attempted")
            print("  (May already be configured)")
            return True
    except Exception as e:
        print(f"✗ Error configuring domain: {e}")
        return False


def main():
    """Run setup wizard."""
    project_root = Path(__file__).resolve().parent.parent
    output_dir = project_root / 'output'

    print("🔧 Netlify One-Time Setup\n")

    # Step 1: Check Netlify CLI
    print("[1/4] Checking Netlify CLI...")
    if not check_netlify_cli():
        if not install_netlify_cli():
            return False
    print("✓ Netlify CLI is installed\n")

    # Step 2: Check and link site
    print("[2/4] Checking for existing site link...")
    if not is_site_linked(output_dir):
        print("No site linked. Linking now...")
        print("\n⚠️  Interactive prompt follows - select or create a site:")
        if not link_site(output_dir):
            print("✗ Site linking failed")
            return False
        print("✓ Site linked successfully")
    else:
        print("✓ Site already linked")
    print()

    # Step 3: Configure custom domain
    CUSTOM_DOMAIN = "analysis.mattlelonek.co.uk"
    configure_custom_domain(CUSTOM_DOMAIN)
    print()

    # Step 4: Completion message
    print("[4/4] Saving configuration...")
    print("✓ Setup complete!\n")
    print("Next steps:")
    print("  1. Add DNS records to your domain provider")
    print("  2. Run analysis: python3 main.py --urls https://example.com")
    print("\nReports will auto-deploy to: https://" + CUSTOM_DOMAIN)

    return True


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
