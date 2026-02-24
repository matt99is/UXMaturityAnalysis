# Bot Detection Handling Guide

This guide explains practical ways to handle anti-bot protections during screenshot capture.

## Current Capture Behavior

- Default run mode is interactive browser-assisted capture for normal analysis runs.
- In this mode, you can manually navigate, close modals, and solve challenge pages before capture.
- For heavily protected sites, manual screenshot mode is the most reliable path.

## Recommended Modes

### 1. Interactive Capture (Default)

Best for:
- Most competitors
- Sites with moderate anti-bot checks
- Checkout/product flows where manual setup is needed

Run:

```bash
python3 main.py --config competitors.json --analysis-type product_pages
```

What happens:
- Browser opens visibly
- You prepare the page state
- Press Enter to capture desktop/mobile screenshots

### 2. Manual Screenshot Mode (Strongly Protected Sites)

Best for:
- Amazon/eBay-style protections
- Login-gated flows
- Cases where automated navigation is repeatedly blocked

Run:

```bash
python3 main.py --manual-mode --screenshots-dir ./my-screenshots --config competitors.json
```

Supported screenshot names:
- `{competitor}_desktop.png` + `{competitor}_mobile.png`
- `{competitor}-desktop.png` + `{competitor}-mobile.png`
- `desktop.png` + `mobile.png` (single-competitor case)

## Practical Tips

- Use full browser (not private automation profile) for challenge-heavy domains.
- Complete cookie banners and location popups before capture.
- Verify page state is the intended audit state (cart populated, variant selected, etc.).
- Keep viewport intent aligned with criteria:
  - Desktop: 1920x1080
  - Mobile: 375x812

## Troubleshooting

### Access denied / CAPTCHA keeps recurring
- Switch to manual screenshot mode.

### Captured screenshot shows blocker page
- Retry capture after solving challenge and reloading target page.

### Manual screenshots not found
- Validate `--screenshots-dir` path.
- Ensure file names match expected patterns.

### Browser does not launch
- Ensure Playwright browser is installed:

```bash
python3 -m playwright install chromium
```

## Related Docs

- `README.md` (main usage)
- `docs/ARCHITECTURE.md` (pipeline design)
- `docs/SAMPLE_OUTPUT.md` (report artifacts)
