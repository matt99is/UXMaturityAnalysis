# Criteria Authoring Guide

How to write and maintain `criteria_config/*.yaml` files. Follow this guide
for all new page types and when updating existing criteria.

---

## Overview of the two-pass pipeline

Each competitor analysis makes two API calls:

**Pass 1 (Observe):** Screenshots -> structured observation JSON.
The model acts as a witness - no scoring, no evaluation. Output includes
`observation_focus` items plus universal sections (pricing, dark patterns, etc.).
Saved as `observation.json` per competitor.

**Pass 2 (Score):** Observation JSON -> scored analysis.
No screenshots. Scores each criterion against the documented evidence.
Requires citation for documented evidence; permits professional judgement
for gaps (noted explicitly in the `evidence` field).

The two passes must speak the same language. **observation_focus items must
map to criteria evaluation_points.** This is the single most important rule.

---

## observation_focus

### What it does

Items are injected into the Pass 1 prompt under a PAGE-SPECIFIC OBSERVATIONS
section. Pass 1 pays special attention to these items alongside its universal
sections (pricing, interactive states, CTAs, trust signals, forms, dark patterns).

### Authoring rules

**One item per criterion minimum.** Every criterion that has evidence needs
that can't be covered by the universal sections must have at least one
observation_focus entry.

**Name what to look for, not just where.** Bad: `"Checkout buttons"`.
Good: `"Express checkout buttons (PayPal, Google Pay, Apple Pay) - exact
position relative to main checkout CTA (above or below?), present on
desktop and mobile separately"`.

**Specify the key distinctions.** If a criterion cares about desktop vs
mobile separately, say so. If positioning matters (above vs below CTA),
say so. These distinctions are what Pass 2's rubric scores on.

**Keep each item to one sentence or two short clauses.** The observation
prompt already has universal sections. observation_focus items are
supplemental, not exhaustive.

### Token budget

Each observation_focus item adds ~25-40 tokens to the Pass 1 prompt.
With Pass 1 at 16000 output tokens, throughput is not a concern.
Keep items concise for readability, not for token reasons.

---

## scoring_rubric

### What it does

Rendered in the Pass 2 prompt directly after each criterion's evaluation_points
and benchmarks. Anchors the 0-10 scale so the same evidence produces the
same score across competitors and runs.

### Required format

Four bands, one sentence each:

```yaml
scoring_rubric:
  "8-10": "<what earns a high score - the positive case>"
  "5-7": "<adequate implementation - present but incomplete>"
  "2-4": "<present but poorly executed or only partially visible>"
  "0-1": "<absent or completely non-functional>"
```

**Quote keys as strings** (`"8-10"` not `8-10`). PyYAML parses unquoted
ranges inconsistently.

### Authoring rules

**One sentence per band.** Rubrics must stay concise - they add ~60 tokens
per criterion to Pass 2's input. Ten-word sentences, not paragraphs.

**The 8-10 band describes the ideal, not perfection.** A site doesn't need
every evaluation_point fulfilled to score 8. Describe what a strong
real-world implementation looks like.

**The 0-1 band describes absence, not failure.** "No X documented in
observation" - not "catastrophic failure". Missing = 0-1, poor = 2-4.

**Each band must be self-contained.** Pass 2 reads rubric bands independently;
don't write "same as above but without Y".

**Reference the observation_focus item's key distinctions.** If your
observation_focus asks about "above or below the main CTA", the 8-10 rubric
should say "positioned above the main checkout CTA". Consistency between the
two is what eliminates the telephone-game effect.

---

## Complete criterion template

```yaml
- id: "criterion_id"               # snake_case, unique within the file
  name: "Human Readable Name"
  weight: 8                         # 1-10; see tier guidance below
  description: "One sentence - what this criterion measures."
  evaluation_points:
    - "Question 1 about what to look for?"
    - "Question 2 - be specific about states (above/below, selected/unselected)"
    - "Question 3"
  benchmarks:
    - source: "Baymard Institute"
      finding: "Evidence sentence from research"
    - source: "Best Practice"
      finding: "Industry norm"
  scoring_rubric:
    "8-10": "Strong positive case - references key distinctions from observation_focus"
    "5-7": "Present but incomplete or partially visible"
    "2-4": "Present but poorly positioned, implemented, or only on one viewport"
    "0-1": "Not documented in observation"
```

---

## Weight tiers

| Tier | Weight | Use for |
|------|--------|---------|
| Critical | 9-10 | Directly drives abandonment (shipping cost, basket clarity) |
| Important | 7-8 | Strong conversion influence (express checkout, CTAs) |
| Supporting | 5-6 | Trust and experience quality (trust signals, cross-sell) |
| Enhancement | 1-4 | Nice-to-have differentiation |

---

## Checklist for new page types

Before shipping a new `criteria_config/*.yaml`:

- [ ] Every criterion has a `scoring_rubric` with all four bands (`8-10`, `5-7`, `2-4`, `0-1`)
- [ ] Every criterion that needs specific visual evidence has at least one `observation_focus` entry
- [ ] Each observation_focus item names the key distinctions Pass 2 will score on
- [ ] Rubric 8-10 bands reference the key distinctions from their observation_focus item
- [ ] No rubric band exceeds two sentences
- [ ] YAML loads cleanly: `python3 src/config_loader.py` (no errors)
- [ ] Existing tests still pass: `pytest tests/ -v`

---

## Updating existing page types

When adding rubrics to non-basket page types, use this process:

1. Read the existing criteria carefully
2. For each criterion, draft the observation_focus item first (what evidence does Pass 2 need?)
3. Then write the rubric bands referencing that evidence
4. Run `pytest tests/ -v` - no regression
5. One commit per page type

The basket_pages.yaml in this repo is the reference implementation.
