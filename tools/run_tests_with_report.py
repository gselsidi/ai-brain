from __future__ import annotations

import argparse
import inspect
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT = ROOT / "state" / "reports" / "test_report.json"


SECTION_BY_FILE = {
    "tests/test_agentic_framework_map.py": "Agent Skills Framework Tests",
    "tests/test_combined_report_html.py": "Report Rendering Tests",
    "tests/test_harness_quality_contract.py": "Harness Quality Tests",
    "tests/test_health.py": "Team Framework Tests",
    "tests/test_improvement_queue.py": "Harness Quality Tests",
    "tests/test_memory_state.py": "Memory And State Tests",
    "tests/test_repo_init.py": "Memory And State Tests",
    "tests/test_team_framework.py": "Team Framework Tests",
    "tests/test_team_reliability.py": "Team Reliability Tests",
}


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def relative_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def source_for_item(item: pytest.Item) -> str:
    obj = getattr(item, "obj", None)
    if obj is not None:
        try:
            return inspect.getsource(obj).rstrip()
        except (OSError, TypeError):
            pass

    path = Path(str(getattr(item, "path", "")))
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return ""

    location = item.location
    line_index = location[1] if len(location) > 1 else 0
    return "\n".join(lines[line_index : line_index + 20]).rstrip()


def serializable_params(item: pytest.Item) -> dict[str, str]:
    callspec = getattr(item, "callspec", None)
    if callspec is None:
        return {}
    return {str(key): repr(value) for key, value in callspec.params.items()}


def status_from_report(report: pytest.TestReport) -> str:
    if report.failed:
        return "FAIL"
    if report.skipped:
        return "SKIP"
    if report.passed and report.when == "call":
        return "PASS"
    return "NOT_RUN"


def stronger_status(current: str, candidate: str) -> str:
    priority = {"FAIL": 4, "SKIP": 3, "PASS": 2, "NOT_RUN": 1}
    return candidate if priority[candidate] > priority[current] else current


class JsonTestReportPlugin:
    def __init__(self) -> None:
        self.tests: dict[str, dict[str, Any]] = {}
        self.collection_errors: list[dict[str, Any]] = []

    def pytest_collection_modifyitems(self, items: list[pytest.Item]) -> None:
        for item in items:
            path = Path(str(getattr(item, "path", item.location[0]))).resolve()
            rel_path = relative_path(path)
            line_number = int(item.location[1]) + 1
            nodeid = item.nodeid
            self.tests[nodeid] = {
                "nodeid": nodeid,
                "name": item.name,
                "section": SECTION_BY_FILE.get(rel_path, rel_path),
                "file": rel_path,
                "line": line_number,
                "status": "NOT_RUN",
                "duration_seconds": 0,
                "parameters": serializable_params(item),
                "source": source_for_item(item),
                "failure": None,
            }

    def pytest_collectreport(self, report: pytest.CollectReport) -> None:
        if report.failed:
            self.collection_errors.append(
                {
                    "nodeid": report.nodeid,
                    "status": "FAIL",
                    "failure": str(report.longrepr),
                }
            )

    def pytest_runtest_logreport(self, report: pytest.TestReport) -> None:
        test = self.tests.get(report.nodeid)
        if test is None:
            return

        candidate = status_from_report(report)
        test["status"] = stronger_status(str(test["status"]), candidate)
        test["duration_seconds"] = round(
            float(test["duration_seconds"]) + float(report.duration),
            6,
        )
        if report.failed or report.skipped:
            test["failure"] = str(report.longrepr)

    def payload(self, exit_code: int, pytest_args: list[str]) -> dict[str, Any]:
        tests = sorted(
            self.tests.values(),
            key=lambda item: (str(item["file"]), int(item["line"]), str(item["nodeid"])),
        )
        counts = Counter(str(item["status"]) for item in tests)
        status = "PASS" if exit_code == 0 and not self.collection_errors else "FAIL"
        return {
            "mode": "pytest",
            "status": status,
            "summary": (
                f"{len(tests)} tests collected: "
                f"{counts.get('PASS', 0)} passed, "
                f"{counts.get('FAIL', 0)} failed, "
                f"{counts.get('SKIP', 0)} skipped."
            ),
            "generated_at": utc_now(),
            "pytest_args": pytest_args,
            "counts": dict(sorted(counts.items())),
            "collection_errors": self.collection_errors,
            "tests": tests,
        }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run pytest and write per-test status/source evidence.",
    )
    parser.add_argument(
        "--report-path",
        default=str(DEFAULT_REPORT),
        help="Where to write the JSON test evidence report.",
    )
    parser.add_argument(
        "pytest_args",
        nargs=argparse.REMAINDER,
        help="Optional pytest arguments. Prefix with -- to pass pytest flags.",
    )
    return parser.parse_args()


def normalize_pytest_args(args: list[str]) -> list[str]:
    if args and args[0] == "--":
        return args[1:]
    return args


def main() -> int:
    args = parse_args()
    pytest_args = normalize_pytest_args(args.pytest_args)
    plugin = JsonTestReportPlugin()
    exit_code = pytest.main(pytest_args, plugins=[plugin])

    report_path = Path(args.report_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(plugin.payload(int(exit_code), pytest_args), indent=2),
        encoding="utf-8",
    )
    print(f"Wrote {report_path}")
    return int(exit_code)


if __name__ == "__main__":
    raise SystemExit(main())
