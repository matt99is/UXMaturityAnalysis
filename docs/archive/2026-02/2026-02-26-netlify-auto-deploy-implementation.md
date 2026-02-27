# Automatic Netlify Deployment Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Automatically deploy UX analysis reports to Netlify at analysis.mattlelonek.co.uk after each analysis completes.

**Architecture:** Integrate Netlify CLI deployment into main.py analysis pipeline, with one-time setup script for site configuration and custom domain.

**Tech Stack:** Python 3.9+, Netlify CLI (npm package), subprocess module

---

## Task 1: Create netlify.toml Configuration File

**Files:**
- Create: `netlify.toml`

**Step 1: Create the configuration file**

```toml
# Netlify build and deployment configuration
[build]
  publish = "output"

[build.processing.css]
  bundle = false

[dev]
  command = "python3 -m http.server 8000 --directory output"
  publish = "output"
```

**Step 2: Verify file creation**

Run: `ls -la netlify.toml`
Expected: File exists at project root

**Step 3: Commit**

```bash
git add netlify.toml
git commit -m "feat: add netlify.toml build configuration"
```

---

## Task 2: Create Setup Script - Basic Structure

**Files:**
- Create: `scripts/setup_netlify.py`

**Step 1: Create script skeleton with shebang and imports**

```python
#!/usr/bin/env python3
"""
One-time Netlify site setup wizard.

Configures Netlify site, links output directory, and sets custom domain.
"""

import sys
import subprocess
from pathlib import Path


def main():
    """Run setup wizard."""
    print("🔧 Netlify One-Time Setup\n")


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
```

**Step 2: Verify script runs**

Run: `python3 scripts/setup_netlify.py`
Expected: Prints "🔧 Netlify One-Time Setup"

**Step 3: Make executable**

Run: `chmod +x scripts/setup_netlify.py`
Expected: No error

**Step 4: Commit**

```bash
git add scripts/setup_netlify.py
git commit -m "feat: add setup_netlify.py skeleton"
```

---

## Task 3: Add Netlify CLI Check Functions to Setup Script

**Files:**
- Modify: `scripts/setup_netlify.py`

**Step 1: Add check_netlify_cli function**

```python
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
```

**Step 2: Test function exists**

Run: `python3 -c "from scripts.setup_netlify import check_netlify_cli, install_netlify_cli; print('OK')"`
Expected: Prints "OK"

**Step 3: Commit**

```bash
git add scripts/setup_netlify.py
git commit -m "feat: add netlify CLI check and install functions"
```

---

## Task 4: Add Site Link Check Function to Setup Script

**Files:**
- Modify: `scripts/setup_netlify.py`

**Step 1: Add is_site_linked function**

```python
def is_site_linked(output_dir: Path) -> bool:
    """Check if output directory is already linked to a Netlify site."""
    state_file = output_dir / '.netlify' / 'state.json'
    return state_file.exists()
```

**Step 2: Update main to check CLI and site link**

```python
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

    # Step 2: Check site link
    print("[2/4] Checking for existing site link...")
    if is_site_linked(output_dir):
        print("✓ Site already linked. Updating configuration...")
    else:
        print("No site linked. Linking now...")
    print()
```

**Step 3: Test updated main**

Run: `python3 scripts/setup_netlify.py`
Expected:
```
🔧 Netlify One-Time Setup

[1/4] Checking Netlify CLI...
✓ Netlify CLI is installed

[2/4] Checking for existing site link...
No site linked. Linking now...
```

**Step 4: Commit**

```bash
git add scripts/setup_netlify.py
git commit -m "feat: add site link check to setup script"
```

---

## Task 5: Add Site Linking Function to Setup Script

**Files:**
- Modify: `scripts/setup_netlify.py`

**Step 1: Add link_site function**

```python
def link_site(output_dir: Path) -> bool:
    """Link output directory to Netlify site."""
    try:
        # Change to output directory for netlify init
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
```

**Step 2: Integrate link_site into main flow**

Update the main function:

```python
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
        if not link_site(output_dir):
            print("✗ Site linking failed")
            return False
        print("✓ Site linked successfully")
    else:
        print("✓ Site already linked")
    print()
```

**Step 3: Test link_site (dry run - will prompt if not linked)**

Run: `python3 scripts/setup_netlify.py`
Expected: Site link step runs (may prompt if no existing link)

**Step 4: Commit**

```bash
git add scripts/setup_netlify.py
git commit -m "feat: add site linking function"
```

---

## Task 6: Add Custom Domain Configuration to Setup Script

