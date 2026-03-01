"""
GLM API integration for UX analysis.

Uses OpenAI-compatible API format for GLM models (ZhipuAI).
Designed as a drop-in alternative to ClaudeUXAnalyzer for testing.
"""

import base64
import io
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from openai import AsyncOpenAI
from PIL import Image


class GLMUXAnalyzer:
    """
    Analyzes UX using GLM's vision capabilities via OpenAI-compatible API.

    This is a testing-focused alternative to ClaudeUXAnalyzer.
    Same interface, different backend.
    """

    def __init__(
        self,
        api_key: str = None,
        model: str = "glm-4-flash",
        base_url: str = None,
    ):
        self.api_key = api_key or os.getenv("GLM_API_KEY")
        self.model = model
        self.base_url = base_url or os.getenv("GLM_BASE_URL", "https://open.bigmodel.cn/api/paas/v4/")

        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
        )

    def _build_analysis_prompt(
        self,
        criteria: List[Dict[str, Any]],
        analysis_name: str,
        site_name: str,
        url: str,
        analysis_context: Optional[str] = None,
        observation: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Build structured analysis prompt - same as Claude analyzer."""

        criteria_text = ""
        for i, criterion in enumerate(criteria, 1):
            criteria_text += f"\n{i}. **{criterion['name']}** (Weight: {criterion['weight']}/10)\n"
            criteria_text += f"   {criterion['description']}\n\n"
            criteria_text += f"   Evaluate:\n"
            for point in criterion["evaluation_points"]:
                criteria_text += f"   - {point}\n"
            criteria_text += f"\n   Benchmarks:\n"
            for benchmark in criterion["benchmarks"]:
                criteria_text += f"   - {benchmark}\n"
            criteria_text += "\n"

        context_section = ""
        if analysis_context:
            context_section = f"\n{analysis_context}\n\n"

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

        source_desc = (
            "the visual evidence documented below"
            if observation
            else f"the provided screenshot(s) of {site_name}'s page (URL: {url})"
        )
        evidence_instruction = (
            "\n5. Cite direct evidence from the observation for every score" if observation else ""
        )

        prompt = f"""You are a competitive intelligence analyst specializing in e-commerce UX strategy.
{context_section}{observation_section}**IMPORTANT: Frame your analysis from a COMPETITIVE INTELLIGENCE perspective, not as recommendations to the competitor.**

Analyze {source_desc} for {analysis_name} against the following criteria:

{criteria_text}

For each criterion, provide:
1. A score from 0-10 (where 10 is excellent, adhering to best practices)
2. Specific observations from the provided evidence (be detailed and reference visible elements)
3. How it compares to best practices and benchmarks mentioned above
4. Competitive assessment: Is this a strength (threat to us) or weakness (opportunity for us)?
{evidence_instruction}

**CRITICAL SCORING GUIDANCE:**
- **Dark Patterns MUST be heavily penalized**: If you detect subscription pre-selected by default, pre-checked boxes committing to recurring payments, or hidden opt-outs, score that criterion 0-3/10 regardless of other factors
- **Visual Evidence Required**: For subscription options, explicitly state whether radio buttons/checkboxes appear selected in the screenshot
- **Look for UI State**: Filled circles (•) vs empty circles (○), checked boxes (☑) vs unchecked (☐), highlighted/active states
- **Default Selection**: If you cannot determine which option is selected by default, note this uncertainty

**Competitive Intelligence Focus:**
- Frame strengths as "competitive advantages" (threats we must counter)
- Frame weaknesses as "exploitable vulnerabilities" (opportunities to differentiate)
- **Flag dark patterns as severe vulnerabilities** - these damage trust and may violate regulations
- Assess the user experience quality based on the criteria and benchmarks provided
- Identify unmet user needs in the customer journey
- Evaluate their competitive position relative to market leaders

Return your analysis as a JSON object with this exact structure:
{{
  "site_name": "{site_name}",
  "url": "{url}",
  "analysis_type": "{analysis_name}",
  "overall_score": <number 0-10>,
  "competitive_position": {{
    "tier": "market_leader|strong_contender|vulnerable",
    "positioning": "<1-2 sentence assessment of their competitive UX position>",
    "key_differentiator": "<their primary UX advantage, if any>"
  }},
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
  "strengths": [
    "<competitive advantage 1 - what they do well that poses a threat>",
    "<competitive advantage 2>",
    "<competitive advantage 3>"
  ],
  "competitive_advantages": [
    "<feature or capability where they lead the market>",
    "<another competitive threat>"
  ],
  "weaknesses": [
    "<exploitable vulnerability 1 - gap we can target>",
    "<exploitable vulnerability 2>",
    "<exploitable vulnerability 3>"
  ],
  "exploitable_vulnerabilities": [
    {{
      "vulnerability": "<specific weakness>",
      "opportunity": "<how we could exploit this>",
      "user_impact": "<why users care about this gap>"
    }}
  ],
  "unmet_user_needs": [
    "<user need this competitor doesn't address>",
    "<gap in their value proposition>"
  ],
  "key_findings": [
    "<competitive insight 1>",
    "<competitive insight 2>",
    "<competitive insight 3>"
  ]
}}

**IMPORTANT JSON FORMATTING RULES:**
- All string values MUST properly escape special characters
- Use \\n for newlines within strings (not actual line breaks)
- Use \\" for quotes within strings
- Ensure all strings are properly terminated with closing quotes
- Ensure all objects and arrays are properly closed with }} or ]
- Do NOT include any text outside the JSON object
- Validate that your JSON is syntactically correct before responding

