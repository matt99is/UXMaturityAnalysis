# Human-in-the-Loop Browser Capture from Headless Servers
## Enabling Web GUI Users to Interact with Remote Browser Sessions

**Research Paper — March 2026**

---

## Executive Summary

This paper addresses a critical architectural challenge for the UX Maturity Analysis platform: **How can users of a web-based GUI interact with browser sessions running on a headless remote server?** This capability is essential for:

1. **Bot-protected sites** — Users must solve CAPTCHAs or pass Cloudflare challenges
2. **Login-gated flows** — Users must authenticate before capturing screenshots
3. **Complex page setup** — Users must add items to baskets, select variants, dismiss modals

We examine five architectural approaches, evaluate them against our requirements, and provide implementation recommendations.

---

## The Problem Space

### Current State (CLI-Based)

The existing system (`screenshot_capture.py`) supports two modes:

| Mode | Function | Browser | User Interaction |
|------|----------|---------|------------------|
| Interactive | `capture_with_interaction()` | Visible (`headless=False`) | Local terminal — waits for Enter key |
| Automated | `capture_multiple_viewports()` | Headless | None |

**Limitation**: Both modes require the browser to run on the same machine as the user. For a web GUI, the browser runs on a remote server — the user cannot see or interact with it.

### The Gap

```
┌─────────────────┐                    ┌─────────────────┐
│   User's Web    │                    │  Remote Server  │
│   Browser       │                    │  (Headless)     │
│                 │                    │                 │
│  ┌───────────┐  │     HTTP/WS       │  ┌───────────┐  │
│  │  Web GUI  │  │◄──────────────────►│  │ Playwright│  │
│  │  (React)  │  │                    │  │ Browser   │  │
│  └───────────┘  │                    │  └───────────┘  │
│                 │                    │       ?         │
│   No way to    │                    │  User cannot    │
│   see/control  │                    │  interact with  │
│   the browser  │                    │  this browser   │
└─────────────────┘                    └─────────────────┘
```

### Requirements Matrix

| Requirement | Priority | Notes |
|-------------|----------|-------|
| User can see browser in real-time | Critical | Essential for CAPTCHA/challenge solving |
| User can interact (click, type, scroll) | Critical | Login flows, basket setup |
| Works through standard web browser | Critical | No client software installation |
| Supports multiple concurrent users | High | Multi-tenant SaaS future |
| Minimal latency | High | Real-time interaction feel |
| Maintains bot-detection evasion | Medium | Patchright/Camoufox compatibility |
| Audit trail / session recording | Medium | Debugging, compliance |
| Cost-effective | Medium | Cloud infrastructure costs |

---

## Architectural Approaches

### Approach 1: VNC + noVNC (Remote Desktop Stream)

**Architecture:**
```
┌─────────────────────────────────────────────────────────────────┐
│                        Remote Server                            │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐  │
│  │ Xvfb     │───►│ x11vnc   │───►│websockify│───►│ noVNC    │  │
│  │ :99      │    │ :5900    │    │ :6080    │    │ HTML5    │  │
│  │1920x1080 │    │          │    │          │    │ client   │  │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘  │
│       ▲                                              │         │
│       │                                              ▼         │
│  ┌──────────┐                                 ┌──────────┐     │
│  │Playwright│                                 │ Embed in │     │
│  │ Browser  │                                 │ Web GUI  │     │
│  │ on :99   │                                 │ iframe   │     │
│  └──────────┘                                 └──────────┘     │
└─────────────────────────────────────────────────────────────────┘
```

**How it works:**
1. Xvfb creates a virtual X11 display (e.g., `:99`)
2. Playwright launches browser on that display (`DISPLAY=:99`)
3. x11vnc exposes the display via VNC protocol (port 5900)
4. websockify bridges VNC to WebSockets (port 6080)
5. noVNC (HTML5/JS client) connects from user's browser
6. Embed noVNC in web GUI via iframe

**Implementation:**