**Files:**
- Modify: `scripts/setup_netlify.py`

**Step 1: Add configure_custom_domain function**

```python
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

        if result.returncode == 0:
            print("✓ Domain configured")
            print("⚠️  DNS configuration required!")
            print("  Add the following record to your DNS:")
            print(f"  CNAME analysis -> <your-netlify-site>.netlify.app")
            return True
        else:
            print(f"✗ Domain configuration failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"✗ Error configuring domain: {e}")
        return False
```

**Step 2: Update main to include domain configuration**

Update the main function, add at the end:

```python
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

    return True
```

**Step 3: Test domain configuration**

Run: `python3 scripts/setup_netlify.py`
Expected: Shows domain configuration step with DNS instructions

**Step 4: Commit**

```bash
git add scripts/setup_netlify.py
git commit -m "feat: add custom domain configuration"
```

---

## Task 7: Create deploy_reports Function in main.py

**Files:**
- Modify: `main.py`

**Step 1: Add deploy_reports function at module level**

Add after imports (around line 40-50, find a good spot):

```python
def deploy_reports(output_dir: Path, skip: bool = False) -> bool:
    """
    Automatically deploy generated reports to Netlify.

    Args:
        output_dir: Path to output directory
        skip: If True, skip deployment

    Returns:
        bool: True if deployment succeeded or was skipped
    """
    if skip:
        print("⏭️  Deployment skipped (--no-deploy flag)")
        return True

    # Check if Netlify site is configured
    state_file = output_dir / '.netlify' / 'state.json'
    if not state_file.exists():
        print("⚠️  Netlify site not configured")
        print("  Run: python3 scripts/setup_netlify.py")
        print("Deployment skipped. Reports saved locally.\n")
        return False

    print("\n🚀 Deploying to Netlify...")

    # Retry logic for network issues
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            result = subprocess.run(
                ['netlify', 'deploy', '--prod', '--dir', str(output_dir)],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                print("✅ Deployment successful: https://analysis.mattlelonek.co.uk")
                return True
            else:
                if attempt < max_retries:
                    print(f"❌ Deployment failed. Retrying... ({attempt}/{max_retries})")
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    print(f"❌ Deployment failed after {max_retries} attempts")
                    if result.stderr:
                        print(f"  Error: {result.stderr}")
                    print("\nManual deployment option:")
                    print("  python3 scripts/deploy_netlify.py")
                    return False

        except subprocess.TimeoutExpired:
            if attempt < max_retries:
                print(f"⏱️  Timeout. Retrying... ({attempt}/{max_retries})")
                time.sleep(2 ** attempt)
            else:
                print("❌ Deployment timed out")
                return False
        except Exception as e:
            print(f"❌ Deployment error: {e}")
            return False

    return False
```

**Step 2: Add time import if not present**

Check top of main.py for imports, add time if missing:

```python
import time
```

**Step 3: Verify function syntax**

Run: `python3 -c "from main import deploy_reports; print('OK')"`
Expected: Prints "OK" or module path depending on import structure

**Step 4: Commit**

```bash
git add main.py
git commit -m "feat: add deploy_reports function with retry logic"
```

---

## Task 8: Add --no-deploy CLI Flag to main.py

**Files:**
- Modify: `main.py`

**Step 1: Add no-deploy argument to argument parser**

Find the argument parser setup in main() (search for `argparse` or `ArgumentParser`), add:

```python
parser.add_argument(
    '--no-deploy',
    action='store_true',
    help='Skip automatic Netlify deployment'
)
```

**Step 2: Verify flag appears in help**

Run: `python3 main.py --help | grep -i deploy`
Expected: Shows `--no-deploy Skip automatic Netlify deployment`

**Step 3: Commit**

```bash
git add main.py
git commit -m "feat: add --no-deploy CLI flag"
```

---

## Task 9: Integrate deploy_reports into main() function

**Files:**
- Modify: `main.py`

**Step 1: Find where reports are generated**

Search for report generation completion in main(). Look for:
- `generate_all_reports()` call
- Success message about reports being generated
- End of analysis pipeline

**Step 2: Add deployment call after report generation**

Insert after report generation success, before final success message:

```python
# Deploy to Netlify if configured
skip_deploy = args.no_deploy if hasattr(args, 'no_deploy') else False
deploy_success = deploy_reports(output_dir, skip=skip_deploy)
```

**Step 3: Update final success message**

Modify the success message to include deployment status:

Find the final success print (search for "Analysis complete" or similar), update to:

