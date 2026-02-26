# Automatic Netlify Deployment - Design Document

**Date:** 2026-02-26
**Status:** Approved
**Author:** Claude + Matthew Lelonek

---

## Overview

Integrate automatic Netlify deployment into the UX Maturity Analysis workflow. When reports are generated, they should automatically deploy to `https://analysis.mattlelonek.co.uk`.

---

## Requirements

### Functional Requirements

- **FR1:** Deploy automatically to Netlify after successful report generation
- **FR2:** Configure custom domain `analysis.mattlelonek.co.uk` via CLI
- **FR3:** Provide option to skip deployment (`--no-deploy` flag)
- **FR4:** One-time setup script for initial Netlify site configuration
- **FR5:** Clear error messages if Netlify CLI is missing or site not linked

### Non-Functional Requirements

- **NFR1:** Deployment only happens on successful analysis (no partial deployments)
- **NFR2:** Netlify CLI auto-install if missing
- **NFR3:** Deployment completes within 30 seconds
- **NFR4:** User feedback on each deployment step

---

## Architecture

```
main.py Analysis Pipeline
    ↓
[1] Screenshot Capture
    ↓
[2] AI Analysis
    ↓
[3] Report Generation
    ↓
[4] CSS Build
    ↓
[5] Index Generation
    ↓
[6] Auto-Deploy (NEW)
    ↓
[7] Success Message with URL
```

### Deployment Flow

**One-Time Setup:**
```
python3 scripts/setup_netlify.py
    ↓
Install netlify-cli (if missing)
    ↓
Link output/ directory to Netlify site
    ↓
Configure custom domain: analysis.mattlelonek.co.uk
    ↓
Save credentials to .netlify/state.json
```

**Automatic Deployment (after each analysis):**
```
main.py completes reports
    ↓
Check: .netlify/state.json exists?
    ├─ No → Warning message, skip deployment
    └─ Yes → Deploy
    ↓
Run: netlify deploy --prod --dir=output
    ↓
Display: https://analysis.mattlelonek.co.uk
```

---

## Components

### 1. Setup Script (`scripts/setup_netlify.py`)

**Purpose:** One-time Netlify site configuration

**Functions:**

```python
def check_netlify_cli() -> bool:
    """Check if netlify-cli is installed."""

def install_netlify_cli() -> bool:
    """Install netlify-cli via npm."""

def is_site_linked() -> bool:
    """Check if output/ is already linked to a Netlify site."""

def link_site() -> bool:
    """Link output/ directory to new or existing Netlify site."""

def configure_custom_domain(site_id: str, domain: str) -> bool:
    """Configure analysis.mattlelonek.co.uk as custom domain."""

def main():
    """Run setup wizard."""
```

**User Flow:**

```
$ python3 scripts/setup_netlify.py

🔧 Netlify One-Time Setup

[1/4] Checking Netlify CLI...
✓ netlify-cli is installed

[2/4] Checking for existing site link...
No site linked. Linking now...
→ Site name: ux-analysis-reports
→ Team: personal
✓ Site linked successfully

[3/4] Configuring custom domain...
→ Domain: analysis.mattlelonek.co.uk
⚠️  DNS configuration required!
Add the following records to your DNS:
  CNAME analysis -> <netlify-site>.netlify.app
✓ Domain configured

[4/4] Saving configuration...
✓ Setup complete!

Next steps:
  1. Add DNS records to your domain provider
  2. Deploy: python3 main.py --urls https://example.com
```

### 2. Deployment Integration (`main.py`)

