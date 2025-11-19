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

        prompt = f"""You are a UX expert specializing in e-commerce conversion optimization. You have deep knowledge of Baymard Institute research and Nielsen Norman Group guidelines.

Analyze the provided screenshot(s) of {site_name}'s basket page (URL: {url}) against the following criteria:

{criteria_text}

For each criterion, provide:
1. A score from 0-10 (where 10 is excellent, adhering to best practices)
2. Specific observations of what you see in the screenshot
3. How it compares to best practices and benchmarks mentioned

Then provide:
- Overall UX score (weighted average)
- Top 3 strengths
- Top 3 weaknesses
- 5 actionable recommendations prioritized by impact

Return your analysis as a JSON object with this exact structure:
{{
  "site_name": "{site_name}",
  "url": "{url}",
  "analysis_type": "{analysis_name}",
  "overall_score": <number 0-10>,
  "criteria_scores": [
    {{
      "criterion_id": "<id>",
      "criterion_name": "<name>",
      "score": <number 0-10>,
      "observations": "<detailed observations>",
      "comparison_to_benchmarks": "<how it compares>"
    }}
  ],
  "strengths": [
    "<strength 1>",
    "<strength 2>",
    "<strength 3>"
  ],
  "weaknesses": [
    "<weakness 1>",
    "<weakness 2>",
    "<weakness 3>"
  ],
  "key_findings": [
    "<finding 1>",
    "<finding 2>",
    "<finding 3>"
  ],
  "actionable_recommendations": [
    {{
      "priority": "high|medium|low",
      "recommendation": "<actionable recommendation>",
      "expected_impact": "<impact description>",
      "affected_criteria": ["<criterion_id>"]
    }}
  ]
}}

Be specific and reference what you actually see in the screenshots. If something cannot be determined from the screenshot, note it as "Cannot verify from screenshot."
"""
        return prompt

    def _load_image_as_base64(self, image_path: str) -> str:
        """Load image and convert to base64."""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

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
