# Scoring Reliability Overhaul Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix systematic scoring inconsistency in the two-pass analysis pipeline by raising token limits, adding per-criterion scoring rubrics, and aligning Pass 1 observations to Pass 2 evidence needs — then document the authoring standard so all future page types meet the same rigour.

**Architecture:** Four phases in dependency order: (1) token limit fixes — safe, isolated, ship first; (2) scoring reliability infrastructure — Pydantic model + prompt changes; (3) basket_pages.yaml content — rubrics + criterion-aligned observation_focus; (4) authoring guide doc. Each task is a single commit. Phases 2 and 3 are interdependent and must ship together.

**Tech Stack:** Python 3.9+, Pydantic v2, PyYAML, `anthropic` async client, pytest

---

## Background: Why Scores Are Inconsistent

The two-pass pipeline has three structural gaps:

**Gap A — Token truncation (Pass 1 fails hard at 8000 tokens).** When Pass 1 hits its limit, the entire competitor is dropped from the report. Claude Sonnet 4.6 supports 64K output; the 8000 cap is a relic of the old 8000 tokens/minute rate limit, not a model constraint.

**Gap B — Horizontal observation vs vertical criteria.** Pass 1 organises evidence into UI sections (CTAs, Pricing, Trust Signals…). Pass 2 scores against criteria (`express_checkout`, `shipping_cost_transparency`…). The model must mentally reorganise Pass 1's output to answer Pass 2's questions. Evidence gets lost in translation — a PayPal button mentioned under "Calls to Action" may not get cited for `express_checkout` scoring.

**Gap C — No scoring anchors.** Without rubrics, Pass 2 invents its own 0–10 scale per run. Pet Plant (PayPal + Google Pay) scores 5, Petshop (Google Pay only) scores 6 — not because the sites differ but because Pass 1 happened to describe Petshop's button in more detail that run. Rubrics pin what each band means so the same evidence always produces the same score.

**What is NOT wrong with the architecture.** Two-pass is the right design: images competing with scoring in a single pass dilutes attention; the `observation.json` audit trail has independent value; re-scoring without re-capturing when criteria change is a real workflow benefit.

---

## Phase 1 — Token Limit Fixes

### Task 1: Raise Pass 1 max_tokens in claude_analyzer.py

**Files:**
- Modify: `src/analyzers/claude_analyzer.py:377`

**Step 1: Write the failing test**

Add to `tests/test_claude_analyzer.py`:

```python
@pytest.mark.asyncio
async def test_observe_screenshots_uses_16000_token_budget(
    analyzer: ClaudeUXAnalyzer,
    tmp_path,
) -> None:
    """Pass 1 must request 16000 output tokens, not 8000."""
    from PIL import Image
    img = Image.new("RGB", (10, 10))
    screenshot = tmp_path / "desktop.png"
    img.save(screenshot)

    captured = []
    mock_obs = {
        "site_name": "x", "url": "u", "analysis_name": "n",
        "desktop": {}, "mobile": {}, "notable_states": [],
    }

    async def mock_create(**kwargs):
        captured.append(kwargs)
        r = MagicMock()
        r.content = [MagicMock(text=json.dumps(mock_obs))]
        return r

    with patch.object(analyzer.client.messages, "create", new=mock_create):
        await analyzer._observe_screenshots(
            screenshot_paths=[str(screenshot)],
            analysis_name="Test",
            observation_focus=[],
            site_name="x",
            url="u",
        )

    assert captured[0]["max_tokens"] == 16000
```

**Step 2: Run to verify it fails**

```bash
cd /home/matt99is/projects/UXMaturityAnalysis
.venv/bin/python -m pytest tests/test_claude_analyzer.py::test_observe_screenshots_uses_16000_token_budget -v
```
Expected: `FAILED — AssertionError: assert 8000 == 16000`

**Step 3: Make the change**

In `src/analyzers/claude_analyzer.py`, line 377, change:
```python
max_tokens=8000,
```
to:
```python
max_tokens=16000,
```

**Step 4: Run to verify it passes**

```bash
.venv/bin/python -m pytest tests/test_claude_analyzer.py::test_observe_screenshots_uses_16000_token_budget -v
```
Expected: `PASSED`

**Step 5: Run full test suite to check no regressions**

```bash
.venv/bin/python -m pytest tests/ -v
```
Expected: all green.

**Step 6: Commit**

```bash
git add src/analyzers/claude_analyzer.py tests/test_claude_analyzer.py
git commit -m "fix: raise Pass 1 max_tokens from 8000 to 16000

Pass 1 was silently dropping competitors when observation exceeded 8000
tokens. Claude Sonnet 4.6 supports 64K output; the 8000 limit was a
relic of the old throughput rate limit, not a model constraint."
```

