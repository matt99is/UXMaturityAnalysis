# Browser Capture Infrastructure Design

**Date:** 2026-03-02
**CLI Alignment:** Updated for unified CLI flow on 2026-03-04 (`run.sh` -> `cli.py` -> `main.py`)
**Status:** Approved
**Related Research:** `docs/research/remote-human-in-the-loop-browser-capture-2026.md`, `/home/matt99is/projects/Resources/ux-analysis/bot-detection-ecom-screenshots-2026.md`

---

## Overview

Unified infrastructure for browser screenshot capture on headless Ubuntu server, supporting both:
1. **Interactive mode** — Human-in-the-loop via VNC for CAPTCHA solving, login flows, page setup
2. **Automated mode** — Unattended capture with bot-detection evasion for batch runs

---

## Requirements

| Requirement | Solution |
|-------------|----------|
| Run on headless Ubuntu server | Xvfb virtual display |
| User can view/interact with browser | x11vnc + websockify + noVNC |
| Bypass bot detection | Patchright + persistent profiles + residential IP |
| Capture desktop and mobile viewports | Playwright viewport resizing on Xvfb display |
| CLI-first, web UI later | `cli.py` capture mode selection routes to `main.py` `--interactive` / `--auto` |

---

## Architecture

### System Components

| Component | Purpose | Port/Display |
|-----------|---------|--------------|
| Xvfb | Virtual X11 display | `:99` (1920x1080x24) |
| x11vnc | Expose display via VNC | `:5900` |
| websockify | Bridge VNC → WebSocket | `:6080` |
| noVNC | HTML5 VNC client | Static files served by websockify |
| Patchright | Stealth browser automation | Connects to display `:99` |

### Infrastructure Layers

```
Layer 3: User Interface
         ┌────────────────────────────────────┐
         │ run.sh -> cli.py -> main.py flags │
         └─────────────────┬──────────────────┘
                          │
Layer 2: Session Management
         ┌─────────────────┐
         │ BrowserSession  │
         │ Pool            │
         └────────┬────────┘
                  │
Layer 1: Infrastructure
         ┌─────────────────────────────────────┐
         │ Xvfb → x11vnc → websockify → noVNC  │
         └─────────────────────────────────────┘
```

### Capture Modes

| Mode | CLI Menu Choice | `main.py` Flag | Use Case | Flow |
|------|------------------|----------------|----------|------|
| Interactive | `Supervised` | `--interactive` | Bot-protected sites, login flows | Browser opens -> user views via noVNC -> presses Enter -> capture |
| Automated | `Automated` | `--auto` | Unattended runs | Browser opens -> delays -> scroll -> capture -> next |

---

## Viewport Handling

Xvfb runs at 1920×1080. Browser viewport is resized per capture:

| Capture | Xvfb Display | Browser Viewport |
|---------|--------------|------------------|
| Desktop | 1920×1080 | 1920×1080 |
| Mobile | 1920×1080 | 375×812 |

User sees full display via noVNC; mobile viewport appears as smaller window centered on canvas.

---

## CLI Interface

Operator entry point is `./run.sh` (tmux wrapper), which launches `cli.py`.
`cli.py` is responsible for capture mode selection and must map:
- `Supervised` -> `main.py --interactive`
- `Automated` -> `main.py --auto`

### New Arguments

| Flag | Mode | Description |
|------|------|-------------|
| `--interactive` | Interactive | Opens browser, prints noVNC URL, waits for user |
| `--auto` | Automated | Runs unattended with delays between captures |

### Interactive Flow

```
$ ./run.sh
? What do you want to do?
  Fresh analysis
? Capture mode?
  Supervised   (watch browser via noVNC URL)
...
cli.py executes: .venv/bin/python3 main.py ... --interactive

━━━ UX Maturity Analysis — Interactive Mode ━━━

✓ Xvfb display :99 ready
✓ VNC streaming at http://192.168.1.50:6080/vnc.html

[1/16] Capturing: tesco.com
       → Browser opened. View/interact at:
         http://192.168.1.50:6080/vnc.html

       [Press Enter when ready to capture screenshots...]

       ✓ Captured desktop.png (1920×1080)
       ✓ Captured mobile.png (375×812)
```

### Automated Flow

