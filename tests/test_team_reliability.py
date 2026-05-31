import json
from pathlib import Path

from tools.score_team_reliability import score_reliability


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def write_standard_reports(report_dir: Path, *, test_status: str = "PASS") -> None:
    tests = [
        {
            "nodeid": "tests/example.py::test_example",
            "section": "Team Framework Tests",
            "status": test_status,
            "source": "def test_example():\n    assert True",
        }
    ]
    write_json(report_dir / "test_report.json", {"status": test_status, "tests": tests})
    write_json(report_dir / "agent-skills-framework_report.json", {"status": "PASS"})
    write_json(report_dir / "implementation-drift_report.json", {"status": "PASS"})
    write_json(report_dir / "harness-quality_report.json", {"status": "PASS"})
    write_json(report_dir / "release-gate_report.json", {"status": "PASS"})


def test_team_reliability_scores_healthy_evidence_without_penalty(tmp_path: Path) -> None:
    report_dir = tmp_path / "reports"
    write_standard_reports(report_dir)

    report = score_reliability(
        report_dir=report_dir,
        feedback_path=tmp_path / "missing_feedback.jsonl",
        history_path=tmp_path / "history.jsonl",
        append=False,
    )

    assert report["status"] == "PASS"
    assert report["run_classification"] == "healthy"
    assert report["team_reliability_score"] == 100


def test_team_reliability_credits_regressions_caught_by_tests(tmp_path: Path) -> None:
    report_dir = tmp_path / "reports"
    write_standard_reports(report_dir, test_status="FAIL")

    report = score_reliability(
        report_dir=report_dir,
        feedback_path=tmp_path / "missing_feedback.jsonl",
        history_path=tmp_path / "history.jsonl",
        append=False,
    )

    assert report["status"] == "PASS"
    assert report["run_classification"] == "caught_regression"
    assert report["signals"]["caught_regressions"][0]["source"] == "test_run"


def test_team_reliability_penalizes_escaped_feedback(tmp_path: Path) -> None:
    report_dir = tmp_path / "reports"
    feedback_path = tmp_path / "team_feedback.jsonl"
    write_standard_reports(report_dir)
    feedback_path.write_text(
        json.dumps(
            {
                "id": "BUG-101",
                "classification": "escaped_regression",
                "severity": "high",
                "summary": "A release gap was reported after completion.",
            }
        ),
        encoding="utf-8",
    )

    report = score_reliability(
        report_dir=report_dir,
        feedback_path=feedback_path,
        history_path=tmp_path / "history.jsonl",
        append=False,
    )

    assert report["status"] == "FAIL"
    assert report["run_classification"] == "missed_regression_feedback"
    assert report["signals"]["missed_regressions"][0]["id"] == "BUG-101"


def test_team_reliability_penalizes_missing_report(tmp_path: Path) -> None:
    report_dir = tmp_path / "reports"
    write_standard_reports(report_dir)
    (report_dir / "harness-quality_report.json").unlink()

    report = score_reliability(
        report_dir=report_dir,
        feedback_path=tmp_path / "missing_feedback.jsonl",
        history_path=tmp_path / "history.jsonl",
        append=False,
    )

    assert report["status"] == "FAIL"
    assert report["run_classification"] == "team_reliability_issue"
    assert report["signals"]["evidence_quality_failures"][0]["source"] == "harness_quality"
