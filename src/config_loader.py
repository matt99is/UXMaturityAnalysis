"""
Configuration loader for UX analysis criteria.

EXTENSIBILITY NOTE: This module loads analysis configurations from YAML.
To add new page types or analysis criteria, simply update config.yaml
without changing this code.
"""

import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class EvaluationCriterion(BaseModel):
    """Represents a single UX evaluation criterion."""
    id: str
    name: str
    weight: float = Field(ge=0.1, le=10.0)
    description: str
    evaluation_points: List[str]
    benchmarks: List[str]


class ScreenshotViewport(BaseModel):
    """Viewport configuration for screenshots."""
    name: str
    width: int
    height: int


class ScreenshotConfig(BaseModel):
    """Configuration for screenshot capture."""
    viewports: List[ScreenshotViewport]
    full_page: bool = True
    capture_states: List[str] = ["initial"]


class InteractionConfig(BaseModel):
    """Configuration for human-in-the-loop interaction."""
    requires_interaction: bool = False
    mode: str = "headless"  # "visible" or "headless"
    prompt: Optional[str] = None
    timeout: int = 0  # seconds
    instructions: Optional[str] = None


class AnalysisType(BaseModel):
    """Configuration for a specific analysis type (e.g., basket pages, product pages)."""
    name: str
    description: str
    analysis_context: Optional[str] = None  # Market/domain-specific context for AI prompts
    interaction: InteractionConfig = InteractionConfig()  # Default to no interaction
    navigation: Dict[str, Any]
    screenshot_config: ScreenshotConfig
    criteria: List[EvaluationCriterion]
    output_template: Dict[str, Any]


class AnalysisConfig:
    """
    Manages analysis configuration loading and access.

    EXTENSIBILITY NOTE: This class provides a clean interface to access
    different analysis types. When adding new page types to config.yaml,
    they'll automatically be available through get_analysis_type().
    """

    def __init__(self, config_path: str = "config.yaml", criteria_config_dir: str = "criteria_config"):
        self.config_path = Path(config_path)
        self.criteria_config_dir = Path(criteria_config_dir)
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file and criteria config directory."""
        config = {}

        # Load main config.yaml if it exists (for backward compatibility)
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f) or {}

        # Load criteria configs from criteria_config directory
        if self.criteria_config_dir.exists() and self.criteria_config_dir.is_dir():
            if "analysis_types" not in config:
                config["analysis_types"] = {}

            for yaml_file in self.criteria_config_dir.glob("*.yaml"):
                analysis_type_name = yaml_file.stem  # e.g., "homepage_pages"
                with open(yaml_file, 'r') as f:
                    criteria_config = yaml.safe_load(f)

                # Process criteria to convert benchmark dicts to strings
                criteria = criteria_config.get("criteria", [])
                for criterion in criteria:
                    if "benchmarks" in criterion:
                        benchmarks = criterion["benchmarks"]
                        # Convert dict benchmarks to string format
                        converted_benchmarks = []
                        for benchmark in benchmarks:
                            if isinstance(benchmark, dict):
                                source = benchmark.get("source", "Unknown")
                                finding = benchmark.get("finding", "")
                                converted_benchmarks.append(f"{source}: {finding}")
                            else:
                                converted_benchmarks.append(str(benchmark))
                        criterion["benchmarks"] = converted_benchmarks

                # Convert criteria config to full analysis type format
                analysis_config = {
                    "name": criteria_config.get("name", analysis_type_name),
                    "description": f"Analysis for {criteria_config.get('name', analysis_type_name)}",
                    "analysis_context": criteria_config.get("analysis_context"),  # Optional context for prompts
                    "navigation": {},
                    "screenshot_config": {
                        "viewports": criteria_config.get("viewports", []),
                        "full_page": True
                    },
                    "criteria": criteria,
                    "output_template": {}
                }

                # Add interaction config if present
                if criteria_config.get("requires_interaction", False):
                    analysis_config["interaction"] = {
                        "requires_interaction": True,
                        "mode": "visible",
                        "prompt": criteria_config.get("interaction_prompt", ""),
                        "timeout": criteria_config.get("interaction_timeout", 300),
                        "instructions": "Navigate through the page as needed"
                    }
                else:
                    analysis_config["interaction"] = {
                        "requires_interaction": False,
                        "mode": "headless",
                        "timeout": 0
                    }

                # Add to config
                config["analysis_types"][analysis_type_name] = analysis_config

        if not config:
            raise FileNotFoundError(
                f"No configuration found. Checked: {self.config_path} and {self.criteria_config_dir}"
            )

        return config

    def get_analysis_type(self, analysis_type: str) -> AnalysisType:
        """
        Get configuration for a specific analysis type.

        Args:
            analysis_type: Type of analysis (e.g., 'basket_pages', 'product_pages')

        Returns:
            AnalysisType configuration

        EXTENSIBILITY NOTE: This method works with any analysis type defined
        in config.yaml, making it easy to add new page type analyses.
        """
        if "analysis_types" not in self.config:
            raise ValueError("No analysis_types found in config")

        if analysis_type not in self.config["analysis_types"]:
            available = ", ".join(self.config["analysis_types"].keys())
            raise ValueError(
                f"Analysis type '{analysis_type}' not found. "
                f"Available types: {available}"
            )

        config_data = self.config["analysis_types"][analysis_type]
        return AnalysisType(**config_data)

    def list_available_analysis_types(self) -> List[str]:
        """List all available analysis types."""
        return list(self.config.get("analysis_types", {}).keys())

    def get_criterion_by_id(self, analysis_type: str, criterion_id: str) -> EvaluationCriterion:
        """Get a specific criterion by ID."""
        analysis = self.get_analysis_type(analysis_type)
        for criterion in analysis.criteria:
            if criterion.id == criterion_id:
                return criterion
        raise ValueError(f"Criterion '{criterion_id}' not found in {analysis_type}")


if __name__ == "__main__":
    # Test configuration loading
    config = AnalysisConfig()
    print(f"Available analysis types: {config.list_available_analysis_types()}")

    basket_config = config.get_analysis_type("basket_pages")
    print(f"\nAnalysis type: {basket_config.name}")
    print(f"Number of criteria: {len(basket_config.criteria)}")
    print(f"Viewports configured: {len(basket_config.screenshot_config.viewports)}")
