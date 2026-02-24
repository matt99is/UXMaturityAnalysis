# Two-Pass Analysis Pipeline Implementation Plan

**Goal:** Replace the single-call UX analysis with a two-pass pipeline — observe first (pass 1, with screenshots), score second (pass 2, text-only) — to eliminate attention dilution and build an auditable evidence trail.

**Architecture:** Pass 1 sends screenshots with a focused observation prompt (no scoring) and saves `observation.json` per competitor. Pass 2 sends the observation JSON as text with the criteria and scores against documented evidence, requiring citation for every score. The `notable_states` array in pass 1 acts as a forcing function — every flagged anomaly must be addressed in the scoring.

**Tech Stack:** Python 3.9+, `anthropic` async client, Pydantic, PyYAML, Pillow, Jinja2 (HTML reports)

---

### Task 1: Add `observation_focus` to YAML criteria configs

**Files:**
- Modify: `criteria_config/product_pages.yaml`
- Modify: `criteria_config/basket_pages.yaml`
- Modify: `criteria_config/checkout_pages.yaml`
- Modify: `criteria_config/homepage_pages.yaml`

**Step 1: Add `observation_focus` block to `product_pages.yaml`**

After line 47 (after the `viewports` block, before `criteria:`), add:

```yaml
observation_focus:
  - "Product variants (size, colour, quantity) and which are selected by default"
  - "Subscription vs one-time purchase toggle — state explicitly which option is pre-selected (look for filled radio buttons, highlighted cards, checked checkboxes)"
  - "Image gallery state — number of images visible, zoom controls, swipe indicators"
  - "Stock availability messaging (in stock, low stock, out of stock)"
  - "Express payment buttons visible (Apple Pay, Google Pay, PayPal, Shop Pay)"
  - "Sticky add-to-cart button presence on mobile"
```

**Step 2: Add `observation_focus` block to `basket_pages.yaml`**

After the `viewports` block:

```yaml
observation_focus:
  - "Cart contents — all items, quantities, individual prices, subtotals"
  - "Order summary breakdown (subtotal, shipping cost, discounts applied, total)"
  - "Free delivery threshold — current status and how close the user is"
  - "Upsell or cross-sell placements — location and content"
  - "Coupon or promo code input — visibility and state"
  - "Quantity adjustment controls — +/- buttons or dropdown state"
  - "Item removal option — visibility and placement"
```

**Step 3: Add `observation_focus` block to `checkout_pages.yaml`**

After the `viewports` block:

```yaml
observation_focus:
  - "Form fields visible — which are pre-filled, which are empty, which are required"
  - "Payment method options — all options listed and which (if any) is pre-selected"
  - "Order summary — visibility, collapsed or expanded state"
  - "Progress indicator — current step label and total steps shown"
  - "Guest checkout vs account creation — default option shown"
  - "Save card or address checkbox — default state (checked or unchecked)"
  - "Express checkout options visible at top of checkout"
```

**Step 4: Add `observation_focus` block to `homepage_pages.yaml`**

After the `viewports` block:

```yaml
observation_focus:
  - "Hero messaging — headline text and primary value proposition verbatim"
  - "Promotional banners or offers — exact text of any active promotions"
  - "Navigation structure — main categories visible in header"
  - "Featured categories or product collections visible"
  - "Any personalisation indicators or location-based content"
  - "Cookie consent or GDPR banner — visibility and default option state"
  - "Newsletter or subscription signup — visibility and placement"
```

**Step 5: Commit**

```bash
git add criteria_config/
git commit -m "feat: add observation_focus blocks to all criteria YAML configs"
```

---

### Task 2: Extend `AnalysisType` model to load `observation_focus`

**Files:**
- Modify: `src/config_loader.py:48-57` (AnalysisType model)
- Modify: `src/config_loader.py:109-121` (analysis_config dict builder)
- Test: `tests/test_config_loader.py`

**Step 1: Write the failing test**

Create `tests/test_config_loader.py`:

```python
import pytest
from src.config_loader import AnalysisConfig, AnalysisType

def test_analysis_type_has_observation_focus():
    """observation_focus is loaded from YAML and available on AnalysisType."""
    config = AnalysisConfig()
    analysis = config.get_analysis_type("product_pages")
    assert hasattr(analysis, "observation_focus")
    assert isinstance(analysis.observation_focus, list)
    assert len(analysis.observation_focus) > 0

def test_analysis_type_observation_focus_defaults_to_empty():
    """observation_focus defaults to empty list if not in YAML."""
    # AnalysisType with no observation_focus key
    data = {
        "name": "Test",
        "description": "Test analysis",
        "navigation": {},
        "screenshot_config": {"viewports": [], "full_page": True},
        "criteria": [],
        "output_template": {},
        "interaction": {"requires_interaction": False, "mode": "headless", "timeout": 0}
    }
    analysis = AnalysisType(**data)
    assert analysis.observation_focus == []
```

**Step 2: Run test to verify it fails**

```bash
cd /home/matt99is/projects/UXMaturityAnalysis
python -m pytest tests/test_config_loader.py -v
```

Expected: `FAILED - AttributeError: 'AnalysisType' object has no attribute 'observation_focus'`