**Add to main.py:**

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

    if not (output_dir / '.netlify' / 'state.json').exists():
        print("⚠️  Netlify site not configured")
        print("  Run: python3 scripts/setup_netlify.py")
        return False

    print("🚀 Deploying to Netlify...")

    # Run netlify deploy
    result = subprocess.run(
        ['netlify', 'deploy', '--prod', '--dir', str(output_dir)],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        print("✅ Deployment successful: https://analysis.mattlelonek.co.uk")
        return True
    else:
        print(f"❌ Deployment failed: {result.stderr}")
        return False
```

**Integration Point:** Call `deploy_reports()` after report generation succeeds.

**CLI Flag:**

```python
parser.add_argument(
    '--no-deploy',
    action='store_true',
    help='Skip automatic Netlify deployment'
)
```

### 3. Build Configuration (`netlify.toml`)

**Purpose:** Netlify build and deployment configuration

**Location:** Project root

**Content:**

```toml
[build]
  publish = "output"

[build.processing.css]
  bundle = false

[dev]
  command = "python3 -m http.server 8000 --directory output"
  publish = "output"
```

---

## Data Flow

### Setup Data Flow

```
setup_netlify.py
    ↓
.npmrc → Create for CLI installation
    ↓
output/.netlify/ → Directory structure
    └── state.json → Site ID, access tokens
    ↓
Netlify API → Site configuration
    └── Custom domains
```

### Deployment Data Flow

```
main.py
    ↓
output/ → Static files to deploy
    ├── index.html
    ├── css/main.css
    └── audits/*
    ↓
netlify deploy --prod --dir=output
    ↓
Netlify CDN → Global distribution
    ↓
https://analysis.mattlelonek.co.uk
```

---

## Error Handling

### Error Scenarios

| Scenario | Handling |
|-----------|-----------|
| Netlify CLI not installed | Auto-install via npm, fail if npm missing |
| `npm install` fails | Show manual install instructions |
| Site not linked | Show setup script command, skip deployment |
| Network timeout | Retry 3 times with exponential backoff |
| DNS records missing | Show required DNS records, proceed with .netlify.app URL |
| Deployment fails | Keep local files, show manual deploy option |
| Custom domain not ready | Deploy to netlify.app URL, show domain setup progress |

### User Messages

**Success:**
```
✅ Analysis complete: 5 reports generated
✅ CSS built: output/css/main.css
✅ Index updated: output/index.html
🚀 Deploying to Netlify...
✅ Deployment successful: https://analysis.mattlelonek.co.uk
```

**Missing Setup:**
```
⚠️  Netlify site not configured
Run: python3 scripts/setup_netlify.py
Deployment skipped. Reports saved locally.
```

**Network Error:**
```
❌ Deployment failed: Connection timeout
Retrying... (1/3)
```

---

## Testing Strategy

### Pre-Deployment Tests

1. **CSS Build Test:** Verify `output/css/main.css` exists and > 1KB
2. **Index Test:** Verify `output/index.html` contains expected HTML structure
3. **Report Count:** At least one report in `output/audits/`
4. **Netlify CLI:** `netlify --version` succeeds

### Deployment Tests

1. **Draft Deploy:** First deployment uses `--draft` flag for preview
2. **Preview Verification:** User confirms preview URL loads correctly
3. **Production Deploy:** Promote to production after preview confirms
4. **Custom Domain Test:** Verify `analysis.mattlelonek.co.uk` resolves correctly

### Rollback Strategy

- Local `output/` directory never deleted
- Netlify retains last 5 deployments (accessible via CLI/dashboard)
- Manual redeploy option: `python3 scripts/deploy_netlify.py`

---

## CLI Usage

### One-Time Setup

```bash
# Install dependencies (if needed)
npm install -g netlify-cli

# Run setup wizard
python3 scripts/setup_netlify.py

# Add DNS records as prompted
```

### Regular Usage

```bash
# Auto-deploy (default)
python3 main.py --urls https://example.com --config competitors.json

# Skip deployment
python3 main.py --urls https://example.com --no-deploy
```

---

## Implementation Plan

See `docs/plans/2026-02-26-netlify-auto-deploy-implementation.md` for detailed implementation steps.

---

## Sign-Off

**Design approved by:** Matthew Lelonek
**Date:** 2026-02-26
**Status:** Ready for implementation