Be specific and reference what you actually see in the screenshots. Think like a competitive strategist analyzing a rival. If something cannot be determined from the screenshot, note it as "Cannot verify from screenshot."
"""
        return prompt

    def _build_observation_prompt(
        self, analysis_name: str, observation_focus: List[str], site_name: str, url: str
    ) -> str:
        """Build pass 1 observation prompt - same as Claude analyzer."""

        page_specific = ""
        if observation_focus:
            page_specific = "\n\nPAGE-SPECIFIC OBSERVATIONS\n"
            for item in observation_focus:
                page_specific += f"- {item}\n"

        prompt = f"""You are documenting the visual state of a webpage as evidence for a UX audit.
Describe only what you can see in the screenshots. Do not evaluate or recommend.
Be a precise witness. If something is unclear or not visible, say so explicitly.

Page: {site_name} - {analysis_name}
URL: {url}

For each section below, document what is visible in BOTH the desktop and mobile screenshots.
Be precise about interactive states: selected vs unselected, checked vs unchecked, highlighted vs default.
Quote visible text verbatim where relevant.

---

PRICING & OFFERS
- All prices shown, their format and visual prominence
- Any strikethrough or original prices alongside sale prices
- Subscription or recurring billing options - state explicitly which option appears selected or highlighted by default
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
- Reviews or ratings visible - star rating and review count if shown
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
    "<any unusual, deceptive, or noteworthy UI state observed - one item per entry>"
  ]
}}

The notable_states array is critical. Include every anomaly, dark pattern, unusual default,
or noteworthy state you observed - even if it seems minor. Each entry should be a plain
English sentence describing exactly what was seen.