**Step 3: Add `observation_focus` to `AnalysisType` model**

In `src/config_loader.py`, modify the `AnalysisType` class (line 48):

```python
class AnalysisType(BaseModel):
    """Configuration for a specific analysis type (e.g., basket pages, product pages)."""
    name: str
    description: str
    analysis_context: Optional[str] = None
    observation_focus: List[str] = []  # Page-specific observation prompts for pass 1
    interaction: InteractionConfig = InteractionConfig()
    navigation: Dict[str, Any]
    screenshot_config: ScreenshotConfig
    criteria: List[EvaluationCriterion]
    output_template: Dict[str, Any]
```

**Step 4: Load `observation_focus` from YAML in `_load_config()`**

In `src/config_loader.py`, modify the `analysis_config` dict builder (around line 110). Change:

```python
                analysis_config = {
                    "name": criteria_config.get("name", analysis_type_name),
                    "description": f"Analysis for {criteria_config.get('name', analysis_type_name)}",
                    "analysis_context": criteria_config.get("analysis_context"),
```

To:

```python
                analysis_config = {
                    "name": criteria_config.get("name", analysis_type_name),
                    "description": f"Analysis for {criteria_config.get('name', analysis_type_name)}",
                    "analysis_context": criteria_config.get("analysis_context"),
                    "observation_focus": criteria_config.get("observation_focus", []),
```

**Step 5: Run test to verify it passes**

```bash
python -m pytest tests/test_config_loader.py -v
```

Expected: `PASSED`

**Step 6: Commit**

```bash
git add src/config_loader.py tests/test_config_loader.py
git commit -m "feat: add observation_focus field to AnalysisType model"
```

---

### Task 3: Add observation prompt builder to `ClaudeUXAnalyzer`

**Files:**
- Modify: `src/analyzers/claude_analyzer.py` (add method after line 156)
- Test: `tests/test_claude_analyzer.py`

**Step 1: Write the failing test**

Create `tests/test_claude_analyzer.py`:

```python
import pytest
from src.analyzers.claude_analyzer import ClaudeUXAnalyzer

@pytest.fixture
def analyzer():
    return ClaudeUXAnalyzer(api_key="test-key")

def test_build_observation_prompt_includes_universal_sections(analyzer):
    prompt = analyzer._build_observation_prompt(
        analysis_name="Product Page UX Maturity Analysis",
        observation_focus=[],
        site_name="example.com",
        url="https://example.com/product"
    )
    assert "PRICING & OFFERS" in prompt
    assert "INTERACTIVE STATES" in prompt
    assert "DARK PATTERNS" in prompt
    assert "notable_states" in prompt
    assert "do not evaluate" in prompt.lower() or "do not score" in prompt.lower()

def test_build_observation_prompt_includes_page_specific_focus(analyzer):
    focus = ["Subscription vs one-time purchase toggle — which is pre-selected"]
    prompt = analyzer._build_observation_prompt(
        analysis_name="Product Page",
        observation_focus=focus,
        site_name="example.com",
        url="https://example.com/product"
    )
    assert "Subscription vs one-time purchase toggle" in prompt

def test_build_observation_prompt_excludes_scoring_language(analyzer):
    prompt = analyzer._build_observation_prompt(
        analysis_name="Product Page",
        observation_focus=[],
        site_name="example.com",
        url="https://example.com/product"
    )
    # Pass 1 should have no scoring language
    assert "score" not in prompt.lower()
    assert "criterion" not in prompt.lower()
```

**Step 2: Run test to verify it fails**

```bash
python -m pytest tests/test_claude_analyzer.py -v
```

Expected: `FAILED - AttributeError: 'ClaudeUXAnalyzer' object has no attribute '_build_observation_prompt'`

**Step 3: Add `_build_observation_prompt()` to `ClaudeUXAnalyzer`**

In `src/analyzers/claude_analyzer.py`, add the following method after `_build_analysis_prompt()` (after line 156):

