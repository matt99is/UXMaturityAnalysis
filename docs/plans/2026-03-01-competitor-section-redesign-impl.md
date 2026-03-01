# Competitor Section Redesign Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the truncated evidence highlights and flat criteria list inside competitor cards with attributed evidence cards and a two-column strengths/vulnerabilities split.

**Architecture:** Three-layer change: (1) Python data preparation adds new fields and removes truncation, (2) Jinja2 template uses new fields to render new markup, (3) SCSS adds new component styles. No new files needed — all changes are additive within existing files.

**Tech Stack:** Python 3.12, Jinja2, SCSS (compiled via `python3 scripts/build_css.py`), pytest

---

### Task 1: Add `_get_top_criteria` helper and wire up `top_strengths` / `top_vulnerabilities`

**Files:**
- Modify: `src/utils/html_report_generator.py:561-571` (the `prepared_competitors.append` block)
- Modify: `src/utils/html_report_generator.py` (add new method after line 639)
- Test: `tests/test_html_report_generator.py`

**Step 1: Write the failing tests**

Add to `tests/test_html_report_generator.py`:

```python
def _make_result(criteria_scores, overall_score=5.0):
    """Minimal result dict for testing."""
    return {
        "success": True,
        "site_name": "Test Site",
        "overall_score": overall_score,
        "criteria_scores": criteria_scores,
        "screenshot_metadata": [],
        "notable_states": [],
    }


def test_get_top_criteria_returns_vulnerabilities_sorted_ascending():
    generator = HTMLReportGenerator(output_dir="/tmp/test_out")
    result = _make_result([
        {"criterion_name": "A", "score": 1, "competitive_status": "vulnerability"},
        {"criterion_name": "B", "score": 3, "competitive_status": "vulnerability"},
        {"criterion_name": "C", "score": 2, "competitive_status": "vulnerability"},
        {"criterion_name": "D", "score": 8, "competitive_status": "strength"},
    ])
    top = generator._get_top_criteria(result, "vulnerability", top=3, ascending=True)
    assert [c["criterion_name"] for c in top] == ["A", "C", "B"]


def test_get_top_criteria_returns_strengths_sorted_descending():
    generator = HTMLReportGenerator(output_dir="/tmp/test_out")
    result = _make_result([
        {"criterion_name": "A", "score": 7, "competitive_status": "strength"},
        {"criterion_name": "B", "score": 9, "competitive_status": "strength"},
        {"criterion_name": "C", "score": 8, "competitive_status": "strength"},
    ])
    top = generator._get_top_criteria(result, "strength", top=3, ascending=False)
    assert [c["criterion_name"] for c in top] == ["B", "C", "A"]


def test_get_top_criteria_respects_top_limit():
    generator = HTMLReportGenerator(output_dir="/tmp/test_out")
    result = _make_result([
        {"criterion_name": str(i), "score": i, "competitive_status": "vulnerability"}
        for i in range(6)
    ])
    top = generator._get_top_criteria(result, "vulnerability", top=3, ascending=True)
    assert len(top) == 3


def test_get_top_criteria_falls_back_to_score_threshold_for_strength():
    generator = HTMLReportGenerator(output_dir="/tmp/test_out")
    result = _make_result([
        {"criterion_name": "High", "score": 8},
        {"criterion_name": "Mid", "score": 5},
        {"criterion_name": "Low", "score": 2},
    ])
    top = generator._get_top_criteria(result, "strength", top=3, ascending=False)
    assert top[0]["criterion_name"] == "High"


def test_prepare_competitor_data_includes_top_strengths_and_vulnerabilities(tmp_path):
    generator = HTMLReportGenerator(output_dir=str(tmp_path / "output"))
    output_path = tmp_path / "output" / "report.html"
    result = _make_result([
        {"criterion_name": "Strong A", "score": 9, "competitive_status": "strength"},
        {"criterion_name": "Weak A",   "score": 1, "competitive_status": "vulnerability"},
        {"criterion_name": "Weak B",   "score": 2, "competitive_status": "vulnerability"},
    ])
    competitors, _ = generator._prepare_competitor_data([result], output_path)
    comp = competitors[0]
    assert "top_strengths" in comp
    assert "top_vulnerabilities" in comp
    assert comp["top_strengths"][0]["criterion_name"] == "Strong A"
    assert comp["top_vulnerabilities"][0]["criterion_name"] == "Weak A"
```

**Step 2: Run tests to verify they fail**

```bash
python3 -m pytest tests/test_html_report_generator.py -v
```

Expected: 5 new tests FAIL with `AttributeError: 'HTMLReportGenerator' object has no attribute '_get_top_criteria'`

