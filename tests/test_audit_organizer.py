import json
from pathlib import Path

from src.utils.audit_organizer import collect_audit_runs, generate_reports_index


def test_collect_audit_runs_discovers_reports_and_metadata(tmp_path: Path):
    audits_root = tmp_path / "output" / "audits"
    audit_dir = audits_root / "2026-02-24_product_pages"
    audit_dir.mkdir(parents=True)

    summary = {
        "audit_date": "2026-02-24",
        "analysis_type": "product_pages",
        "analysis_type_name": "Product Page UX",
        "total_competitors": 2,
        "successful_analyses": 2,
        "failed_analyses": 0,
        "runtime_seconds": 123.4,
    }
    (audit_dir / "_audit_summary.json").write_text(json.dumps(summary), encoding="utf-8")
    (audit_dir / "_comparison_report.md").write_text("# report", encoding="utf-8")
    (audit_dir / "2026-02-24_product_pages_report.html").write_text("<html></html>", encoding="utf-8")

    runs = collect_audit_runs(audits_root)

    assert len(runs) == 1
    run = runs[0]
    assert run["analysis_type"] == "Product Page UX"
    assert run["html_report"] == "audits/2026-02-24_product_pages/2026-02-24_product_pages_report.html"
    assert run["markdown_report"] == "audits/2026-02-24_product_pages/_comparison_report.md"
    assert run["summary_file"] == "audits/2026-02-24_product_pages/_audit_summary.json"


def test_generate_reports_index_writes_index_file(tmp_path: Path):
    output_root = tmp_path / "output"
    audits_root = output_root / "audits"
    audit_dir = audits_root / "2026-02-23_checkout_pages"
    audit_dir.mkdir(parents=True)

    (audit_dir / "_comparison_report.md").write_text("# md", encoding="utf-8")
    (audit_dir / "_comparison_report.html").write_text("<html></html>", encoding="utf-8")

    index_path = generate_reports_index(audits_root)

    assert index_path == output_root / "index.html"
    content = index_path.read_text(encoding="utf-8")
    assert "UX Analysis Reports" in content
    assert "audits/2026-02-23_checkout_pages/_comparison_report.html" in content


def test_generate_reports_index_from_output_root_includes_legacy_files(tmp_path: Path):
    output_root = tmp_path / "output"
    output_root.mkdir(parents=True)

    (output_root / "competitive_intelligence_20260224_120000.html").write_text("<html></html>", encoding="utf-8")
    (output_root / "ux_analysis_report_20260224_120000.md").write_text("# report", encoding="utf-8")
    (output_root / "ux_analysis_20260224_120000.json").write_text("{}", encoding="utf-8")

    index_path = generate_reports_index(output_root)

    assert index_path == output_root / "index.html"
    content = index_path.read_text(encoding="utf-8")
    assert "competitive_intelligence_20260224_120000.html" in content
    assert "ux_analysis_report_20260224_120000.md" in content
    assert "ux_analysis_20260224_120000.json" in content


def test_get_audits_dir_returns_audits_subdir():
    from src.utils.audit_organizer import get_audits_dir
    result = get_audits_dir("output")
    assert result.name == "audits"
    assert result.parent.name == "output"