```python
    def _build_observation_prompt(
        self,
        analysis_name: str,
        observation_focus: List[str],
        site_name: str,
        url: str
    ) -> str:
        """
        Build pass 1 observation prompt.

        The model acts as a witness only — no scoring, no evaluation.
        All interactive states, defaults, and anomalies are documented
        so pass 2 can score against concrete evidence.
        """
        page_specific = ""
        if observation_focus:
            page_specific = "\n\nPAGE-SPECIFIC OBSERVATIONS\n"
            for item in observation_focus:
                page_specific += f"- {item}\n"

        prompt = f"""You are documenting the visual state of a webpage as evidence for a UX audit.
Describe only what you can see in the screenshots. Do not evaluate, score, or recommend.
Be a precise witness. If something is unclear or not visible, say so explicitly.

Page: {site_name} — {analysis_name}
URL: {url}

For each section below, document what is visible in BOTH the desktop and mobile screenshots.
Be precise about interactive states: selected vs unselected, checked vs unchecked, highlighted vs default.
Quote visible text verbatim where relevant.

---

PRICING & OFFERS
- All prices shown, their format and visual prominence
- Any strikethrough or original prices alongside sale prices
- Subscription or recurring billing options — state explicitly which option appears selected or highlighted by default
- Free delivery thresholds or shipping cost messaging visible

INTERACTIVE STATES
- Any pre-selected options (radio buttons, checkboxes, toggles, dropdowns)
- Default form field values visible
- Highlighted, active, or visually emphasised options
- Any opt-in or opt-out states and their default position

CALLS TO ACTION
- Primary CTA button: exact text, colour, size, and placement
- Secondary CTAs visible
- Express payment buttons (Apple Pay, Google Pay, PayPal, etc.)

TRUST SIGNALS
- Reviews or ratings visible — star score and review count if shown
- Trust badges, guarantees, security indicators
- Returns or refund policy text visible

FORMS & INPUTS
- All visible input fields and their current state
- Pre-filled values
- Required field indicators
{page_specific}
NAVIGATION & STRUCTURE
- Header content and main navigation visible
- Breadcrumbs or progress indicators
- Sticky elements (headers, CTAs)

DARK PATTERNS (document any of the following if present)
- Pre-selected subscription or recurring billing options
- Pre-checked boxes for add-ons, marketing, or optional extras
- Hidden, de-emphasised, or small opt-out options
- Urgency or scarcity messaging (countdown timers, low stock warnings)
- Misleading button text or confusing UI hierarchy

---

Return your observations as JSON with this exact structure:
{{
  "site_name": "{site_name}",
  "url": "{url}",
  "analysis_name": "{analysis_name}",
  "desktop": {{
    "pricing_and_offers": "<observations>",
    "interactive_states": "<observations>",
    "calls_to_action": "<observations>",
    "trust_signals": "<observations>",
    "forms_and_inputs": "<observations>",
    "page_specific": "<observations>",
    "navigation_and_structure": "<observations>",
    "dark_patterns": "<observations or 'None observed'>"
  }},
  "mobile": {{
    "pricing_and_offers": "<observations>",
    "interactive_states": "<observations>",
    "calls_to_action": "<observations>",
    "trust_signals": "<observations>",
    "forms_and_inputs": "<observations>",
    "page_specific": "<observations>",
    "navigation_and_structure": "<observations>",
    "dark_patterns": "<observations or 'None observed'>"
  }},
  "notable_states": [
    "<any unusual, deceptive, or noteworthy UI state observed — one item per entry>"
  ]
}}

The notable_states array is critical. Include every anomaly, dark pattern, unusual default,
or noteworthy state you observed — even if it seems minor. Each entry should be a plain
English sentence describing exactly what was seen.

IMPORTANT JSON FORMATTING RULES:
- All string values MUST properly escape special characters
- Use \\n for newlines within strings
- Use \\" for quotes within strings
- Do NOT include any text outside the JSON object
"""
        return prompt
```

**Step 4: Run test to verify it passes**

```bash
python -m pytest tests/test_claude_analyzer.py -v
```

Expected: All 3 tests `PASSED`

**Step 5: Commit**

```bash
git add src/analyzers/claude_analyzer.py tests/test_claude_analyzer.py
git commit -m "feat: add _build_observation_prompt to ClaudeUXAnalyzer"
```

---

### Task 4: Add `_observe_screenshots()` async method

**Files:**
- Modify: `src/analyzers/claude_analyzer.py` (add method after `_build_observation_prompt`)

**Step 1: Add `_observe_screenshots()` method**

In `src/analyzers/claude_analyzer.py`, add the following method after `_build_observation_prompt()`:

```python
    async def _observe_screenshots(
        self,
        screenshot_paths: List[str],
        analysis_name: str,
        observation_focus: List[str],
        site_name: str,
        url: str
    ) -> Dict[str, Any]:
        """
        Pass 1: Send screenshots and return structured visual observations.

        No scoring or criteria. The model documents what it sees as evidence.
        Output is saved to observation.json for use in pass 2.

        Returns:
            {"success": True, "observation": {...}} or {"success": False, "error": "..."}
        """
        prompt = self._build_observation_prompt(analysis_name, observation_focus, site_name, url)

        image_content = []
        for path in screenshot_paths:
            if not Path(path).exists():
                continue
            image_data = self._load_image_as_base64(path)
            image_content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": image_data
                }
            })

        content = image_content + [{"type": "text", "text": prompt}]

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=3000,  # Observations are compact — no scoring needed
                messages=[{"role": "user", "content": content}]
            )

            response_text = response.content[0].text

            # Parse JSON — same handling as analyze_screenshots
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                json_text = response_text[json_start:json_end].strip()
            else:
                json_text = response_text

            observation = json.loads(json_text)
            observation["screenshots_analyzed"] = screenshot_paths
            observation["model_used"] = self.model

            return {"success": True, "observation": observation}

        except json.JSONDecodeError as e:
            return {
                "success": False,
                "error": f"Failed to parse observation response as JSON: {e}",
                "raw_response": response_text if "response_text" in dir() else None
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
```

**Step 2: Add test for `_observe_screenshots` (mock the API call)**

Add to `tests/test_claude_analyzer.py`:

```python
import json
from unittest.mock import AsyncMock, patch, MagicMock

@pytest.mark.asyncio
async def test_observe_screenshots_returns_observation_on_success(analyzer, tmp_path):
    """_observe_screenshots calls Claude and returns parsed observation dict."""
    # Create a dummy screenshot file
    from PIL import Image
    img = Image.new("RGB", (100, 100), color=(255, 255, 255))
    screenshot = tmp_path / "desktop.png"
    img.save(screenshot)

    mock_observation = {
        "site_name": "example.com",
        "url": "https://example.com/product",
        "analysis_name": "Product Page",
        "desktop": {"dark_patterns": "None observed"},
        "mobile": {"dark_patterns": "None observed"},
        "notable_states": ["Annual subscription pre-selected by default"]
    }

    mock_response = MagicMock()
    mock_response.content = [MagicMock(text=json.dumps(mock_observation))]

    with patch.object(analyzer.client.messages, "create", new=AsyncMock(return_value=mock_response)):
        result = await analyzer._observe_screenshots(
            screenshot_paths=[str(screenshot)],
            analysis_name="Product Page",
            observation_focus=["Subscription toggle state"],
            site_name="example.com",
            url="https://example.com/product"
        )

    assert result["success"] is True
    assert result["observation"]["notable_states"] == ["Annual subscription pre-selected by default"]
```

**Step 3: Install pytest-asyncio if needed, then run tests**

```bash
pip install pytest-asyncio
python -m pytest tests/test_claude_analyzer.py -v
```

Expected: All tests `PASSED`

**Step 4: Commit**

```bash
git add src/analyzers/claude_analyzer.py tests/test_claude_analyzer.py
git commit -m "feat: add _observe_screenshots pass 1 method to ClaudeUXAnalyzer"
```

---

### Task 5: Update `_build_analysis_prompt()` to accept observation

**Files:**
- Modify: `src/analyzers/claude_analyzer.py:31-156` (`_build_analysis_prompt`)

**Step 1: Add test for observation-aware prompt**

Add to `tests/test_claude_analyzer.py`:

```python
def test_build_analysis_prompt_with_observation_cites_evidence(analyzer):
    """When observation is provided, prompt requires evidence citation and notable_states handling."""
    observation = {
        "notable_states": ["Annual subscription pre-selected by default"],
        "desktop": {"dark_patterns": "Annual plan radio button is pre-selected"},
        "mobile": {"dark_patterns": "Annual plan radio button is pre-selected"}
    }
    criteria = [{
        "id": "subscription_purchase_options",
        "name": "Subscription/Auto-Delivery Options",
        "weight": 1.2,
        "description": "Test",
        "evaluation_points": ["Check default selection"],
        "benchmarks": ["Baymard: pre-selected options increase abandonment"]
    }]
    prompt = analyzer._build_analysis_prompt(
        criteria=criteria,
        analysis_name="Product Page",
        site_name="example.com",
        url="https://example.com",
        observation=observation
    )
    assert "notable_states" in prompt
    assert "Annual subscription pre-selected by default" in prompt
    assert "evidence" in prompt.lower()
    assert "cite" in prompt.lower() or "quote" in prompt.lower()

def test_build_analysis_prompt_without_observation_unchanged(analyzer):
    """Without observation, prompt works as before (backward compat)."""
    criteria = [{
        "id": "test", "name": "Test", "weight": 1.0,
        "description": "Test", "evaluation_points": [], "benchmarks": []
    }]
    prompt = analyzer._build_analysis_prompt(
        criteria=criteria,
        analysis_name="Product Page",
        site_name="example.com",
        url="https://example.com"
    )
    assert "example.com" in prompt
    assert "Product Page" in prompt
```

**Step 2: Run test to verify it fails**

```bash
python -m pytest tests/test_claude_analyzer.py::test_build_analysis_prompt_with_observation_cites_evidence -v
```

Expected: `FAILED - TypeError: _build_analysis_prompt() got an unexpected keyword argument 'observation'`

**Step 3: Update `_build_analysis_prompt()` signature and body**

In `src/analyzers/claude_analyzer.py`, update the method signature (line 31) to add the `observation` parameter:

```python
    def _build_analysis_prompt(
        self,
        criteria: List[Dict[str, Any]],
        analysis_name: str,
        site_name: str,
        url: str,
        analysis_context: Optional[str] = None,
        observation: Optional[Dict[str, Any]] = None
    ) -> str:
```

Then, in the body of `_build_analysis_prompt`, add the observation section after the `context_section` block (after line 63) and before the `prompt = f"""...` line:

```python
        # Build observation section for pass 2
        observation_section = ""
        if observation:
            notable = observation.get("notable_states", [])
            notable_text = "\n".join(f"  - {s}" for s in notable) if notable else "  (none flagged)"
            observation_section = f"""
**VISUAL EVIDENCE (from observation pass)**

The following structured observation was made from the screenshots before scoring.
Use ONLY this evidence to support your scores. Do not infer what is not documented here.
If an observation is marked unclear or not visible, reflect that uncertainty in your score.

Notable states flagged during observation:
{notable_text}

Full observation data:
{json.dumps(observation, indent=2)}

**CRITICAL: Before scoring, review the notable_states list above.**
Every item in notable_states MUST be addressed:
- In the relevant criterion score (quote the observation as evidence), OR
- In key_findings if no criterion directly covers it.
Nothing in notable_states should be silently ignored.

"""
```

Also update the main `prompt` f-string to include `observation_section` before `criteria_text`. Replace the line:

