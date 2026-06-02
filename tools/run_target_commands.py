from __future__ import annotations

import argparse
import json
import shlex
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROFILE = ROOT / "state" / "ai_brain_repo_profile.local.json"
DEFAULT_OUTPUT = ROOT / "state" / "reports" / "target-command_report.json"
DEFAULT_PURPOSES = ("lint", "typecheck", "check", "test", "build")


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def selected_commands(profile: dict[str, Any], purposes: set[str]) -> list[dict[str, str]]:
    commands = profile.get("detected_commands", [])
    if not isinstance(commands, list):
        return []
    selected = []
    for item in commands:
        if not isinstance(item, dict):
            continue
        purpose = str(item.get("purpose", "")).strip()
        command = str(item.get("command", "")).strip()
        if purpose in purposes and command:
            selected.append({"purpose": purpose, "command": command})
    return selected


def run_command(root: Path, purpose: str, command: str, timeout_seconds: int) -> dict[str, Any]:
    try:
        args = shlex.split(command)
    except ValueError as exc:
        return {
            "purpose": purpose,
            "command": command,
            "status": "FAIL",
            "returncode": None,
            "summary": f"Could not parse command: {exc}",
        }
    if not args:
        return {
            "purpose": purpose,
            "command": command,
            "status": "FAIL",
            "returncode": None,
            "summary": "Empty command.",
        }
    try:
        result = subprocess.run(
            args,
            cwd=root,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {
            "purpose": purpose,
            "command": command,
            "status": "FAIL",
            "returncode": None,
            "summary": str(exc),
        }
    return {
        "purpose": purpose,
        "command": command,
        "status": "PASS" if result.returncode == 0 else "FAIL",
        "returncode": result.returncode,
        "stdout_tail": result.stdout[-2000:],
        "stderr_tail": result.stderr[-2000:],
    }


def build_report(
    *,
    profile_path: Path = DEFAULT_PROFILE,
    output: Path = DEFAULT_OUTPUT,
    purposes: set[str] | None = None,
    timeout_seconds: int = 300,
    generated_at: str | None = None,
) -> dict[str, Any]:
    generated_at = generated_at or utc_now()
    profile = load_json(profile_path)
    if not profile:
        report = {
            "mode": "target-command",
            "status": "SKIP",
            "generated_at": generated_at,
            "summary": "No target repo profile found. Run make init-repo.",
            "commands": [],
        }
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
        return report

    root = Path(str(profile.get("project_root", ROOT))).expanduser()
    if not root.exists():
        status = "FAIL"
        commands: list[dict[str, Any]] = []
        summary = f"Target repo root does not exist: {root}"
    else:
        commands_to_run = selected_commands(profile, purposes or set(DEFAULT_PURPOSES))
        commands = [
            run_command(root, item["purpose"], item["command"], timeout_seconds)
            for item in commands_to_run
        ]
        if not commands:
            status = "FAIL"
            summary = "No target repo commands matched the requested purposes."
        else:
            status = "PASS" if all(item["status"] == "PASS" for item in commands) else "FAIL"
            summary = (
                "Target repo commands passed."
                if status == "PASS"
                else "One or more target repo commands failed."
            )

    report = {
        "mode": "target-command",
        "status": status,
        "generated_at": generated_at,
        "summary": summary,
        "profile": profile_path.as_posix(),
        "project_root": root.as_posix() if "root" in locals() else None,
        "commands": commands,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Run detected target repo commands from the AI Brain repo profile.")
    parser.add_argument("--profile", default=str(DEFAULT_PROFILE))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--purpose", action="append", default=[])
    parser.add_argument("--timeout-seconds", type=int, default=300)
    args = parser.parse_args()

    purposes = set(args.purpose) if args.purpose else set(DEFAULT_PURPOSES)
    result = build_report(
        profile_path=Path(args.profile),
        output=Path(args.output),
        purposes=purposes,
        timeout_seconds=args.timeout_seconds,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["status"] in {"PASS", "SKIP"} else 1)


if __name__ == "__main__":
    main()