**Step 3: Add `_get_top_criteria` method**

In `src/utils/html_report_generator.py`, add the following method directly after `_build_competitor_evidence_items` (after line 639):

```python
def _get_top_criteria(
    self, result: Dict[str, Any], status: str, top: int, ascending: bool
) -> List[Dict[str, Any]]:
    """Return top N criteria filtered by competitive_status, sorted by score."""
    criteria_scores = result.get("criteria_scores", []) or []
    filtered = [c for c in criteria_scores if c.get("competitive_status") == status]

    # Fallback: use score thresholds when competitive_status is not populated
    if not filtered:
        if status == "strength":
            filtered = [c for c in criteria_scores if c.get("score", 0) >= 7]
        elif status == "vulnerability":
            filtered = [c for c in criteria_scores if c.get("score", 0) < 5]

    return sorted(filtered, key=lambda c: c.get("score", 0), reverse=not ascending)[:top]
```

**Step 4: Wire into `_prepare_competitor_data`**

In the `prepared_competitors.append({...})` block (around line 561), add two new keys:

```python
prepared_competitors.append(
    {
        "id": comp_id,
        "name": result.get("site_name"),
        "overall_score": result.get("overall_score", 0),
        "criteria_scores": result.get("criteria_scores", []),
        "screenshots": screenshots,
        "notable_states": result.get("notable_states", []),
        "evidence_items": self._build_competitor_evidence_items(result),
        "top_strengths": self._get_top_criteria(result, "strength", top=3, ascending=False),
        "top_vulnerabilities": self._get_top_criteria(result, "vulnerability", top=3, ascending=True),
    }
)
```

**Step 5: Run tests**

```bash
python3 -m pytest tests/test_html_report_generator.py -v
```

Expected: All 6 tests PASS

**Step 6: Commit**

```bash
git add src/utils/html_report_generator.py tests/test_html_report_generator.py
git commit -m "feat: add _get_top_criteria helper and top_strengths/top_vulnerabilities to competitor data"
```

---

### Task 2: Rewrite `_build_competitor_evidence_items` to remove truncation and add attribution

**Files:**
- Modify: `src/utils/html_report_generator.py:575-639`
- Test: `tests/test_html_report_generator.py`

**Step 1: Write the failing tests**

Add to `tests/test_html_report_generator.py`:

```python
def test_build_evidence_items_does_not_truncate_text():
    generator = HTMLReportGenerator(output_dir="/tmp/test_out")
    long_evidence = "x" * 500
    result = _make_result([
        {"criterion_name": "Weak", "score": 1, "competitive_status": "vulnerability",
         "evidence": long_evidence, "observations": ""},
    ])
    items = generator._build_competitor_evidence_items(result)
    assert any(item["text"] == long_evidence for item in items)


def test_build_evidence_items_includes_criterion_name():
    generator = HTMLReportGenerator(output_dir="/tmp/test_out")
    result = _make_result([
        {"criterion_name": "Shipping Cost", "score": 1, "competitive_status": "vulnerability",
         "evidence": "No free delivery threshold shown.", "observations": ""},
    ])
    items = generator._build_competitor_evidence_items(result)
    assert any(item["criterion_name"] == "Shipping Cost" for item in items)


def test_build_evidence_items_includes_competitive_status():
    generator = HTMLReportGenerator(output_dir="/tmp/test_out")
    result = _make_result([
        {"criterion_name": "Checkout CTA", "score": 8, "competitive_status": "strength",
         "evidence": "Clear CTA with strong contrast.", "observations": ""},
    ])
    items = generator._build_competitor_evidence_items(result)
    assert any(item["competitive_status"] == "strength" for item in items)


def test_build_evidence_items_selects_worst_vuln_best_strength_second_vuln():
    generator = HTMLReportGenerator(output_dir="/tmp/test_out")
    result = _make_result([
        {"criterion_name": "Vuln1", "score": 1, "competitive_status": "vulnerability",
         "evidence": "v1 evidence", "observations": ""},
        {"criterion_name": "Vuln2", "score": 2, "competitive_status": "vulnerability",
         "evidence": "v2 evidence", "observations": ""},
        {"criterion_name": "Strength1", "score": 9, "competitive_status": "strength",
         "evidence": "s1 evidence", "observations": ""},
    ])
    items = generator._build_competitor_evidence_items(result)
    names = [i["criterion_name"] for i in items]
    assert names[0] == "Vuln1"
    assert names[1] == "Strength1"
    assert names[2] == "Vuln2"
```

**Step 2: Run tests to verify they fail**

```bash
python3 -m pytest tests/test_html_report_generator.py -v -k "evidence"
```