---

### Task 2: Fix GLM analyzer token limits

The GLM analyzer (OpenAI-compatible API) was never updated when the two-pass
pipeline raised Claude's limits. Pass 1 is still at 3000, Pass 2 at 6000.

**Files:**
- Modify: `src/analyzers/glm_analyzer.py` — find both `max_tokens` lines

**Step 1: Locate the lines**

```bash
grep -n "max_tokens" src/analyzers/glm_analyzer.py
```

Expected output shows two lines — one ~407 (Pass 1 call), one ~467 (Pass 2 call).

**Step 2: Make the changes**

Pass 1 call: `max_tokens=3000` → `max_tokens=8000`
Pass 2 call: `max_tokens=6000` → `max_tokens=12000`

(GLM providers typically have lower limits than Anthropic; 8000/12000 is a
conservative but safe raise. Adjust per provider if needed.)

**Step 3: Run tests**

```bash
.venv/bin/python -m pytest tests/ -v
```
Expected: all green (GLM has no dedicated token-limit tests, but existing
tests must not regress).

**Step 4: Commit**

```bash
git add src/analyzers/glm_analyzer.py
git commit -m "fix: raise GLM analyzer token limits (Pass 1: 3000→8000, Pass 2: 6000→12000)"
```

---

## Phase 2 — Scoring Reliability Infrastructure

### Task 3: Add scoring_rubric field to EvaluationCriterion

**Files:**
- Modify: `src/config_loader.py:16-24`
- Test: `tests/test_config_loader.py`

**Step 1: Write the failing tests**

Add to `tests/test_config_loader.py`:

```python
def test_evaluation_criterion_scoring_rubric_defaults_to_none():
    """scoring_rubric is optional — criteria without one are valid."""
    from src.config_loader import EvaluationCriterion
    criterion = EvaluationCriterion(
        id="test",
        name="Test",
        weight=5.0,
        description="Test",
        evaluation_points=[],
        benchmarks=[],
    )
    assert criterion.scoring_rubric is None


def test_evaluation_criterion_accepts_scoring_rubric():
    """scoring_rubric is stored when provided."""
    from src.config_loader import EvaluationCriterion
    rubric = {
        "8-10": "Excellent",
        "5-7": "Adequate",
        "2-4": "Poor",
        "0-1": "Absent",
    }
    criterion = EvaluationCriterion(
        id="test",
        name="Test",
        weight=5.0,
        description="Test",
        evaluation_points=[],
        benchmarks=[],
        scoring_rubric=rubric,
    )
    assert criterion.scoring_rubric == rubric
```

**Step 2: Run to verify they fail**

