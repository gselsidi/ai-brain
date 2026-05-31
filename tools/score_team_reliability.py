from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT_DIR = ROOT / "state" / "reports"
DEFAULT_OUTPUT = DEFAULT_REPORT_DIR / "team-reliability_report.json"
DEFAULT_HISTORY = DEFAULT_REPORT_DIR / "team-reliability_history.jsonl"
DEFAULT_FEEDBACK = ROOT / "state" / "team_feedback.jsonl"

REPORT_FILES = {
    "test_run": "test_report.json",
    "agent_skills_framework": "agent-skills-framework_report.json",
    "framework_drift": "implementation-drift_report.json",
    "harness_quality": "harness-quality_report.json",
}

FEEDBACK_MISSED = {"escaped_regression", "missed_regression", "process_miss"}
FEEDBACK_CAUGHT = {"caught_regression", "caught_by_tests", "caught_by_review"}
FEEDBACK_FALSE_POSITIVE = {"false_positive", "false_alarm"}
SEVERITY_PENALTY = {
    "critical": 30,
    "high": 24,
    "medium": 16,
    "low": 8,
    "info": 2,
}


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def load_report(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    if not path.exists():
        return None, "missing"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, f"invalid_json: {exc}"
    if not isinstance(payload, dict):
        return None, "invalid_shape"
    return payload, None


def status_of(report: dict[str, Any] | None) -> str:
    return str((report or {}).get("status") or "MISSING").upper()


def read_feedback(path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if not path.exists():
        return [], []
    items: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append({"line": line_number, "error": str(exc)})
            continue
        if not isinstance(item, dict):
            errors.append({"line": line_number, "error": "feedback entry must be an object"})
            continue
        items.append(item)
    return items, errors


def feedback_id(item: dict[str, Any], index: int) -> str:
    return str(item.get("id") or item.get("ticket") or f"feedback-{index}")


def severity_penalty(item: dict[str, Any]) -> int:
    severity = str(item.get("severity") or "medium").casefold()
    return SEVERITY_PENALTY.get(severity, SEVERITY_PENALTY["medium"])


def failed_tests(test_report: dict[str, Any] | None) -> int:
    if not isinstance(test_report, dict):
        return 0
    tests = test_report.get("tests")
    if isinstance(tests, list):
        return sum(1 for test in tests if isinstance(test, dict) and test.get("status") == "FAIL")
    counts = test_report.get("counts")
    if isinstance(counts, dict):
        return int(counts.get("FAIL") or counts.get("failed") or 0)
    return 0


def read_history(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    entries: list[dict[str, Any]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        try:
            item = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict):
            entries.append(item)
    return entries


def append_history(path: Path, entry: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, sort_keys=True) + "\n")


def trend(history: list[dict[str, Any]], current_score: int) -> dict[str, Any]:
    previous = history[-1] if history else None
    scores = [
        int(item.get("team_reliability_score"))
        for item in history[-9:]
        if isinstance(item.get("team_reliability_score"), int)
    ]
    scores.append(current_score)
    return {
        "history_window_size": len(scores),
        "previous_score": previous.get("team_reliability_score") if previous else None,
        "score_delta": (
            current_score - int(previous["team_reliability_score"])
            if previous and isinstance(previous.get("team_reliability_score"), int)
            else None
        ),
        "recent_average_score": round(sum(scores) / len(scores), 2) if scores else current_score,
        "total_runs_recorded_before_append": len(history),
    }


def score_reliability(
    *,
    report_dir: Path = DEFAULT_REPORT_DIR,
    feedback_path: Path = DEFAULT_FEEDBACK,
    history_path: Path = DEFAULT_HISTORY,
    append: bool = True,
) -> dict[str, Any]:
    loaded: dict[str, dict[str, Any] | None] = {}
    load_errors: dict[str, str] = {}
    for name, filename in REPORT_FILES.items():
        report, error = load_report(report_dir / filename)
        loaded[name] = report
        if error:
            load_errors[name] = error

    feedback, feedback_errors = read_feedback(feedback_path)
    history = read_history(history_path)

    evidence_quality_failures: list[dict[str, Any]] = []
    caught_regressions: list[dict[str, Any]] = []
    missed_regressions: list[dict[str, Any]] = []
    false_positives: list[dict[str, Any]] = []
    known_gaps: list[dict[str, Any]] = []

    for name in sorted(load_errors):
        evidence_quality_failures.append({"source": name, "reason": load_errors[name]})

    if failed_tests(loaded.get("test_run")):
        caught_regressions.append(
            {
                "source": "test_run",
                "failed_tests": failed_tests(loaded.get("test_run")),
                "reason": "regression_tests_failed",
            }
        )

    for name, report in loaded.items():
        if report and status_of(report) == "FAIL" and name != "test_run":
            evidence_quality_failures.append({"source": name, "reason": "evidence_gate_failed"})

    for index, item in enumerate(feedback, start=1):
        classification = str(
            item.get("classification") or item.get("outcome") or item.get("type") or ""
        ).casefold()
        normalized = {
            "id": feedback_id(item, index),
            "classification": classification or "unclassified",
            "severity": str(item.get("severity") or "medium"),
            "summary": item.get("summary") or item.get("title") or "",
        }
        if classification in FEEDBACK_MISSED:
            missed_regressions.append({**normalized, "penalty": severity_penalty(item)})
        elif classification in FEEDBACK_CAUGHT:
            caught_regressions.append({**normalized, "source": "feedback"})
        elif classification in FEEDBACK_FALSE_POSITIVE:
            false_positives.append(normalized)
        else:
            known_gaps.append(normalized)

    score = 100
    score -= 18 * len(evidence_quality_failures)
    score -= sum(item["penalty"] for item in missed_regressions)
    score -= 5 * len(false_positives)
    score += min(6, 2 * len(caught_regressions))
    score = max(0, min(100, score))

    if missed_regressions:
        classification = "missed_regression_feedback"
    elif evidence_quality_failures:
        classification = "team_reliability_issue"
    elif caught_regressions:
        classification = "caught_regression"
    else:
        classification = "healthy"

    status = (
        "PASS"
        if score >= 80 and not missed_regressions and not evidence_quality_failures and not feedback_errors
        else "FAIL"
    )

    report_statuses = {
        name: {
            "status": status_of(report),
            "path": relative(report_dir / REPORT_FILES[name]),
        }
        for name, report in loaded.items()
    }
    entry = {
        "run_id": str(uuid4()),
        "generated_at": utc_now(),
        "team_reliability_score": score,
        "run_classification": classification,
        "status": status,
        "caught_regression_count": len(caught_regressions),
        "missed_regression_count": len(missed_regressions),
        "evidence_quality_failure_count": len(evidence_quality_failures),
        "false_positive_count": len(false_positives),
    }

    if append:
        append_history(history_path, entry)

    summary = f"Team reliability {status}: score {score}/100, classification {classification}."
    if classification == "caught_regression":
        summary += " Caught regressions are credited and do not count against the team process."
    if missed_regressions:
        summary += " Escaped regression feedback needs triage and regression coverage."

    return {
        "mode": "team-reliability",
        "status": status,
        "summary": summary,
        "generated_at": entry["generated_at"],
        "report_dir": relative(report_dir),
        "feedback_path": relative(feedback_path),
        "history_path": relative(history_path),
        "team_reliability_score": score,
        "run_classification": classification,
        "report_statuses": report_statuses,
        "signals": {
            "caught_regressions": caught_regressions,
            "missed_regressions": missed_regressions,
            "evidence_quality_failures": evidence_quality_failures,
            "false_positives": false_positives,
            "known_gaps_or_unclassified_feedback": known_gaps,
            "feedback_parse_errors": feedback_errors,
        },
        "trend": trend(history, score),
        "history_entry": entry,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Score autonomous SDLC team reliability.")
    parser.add_argument("--report-dir", default=str(DEFAULT_REPORT_DIR))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--history", default=str(DEFAULT_HISTORY))
    parser.add_argument("--feedback", default=str(DEFAULT_FEEDBACK))
    parser.add_argument("--no-append", action="store_true", help="Do not append this run to history.")
    args = parser.parse_args()

    result = score_reliability(
        report_dir=Path(args.report_dir),
        feedback_path=Path(args.feedback),
        history_path=Path(args.history),
        append=not args.no_append,
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
