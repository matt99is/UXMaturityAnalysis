"""
Claude API integration for UX analysis.

EXTENSIBILITY NOTE: This module uses templated prompts that can be
customized for different analysis types by injecting criteria from config.
"""

import os
import base64
from pathlib import Path
from typing import Dict, List, Any
import anthropic
from anthropic import Anthropic
import json
from PIL import Image
import io


class ClaudeUXAnalyzer:
    """
    Analyzes UX using Claude's vision and analysis capabilities.

    EXTENSIBILITY NOTE: This analyzer generates prompts dynamically based
    on criteria from config, making it work with any analysis type.
    """

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-5-20250929"):
        self.client = Anthropic(api_key=api_key)
        self.model = model

    def _build_analysis_prompt(
        self,
        criteria: List[Dict[str, Any]],
        analysis_name: str,
        site_name: str,
        url: str
    ) -> str:
        """
        Build structured analysis prompt from criteria.

        EXTENSIBILITY NOTE: This template-based approach allows criteria
        to be defined in config.yaml and automatically integrated into
        prompts for any page type analysis.
        """

        criteria_text = ""
        for i, criterion in enumerate(criteria, 1):
            criteria_text += f"\n{i}. **{criterion['name']}** (Weight: {criterion['weight']}/10)\n"
            criteria_text += f"   {criterion['description']}\n\n"
            criteria_text += f"   Evaluate:\n"
            for point in criterion['evaluation_points']:
                criteria_text += f"   - {point}\n"
            criteria_text += f"\n   Benchmarks:\n"
            for benchmark in criterion['benchmarks']:
                criteria_text += f"   - {benchmark}\n"
            criteria_text += "\n"

        prompt = f"""You are a competitive intelligence analyst specializing in e-commerce UX strategy. You have deep knowledge of Baymard Institute research and Nielsen Norman Group guidelines.

**IMPORTANT: Frame your analysis from a COMPETITIVE INTELLIGENCE perspective, not as recommendations to the competitor.**

Analyze the provided screenshot(s) of {site_name}'s page (URL: {url}) against the following criteria:

{criteria_text}

For each criterion, provide:
1. A score from 0-10 (where 10 is excellent, adhering to best practices)
2. Specific observations of what you see in the screenshot
3. How it compares to best practices and benchmarks mentioned
4. Competitive assessment: Is this a strength (threat to us) or weakness (opportunity for us)?

**Competitive Intelligence Focus:**
- Frame strengths as "competitive advantages" (threats we must counter)
- Frame weaknesses as "exploitable vulnerabilities" (opportunities to differentiate)
- Identify unmet user needs that neither this competitor nor market addresses
- Assess their competitive position relative to UX best practices

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
      "observations": "<detailed observations>",
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

Be specific and reference what you actually see in the screenshots. Think like a competitive strategist analyzing a rival. If something cannot be determined from the screenshot, note it as "Cannot verify from screenshot."
"""
        return prompt

    def _load_image_as_base64(self, image_path: str) -> str:
        """
        Load image, compress if needed, and convert to base64.

        Claude API has a 5MB limit per image. This method compresses
        large screenshots to stay under that limit while maintaining quality.
        """
        MAX_SIZE_BYTES = 5 * 1024 * 1024  # 5MB limit

        # Check original file size
        file_size = os.path.getsize(image_path)

        if file_size <= MAX_SIZE_BYTES:
            # File is small enough, use as-is
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode("utf-8")

        # File too large - compress it
        img = Image.open(image_path)

        # Convert RGBA to RGB if needed (for JPEG compression)
        if img.mode == 'RGBA':
            rgb_img = Image.new('RGB', img.size, (255, 255, 255))
            rgb_img.paste(img, mask=img.split()[3])  # Use alpha channel as mask
            img = rgb_img

        # Try progressively lower quality until under limit
        for quality in [85, 75, 65, 55, 45]:
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG', quality=quality, optimize=True)
            compressed_size = buffer.tell()

            if compressed_size <= MAX_SIZE_BYTES:
                buffer.seek(0)
                return base64.b64encode(buffer.read()).decode("utf-8")

        # If still too large, resize and try again
        # Reduce dimensions by 30% and compress
        new_width = int(img.width * 0.7)
        new_height = int(img.height * 0.7)
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=70, optimize=True)
        buffer.seek(0)
        return base64.b64encode(buffer.read()).decode("utf-8")

    async def analyze_screenshots(
        self,
        screenshot_paths: List[str],
        criteria: List[Dict[str, Any]],
        analysis_name: str,
        site_name: str,
        url: str
    ) -> Dict[str, Any]:
        """
        Analyze UX from screenshots using Claude.

        Args:
            screenshot_paths: Paths to screenshot files
            criteria: Analysis criteria from config
            analysis_name: Name of analysis type
            site_name: Competitor site name
            url: URL analyzed

        Returns:
            Structured analysis results

        EXTENSIBILITY NOTE: This method works with any criteria set,
        making it usable for different page types without modification.
        """

        # Build the analysis prompt
        prompt = self._build_analysis_prompt(criteria, analysis_name, site_name, url)

        # Prepare image content for API
        image_content = []
        for path in screenshot_paths:
            if not Path(path).exists():
                continue

            image_data = self._load_image_as_base64(path)
            image_content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": image_data
                }
            })

        # Add text prompt
        content = image_content + [{"type": "text", "text": prompt}]

        try:
            # Call Claude API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                messages=[{
                    "role": "user",
                    "content": content
                }]
            )

            # Extract response text
            response_text = response.content[0].text

            # Parse JSON from response
            # Claude might wrap JSON in markdown code blocks, so handle that
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

            analysis_result = json.loads(json_text)

            # Add metadata
            analysis_result["screenshots_analyzed"] = screenshot_paths
            analysis_result["model_used"] = self.model

            return {
                "success": True,
                "analysis": analysis_result
            }

        except json.JSONDecodeError as e:
            return {
                "success": False,
                "error": f"Failed to parse Claude response as JSON: {e}",
                "raw_response": response_text if 'response_text' in locals() else None
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def analyze_screenshots_sync(
        self,
        screenshot_paths: List[str],
        criteria: List[Dict[str, Any]],
        analysis_name: str,
        site_name: str,
        url: str
    ) -> Dict[str, Any]:
        """
        Synchronous version of analyze_screenshots for easier integration.

        EXTENSIBILITY NOTE: Both sync and async versions provided for
        flexibility in different application architectures.
        """
        import asyncio

        # If already in async context, use that; otherwise create new loop
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # We're already in an async context
                return asyncio.create_task(
                    self.analyze_screenshots(
                        screenshot_paths, criteria, analysis_name, site_name, url
                    )
                )
        except RuntimeError:
            pass

        # Create new event loop for sync call
        return asyncio.run(
            self.analyze_screenshots(
                screenshot_paths, criteria, analysis_name, site_name, url
            )
        )


# EXTENSIBILITY NOTE: Future enhancement for comparative analysis
class ComparativeAnalyzer(ClaudeUXAnalyzer):
    """
    Extends Claude analyzer to perform comparative analysis across competitors.

    Future capability: Analyze multiple competitors simultaneously and generate
    competitive positioning insights.
    """

    async def compare_competitors(
        self,
        competitor_analyses: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate comparative insights across multiple competitor analyses.

        Args:
            competitor_analyses: List of individual competitor analysis results

        Returns:
            Comparative analysis with rankings and insights

        EXTENSIBILITY NOTE: This will enable benchmarking against multiple
        competitors to identify best-in-class patterns.
        """
        # Future implementation
        raise NotImplementedError(
            "Comparative analysis across competitors will be implemented "
            "in future iteration."
        )