```
$ ./run.sh
? What do you want to do?
  Fresh analysis
? Capture mode?
  Automated    (fully unattended)
...
cli.py executes: .venv/bin/python3 main.py ... --auto

━━━ UX Maturity Analysis — Automated Mode ━━━

[1/16] Capturing: tesco.com
       Waiting 5s for page load...
       Scrolling to trigger lazy content...
       ✓ Captured desktop.png
       ✓ Captured mobile.png
       Waiting 8s before next capture...

[2/16] Capturing: sainsburys.co.uk
       ⚠ Bot detection triggered: Cloudflare challenge
       Skipping — run with --interactive to handle manually
```

---

## Code Changes

### New Module: `src/browser_session.py`

```python
class DisplayAllocator:
    """Manages Xvfb display numbers for concurrent sessions"""
    def allocate(self) -> int
    def release(self, display: int)

class BrowserSession:
    """Single browser session with VNC streaming"""
    async def start(self, url: str, viewport: dict)
    async def get_vnc_url(self) -> str
    async def wait_for_user_ready(self)
    async def capture_screenshot(self, viewport: dict) -> str
    async def close(self)

class BrowserSessionPool:
    """Manages multiple concurrent browser sessions"""
    async def acquire(self, session_id: str) -> BrowserSession
    async def release(self, session_id: str)
```

### Modified Files

| File | Changes |
|------|---------|
| `src/analyzers/screenshot_capture.py` | Patchright import, persistent context, remove playwright-stealth |
| `main.py` | `--interactive` and `--auto` mode handling, session pool integration |
| `cli.py` | Capture mode routing (`Supervised` -> `--interactive`, `Automated` -> `--auto`) |
| `requirements.txt` | Add `patchright`, remove `playwright-stealth` |

---

## Infrastructure Setup

### System Packages

```bash
sudo apt-get install -y \
    xvfb x11vnc websockify novnc \
    libgbm1 libnss3 libatk-bridge2.0-0 libdrm2 \
    fonts-liberation fonts-dejavu fonts-noto
```

### Python Packages

```bash
pip install patchright
patchright install chrome
```

### Systemd Services

Three always-on services:
- `xvfb.service` — Virtual display on :99
- `x11vnc.service` — VNC server on :5900
- `vnc-bridge.service` — WebSocket bridge on :6080

### Directory Structure

```
browser_profiles/
├── desktop/    # Persistent Chrome profile
└── mobile/     # Separate profile for mobile
```

---

## Error Handling

### Bot Detection

| Scenario | Interactive | Automated |
|----------|-------------|-----------|
| Cloudflare | User solves | Skip + warn |
| CAPTCHA | User solves | Skip + warn |
| Login required | User logs in | Skip + warn |

### Fallback Chain

1. Try automated capture with Patchright
2. If blocked and `--interactive`: prompt user via noVNC
3. If still failing: log to `blocked_sites.json`, skip
4. Post-run summary lists blocked sites

### Timeouts

| Timeout | Default |
|---------|---------|
| Page load | 30s |
| User inactivity | 5 min |
| Between captures (auto) | 3-10s random |

---

## Verification

After setup, verify with:

```bash
# Check services
DISPLAY=:99 xdpyinfo | head -5
curl http://localhost:6080/vnc.html | head -10

# Test Patchright + Xvfb
DISPLAY=:99 python -c "
from patchright.sync_api import sync_playwright
with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context('./test_profile', channel='chrome', headless=False)
    page = ctx.new_page()
    page.goto('https://bot.sannysoft.com')
    page.screenshot(path='test_detection.png')
    ctx.close()
"
```

Test against detection sites:
- `bot.sannysoft.com` — CDP/webdriver flags
- `pixelscan.net` — Fingerprint consistency
- `abrahamjuliot.github.io/creepjs` — Target trust score >85%

---

## Future: Web UI Integration

When wiring up the "new analysis" button:
1. API endpoint triggers capture session
2. Returns noVNC URL to frontend
3. Frontend opens URL in new tab
4. User interacts, signals ready
5. API captures screenshots, returns results

---

## References

- Research paper: `docs/research/remote-human-in-the-loop-browser-capture-2026.md`
- Bot detection research: `/home/matt99is/projects/Resources/ux-analysis/bot-detection-ecom-screenshots-2026.md`
- Patchright: https://github.com/Kaliiiiiiiiii-Vinyzu/patchright-python