Expected: 4 new tests FAIL

**Step 3: Replace `_build_competitor_evidence_items`**

Replace the entire method body (lines 575–639) with:

```python
def _build_competitor_evidence_items(self, result: Dict[str, Any]) -> List[Dict[str, str]]:
    """Build attributed evidence items for each competitor card."""
    criteria_scores = result.get("criteria_scores", []) or []

    vulnerabilities = sorted(
        [c for c in criteria_scores if c.get("competitive_status") == "vulnerability"],
        key=lambda c: c.get("score", 0),
    )
    strengths = sorted(
        [c for c in criteria_scores if c.get("competitive_status") == "strength"],
        key=lambda c: c.get("score", 0),
        reverse=True,
    )

    # Score-threshold fallbacks when competitive_status is absent
    if not vulnerabilities:
        vulnerabilities = sorted(
            [c for c in criteria_scores if c.get("score", 0) < 5],
            key=lambda c: c.get("score", 0),
        )
    if not strengths:
        strengths = sorted(
            [c for c in criteria_scores if c.get("score", 0) >= 7],
            key=lambda c: c.get("score", 0),
            reverse=True,
        )

    candidates = []
    if vulnerabilities:
        candidates.append((vulnerabilities[0], "vulnerability"))
    if strengths:
        candidates.append((strengths[0], "strength"))
    if len(vulnerabilities) >= 2:
        candidates.append((vulnerabilities[1], "vulnerability"))

    items = []
    for criterion, status in candidates:
        text = (criterion.get("evidence") or criterion.get("observations") or "").strip()
        if not text:
            continue
        items.append({
            "criterion_name": criterion.get("criterion_name", ""),
            "competitive_status": status,
            "text": text,
        })

    return items
```

**Step 4: Run tests**

```bash
python3 -m pytest tests/test_html_report_generator.py -v
```

Expected: All tests PASS

**Step 5: Commit**

```bash
git add src/utils/html_report_generator.py tests/test_html_report_generator.py
git commit -m "feat: rewrite evidence items — remove truncation, add criterion attribution"
```

---

### Task 3: Add new CSS component styles

**Files:**
- Modify: `css/_components.scss` (append to end of file)

**Step 1: Append new styles to `css/_components.scss`**

Add at the end of the file:

```scss
// ===== Evidence Highlight Cards =====
.evidence-highlights-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: $spacing-sm;
}

.evidence-highlight-item {
  padding: $spacing-md $spacing-lg;
  border-left: 3px solid var(--border);
  background: var(--bg);
  border-radius: 0 $border-radius-sm $border-radius-sm 0;

  &--vulnerability {
    border-left-color: var(--red);
  }

  &--strength {
    border-left-color: var(--green);
  }
}

.evidence-highlight-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: $spacing-sm;
  margin-bottom: $spacing-xs;
}

.evidence-highlight-criterion {
  font-size: $font-size-xs;
  font-weight: $font-weight-semibold;
  text-transform: uppercase;
  letter-spacing: $letter-spacing-wide;
  color: var(--text-dim);
}

.evidence-highlight-badge {
  font-size: $font-size-xs;
  font-weight: $font-weight-semibold;
  text-transform: uppercase;
  letter-spacing: $letter-spacing-normal;
  padding: 2px $spacing-sm;
  border-radius: $border-radius-sm;
  white-space: nowrap;
  flex-shrink: 0;

  &--vulnerability {
    background: var(--red-dim);
    color: var(--red);
  }

  &--strength {
    background: var(--green-dim);
    color: var(--green);
  }
}

.evidence-highlight-text {
  font-size: $font-size-sm;
  color: var(--text-muted);
  line-height: 1.6;
  margin: 0;
}

// ===== Criteria Split (Strengths / Vulnerabilities) =====
.criteria-split {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: $spacing-lg;
  margin-bottom: $spacing-lg;
}

.criteria-col-header {
  font-size: $font-size-xs;
  font-weight: $font-weight-semibold;
  text-transform: uppercase;
  letter-spacing: $letter-spacing-wide;
  margin-bottom: $spacing-sm;
  padding-bottom: $spacing-sm;
  border-bottom: 1px solid var(--border);

  .criteria-col--strengths & {
    color: var(--green);
  }

  .criteria-col--vulnerabilities & {
    color: var(--red);
  }
}

.criteria-col-item {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: $spacing-sm;
  padding: $spacing-xs 0;
  border-bottom: 1px solid var(--border);

  &:last-child {
    border-bottom: none;
  }
}

.criteria-col-name {
  font-size: $font-size-sm;
  color: var(--text-muted);
  line-height: 1.4;
}

.criteria-col-score {
  font-size: $font-size-sm;
  font-weight: $font-weight-semibold;
  white-space: nowrap;
  flex-shrink: 0;

  &--strength {
    color: var(--green);
  }

  &--vulnerability {
    color: var(--red);
  }
}
```

