from pathlib import Path

from src.utils.html_report_generator import HTMLReportGenerator


def _make_result(criteria_scores, overall_score=5.0):
    """Minimal result dict for testing."""
    return {
        "success": True,
        "site_name": "Test Site",
        "overall_score": overall_score,
        "criteria_scores": criteria_scores,
        "screenshot_metadata": [],
        "notable_states": [],
    }


def test_get_top_criteria_returns_vulnerabilities_sorted_ascending():
    generator = HTMLReportGenerator(output_dir="/tmp/test_out")
    result = _make_result([
        {"criterion_name": "A", "score": 1, "competitive_status": "vulnerability"},
        {"criterion_name": "B", "score": 3, "competitive_status": "vulnerability"},
        {"criterion_name": "C", "score": 2, "competitive_status": "vulnerability"},
        {"criterion_name": "D", "score": 8, "competitive_status": "strength"},
    ])
    top = generator._get_top_criteria(result, "vulnerability", top=3, ascending=True)
    assert [c["criterion_name"] for c in top] == ["A", "C", "B"]


def test_get_top_criteria_returns_strengths_sorted_descending():
    generator = HTMLReportGenerator(output_dir="/tmp/test_out")
    result = _make_result([
        {"criterion_name": "A", "score": 7, "competitive_status": "strength"},
        {"criterion_name": "B", "score": 9, "competitive_status": "strength"},
        {"criterion_name": "C", "score": 8, "competitive_status": "strength"},
    ])
    top = generator._get_top_criteria(result, "strength", top=3, ascending=False)
    assert [c["criterion_name"] for c in top] == ["B", "C", "A"]


def test_get_top_criteria_respects_top_limit():
    generator = HTMLReportGenerator(output_dir="/tmp/test_out")
    result = _make_result([
        {"criterion_name": str(i), "score": i, "competitive_status": "vulnerability"}
        for i in range(6)
    ])
    top = generator._get_top_criteria(result, "vulnerability", top=3, ascending=True)
    assert len(top) == 3


def test_get_top_criteria_falls_back_to_score_threshold_for_strength():
    generator = HTMLReportGenerator(output_dir="/tmp/test_out")
    result = _make_result([
        {"criterion_name": "High", "score": 8},
        {"criterion_name": "Mid", "score": 5},
        {"criterion_name": "Low", "score": 2},
    ])
    top = generator._get_top_criteria(result, "strength", top=3, ascending=False)
    assert top[0]["criterion_name"] == "High"


def test_prepare_competitor_data_includes_top_strengths_and_vulnerabilities(tmp_path):
    generator = HTMLReportGenerator(output_dir=str(tmp_path / "output"))
    output_path = tmp_path / "output" / "report.html"
    result = _make_result([
        {"criterion_name": "Strong A", "score": 9, "competitive_status": "strength"},
        {"criterion_name": "Weak A",   "score": 1, "competitive_status": "vulnerability"},
        {"criterion_name": "Weak B",   "score": 2, "competitive_status": "vulnerability"},
    ])
    competitors, _ = generator._prepare_competitor_data([result], output_path)
    comp = competitors[0]
    assert "top_strengths" in comp
    assert "top_vulnerabilities" in comp
    assert comp["top_strengths"][0]["criterion_name"] == "Strong A"
    assert comp["top_vulnerabilities"][0]["criterion_name"] == "Weak A"


def test_get_top_criteria_falls_back_to_score_threshold_for_vulnerability():
    generator = HTMLReportGenerator(output_dir="/tmp/test_out")
    result = _make_result([
        {"criterion_name": "High", "score": 8},
        {"criterion_name": "Low", "score": 3},
        {"criterion_name": "Mid", "score": 5},
    ])
    top = generator._get_top_criteria(result, "vulnerability", top=3, ascending=True)
    assert top[0]["criterion_name"] == "Low"


def test_build_evidence_items_does_not_truncate_text():
    generator = HTMLReportGenerator(output_dir="/tmp/test_out")
    long_evidence = "x" * 500
    result = _make_result([
        {"criterion_name": "Weak", "score": 1, "competitive_status": "vulnerability",
         "evidence": long_evidence, "observations": ""},
    ])
    items = generator._build_competitor_evidence_items(result)
    assert any(item["text"] == long_evidence for item in items)


def test_build_evidence_items_includes_criterion_name():
    generator = HTMLReportGenerator(output_dir="/tmp/test_out")
    result = _make_result([
        {"criterion_name": "Shipping Cost", "score": 1, "competitive_status": "vulnerability",
         "evidence": "No free delivery threshold shown.", "observations": ""},
    ])
    items = generator._build_competitor_evidence_items(result)
    assert any(item["criterion_name"] == "Shipping Cost" for item in items)


def test_build_evidence_items_includes_competitive_status():
    generator = HTMLReportGenerator(output_dir="/tmp/test_out")
    result = _make_result([
        {"criterion_name": "Checkout CTA", "score": 8, "competitive_status": "strength",
         "evidence": "Clear CTA with strong contrast.", "observations": ""},
    ])
    items = generator._build_competitor_evidence_items(result)
    assert any(item["competitive_status"] == "strength" for item in items)


def test_build_evidence_items_selects_worst_vuln_best_strength_second_vuln():
    generator = HTMLReportGenerator(output_dir="/tmp/test_out")
    result = _make_result([
        {"criterion_name": "Vuln1", "score": 1, "competitive_status": "vulnerability",
         "evidence": "v1 evidence", "observations": ""},
        {"criterion_name": "Vuln2", "score": 2, "competitive_status": "vulnerability",
         "evidence": "v2 evidence", "observations": ""},
        {"criterion_name": "Strength1", "score": 9, "competitive_status": "strength",
         "evidence": "s1 evidence", "observations": ""},
    ])
    items = generator._build_competitor_evidence_items(result)
    names = [i["criterion_name"] for i in items]
    assert names[0] == "Vuln1"
    assert names[1] == "Strength1"
    assert names[2] == "Vuln2"


def test_prepare_competitor_data_uses_raw_filepath_over_annotated(tmp_path: Path):
    raw_screenshot = tmp_path / "screenshots" / "desktop.png"
    annotated_screenshot = tmp_path / "screenshots" / "desktop_annotated.png"
    raw_screenshot.parent.mkdir(parents=True)
    raw_screenshot.write_bytes(b"")
    annotated_screenshot.write_bytes(b"")

    results = [
        {
            "success": True,
            "site_name": "Demo Site",
            "overall_score": 7.2,
            "criteria_scores": [
                {"criterion_name": "Navigation", "score": 8.4},
                {"criterion_name": "Checkout", "score": 5.2},
            ],
            "screenshot_metadata": [
                {
                    "filepath": str(raw_screenshot),
                    "annotated_filepath": str(annotated_screenshot),
                    "viewport_name": "Desktop",
                }
            ],
            "notable_states": [],
        }
    ]

    generator = HTMLReportGenerator(output_dir=str(tmp_path / "output"))
    output_path = tmp_path / "output" / "demo_report.html"

    competitors, screenshot_sets = generator._prepare_competitor_data(results, output_path)

    assert len(competitors) == 1
    screenshot_path = competitors[0]["screenshots"][0]["path"]
    assert screenshot_path.endswith("desktop.png")
    assert "annotated" not in screenshot_path
    assert screenshot_sets[competitors[0]["id"]][0] == screenshot_path

