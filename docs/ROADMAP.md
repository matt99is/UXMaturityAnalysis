# Roadmap

**Last updated:** 2026-03-03
**Current version:** v1.13.0
**Live site:** https://analysis.mattlelonek.co.uk

---

## What this tool does today

Analyses competitor e-commerce pages and generates UX maturity reports. You point it at a set of URLs, it captures screenshots (desktop + mobile), runs a two-pass Claude analysis (observe → score), and publishes interactive HTML reports to Netlify.

Current workflow: `./run.sh` → choose Fresh analysis or Reanalyse → reports deploy to Netlify.

---

## Phase 1 — Scoring Reliability (in progress)

**Goal:** Make scores consistent and trustworthy across runs and across competitors.

**Problem:** Three gaps in the current two-pass pipeline produce inconsistent scores:
- Pass 1 truncates at 8,000 tokens — drops entire competitors from reports
- Pass 1 organises by UI section; Pass 2 scores by criterion — evidence gets lost in translation
- No scoring anchors — the model invents its own 0–10 scale per run

**Solution:** Raise token limits, add per-criterion `scoring_rubric` fields to YAML configs, align `observation_focus` items to criteria evaluation points.

**Plan:** `docs/plans/2026-03-02-scoring-reliability-overhaul.md`

**Status:** Implementation in progress (uncommitted changes on main).

---

## Phase 2 — Automated Capture (unattended)

**Goal:** Run the full capture pipeline unattended on the server — no SSH, no manual intervention — for sites that don't heavily block bots.

**Why vanilla Playwright fails:** VPS IPs are flagged before JS runs; headless Chrome returns a known fingerprint; CDP `Runtime.enable` is a known bot signal. `headless=True` is a non-starter for anything above basic Cloudflare.

**Solution:**
- **Patchright** — drop-in Playwright replacement that patches the CDP leak
- **Google Chrome** (not Chromium) — better fingerprint
- **Xvfb** — persistent virtual display so the browser runs headed on the server
- **ISP/residential proxy** — removes the datacenter IP flag
- **BrowserForge** — statistically realistic HTTP headers
- Persistent browser profiles (fresh profile = bot signal)

**New CLI flag:** `./run.sh` → "Automated" capture mode in the fresh analysis menu.

**Expected coverage:**
- Small/mid UK retailers: ✓ works easily
- Cloudflare standard (Tesco, Sainsbury's, Morrisons): ✓ with Patchright + residential IP
- Cloudflare Bot Management / DataDome: ~80–90%
- Kasada (JD Sports): occasional failures, needs retry logic

**Research:** `/home/matt99is/projects/Resources/ux-analysis/bot-detection-ecom-screenshots-2026.md`
**Design:** `docs/plans/2026-03-02-browser-capture-infrastructure-design.md`

---

## Phase 3 — Human-in-the-Loop Capture (VNC streaming)

**Goal:** For bot-protected sites, CAPTCHAs, and basket setup — let the user watch and interact with the browser via the web GUI, not the terminal.

**Problem:** Interactive mode currently requires you to be at the server terminal. A web GUI user on a remote device can't see or interact with a browser running on the server.

**Solution:** VNC streaming embedded in the web GUI:
- Xvfb virtual display on the server
- x11vnc exposes it over VNC
- websockify bridges VNC → WebSocket
- noVNC HTML5 client embedded as an iframe in the web GUI
- User clicks "Start capture", sees the browser live, solves CAPTCHAs, sets up page state, clicks "Ready"

**Flow:**
1. Analysis job starts → browser session opens on server
2. Web GUI shows noVNC iframe with a live view of the browser
3. User navigates to correct page state (adds items to basket, dismisses popups)
4. User clicks "Ready to capture" → server takes screenshots → analysis proceeds

**Research:** `docs/research/remote-human-in-the-loop-browser-capture-2026.md`
**Design:** `docs/plans/2026-03-02-browser-capture-infrastructure-design.md`

---

## Phase 4 — Web Management GUI

**Goal:** A full GUI experience at `analysis.mattlelonek.co.uk` — trigger and monitor analysis runs, manage competitor sets, and watch live capture — without ever touching the terminal.

**What the current site does:** Static HTML reports only (read-only).

**What this adds:**

| Feature | Description |
|---|---|
| Start new analysis | Select page type + competitor set, choose capture mode |
| Live progress | Watch analysis run step by step (capture → observe → score) |
| Browser view | Embedded noVNC iframe for human-in-the-loop capture (Phase 3) |
| Reanalyse | Pick existing audit folder, choose depth, trigger re-run |
| Competitor management | View/edit `competitors/*.yaml` via a form UI |
| Deploy | Trigger Netlify deploy from the GUI |

**Dependencies:** Requires Phase 2 (automated capture) and Phase 3 (VNC streaming) to be in place before the capture flow can work end-to-end.

**Stack options to evaluate:** FastAPI backend (clean Python fit, async), or a lightweight job queue (e.g. asyncio task manager with SSE for progress streaming). Frontend: minimal JS, fits the existing Jinja2 + SCSS stack.

---

## Phase 5 — Multi-Tenant SaaS (future)

**Goal:** Let multiple agencies or brands run their own analyses with their own competitor lists and custom criteria.

**Current state:** Single-tenant, file-based, password-protected Netlify site.

| Aspect | Now | Future |
|---|---|---|
| Tenants | One | Multiple (agencies, brands) |
| Competitor lists | Global YAML | Per-tenant |
| Criteria/benchmarks | Fixed | Per-tenant custom |
| Auth | Netlify password | Per-user accounts (Supabase) |
| URLs | `/basket-pages/` | `/{tenant}/basket-pages/` |

**Design:** `docs/ARCHITECTURE.md` (Future Architecture section)

---

## What's been built

| Version | Key additions |
|---|---|
| v1.14 (today) | Unified CLI — `cli.py` + simplified `run.sh`, `competitors/petfood.yaml`, YAML competitor config system |
| v1.13 | Competitor card redesign (evidence cards, strengths/vulnerabilities), radar chart, rankings, AI trope removal |
| v1.12 | GLM analyzer (OpenAI-compatible API support) |
| v1.11 | Index direct links, reanalyze fixed (all 16 competitors), output structure |
| v1.10 | Rich progress bar + live countdown, improved error handling, raised max_tokens |
| v1.9 | New output URL structure (`/{type}/{date}.html`), type index pages |
| v1.8 | Automatic Netlify deployment, `--no-deploy` flag |
| v1.7 | Template partials, auto-build CSS |