IMPORTANT JSON FORMATTING RULES:
- All string values MUST properly escape special characters
- Use \\n+ for newlines within strings
- Use \\" for quotes within strings
- Do NOT include any text outside the JSON object
"""
        return prompt

    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """Extract and parse JSON from response - handles markdown fences."""
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
        return json.loads(json_text)

    def _load_image_as_base64(self, image_path: str) -> str:
        """Load image, convert to JPEG, encode as base64."""
        MAX_SIZE_BYTES = 5 * 1024 * 1024
        MAX_FILE_SIZE = int(MAX_SIZE_BYTES / 1.37)

        img = Image.open(image_path)

        if img.mode == "RGBA":
            rgb_img = Image.new("RGB", img.size, (255, 255, 255))
            rgb_img.paste(img, mask=img.split()[3])
            img = rgb_img
        elif img.mode != "RGB":
            img = img.convert("RGB")

        MAX_DIMENSION = 8000
        if img.width > MAX_DIMENSION or img.height > MAX_DIMENSION:
            scale_factor = min(MAX_DIMENSION / img.width, MAX_DIMENSION / img.height)
            new_width = int(img.width * scale_factor)
            new_height = int(img.height * scale_factor)
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        file_size = os.path.getsize(image_path)

        if file_size <= MAX_FILE_SIZE:
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=95, optimize=True)
            buffer.seek(0)
            return base64.b64encode(buffer.read()).decode("utf-8")

        for quality in [85, 75, 65, 55, 45]:
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=quality, optimize=True)
            compressed_size = buffer.tell()

            if compressed_size <= MAX_SIZE_BYTES:
                buffer.seek(0)
                return base64.b64encode(buffer.read()).decode("utf-8")

        new_width = int(img.width * 0.7)
        new_height = int(img.height * 0.7)
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=70, optimize=True)
        buffer.seek(0)
        return base64.b64encode(buffer.read()).decode("utf-8")

    def _load_image_as_url_data(self, image_path: str) -> str:
        """Load image and return as base64 data URL for OpenAI-compatible APIs."""
        b64_data = self._load_image_as_base64(image_path)
        return f"data:image/jpeg;base64,{b64_data}"

    async def _observe_screenshots(
        self,
        screenshot_paths: List[str],
        analysis_name: str,
        observation_focus: List[str],
        site_name: str,
        url: str,
    ) -> Dict[str, Any]:
        """Pass 1: Send screenshots and return structured visual observations."""

        prompt = self._build_observation_prompt(
            analysis_name,
            observation_focus,
            site_name,
            url,
        )

        # Build OpenAI-style message content
        content = []

        for path in screenshot_paths:
            if not Path(path).exists():
                continue

            image_url = self._load_image_as_url_data(path)
            content.append({
                "type": "image_url",
                "image_url": {"url": image_url}
            })

        content.append({"type": "text", "text": prompt})

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": content}],
                max_tokens=3000,
            )

            response_text = response.choices[0].message.content

            observation = self._parse_json_response(response_text)
            observation["screenshots_analyzed"] = screenshot_paths
            observation["model_used"] = self.model

            return {"success": True, "observation": observation}

        except json.JSONDecodeError as e:
            return {
                "success": False,
                "error": f"Failed to parse observation response as JSON: {e}",
                "raw_response": response_text if "response_text" in locals() else None,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def analyze_screenshots(
        self,
        screenshot_paths: List[str],
        criteria: List[Dict[str, Any]],
        analysis_name: str,
        site_name: str,
        url: str,
        analysis_context: Optional[str] = None,
        observation: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Analyze UX from screenshots using GLM.

        Same interface as ClaudeUXAnalyzer for drop-in compatibility.
        """

        prompt = self._build_analysis_prompt(
            criteria, analysis_name, site_name, url, analysis_context, observation
        )

        if observation:
            # Pass 2: text-only - observation replaces images
            content = [{"type": "text", "text": prompt}]
        else:
            # Single-pass: include images
            content = []
            for path in screenshot_paths:
                if not Path(path).exists():
                    continue
                image_url = self._load_image_as_url_data(path)
                content.append({
                    "type": "image_url",
                    "image_url": {"url": image_url}
                })
            content.append({"type": "text", "text": prompt})

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": content}],
                max_tokens=6000,
            )

            response_text = response.choices[0].message.content

            try:
                analysis_result = self._parse_json_response(response_text)
            except json.JSONDecodeError as json_error:
                debug_path = Path("output/debug_malformed_json")
                debug_path.mkdir(parents=True, exist_ok=True)
                timestamp = (
                    Path(screenshot_paths[0]).parent.parent.name if screenshot_paths else "unknown"
                )
                debug_file = debug_path / f"{site_name.replace(' ', '_')}_{timestamp}.txt"
                with open(debug_file, "w") as f:
                    f.write(f"=== MALFORMED JSON DEBUG ===\n")
                    f.write(f"Site: {site_name}\n")
                    f.write(f"Error: {json_error}\n\n")
                    f.write(f"=== RAW RESPONSE ===\n")
                    f.write(response_text)
                raise

            analysis_result["screenshots_analyzed"] = screenshot_paths
            analysis_result["model_used"] = self.model

            return {"success": True, "analysis": analysis_result}

        except json.JSONDecodeError as e:
            error_pos = getattr(e, "pos", None)
            pos_hint = f" at position {error_pos}" if error_pos is not None else ""
            error_msg = (
                f"Failed to parse GLM response as JSON: {e}{pos_hint}. "
                f"Raw response saved to output/debug_malformed_json/ for inspection."
            )
            return {
                "success": False,
                "error": error_msg,
                "raw_response": response_text if "response_text" in locals() else None,
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def analyze_screenshots_sync(
        self,
        screenshot_paths: List[str],
        criteria: List[Dict[str, Any]],
        analysis_name: str,
        site_name: str,
        url: str,
        analysis_context: Optional[str] = None,
        observation: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Synchronous version for easier integration."""
        import asyncio

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                return asyncio.create_task(
                    self.analyze_screenshots(
                        screenshot_paths,
                        criteria,
                        analysis_name,
                        site_name,
                        url,
                        analysis_context,
                        observation,
                    )
                )
        except RuntimeError:
            pass

        return asyncio.run(
            self.analyze_screenshots(
                screenshot_paths,
                criteria,
                analysis_name,
                site_name,
                url,
                analysis_context,
                observation,
            )
        )
