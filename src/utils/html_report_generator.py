"""
HTML Report Generator with Interactive Visualizations

Generates beautiful, interactive HTML reports with:
- Heatmaps for feature matrices
- Screenshot galleries with preview system
- Executive summaries
- Evidence tab with notable states
- Multi-page site structure
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from jinja2 import Environment, FileSystemLoader, select_autoescape
import base64
import os


def _truncate_label(text: str, max_length: int = 18) -> str:
    """Truncate label to max_length with ellipsis if needed."""
    if len(text) <= max_length:
        return text
    return text[:max_length - 2] + '…'


class HTMLReportGenerator:
    """
    Generates interactive HTML reports with charts and visualizations.

    Updated to use Jinja2 templates for the new multi-page design.
    """

    # Template directory relative to this file
    _TEMPLATES_DIR = Path(__file__).parent.parent.parent / "templates"
    # CSS directory
    _CSS_DIR = Path(__file__).parent.parent.parent / "css"

    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # Set up Jinja2 environment
        self.template_dir = self._TEMPLATES_DIR
        if self.template_dir.exists():
            self.env = Environment(
                loader=FileSystemLoader(str(self.template_dir)),
                autoescape=select_autoescape(['html', 'xml'])
            )
        else:
            # Fallback to inline templates if directory doesn't exist
            self.env = None

    def _build_css(self) -> bool:
        """
        Build CSS from Sass source files.

        Returns:
            True if CSS was built successfully, False otherwise
        """
        import subprocess

        css_output_dir = self.output_dir / 'css'
        css_output_dir.mkdir(parents=True, exist_ok=True)

        source_file = self._CSS_DIR / 'main.scss'
        output_file = css_output_dir / 'main.css'

        if not source_file.exists():
            return False

        try:
            result = subprocess.run(
                [
                    'sass',
                    str(source_file),
                    str(output_file),
                    '--style=compressed',
                    '--no-source-map',
                ],
                capture_output=True,
                timeout=30,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def _copy_css(self) -> bool:
        """
        Copy pre-built CSS files to output directory.

        Returns:
            True if CSS files were copied successfully
        """
        import shutil

        css_output_dir = self.output_dir / 'css'
        css_output_dir.mkdir(parents=True, exist_ok=True)

        source_css = self._CSS_DIR / '../output/css/main.css'
        if not source_css.exists():
            # Try building CSS first
            if not self._build_css():
                return False
            source_css = self._CSS_DIR.parent / 'output' / 'css' / 'main.css'

        if not source_css.exists():
            return False

        try:
            shutil.copy(source_css, css_output_dir / 'main.css')
            return True
        except (FileNotFoundError, shutil.Error):
            return False

    def _create_heatmap(self, results: List[Dict[str, Any]]) -> go.Figure:
        """
        Create heatmap showing feature adoption matrix.

        Args:
            results: List of competitor analysis results

        Returns:
            Plotly figure object
        """
        successful_results = [r for r in results if r.get('success') and r.get('criteria_scores')]

        if not successful_results:
            return None

        # Prepare data
        competitors = [r.get('site_name', 'Unknown') for r in successful_results]
        criteria_names = [c['criterion_name'] for c in successful_results[0]['criteria_scores']]
        criteria_display_names = [_truncate_label(name, max_length=24 if len(criteria_names) > 6 else 18) for name in criteria_names]

        # Build score matrix
        scores_matrix = []
        for result in successful_results:
            scores = [c['score'] for c in result['criteria_scores']]
            scores_matrix.append(scores)

        # Create heatmap with green-to-red scale
        # Don't display text in cells - it interferes with hover tooltip
        # Single hover template with competitor name, full criterion, and score
        hover_template = '<b>%{y}</b><br>%{x}<br>Score: %{z:.1f}/10<extra></extra>'
        fig = go.Figure(data=go.Heatmap(
            z=scores_matrix,
            x=criteria_display_names,  # Use truncated labels
            y=competitors,
            colorscale=[
                [0, '#ef4444'],      # Red (0-2)
                [0.3, '#f97316'],    # Orange (2-4)
                [0.5, '#f59e0b'],    # Amber (4-6)
                [0.7, '#84cc16'],    # Light green (6-8)
                [1, '#22c55e']       # Green (8-10)
            ],
            zmin=0,
            zmax=10,
            hovertemplate=hover_template,  # %y = competitor, %x = criterion, %z = score
            showscale=False
        ))

        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font={'family': 'Inter, sans-serif', 'size': 11, 'color': '#6b6b6b'},
            margin={'b': 140, 'l': 140, 'r': 40, 't': 50},  # Increased bottom margin
            xaxis={
                'tickfont': {'color': '#6b6b6b', 'size': 10},
                'tickangle': -45,
                'automargin': True
            },
            yaxis={
                'tickfont': {'color': '#6b6b6b', 'size': 11},
                'automargin': True
            }
        )

        return fig

    def _create_radar_chart(self, results: List[Dict[str, Any]], top_n: int = 3) -> go.Figure:
        """
        Create radar chart comparing top competitors across criteria.

        Args:
            results: List of competitor analysis results
            top_n: Number of top competitors to show

        Returns:
            Plotly figure object
        """
        successful_results = [r for r in results if r.get('success') and r.get('criteria_scores')]

        if not successful_results:
            return None

        # Get top competitors
        sorted_results = sorted(successful_results, key=lambda x: x.get('overall_score', 0), reverse=True)[:top_n]

        if not sorted_results:
            return None

        # Get criteria names - use truncated for display, full for hover
        criteria_names = [c['criterion_name'] for c in sorted_results[0]['criteria_scores']]
        criteria_display_names = [_truncate_label(name, max_length=18) for name in criteria_names]

        # Create traces for each competitor
        traces = []
        colors = ['#14b8a6', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6']

        for i, result in enumerate(sorted_results):
            scores = [c['score'] for c in result['criteria_scores']]
            # Build custom hover templates with full criteria names
            hover_templates = [
                f'<b>{result.get("site_name", "Unknown")}</b><br>{full_name}<br>Score: %{{r:.1f}}/10<extra></extra>'
                for full_name in criteria_names
            ]
            traces.append(go.Scatterpolar(
                r=scores,
                theta=criteria_display_names,  # Use truncated labels
                fill='toself',
                name=result.get('site_name', 'Unknown'),
                line={'color': colors[i % len(colors)], 'width': 2},
                hovertemplate=hover_templates  # Custom hover with full names
            ))

        fig = go.Figure(data=traces)

        fig.update_layout(
            polar={
                'radialaxis': {
                    'visible': True,
                    'range': [0, 10],
                    'gridcolor': '#2a2a2a'
                },
                'angularaxis': {
                    'rotation': 90,
                    'direction': 'clockwise',
                    'tickfont': {'size': 10, 'color': '#6b6b6b'},
                    'showline': False,
                    'showticklabels': True
                }
            },
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font={'family': 'Inter, sans-serif', 'size': 11, 'color': '#6b6b6b'},
            margin={'t': 60, 'r': 60, 'b': 120, 'l': 60},
            showlegend=True,
            legend={'bgcolor': 'rgba(0,0,0,0)', 'orientation': 'h', 'y': -0.05, 'x': 0.5, 'xanchor': 'center'}
        )

        return fig

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
                'avg_score': 0,
                'leader': {'name': 'N/A', 'score': 0},
                'weakest': {'name': 'N/A', 'score': 0}
            }

        # Find leader and weakest
        sorted_by_score = sorted(successful_results, key=lambda x: x.get('overall_score', 0), reverse=True)
        leader = sorted_by_score[0]
        weakest = sorted_by_score[-1]

        # Calculate average score
        avg_score = sum(r.get('overall_score', 0) for r in successful_results) / len(successful_results)

        return {
            'total': len(results),
            'successful': len(successful_results),
            'failed': len(results) - len(successful_results),
            'avg_score': avg_score,
            'leader': {
                'name': leader.get('site_name'),
                'score': leader.get('overall_score')
            },
            'weakest': {
                'name': weakest.get('site_name'),
                'score': weakest.get('overall_score')
            }
        }

    def _get_strategic_insights(self, results: List[Dict[str, Any]]) -> Dict[str, str]:
        """
        Generate strategic insights: market leaders, opportunities, threats.

        Args:
            results: List of competitor analysis results

        Returns:
            Dictionary with strategic insights
        """
        successful_results = [r for r in results if r.get('success') and r.get('overall_score')]

        if not successful_results:
            return {
                'market_leader': 'No data available',
                'threat': 'No data available',
                'opportunity': 'No data available'
            }

        # Market leader
        leader = max(successful_results, key=lambda x: x.get('overall_score', 0))
        leader_name = leader.get('site_name', 'Unknown')
        leader_score = leader.get('overall_score', 0)

        # Find leader's key differentiator
        best_criterion = ''
        best_score = 0
        for c in leader.get('criteria_scores', []):
            if c['score'] > best_score:
                best_score = c['score']
                best_criterion = c['criterion_name']

        # Calculate criteria averages to find opportunities
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

        # Find weakest criterion (opportunity)
        weakest_criterion = min(avg_by_criterion, key=avg_by_criterion.get) if avg_by_criterion else 'N/A'
        weakest_avg = avg_by_criterion.get(weakest_criterion, 0)

        # Find strongest criterion (threat)
        strongest_criterion = max(avg_by_criterion, key=avg_by_criterion.get) if avg_by_criterion else 'N/A'

        return {
            'market_leader': f"{leader_name} leads with {leader_score:.1f}/10. Their {best_criterion} sets the benchmark.",
            'threat': f"Market standard for {strongest_criterion} is {avg_by_criterion[strongest_criterion]:.1f}/10. Must match to compete.",
            'opportunity': f"{weakest_criterion} averages only {weakest_avg:.1f}/10 across competitors. Clear differentiation opportunity."
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

            # Determine competitive position
            if score >= 8.0:
                tier = 'Market Leader'
            elif score >= 6.5:
                tier = 'Strong Contender'
            elif score >= 5.0:
                tier = 'Competitive'
            else:
                tier = 'Needs Improvement'

            rankings.append({
                'rank': rank,
                'name': comp.get('site_name'),
                'score': score,
                'tier': tier
            })

        return rankings

    def _get_evidence_data(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate evidence tab data from notable states and observations.

        Args:
            results: List of competitor analysis results

        Returns:
            List of evidence items per competitor
        """
        successful_results = [r for r in results if r.get('success') and r.get('overall_score')]

        if not successful_results:
            return []

        # Sort by score and take top 3
        sorted_comps = sorted(successful_results, key=lambda x: x.get('overall_score', 0), reverse=True)[:3]

        evidence = []
        colors = ['#22c55e', '#22c55e', '#f59e0b']  # green, green, amber
        color_dims = ['rgba(34, 197, 94, 0.1)', 'rgba(34, 197, 94, 0.1)', 'rgba(245, 158, 11, 0.1)']

        for i, comp in enumerate(sorted_comps):
            name = comp.get('site_name', 'Unknown')
            initial = name[0].upper() if name else '?'
            score = comp.get('overall_score', 0)

            # Build evidence list from criteria scores
            evidence_list = []

            # Get top strength
            strengths = [
                c for c in comp.get('criteria_scores', [])
                if c['score'] >= 8
            ]
            if strengths:
                best = max(strengths, key=lambda x: x['score'])
                evidence_list.append({
                    'icon': 'check-circle-2',
                    'icon_class': 'success',
                    'text': f"{best['criterion_name']}: {best['score']:.1f}/10 - Best in class"
                })

            # Get notable states if available
            notable_states = comp.get('notable_states', [])
            for state in notable_states[:2]:
                # Determine icon based on content
                if any(word in state.lower() for word in ['good', 'excellent', 'clear', 'prominent']):
                    evidence_list.append({
                        'icon': 'check-circle-2',
                        'icon_class': 'success',
                        'text': state[:100]
                    })
                elif any(word in state.lower() for word in ['missing', 'lack', 'unclear', 'hidden']):
                    evidence_list.append({
                        'icon': 'alert-circle',
                        'icon_class': 'warning',
                        'text': state[:100]
                    })
                else:
                    evidence_list.append({
                        'icon': 'info',
                        'icon_class': 'info',
                        'text': state[:100]
                    })

            # Get a weakness if available
            weaknesses = [
                c for c in comp.get('criteria_scores', [])
                if c['score'] < 6
            ]
            if weaknesses and len(evidence_list) < 4:
                worst = min(weaknesses, key=lambda x: x['score'])
                evidence_list.append({
                    'icon': 'alert-circle',
                    'icon_class': 'warning',
                    'text': f"{worst['criterion_name']}: {worst['score']:.1f}/10 - Room for improvement"
                })

            evidence.append({
                'name': name,
                'initial': initial,
                'color': colors[i % len(colors)],
                'color_dim': color_dims[i % len(color_dims)],
                'evidence_list': evidence_list
            })

        return evidence

    def _prepare_competitor_data(
        self,
        results: List[Dict[str, Any]],
        output_path: Path
    ) -> List[Dict[str, Any]]:
        """
        Prepare competitor data for template rendering.

        Args:
            results: List of competitor analysis results
            output_path: Path where HTML will be saved (for relative paths)

        Returns:
            List of prepared competitor data
        """
        successful_results = [r for r in results if r.get('success') and r.get('overall_score')]

        # Attach notable states
        successful_results = self._attach_notable_states(successful_results)

        # Prepare screenshot data
        prepared_competitors = []
        screenshot_sets = {}

        for result in successful_results:
            comp_id = result.get('site_name', '').lower().replace(' ', '_').replace("'", '')

            # Prepare screenshots with relative paths
            screenshots = []
            screenshot_paths = []

            if result.get('screenshot_metadata'):
                for ss in result['screenshot_metadata']:
                    # Get relative path
                    ss_path = ss.get('filepath')
                    if ss_path:
                        try:
                            rel_path = os.path.relpath(ss_path, output_path.parent)
                            screenshots.append({
                                'path': rel_path,
                                'viewport_name': ss.get('viewport_name', 'Desktop'),
                                'annotations': self._get_annotations_for_screenshot(ss, result)
                            })
                            screenshot_paths.append(rel_path)
                        except ValueError:
                            # Different drives on Windows, skip
                            pass

            screenshot_sets[comp_id] = screenshot_paths

            prepared_competitors.append({
                'id': comp_id,
                'name': result.get('site_name'),
                'overall_score': result.get('overall_score', 0),
                'criteria_scores': result.get('criteria_scores', []),
                'screenshots': screenshots,
                'notable_states': result.get('notable_states', []),
                'evidence_items': self._build_competitor_evidence_items(result),
            })

        return prepared_competitors, screenshot_sets

    def _build_competitor_evidence_items(self, result: Dict[str, Any]) -> List[Dict[str, str]]:
        """Build compact evidence snippets for each competitor card."""
        items: List[Dict[str, str]] = []

        notable_states = result.get('notable_states', []) or []
        for state in notable_states[:2]:
            state_text = str(state).strip()
            if not state_text:
                continue

            lowered = state_text.lower()
            if any(token in lowered for token in ['missing', 'lack', 'unclear', 'hidden', 'error']):
                icon, icon_class = 'alert-circle', 'warning'
            elif any(token in lowered for token in ['good', 'excellent', 'clear', 'prominent', 'strong']):
                icon, icon_class = 'check-circle-2', 'success'
            else:
                icon, icon_class = 'info', 'info'

            items.append(
                {
                    'icon': icon,
                    'icon_class': icon_class,
                    'text': state_text[:160],
                }
            )

        criteria_scores = result.get('criteria_scores', []) or []
        strengths = [c for c in criteria_scores if c.get('score', 0) >= 8]
        weaknesses = [c for c in criteria_scores if c.get('score', 0) < 6]

        if strengths:
            best = max(strengths, key=lambda c: c.get('score', 0))
            evidence_text = best.get('evidence') or best.get('observations') or ''
            text = evidence_text.strip()[:140] if evidence_text else f"{best.get('criterion_name', 'Strength')}: {best.get('score', 0):.1f}/10"
            items.append({'icon': 'check-circle-2', 'icon_class': 'success', 'text': text})

        if weaknesses:
            worst = min(weaknesses, key=lambda c: c.get('score', 0))
            evidence_text = worst.get('evidence') or worst.get('observations') or ''
            text = evidence_text.strip()[:140] if evidence_text else f"{worst.get('criterion_name', 'Weakness')}: {worst.get('score', 0):.1f}/10"
            items.append({'icon': 'alert-circle', 'icon_class': 'warning', 'text': text})

        # Keep card concise and de-duplicate near-identical entries.
        deduped: List[Dict[str, str]] = []
        seen_text = set()
        for item in items:
            key = item['text'].strip().lower()
            if not key or key in seen_text:
                continue
            seen_text.add(key)
            deduped.append(item)
            if len(deduped) == 3:
                break

        return deduped

    def _get_annotations_for_screenshot(
        self,
        screenshot: Dict[str, Any],
        result: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Generate annotation data for a screenshot.

        Args:
            screenshot: Screenshot metadata
            result: Competitor analysis result

        Returns:
            List of annotation objects
        """
        annotations = []

        # Get strengths and weaknesses from criteria
        criteria_scores = result.get('criteria_scores', [])

        # Get top strength
        strengths = [c for c in criteria_scores if c['score'] >= 8]
        if strengths:
            best = max(strengths, key=lambda x: x['score'])
            annotations.append({
                'type': 'strength',
                'icon': 'check-circle-2',
                'text': f"{best['criterion_name']}: {best['score']:.1f}",
                'top': 20,
                'left': 30
            })

        # Get a weakness if available
        weaknesses = [c for c in criteria_scores if c['score'] < 6]
        if weaknesses:
            worst = min(weaknesses, key=lambda x: x['score'])
            annotations.append({
                'type': 'weakness',
                'icon': 'x-circle',
                'text': f"{worst['criterion_name']}: {worst['score']:.1f}",
                'top': 40,
                'left': 60
            })

        return annotations

    def _attach_notable_states(
        self,
        competitor_results: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Load notable_states from observation files into competitor payloads."""
        for result in competitor_results:
            result["notable_states"] = []
            observation_file = result.get("observation_file")
            if not observation_file:
                continue

            # Resolve relative filename against competitor_root if available
            competitor_root = result.get("competitor_root")
            if competitor_root:
                obs_path = Path(competitor_root) / observation_file
            else:
                obs_path = Path(observation_file)
            if not obs_path.exists():
                continue

            try:
                with open(obs_path, "r", encoding="utf-8") as f:
                    observation = json.load(f)

                notable_states = observation.get("notable_states", [])
                if isinstance(notable_states, list):
                    result["notable_states"] = [
                        str(state).strip()
                        for state in notable_states
                        if str(state).strip()
                    ]
            except (OSError, json.JSONDecodeError):
                continue

        return competitor_results

    def generate_index_page(
        self,
        reports: List[Dict[str, Any]]
    ) -> str:
        """
        Generate the index page listing all reports.

        Args:
            reports: List of report metadata dicts with keys:
                - filename: HTML filename
                - title: Short title for nav
                - full_title: Full title for card
                - date: Report date
                - competitors: Number of competitors
                - category: Category description
                - avg_score: Average score
                - leader_score: Leader score
                - icon: Lucide icon name
                - published: Boolean

        Returns:
            Path to generated index file
        """
        if self.env is None:
            raise RuntimeError("Template directory not found. Cannot generate index page.")

        # Build/copy CSS before rendering
        if not self._build_css():
            self._copy_css()

        template = self.env.get_template('index.html.jinja2')
        output_path = self.output_dir / 'index.html'

        html_content = template.render(
            reports=reports,
            timestamp=datetime.now().strftime("%B %d, %Y")
        )

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        return str(output_path)

    def generate_html_report(
        self,
        results: List[Dict[str, Any]],
        analysis_type: str = "UX Analysis",
        output_filename: str = None
    ) -> str:
        """
        Generate complete HTML report (legacy method for backward compatibility).

        This method maintains the old behavior for existing code.
        For new reports, use generate_report_page() instead.

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

        # Filter successful competitors
        successful_competitors = [r for r in results if r.get('success') and r.get('overall_score') is not None]

        if not successful_competitors:
            raise ValueError("No successful analysis results to generate report.")

        # Attach notable states and prepare screenshots
        successful_competitors = self._attach_notable_states(successful_competitors)

        # Generate using new template system
        return self.generate_report_page(
            results=successful_competitors,
            report_title=analysis_type,
            report_short_title=analysis_type.replace(' ', ' '),
            category="Competitive Analysis",
            output_filename=output_filename
        )

    def generate_report_page(
        self,
        results: List[Dict[str, Any]],
        report_title: str,
        report_short_title: str,
        category: str,
        output_filename: str
    ) -> str:
        """
        Generate a complete report page with all tabs and visualizations.

        Args:
            results: List of competitor analysis results
            report_title: Full title for the page
            report_short_title: Short title for breadcrumb
            category: Category description
            output_filename: Output HTML filename

        Returns:
            Path to generated HTML file
        """
        if self.env is None:
            raise RuntimeError("Template directory not found. Cannot generate report page.")

        # Build/copy CSS before rendering
        if not self._build_css():
            self._copy_css()

        template = self.env.get_template('report.html.jinja2')
        output_path = self.output_dir / output_filename

        # Prepare data
        successful_results = [r for r in results if r.get('success') and r.get('overall_score')]

        if not successful_results:
            raise ValueError("No successful analysis results to generate report.")

        # Attach notable states
        successful_results = self._attach_notable_states(successful_results)

        # Get summary and insights
        summary = self._get_executive_summary(successful_results)
        insights = self._get_strategic_insights(successful_results)
        rankings = self._get_rankings_data(successful_results)
        evidence = self._get_evidence_data(successful_results)

        # Prepare competitor data
        competitors, screenshot_sets = self._prepare_competitor_data(successful_results, output_path)

        # Create charts
        heatmap_fig = self._create_heatmap(successful_results)
        radar_fig = self._create_radar_chart(successful_results, top_n=3)

        # Convert charts to JSON for template
        import json
        radar_json = ''
        heatmap_json = ''

        # Link report pages back to the project-level output index.
        project_output_index = Path(__file__).resolve().parents[2] / 'output' / 'index.html'
        try:
            index_href = os.path.relpath(project_output_index, output_path.parent)
        except ValueError:
            index_href = 'index.html'

        if radar_fig:
            radar_json = f'''
            const radarData = {json.dumps(radar_fig.data, cls=PlotlyEncoder)};
            const radarLayout = {json.dumps(radar_fig.layout, cls=PlotlyEncoder)};
            Plotly.newPlot('radar', radarData, radarLayout, {{displayModeBar: false}});
            '''

        if heatmap_fig:
            heatmap_json = f'''
            const heatmapData = {json.dumps(heatmap_fig.data, cls=PlotlyEncoder)};
            const heatmapLayout = {json.dumps(heatmap_fig.layout, cls=PlotlyEncoder)};
            Plotly.newPlot('heatmap', heatmapData, heatmapLayout, {{displayModeBar: false}});
            '''

        # Render template
        html_content = template.render(
            report_title=report_title,
            report_short_title=report_short_title,
            category=category,
            timestamp=datetime.now().strftime("%B %d, %Y"),
            competitors=competitors,
            summary=summary,
            insights=insights,
            rankings=rankings,
            evidence=evidence,
            index_href=index_href,
            screenshot_sets_json=json.dumps(screenshot_sets),
            radar_chart_json=radar_json,
            heatmap_chart_json=heatmap_json
        )

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        return str(output_path)


class PlotlyEncoder(json.JSONEncoder):
    """Custom JSON encoder for Plotly objects."""
    def default(self, obj):
        if hasattr(obj, 'to_plotly_json'):
            return obj.to_plotly_json()
        return super().default(obj)
