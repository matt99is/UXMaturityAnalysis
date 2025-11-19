"""
Report generation for UX analysis results.

EXTENSIBILITY NOTE: Report templates can be customized for different
analysis types and output formats.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any


class ReportGenerator:
    """
    Generates analysis reports in multiple formats.

    EXTENSIBILITY NOTE: Easily add new output formats (HTML, PDF, etc.)
    by adding new methods following the same pattern.
    """

    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def save_json_report(
        self,
        analysis_results: List[Dict[str, Any]],
        filename: str = None
    ) -> str:
        """
        Save analysis results as JSON.

        Args:
            analysis_results: List of competitor analysis results
            filename: Optional custom filename

        Returns:
            Path to saved file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ux_analysis_{timestamp}.json"

        filepath = self.output_dir / filename

        output_data = {
            "generated_at": datetime.now().isoformat(),
            "total_competitors_analyzed": len(analysis_results),
            "analyses": analysis_results
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        return str(filepath)

    def generate_markdown_report(
        self,
        analysis_results: List[Dict[str, Any]],
        filename: str = None
    ) -> str:
        """
        Generate comprehensive markdown report.

        Args:
            analysis_results: List of competitor analysis results
            filename: Optional custom filename

        Returns:
            Path to saved file

        EXTENSIBILITY NOTE: Markdown template can be customized
        for different analysis types by modifying the structure below.
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ux_analysis_report_{timestamp}.md"

        filepath = self.output_dir / filename

        markdown = self._build_markdown_content(analysis_results)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(markdown)

        return str(filepath)

    def _build_markdown_content(self, analysis_results: List[Dict[str, Any]]) -> str:
        """Build markdown report content."""

        md = "# E-commerce Basket Page UX Analysis\n\n"
        md += f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        md += f"**Competitors Analyzed:** {len(analysis_results)}\n\n"

        md += "---\n\n"

        # Executive Summary
        md += "## Executive Summary\n\n"
        md += self._generate_executive_summary(analysis_results)
        md += "\n\n---\n\n"

        # Competitor Rankings
        md += "## Overall Rankings\n\n"
        md += self._generate_rankings_table(analysis_results)
        md += "\n\n---\n\n"

        # Individual Competitor Analysis
        md += "## Detailed Competitor Analysis\n\n"
        for i, result in enumerate(analysis_results, 1):
            if not result.get("success"):
                md += f"### {i}. {result.get('site_name', 'Unknown')} - Analysis Failed\n\n"
                md += f"**Error:** {result.get('error', 'Unknown error')}\n\n"
                continue

            analysis = result.get("analysis", {})
            md += self._generate_competitor_section(analysis, i)
            md += "\n\n---\n\n"

        # Comparative Insights
        md += "## Comparative Insights\n\n"
        md += self._generate_comparative_insights(analysis_results)

        # Appendix
        md += "\n\n---\n\n"
        md += "## Appendix: Methodology\n\n"
        md += self._generate_methodology_section(analysis_results)

        return md

    def _generate_executive_summary(self, results: List[Dict[str, Any]]) -> str:
        """Generate executive summary section."""
        successful = [r for r in results if r.get("success")]

        if not successful:
            return "No successful analyses to summarize.\n"

        scores = [r["analysis"]["overall_score"] for r in successful]
        avg_score = sum(scores) / len(scores)

        md = f"Analysis of {len(successful)} competitor basket pages reveals:\n\n"
        md += f"- **Average UX Score:** {avg_score:.1f}/10\n"
        md += f"- **Highest Score:** {max(scores):.1f}/10 ({self._get_site_name(successful[scores.index(max(scores))])})\n"
        md += f"- **Lowest Score:** {min(scores):.1f}/10 ({self._get_site_name(successful[scores.index(min(scores))])})\n\n"

        return md

    def _generate_rankings_table(self, results: List[Dict[str, Any]]) -> str:
        """Generate rankings table."""
        successful = [r for r in results if r.get("success")]

        if not successful:
            return "No successful analyses to rank.\n"

        # Sort by overall score
        sorted_results = sorted(
            successful,
            key=lambda x: x["analysis"]["overall_score"],
            reverse=True
        )

        md = "| Rank | Competitor | Overall Score | Key Strength |\n"
        md += "|------|------------|---------------|---------------|\n"

        for i, result in enumerate(sorted_results, 1):
            analysis = result["analysis"]
            site_name = analysis.get("site_name", "Unknown")
            score = analysis.get("overall_score", 0)
            strength = analysis.get("strengths", ["N/A"])[0][:60]

            md += f"| {i} | {site_name} | {score:.1f}/10 | {strength} |\n"

        return md

    def _generate_competitor_section(self, analysis: Dict[str, Any], number: int) -> str:
        """Generate detailed competitor analysis section."""
        site_name = analysis.get("site_name", "Unknown")
        url = analysis.get("url", "")
        overall_score = analysis.get("overall_score", 0)

        md = f"### {number}. {site_name}\n\n"
        md += f"**URL:** {url}\n\n"
        md += f"**Overall UX Score:** {overall_score:.1f}/10\n\n"

        # Criteria Scores
        md += "#### Detailed Criteria Scores\n\n"
        md += "| Criterion | Score | Observations |\n"
        md += "|-----------|-------|-------------|\n"

        for criterion in analysis.get("criteria_scores", []):
            name = criterion.get("criterion_name", "Unknown")
            score = criterion.get("score", 0)
            obs = criterion.get("observations", "")[:100] + "..."

            md += f"| {name} | {score}/10 | {obs} |\n"

        md += "\n"

        # Strengths
        md += "#### Strengths\n\n"
        for strength in analysis.get("strengths", []):
            md += f"- {strength}\n"

        md += "\n"

        # Weaknesses
        md += "#### Weaknesses\n\n"
        for weakness in analysis.get("weaknesses", []):
            md += f"- {weakness}\n"

        md += "\n"

        # Recommendations
        md += "#### Actionable Recommendations\n\n"
        for rec in analysis.get("actionable_recommendations", []):
            priority = rec.get("priority", "medium").upper()
            recommendation = rec.get("recommendation", "")
            impact = rec.get("expected_impact", "")

            md += f"**[{priority}]** {recommendation}\n"
            md += f"- *Expected Impact:* {impact}\n\n"

        return md

    def _generate_comparative_insights(self, results: List[Dict[str, Any]]) -> str:
        """Generate comparative insights across competitors."""
        successful = [r for r in results if r.get("success")]

        if len(successful) < 2:
            return "Insufficient data for comparative insights (need at least 2 successful analyses).\n"

        md = "### Best Practices Observed\n\n"

        # Find highest scoring criteria across all competitors
        all_criteria_scores = {}
        for result in successful:
            for criterion in result["analysis"].get("criteria_scores", []):
                crit_id = criterion.get("criterion_id", "")
                crit_name = criterion.get("criterion_name", "")
                score = criterion.get("score", 0)

                if crit_id not in all_criteria_scores:
                    all_criteria_scores[crit_id] = {
                        "name": crit_name,
                        "scores": []
                    }
                all_criteria_scores[crit_id]["scores"].append(score)

        # Calculate averages
        for crit_id, data in all_criteria_scores.items():
            avg = sum(data["scores"]) / len(data["scores"])
            data["average"] = avg

        # Sort by average score
        sorted_criteria = sorted(
            all_criteria_scores.items(),
            key=lambda x: x[1]["average"],
            reverse=True
        )

        md += "**Strongest Areas (across all competitors):**\n\n"
        for crit_id, data in sorted_criteria[:3]:
            md += f"- **{data['name']}**: Average score {data['average']:.1f}/10\n"

        md += "\n**Weakest Areas (opportunities for improvement):**\n\n"
        for crit_id, data in sorted_criteria[-3:]:
            md += f"- **{data['name']}**: Average score {data['average']:.1f}/10\n"

        return md

    def _generate_methodology_section(self, results: List[Dict[str, Any]]) -> str:
        """Generate methodology appendix."""
        md = "### Analysis Methodology\n\n"
        md += "This analysis was conducted using:\n\n"
        md += "- **Browser Automation:** Playwright for screenshot capture\n"
        md += "- **AI Analysis:** Claude (Anthropic) for UX evaluation\n"
        md += "- **Benchmarks:** Baymard Institute and Nielsen Norman Group research\n\n"

        if results and results[0].get("success"):
            analysis = results[0].get("analysis", {})
            model = analysis.get("model_used", "Unknown")
            md += f"- **AI Model:** {model}\n"

        md += "\n"
        md += "Each competitor's basket page was evaluated against 10 key UX criteria, "
        md += "weighted by importance for conversion optimization.\n"

        return md

    def _get_site_name(self, result: Dict[str, Any]) -> str:
        """Extract site name from result."""
        return result.get("analysis", {}).get("site_name", "Unknown")


# EXTENSIBILITY NOTE: Future enhancement for additional report formats
class HTMLReportGenerator(ReportGenerator):
    """
    HTML report generator with interactive features.

    Future capability: Generate interactive HTML reports with
    charts, screenshots embedded, and filterable criteria.
    """

    def generate_html_report(self, analysis_results: List[Dict[str, Any]]) -> str:
        """Generate interactive HTML report."""
        raise NotImplementedError(
            "HTML report generation will be implemented in future iteration."
        )
