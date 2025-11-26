"""
Report generation for UX analysis results.

EXTENSIBILITY NOTE: Report templates can be customized for different
analysis types and output formats.

Updated to support hierarchical audit organization:
- Individual competitor analysis files
- Audit-level comparison reports
- Audit summary metadata
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional


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

    def save_competitor_analysis(
        self,
        competitor_analysis: Dict[str, Any],
        filepath: Path
    ) -> str:
        """
        Save an individual competitor's analysis to their folder.

        Args:
            competitor_analysis: Single competitor analysis dict
            filepath: Full path where to save analysis.json

        Returns:
            Path to saved file
        """
        # Ensure parent directory exists
        filepath.parent.mkdir(parents=True, exist_ok=True)

        # Save just the analysis data (not wrapped)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(competitor_analysis, f, indent=2, ensure_ascii=False)

        return str(filepath)

    def save_audit_summary(
        self,
        summary_data: Dict[str, Any],
        filepath: Path
    ) -> str:
        """
        Save audit-level summary metadata.

        Args:
            summary_data: Audit summary dict
            filepath: Full path where to save _audit_summary.json

        Returns:
            Path to saved file
        """
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, indent=2, ensure_ascii=False)

        return str(filepath)

    def generate_markdown_report(
        self,
        analysis_results: List[Dict[str, Any]],
        filename: str = None,
        filepath: Optional[Path] = None
    ) -> str:
        """
        Generate comprehensive markdown report.

        Args:
            analysis_results: List of competitor analysis results
            filename: Optional custom filename (used if filepath not provided)
            filepath: Optional full path (overrides filename)

        Returns:
            Path to saved file

        EXTENSIBILITY NOTE: Markdown template can be customized
        for different analysis types by modifying the structure below.
        """
        if filepath is None:
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"ux_analysis_report_{timestamp}.md"
            filepath = self.output_dir / filename

        markdown = self._build_markdown_content(analysis_results)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(markdown)

        return str(filepath)

    def _build_markdown_content(self, analysis_results: List[Dict[str, Any]]) -> str:
        """Build markdown report content with competitive intelligence focus."""

        md = "# UX Maturity Report\n\n"
        md += f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        md += f"**Competitors Analyzed:** {len(analysis_results)}\n\n"

        md += "---\n\n"

        # Market Landscape Analysis
        md += "## Market Landscape Analysis\n\n"
        md += self._generate_market_landscape(analysis_results)
        md += "\n\n---\n\n"

        # Feature Adoption Heatmap
        md += "## Feature Adoption Heatmap\n\n"
        md += self._generate_feature_heatmap(analysis_results)
        md += "\n\n---\n\n"

        # Strategic Insights
        md += "## Strategic Insights\n\n"
        md += self._generate_strategic_insights(analysis_results)
        md += "\n\n---\n\n"

        # Individual Competitor Profiles
        md += "## Competitor Profiles\n\n"
        for i, result in enumerate(analysis_results, 1):
            if not result.get("success"):
                md += f"### {i}. {result.get('site_name', 'Unknown')} - Analysis Failed\n\n"
                md += f"**Error:** {result.get('error', 'Unknown error')}\n\n"
                continue

            # Data is now flattened at the top level
            md += self._generate_competitive_profile(result, i)
            md += "\n\n---\n\n"

        # Competitive Positioning Map
        md += "## Competitive Positioning Map\n\n"
        md += self._generate_positioning_map(analysis_results)
        md += "\n\n---\n\n"

        # Strategic Recommendations
        md += "## Strategic Recommendations\n\n"
        md += self._generate_strategic_recommendations(analysis_results)

        # Appendix
        md += "\n\n---\n\n"
        md += "## Appendix: Methodology\n\n"
        md += self._generate_methodology_section(analysis_results)

        return md

    def _generate_market_landscape(self, results: List[Dict[str, Any]]) -> str:
        """Generate market landscape analysis with feature adoption and competitive clusters."""
        successful = [r for r in results if r.get("success")]

        if not successful:
            return "No successful analyses to summarize.\n"

        scores = [r.get("overall_score", 0) for r in successful]
        avg_score = sum(scores) / len(scores)

        md = f"### Overview\n\n"
        md += f"Analyzed {len(successful)} competitors to map the competitive landscape and identify strategic opportunities.\n\n"
        md += f"**Market UX Maturity:** {avg_score:.1f}/10\n\n"

        # Feature adoption rates
        md += "### Feature Adoption Analysis\n\n"
        all_criteria_scores = {}
        for result in successful:
            for criterion in result.get("criteria_scores", []):
                crit_id = criterion.get("criterion_id", "")
                crit_name = criterion.get("criterion_name", "")
                score = criterion.get("score", 0)

                if crit_id not in all_criteria_scores:
                    all_criteria_scores[crit_id] = {
                        "name": crit_name,
                        "scores": []
                    }
                all_criteria_scores[crit_id]["scores"].append(score)

        # Calculate adoption rates
        for crit_id, data in all_criteria_scores.items():
            avg = sum(data["scores"]) / len(data["scores"])
            data["average"] = avg
            # Adoption rate: % of competitors scoring 7+
            high_performers = [s for s in data["scores"] if s >= 7]
            data["adoption_rate"] = (len(high_performers) / len(data["scores"])) * 100

        sorted_by_adoption = sorted(
            all_criteria_scores.items(),
            key=lambda x: x[1]["adoption_rate"],
            reverse=True
        )

        md += "| Feature Category | Adoption Rate | Avg Score | Market Status |\n"
        md += "|-----------------|---------------|-----------|---------------|\n"

        for crit_id, data in sorted_by_adoption:
            adoption = data["adoption_rate"]
            avg = data["average"]
            if adoption >= 75:
                status = "Industry Standard"
            elif adoption >= 50:
                status = "Widely Adopted"
            elif adoption >= 25:
                status = "Emerging Practice"
            else:
                status = "Differentiator"

            md += f"| {data['name']} | {adoption:.0f}% | {avg:.1f}/10 | {status} |\n"

        # Competitive clusters
        md += "\n\n### Competitive Clusters\n\n"

        # Leaders (7.5+), Contenders (6-7.5), Laggards (<6)
        leaders = [r for r in successful if r.get("overall_score", 0) >= 7.5]
        contenders = [r for r in successful if 6 <= r.get("overall_score", 0) < 7.5]
        laggards = [r for r in successful if r.get("overall_score", 0) < 6]

        if leaders:
            md += f"**Leaders (7.5+):** {', '.join([self._get_site_name(r) for r in leaders])}\n"
            md += f"- Setting industry benchmarks with superior UX execution\n\n"

        if contenders:
            md += f"**Contenders (6.0-7.5):** {', '.join([self._get_site_name(r) for r in contenders])}\n"
            md += f"- Solid execution with room for strategic improvements\n\n"

        if laggards:
            md += f"**Laggards (<6.0):** {', '.join([self._get_site_name(r) for r in laggards])}\n"
            md += f"- Significant UX gaps present exploitable opportunities\n"

        return md

    def _generate_feature_heatmap(self, results: List[Dict[str, Any]]) -> str:
        """Generate feature adoption heatmap with emoji indicators."""
        successful = [r for r in results if r.get("success")]

        if not successful:
            return "No successful analyses to rank.\n"

        # Build criteria matrix
        all_criteria = {}
        for result in successful:
            for criterion in result.get("criteria_scores", []):
                crit_id = criterion.get("criterion_id", "")
                crit_name = criterion.get("criterion_name", "")
                if crit_id not in all_criteria:
                    all_criteria[crit_id] = {"name": crit_name, "competitor_scores": {}}

        # Populate scores for each competitor
        for result in successful:
            site_name = self._get_site_name(result)
            for criterion in result.get("criteria_scores", []):
                crit_id = criterion.get("criterion_id", "")
                score = criterion.get("score", 0)
                if crit_id in all_criteria:
                    all_criteria[crit_id]["competitor_scores"][site_name] = score

        # Generate heatmap table
        competitor_names = [self._get_site_name(r) for r in successful]

        md = "Visual representation of UX feature implementation across competitors:\n\n"
        md += "Legend: ✅ Strong (8-10) | ⚠️ Moderate (5-7) | ❌ Weak (0-4)\n\n"

        md += "| Feature | " + " | ".join(competitor_names) + " |\n"
        md += "|---------|" + "|".join(["---"] * len(competitor_names)) + "|\n"

        for crit_id, data in all_criteria.items():
            row = f"| {data['name']} |"
            for comp_name in competitor_names:
                score = data["competitor_scores"].get(comp_name, 0)
                if score >= 8:
                    emoji = " ✅ "
                elif score >= 5:
                    emoji = " ⚠️ "
                else:
                    emoji = " ❌ "
                row += f" {emoji} {score:.1f} |"
            md += row + "\n"

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
            for criterion in result.get("criteria_scores", []):
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

    def _generate_strategic_insights(self, results: List[Dict[str, Any]]) -> str:
        """Generate strategic insights including white space opportunities and market trends."""
        successful = [r for r in results if r.get("success")]

        if len(successful) < 2:
            return "Insufficient data for strategic insights (need at least 2 successful analyses).\n"

        # Calculate criteria averages
        all_criteria_scores = {}
        for result in successful:
            for criterion in result.get("criteria_scores", []):
                crit_id = criterion.get("criterion_id", "")
                crit_name = criterion.get("criterion_name", "")
                score = criterion.get("score", 0)

                if crit_id not in all_criteria_scores:
                    all_criteria_scores[crit_id] = {
                        "name": crit_name,
                        "scores": []
                    }
                all_criteria_scores[crit_id]["scores"].append(score)

        for crit_id, data in all_criteria_scores.items():
            avg = sum(data["scores"]) / len(data["scores"])
            data["average"] = avg
            data["max_score"] = max(data["scores"])

        sorted_criteria = sorted(
            all_criteria_scores.items(),
            key=lambda x: x[1]["average"],
            reverse=True
        )

        md = "### White Space Opportunities\n\n"
        md += "Areas where the market is underperforming, representing opportunities for differentiation:\n\n"

        # Find low-performing criteria (avg < 6)
        weak_areas = [(cid, data) for cid, data in sorted_criteria if data["average"] < 6]
        if weak_areas:
            for crit_id, data in weak_areas[:3]:
                md += f"- **{data['name']}** (market avg: {data['average']:.1f}/10)\n"
                md += f"  - Industry-wide weakness - opportunity to stand out\n"
                md += f"  - Even market leader only scores {data['max_score']:.1f}/10\n\n"
        else:
            md += "No significant white space identified - market is mature.\n\n"

        md += "### Best-in-Class Reference\n\n"
        md += "Market leaders by specific criteria:\n\n"

        # Find best performer for each criterion
        for crit_id, data in sorted_criteria[:5]:
            best_score = 0
            best_competitor = "Unknown"
            for result in successful:
                for criterion in result.get("criteria_scores", []):
                    if criterion.get("criterion_id") == crit_id:
                        score = criterion.get("score", 0)
                        if score > best_score:
                            best_score = score
                            best_competitor = self._get_site_name(result)

            md += f"- **{data['name']}**: {best_competitor} ({best_score:.1f}/10)\n"

        md += "\n### Market Trends\n\n"

        # Identify trends based on score distribution
        high_variance_criteria = []
        for crit_id, data in all_criteria_scores.items():
            scores = data["scores"]
            if len(scores) > 1:
                variance = sum((x - data["average"]) ** 2 for x in scores) / len(scores)
                if variance > 4:  # High variance threshold
                    high_variance_criteria.append((crit_id, data, variance))

        if high_variance_criteria:
            md += "**Fragmented Features** (high variance = opportunity for standardization):\n\n"
            for crit_id, data, variance in sorted(high_variance_criteria, key=lambda x: x[2], reverse=True)[:3]:
                md += f"- **{data['name']}**: Wide implementation gap (variance: {variance:.1f})\n"
                md += f"  - Some competitors excel while others underperform\n\n"
        else:
            md += "Market shows consistent feature implementation across competitors.\n\n"

        return md

    def _generate_competitive_profile(self, analysis: Dict[str, Any], number: int) -> str:
        """Generate competitive profile with advantages and vulnerabilities."""
        site_name = analysis.get("site_name", "Unknown")
        url = analysis.get("url", "")
        overall_score = analysis.get("overall_score", 0)

        md = f"### {number}. {site_name}\n\n"
        md += f"**URL:** {url}\n\n"
        md += f"**Competitive Score:** {overall_score:.1f}/10\n\n"

        # Competitive position
        if overall_score >= 7.5:
            position = "Market Leader"
            position_desc = "Setting benchmarks that others must match"
        elif overall_score >= 6:
            position = "Strong Contender"
            position_desc = "Competitive but with exploitable gaps"
        else:
            position = "Vulnerable Position"
            position_desc = "Significant weaknesses to exploit"

        md += f"**Position:** {position} - {position_desc}\n\n"

        # Criteria Scores
        md += "#### Feature Performance\n\n"
        md += "| Criterion | Score | Competitive Status |\n"
        md += "|-----------|-------|-------------------|\n"

        for criterion in analysis.get("criteria_scores", []):
            name = criterion.get("criterion_name", "Unknown")
            score = criterion.get("score", 0)

            if score >= 8:
                status = "🔥 Competitive Advantage"
            elif score >= 6:
                status = "✓ Market Parity"
            else:
                status = "⚠️ Exploitable Weakness"

            md += f"| {name} | {score}/10 | {status} |\n"

        md += "\n"

        # Competitive Advantages
        md += "#### Competitive Advantages\n\n"
        strengths = analysis.get("strengths", [])
        if strengths:
            for strength in strengths[:3]:
                md += f"- **Threat:** {strength}\n"
        else:
            md += "No significant competitive advantages identified.\n"

        md += "\n"

        # Exploitable Vulnerabilities
        md += "#### Exploitable Vulnerabilities\n\n"
        weaknesses = analysis.get("weaknesses", [])
        if weaknesses:
            for weakness in weaknesses[:3]:
                md += f"- **Opportunity:** {weakness}\n"
        else:
            md += "No major vulnerabilities identified.\n"

        md += "\n"

        return md

    def _generate_positioning_map(self, results: List[Dict[str, Any]]) -> str:
        """Generate competitive positioning visualization."""
        successful = [r for r in results if r.get("success")]

        if len(successful) < 2:
            return "Insufficient data for positioning map (need at least 2 successful analyses).\n"

        md = "Visual representation of competitive positioning:\n\n"

        # Sort by overall score
        sorted_results = sorted(
            successful,
            key=lambda x: x.get("overall_score", 0),
            reverse=True
        )

        md += "```\n"
        md += "UX MATURITY SPECTRUM\n"
        md += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

        for result in sorted_results:
            site_name = self._get_site_name(result)
            score = result.get("overall_score", 0)

            # Create visual bar
            filled = int(score)
            empty = 10 - filled
            bar = "█" * filled + "░" * empty

            md += f"{site_name:<20} [{bar}] {score:.1f}/10\n"

        md += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        md += "```\n\n"

        # Score distribution
        scores = [r.get("overall_score", 0) for r in successful]
        avg = sum(scores) / len(scores)
        md += f"**Market Average:** {avg:.1f}/10\n"
        md += f"**Score Spread:** {max(scores) - min(scores):.1f} points\n\n"

        if max(scores) - min(scores) > 2:
            md += "**Insight:** Wide performance gap indicates opportunity to leapfrog competitors.\n"
        else:
            md += "**Insight:** Tight competition - small improvements can shift market position.\n"

        return md

    def _generate_strategic_recommendations(self, results: List[Dict[str, Any]]) -> str:
        """Generate strategic recommendations focused on competitive positioning."""
        successful = [r for r in results if r.get("success")]

        if not successful:
            return "No successful analyses to base recommendations on.\n"

        # Calculate criteria averages
        all_criteria_scores = {}
        for result in successful:
            for criterion in result.get("criteria_scores", []):
                crit_id = criterion.get("criterion_id", "")
                crit_name = criterion.get("criterion_name", "")
                score = criterion.get("score", 0)

                if crit_id not in all_criteria_scores:
                    all_criteria_scores[crit_id] = {
                        "name": crit_name,
                        "scores": []
                    }
                all_criteria_scores[crit_id]["scores"].append(score)

        for crit_id, data in all_criteria_scores.items():
            avg = sum(data["scores"]) / len(data["scores"])
            data["average"] = avg
            high_performers = [s for s in data["scores"] if s >= 7]
            data["adoption_rate"] = (len(high_performers) / len(data["scores"])) * 100

        sorted_criteria = sorted(
            all_criteria_scores.items(),
            key=lambda x: x[1]["average"],
            reverse=True
        )

        md = "### Table Stakes (Must-Have Features)\n\n"
        md += "Features where market leaders excel - failure to match these creates competitive disadvantage:\n\n"

        md += "| Feature | Market Performance | Strategic Priority |\n"
        md += "|---------|-------------------|-------------------|\n"

        # Table stakes: High adoption (>50%) and high avg score (>7)
        for crit_id, data in sorted_criteria:
            if data["adoption_rate"] > 50 and data["average"] >= 7:
                md += f"| {data['name']} | {data['average']:.1f}/10 ({data['adoption_rate']:.0f}% adoption) | Critical |\n"

        md += "\n### Differentiation Opportunities\n\n"
        md += "Features where the market is weak - opportunities to stand out:\n\n"

        md += "| Feature | Market Gap | Opportunity Type |\n"
        md += "|---------|-----------|------------------|\n"

        # Differentiation: Low average (<6) or low adoption (<50%)
        for crit_id, data in sorted_criteria:
            if data["average"] < 6:
                gap = 10 - data["average"]
                md += f"| {data['name']} | {gap:.1f} point gap | Quick Win |\n"
            elif data["adoption_rate"] < 50 and data["average"] < 7.5:
                md += f"| {data['name']} | Low adoption ({data['adoption_rate']:.0f}%) | Emerging Standard |\n"

        md += "\n### Emerging Threats\n\n"
        md += "Areas where some competitors are pulling ahead:\n\n"

        # Emerging threats: High variance (some excel, some don't)
        threats = []
        for crit_id, data in all_criteria_scores.items():
            if len(data["scores"]) > 1:
                max_score = max(data["scores"])
                min_score = min(data["scores"])
                if max_score - min_score > 3:  # High spread
                    threats.append((crit_id, data, max_score - min_score))

        if threats:
            for crit_id, data, spread in sorted(threats, key=lambda x: x[2], reverse=True)[:3]:
                md += f"- **{data['name']}**: Some competitors ({spread:.1f} point lead) establishing superiority\n"
                md += f"  - Risk of becoming new industry standard\n\n"
        else:
            md += "No significant emerging threats identified - stable competitive environment.\n\n"

        return md

    def _get_site_name(self, result: Dict[str, Any]) -> str:
        """Extract site name from result."""
        return result.get("site_name", "Unknown")