```python
        prompt = f"""You are a competitive intelligence analyst specializing in e-commerce UX strategy.
{context_section}**IMPORTANT: Frame your analysis from a COMPETITIVE INTELLIGENCE perspective, not as recommendations to the competitor.**

Analyze the provided screenshot(s) of {site_name}'s page (URL: {url}) for {analysis_name} against the following criteria:
```

With:

```python
        # Determine source description for prompt
        source_desc = "the visual evidence documented below" if observation else f"the provided screenshot(s) of {site_name}'s page (URL: {url})"

        prompt = f"""You are a competitive intelligence analyst specializing in e-commerce UX strategy.
{context_section}{observation_section}**IMPORTANT: Frame your analysis from a COMPETITIVE INTELLIGENCE perspective, not as recommendations to the competitor.**

Analyze {source_desc} for {analysis_name} against the following criteria:
```

Also update the `criteria_scores` JSON template to include the `evidence` field. In the JSON template (around line 103), replace:

```python
  "criteria_scores": [
    {{
      "criterion_id": "<id>",
      "criterion_name": "<name>",
      "score": <number 0-10>,
      "observations": "<detailed observations>",
      "comparison_to_benchmarks": "<how it compares>",
      "competitive_status": "advantage|parity|vulnerability"
    }}
  ],
```

With:

```python
  "criteria_scores": [
    {{
      "criterion_id": "<id>",
      "criterion_name": "<name>",
      "score": <number 0-10>,
      "evidence": "<direct quote from the observation that supports this score, or 'Not documented in observation' if unclear>",
      "observations": "<detailed competitive analysis based on the evidence>",
      "comparison_to_benchmarks": "<how it compares>",
      "competitive_status": "advantage|parity|vulnerability"
    }}
  ],
```

**Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/test_claude_analyzer.py -v
```

Expected: All tests `PASSED`

**Step 5: Commit**

```bash
git add src/analyzers/claude_analyzer.py tests/test_claude_analyzer.py
git commit -m "feat: update _build_analysis_prompt to accept observation for pass 2 evidence citation"
```

---

### Task 6: Update `analyze_screenshots()` to use observation as input (text-only pass 2)

**Files:**
- Modify: `src/analyzers/claude_analyzer.py:227-353` (`analyze_screenshots`)

**Step 1: Update `analyze_screenshots()` signature and content prep**

In `src/analyzers/claude_analyzer.py`, update `analyze_screenshots()` to accept `observation`:

```python
    async def analyze_screenshots(
        self,
        screenshot_paths: List[str],
        criteria: List[Dict[str, Any]],
        analysis_name: str,
        site_name: str,
        url: str,
        analysis_context: Optional[str] = None,
        observation: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
```

Then update the prompt build call (around line 255):

```python
        prompt = self._build_analysis_prompt(
            criteria, analysis_name, site_name, url, analysis_context, observation
        )
```

Then update the content preparation (around line 258-274) to skip images when observation is provided:

```python
        if observation:
            # Pass 2: text-only — observation replaces images
            # Full output token budget goes to scoring
            content = [{"type": "text", "text": prompt}]
        else:
            # Single-pass or legacy: include images
            image_content = []
            for path in screenshot_paths:
                if not Path(path).exists():
                    continue
                image_data = self._load_image_as_base64(path)
                image_content.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": image_data
                    }
                })
            content = image_content + [{"type": "text", "text": prompt}]
```

**Step 2: Add test for text-only pass 2**

Add to `tests/test_claude_analyzer.py`:

```python
@pytest.mark.asyncio
async def test_analyze_screenshots_with_observation_sends_no_images(analyzer):
    """When observation is provided, analyze_screenshots sends text-only request."""
    observation = {
        "notable_states": ["Test state"],
        "desktop": {}, "mobile": {}
    }
    criteria = [{
        "id": "test", "name": "Test Criterion", "weight": 1.0,
        "description": "Test", "evaluation_points": [], "benchmarks": []
    }]
    mock_result = {
        "site_name": "example.com", "url": "https://example.com",
        "analysis_type": "Product Page", "overall_score": 7,
        "competitive_position": {"tier": "strong_contender", "positioning": "test", "key_differentiator": "test"},
        "criteria_scores": [{"criterion_id": "test", "criterion_name": "Test Criterion",
                             "score": 7, "evidence": "test", "observations": "test",
                             "comparison_to_benchmarks": "test", "competitive_status": "parity"}],
        "strengths": [], "competitive_advantages": [], "weaknesses": [],
        "exploitable_vulnerabilities": [], "unmet_user_needs": [], "key_findings": []
    }

    mock_response = MagicMock()
    mock_response.content = [MagicMock(text=json.dumps(mock_result))]

    captured_calls = []
    async def mock_create(**kwargs):
        captured_calls.append(kwargs)
        return mock_response

    with patch.object(analyzer.client.messages, "create", new=mock_create):
        result = await analyzer.analyze_screenshots(
            screenshot_paths=[],
            criteria=criteria,
            analysis_name="Product Page",
            site_name="example.com",
            url="https://example.com",
            observation=observation
        )

    assert result["success"] is True
    # Verify no image content was sent
    call_content = captured_calls[0]["messages"][0]["content"]
    assert all(item["type"] == "text" for item in call_content), \
        "Pass 2 with observation should send text-only content"
