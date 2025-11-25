"""
HTML Report Generator with Interactive Visualizations

Generates beautiful, interactive HTML reports with:
- Radar charts for competitor comparison
- Bar charts for criteria rankings
- Heatmaps for feature matrices
- Screenshot galleries
- Executive summaries
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from jinja2 import Template
import base64
from .screenshot_annotator import ScreenshotAnnotator


class HTMLReportGenerator:
    """
    Generates interactive HTML reports with charts and visualizations.
    """

    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.annotator = ScreenshotAnnotator()

    def _create_radar_chart(self, results: List[Dict[str, Any]]) -> str:
        """
        Create interactive radar chart comparing all competitors across criteria.

        Args:
            results: List of competitor analysis results

        Returns:
            HTML string with embedded chart
        """
        fig = go.Figure()

        # Filter successful results
        successful_results = [r for r in results if r.get('success') and r.get('criteria_scores')]

        if not successful_results:
            return "<p class='text-muted'>No data available for radar chart</p>"

        # Add trace for each competitor
        for result in successful_results:
            criteria_names = [c['criterion_name'] for c in result['criteria_scores']]
            scores = [c['score'] for c in result['criteria_scores']]

            fig.add_trace(go.Scatterpolar(
                r=scores,
                theta=criteria_names,
                fill='toself',
                name=result.get('site_name', 'Unknown'),
                hovertemplate='<b>%{theta}</b><br>Score: %{r:.1f}/10<extra></extra>'
            ))

        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 10],
                    tickfont=dict(size=10)
                )
            ),
            showlegend=True,
            title=dict(
                text="<b>Competitive UX Comparison</b><br><sub>Overall performance across all criteria</sub>",
                x=0.5,
                xanchor='center'
            ),
            height=600,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.2,
                xanchor="center",
                x=0.5
            )
        )

        return fig.to_html(include_plotlyjs='cdn', div_id='radar-chart', config={'displayModeBar': False})

    def _create_criteria_bar_chart(self, results: List[Dict[str, Any]]) -> str:
        """
        Create bar chart showing top performers for each criterion.

        Args:
            results: List of competitor analysis results

        Returns:
            HTML string with embedded chart
        """
        successful_results = [r for r in results if r.get('success') and r.get('criteria_scores')]

        if not successful_results:
            return "<p class='text-muted'>No data available for bar chart</p>"

        # Aggregate data by criterion
        criteria_data = {}
        for result in successful_results:
            site_name = result.get('site_name', 'Unknown')
            for criterion in result['criteria_scores']:
                crit_name = criterion['criterion_name']
                if crit_name not in criteria_data:
                    criteria_data[crit_name] = []
                criteria_data[crit_name].append({
                    'competitor': site_name,
                    'score': criterion['score']
                })

        # Create grouped bar chart
        fig = go.Figure()

        competitors = list(set([r.get('site_name', 'Unknown') for r in successful_results]))

        for competitor in competitors:
            criterion_names = []
            scores = []

            for crit_name, data in criteria_data.items():
                criterion_names.append(crit_name)
                comp_score = next((d['score'] for d in data if d['competitor'] == competitor), 0)
                scores.append(comp_score)

            fig.add_trace(go.Bar(
                name=competitor,
                x=criterion_names,
                y=scores,
                hovertemplate='<b>%{x}</b><br>%{fullData.name}: %{y:.1f}/10<extra></extra>'
            ))

        fig.update_layout(
            title=dict(
                text="<b>Criteria Performance Comparison</b><br><sub>Scores across all evaluation criteria</sub>",
                x=0.5,
                xanchor='center'
            ),
            xaxis_title="Criteria",
            yaxis_title="Score (0-10)",
            barmode='group',
            height=500,
            xaxis={'tickangle': -45},
            yaxis={'range': [0, 10]},
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.4,
                xanchor="center",
                x=0.5
            )
        )

        return fig.to_html(include_plotlyjs=False, div_id='bar-chart', config={'displayModeBar': False})

    def _create_heatmap(self, results: List[Dict[str, Any]]) -> str:
        """
        Create heatmap showing feature adoption matrix.

        Args:
            results: List of competitor analysis results

        Returns:
            HTML string with embedded chart
        """
        successful_results = [r for r in results if r.get('success') and r.get('criteria_scores')]

        if not successful_results:
            return "<p class='text-muted'>No data available for heatmap</p>"

        # Prepare data
        competitors = [r.get('site_name', 'Unknown') for r in successful_results]
        criteria_names = [c['criterion_name'] for c in successful_results[0]['criteria_scores']]

        # Build score matrix
        scores_matrix = []
        for result in successful_results:
            scores = [c['score'] for c in result['criteria_scores']]
            scores_matrix.append(scores)

        # Create heatmap
        fig = go.Figure(data=go.Heatmap(
            z=scores_matrix,
            x=criteria_names,
            y=competitors,
            colorscale=[
                [0, '#d32f2f'],      # Red (0-2)
                [0.2, '#f57c00'],    # Orange (2-4)
                [0.4, '#fbc02d'],    # Yellow (4-6)
                [0.6, '#7cb342'],    # Light green (6-8)
                [0.8, '#388e3c'],    # Green (8-9)
                [1, '#1b5e20']       # Dark green (9-10)
            ],
            text=scores_matrix,
            texttemplate='%{text:.1f}',
            textfont={"size": 12, "color": "white"},
            hovertemplate='<b>%{y}</b><br>%{x}<br>Score: %{z:.1f}/10<extra></extra>',
            colorbar=dict(
                title="Score",
                tickvals=[0, 2, 4, 6, 8, 10],
                ticktext=['0', '2', '4', '6', '8', '10']
            )
        ))

        fig.update_layout(
            title=dict(
                text="<b>Feature Adoption Heatmap</b><br><sub>Color-coded performance matrix</sub>",
                x=0.5,
                xanchor='center'
            ),
            xaxis_title="Criteria",
            yaxis_title="Competitors",
            height=max(400, len(competitors) * 60),
            xaxis={'tickangle': -45, 'side': 'bottom'}
        )

        return fig.to_html(include_plotlyjs=False, div_id='heatmap', config={'displayModeBar': False})


    def _get_executive_summary(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate executive summary statistics.

        Args:
            results: List of competitor analysis results

        Returns:
            Dictionary with summary stats
        """
        successful_results = [r for r in results if r.get('success') and r.get('overall_score')]

        if not successful_results:
            return {
                'total': len(results),
                'successful': 0,
                'failed': len(results),
                'average_score': 0,
                'leader': {'name': 'N/A', 'score': 0},
                'weakest': {'name': 'N/A', 'score': 0},
                'most_consistent': None,
                'weakest_criterion': None,
                'weakest_criterion_avg': 0,
                'strongest_criterion': None,
                'strongest_criterion_avg': 0
            }

        # Find leader
        leader = max(successful_results, key=lambda x: x.get('overall_score', 0))

        # Find weakest
        weakest = min(successful_results, key=lambda x: x.get('overall_score', 0))

        # Calculate average score
        avg_score = sum(r.get('overall_score', 0) for r in successful_results) / len(successful_results)

        # Find most consistent (lowest variance)
        consistency = {}
        for result in successful_results:
            scores = [c['score'] for c in result.get('criteria_scores', [])]
            if scores:
                variance = sum((s - sum(scores)/len(scores))**2 for s in scores) / len(scores)
                consistency[result.get('site_name')] = variance

        most_consistent = min(consistency, key=consistency.get) if consistency else None

        # Find biggest vulnerabilities across all competitors
        criteria_scores = {}
        for result in successful_results:
            for criterion in result.get('criteria_scores', []):
                crit_name = criterion['criterion_name']
                if crit_name not in criteria_scores:
                    criteria_scores[crit_name] = []
                criteria_scores[crit_name].append(criterion['score'])

        # Average by criterion
        avg_by_criterion = {
            name: sum(scores) / len(scores)
            for name, scores in criteria_scores.items()
        }

        weakest_criterion = min(avg_by_criterion, key=avg_by_criterion.get) if avg_by_criterion else None
        strongest_criterion = max(avg_by_criterion, key=avg_by_criterion.get) if avg_by_criterion else None

        return {
            'total': len(results),
            'successful': len(successful_results),
            'failed': len(results) - len(successful_results),
            'leader': {
                'name': leader.get('site_name'),
                'score': leader.get('overall_score')
            },
            'weakest': {
                'name': weakest.get('site_name'),
                'score': weakest.get('overall_score')
            },
            'average_score': avg_score,
            'most_consistent': most_consistent,
            'weakest_criterion': weakest_criterion,
            'weakest_criterion_avg': avg_by_criterion.get(weakest_criterion, 0) if weakest_criterion else 0,
            'strongest_criterion': strongest_criterion,
            'strongest_criterion_avg': avg_by_criterion.get(strongest_criterion, 0) if strongest_criterion else 0
        }

    def _get_strategic_insights(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate strategic insights: market leaders, opportunities, threats, and quick wins.

        Args:
            results: List of competitor analysis results

        Returns:
            Dictionary with strategic insights data
        """
        successful_results = [r for r in results if r.get('success') and r.get('overall_score')]

        if not successful_results:
            return {
                'market_leaders': [],
                'opportunities': [],
                'threats': [],
                'quick_wins': []
            }

        # 1. Market Leaders - Top 3 by overall score
        sorted_by_score = sorted(successful_results, key=lambda x: x.get('overall_score', 0), reverse=True)
        market_leaders = []
        for comp in sorted_by_score[:3]:
            # Find their key differentiator (highest scoring criterion)
            best_criterion = None
            best_score = 0
            for criterion in comp.get('criteria_scores', []):
                if criterion['score'] > best_score:
                    best_score = criterion['score']
                    best_criterion = criterion['criterion_name']

            market_leaders.append({
                'name': comp.get('site_name'),
                'score': comp.get('overall_score'),
                'differentiator': best_criterion if best_criterion else 'N/A'
            })

        # 2. Calculate average scores by criterion
        criteria_scores = {}
        for result in successful_results:
            for criterion in result.get('criteria_scores', []):
                crit_name = criterion['criterion_name']
                if crit_name not in criteria_scores:
                    criteria_scores[crit_name] = []
                criteria_scores[crit_name].append(criterion['score'])

        avg_by_criterion = {
            name: sum(scores) / len(scores)
            for name, scores in criteria_scores.items()
        }

        # 3. Top 3 Opportunities - Criteria with lowest avg scores (where 60%+ score below threshold)
        opportunities = []
        for crit_name, scores in criteria_scores.items():
            avg_score = avg_by_criterion[crit_name]
            below_threshold = sum(1 for s in scores if s < 6)
            pct_below = (below_threshold / len(scores)) * 100

            if pct_below >= 60:  # At least 60% scoring below 6
                # Calculate potential gain vs average competitor
                potential_gain = 8.0 - avg_score  # Assume reaching 8/10 is achievable
                opportunities.append({
                    'criterion': crit_name,
                    'avg_score': avg_score,
                    'pct_below_6': pct_below,
                    'potential_gain': potential_gain
                })

        # Sort by potential gain (biggest opportunities first)
        opportunities.sort(key=lambda x: x['potential_gain'], reverse=True)
        opportunities = opportunities[:3]  # Top 3

        # 4. Competitive Threats - Standout strengths from market leaders (8+ overall score)
        threats = []
        market_leader_comps = [c for c in successful_results if c.get('overall_score', 0) >= 8.0]

        for comp in market_leader_comps:
            # Find their strongest criteria (9+ score)
            strong_criteria = [
                c for c in comp.get('criteria_scores', [])
                if c['score'] >= 9.0
            ]

            if strong_criteria:
                # Take their top strength
                top_strength = max(strong_criteria, key=lambda x: x['score'])
                threats.append({
                    'competitor': comp.get('site_name'),
                    'criterion': top_strength['criterion_name'],
                    'score': top_strength['score'],
                    'action': f"Must match {top_strength['criterion_name'].lower()}"
                })

        # Limit to top 3 threats
        threats.sort(key=lambda x: x['score'], reverse=True)
        threats = threats[:3]

        # 5. Quick Wins - Common gaps (60%+ below 6) that are typically fast to implement
        quick_wins = []
        for crit_name, scores in criteria_scores.items():
            below_6_count = sum(1 for s in scores if s < 6)
            pct_below_6 = (below_6_count / len(scores)) * 100

            if pct_below_6 >= 60:  # Widespread weakness
                avg = avg_by_criterion[crit_name]
                missing_count = sum(1 for s in scores if s < 4)  # Completely missing

                quick_wins.append({
                    'criterion': crit_name,
                    'missing_count': missing_count,
                    'total_count': len(scores),
                    'avg_score': avg
                })

        # Sort by how many competitors are missing it entirely
        quick_wins.sort(key=lambda x: x['missing_count'], reverse=True)
        quick_wins = quick_wins[:4]  # Top 4 quick wins

        return {
            'market_leaders': market_leaders,
            'opportunities': opportunities,
            'threats': threats,
            'quick_wins': quick_wins
        }

    def _get_rankings_data(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate rankings table data with competitive positioning.

        Args:
            results: List of competitor analysis results

        Returns:
            List of competitors with ranking data
        """
        successful_results = [r for r in results if r.get('success') and r.get('overall_score')]

        if not successful_results:
            return []

        # Sort by overall score
        sorted_comps = sorted(successful_results, key=lambda x: x.get('overall_score', 0), reverse=True)

        rankings = []
        for rank, comp in enumerate(sorted_comps, 1):
            score = comp.get('overall_score', 0)

            # Determine competitive position based on score
            if score >= 8.0:
                position = 'Market Leader'
                position_class = 'advantage'
            elif score >= 6.5:
                position = 'Strong Contender'
                position_class = 'advantage'
            elif score >= 5.0:
                position = 'Competitive'
                position_class = 'parity'
            else:
                position = 'Vulnerable'
                position_class = 'vulnerability'

            # Find key differentiator (highest scoring criterion)
            best_criterion = None
            best_score = 0
            for criterion in comp.get('criteria_scores', []):
                if criterion['score'] > best_score:
                    best_score = criterion['score']
                    best_criterion = criterion['criterion_name']

            rankings.append({
                'rank': rank,
                'name': comp.get('site_name'),
                'score': score,
                'position': position,
                'position_class': position_class,
                'differentiator': best_criterion if best_criterion else 'N/A'
            })

        return rankings

    def _prepare_annotated_screenshots(
        self,
        competitor_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Create annotated versions of screenshots for each competitor.

        Args:
            competitor_results: List of competitor analysis results

        Returns:
            Updated results with annotated screenshot paths
        """
        for result in competitor_results:
            if not result.get('success') or not result.get('screenshot_metadata'):
                continue

            # Generate annotations from criteria scores
            if result.get('criteria_scores'):
                annotations = self.annotator.create_annotations_from_analysis(
                    result['criteria_scores'],
                    top_n=2  # Top 2 strengths and weaknesses
                )

                # Annotate each screenshot
                for screenshot in result['screenshot_metadata']:
                    try:
                        screenshot_path = screenshot.get('filepath')
                        if screenshot_path and Path(screenshot_path).exists():
                            annotated_path = self.annotator.annotate_screenshot(
                                screenshot_path,
                                annotations
                            )
                            screenshot['annotated_filepath'] = annotated_path
                    except Exception as e:
                        # If annotation fails, just skip it
                        pass

        return competitor_results

    def _make_paths_relative(
        self,
        competitor_results: List[Dict[str, Any]],
        html_file_path: Path
    ) -> List[Dict[str, Any]]:
        """
        Convert absolute screenshot paths to relative paths from HTML file location.

        Args:
            competitor_results: List of competitor analysis results
            html_file_path: Path where HTML file will be saved

        Returns:
            Updated results with relative screenshot paths
        """
        from pathlib import Path
        import os

        html_dir = html_file_path.parent

        for result in competitor_results:
            if not result.get('screenshot_metadata'):
                continue

            for screenshot in result['screenshot_metadata']:
                # Convert filepath to relative
                if screenshot.get('filepath'):
                    abs_path = Path(screenshot['filepath'])
                    try:
                        rel_path = os.path.relpath(abs_path, html_dir)
                        screenshot['filepath'] = rel_path
                    except ValueError:
                        # If paths are on different drives (Windows), keep absolute
                        pass

                # Convert annotated_filepath to relative
                if screenshot.get('annotated_filepath'):
                    abs_path = Path(screenshot['annotated_filepath'])
                    try:
                        rel_path = os.path.relpath(abs_path, html_dir)
                        screenshot['annotated_filepath'] = rel_path
                    except ValueError:
                        # If paths are on different drives (Windows), keep absolute
                        pass

        return competitor_results

    def _get_html_template(self) -> str:
        """
        Return HTML template string with lightbox and filtering.

        Returns:
            HTML template with Bootstrap, custom styling, and interactive features
        """
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ analysis_type }} - Competitive Intelligence Report</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        /* Lightbox Modal */
        .lightbox-modal {
            display: none;
            position: fixed;
            z-index: 9999;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.95);
            align-items: center;
            justify-content: center;
        }
        .lightbox-modal.active {
            display: flex;
        }
        .lightbox-content {
            position: relative;
            max-width: 95%;
            max-height: 95%;
            animation: zoomIn 0.3s;
        }
        .lightbox-content img {
            max-width: 100%;
            max-height: 95vh;
            object-fit: contain;
            border-radius: 8px;
            box-shadow: 0 0 50px rgba(255,255,255,0.2);
        }
        .lightbox-close {
            position: absolute;
            top: 20px;
            right: 40px;
            color: white;
            font-size: 40px;
            font-weight: bold;
            cursor: pointer;
            z-index: 10000;
            background: rgba(0,0,0,0.5);
            width: 50px;
            height: 50px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.3s;
        }
        .lightbox-close:hover {
            background: rgba(255,255,255,0.2);
            transform: scale(1.1);
        }
        .lightbox-nav {
            position: absolute;
            top: 50%;
            transform: translateY(-50%);
            color: white;
            font-size: 40px;
            cursor: pointer;
            background: rgba(0,0,0,0.5);
            width: 50px;
            height: 50px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.3s;
        }
        .lightbox-nav:hover {
            background: rgba(255,255,255,0.2);
            transform: translateY(-50%) scale(1.1);
        }
        .lightbox-prev {
            left: 20px;
        }
        .lightbox-next {
            right: 20px;
        }
        .lightbox-caption {
            position: absolute;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            color: white;
            background: rgba(0,0,0,0.7);
            padding: 15px 30px;
            border-radius: 25px;
            font-size: 1.1rem;
            max-width: 80%;
            text-align: center;
        }
        @keyframes zoomIn {
            from {
                transform: scale(0.8);
                opacity: 0;
            }
            to {
                transform: scale(1);
                opacity: 1;
            }
        }

        /* Filter Controls */
        .filter-panel {
            background: white;
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            position: sticky;
            top: 20px;
            z-index: 100;
        }
        .filter-panel .form-label {
            font-weight: 600;
            color: #2d3748;
            margin-bottom: 8px;
        }
        .filter-panel .form-select,
        .filter-panel .form-control {
            border: 2px solid #e2e8f0;
            border-radius: 8px;
            padding: 10px 15px;
        }
        .filter-panel .form-select:focus,
        .filter-panel .form-control:focus {
            border-color: #10b981;
            box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.1);
        }
        .filter-badge {
            display: inline-block;
            padding: 6px 12px;
            background: #10b981;
            color: white;
            border-radius: 20px;
            font-size: 0.85rem;
            margin-right: 8px;
            margin-bottom: 8px;
            cursor: pointer;
            transition: all 0.3s;
        }
        .filter-badge:hover {
            background: #059669;
            transform: translateY(-2px);
        }
        .filter-badge.active {
            background: #48bb78;
        }
        .reset-filters-btn {
            background: linear-gradient(135deg, #f56565 0%, #ed8936 100%);
            border: none;
            color: white;
            padding: 10px 20px;
            border-radius: 8px;
            font-weight: 600;
            transition: all 0.3s;
        }
        .reset-filters-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(245, 101, 101, 0.4);
        }
        .filter-results-count {
            font-size: 0.9rem;
            color: #718096;
            margin-top: 10px;
        }

        /* Make competitor cards filterable */
        .filtered-out {
            display: none !important;
        }

        /* Enhanced Screenshot Gallery */
        .screenshot-gallery {
            display: flex;
            gap: 15px;
            margin-top: 20px;
            flex-wrap: wrap;
        }
        .screenshot-thumb {
            border: 2px solid #e2e8f0;
            border-radius: 8px;
            overflow: hidden;
            transition: all 0.3s ease;
            cursor: pointer;
            position: relative;
        }
        .screenshot-thumb:hover {
            border-color: #10b981;
            transform: scale(1.05);
            box-shadow: 0 8px 25px rgba(0,0,0,0.2);
        }
        .screenshot-thumb img {
            width: 250px;
            height: auto;
            display: block;
        }
        .screenshot-thumb .overlay {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(16, 185, 129, 0.9);
            display: flex;
            align-items: center;
            justify-content: center;
            opacity: 0;
            transition: opacity 0.3s;
            color: white;
            font-size: 2rem;
        }
        .screenshot-thumb:hover .overlay {
            opacity: 1;
        }
        .screenshot-badge {
            position: absolute;
            top: 10px;
            right: 10px;
            background: rgba(0,0,0,0.7);
            color: white;
            padding: 5px 10px;
            border-radius: 5px;
            font-size: 0.75rem;
            font-weight: 600;
        }
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            padding: 20px 0;
        }
        .container-main {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            padding: 40px;
            margin-bottom: 40px;
        }
        .header {
            text-align: center;
            margin-bottom: 40px;
            padding-bottom: 30px;
            border-bottom: 3px solid #10b981;
        }
        .header h1 {
            color: #2d3748;
            font-weight: 700;
            margin-bottom: 10px;
        }
        .header .subtitle {
            color: #718096;
            font-size: 1.1rem;
        }
        .stat-card {
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            color: white;
            padding: 25px;
            border-radius: 15px;
            margin-bottom: 20px;
            box-shadow: 0 4px 15px rgba(16, 185, 129, 0.4);
            transition: transform 0.3s ease;
        }
        .stat-card:hover {
            transform: translateY(-5px);
        }
        .stat-card .stat-value {
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 5px;
        }
        .stat-card .stat-label {
            font-size: 0.9rem;
            opacity: 0.9;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .chart-container {
            background: #f7fafc;
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }
        .competitor-card {
            border: 2px solid #e2e8f0;
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 25px;
            transition: all 0.3s ease;
            background: white;
        }
        .competitor-card:hover {
            border-color: #10b981;
            box-shadow: 0 8px 25px rgba(16, 185, 129, 0.15);
            transform: translateY(-2px);
        }
        .competitor-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 2px solid #e2e8f0;
        }
        .competitor-name {
            font-size: 1.5rem;
            font-weight: 700;
            color: #2d3748;
        }
        .overall-score {
            font-size: 2rem;
            font-weight: 700;
            color: #10b981;
        }
        .score-badge {
            display: inline-block;
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: 600;
            font-size: 0.9rem;
            margin-right: 8px;
            margin-bottom: 8px;
        }
        .score-excellent { background: #48bb78; color: white; }
        .score-good { background: #38b2ac; color: white; }
        .score-average { background: #ed8936; color: white; }
        .score-poor { background: #f56565; color: white; }
        .criterion-row {
            padding: 12px;
            margin-bottom: 8px;
            border-radius: 8px;
            background: #f7fafc;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .criterion-name {
            font-weight: 600;
            color: #2d3748;
            flex: 1;
        }
        .criterion-score {
            font-weight: 700;
            font-size: 1.1rem;
            margin-left: 15px;
        }
        .progress-bar-custom {
            height: 8px;
            border-radius: 10px;
            background: #e2e8f0;
            overflow: hidden;
            margin-top: 8px;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #10b981 0%, #059669 100%);
            border-radius: 10px;
            transition: width 0.3s ease;
        }
        .screenshot-gallery {
            display: flex;
            gap: 15px;
            margin-top: 20px;
            flex-wrap: wrap;
        }
        .screenshot-thumb {
            border: 2px solid #e2e8f0;
            border-radius: 8px;
            overflow: hidden;
            transition: all 0.3s ease;
            cursor: pointer;
        }
        .screenshot-thumb:hover {
            border-color: #667eea;
            transform: scale(1.05);
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        }
        .screenshot-thumb img {
            width: 250px;
            height: auto;
            display: block;
        }
        .competitive-status {
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: 600;
            font-size: 0.85rem;
            display: inline-block;
        }
        .status-advantage { background: #48bb78; color: white; }
        .status-parity { background: #4299e1; color: white; }
        .status-vulnerability { background: #f56565; color: white; }
        .footer {
            text-align: center;
            padding: 30px;
            color: #718096;
            font-size: 0.9rem;
        }
        .section-title {
            font-size: 1.8rem;
            font-weight: 700;
            color: #2d3748;
            margin-bottom: 25px;
            padding-bottom: 15px;
            border-bottom: 3px solid #10b981;
        }
        .alert-custom {
            background: linear-gradient(135deg, #10b98115 0%, #05966915 100%);
            border-left: 4px solid #10b981;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 25px;
        }
        .card-body-collapsible {
            overflow: hidden;
            transition: max-height 0.3s ease, opacity 0.3s ease;
            max-height: 5000px;
            opacity: 1;
        }
        .card-body-collapsible.collapsed {
            max-height: 0;
            opacity: 0;
            margin: 0;
            padding: 0;
        }
        .toggle-card-btn {
            background: none;
            border: none;
            color: #10b981;
            cursor: pointer;
            font-size: 1.5rem;
            padding: 0;
            margin-left: 10px;
            transition: transform 0.3s ease;
        }
        .toggle-card-btn:hover {
            color: #059669;
        }
        .toggle-card-btn.collapsed {
            transform: rotate(180deg);
        }
        /* Strategic Insights Section */
        .exec-summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        @media (max-width: 768px) {
            .exec-summary-grid {
                grid-template-columns: 1fr;
            }
        }
        .exec-card {
            background: white;
            border: 2px solid #e2e8f0;
            border-radius: 12px;
            padding: 20px;
            transition: all 0.3s ease;
        }
        .exec-card:hover {
            border-color: #10b981;
            box-shadow: 0 4px 15px rgba(16, 185, 129, 0.2);
            transform: translateY(-3px);
        }
        .exec-card h4 {
            color: #10b981;
            font-size: 1.1rem;
            font-weight: 700;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #e2e8f0;
        }
        .exec-card ul, .exec-card ol {
            margin: 0;
            padding-left: 20px;
        }
        .exec-card li {
            margin-bottom: 10px;
            color: #2d3748;
        }
        .exec-card .stat {
            display: block;
            color: #718096;
            font-size: 0.85rem;
            font-style: italic;
            margin-top: 5px;
        }
        .exec-card .impact {
            background: linear-gradient(135deg, #10b98115 0%, #05966915 100%);
            border-left: 3px solid #10b981;
            padding: 10px;
            border-radius: 6px;
            margin-top: 15px;
            font-size: 0.9rem;
        }
        /* Rankings Table */
        .ranking-table {
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }
        .ranking-table thead {
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            color: white;
        }
        .ranking-table th {
            padding: 15px;
            text-align: left;
            font-weight: 600;
        }
        .ranking-table td {
            padding: 12px 15px;
            border-bottom: 1px solid #e2e8f0;
        }
        .ranking-table tbody tr:hover {
            background: #f7fafc;
        }
        .rank-badge {
            display: inline-block;
            width: 32px;
            height: 32px;
            border-radius: 50%;
            text-align: center;
            line-height: 32px;
            font-weight: 700;
            color: white;
        }
        .rank-1 { background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%); }
        .rank-2 { background: linear-gradient(135deg, #C0C0C0 0%, #A8A8A8 100%); }
        .rank-3 { background: linear-gradient(135deg, #CD7F32 0%, #B8860B 100%); }
        .rank-other { background: linear-gradient(135deg, #718096 0%, #4a5568 100%); }
        .score-cell {
            font-weight: 700;
            font-size: 1.1rem;
        }
        .score-high { color: #48bb78; }
        .score-medium { color: #ed8936; }
        .score-low { color: #f56565; }
    </style>
</head>
<body>
    <div class="container">
        <div class="container-main">
            <!-- Header -->
            <div class="header">
                <h1><i class="fas fa-chart-line"></i> Competitive Intelligence Report</h1>
                <div class="subtitle">{{ analysis_type }} | Generated {{ timestamp }}</div>
            </div>

            <!-- Executive Summary -->
            <div class="row mb-4">
                <div class="col-12">
                    <h2 class="section-title"><i class="fas fa-star"></i> Executive Summary</h2>
                </div>
                <div class="col-md-3">
                    <div class="stat-card">
                        <div class="stat-value">{{ summary.successful }}</div>
                        <div class="stat-label">Competitors Analyzed</div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="stat-card">
                        <div class="stat-value">{{ "%.1f"|format(summary.average_score) }}</div>
                        <div class="stat-label">Average Score</div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="stat-card">
                        <div class="stat-value">{{ "%.1f"|format(summary.leader.score) }}</div>
                        <div class="stat-label">Top Score ({{ summary.leader.name }})</div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="stat-card">
                        <div class="stat-value">{{ "%.1f"|format(summary.weakest.score) }}</div>
                        <div class="stat-label">Lowest ({{ summary.weakest.name }})</div>
                    </div>
                </div>
            </div>

            <!-- Key Insights -->
            <div class="alert-custom">
                <h5><i class="fas fa-lightbulb"></i> <strong>Key Insights</strong></h5>
                <ul class="mb-0">
                    <li><strong><i class="fas fa-trophy"></i> Market Leader:</strong> {{ summary.leader.name }} leads with {{ "%.1f"|format(summary.leader.score) }}/10</li>
                    {% if summary.most_consistent %}
                    <li><strong><i class="fas fa-chart-bar"></i> Most Consistent:</strong> {{ summary.most_consistent }} shows the most balanced performance</li>
                    {% endif %}
                    {% if summary.strongest_criterion %}
                    <li><strong><i class="fas fa-fire"></i> Industry Strength:</strong> {{ summary.strongest_criterion }} (avg: {{ "%.1f"|format(summary.strongest_criterion_avg) }}/10)</li>
                    {% endif %}
                    {% if summary.weakest_criterion %}
                    <li><strong><i class="fas fa-exclamation-triangle"></i> Market Vulnerability:</strong> {{ summary.weakest_criterion }} (avg: {{ "%.1f"|format(summary.weakest_criterion_avg) }}/10) - opportunity to differentiate</li>
                    {% endif %}
                </ul>
            </div>

            <!-- Strategic Insights -->
            <div class="row mb-4">
                <div class="col-12">
                    <h2 class="section-title"><i class="fas fa-lightbulb"></i> Strategic Insights</h2>
                </div>
                <div class="col-12">
                    <div class="exec-summary-grid">
                        <!-- Market Leaders -->
                        <div class="exec-card">
                            <h4><i class="fas fa-crown"></i> Market Leaders</h4>
                            <ul>
                                {% for leader in strategic_insights.market_leaders %}
                                <li><strong>{{ leader.name }}</strong> ({{ "%.1f"|format(leader.score) }}/10){% if leader.differentiator != 'N/A' %} - {{ leader.differentiator }}{% endif %}</li>
                                {% endfor %}
                                {% if not strategic_insights.market_leaders %}
                                <li class="text-muted">No data available</li>
                                {% endif %}
                            </ul>
                        </div>

                        <!-- Top 3 Opportunities -->
                        <div class="exec-card">
                            <h4><i class="fas fa-bullseye"></i> Top Opportunities</h4>
                            <ol>
                                {% for opp in strategic_insights.opportunities %}
                                <li><strong>{{ opp.criterion }}</strong> - {{ "%.0f"|format(opp.pct_below_6) }}% score below 6
                                    <span class="stat">Potential: +{{ "%.1f"|format(opp.potential_gain) }}pts vs avg competitor</span>
                                </li>
                                {% endfor %}
                                {% if not strategic_insights.opportunities %}
                                <li class="text-muted">No widespread weaknesses identified (strong market overall)</li>
                                {% endif %}
                            </ol>
                        </div>

                        <!-- Competitive Threats -->
                        <div class="exec-card">
                            <h4><i class="fas fa-exclamation-circle"></i> Competitive Threats</h4>
                            <ul>
                                {% for threat in strategic_insights.threats %}
                                <li><strong>{{ threat.competitor }}:</strong> {{ threat.criterion }} ({{ "%.1f"|format(threat.score) }}/10)
                                    <br><em>Action: {{ threat.action }}</em>
                                </li>
                                {% endfor %}
                                {% if not strategic_insights.threats %}
                                <li class="text-muted">No standout threats identified (no competitor scoring 9+ on any criterion)</li>
                                {% endif %}
                            </ul>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Overall Rankings -->
            <div class="row mb-4">
                <div class="col-12">
                    <h2 class="section-title"><i class="fas fa-trophy"></i> Overall Rankings</h2>
                </div>
                <div class="col-12">
                    <table class="ranking-table">
                        <thead>
                            <tr>
                                <th>Rank</th>
                                <th>Competitor</th>
                                <th>Overall Score</th>
                                <th>Competitive Position</th>
                                <th>Key Differentiator</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for comp in rankings %}
                            <tr>
                                <td><span class="rank-badge rank-{% if comp.rank <= 3 %}{{ comp.rank }}{% else %}other{% endif %}">{{ comp.rank }}</span></td>
                                <td><strong>{{ comp.name }}</strong></td>
                                <td><span class="score-cell {% if comp.score >= 8 %}score-high{% elif comp.score >= 6 %}score-medium{% else %}score-low{% endif %}">{{ "%.1f"|format(comp.score) }}/10</span></td>
                                <td><span class="competitive-status status-{{ comp.position_class }}">{{ comp.position }}</span></td>
                                <td>{{ comp.differentiator }}</td>
                            </tr>
                            {% endfor %}
                            {% if not rankings %}
                            <tr>
                                <td colspan="5" class="text-center text-muted">No data available</td>
                            </tr>
                            {% endif %}
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Filter Panel -->
            <div class="row mb-4">
                <div class="col-12">
                    <div class="filter-panel">
                        <h5><i class="fas fa-filter"></i> <strong>Filter & Search</strong></h5>
                        <div class="row">
                            <div class="col-md-4">
                                <label class="form-label">Search Competitor</label>
                                <input type="text" class="form-control" id="searchCompetitor" placeholder="Type competitor name...">
                            </div>
                            <div class="col-md-4">
                                <label class="form-label">Minimum Score</label>
                                <input type="range" class="form-range" id="minScoreFilter" min="0" max="10" step="0.5" value="0">
                                <div class="text-center"><span id="minScoreValue">0.0</span>/10</div>
                            </div>
                            <div class="col-md-4">
                                <label class="form-label">Competitive Position</label>
                                <select class="form-select" id="statusFilter">
                                    <option value="all">All Status</option>
                                    <option value="market_leader">Market Leader</option>
                                    <option value="strong_contender">Strong Contender</option>
                                    <option value="competitive">Competitive</option>
                                    <option value="vulnerable">Vulnerable</option>
                                </select>
                            </div>
                        </div>
                        <div class="mt-3">
                            <button class="reset-filters-btn" onclick="resetFilters()">
                                <i class="fas fa-redo"></i> Reset Filters
                            </button>
                            <span class="filter-results-count" id="filterCount">Showing {{ competitors|length }} competitors</span>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Charts Section -->
            <div class="row">
                <div class="col-12">
                    <h2 class="section-title"><i class="fas fa-chart-area"></i> Visual Analysis</h2>
                </div>

                <!-- Radar Chart -->
                <div class="col-12">
                    <div class="chart-container" id="radarChartContainer">
                        {{ radar_chart|safe }}
                    </div>
                </div>

                <!-- Heatmap -->
                <div class="col-12">
                    <div class="chart-container" id="heatmapContainer">
                        {{ heatmap|safe }}
                    </div>
                </div>

                <!-- Bar Chart -->
                <div class="col-12">
                    <div class="chart-container" id="barChartContainer">
                        {{ bar_chart|safe }}
                    </div>
                </div>
            </div>

            <!-- Competitor Details -->
            <div class="row" id="competitorContainer">
                <div class="col-12">
                    <h2 class="section-title"><i class="fas fa-users"></i> Competitor Profiles</h2>
                </div>

                {% for competitor in competitors %}
                {% if competitor.success %}
                <div class="col-12">
                    <div class="competitor-card"
                         data-competitor="{{ competitor.site_name|lower }}"
                         data-score="{{ competitor.overall_score }}"
                         data-tier="{{ competitor.competitive_position.tier if competitor.competitive_position else '' }}">
                        <div class="competitor-header">
                            <div>
                                <div class="competitor-name">{{ competitor.site_name }}</div>
                                <small class="text-muted">{{ competitor.url }}</small>
                            </div>
                            <div style="display: flex; align-items: center; gap: 15px;">
                                <div class="overall-score">
                                    {{ "%.1f"|format(competitor.overall_score) }}/10
                                </div>
                                <button class="toggle-card-btn{% if loop.index > 3 %} collapsed{% endif %}"
                                        onclick="toggleCard('{{ competitor.site_name|lower|replace(' ', '-')|replace('.', '-') }}')">
                                    <i class="fas fa-chevron-up"></i>
                                </button>
                            </div>
                        </div>

                        <!-- Competitive Position -->
                        {% if competitor.competitive_position %}
                        <div class="mb-3">
                            <span class="score-badge
                                {% if competitor.competitive_position.tier == 'market_leader' %}score-excellent
                                {% elif competitor.competitive_position.tier == 'strong_contender' %}score-good
                                {% else %}score-average{% endif %}">
                                {{ competitor.competitive_position.tier|replace('_', ' ')|title }}
                            </span>
                            <p class="mt-2 text-muted">{{ competitor.competitive_position.positioning }}</p>
                        </div>
                        {% endif %}

                        <!-- Collapsible Card Body -->
                        <div class="card-body-collapsible{% if loop.index > 3 %} collapsed{% endif %}"
                             id="{{ competitor.site_name|lower|replace(' ', '-')|replace('.', '-') }}">

                        <!-- Criteria Scores -->
                        <div class="mt-3">
                            <h5><strong>Performance by Criteria</strong></h5>
                            {% for criterion in competitor.criteria_scores %}
                            <div class="criterion-row">
                                <div class="criterion-name">
                                    {{ criterion.criterion_name }}
                                    <span class="competitive-status status-{{ criterion.competitive_status }}">
                                        {{ criterion.competitive_status }}
                                    </span>
                                </div>
                                <div class="criterion-score" style="color:
                                    {% if criterion.score >= 8 %}#48bb78
                                    {% elif criterion.score >= 6 %}#38b2ac
                                    {% elif criterion.score >= 4 %}#ed8936
                                    {% else %}#f56565{% endif %}">
                                    {{ "%.1f"|format(criterion.score) }}
                                </div>
                            </div>
                            <div class="progress-bar-custom">
                                <div class="progress-fill" style="width: {{ criterion.score * 10 }}%"></div>
                            </div>
                            {% endfor %}
                        </div>

                        <!-- Strengths & Vulnerabilities -->
                        <div class="row mt-4">
                            {% if competitor.strengths %}
                            <div class="col-md-6">
                                <h6><i class="fas fa-trophy text-success"></i> <strong>Competitive Advantages</strong></h6>
                                <ul>
                                    {% for strength in competitor.strengths[:3] %}
                                    <li>{{ strength }}</li>
                                    {% endfor %}
                                </ul>
                            </div>
                            {% endif %}
                            {% if competitor.exploitable_vulnerabilities %}
                            <div class="col-md-6">
                                <h6><i class="fas fa-exclamation-triangle text-warning"></i> <strong>Vulnerabilities</strong></h6>
                                <ul>
                                    {% for vuln in competitor.exploitable_vulnerabilities[:3] %}
                                    <li>{{ vuln.vulnerability }}</li>
                                    {% endfor %}
                                </ul>
                            </div>
                            {% endif %}
                        </div>

                        <!-- Screenshots (if available) -->
                        {% if competitor.screenshot_metadata %}
                        <div class="screenshot-gallery">
                            {% for screenshot in competitor.screenshot_metadata %}
                            <div class="screenshot-thumb"
                                 onclick="openLightbox('{{ screenshot.annotated_filepath if screenshot.annotated_filepath else screenshot.filepath }}', '{{ competitor.site_name }} - {{ screenshot.viewport_name|title }}')">
                                <img src="{{ screenshot.annotated_filepath if screenshot.annotated_filepath else screenshot.filepath }}"
                                     alt="{{ screenshot.viewport_name }}"
                                     title="{{ screenshot.viewport_name|title }} ({{ screenshot.viewport.width }}x{{ screenshot.viewport.height }})">
                                <div class="overlay">
                                    <i class="fas fa-search-plus"></i>
                                </div>
                                <div class="screenshot-badge">{{ screenshot.viewport_name|title }}</div>
                            </div>
                            {% endfor %}
                        </div>
                        {% endif %}

                        </div><!-- End card-body-collapsible -->
                    </div>
                </div>
                {% endif %}
                {% endfor %}
            </div>

            <!-- Footer -->
            <div class="footer">
                <p>Generated by <strong>E-commerce UX Benchmark Agent v1.2.0</strong></p>
                <p>Report Date: {{ timestamp }}</p>
            </div>
        </div>
    </div>

    <!-- Lightbox Modal -->
    <div id="lightboxModal" class="lightbox-modal" onclick="closeLightbox(event)">
        <span class="lightbox-close" onclick="closeLightbox(event)">&times;</span>
        <div class="lightbox-content" onclick="event.stopPropagation()">
            <img id="lightboxImage" src="" alt="">
            <div class="lightbox-caption" id="lightboxCaption"></div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        // Lightbox functionality
        function openLightbox(imageSrc, caption) {
            const modal = document.getElementById('lightboxModal');
            const img = document.getElementById('lightboxImage');
            const cap = document.getElementById('lightboxCaption');

            img.src = imageSrc;
            cap.textContent = caption;
            modal.classList.add('active');

            // Prevent body scroll when lightbox is open
            document.body.style.overflow = 'hidden';
        }

        function closeLightbox(event) {
            const modal = document.getElementById('lightboxModal');
            modal.classList.remove('active');
            document.body.style.overflow = 'auto';
            event.stopPropagation();
        }

        // Close lightbox on ESC key
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                closeLightbox(event);
            }
        });

        // Filter functionality
        const searchInput = document.getElementById('searchCompetitor');
        const minScoreSlider = document.getElementById('minScoreFilter');
        const minScoreValue = document.getElementById('minScoreValue');
        const statusFilter = document.getElementById('statusFilter');
        const filterCount = document.getElementById('filterCount');

        // Update min score display
        minScoreSlider.addEventListener('input', function() {
            minScoreValue.textContent = this.value;
            applyFilters();
        });

        // Apply filters on input
        searchInput.addEventListener('input', applyFilters);
        statusFilter.addEventListener('change', applyFilters);

        function applyFilters() {
            const searchTerm = searchInput.value.toLowerCase();
            const minScore = parseFloat(minScoreSlider.value);
            const positionFilter = statusFilter.value;

            const cards = document.querySelectorAll('.competitor-card');
            const rankingRows = document.querySelectorAll('.ranking-table tbody tr');
            let visibleCount = 0;
            let visibleCompetitors = [];

            cards.forEach(card => {
                const competitorName = card.getAttribute('data-competitor');
                const score = parseFloat(card.getAttribute('data-score'));
                const tier = card.getAttribute('data-tier');

                // Search filter
                const matchesSearch = competitorName.includes(searchTerm);

                // Score filter
                const matchesScore = score >= minScore;

                // Position filter - filter by competitive position tier
                let matchesPosition = positionFilter === 'all';
                if (!matchesPosition) {
                    matchesPosition = tier === positionFilter;
                }

                // Show/hide card
                if (matchesSearch && matchesScore && matchesPosition) {
                    card.parentElement.classList.remove('filtered-out');
                    visibleCount++;
                    visibleCompetitors.push(competitorName);
                } else {
                    card.parentElement.classList.add('filtered-out');
                }
            });

            // Update count
            filterCount.textContent = `Showing ${visibleCount} of ${cards.length} competitors`;

            // Update charts with filtered data
            updateCharts(visibleCompetitors);
        }

        function updateCharts(visibleCompetitors) {
            // Re-render Plotly charts with only visible competitors

            // If no competitors visible, show all
            const showAll = !visibleCompetitors || visibleCompetitors.length === 0;

            // Update Radar Chart
            const radarDiv = document.getElementById('radar-chart');
            if (radarDiv && radarDiv.data) {
                const visibility = radarDiv.data.map(trace => {
                    if (showAll) return true;
                    return visibleCompetitors.includes(trace.name.toLowerCase()) ? true : 'legendonly';
                });
                Plotly.restyle('radar-chart', { visible: visibility },
                    Array.from({length: radarDiv.data.length}, (_, i) => i));
            }

            // Update Bar Chart
            const barDiv = document.getElementById('bar-chart');
            if (barDiv && barDiv.data) {
                const visibility = barDiv.data.map(trace => {
                    if (showAll) return true;
                    return visibleCompetitors.includes(trace.name.toLowerCase()) ? true : 'legendonly';
                });
                Plotly.restyle('bar-chart', { visible: visibility },
                    Array.from({length: barDiv.data.length}, (_, i) => i));
            }

            // Update Heatmap (requires data filtering and redraw)
            const heatmapDiv = document.getElementById('heatmap');
            if (heatmapDiv && heatmapDiv.data) {
                // Store original data on first call
                if (!window.originalHeatmapData) {
                    window.originalHeatmapData = JSON.parse(JSON.stringify(heatmapDiv.data));
                }

                if (showAll) {
                    // Restore original data
                    Plotly.react('heatmap', window.originalHeatmapData, heatmapDiv.layout);
                } else {
                    // Filter heatmap by y-axis labels (competitors)
                    const originalData = window.originalHeatmapData[0];
                    const filteredIndices = [];
                    const filteredY = [];
                    const filteredZ = [];

                    originalData.y.forEach((comp, idx) => {
                        if (visibleCompetitors.includes(comp.toLowerCase())) {
                            filteredIndices.push(idx);
                            filteredY.push(comp);
                            filteredZ.push(originalData.z[idx]);
                        }
                    });

                    const filteredData = [{
                        ...originalData,
                        y: filteredY,
                        z: filteredZ
                    }];

                    Plotly.react('heatmap', filteredData, heatmapDiv.layout);
                }
            }
        }

        function resetFilters() {
            searchInput.value = '';
            minScoreSlider.value = 0;
            minScoreValue.textContent = '0.0';
            statusFilter.value = 'all';
            applyFilters();
        }

        // Initialize filters and build dynamic dropdown
        document.addEventListener('DOMContentLoaded', function() {
            const cards = document.querySelectorAll('.competitor-card');
            const totalCards = cards.length;
            filterCount.textContent = `Showing ${totalCards} competitors`;

            // Build dynamic filter dropdown based on available tiers
            const availableTiers = new Map();
            cards.forEach(card => {
                const tier = card.getAttribute('data-tier');
                if (tier) {
                    availableTiers.set(tier, (availableTiers.get(tier) || 0) + 1);
                }
            });

            // Tier labels and display order
            const tierConfig = [
                { value: 'market_leader', label: 'Market Leader' },
                { value: 'strong_contender', label: 'Strong Contender' },
                { value: 'competitive', label: 'Competitive' },
                { value: 'vulnerable', label: 'Vulnerable' }
            ];

            // Rebuild status filter dropdown
            const statusFilter = document.getElementById('statusFilter');
            statusFilter.innerHTML = '<option value="all">All Status</option>';

            tierConfig.forEach(tier => {
                if (availableTiers.has(tier.value)) {
                    const count = availableTiers.get(tier.value);
                    const option = document.createElement('option');
                    option.value = tier.value;
                    option.textContent = `${tier.label} (${count})`;
                    statusFilter.appendChild(option);
                }
            });
        });

        // Toggle card collapse/expand
        function toggleCard(cardId) {
            const cardBody = document.getElementById(cardId);
            const button = document.querySelector(`button[onclick="toggleCard('${cardId}')"]`);

            if (cardBody && button) {
                cardBody.classList.toggle('collapsed');
                button.classList.toggle('collapsed');
            }
        }
    </script>
</body>
</html>"""

    def generate_html_report(
        self,
        results: List[Dict[str, Any]],
        analysis_type: str = "UX Analysis",
        output_filename: str = None
    ) -> str:
        """
        Generate complete HTML report with all visualizations.

        Args:
            results: List of competitor analysis results
            analysis_type: Type of analysis performed
            output_filename: Optional custom filename

        Returns:
            Path to generated HTML file
        """
        if output_filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"competitive_intelligence_{timestamp}.html"

        # Filter successful competitors for display
        # Must have both success=True AND overall_score to be included
        successful_competitors = [r for r in results if r.get('success') and r.get('overall_score') is not None]

        # Annotate screenshots with findings
        successful_competitors = self._prepare_annotated_screenshots(successful_competitors)

        # Generate all charts
        radar_chart = self._create_radar_chart(successful_competitors)
        bar_chart = self._create_criteria_bar_chart(successful_competitors)
        heatmap = self._create_heatmap(successful_competitors)

        # Get executive summary, strategic insights, and rankings
        summary = self._get_executive_summary(successful_competitors)
        strategic_insights = self._get_strategic_insights(successful_competitors)
        rankings = self._get_rankings_data(successful_competitors)

        # Convert screenshot paths to be relative to HTML file location
        output_path = self.output_dir / output_filename
        successful_competitors = self._make_paths_relative(successful_competitors, output_path)

        # Render template
        template = Template(self._get_html_template())
        html_content = template.render(
            analysis_type=analysis_type,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            radar_chart=radar_chart,
            bar_chart=bar_chart,
            heatmap=heatmap,
            summary=summary,
            strategic_insights=strategic_insights,
            rankings=rankings,
            competitors=successful_competitors
        )

        # Save to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        return str(output_path)