```bash
# Server setup (systemd)
# /etc/systemd/system/xvfb.service
[Unit]
Description=X Virtual Framebuffer
After=network.target

[Service]
ExecStart=/usr/bin/Xvfb :99 -screen 0 1920x1080x24 -ac +extension GLX
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# /etc/systemd/system/novnc.service
[Unit]
Description=noVNC WebSocket Proxy
After=xvfb.service

[Service]
ExecStart=/usr/bin/websockify --web /usr/share/novnc 6080 localhost:5900
Restart=always

[Install]
WantedBy=multi-user.target
```

```python
# Python — start browser on virtual display
import os
os.environ["DISPLAY"] = ":99"

from patchright.async_api import async_playwright

async def interactive_capture(url: str):
    async with async_playwright() as p:
        # Launch in headed mode (visible on Xvfb display)
        context = await p.chromium.launch_persistent_context(
            user_data_dir="./browser_profile",
            channel="chrome",
            headless=False,  # Headed, but on virtual display
        )
        page = await context.new_page()
        await page.goto(url)

        # Signal to web GUI that browser is ready
        # User interacts via noVNC...

        # Wait for user to signal completion (via API call)
        await wait_for_user_signal()

        # Capture screenshots
        await page.screenshot(path="desktop.png", full_page=True)
        await context.close()
```

**Web GUI Integration:**
```html
<!-- React component -->
<iframe
  src="http://server:6080/vnc.html?autoconnect=true&password=secret"
  width="100%"
  height="600px"
/>
<button onClick={signalCaptureComplete}>
  Ready to Capture
</button>
```

**Pros:**
- ✅ Mature, well-documented stack
- ✅ Full desktop visibility and control
- ✅ Works with any browser automation tool
- ✅ Can run multiple sessions (different displays)
- ✅ Session recording possible (x11vnc has built-in recording)
- ✅ Works through firewalls (single WebSocket port)

**Cons:**
- ❌ Latency (VNC protocol wasn't designed for low-latency interaction)
- ❌ Bandwidth-intensive (streaming full desktop)
- ❌ Requires Xvfb + x11vnc + websockify + noVNC (4 components)
- ❌ Per-session display management complexity
- ❌ No native multi-tenancy (need display pool)

**Cost Assessment:** Low infrastructure cost, moderate complexity.

**Latency:** 100-500ms depending on network and resolution.

---

### Approach 2: Chrome DevTools Protocol (CDP) Remote Debugging

**Architecture:**
```
┌─────────────────────────────────────────────────────────────────┐
│                        Remote Server                            │
│  ┌──────────────────────┐         ┌──────────────────────┐     │
│  │ Chrome/Chromium      │         │ WebSocket Proxy      │     │
│  │ --remote-debugging   │◄───────►│ (nginx/cloudflared)  │     │
│  │ :9222                │  CDP    │ :443 (WSS)           │     │
│  └──────────────────────┘         └──────────────────────┘     │
│          │                                  │                   │
│          │                                  ▼                   │
│          │                         ┌──────────────────┐        │
│          │                         │ User's Browser   │        │
│          │                         │ DevTools Frontend│        │
│          │                         │ (chrome-devtools-│        │
│          │                         │  frontend)       │        │
│          │                         └──────────────────┘        │
│          ▼                                                     │
│  ┌──────────────────────┐                                      │
│  │ Playwright           │                                      │
│  │ connects to CDP      │                                      │
│  └──────────────────────┘                                      │
└─────────────────────────────────────────────────────────────────┘
```

**How it works:**
1. Chrome launched with `--remote-debugging-port=9222`
2. CDP exposes full browser control via WebSocket
3. User connects to DevTools frontend (hosted or `chrome-devtools-frontend`)
4. Playwright can share the same browser instance via CDP endpoint

**Implementation:**

```python
# Server — launch browser with remote debugging
from patchright.async_api import async_playwright

async def launch_remote_debug_browser():
    async with async_playwright() as p:
        # Launch with CDP exposed
        browser = await p.chromium.launch(
            headless=False,
            args=[
                "--remote-debugging-port=9222",
                "--remote-debugging-address=0.0.0.0",  # Bind to all interfaces
            ]
        )

        # Get CDP endpoint for Playwright connection
        cdp_endpoint = browser.ws_endpoint
        # ws://localhost:9222/devtools/browser/...

        # Store endpoint for client retrieval
        await store_endpoint_for_session(session_id, cdp_endpoint)
```

```javascript
// Web GUI — connect to remote DevTools
import { RTCEngine } from '@devtools-frontend/remote';

async function connectToRemoteBrowser(cdpUrl) {
  // Use Chrome DevTools Frontend
  const iframe = document.createElement('iframe');
  iframe.src = `https://chrome-devtools-frontend.appspot.com/serve_file/@crdt/inspector.html?ws=${cdpUrl}`;
  document.body.appendChild(iframe);
}
```

**Alternative: Browserbase-style Live View**
```javascript
// Browserbase exposes a /ws/liveview endpoint
const ws = new WebSocket('wss://account.browserbase.com/ws/liveview?browserId=xxx');

