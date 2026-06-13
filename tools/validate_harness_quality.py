from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml


ROOT_DIR = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT_DIR / "contracts" / "harness_quality_gates.yaml"
REPORT_PATH = ROOT_DIR / "state" / "reports" / "harness-quality_report.json"


def load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def load_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def relative(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT_DIR))
    except ValueError:
        return str(path)


def artifact_check(contract: dict[str, Any]) -> dict[str, Any]:
    required = contract.get("required_artifacts", [])
    generated_missing = [
        path
        for path in required
        if path.startswith("state/reports/") and not (ROOT_DIR / path).exists()
    ]
    missing = [
        path
        for path in required
        if not path.startswith("state/reports/") and not (ROOT_DIR / path).exists()
    ]
    return {
        "status": "PASS" if not missing else "FAIL",
        "missing": missing,
        "generated_missing": generated_missing,
        "checked_count": len(required),
    }


def artifact_marker_check(contract: dict[str, Any]) -> dict[str, Any]:
    failures = []
    for item in contract.get("required_artifact_markers", []):
        path = ROOT_DIR / item["path"]
        text = load_text(path).casefold()
        missing = [marker for marker in item.get("markers", []) if marker.casefold() not in text]
        if missing:
            failures.append({"path": item["path"], "missing_markers": missing})
    return {
        "status": "PASS" if not failures else "FAIL",
        "failures": failures,
    }


def test_report_check(contract: dict[str, Any], report_dir: Path | None = None) -> dict[str, Any]:
    report_spec = contract.get("required_reports", {}).get("test_report", {})
    path = (
        report_dir / Path(str(report_spec.get("path", ""))).name
        if report_dir is not None
        else ROOT_DIR / report_spec.get("path", "")
    )
    report = load_json(path)
    if report is None:
        return {"status": "FAIL", "path": relative(path), "reason": "missing_or_invalid_json"}

    tests = report.get("tests", [])
    sections = {str(test.get("section")) for test in tests if isinstance(test, dict)}
    nodeids = [str(test.get("nodeid")) for test in tests if isinstance(test, dict)]
    minimum_count = int(contract.get("minimum_test_count", 0))
    missing_sections = sorted(set(contract.get("required_test_sections", [])) - sections)
    missing_nodes = [
        fragment
        for fragment in contract.get("required_test_node_fragments", [])
        if not any(fragment in nodeid for nodeid in nodeids)
    ]
    tests_without_source = [
        str(test.get("nodeid"))
        for test in tests
        if isinstance(test, dict) and not str(test.get("source", "")).strip()
    ]
    status_errors = []
    if report_spec.get("require_status") and report.get("status") != report_spec["require_status"]:
        status_errors.append(
            {
                "expected": report_spec["require_status"],
                "actual": report.get("status"),
            }
        )

    failures = {
        "status_errors": status_errors,
        "missing_sections": missing_sections,
        "missing_required_nodes": missing_nodes,
        "tests_without_source": tests_without_source[:20],
        "below_minimum_count": len(tests) < minimum_count,
    }
    failed = (
        bool(status_errors)
        or bool(missing_sections)
        or bool(missing_nodes)
        or bool(tests_without_source)
        or len(tests) < minimum_count
    )
    return {
        "status": "FAIL" if failed else "PASS",
        "path": relative(path),
        "test_count": len(tests),
        "minimum_test_count": minimum_count,
        "sections": sorted(sections),
        "failures": failures,
    }


def combined_report_check(contract: dict[str, Any], report_dir: Path | None = None) -> dict[str, Any]:
    report_spec = contract.get("required_reports", {}).get("combined_report", {})
    path = (
        report_dir / Path(str(report_spec.get("path", ""))).name
        if report_dir is not None
        else ROOT_DIR / report_spec.get("path", "")
    )
    text = load_text(path)
    if not text:
        return {"status": "FAIL", "path": relative(path), "reason": "missing_or_empty"}
    markers = report_spec.get("markers", [])
    missing = [marker for marker in markers if marker not in text]
    return {
        "status": "PASS" if not missing else "FAIL",
        "path": relative(path),
        "missing_markers": missing,
    }


def validate(report_dir: Path | None = None) -> dict[str, Any]:
    contract = yaml.safe_load(CONTRACT_PATH.read_text(encoding="utf-8"))
    checks = {
        "artifacts": artifact_check(contract),
        "artifact_markers": artifact_marker_check(contract),
        "test_report": test_report_check(contract, report_dir=report_dir),
        "combined_report": combined_report_check(contract, report_dir=report_dir),
    }
    status = "PASS" if all(check["status"] == "PASS" for check in checks.values()) else "FAIL"
    return {
        "mode": "harness-quality",
        "status": status,
        "generated_at": datetime.now(UTC).isoformat(),
        "summary": (
            "Harness quality gates passed: layered tests, source-backed reports, docs tooling, and agent prompts are covered."
            if status == "PASS"
            else "Harness quality gates failed; inspect missing artifacts, report evidence, or agent prompt markers."
        ),
        "contract": relative(CONTRACT_PATH),
        "checks": checks,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate AI Brain harness quality gates.")
    parser.add_argument("--report-dir", default=None)
    parser.add_argument("--output", default=str(REPORT_PATH))
    args = parser.parse_args()

    result = validate(report_dir=Path(args.report_dir) if args.report_dir else None)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
