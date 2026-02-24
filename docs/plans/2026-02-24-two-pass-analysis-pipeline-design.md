# Two-Pass Analysis Pipeline Design

**Date:** 2026-02-24
**Status:** Approved
**Priority:** Accuracy over speed

---

## Problem

The current single-call analysis pipeline sends both desktop and mobile screenshots plus all 10+ criteria in one API call. With `max_tokens=6000`, each criterion receives ~600 output tokens — not enough for the model to notice nuanced UI states such as subscription options pre-selected by default. This forces manual verification of every screenshot against the analysis, reducing trust in the output.

Root causes:
- Attention dilution: model is scoring 10+ criteria simultaneously
- Output budget dilution: ~600 tokens per criterion leaves no room for nuance
- No audit trail: there is no record of what the model *observed* before it scored

---

## Solution: Two-Pass Pipeline

Each competitor analysis becomes two sequential API calls.

```
[Screenshots] → Pass 1: Observe → [observation.json]
                                         ↓
               [criteria.yaml] → Pass 2: Score → [analysis.json]
```

**Pass 1 (Observe):** Send screenshots with a prompt focused purely on visual documentation. No scoring. No criteria. The model acts as a witness, describing all visible UI states, interactive elements, pricing, dark patterns, and anomalies. Output is a structured JSON observation saved to disk.

**Pass 2 (Score):** Send the observation JSON as text — no images. Score all criteria against the documented evidence. Each score must cite the specific observation that supports it. The full output token budget goes to scoring since there are no image tokens.

---

## Pass 1 — Observation Prompt Design

The prompt has two layers:

### Universal core (all page types)

Always included:

- Pricing & offers (all prices, subscription/recurring options, which option is selected by default, shipping thresholds)
- Interactive states (pre-selected radio buttons, checkboxes, toggles, dropdowns, default form values)
- Calls to action (primary CTA text, colour, placement, secondary CTAs)
- Trust signals (reviews, ratings, guarantees, badges, security indicators)
- Forms & inputs (all visible fields, pre-filled values)
- Navigation & structure (header, breadcrumbs, sticky elements)
- Dark patterns (pre-selected subscriptions, pre-checked opt-in boxes, hidden opt-outs, urgency/scarcity messaging)

Output includes a `notable_states` array — a flat list of anything unusual or potentially deceptive observed in either viewport. This is a forcing function: every entry must be addressed in pass 2.

### Page-specific sections (from YAML)

Each `criteria_config/*.yaml` gets a new `observation_focus` block. The observation prompt builder merges the universal core with these page-specific entries. Example:

```yaml
# product_pages.yaml
observation_focus:
  - "Product variants (size, colour, quantity) and which are selected by default"
  - "Subscription vs one-time purchase toggle — which is pre-selected"
  - "Image gallery state and visible product imagery"
  - "Stock availability messaging"

# basket_pages.yaml
observation_focus:
  - "Cart contents — items, quantities, prices"
  - "Order summary breakdown (subtotal, shipping, discounts)"
  - "Upsell or cross-sell placements"
  - "Coupon or promo code input visibility"

# checkout_pages.yaml
observation_focus:
  - "Form fields visible and their pre-filled state"
  - "Payment method options and which is selected"
  - "Order summary visibility at each step"
  - "Progress indicator and current step"

# homepage_pages.yaml
observation_focus:
  - "Hero messaging and primary value proposition"
  - "Promotional banners or offers visible"
  - "Navigation structure and featured categories"
  - "Any personalisation or location-based content"
```

New page types define their own `observation_focus` in YAML. No code changes required.

---

## Pass 2 — Scoring Prompt Design

Pass 2 receives the observation JSON and scores against criteria. Key changes from the current prompt:

**Mandatory evidence citation:** Every score must quote the specific observation that supports it. The model cannot score vaguely — it must reference what was documented.

**notable_states forcing function:** The prompt instructs the model to review `notable_states` before scoring and ensure every item is addressed in a relevant criterion score. If no criterion covers it, it must be escalated to `key_findings`.

**Prompt structure:**
```
You are a competitive intelligence analyst scoring a {page_type} for UX maturity.

Use ONLY the observations below as your evidence. Do not infer what is not documented.
If the observation notes something was unclear, reflect that uncertainty in your score.

[OBSERVATION JSON]

[ANALYSIS CONTEXT / MARKET EXPERTISE — unchanged from today]

Score each criterion. For each you MUST:
1. Quote the specific observation(s) that support your score
2. Give a score 0-10
3. Flag if the observation was ambiguous or unclear

IMPORTANT: Review notable_states before scoring. Every item must be addressed
in a criterion score or escalated to key_findings.

[CRITERIA LIST — unchanged from today]
```

---

## Data Model

### New file: `observation.json`

Saved to `{audit_dir}/{competitor}/` alongside `analysis.json`:

```
{competitor}/
├── screenshots/
│   ├── desktop.png
│   └── mobile.png
├── observation.json    ← new
└── analysis.json       ← unchanged structure, one new field
```

`observation.json` stores the full pass 1 output including `notable_states`. Stored separately so:
- `reanalyze_screenshots.py` can skip pass 1 and go straight to scoring
- Observations can be inspected independently
- Criteria changes do not require re-observing

### Change to `analysis.json`

Two additions only:

```json
{
  "observation_file": "observation.json",
  "criteria_scores": [
    {
      "...existing fields...",
      "evidence": "quoted observation text supporting this score"
    }
  ]
}
```

All other fields unchanged. Downstream tooling (HTML report, markdown report, comparison) unaffected.

### `reanalyze_screenshots.py` skip logic

| State | Behaviour |
|-------|-----------|
| Neither file exists | Run both passes |
| `observation.json` exists, no `analysis.json` | Skip pass 1, run pass 2 only |
| Both files exist | Skip both (existing behaviour) |
| `--force-observe` flag | Re-run pass 1, then pass 2 |
| `--force` flag | Re-run both passes |

---

## Report Changes

### HTML report — Evidence tab

Each competitor profile gets a new "Evidence" tab alongside criteria scores. Displays the `observation.json` content in readable sections (not raw JSON). Replaces the need to open screenshots to verify scoring.

### notable_states callout

The `notable_states` array is rendered as a highlighted callout at the top of each competitor profile — before criteria scores. Flagged anomalies are immediately visible.

### notable_states in markdown report

A short "Flagged anomalies" section added per competitor. Useful for stakeholders who receive the markdown report rather than the HTML dashboard.

### No changes to

- Rankings, radar charts, heatmap
- Strategic insights
- Existing JSON structure
- Screenshot capture pipeline

---

## What This Solves

| Problem | Solution |
|---------|----------|
| Pre-selected subscriptions missed | Pass 1 explicitly documents interactive states and default selections before any scoring |
| Low trust in analysis | Observation is a human-readable audit trail; scores cite specific evidence |
| Manual screenshot verification | Read the observation instead — plain language, faster to scan |
| Output tokens spread thin | Pass 2 has zero image tokens; full budget goes to scoring |
| No record of what model saw | `observation.json` stored on disk, reusable across scoring runs |
