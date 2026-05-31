from __future__ import annotations

import argparse
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "state" / "reports" / "release-gate_report.json"


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def command_check(name: str, command: list[str]) -> dict[str, Any]:
    result = subprocess.run(
        command,
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return {
        "name": name,
        "status": "PASS" if result.returncode == 0 else "FAIL",
        "returncode": result.returncode,
        "command": command,
        "stdout_tail": result.stdout[-2000:],
        "stderr_tail": result.stderr[-2000:],
    }


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def text_has_status(path: Path) -> bool:
    return path.exists() and "Status: PASS" in path.read_text(encoding="utf-8")


def state_definition_of_done_check() -> dict[str, Any]:
    local_state = ROOT / "state/sdlc_state.json"
    template_state = ROOT / "state/sdlc_state.template.json"
    state = load_json(local_state)
    if state:
        dod = state.get("definition_of_done", {})
        return {
            "status": "PASS" if dod and all(dod.values()) else "FAIL",
            "mode": "local_state",
            "path": "state/sdlc_state.json",
            "definition_of_done": dod,
        }

    template = load_json(template_state)
    return {
        "status": "PASS" if template else "FAIL",
        "mode": "template_only",
        "path": "state/sdlc_state.template.json",
        "summary": (
            "No local lifecycle state is present; tracked template is available."
            if template
            else "No local lifecycle state or tracked state template found."
        ),
    }


def run_release_gate() -> dict[str, Any]:
    checks: dict[str, dict[str, Any]] = {
        "lint": command_check("lint", ["ruff", "check", "team_framework", "tests", "tools"]),
        "agent_skills_framework": command_check(
            "agent_skills_framework",
            ["python", "tools/validate_agentic_framework.py"],
        ),
        "tests": command_check("tests", ["python", "tools/run_tests_with_report.py"]),
        "framework_drift": command_check(
            "framework_drift",
            ["python", "tools/check_implementation_drift.py"],
        ),
        "harness_quality": command_check(
            "harness_quality",
            ["python", "tools/validate_harness_quality.py"],
        ),
        "improvement_queue": command_check(
            "improvement_queue",
            ["python", "tools/run_improvement_queue.py"],
        ),
        "combined_report_generation": command_check(
            "combined_report_generation",
            ["python", "tools/generate_combined_report_html.py"],
        ),
    }

    reliability = load_json(ROOT / "state/reports/team-reliability_report.json")
    checks["team_reliability"] = {
        "status": "PASS"
        if reliability.get("status") == "PASS"
        and int(reliability.get("team_reliability_score", 0)) >= 80
        else "FAIL",
        "path": "state/reports/team-reliability_report.json",
        "score": reliability.get("team_reliability_score"),
        "classification": reliability.get("run_classification"),
        "summary": reliability.get("summary"),
    }
    checks["security_review"] = {
        "status": "PASS" if text_has_status(ROOT / "docs/security_review.md") else "FAIL",
        "path": "docs/security_review.md",
    }
    checks["pr_review"] = {
        "status": "PASS" if text_has_status(ROOT / "docs/pr_review.md") else "FAIL",
        "path": "docs/pr_review.md",
    }

    checks["state_definition_of_done"] = state_definition_of_done_check()

    status = "PASS" if all(check.get("status") == "PASS" for check in checks.values()) else "FAIL"
    return {
        "mode": "release-gate",
        "status": status,
        "generated_at": utc_now(),
        "checks": {name: check["status"] for name, check in checks.items()},
        "summary": (
            "Release gate passed for the autonomous SDLC team framework."
            if status == "PASS"
            else "Release gate failed for one or more framework evidence checks."
        ),
        "static_checks": checks,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the autonomous SDLC team release gate.")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()

    result = run_release_gate()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
