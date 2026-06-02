from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from tools.init_repo_profile import build_profile


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROFILE = ROOT / "state" / "ai_brain_repo_profile.local.json"
DEFAULT_STATE = ROOT / "state" / "sdlc_state.json"
DEFAULT_OUTPUT = ROOT / "state" / "reports" / "target-drift_report.json"


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def command_map(profile: dict[str, Any]) -> dict[str, str]:
    commands = profile.get("detected_commands", [])
    if not isinstance(commands, list):
        return {}
    result = {}
    for item in commands:
        if isinstance(item, dict):
            purpose = str(item.get("purpose", "")).strip()
            command = str(item.get("command", "")).strip()
            if purpose and command:
                result[purpose] = command
    return result


def profile_drift_check(profile: dict[str, Any]) -> dict[str, Any]:
    root = Path(str(profile.get("project_root", ROOT))).expanduser()
    if not root.exists():
        return {
            "status": "FAIL",
            "summary": f"Target repo root does not exist: {root}",
            "missing_commands": [],
            "changed_commands": [],
            "missing_source_markers": [],
        }
    current = build_profile(root)
    old_commands = command_map(profile)
    new_commands = command_map(current)
    missing_commands = sorted(purpose for purpose in old_commands if purpose not in new_commands)
    changed_commands = sorted(
        purpose
        for purpose, command in old_commands.items()
        if purpose in new_commands and new_commands[purpose] != command
    )
    source_markers = [str(marker) for marker in profile.get("source_markers", [])]
    missing_source_markers = sorted(marker for marker in source_markers if not (root / marker).exists())
    failed = bool(missing_commands or changed_commands or missing_source_markers)
    return {
        "status": "FAIL" if failed else "PASS",
        "summary": (
            "Target repo profile is still aligned."
            if not failed
            else "Target repo profile drift was detected."
        ),
        "missing_commands": missing_commands,
        "changed_commands": changed_commands,
        "missing_source_markers": missing_source_markers,
    }


def work_spec_check(state: dict[str, Any], root: Path = ROOT) -> dict[str, Any]:
    spec = state.get("current_work_spec", {})
    if not isinstance(spec, dict) or not spec.get("path"):
        return {
            "status": "SKIP",
            "summary": "No current repo work spec is recorded.",
        }
    path = Path(str(spec["path"]))
    if not path.is_absolute():
        path = root / path
    if not path.exists():
        return {
            "status": "FAIL",
            "summary": f"Current repo work spec is missing: {path}",
            "path": path.as_posix(),
        }
    text = path.read_text(encoding="utf-8")
    required_markers = [
        "Requirements Checklist",
        "Affected Artifacts",
        "Tests And Commands",
        "Documentation Updates",
        "Completion Audit",
    ]
    missing_markers = [marker for marker in required_markers if marker not in text]
    placeholder_markers = [
        "No changed files recorded yet.",
        "No verification commands recorded yet.",
        "Documentation impact not recorded yet.",
    ]
    placeholders = [marker for marker in placeholder_markers if marker in text]
    failed = bool(missing_markers)
    return {
        "status": "FAIL" if failed else "PASS",
        "summary": (
            "Current repo work spec is present and auditable."
            if not failed
            else "Current repo work spec is missing required sections."
        ),
        "path": path.as_posix(),
        "missing_markers": missing_markers,
        "placeholders": placeholders,
    }


def build_report(
    *,
    profile_path: Path = DEFAULT_PROFILE,
    state_path: Path = DEFAULT_STATE,
    output: Path = DEFAULT_OUTPUT,
    generated_at: str | None = None,
) -> dict[str, Any]:
    generated_at = generated_at or utc_now()
    profile = load_json(profile_path)
    state = load_json(state_path)
    if not profile:
        checks = {
            "profile": {
                "status": "SKIP",
                "summary": "No target repo profile found. Run make init-repo.",
            },
            "work_spec": work_spec_check(state),
        }
    else:
        checks = {
            "profile": profile_drift_check(profile),
            "work_spec": work_spec_check(state),
        }
    statuses = [str(check.get("status")) for check in checks.values()]
    status = "FAIL" if "FAIL" in statuses else "PASS"
    report = {
        "mode": "target-drift",
        "status": status,
        "generated_at": generated_at,
        "summary": (
            "Target repo drift checks passed."
            if status == "PASS"
            else "Target repo drift checks found blockers."
        ),
        "profile": profile_path.as_posix(),
        "state": state_path.as_posix(),
        "checks": checks,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Check target repo profile and work-spec drift.")
    parser.add_argument("--profile", default=str(DEFAULT_PROFILE))
    parser.add_argument("--state", default=str(DEFAULT_STATE))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()

    result = build_report(
        profile_path=Path(args.profile),
        state_path=Path(args.state),
        output=Path(args.output),
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