```

**Step 3: Run tests**

```bash
python -m pytest tests/test_claude_analyzer.py -v
```

Expected: All tests `PASSED`

**Step 4: Commit**

```bash
git add src/analyzers/claude_analyzer.py tests/test_claude_analyzer.py
git commit -m "feat: make analyze_screenshots text-only when observation provided (pass 2)"
```

---

### Task 7: Update `analyze_competitor_from_screenshots()` in `main.py` to orchestrate two passes

**Files:**
- Modify: `main.py:368-418` (`analyze_competitor_from_screenshots`)

**Step 1: Update `analyze_competitor_from_screenshots()`**

In `main.py`, replace the `analyze_competitor_from_screenshots()` method body:

```python
    async def analyze_competitor_from_screenshots(
        self,
        capture_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze a competitor using two-pass pipeline:
        - Pass 1: Observe screenshots → observation.json
        - Pass 2: Score against criteria using observation text (no images)

        If observation.json already exists for this competitor, pass 1 is skipped.
        """
        site_name = capture_data["site_name"]
        url = capture_data["url"]
        screenshot_paths = capture_data["screenshot_paths"]
        competitor_paths = capture_data.get("competitor_paths")

        self.console.print(f"\n[bold cyan]Analyzing:[/bold cyan] {site_name}")

        # Determine observation file path (if competitor_paths available)
        observation_path = None
        if competitor_paths:
            observation_path = Path(competitor_paths['root']) / "observation.json"

        try:
            # --- Pass 1: Observe ---
            observation = None

            if observation_path and observation_path.exists():
                self.console.print(f"  [dim]↻ Loading existing observation from {observation_path.name}[/dim]")
                with open(observation_path, 'r') as f:
                    observation = json.load(f)
            else:
                self.console.print(f"  [cyan]Pass 1: Observing screenshots...[/cyan]")
                observation_focus = list(getattr(self.analysis_type_config, 'observation_focus', []))

                observe_result = await self.claude_analyzer._observe_screenshots(
                    screenshot_paths=screenshot_paths,
                    analysis_name=self.analysis_type_config.name,
                    observation_focus=observation_focus,
                    site_name=site_name,
                    url=url
                )

                if not observe_result.get("success"):
                    self.console.print(f"  [red]Observation failed: {observe_result.get('error')}[/red]")
                    return {
                        "success": False,
                        "site_name": site_name,
                        "url": url,
                        "error": f"Pass 1 observation failed: {observe_result.get('error')}",
                        "screenshots": screenshot_paths
                    }

                observation = observe_result["observation"]

                # Save observation.json
                if observation_path:
                    observation_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(observation_path, 'w') as f:
                        json.dump(observation, f, indent=2)
                    self.console.print(f"  [green]✓ Observation saved ({len(observation.get('notable_states', []))} notable states)[/green]")
                else:
                    self.console.print(f"  [green]✓ Observation complete ({len(observation.get('notable_states', []))} notable states)[/green]")

            # Surface notable states to console
            notable = observation.get("notable_states", [])
            if notable:
                self.console.print(f"  [yellow]Notable states:[/yellow]")
                for state in notable:
                    self.console.print(f"    [yellow]• {state}[/yellow]")

            # --- Pass 2: Score ---
            self.console.print(f"  [cyan]Pass 2: Scoring against criteria...[/cyan]")

            criteria_dicts = [
                {
                    "id": c.id,
                    "name": c.name,
                    "weight": c.weight,
                    "description": c.description,
                    "evaluation_points": c.evaluation_points,
                    "benchmarks": c.benchmarks
                }
                for c in self.analysis_type_config.criteria
            ]

            analysis_result = await self.claude_analyzer.analyze_screenshots(
                screenshot_paths=screenshot_paths,
                criteria=criteria_dicts,
                analysis_name=self.analysis_type_config.name,
                site_name=site_name,
                url=url,
                analysis_context=self.analysis_type_config.analysis_context,
                observation=observation
            )

            if not analysis_result.get("success"):
                self.console.print(f"  [red]Scoring failed: {analysis_result.get('error')}[/red]")
                return {
                    "success": False,
                    "site_name": site_name,
                    "url": url,
                    "error": analysis_result.get("error"),
                    "screenshots": screenshot_paths
                }

            # Add observation reference to analysis result
            result_data = analysis_result["analysis"]
            result_data["observation_file"] = str(observation_path) if observation_path else None
            result_data["screenshots_analyzed"] = screenshot_paths
            result_data["model_used"] = self.claude_analyzer.model

            self.console.print(f"  [green]✓ Analysis complete[/green]")

            # Save analysis.json if competitor_paths available
            if competitor_paths:
                analysis_file_path = Path(competitor_paths['root']) / "analysis.json"
                with open(analysis_file_path, 'w') as f:
                    json.dump(result_data, f, indent=2)

            return {
                "success": True,
                "site_name": site_name,
                "url": url,
                "screenshot_paths": screenshot_paths,
                **result_data
            }

        except Exception as e:
            self.console.print(f"  [red]Error: {str(e)}[/red]")
            return {
                "success": False,
                "site_name": site_name,
                "url": url,
                "error": str(e)
            }
```

**Step 2: Add `import json` guard**

`json` is already imported in `main.py` (line 9). Confirm it's there, no change needed.

**Step 3: Manually test with one competitor using existing screenshots**

```bash
cd /home/matt99is/projects/UXMaturityAnalysis
python scripts/reanalyze_screenshots.py output/audits/<most-recent-product-audit-folder> 2>&1 | head -60
```

Expected output:
```
Pass 1: Observing screenshots...
✓ Observation saved (N notable states)
Notable states:
  • <any states found>
Pass 2: Scoring against criteria...
✓ Analysis complete
```

**Step 4: Commit**

```bash
git add main.py
git commit -m "feat: orchestrate two-pass analysis in analyze_competitor_from_screenshots"
```

---

### Task 8: Update `reanalyze_screenshots.py` skip logic

**Files:**
- Modify: `scripts/reanalyze_screenshots.py:139-165` (skip logic)
- Modify: `scripts/reanalyze_screenshots.py:234-240` (CLI args)

**Step 1: Add `--force-observe` and `--force` flags to CLI**

In `scripts/reanalyze_screenshots.py`, replace the `if __name__ == "__main__":` block:

```python
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("audit_folder", help="Path to the audit folder to reanalyze")
    parser.add_argument("--force-observe", action="store_true",
                        help="Re-run pass 1 (observation) even if observation.json exists")
    parser.add_argument("--force", action="store_true",
                        help="Re-run both passes even if analysis.json exists")
    args = parser.parse_args()

    asyncio.run(reanalyze_audit(args.audit_folder, force_observe=args.force_observe, force=args.force))
```

**Step 2: Update `reanalyze_audit()` signature and skip logic**

Change the function signature:

```python
async def reanalyze_audit(audit_path: str, force_observe: bool = False, force: bool = False):
```

Replace the skip logic block (around line 139-165):

```python
    # Check which competitors need (re)analysis
    needs_analysis = []
    existing_results = []

    for comp_data in competitors_data:
        comp_dir = audit_dir / comp_data['site_name']
        analysis_path = comp_dir / "analysis.json"
        observation_path = comp_dir / "observation.json"

        if not force and analysis_path.exists():
            # Load existing analysis (skip both passes)
            with open(analysis_path, 'r') as f:
                existing_analysis = json.load(f)

            if not existing_analysis.get('screenshot_metadata') and existing_analysis.get('screenshots_analyzed'):
                screenshot_metadata = []
                for screenshot_path in existing_analysis['screenshots_analyzed']:
                    screenshot_file = Path(screenshot_path)
                    viewport = 'mobile' if 'mobile' in screenshot_file.name else 'desktop'
                    screenshot_metadata.append({'filepath': str(screenshot_path), 'viewport': viewport})
                existing_analysis['screenshot_metadata'] = screenshot_metadata

            existing_results.append(existing_analysis)
            print(f"  [↻] {comp_data['site_name']}: Using existing analysis")
        else:
            # Mark whether observation pass can be skipped
            comp_data['_skip_observe'] = (not force_observe) and observation_path.exists()
            if comp_data['_skip_observe']:
                print(f"  [→] {comp_data['site_name']}: Will skip observation (observation.json exists)")
            needs_analysis.append(comp_data)
```

**Step 3: Pass `_skip_observe` flag through to orchestrator**

The `_skip_observe` flag is already handled by the updated `analyze_competitor_from_screenshots()` — it checks for `observation.json` on disk automatically. No extra plumbing needed. The `_skip_observe` field in `comp_data` is informational only (for the console print above).

**Step 4: Test the flags**

```bash
# Test --force-observe removes observation.json before run
python scripts/reanalyze_screenshots.py output/audits/<folder> --force-observe 2>&1 | head -20
# Test --force re-runs everything
python scripts/reanalyze_screenshots.py output/audits/<folder> --force 2>&1 | head -20
```

**Step 5: Commit**

```bash
git add scripts/reanalyze_screenshots.py
git commit -m "feat: add --force-observe and --force flags to reanalyze_screenshots.py"
```

---

### Task 9: Add Evidence tab and notable_states callout to HTML report

**Files:**
- Modify: `src/utils/html_report_generator.py` (find competitor profile template section)

**Step 1: Identify where competitor profiles are rendered**

```bash
grep -n "notable_states\|observation\|evidence\|criteria_scores\|competitor.*profile\|tab" \
  src/utils/html_report_generator.py | head -30
```

This will show the relevant template sections. Read the surrounding context for each match.

**Step 2: Add `notable_states` callout to competitor profile**

Find the section of `html_report_generator.py` that renders each competitor's criteria scores (search for `criteria_scores` in the template string). Before the criteria scores table/list, add a notable states callout:

```python
# In the Jinja2 template or f-string, add before criteria scores rendering:
notable_states_html = ""
if competitor_data.get("observation_file"):
    obs_path = Path(competitor_data["observation_file"])
    if obs_path.exists():
        with open(obs_path) as f:
            obs = json.load(f)
        notable = obs.get("notable_states", [])
        if notable:
            items = "".join(f"<li>{s}</li>" for s in notable)
            notable_states_html = f"""
<div class="notable-states-callout">
  <h4>⚠ Flagged anomalies (observation pass)</h4>
  <ul>{items}</ul>
</div>"""
```

**Step 3: Add CSS for the callout**

In the `<style>` block of the HTML template, add:

```css
.notable-states-callout {
  background: #fff3cd;
  border-left: 4px solid #ffc107;
  padding: 12px 16px;
  margin-bottom: 20px;
  border-radius: 4px;
}
.notable-states-callout h4 {
  margin: 0 0 8px 0;
  font-size: 14px;
  color: #856404;
}
.notable-states-callout ul {
  margin: 0;
  padding-left: 20px;
  color: #533f03;
  font-size: 13px;
}
```

**Step 4: Add `evidence` field to criteria score display**

In the criteria score rendering loop, after `observations`, add the `evidence` field:

```python
# In the criteria score loop, after observations display:
evidence = score.get("evidence", "")
if evidence and evidence != "Not documented in observation":
    evidence_html = f'<div class="evidence-citation"><strong>Evidence:</strong> {evidence}</div>'
```

With CSS:

```css
.evidence-citation {
  background: #f8f9fa;
  border-left: 3px solid #6c757d;
  padding: 6px 10px;
  margin-top: 6px;
  font-size: 12px;
  color: #495057;
  font-style: italic;
}
```

**Step 5: Test by regenerating a report**

```bash
python scripts/reanalyze_screenshots.py output/audits/<recent-folder>
# Open the generated HTML report in a browser and verify:
# - Notable states callout appears for competitors with observation.json
# - Evidence citations appear in criteria scores
```

**Step 6: Commit**

```bash
git add src/utils/html_report_generator.py
git commit -m "feat: add notable_states callout and evidence citations to HTML report"
```

---

### Task 10: Add flagged anomalies to markdown report

**Files:**
- Modify: `src/utils/report_generator.py`

**Step 1: Find where competitor sections are written in the markdown report**

```bash
grep -n "def.*report\|site_name\|criteria_scores\|## " src/utils/report_generator.py | head -30
```

**Step 2: Add "Flagged anomalies" section per competitor**

In `report_generator.py`, in the method that generates per-competitor markdown sections, add after the competitor header and before the criteria scores:

```python
# After competitor header (e.g., ## {site_name}), add:
notable = []
if result.get("observation_file"):
    obs_path = Path(result["observation_file"])
    if obs_path.exists():
        with open(obs_path) as f:
            obs = json.load(f)
        notable = obs.get("notable_states", [])

if notable:
    report += "\n**Flagged anomalies (observation pass):**\n"
    for state in notable:
        report += f"- {state}\n"
    report += "\n"
```

**Step 3: Test markdown output**

```bash
python scripts/reanalyze_screenshots.py output/audits/<recent-folder>
# Check the generated _comparison_report.md for "Flagged anomalies" sections
grep -A 5 "Flagged anomalies" output/audits/<recent-folder>/_comparison_report.md
```

**Step 4: Commit**

```bash
git add src/utils/report_generator.py
git commit -m "feat: add flagged anomalies section to markdown comparison report"
```

---

### Task 11: Run full end-to-end test

**Step 1: Run full analysis against one competitor with fresh screenshots**

```bash
python main.py --config competitors.json --analysis-type product_pages
```

Watch the console for:
- `Pass 1: Observing screenshots...`
- `✓ Observation saved (N notable states)`
- `Notable states:` list (if any found)
- `Pass 2: Scoring against criteria...`
- `✓ Analysis complete`

**Step 2: Verify output files exist**

```bash
ls output/audits/<new-folder>/<competitor>/
# Should show: screenshots/, observation.json, analysis.json
```

**Step 3: Verify `observation.json` contains notable_states**

```bash
python -c "
import json
from pathlib import Path
obs = json.load(open('output/audits/<new-folder>/<competitor>/observation.json'))
print('Notable states:', obs.get('notable_states', []))
"
```

**Step 4: Verify `analysis.json` contains evidence citations**

```bash
python -c "
import json
analysis = json.load(open('output/audits/<new-folder>/<competitor>/analysis.json'))
for score in analysis.get('criteria_scores', []):
    print(score['criterion_name'], '→', score.get('evidence', 'NO EVIDENCE')[:80])
"
```

**Step 5: Open HTML report and verify Evidence tab and notable_states callout**

```bash
open output/audits/<new-folder>/_comparison_report.html
```

**Step 6: Final commit**

```bash
git add -A
git commit -m "test: verify two-pass pipeline end-to-end with real competitor analysis"
```

---

## Rate Limit Notes

Pass 1 uses `max_tokens=3000`. Pass 2 uses `max_tokens=6000` (existing). Total per competitor: ~9000 tokens output. At 8000 tokens/min rate limit, one competitor takes ~70 seconds minimum. The existing `ANALYSIS_DELAY = 60` should be increased to **90 seconds** in both `main.py` and `reanalyze_screenshots.py` to account for the two-pass cost.

Update in both files:

```python
ANALYSIS_DELAY = 90  # Two-pass: ~9000 output tokens per competitor, 8000/min limit
```

Commit this alongside Task 7 or as a follow-up.
