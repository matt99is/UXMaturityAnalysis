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


def test_evaluation_criterion_scoring_rubric_defaults_to_none():
    """scoring_rubric is optional — criteria without one are valid."""
    from src.config_loader import EvaluationCriterion

    criterion = EvaluationCriterion(
        id="test",
        name="Test",
        weight=5.0,
        description="Test",
        evaluation_points=[],
        benchmarks=[],
    )
    assert criterion.scoring_rubric is None


def test_evaluation_criterion_accepts_scoring_rubric():
    """scoring_rubric is stored when provided."""
    from src.config_loader import EvaluationCriterion

    rubric = {
        "8-10": "Excellent",
        "5-7": "Adequate",
        "2-4": "Poor",
        "0-1": "Absent",
    }
    criterion = EvaluationCriterion(
        id="test",
        name="Test",
        weight=5.0,
        description="Test",
        evaluation_points=[],
        benchmarks=[],
        scoring_rubric=rubric,
    )
    assert criterion.scoring_rubric == rubric


def test_basket_pages_has_criterion_aligned_observation_focus():
    """basket_pages observation_focus must include express checkout evidence item."""
    config = AnalysisConfig()
    analysis = config.get_analysis_type("basket_pages")
    focus_text = " ".join(analysis.observation_focus).lower()
    assert "express" in focus_text, (
        "observation_focus must include an express checkout item so Pass 1 "
        "captures the evidence Pass 2 needs to score express_checkout"
    )


def test_basket_pages_all_criteria_have_scoring_rubric():
    """Every basket page criterion must have a scoring_rubric with all four bands."""
    config = AnalysisConfig()
    analysis = config.get_analysis_type("basket_pages")
    expected_bands = {"8-10", "5-7", "2-4", "0-1"}
    for criterion in analysis.criteria:
        assert criterion.scoring_rubric is not None, (
            f"Criterion '{criterion.id}' has no scoring_rubric"
        )
        assert set(criterion.scoring_rubric.keys()) == expected_bands, (
            f"Criterion '{criterion.id}' rubric must have bands: {expected_bands}"
        )