// Stream is video/frames, not full DevTools
ws.onmessage = (event) => {
  // Render frame to canvas
};
```

**Pros:**
- ✅ Native browser control (not just screen view)
- ✅ Lower bandwidth than VNC (sends DOM events, not pixels)
- ✅ Can inspect elements, debug JS, view network
- ✅ Playwright can share the same browser session
- ✅ Better for precise interactions (click exact elements)

**Cons:**
- ❌ Requires DevTools frontend hosting or iframe to Google's hosted version
- ❌ Security concern: CDP gives full browser control
- ❌ Need WebSocket proxy for HTTPS (browsers block ws:// from https://)
- ❌ Not designed for multi-tenant isolation
- ❌ DevTools UI is developer-focused, not end-user friendly

**Cost Assessment:** Low infrastructure cost, moderate security complexity.

**Latency:** 50-200ms (better than VNC for interactions).

---

### Approach 3: Cloud Browser Services (Browserbase / E2B)

**Architecture:**
```
┌─────────────────┐                    ┌─────────────────────────┐
│   User's Web    │                    │  Browserbase / E2B      │
│   Browser       │                    │  (Managed Service)      │
│                 │                    │                         │
│  ┌───────────┐  │     HTTPS/WS      │  ┌───────────────────┐  │
│  │  Web GUI  │  │◄─────────────────►│  │ Browser Instance  │  │
│  │           │  │                   │  │ + Live View (VNC) │  │
│  │  Embed    │  │                   │  │ + CDP Endpoint    │  │
│  │  Live View│  │                   │  │ + Screenshot API  │  │
│  └───────────┘  │                   │  └───────────────────┘  │
│                 │                   │           │             │
└─────────────────┘                   │           ▼             │
                                      │  ┌───────────────────┐  │
                                      │  │ Managed Infra     │  │
                                      │  │ - Anti-detection  │  │
                                      │  │ - Proxies         │  │
                                      │  │ - Scaling         │  │
                                      │  └───────────────────┘  │
                                      └─────────────────────────┘
```

**How it works:**
1. API call creates browser instance
2. Service returns Live View URL + CDP endpoint
3. Embed Live View in web GUI (iframe)
4. User interacts via Live View
5. Call Screenshot API when ready

**Implementation (Browserbase):**

```python
# Backend — create browser session
import httpx

async def create_browser_session():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://www.browserbase.com/v1/sessions",
            headers={"x-bb-api-key": BROWSERBASE_API_KEY},
            json={
                "projectId": PROJECT_ID,
                "browserSettings": {
                    "fingerprint": {
                        "browsers": ["chrome"],
                        "devices": ["desktop"],
                    }
                }
            }
        )

        session = response.json()
        return {
            "session_id": session["id"],
            "cdp_url": session["connectUrl"],  # For Playwright
            "live_view_url": session["liveViewUrl"],  # For iframe
        }
```

```javascript
// Frontend — embed live view
function BrowserCapture({ sessionId }) {
  const { live_view_url, cdp_url } = useBrowserSession(sessionId);

  return (
    <div>
      <iframe src={live_view_url} width="100%" height="500px" />
      <button onClick={() => captureScreenshot(sessionId)}>
        Capture Screenshot
      </button>
    </div>
  );
}
```

**Implementation (E2B Desktop):**

```python
from e2b_desktop import Desktop