**Step 2: Build CSS**

```bash
python3 scripts/build_css.py
```

Expected: `output/css/main.css` updated with no errors

**Step 3: Commit**

```bash
git add css/_components.scss output/css/main.css
git commit -m "feat: add evidence highlight card and criteria split CSS components"
```

---

### Task 4: Update the Jinja2 template

**Files:**
- Modify: `templates/report.html.jinja2:158-179`

**Step 1: Replace the evidence section markup**

Find this block (lines 158–170):

```html
{% if comp.evidence_items %}
<div class="evidence-card-inline">
  <div class="evidence-card-inline-title">Evidence Highlights</div>
  <ul class="evidence-card-inline-list">
    {% for evidence_item in comp.evidence_items %}
    <li class="evidence-card-inline-item">
      <i data-lucide="{{ evidence_item.icon }}" class="evidence-icon {{ evidence_item.icon_class }}"></i>
      <span class="evidence-text">{{ evidence_item.text }}</span>
    </li>
    {% endfor %}
  </ul>
</div>
{% endif %}
```

Replace with:

```html
{% if comp.evidence_items %}
<div class="evidence-card-inline">
  <div class="evidence-card-inline-title">Evidence Highlights</div>
  <ul class="evidence-highlights-list">
    {% for item in comp.evidence_items %}
    <li class="evidence-highlight-item evidence-highlight-item--{{ item.competitive_status }}">
      <div class="evidence-highlight-header">
        <span class="evidence-highlight-criterion">{{ item.criterion_name }}</span>
        <span class="evidence-highlight-badge evidence-highlight-badge--{{ item.competitive_status }}">{{ item.competitive_status | title }}</span>
      </div>
      <p class="evidence-highlight-text">{{ item.text }}</p>
    </li>
    {% endfor %}
  </ul>
</div>
{% endif %}
```

**Step 2: Replace the criteria section markup**

Find this block (lines 172–179):

```html
<div class="criteria">
  {% for criterion in comp.criteria_scores %}
  <div class="criterion">
    <span class="criterion-name">{{ criterion.criterion_name }}</span>
    <span class="criterion-score {% if criterion.score >= 7 %}high{% elif criterion.score >= 5 %}med{% endif %}">{{ criterion.score|round(1) }}</span>
  </div>
  {% endfor %}
</div>
```

Replace with:

```html
{% if comp.top_strengths or comp.top_vulnerabilities %}
<div class="criteria-split">
  <div class="criteria-col criteria-col--strengths">
    <div class="criteria-col-header">Strengths</div>
    {% for criterion in comp.top_strengths %}
    <div class="criteria-col-item">
      <span class="criteria-col-name">{{ criterion.criterion_name }}</span>
      <span class="criteria-col-score criteria-col-score--strength">{{ criterion.score|round(1) }}</span>
    </div>
    {% endfor %}
  </div>
  <div class="criteria-col criteria-col--vulnerabilities">
    <div class="criteria-col-header">Vulnerabilities</div>
    {% for criterion in comp.top_vulnerabilities %}
    <div class="criteria-col-item">
      <span class="criteria-col-name">{{ criterion.criterion_name }}</span>
      <span class="criteria-col-score criteria-col-score--vulnerability">{{ criterion.score|round(1) }}</span>
    </div>
    {% endfor %}
  </div>
</div>
{% endif %}
```

**Step 3: Commit**

```bash
git add templates/report.html.jinja2
git commit -m "feat: update competitor card template — evidence attribution cards and criteria split"
```

---

### Task 5: Regenerate report and verify

**Step 1: Regenerate the example report**

```bash
python3 scripts/regenerate_example_report.py
```

Expected: Script completes without errors

**Step 2: Verify in browser**

Open http://localhost:9000/basket-pages/2026-02-28.html

- Expand any competitor card
- Evidence Highlights should show 3 items: each with a criterion name label, a VULNERABILITY or STRENGTH badge, and full untruncated evidence text
- Below that, a two-column grid: STRENGTHS on left (green scores), VULNERABILITIES on right (red scores), max 3 rows each

**Step 3: Run full test suite**

```bash
python3 -m pytest tests/ -v
```

Expected: All tests pass

**Step 4: Final commit**

```bash
git add output/basket-pages/2026-02-28.html
git commit -m "feat: regenerate report with competitor section redesign"
```
