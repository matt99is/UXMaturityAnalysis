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


class HTMLReportGenerator:
    """
    Generates interactive HTML reports with charts and visualizations.
    """

    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

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

    def _create_score_distribution(self, results: List[Dict[str, Any]]) -> str:
        """
        Create box plot showing score distribution for each competitor.

        Args:
            results: List of competitor analysis results

        Returns:
            HTML string with embedded chart
        """
        successful_results = [r for r in results if r.get('success') and r.get('criteria_scores')]

        if not successful_results:
            return "<p class='text-muted'>No data available</p>"

        fig = go.Figure()

        for result in successful_results:
            scores = [c['score'] for c in result['criteria_scores']]
            site_name = result.get('site_name', 'Unknown')
            overall_score = result.get('overall_score', 0)

            fig.add_trace(go.Box(
                y=scores,
                name=site_name,
                boxmean='sd',
                hovertemplate='<b>%{fullData.name}</b><br>Score: %{y:.1f}<extra></extra>',
                marker=dict(size=8)
            ))

        fig.update_layout(
            title=dict(
                text="<b>Score Distribution</b><br><sub>Performance consistency across criteria</sub>",
                x=0.5,
                xanchor='center'
            ),
            yaxis_title="Score (0-10)",
            yaxis={'range': [0, 10]},
            height=450,
            showlegend=False
        )

        return fig.to_html(include_plotlyjs=False, div_id='box-plot', config={'displayModeBar': False})

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
                'failed': len(results)
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

    def _get_html_template(self) -> str:
        """
        Return HTML template string.

        Returns:
            HTML template with Bootstrap and custom styling
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
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
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
            border-bottom: 3px solid #667eea;
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
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 25px;
            border-radius: 15px;
            margin-bottom: 20px;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
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
            border-color: #667eea;
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.15);
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
            color: #667eea;
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
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
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
            border-bottom: 3px solid #667eea;
        }
        .alert-custom {
            background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%);
            border-left: 4px solid #667eea;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 25px;
        }
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
                    <li><strong>🏆 Market Leader:</strong> {{ summary.leader.name }} leads with {{ "%.1f"|format(summary.leader.score) }}/10</li>
                    {% if summary.most_consistent %}
                    <li><strong>📊 Most Consistent:</strong> {{ summary.most_consistent }} shows the most balanced performance</li>
                    {% endif %}
                    {% if summary.strongest_criterion %}
                    <li><strong>💪 Industry Strength:</strong> {{ summary.strongest_criterion }} (avg: {{ "%.1f"|format(summary.strongest_criterion_avg) }}/10)</li>
                    {% endif %}
                    {% if summary.weakest_criterion %}
                    <li><strong>⚠️ Market Vulnerability:</strong> {{ summary.weakest_criterion }} (avg: {{ "%.1f"|format(summary.weakest_criterion_avg) }}/10) - opportunity to differentiate</li>
                    {% endif %}
                </ul>
            </div>

            <!-- Charts Section -->
            <div class="row">
                <div class="col-12">
                    <h2 class="section-title"><i class="fas fa-chart-area"></i> Visual Analysis</h2>
                </div>

                <!-- Radar Chart -->
                <div class="col-12">
                    <div class="chart-container">
                        {{ radar_chart|safe }}
                    </div>
                </div>

                <!-- Heatmap -->
                <div class="col-12">
                    <div class="chart-container">
                        {{ heatmap|safe }}
                    </div>
                </div>

                <!-- Bar Chart -->
                <div class="col-12">
                    <div class="chart-container">
                        {{ bar_chart|safe }}
                    </div>
                </div>

                <!-- Score Distribution -->
                <div class="col-12">
                    <div class="chart-container">
                        {{ box_plot|safe }}
                    </div>
                </div>
            </div>

            <!-- Competitor Details -->
            <div class="row">
                <div class="col-12">
                    <h2 class="section-title"><i class="fas fa-users"></i> Competitor Profiles</h2>
                </div>

                {% for competitor in competitors %}
                {% if competitor.success %}
                <div class="col-12">
                    <div class="competitor-card">
                        <div class="competitor-header">
                            <div>
                                <div class="competitor-name">{{ competitor.site_name }}</div>
                                <small class="text-muted">{{ competitor.url }}</small>
                            </div>
                            <div class="overall-score">
                                {{ "%.1f"|format(competitor.overall_score) }}/10
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
                            <div class="screenshot-thumb">
                                <img src="{{ screenshot.filepath }}" alt="{{ screenshot.viewport_name }}" title="{{ screenshot.viewport_name|title }} ({{ screenshot.viewport.width }}x{{ screenshot.viewport.height }})">
                            </div>
                            {% endfor %}
                        </div>
                        {% endif %}
                    </div>
                </div>
                {% endif %}
                {% endfor %}
            </div>

            <!-- Footer -->
            <div class="footer">
                <p>Generated by <strong>E-commerce UX Competitive Intelligence Agent v1.2.0</strong></p>
                <p>Powered by Claude AI | Report Date: {{ timestamp }}</p>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
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

        # Generate all charts
        radar_chart = self._create_radar_chart(results)
        bar_chart = self._create_criteria_bar_chart(results)
        heatmap = self._create_heatmap(results)
        box_plot = self._create_score_distribution(results)

        # Get executive summary
        summary = self._get_executive_summary(results)

        # Filter successful competitors for display
        successful_competitors = [r for r in results if r.get('success')]

        # Render template
        template = Template(self._get_html_template())
        html_content = template.render(
            analysis_type=analysis_type,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            radar_chart=radar_chart,
            bar_chart=bar_chart,
            heatmap=heatmap,
            box_plot=box_plot,
            summary=summary,
            competitors=successful_competitors
        )

        # Save to file
        output_path = self.output_dir / output_filename
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        return str(output_path)