async def create_desktop_session():
    desktop = Desktop()
    await desktop.start()

    # Open browser in E2B desktop
    await desktop.open_url("https://example.com")

    # Get VNC URL for embedding
    vnc_url = desktop.get_vnc_url()

    return {
        "desktop_id": desktop.id,
        "vnc_url": vnc_url,
    }
```

**Pros:**
- ✅ Zero infrastructure management
- ✅ Built-in anti-detection (residential proxies, fingerprint rotation)
- ✅ Designed for multi-tenancy
- ✅ Managed scaling (spin up 1000 browsers instantly)
- ✅ SOC-2 / HIPAA compliance available
- ✅ Built-in session recording and debugging

**Cons:**
- ❌ Cost: ~$0.05-0.10 per browser-minute (can get expensive)
- ❌ Vendor lock-in
- ❌ Less control over browser fingerprint
- ❌ May not support all Playwright features
- ❌ Network latency to cloud provider

**Cost Assessment:**
- Browserbase: ~$0.05/minute per browser
- E2B: ~$0.03/minute per sandbox
- For 16 competitors × 2 minutes each = ~$1.60 per analysis run

**Latency:** 100-300ms (depends on cloud region).

---

### Approach 4: Selenium Grid + noVNC (Enterprise Pattern)

**Architecture:**
```
┌──────────────────────────────────────────────────────────────────────────┐
│                          Selenium Grid Cluster                           │
│                                                                          │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐                    │
│  │ Hub         │   │ Node 1      │   │ Node 2      │   ...              │
│  │ :4444       │   │ Chrome      │   │ Firefox     │                    │
│  │             │   │ + VNC :5900 │   │ + VNC :5901 │                    │
│  │             │   │ + noVNC     │   │ + noVNC     │                    │
│  │             │   │   :7900     │   │   :7901     │                    │
│  └─────────────┘   └─────────────┘   └─────────────┘                    │
│         │                 │                 │                            │
│         └─────────────────┴─────────────────┘                            │
│                           │                                              │
│                           ▼                                              │
│                    ┌─────────────┐                                       │
│                    │ Web GUI     │                                       │
│                    │ (select     │                                       │
│                    │  node VNC)  │                                       │
│                    └─────────────┘                                       │
└──────────────────────────────────────────────────────────────────────────┘
```

**How it works:**
1. Selenium Grid manages browser nodes
2. Each node runs Chrome/Firefox with VNC enabled
3. noVNC provides web access to each node
4. User selects node and views/interacts via noVNC
5. Playwright can also connect to Grid (via WebDriver)

**Implementation:**

```yaml
# docker-compose.yml
version: '3'
services:
  selenium-hub:
    image: selenium/hub:4.32.0
    ports:
      - "4444:4444"

  chrome-node:
    image: selenium/node-chrome:4.32.0
    depends_on:
      - selenium-hub
    environment:
      - SE_EVENT_BUS_HOST=selenium-hub
      - SE_EVENT_BUS_PUBLISH_PORT=4442
      - SE_EVENT_BUS_SUBSCRIBE_PORT=4443
      - SE_VNC_NO_PASSWORD=1
      - SE_NOVNC=true
    ports:
      - "7900:7900"  # noVNC
      - "5900:5900"  # VNC
    shm_size: '2gb'
```

```python
# Connect Playwright to Selenium Grid
from playwright.sync_api import sync_playwright

def connect_to_grid():
    with sync_playwright() as p:
        # Connect via CDP-over-WebDriver
        browser = p.chromium.connect_over_cdp(
            "http://selenium-hub:4444/wd/hub"
        )
        page = browser.new_page()
        page.goto("https://example.com")
        # ...
