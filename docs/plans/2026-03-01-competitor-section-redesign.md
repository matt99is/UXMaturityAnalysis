# Competitor Section Redesign

**Date:** 2026-03-01
**Status:** Approved

## Problem

Two areas inside the expandable competitor cards are underperforming:

1. **Evidence Highlights** — text is hard-truncated at 140 characters in Python, causing mid-sentence cuts. Items lack criterion attribution, so the reader can't tell *what* the evidence relates to. This erodes trust in the analysis.

2. **Criteria Scores** — a flat bulleted list of 11 criterion names + numbers. No visual hierarchy. No ability to quickly identify strengths vs vulnerabilities.

## Design

### Section 1: Evidence Highlights

Replace the plain icon + truncated text list with attributed evidence cards.

**Structure per item:**
- Left border (3px): red = vulnerability, green = strength
- Criterion name — small uppercase label top-left
- Competitive status badge — top-right: VULNERABILITY (red tint) / STRENGTH (green tint)
- Full evidence text — untruncated, muted colour, 1.5 line-height

**Items shown:** 3 total
- Worst vulnerability (lowest score with `competitive_status: vulnerability`)
- Best strength (highest score with `competitive_status: strength`)
- Second worst vulnerability

**Python changes (`_build_competitor_evidence_items`):**
- Remove `[:140]` truncation
- Add `criterion_name` and `competitive_status` to each item dict
- Update item selection logic to: worst vulnerability + best strength + second worst vulnerability

### Section 2: Criteria Scores → Notable Split

Replace the flat list with a two-column layout showing only the most notable criteria.

**Layout:**
- `display: grid; grid-template-columns: 1fr 1fr`
- Left column: STRENGTHS header (green label) + top 3 by score, sorted descending
- Right column: VULNERABILITIES header (red label) + top 3 by score, sorted ascending (worst first)
- Each row: criterion name (truncated to 2 lines max via CSS) + score badge right-aligned
- Strength score badges: green; Vulnerability score badges: red

**Python changes (`_prepare_competitor_data`):**
- Add `top_strengths`: top 3 criteria with `competitive_status: strength`, sorted highest first
- Add `top_vulnerabilities`: top 3 criteria with `competitive_status: vulnerability`, sorted lowest first
- These replace `criteria_scores` in the template render context for this section

## Files

| File | Change |
|------|--------|
| `src/utils/html_report_generator.py` | `_build_competitor_evidence_items()` + `_prepare_competitor_data()` |
| `templates/report.html.jinja2` | Competitor body: evidence card markup + criteria split markup |
| `css/_components.scss` | New evidence card styles + criteria split styles |

## Constraints

- No truncation of evidence text in Python (CSS `line-clamp` is acceptable if needed for extreme cases, but preference is full display)
- No decorative elements — colour is used only to communicate strength/vulnerability status
- No icons added beyond existing icon system
- Must work in both light and dark theme (use CSS custom properties throughout)
- Rebuild sequence: `python3 scripts/build_css.py` then `python3 scripts/regenerate_example_report.py`
