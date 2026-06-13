from __future__ import annotations

import argparse
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT_DIR = ROOT / "state" / "reports"
DEFAULT_OUTPUT = DEFAULT_REPORT_DIR / "release-gate_report.json"
DEFAULT_PROFILE = ROOT / "state" / "ai_brain_repo_profile.local.json"
DEFAULT_STATE = ROOT / "state" / "sdlc_state.json"


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


def state_definition_of_done_check(state_path: Path | None = None) -> dict[str, Any]:
    local_state = state_path or ROOT / "state/sdlc_state.json"
    template_state = ROOT / "state/sdlc_state.template.json"
    state = load_json(local_state)
    if state:
        dod = state.get("definition_of_done", {})
        if not dod and state.get("status") == "initialized" and state.get("repo_profile"):
            return {
                "status": "PASS",
                "mode": "local_state_initialized",
                "path": local_state.as_posix(),
                "summary": "Local repo profile is initialized; no completion DoD is claimed yet.",
            }
        return {
            "status": "PASS" if dod and all(dod.values()) else "FAIL",
            "mode": "local_state",
            "path": local_state.as_posix(),
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


def run_release_gate(
    *,
    report_dir: Path | None = None,
    profile_path: Path | None = None,
    state_path: Path | None = None,
) -> dict[str, Any]:
    report_dir = report_dir or ROOT / "state" / "reports"
    profile_path = profile_path or ROOT / "state" / "ai_brain_repo_profile.local.json"
    state_path = state_path or ROOT / "state" / "sdlc_state.json"
    checks: dict[str, dict[str, Any]] = {
        "lint": command_check("lint", ["ruff", "check", "team_framework", "tests", "tools"]),
        "agent_skills_framework": command_check(
            "agent_skills_framework",
            [
                "python",
                "tools/validate_agentic_framework.py",
                "--output",
                (report_dir / "agent-skills-framework_report.json").as_posix(),
            ],
        ),
        "tests": command_check(
            "tests",
            [
                "python",
                "tools/run_tests_with_report.py",
                "--report-path",
                (report_dir / "test_report.json").as_posix(),
            ],
        ),
        "framework_drift": command_check(
            "framework_drift",
            [
                "python",
                "tools/check_implementation_drift.py",
                "--report-dir",
                report_dir.as_posix(),
                "--output",
                (report_dir / "implementation-drift_report.json").as_posix(),
            ],
        ),
        "harness_quality": command_check(
            "harness_quality",
            [
                "python",
                "tools/validate_harness_quality.py",
                "--report-dir",
                report_dir.as_posix(),
                "--output",
                (report_dir / "harness-quality_report.json").as_posix(),
            ],
        ),
        "improvement_queue": command_check(
            "improvement_queue",
            [
                "python",
                "tools/run_improvement_queue.py",
                "--output",
                (report_dir / "improvement-queue_report.json").as_posix(),
            ],
        ),
        "target_commands": command_check(
            "target_commands",
            [
                "python",
                "tools/run_target_commands.py",
                "--profile",
                profile_path.as_posix(),
                "--output",
                (report_dir / "target-command_report.json").as_posix(),
            ],
        ),
        "target_drift": command_check(
            "target_drift",
            [
                "python",
                "tools/check_target_drift.py",
                "--profile",
                profile_path.as_posix(),
                "--state",
                state_path.as_posix(),
                "--output",
                (report_dir / "target-drift_report.json").as_posix(),
            ],
        ),
        "combined_report_generation": command_check(
            "combined_report_generation",
            [
                "python",
                "tools/generate_combined_report_html.py",
                "--report-dir",
                report_dir.as_posix(),
                "--output",
                (report_dir / "combined_report.html").as_posix(),
            ],
        ),
    }

    reliability = load_json(report_dir / "team-reliability_report.json")
    checks["team_reliability"] = {
        "status": "PASS"
        if reliability.get("status") == "PASS"
        and int(reliability.get("team_reliability_score", 0)) >= 80
        else "FAIL",
        "path": (report_dir / "team-reliability_report.json").as_posix(),
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

    checks["state_definition_of_done"] = state_definition_of_done_check(state_path)

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
    parser.add_argument("--report-dir", default=str(DEFAULT_REPORT_DIR))
    parser.add_argument("--profile", default=str(DEFAULT_PROFILE))
    parser.add_argument("--state", default=str(DEFAULT_STATE))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()

    result = run_release_gate(
        report_dir=Path(args.report_dir),
        profile_path=Path(args.profile),
        state_path=Path(args.state),
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
