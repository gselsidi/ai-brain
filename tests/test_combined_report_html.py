import json
from pathlib import Path

from tools.generate_combined_report_html import render_report


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_render_report_combines_team_framework_reports(tmp_path: Path) -> None:
    report_dir = tmp_path / "reports"
    report_dir.mkdir()
    output = report_dir / "combined_report.html"

    write_json(
        report_dir / "test_report.json",
        {
            "status": "PASS",
            "summary": "1 tests collected: 1 passed, 0 failed, 0 skipped.",
            "generated_at": "now",
            "counts": {"PASS": 1},
            "collection_errors": [],
            "tests": [
                {
                    "nodeid": "tests/test_team_framework.py::test_real_constraint",
                    "name": "test_real_constraint",
                    "section": "Team Framework Tests",
                    "file": "tests/test_team_framework.py",
                    "line": 3,
                    "status": "PASS",
                    "duration_seconds": 0.001,
                    "parameters": {},
                    "source": "def test_real_constraint():\n    assert True",
                    "failure": None,
                }
            ],
        },
    )
    for filename, summary in {
        "agent-skills-framework_report.json": "Framework map passed.",
        "implementation-drift_report.json": "Framework drift passed.",
        "harness-quality_report.json": "Harness quality passed.",
        "team-reliability_report.json": "Team reliability passed.",
        "improvement_hardening_report.json": "Hardening passed.",
        "requirements_audit_report.json": "Audit passed.",
        "release-gate_report.json": "Release passed.",
    }.items():
        write_json(report_dir / filename, {"status": "PASS", "summary": summary, "checks": {}})

    generated = render_report(report_dir, output)

    html = generated.read_text(encoding="utf-8")
    assert "Autonomous SDLC Team Report" in html
    assert "Regression Test Evidence" in html
    assert "Team Reliability" in html
    assert "Framework Drift" in html
    assert "source-code" in html
    assert "tests/test_team_framework.py::test_real_constraint" in html
    assert "def test_real_constraint" in html
