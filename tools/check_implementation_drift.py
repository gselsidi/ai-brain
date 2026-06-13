from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "state" / "reports" / "implementation-drift_report.json"
REQUIRED_TEST_SECTIONS = {
    "Agent Skills Framework Tests",
    "Harness Quality Tests",
    "Memory And State Tests",
    "Report Rendering Tests",
    "Team Framework Tests",
    "Team Reliability Tests",
}
ORCHESTRATOR_MARKERS = {
    "AGENTS.md": [
        "autonomous full-stack SDLC team",
        "memory/PROJECT_MEMORY.md",
        "implementation hardening",
        "requirements audit",
        "release gate",
    ],
    ".codex/agents/sdlc_orchestrator.toml": [
        "autonomous full-stack SDLC team",
        "bounded task",
        "prompt-to-agent routing",
        "division-first",
        "release evidence",
    ],
    "Makefile": ["framework-drift", "harness-check", "release-gate"],
    "docs/maintenance.md": ["framework drift", "team reliability", "release gate"],
}


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def relative(path: Path, root: Path = ROOT) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path)


def contract_artifact_check(root: Path, contract: dict[str, Any]) -> dict[str, Any]:
    artifacts = contract.get("required_artifacts", [])
    generated_missing = [
        path for path in artifacts if path.startswith("state/reports/") and not (root / path).exists()
    ]
    missing = [
        path
        for path in artifacts
        if not path.startswith("state/reports/") and not (root / path).exists()
    ]
    return {
        "status": "PASS" if not missing else "FAIL",
        "checked_count": len(artifacts),
        "generated_missing": generated_missing,
        "missing": missing,
    }


def role_prompt_check(root: Path, contract: dict[str, Any]) -> dict[str, Any]:
    role_files = contract.get("role_files", [])
    missing_files = [path for path in role_files if not (root / path).exists()]
    return {
        "status": "PASS" if not missing_files else "FAIL",
        "role_count": len(role_files),
        "missing_files": missing_files,
    }


def documentation_marker_check(root: Path, contract: dict[str, Any]) -> dict[str, Any]:
    failures = []
    for item in contract.get("required_document_markers", []):
        path = root / item["path"]
        text = path.read_text(encoding="utf-8").casefold() if path.exists() else ""
        missing = [marker for marker in item.get("markers", []) if marker.casefold() not in text]
        if missing:
            failures.append({"path": item["path"], "missing_markers": missing})
    return {"status": "PASS" if not failures else "FAIL", "failures": failures}


def orchestrator_marker_check(root: Path = ROOT) -> dict[str, Any]:
    failures = []
    for path_text, markers in ORCHESTRATOR_MARKERS.items():
        path = root / path_text
        text = path.read_text(encoding="utf-8") if path.exists() else ""
        missing = [marker for marker in markers if marker.casefold() not in text.casefold()]
        if missing:
            failures.append({"path": path_text, "missing_markers": missing})
    return {"status": "PASS" if not failures else "FAIL", "failures": failures}


def regression_evidence_check(test_report: dict[str, Any]) -> dict[str, Any]:
    tests = test_report.get("tests", [])
    sections = {str(test.get("section")) for test in tests if isinstance(test, dict)}
    missing_sections = sorted(REQUIRED_TEST_SECTIONS - sections)
    tests_without_source = [
        str(test.get("nodeid"))
        for test in tests
        if isinstance(test, dict) and not str(test.get("source", "")).strip()
    ]
    status_failures = [
        str(test.get("nodeid"))
        for test in tests
        if isinstance(test, dict) and test.get("status") not in {"PASS", "SKIP"}
    ]
    failed = bool(missing_sections or tests_without_source or status_failures)
    return {
        "status": "FAIL" if failed else "PASS",
        "test_count": len(tests),
        "missing_sections": missing_sections,
        "tests_without_source": tests_without_source[:20],
        "status_failures": status_failures[:20],
    }


def validate(
    *,
    contract: dict[str, Any] | None = None,
    test_report: dict[str, Any] | None = None,
    root: Path = ROOT,
) -> dict[str, Any]:
    if contract is None:
        contract = load_yaml(root / "contracts/team_framework.yaml")
    if test_report is None:
        test_report = load_json(root / "state/reports/test_report.json")

    checks = {
        "contract_artifacts": contract_artifact_check(root, contract),
        "role_prompts": role_prompt_check(root, contract),
        "documentation_markers": documentation_marker_check(root, contract),
        "orchestrator_markers": orchestrator_marker_check(root),
        "regression_evidence": regression_evidence_check(test_report),
    }
    status = "PASS" if all(check["status"] == "PASS" for check in checks.values()) else "FAIL"
    return {
        "mode": "framework-drift",
        "status": status,
        "generated_at": utc_now(),
        "summary": (
            "Framework drift check passed: roles, docs, memory, reports, and regression evidence are aligned."
            if status == "PASS"
            else "Framework drift check failed; inspect role prompts, docs, memory, reports, or tests."
        ),
        "contract": relative(root / "contracts/team_framework.yaml", root),
        "checks": checks,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Check drift across autonomous SDLC team roles, docs, reports, and tests.",
    )
    parser.add_argument("--report-dir", default=None)
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()

    test_report = None
    if args.report_dir:
        test_report = load_json(Path(args.report_dir) / "test_report.json")
    result = validate(test_report=test_report)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