```bash
.venv/bin/python -m pytest tests/test_config_loader.py::test_evaluation_criterion_scoring_rubric_defaults_to_none tests/test_config_loader.py::test_evaluation_criterion_accepts_scoring_rubric -v
```
Expected: `FAILED — ValidationError` (field doesn't exist yet).

**Step 3: Add the field to EvaluationCriterion**

In `src/config_loader.py`, the `EvaluationCriterion` class currently ends at line 24. Add one line:

```python
class EvaluationCriterion(BaseModel):
    """Represents a single UX evaluation criterion."""

    id: str
    name: str
    weight: float = Field(ge=0.1, le=10.0)
    description: str
    evaluation_points: List[str]
    benchmarks: List[str]
    scoring_rubric: Optional[Dict[str, str]] = None  # ← add this line
```

The `Optional` and `Dict` are already imported. No other changes to config_loader.py — the YAML loader already passes criterion data straight through to Pydantic; a new optional field just gets populated when present in YAML and defaults to None when absent.

**Step 4: Run to verify the tests pass**

```bash
.venv/bin/python -m pytest tests/test_config_loader.py -v
```
Expected: all green.

**Step 5: Commit**

```bash
git add src/config_loader.py tests/test_config_loader.py
git commit -m "feat: add optional scoring_rubric field to EvaluationCriterion

Rubrics are Dict[str, str] — band label to description (e.g. '8-10':
'...'). Optional with None default; existing criteria and page types
are unaffected until rubrics are added to their YAML files."
```

---

### Task 4: Thread scoring_rubric through criteria_dicts in main.py

**Files:**
- Modify: `main.py:584-594`

**Step 1: Write the failing test**

The existing integration test `test_analyze_competitor_stores_relative_observation_file`
patches the full orchestrator run. Add a targeted unit test that checks the
criteria dicts passed to the analyzer include the rubric field:

Add to `tests/test_claude_analyzer.py`:

```python
def test_criteria_dict_includes_scoring_rubric(analyzer: ClaudeUXAnalyzer) -> None:
    """scoring_rubric key must be present in criteria dicts passed to the prompt builder."""
    criteria_with_rubric = [
        {
            "id": "express_checkout",
            "name": "Express Checkout",
            "weight": 8,
            "description": "Express checkout options",
            "evaluation_points": ["Are express buttons visible?"],
            "benchmarks": ["Baymard: reduces friction"],
            "scoring_rubric": {
                "8-10": "Multiple options above CTA",
                "0-1": "Not present",
            },
        }
    ]
    # _build_analysis_prompt must not raise when scoring_rubric is present
    observation = {"notable_states": [], "desktop": {}, "mobile": {}}
    prompt = analyzer._build_analysis_prompt(
        criteria=criteria_with_rubric,
        analysis_name="Basket Page",
        site_name="example.com",
        url="https://example.com/basket",
        observation=observation,
    )
    assert isinstance(prompt, str)  # did not raise
```

**Step 2: Run to verify — this will pass already** (the prompt builder ignores unknown keys currently). That's fine — this test ensures it keeps passing after we add rubric rendering.

```bash
.venv/bin/python -m pytest tests/test_claude_analyzer.py::test_criteria_dict_includes_scoring_rubric -v
```

**Step 3: Add scoring_rubric to criteria_dicts in main.py**

Find the `criteria_dicts` list comprehension at `main.py:584`:

```python
criteria_dicts = [
    {
        "id": c.id,
        "name": c.name,
        "weight": c.weight,
        "description": c.description,
        "evaluation_points": c.evaluation_points,
        "benchmarks": c.benchmarks,
        "scoring_rubric": c.scoring_rubric,   # ← add this line
    }
    for c in self.analysis_type_config.criteria
]
```

**Step 4: Run full test suite**

```bash
.venv/bin/python -m pytest tests/ -v
```
Expected: all green.

**Step 5: Commit**

```bash
git add main.py tests/test_claude_analyzer.py
git commit -m "feat: pass scoring_rubric through criteria_dicts to analyzer"
```

---

### Task 5: Update _build_analysis_prompt — render rubrics and soften evidence constraint

This is the most important prompt change. Two things happen here:
1. Rubrics are rendered in the criteria block so Pass 2 has scoring anchors.
2. "ONLY this evidence" is replaced with language that permits professional
   judgement for gaps, while still requiring citation for what IS documented.

**Files:**
- Modify: `src/analyzers/claude_analyzer.py` — `_build_analysis_prompt` method (~line 53)

**Step 1: Write the failing tests**

Add to `tests/test_claude_analyzer.py`:

```python
def test_build_analysis_prompt_renders_scoring_rubric(
    analyzer: ClaudeUXAnalyzer,
) -> None:
    """Rubric bands are included in the Pass 2 prompt when criterion has one."""
    criteria = [
        {
            "id": "express_checkout",
            "name": "Express Checkout",
            "weight": 8,
            "description": "Express checkout options",
            "evaluation_points": ["Are express buttons visible?"],
            "benchmarks": ["Baymard: reduces friction"],
            "scoring_rubric": {
                "8-10": "Multiple options above CTA on both viewports",
                "5-7": "One option present, positioning unclear",
                "2-4": "Present but poorly positioned",
                "0-1": "Not present",
            },
        }
    ]
    observation = {"notable_states": [], "desktop": {}, "mobile": {}}
    prompt = analyzer._build_analysis_prompt(
        criteria=criteria,
        analysis_name="Basket Page",
        site_name="example.com",
        url="https://example.com/basket",
        observation=observation,
    )
    assert "Scoring Rubric" in prompt
    assert "Multiple options above CTA on both viewports" in prompt
    assert "8-10" in prompt


def test_build_analysis_prompt_no_rubric_omits_rubric_section(
    analyzer: ClaudeUXAnalyzer,
) -> None:
    """When scoring_rubric is None, no Scoring Rubric section is rendered."""
    criteria = [
        {
            "id": "test",
            "name": "Test",
            "weight": 5,
            "description": "Test",
            "evaluation_points": [],
            "benchmarks": [],
            "scoring_rubric": None,
        }
    ]
    observation = {"notable_states": [], "desktop": {}, "mobile": {}}
    prompt = analyzer._build_analysis_prompt(
        criteria=criteria,
        analysis_name="Test",
        site_name="example.com",
        url="https://example.com",
        observation=observation,
    )
    assert "Scoring Rubric" not in prompt


def test_build_analysis_prompt_softened_evidence_instruction(
    analyzer: ClaudeUXAnalyzer,
) -> None:
    """Pass 2 prompt must not use 'ONLY this evidence' — too punitive for thin observations."""
    criteria = [
        {
            "id": "t", "name": "T", "weight": 1, "description": "T",
            "evaluation_points": [], "benchmarks": [], "scoring_rubric": None,
        }
    ]
    observation = {"notable_states": [], "desktop": {}, "mobile": {}}
    prompt = analyzer._build_analysis_prompt(
        criteria=criteria,
        analysis_name="Test",
        site_name="example.com",
        url="https://example.com",
        observation=observation,
    )
    assert "ONLY this evidence" not in prompt
    # Must still require citation for what IS documented
    assert "cite" in prompt.lower() or "quote" in prompt.lower()
    # Must permit professional judgement for gaps
    assert "professional" in prompt.lower()
```

**Step 2: Run to verify they fail**

```bash
.venv/bin/python -m pytest tests/test_claude_analyzer.py::test_build_analysis_prompt_renders_scoring_rubric tests/test_claude_analyzer.py::test_build_analysis_prompt_no_rubric_omits_rubric_section tests/test_claude_analyzer.py::test_build_analysis_prompt_softened_evidence_instruction -v
```
Expected: first two `FAILED`, third `FAILED` (current prompt has "ONLY this evidence").

**Step 3: Implement the changes in _build_analysis_prompt**

**Change A — Rubric rendering.** In the criteria loop, after the benchmarks
block and before the trailing `\n`, add:

```python
# existing code:
criteria_text += f"\n   Benchmarks:\n"
for benchmark in criterion["benchmarks"]:
    criteria_text += f"   - {benchmark}\n"

# ADD after benchmarks:
rubric = criterion.get("scoring_rubric")
if rubric:
    criteria_text += f"\n   Scoring Rubric:\n"
    for band, description in rubric.items():
        criteria_text += f"   - {band}: {description}\n"

criteria_text += "\n"   # existing trailing newline
```

**Change B — Soften evidence constraint.** In the `observation_section` f-string
(around line 75), the current text reads:

```python
observation_section = f"""
**VISUAL EVIDENCE (from observation pass)**

The following structured observation was made from the screenshots before scoring.
Use ONLY this evidence to support your scores. Do not infer what is not documented here.
If an observation is marked unclear or not visible, reflect that uncertainty in your score.
...
```

Replace those three sentences with:

```python
observation_section = f"""
**VISUAL EVIDENCE (from observation pass)**

The following structured observation was made from the screenshots before scoring.
Base your scores primarily on this documented evidence, quoting it directly for each score.
Where a criterion has gaps in the observation, apply informed professional judgement —
note it explicitly in the evidence field as "Not documented in observation — scored on
basis of [your reasoning]". Absence of documentation is not the same as absence of the feature.
...
```

**Step 4: Run to verify all three new tests pass**

```bash
.venv/bin/python -m pytest tests/test_claude_analyzer.py -v
```
Expected: all green including existing tests. The existing test
`test_build_analysis_prompt_with_observation_cites_evidence` checks for
"cite" or "quote" — the updated text still contains "quoting", so it passes.

**Step 5: Commit**

```bash
git add src/analyzers/claude_analyzer.py tests/test_claude_analyzer.py
git commit -m "feat: render scoring rubrics in Pass 2 prompt, soften evidence constraint

Two changes to _build_analysis_prompt:
1. Rubric bands rendered per-criterion when scoring_rubric is set in YAML.
   Pins the scoring scale so the same evidence produces the same score
   across competitors and runs.
2. Replace 'ONLY this evidence' with guidance that permits professional
   judgement for observation gaps, while still requiring citation for
   what IS documented. Eliminates the systematic downward bias that was
   scoring Viovet's PayPal button as a 3."
```

---

### Task 6: Mirror prompt changes in glm_analyzer.py

The GLM analyzer has its own copy of `_build_analysis_prompt`. Apply identical
changes so both analyzers behave consistently.

**Files:**
- Modify: `src/analyzers/glm_analyzer.py` — `_build_analysis_prompt` method

**Step 1: Locate the benchmarks loop and observation section**

```bash
grep -n "scoring_rubric\|ONLY this evidence\|Benchmarks" src/analyzers/glm_analyzer.py
```

**Step 2: Apply identical changes**

Same as Task 5 Step 3 — rubric rendering after benchmarks loop, softened
evidence instruction in the observation_section f-string.

**Step 3: Run full test suite**

```bash
.venv/bin/python -m pytest tests/ -v
```
Expected: all green.

**Step 4: Commit**

```bash
git add src/analyzers/glm_analyzer.py
git commit -m "feat: mirror rubric rendering and softened evidence instruction in GLM analyzer"
```

---

## Phase 3 — basket_pages.yaml Content

### Task 7: Add criterion-aligned observation_focus and scoring rubrics

This is the content task — the infrastructure from Phase 2 makes it possible.
Two additions to `criteria_config/basket_pages.yaml`:

1. **Six new `observation_focus` items** — criterion-aligned, replacing generic
   UI section descriptions. Each maps to one specific criterion's evidence needs.
2. **`scoring_rubric` on all 11 criteria** — four bands each, one sentence.

**Files:**
- Modify: `criteria_config/basket_pages.yaml`

**Step 1: Write a failing test that verifies the final state**

Add to `tests/test_config_loader.py`:

```python
def test_basket_pages_has_criterion_aligned_observation_focus():
    """basket_pages observation_focus must include express checkout evidence item."""
    config = AnalysisConfig()
    analysis = config.get_analysis_type("basket_pages")
    focus_text = " ".join(analysis.observation_focus).lower()
    assert "express" in focus_text, (
        "observation_focus must include an express checkout item so Pass 1 "
        "captures the evidence Pass 2 needs to score express_checkout"
    )


def test_basket_pages_all_criteria_have_scoring_rubric():
    """Every basket page criterion must have a scoring_rubric with all four bands."""
    config = AnalysisConfig()
    analysis = config.get_analysis_type("basket_pages")
    expected_bands = {"8-10", "5-7", "2-4", "0-1"}
    for criterion in analysis.criteria:
        assert criterion.scoring_rubric is not None, (
            f"Criterion '{criterion.id}' has no scoring_rubric"
        )
        assert set(criterion.scoring_rubric.keys()) == expected_bands, (
            f"Criterion '{criterion.id}' rubric must have bands: {expected_bands}"
        )
```

**Step 2: Run to verify they fail**

```bash
.venv/bin/python -m pytest tests/test_config_loader.py::test_basket_pages_has_criterion_aligned_observation_focus tests/test_config_loader.py::test_basket_pages_all_criteria_have_scoring_rubric -v
```
Expected: both `FAILED`.

**Step 3: Update basket_pages.yaml**

**3a — Replace the `observation_focus` block** (currently 7 items) with the
following 13 items. The first 7 are refined versions of the existing ones; the
last 6 are new criterion-aligned additions:

```yaml
observation_focus:
  # Existing items — refined
  - "Cart contents — all items, quantities, individual prices, subtotals; product images (size and clarity), pack size/weight prominence, variant details (flavour, life stage)"
  - "Order summary breakdown — subtotal, shipping cost, discounts applied, and grand total; are all components itemised and labelled?"
  - "Free delivery threshold — exact messaging visible (e.g. 'Add £5.00 for free delivery'), progress bar or indicator present, current gap to threshold"
  - "Cross-sell or recommendation section — document TWO things separately: (1) what is in the basket (specific products, brand, species/category, life stage if visible); (2) what is being recommended (product name, type, brand). Both must be documented for Pass 2 to assess contextual relevance."
  - "Coupon or promo code input — visibility, placement, current state"
  - "Quantity adjustment controls — +/- buttons or dropdown; is there an 'Update basket' or 'Update' button/link present? If so, price likely requires manual trigger to recalculate rather than updating automatically"
  - "Item removal option — visibility and placement per item"
  # New criterion-aligned additions
  - "Express checkout buttons (PayPal, Google Pay, Apple Pay, Shop Pay) — exact position relative to the main checkout CTA (above or below?), present on desktop and mobile separately, any value proposition text visible (e.g. 'Skip the forms')"
  - "Delivery date or window shown in basket — specific date (e.g. 'Arrives Tuesday 5th March') vs vague range (e.g. '3-5 days'), order cutoff time if visible, any urgency messaging"
  - "Subscription or auto-delivery indicator in basket — is the subscription nature of any items clearly communicated? Delivery frequency shown, savings percentage visible, option to modify or cancel accessible. NOTE: do NOT attempt to assess whether auto-delivery was pre-selected as default — basket state is set by the user at PDP stage and cannot be evaluated here."
  - "Mobile layout — overall design for mobile viewport: text readability, touch target sizes, ease of quantity editing, accessibility of basket summary and checkout action without excessive scrolling"
  - "Primary checkout CTA — button text, colour, and visual prominence on both desktop and mobile; any competing CTAs of similar visual weight; sticky/fixed behaviour on mobile if present"
  - "Payment method icons and trust/security badges — location relative to checkout CTA; return policy link visibility; customer service contact visible"
  - "Dark patterns — pre-checked opt-in boxes for add-ons or marketing, hidden opt-outs, misleading button text or UI hierarchy, urgency/scarcity messaging (countdown timers, low stock warnings). NOTE: auto-delivery pre-selection cannot be assessed on basket pages — that state is set by the user at PDP stage. Flag it there, not here."
```

**3b — Add `scoring_rubric` to each of the 11 criteria.** Add after the
`benchmarks` block of each criterion with no other changes:

```yaml
  - id: "shipping_cost_transparency"
    # ... existing fields unchanged ...
    # NOTE: progress bars and multiple delivery options are enhancements, not requirements.
    # A site showing delivery cost clearly + a specific free threshold message scores 8-10.
    scoring_rubric:
      "8-10": "Delivery cost shown in basket and free delivery threshold clearly communicated with a specific amount (e.g. 'Add £5.00 for free delivery'); user is not surprised by cost at checkout"
      "5-7": "Delivery cost visible but free threshold absent or vague; or threshold shown but delivery cost not visible until checkout"
      "2-4": "Delivery cost hidden until checkout and/or no threshold information on basket page"
      "0-1": "No delivery cost or threshold information visible on basket page"

  - id: "subscription_auto_delivery"
    # ... existing fields unchanged ...
    # NOTE: dark pattern detection (pre-selected default) is NOT applicable on basket pages.
    # Basket state is set by the user at PDP stage. Score purely on how clearly the
    # subscription is communicated and how easy it is to manage from the basket.
    scoring_rubric:
      "8-10": "Subscription status clearly communicated in basket (frequency, savings percentage shown), easy access to modify frequency or switch to one-time, cancellation terms visible"
      "5-7": "Subscription nature of order shown but savings, frequency, or flexibility terms are unclear or hard to find"
      "2-4": "Subscription items in basket not clearly flagged as recurring, or modification options absent/buried"
      "0-1": "No subscription offering on site; or subscription items present in basket but with no subscription information visible"

  - id: "basket_summary"
    # ... existing fields unchanged ...
    scoring_rubric:
      "8-10": "Itemised breakdown of subtotal, delivery, discounts, and total; large prominent total; real-time updates on quantity change"
      "5-7": "Total clearly visible but breakdown is incomplete or not all cost components are labelled"
      "2-4": "Total shown without breakdown, or breakdown is confusing and costs are hard to reconcile"
      "0-1": "No clear order total visible on basket page"

  - id: "product_information_cart"
    # ... existing fields unchanged ...
    scoring_rubric:
      "8-10": "Clear product image, pack size/weight prominent, unit price visible, variants shown (flavour/life stage), inline quantity editing available"
      "5-7": "Product identifiable and images present but pack size/weight unclear or variants not shown"
      "2-4": "Products listed by name only; no image, weight, or variant detail visible in cart view"
      "0-1": "Cart contents unclear or individual products not identifiable"

  - id: "mobile_layout_usability"
    # ... existing fields unchanged ...
    scoring_rubric:
      "8-10": "Layout clearly designed for mobile — readable text, appropriately sized touch targets, easy quantity editing, basket summary accessible without excessive scrolling, no horizontal scroll"
      "5-7": "Functional on mobile but usability compromised — small touch targets, text requires zooming, or key basket elements require significant scrolling to reach"
      "2-4": "Mobile experience poor — elements misaligned, overlapping, or inaccessible; layout clearly adapted from desktop with no mobile-specific consideration"
      "0-1": "Desktop-only layout served on mobile viewport — no responsive adaptation"

  - id: "delivery_estimates"
    # ... existing fields unchanged ...
    scoring_rubric:
      "8-10": "Specific delivery date shown in basket (e.g. 'Arrives Tuesday 5th March') AND order cutoff time displayed (e.g. 'Order within 2hrs for next-day delivery'); urgency messaging where relevant"
      "5-7": "Specific delivery date shown but no cutoff time; or delivery window with cutoff time but no specific date"
      "2-4": "Vague delivery messaging only (e.g. 'standard delivery', '3–5 working days') — no specific date or cutoff"
      "0-1": "No delivery timing information visible on basket page"

  - id: "express_checkout"
    # ... existing fields unchanged ...
    scoring_rubric:
      "8-10": "Two or more express options (PayPal, Google Pay, Apple Pay, Shop Pay) visible and prominent, positioned above the main checkout CTA, present on both desktop and mobile"
      "5-7": "At least one express option present and reasonably prominent; positioning relative to CTA or mobile presence not fully confirmed in observation"
      "2-4": "Express option documented but positioned below main CTA, footer-only, or only on one viewport"
      "0-1": "No express checkout options documented in observation"

  - id: "quantity_management"
    # ... existing fields unchanged ...
    scoring_rubric:
      "8-10": "Per-item +/- buttons with immediate price update; clear remove option; quantity editable without page reload"
      "5-7": "Quantity changeable but via dropdown or text field rather than +/- buttons; or an 'Update' button is present indicating price does not recalculate automatically"
      "2-4": "Quantity editing is difficult, unclear, or requires navigating away from the basket"
      "0-1": "No visible way to change item quantities in basket"

  - id: "cta_buttons"
    # ... existing fields unchanged ...
    scoring_rubric:
      "8-10": "Primary CTA large, high-contrast colour, action-oriented copy (e.g. 'Proceed to Checkout'), no competing CTAs of equal visual weight; sticky on mobile where present is a positive differentiator"
      "5-7": "CTA clearly visible and labelled but copy is generic ('Next', 'Continue'), or secondary buttons compete for attention"
      "2-4": "CTA present but low-contrast, small, or visually competes with equally prominent secondary buttons"
      "0-1": "No clear primary checkout CTA visible on basket page"

  - id: "cross_sell_recommendations"
    # ... existing fields unchanged ...
    # NOTE: "Contextual" means observable signals: same species, same brand, complementary product type
    # (treats + food, accessories + a specific item). Deep algorithmic relevance is not assessable.
    # The observation_focus item explicitly asks Pass 1 to document BOTH basket contents AND
    # cross-sell contents. If a gap occurs despite this, re-run the analysis — do not score blind.
    scoring_rubric:
      "8-10": "Pass 1 documented basket contents and cross-sells; recommended products show clear observable relevance (same brand, same species, complementary type — e.g. treats alongside food); inline add-to-cart without leaving basket"
      "5-7": "Recommendations present and species/category appropriate but specific relevance to basket contents is unclear; or add-to-cart requires navigating away"
      "2-4": "Recommendations appear entirely generic (species mismatch, irrelevant categories) or are so numerous they distract from the checkout flow"
      "0-1": "No cross-sell section visible on basket page"

  - id: "payment_and_trust"
    # ... existing fields unchanged ...
    scoring_rubric:
      "8-10": "Payment method icons displayed near CTA, trust/security badge visible, return policy clearly linked, customer service contact accessible"
      "5-7": "Some trust signals present (icons or badge) but return policy hard to find or no customer service contact"
      "2-4": "Minimal trust signals — no payment icons, no security badge, return policy absent or buried in footer"
      "0-1": "No trust signals of any kind visible on basket page"
```

**Step 4: Verify YAML loads cleanly**

```bash
cd /home/matt99is/projects/UXMaturityAnalysis
.venv/bin/python src/config_loader.py
```
Expected output includes `basket_pages` in available types with 11 criteria. No errors.

**Step 5: Run the new tests**

```bash
.venv/bin/python -m pytest tests/test_config_loader.py -v
```
Expected: all green including the two new tests.

**Step 6: Run full suite**

```bash
.venv/bin/python -m pytest tests/ -v
```
Expected: all green.

**Step 7: Commit**

```bash
git add criteria_config/basket_pages.yaml tests/test_config_loader.py
git commit -m "feat: add scoring rubrics and criterion-aligned observation_focus to basket_pages

Addresses the root cause of express_checkout scoring inconsistency (Pet
Plant 5, Viovet 3, Petshop 6 for comparable implementations).

Changes:
- observation_focus: 7 generic items → 13 criterion-aligned items. Each
  maps directly to evidence a specific criterion needs in Pass 2.
- scoring_rubric: all 11 criteria now have 4-band rubrics (8-10/5-7/2-4/0-1).
  Anchors the Pass 2 scoring scale so the same evidence produces the same
  score across competitors and runs."
```

---

## Phase 4 — Authoring Documentation

### Task 8: Create criteria-authoring-guide.md

This document is the replication template. Anyone creating a new page type
(or updating existing criteria) should read it first.

**Files:**
- Create: `docs/criteria-authoring-guide.md`

**Step 1: Write the document**

```markdown
# Criteria Authoring Guide

How to write and maintain `criteria_config/*.yaml` files. Follow this guide
for all new page types and when updating existing criteria.

---

## Overview of the two-pass pipeline

Each competitor analysis makes two API calls:

**Pass 1 (Observe):** Screenshots → structured observation JSON.
The model acts as a witness — no scoring, no evaluation. Output includes
`observation_focus` items plus universal sections (pricing, dark patterns, etc.).
Saved as `observation.json` per competitor.

**Pass 2 (Score):** Observation JSON → scored analysis.
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
Good: `"Express checkout buttons (PayPal, Google Pay, Apple Pay) — exact
position relative to main checkout CTA (above or below?), present on
desktop and mobile separately"`.

**Specify the key distinctions.** If a criterion cares about desktop vs
mobile separately, say so. If positioning matters (above vs below CTA),
say so. These distinctions are what Pass 2's rubric scores on.

**Keep each item to one sentence or two short clauses.** The observation
prompt already has universal sections. observation_focus items are
supplemental, not exhaustive.

### Token budget

Each observation_focus item adds ~25–40 tokens to the Pass 1 prompt.
With Pass 1 at 16000 output tokens, throughput is not a concern.
Keep items concise for readability, not for token reasons.

---

## scoring_rubric

### What it does

Rendered in the Pass 2 prompt directly after each criterion's evaluation_points
and benchmarks. Anchors the 0–10 scale so the same evidence produces the
same score across competitors and runs.

### Required format

Four bands, one sentence each:

```yaml
scoring_rubric:
  "8-10": "<what earns a high score — the positive case>"
  "5-7": "<adequate implementation — present but incomplete>"
  "2-4": "<present but poorly executed or only partially visible>"
  "0-1": "<absent or completely non-functional>"
```

**Quote keys as strings** (`"8-10"` not `8-10`). PyYAML parses unquoted
ranges inconsistently.

### Authoring rules

**One sentence per band.** Rubrics must stay concise — they add ~60 tokens
per criterion to Pass 2's input. Ten-word sentences, not paragraphs.

**The 8-10 band describes the ideal, not perfection.** A site doesn't need
every evaluation_point fulfilled to score 8. Describe what a strong
real-world implementation looks like.

**The 0-1 band describes absence, not failure.** "No X documented in
observation" — not "catastrophic failure". Missing = 0-1, poor = 2-4.

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
  weight: 8                         # 1–10; see tier guidance below
  description: "One sentence — what this criterion measures."
  evaluation_points:
    - "Question 1 about what to look for?"
    - "Question 2 — be specific about states (above/below, selected/unselected)"
    - "Question 3"
  benchmarks:
    - source: "Baymard Institute"
      finding: "Evidence sentence from research"
    - source: "Best Practice"
      finding: "Industry norm"
  scoring_rubric:
    "8-10": "Strong positive case — references key distinctions from observation_focus"
    "5-7": "Present but incomplete or partially visible"
    "2-4": "Present but poorly positioned, implemented, or only on one viewport"
    "0-1": "Not documented in observation"
```

---

## Weight tiers

| Tier | Weight | Use for |
|------|--------|---------|
| Critical | 9–10 | Directly drives abandonment (shipping cost, basket clarity) |
| Important | 7–8 | Strong conversion influence (express checkout, CTAs) |
| Supporting | 5–6 | Trust and experience quality (trust signals, cross-sell) |
| Enhancement | 1–4 | Nice-to-have differentiation |

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
4. Run `pytest tests/ -v` — no regression
5. One commit per page type

The basket_pages.yaml in this repo is the reference implementation.
```

**Step 2: Add entry to docs/archive/INDEX.md**

Under `## 2026-03` (create the section if it doesn't exist):

```markdown
## 2026-03

| File | Type | Description |
|------|------|-------------|
| `../plans/2026-03-02-scoring-reliability-overhaul.md` | Implementation | Scoring reliability overhaul — token limits, rubrics, observation alignment |
```

**Step 3: Commit**

```bash
git add docs/criteria-authoring-guide.md docs/archive/INDEX.md
git commit -m "docs: add criteria authoring guide — rubric and observation_focus standards

Documents the two-pass pipeline's authoring contract: how observation_focus
items must map to criteria evaluation_points, rubric format and token budget
constraints, and a checklist for new page types. basket_pages.yaml is the
reference implementation."
```

---

## Verification: End-to-End Smoke Test

After all tasks are complete, verify the full pipeline still works:

```bash
# All tests pass
.venv/bin/python -m pytest tests/ -v

# Config loads cleanly for all page types
.venv/bin/python src/config_loader.py

# Linters pass
pre-commit run --all-files
```

---

## What this does NOT change

- The two-pass architecture — it's correct
- `reanalyze_screenshots.py` skip logic — unaffected
- HTML report structure — `scoring_rubric` is prompt-only; it doesn't appear in `analysis.json` output
- Any other page type YAMLs — basket_pages is the reference; others are updated separately using the authoring guide

---

## Next: other page types

After this plan ships, apply the same treatment to:
- `criteria_config/product_pages.yaml`
- `criteria_config/checkout_pages.yaml`
- `criteria_config/homepage_pages.yaml`

Use `docs/criteria-authoring-guide.md` as the process. Each is a standalone
plan or a single commit following the Task 7 pattern.