```

**Pros:**
- ✅ Battle-tested enterprise solution
- ✅ Native multi-tenancy (multiple nodes)
- ✅ Built-in VNC/noVNC (official Docker images)
- ✅ Can mix Chrome and Firefox nodes
- ✅ Automatic session queue management
- ✅ Video recording built-in

**Cons:**
- ❌ Heavier infrastructure (Grid + multiple nodes)
- ❌ Selenium focus (Playwright support is secondary)
- ❌ VNC latency issues remain
- ❌ Resource-intensive (each node = full browser + VNC)
- ❌ Complex scaling (manual node provisioning)

**Cost Assessment:** Moderate infrastructure cost, high operational complexity.

---

### Approach 5: Custom WebSocket Stream (Lightweight Video)

**Architecture:**
```
┌─────────────────────────────────────────────────────────────────┐
│                        Remote Server                            │
│                                                                 │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐  │
│  │ Playwright│   │ Frame    │   │ WebSocket│   │ Web GUI  │  │
│  │ Browser  │───►│ Capture  │───►│ Server   │───►│ Canvas   │  │
│  │          │    │ (MJPEG/  │    │ :8765    │    │ Render   │  │
│  │          │    │ WebP)    │    │          │    │          │  │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘  │
│       ▲                                              │         │
│       │              ┌──────────┐                    │         │
│       └──────────────│ Input    │◄───────────────────┘         │
│                      │ Handler  │   Mouse/Keyboard events       │
│                      │ (CDP)    │                               │
│                      └──────────┘                               │
└─────────────────────────────────────────────────────────────────┘
```

**How it works:**
1. Periodically capture screenshots from browser (e.g., 10 FPS)
2. Stream frames to client via WebSocket
3. Client renders frames to `<canvas>`
4. Client sends mouse/keyboard events back via WebSocket
5. Server translates events to CDP input commands

**Implementation:**

```python
# Server — frame streaming + input handling
import asyncio
import websockets
import base64
from patchright.async_api import async_playwright

class BrowserStreamSession:
    def __init__(self):
        self.browser = None
        self.page = None
        self.clients = set()

    async def start(self):
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=False)
        self.page = await self.browser.new_page()

        # Start frame capture loop
        asyncio.create_task(self.stream_frames())

    async def stream_frames(self):
        while True:
            if self.page and self.clients:
                # Capture frame
                screenshot = await self.page.screenshot(type="jpeg", quality=70)
                frame_b64 = base64.b64encode(screenshot).decode()

                # Broadcast to all clients
                message = json.dumps({"type": "frame", "data": frame_b64})
                await asyncio.gather(*[c.send(message) for c in self.clients])

            await asyncio.sleep(0.1)  # ~10 FPS

    async def handle_input(self, event):
        """Handle mouse/keyboard events from client"""
        if event["type"] == "click":
            await self.page.mouse.click(event["x"], event["y"])
        elif event["type"] == "type":
            await self.page.keyboard.type(event["text"])
        elif event["type"] == "scroll":
            await self.page.evaluate(f"window.scrollBy(0, {event['deltaY']})")

    async def websocket_handler(self, websocket):
        self.clients.add(websocket)
        try:
            async for message in websocket:
                event = json.loads(message)
                await self.handle_input(event)
        finally:
            self.clients.remove(websocket)
```

```javascript
// Client — render frames + send input
class RemoteBrowser {
  constructor(canvas, wsUrl) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
    this.ws = new WebSocket(wsUrl);

    this.ws.onmessage = (event) => {
      const { type, data } = JSON.parse(event.data);
      if (type === 'frame') {
        this.renderFrame(data);
      }
    };

