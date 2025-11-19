"""
Configuration loader for UX analysis criteria.

EXTENSIBILITY NOTE: This module loads analysis configurations from YAML.
To add new page types or analysis criteria, simply update config.yaml
without changing this code.
"""

import yaml
from pathlib import Path
from typing import Dict, Any, List
from pydantic import BaseModel, Field


class EvaluationCriterion(BaseModel):
    """Represents a single UX evaluation criterion."""
    id: str
    name: str
    weight: int = Field(ge=1, le=10)
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


class AnalysisType(BaseModel):
    """Configuration for a specific analysis type (e.g., basket pages, product pages)."""
    name: str
    description: str
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

    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = Path(config_path)
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)

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
