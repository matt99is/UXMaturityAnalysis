from pathlib import Path

from src.utils.html_report_generator import HTMLReportGenerator


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