    this.setupInputHandlers();
  }

  renderFrame(b64Data) {
    const img = new Image();
    img.onload = () => {
      this.ctx.drawImage(img, 0, 0, this.canvas.width, this.canvas.height);
    };
    img.src = `data:image/jpeg;base64,${b64Data}`;
  }

  setupInputHandlers() {
    this.canvas.addEventListener('click', (e) => {
      const rect = this.canvas.getBoundingClientRect();
      const x = (e.clientX - rect.left) * (1920 / rect.width);
      const y = (e.clientY - rect.top) * (1080 / rect.height);

      this.ws.send(JSON.stringify({ type: 'click', x, y }));
    });

    this.canvas.addEventListener('keydown', (e) => {
      this.ws.send(JSON.stringify({ type: 'type', text: e.key }));
    });
  }
}
```

**Pros:**
- ✅ Full control over implementation
- ✅ Can optimize for latency (adjust FPS, quality)
- ✅ No external dependencies (no VNC stack)
- ✅ Natural multi-tenancy (one WebSocket per session)
- ✅ Can add custom overlays, annotations
- ✅ Lower resource usage than full VNC

**Cons:**
- ❌ Significant development effort
- ❌ Input handling is complex (coordinate translation, keyboard mapping)
- ❌ No scroll wheel, right-click, drag-drop without extra work
- ❌ Must handle edge cases (canvas resize, connection drops)
- ❌ Not as battle-tested as VNC

**Cost Assessment:** Low infrastructure cost, high development cost.

**Latency:** 50-150ms (depends on frame rate and network).

---

## Comparison Matrix

| Factor | VNC/noVNC | CDP Remote | Cloud Service | Selenium Grid | Custom WS |
|--------|-----------|------------|---------------|---------------|-----------|
| **Latency** | 100-500ms | 50-200ms | 100-300ms | 100-500ms | 50-150ms |
| **Infra Cost** | Low | Low | High ($0.05/min) | Medium | Low |
| **Dev Cost** | Low | Medium | Low | Medium | High |
| **Multi-tenancy** | Complex | Complex | Native | Native | Native |
| **User Experience** | Good | Excellent | Good | Good | Excellent |
| **Bot Evasion** | Maintained | Maintained | Built-in | Maintained | Maintained |
| **Session Recording** | Easy | Hard | Built-in | Built-in | Custom |
| **Scalability** | Manual | Manual | Auto | Manual | Manual |
| **Security** | Standard | CDP Risk | Managed | Standard | Standard |

---

## Integration with Existing Research

### Overlap with Bot Detection Research

The existing `bot-detection-ecom-screenshots-2026.md` research covers **fully automated capture** with bot evasion. Key overlaps:

| Bot Detection Research | This Paper |
|------------------------|------------|
| Patchright for CDP patching | Required regardless of approach |
| Xvfb for virtual display | Core component of VNC approach |
| Residential proxies | Critical for cloud services; optional for self-hosted |
| Fingerprint consistency | Must maintain when user interacts |

**Key Insight:** Human-in-the-loop actually **reduces** bot detection risk. When a real human solves a CAPTCHA or navigates a login flow, the behavioral signals are genuinely human. The automation only needs to capture the screenshot afterward.

### Hybrid Architecture Recommendation

Combining both research streams:

```
┌─────────────────────────────────────────────────────────────────┐
│                      Recommended Hybrid                         │
│                                                                 │
│  1. Attempt automated capture with Patchright + Xvfb           │
│     │                                                          │
│     ├─► Success → Continue to next competitor                  │
│     │                                                          │
│     └─► Bot detected / Login required →                        │
│          │                                                     │
│          ▼                                                     │
│  2. Spawn interactive session (VNC + noVNC)                    │
│     │                                                          │
│     ├─► User solves challenge / logs in                        │
│     │                                                          │
│     └─► Capture screenshot when user signals ready             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Recommended Architecture for UX Maturity Analysis

### Phase 1: MVP (Self-Hosted VNC)

**Target:** Enable web GUI users to interact with browser on remote server.

**Components:**
- Xvfb (virtual display)
- x11vnc (VNC server)
- websockify (WebSocket bridge)
- noVNC (HTML5 client)
- Session management API

**Implementation Priority:**

1. **Session Pool Manager**
   ```python
   class BrowserSessionPool:
       def __init__(self, max_sessions=10):
           self.sessions = {}  # session_id -> BrowserSession

       async def acquire_session(self, user_id: str) -> BrowserSession:
           # Create or reuse session
           pass

       async def release_session(self, session_id: str):
           # Clean up session
           pass
   ```

2. **VNC Display Allocator**
   ```python
   class DisplayAllocator:
       def __init__(self, base_display=99, max_displays=10):
           self.available = list(range(base_display, base_display + max_displays))

       def allocate(self) -> int:
           return self.available.pop()

       def release(self, display: int):
           self.available.append(display)
   ```

3. **Web GUI Integration**
   - iframe embedding noVNC
   - "Ready to Capture" button → API call → screenshot
   - Session timeout handling