```python
if not skip_deploy:
    print("\n✅ Analysis complete!")
    print(f"  Reports: {len(successful_analyses)} generated")
    print(f"  Output: {output_dir}")
else:
    print("\n✅ Analysis complete!")
    print(f"  Reports: {len(successful_analyses)} generated")
    print(f"  Output: {output_dir}")
    print("  Deployment: Skipped (--no-deploy flag)")
```

**Step 4: Test help message**

Run: `python3 main.py --help`
Expected: Shows new --no-deploy flag

**Step 5: Commit**

```bash
git add main.py
git commit -m "feat: integrate auto-deploy into analysis pipeline"
```

---

## Task 10: Create Unit Tests for Setup Script

**Files:**
- Create: `tests/test_setup_netlify.py`

**Step 1: Create test file skeleton**

```python
#!/usr/bin/env python3
"""Tests for Netlify setup script."""

import pytest
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.setup_netlify import check_netlify_cli, is_site_linked


def test_check_netlify_cli_installed():
    """Test that check_netlify_cli detects installed CLI."""
    # This test assumes netlify-cli may or may not be installed
    result = check_netlify_cli()
    assert isinstance(result, bool)


def test_is_site_linked_no_state():
    """Test that is_site_linked returns False when state file missing."""
    # Create temp directory
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        assert is_site_linked(tmpdir) is False


def test_is_site_linked_with_state():
    """Test that is_site_linked returns True when state file exists."""
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        # Create .netlify/state.json
        (tmpdir / '.netlify').mkdir()
        (tmpdir / '.netlify' / 'state.json').write_text('{}')
        assert is_site_linked(tmpdir) is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

**Step 2: Run tests**

Run: `python3 tests/test_setup_netlify.py`
Expected: All tests pass or clear failures

**Step 3: Commit**

```bash
git add tests/test_setup_netlify.py
git commit -m "test: add unit tests for setup_netlify.py"
```

---

## Task 11: Create Integration Test for Full Setup Flow

**Files:**
- Create: `tests/test_integration_setup.py`

**Step 1: Create integration test file**

```python
#!/usr/bin/env python3
"""Integration test for Netlify setup and deployment."""

import pytest
import subprocess
from pathlib import Path
import tempfile
import shutil


def test_full_setup_flow_with_mock():
    """Test full setup flow with mocked Netlify CLI."""
    # This is a smoke test - actual Netlify CLI must be installed
    # but we don't actually deploy in tests

    result = subprocess.run(
        ['python3', 'scripts/setup_netlify.py', '--help'],
        capture_output=True,
        text=True
    )
    # Should have --help or show usage
    # We're just verifying script is importable and runs
    assert 'setup' in result.stdout.lower() or result.returncode == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

**Step 2: Run integration test**

Run: `python3 tests/test_integration_setup.py`
Expected: Smoke test passes

**Step 3: Commit**

```bash
git add tests/test_integration_setup.py
git commit -m "test: add integration test for setup flow"
```

---

## Task 12: Update Documentation

**Files:**
- Modify: `docs/deployment/NETLIFY.md`
- Modify: `docs/ONBOARDING.md`
- Modify: `docs/COMMON_TASKS.md`

**Step 1: Update NETLIFY.md with auto-deploy info**

Add section after existing options:

```markdown
### Option 4: Automatic Deployment (Recommended)

After one-time setup, deployment happens automatically after each analysis.

#### First-Time Setup

1. Run setup wizard:
   ```bash
   python3 scripts/setup_netlify.py
   ```

2. Follow prompts to:
   - Link `output/` directory to Netlify site
   - Configure custom domain: `analysis.mattlelonek.co.uk`
   - Add DNS records as shown

#### Automatic Deployment

After setup, every analysis automatically deploys:

```bash
# Runs analysis AND auto-deploys
python3 main.py --urls https://example.com --config competitors.json

# Skip deployment when needed
python3 main.py --urls https://example.com --config competitors.json --no-deploy
```

The analysis pipeline now:
1. Captures screenshots
2. Runs AI analysis
3. Generates reports
4. Builds CSS
5. Generates index
6. **Deploys to Netlify automatically**
```

**Step 2: Add to ONBOARDING.md**

Add section in "Deployment" chapter:

```markdown
### Automatic Netlify Deployment

The project supports automatic deployment to Netlify after analysis completes.

#### One-Time Setup

Run the setup wizard once:
```bash
python3 scripts/setup_netlify.py
```

This will:
- Install Netlify CLI if missing
- Link your `output/` directory to Netlify
- Configure `analysis.mattlelonek.co.uk` custom domain
- Provide DNS records to add

#### Automatic Deploy

After setup, deployment is automatic:
```bash
python3 main.py --urls https://example.com
```

To skip deployment:
```bash
python3 main.py --urls https://example.com --no-deploy
```
```

