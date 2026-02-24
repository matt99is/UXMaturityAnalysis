from src.config_loader import AnalysisConfig, AnalysisType


def test_analysis_type_has_observation_focus():
    """observation_focus is loaded from YAML and available on AnalysisType."""
    config = AnalysisConfig()
    analysis = config.get_analysis_type("product_pages")
    assert hasattr(analysis, "observation_focus")
    assert isinstance(analysis.observation_focus, list)
    assert len(analysis.observation_focus) > 0


def test_analysis_type_observation_focus_defaults_to_empty():
    """observation_focus defaults to empty list if not in YAML."""
    data = {
        "name": "Test",
        "description": "Test analysis",
        "navigation": {},
        "screenshot_config": {"viewports": [], "full_page": True},
        "criteria": [],
        "output_template": {},
        "interaction": {
            "requires_interaction": False,
            "mode": "headless",
            "timeout": 0,
        },
    }
    analysis = AnalysisType(**data)
    assert analysis.observation_focus == []