**Estimated Effort:** 2-3 days

### Phase 2: Cloud Service Integration (Optional)

**Target:** Offload bot-protected sites to managed service.

**When to use:**
- Site has aggressive bot detection (Kasada, DataDome)
- Need residential proxy rotation
- Scaling beyond 10 concurrent sessions

**Integration:**
```python
async def capture_with_fallback(url: str) -> CaptureResult:
    # Try local Patchright first
    result = await local_capture(url)

    if result.blocked:
        # Fall back to Browserbase
        result = await browserbase_capture(url, interactive=True)

    return result
```

**Estimated Effort:** 1-2 days (API integration)

---

## Security Considerations

### VNC/noVNC Security

1. **Authentication:** Use token-based auth for noVNC connections
   ```python
   # Generate one-time token per session
   token = jwt.encode({
       "session_id": session_id,
       "exp": datetime.utcnow() + timedelta(minutes=30)
   }, SECRET_KEY)

   # noVNC URL with token
   vnc_url = f"http://server:6080/vnc.html?token={token}"
   ```

2. **Network Isolation:** Don't expose VNC ports directly
   ```yaml
   # docker-compose.yml
   services:
     novnc:
       ports:
         - "127.0.0.1:6080:6080"  # Only localhost
   ```

3. **HTTPS:** Use reverse proxy for TLS
   ```nginx
   server {
       listen 443 ssl;
       server_name capture.example.com;

       location /vnc/ {
           proxy_pass http://localhost:6080/;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection "upgrade";
       }
   }
   ```

### CDP Security

1. **Never expose CDP port to internet**
2. **Use authenticated WebSocket proxy**
3. **Session isolation per user**

### Cloud Service Security

1. **API key management** (environment variables, not code)
2. **Session timeout enforcement**
3. **Audit logging**

---

## Implementation Roadmap

### Week 1: Core Infrastructure
- [ ] Set up Xvfb as systemd service
- [ ] Install and configure x11vnc + websockify + noVNC
- [ ] Test single-session capture flow

### Week 2: Session Management
- [ ] Implement BrowserSessionPool
- [ ] Implement DisplayAllocator
- [ ] Add session lifecycle API endpoints

### Week 3: Web GUI Integration
- [ ] Create React component for noVNC iframe
- [ ] Add "Ready to Capture" flow
- [ ] Handle session timeouts gracefully

### Week 4: Polish & Testing
- [ ] Load testing (concurrent sessions)
- [ ] Security review
- [ ] Documentation

---

## Conclusion

For the UX Maturity Analysis platform's web GUI, we recommend:

1. **Primary Approach:** VNC + noVNC (Approach 1)
   - Mature, well-documented
   - Full visibility and control
   - Integrates with existing Xvfb setup from bot detection research

2. **Fallback Option:** Browserbase (Approach 3)
   - For heavily protected sites
   - When scaling beyond self-hosted capacity

3. **Future Enhancement:** Custom WebSocket stream (Approach 5)
   - If latency becomes a user complaint
   - If we need more control over the UX

The hybrid architecture—automated capture first, human-in-the-loop fallback—aligns with both the existing bot detection research and the PROJECT_STATE.md proposal for `--headless` mode.

---

## References

### Tools & Libraries
- [Patchright](https://github.com/Kaliiiiiiiiii-Vinyzu/patchright-python) — Stealth Playwright
- [Camoufox](https://github.com/daijro/camoufox) — Stealth Firefox
- [noVNC](https://novnc.com/) — HTML5 VNC client
- [Browserbase](https://www.browserbase.com/) — Cloud browser service
- [E2B Desktop](https://e2b.dev/) — Cloud sandbox with desktop
- [Selenium Grid](https://www.selenium.dev/documentation/grid/) — Enterprise browser grid

### Research Sources
- Bot detection landscape research (internal: `bot-detection-ecom-screenshots-2026.md`)
- Browserbase Live View documentation
- Chrome DevTools Protocol specification
- Apache Guacamole architecture documentation
- noVNC WebSocket implementation

---

*Research compiled March 2026. This is a rapidly evolving space — cloud browser services in particular are seeing significant investment and feature development.*