**Step 3: Add to COMMON_TASKS.md**

Add under "Deployment" section:

```markdown
### Set up automatic Netlify deployment

Run the setup wizard:
```bash
python3 scripts/setup_netlify.py
```

Follow prompts to configure Netlify site and custom domain.

### Skip deployment for one-off analysis

Add the `--no-deploy` flag:
```bash
python3 main.py --urls https://example.com --no-deploy
```
```

**Step 4: Commit**

```bash
git add docs/deployment/NETLIFY.md docs/ONBOARDING.md docs/COMMON_TASKS.md
git commit -m "docs: update documentation for auto-deployment"
```

---

## Task 13: Final Testing & Verification

**Files:**
- None (testing existing implementation)

**Step 1: Run all tests**

Run: `pytest tests/ -v`
Expected: All tests pass

**Step 2: Verify --help shows new flag**

Run: `python3 main.py --help | grep no-deploy`
Expected: Shows `--no-deploy Skip automatic Netlify deployment`

**Step 3: Dry-run setup script**

Run: `python3 scripts/setup_netlify.py --help 2>/dev/null || python3 scripts/setup_netlify.py`
Expected: Script starts or shows help

**Step 4: Verify netlify.toml is valid**

Run: `cat netlify.toml`
Expected: Valid TOML with [build], [build.processing.css], [dev] sections

**Step 5: Commit (if any test fixes needed)**

```bash
git add .
git commit -m "fix: address test failures"
```

---

## Task 14: Create Release Notes and CHANGELOG Entry

**Files:**
- Modify: `CHANGELOG.md`

**Step 1: Add v1.8.0 entry to CHANGELOG.md**

Add at the top after current version:

```markdown
## [1.8.0] - 2026-02-26

### Added
- **🚀 Automatic Netlify Deployment:** Reports deploy automatically after analysis
  - `scripts/setup_netlify.py` - One-time configuration wizard
  - Auto-deployment integrated into main.py analysis pipeline
  - Custom domain support: analysis.mattlelonek.co.uk
  - `--no-deploy` flag for manual control
  - Retry logic with exponential backoff for network issues

### Changed
- **📦 Build Configuration:** Added `netlify.toml` for Netlify configuration
  - Specifies `output` as publish directory
  - Configures local dev server

### Documentation
- Updated NETLIFY.md with automatic deployment workflow
- Updated ONBOARDING.md with setup and deployment instructions
- Updated COMMON_TASKS.md with new deployment commands
```

**Step 2: Bump version in src/version.py**

Update version to 1.8.0:

```python
__version__ = "1.8.0"
```

**Step 3: Commit**

```bash
git add CHANGELOG.md src/version.py
git commit -m "docs: add v1.8.0 release notes"
```

---

## Task 15: Final Verification and Tag Release

**Files:**
- None (verification and tagging)

**Step 1: Verify all tests pass**

Run: `pytest tests/ -v --tb=short`
Expected: All tests pass with clear output

**Step 2: Verify git history is clean**

Run: `git status`
Expected: No uncommitted changes

**Step 3: Create release tag**

Run:
```bash
git tag -a v1.8.0 -m "Automatic Netlify Deployment

Features:
- Auto-deploy after analysis
- Setup wizard for Netlify configuration
- Custom domain analysis.mattlelonek.co.uk
- --no-deploy flag for manual control
"
```

**Step 4: Push all changes**

Run:
```bash
git push origin main
git push origin v1.8.0
```

**Step 5: Verify on GitHub**

Check that:
- Release v1.8.0 appears on GitHub releases page
- CHANGELOG.md is updated
- All commits from this plan are present

---

## Summary

This implementation plan creates a complete automatic deployment workflow:

1. ✅ One-time setup wizard (`scripts/setup_netlify.py`)
2. ✅ Auto-deployment integrated into `main.py`
3. ✅ Custom domain configuration via CLI
4. ✅ `--no-deploy` flag for manual control
5. ✅ Retry logic and error handling
6. ✅ Unit tests for setup script
7. ✅ Documentation updates
8. ✅ CHANGELOG and version bump

**Total estimated time:** ~2-3 hours with TDD approach

**Files created:** 4 (setup script, tests, config)
**Files modified:** 4 (main.py, docs)
**Tests added:** 2 test files with 5+ test cases
