from __future__ import annotations

import argparse
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_STATE = ROOT / "state" / "sdlc_state.json"
DEFAULT_PROFILE = ROOT / "state" / "ai_brain_repo_profile.local.json"
DEFAULT_SPEC_DIR = ROOT / "specs" / "work"


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def today() -> str:
    return datetime.now(UTC).date().isoformat()


def slugify(value: str) -> str:
    words = re.findall(r"[a-z0-9]+", value.lower())
    return "_".join(words[:8]) or "repo_work"


def load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def normalize_items(values: list[str] | None) -> list[str]:
    return [value.strip() for value in values or [] if value.strip()]


def bullet_list(values: list[str], empty: str) -> str:
    if not values:
        return f"- {empty}"
    return "\n".join(f"- {value}" for value in values)


def target_root_from_profile(profile_path: Path = DEFAULT_PROFILE) -> Path:
    profile = load_json(profile_path)
    root = profile.get("project_root")
    if isinstance(root, str) and root.strip():
        return Path(root).expanduser()
    return ROOT


def work_spec_dir_from_profile(profile_path: Path = DEFAULT_PROFILE, root: Path | None = None) -> Path:
    profile = load_json(profile_path)
    target_root = root or target_root_from_profile(profile_path)
    local_files = profile.get("local_files", {})
    if isinstance(local_files, dict):
        work_specs = local_files.get("work_specs")
        if isinstance(work_specs, str) and work_specs.strip():
            path = Path(work_specs).expanduser()
            return path if path.is_absolute() else target_root / path
    return target_root / "specs" / "work"


def spec_path_for(title: str, spec_dir: Path | None = None, root: Path | None = None) -> Path:
    if spec_dir is None:
        spec_dir = (root or ROOT) / "specs" / "work"
    return spec_dir / f"{today()}_{slugify(title)}.md"


def render_spec(
    *,
    title: str,
    prompt: str,
    requirements: list[str],
    changed_files: list[str],
    docs: list[str],
    commands: list[str],
    status: str,
    generated_at: str,
) -> str:
    return "\n".join(
        [
            f"# Repo Work Spec: {title}",
            "",
            "## User Prompt",
            "",
            prompt or "Not recorded.",
            "",
            "## Goal",
            "",
            "Use AI Brain's SDLC workflow to make and verify repo-level changes.",
            "",
            "## Requirements Checklist",
            "",
            bullet_list(requirements, "No explicit requirements recorded yet."),
            "",
            "## Affected Artifacts",
            "",
            bullet_list(changed_files, "No changed files recorded yet."),
            "",
            "## Tests And Commands",
            "",
            bullet_list(commands, "No verification commands recorded yet."),
            "",
            "## Documentation Updates",
            "",
            bullet_list(docs, "Documentation impact not recorded yet."),
            "",
            "## Evidence",
            "",
            "- Target command report: `state/reports/target-command_report.json`",
            "- Target drift report: `state/reports/target-drift_report.json`",
            "- Release gate report: `state/reports/release-gate_report.json`",
            "",
            "## Completion Audit",
            "",
            f"- Status: {status}",
            f"- Last updated: {generated_at}",
            "- AI Brain contracts remained framework-level.",
            "- Repo-specific facts stayed in memory, state, repo profile, reports, and this work spec.",
            "",
        ]
    )


def update_state(state_path: Path, spec_path: Path, *, status: str, generated_at: str) -> None:
    state = load_json(state_path)
    state.setdefault("repo_profile", {})
    state["current_phase"] = "repo-work-spec"
    state["current_work_spec"] = {
        "path": spec_path.as_posix(),
        "status": status,
        "updated_at": generated_at,
    }
    write_json(state_path, state)


def create_or_update_spec(
    *,
    title: str,
    prompt: str = "",
    requirements: list[str] | None = None,
    changed_files: list[str] | None = None,
    docs: list[str] | None = None,
    commands: list[str] | None = None,
    status: str = "in_progress",
    path: Path | None = None,
    state_path: Path = DEFAULT_STATE,
    profile_path: Path = DEFAULT_PROFILE,
    root: Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    generated_at = generated_at or utc_now()
    target_root = root or target_root_from_profile(profile_path)
    spec_dir = work_spec_dir_from_profile(profile_path, root=target_root)
    spec_path = path or spec_path_for(title, spec_dir=spec_dir, root=target_root)
    spec_path.parent.mkdir(parents=True, exist_ok=True)
    content = render_spec(
        title=title,
        prompt=prompt,
        requirements=normalize_items(requirements),
        changed_files=normalize_items(changed_files),
        docs=normalize_items(docs),
        commands=normalize_items(commands),
        status=status,
        generated_at=generated_at,
    )
    spec_path.write_text(content, encoding="utf-8")
    update_state(state_path, spec_path, status=status, generated_at=generated_at)
    return {
        "mode": "repo-work-spec",
        "status": "PASS",
        "generated_at": generated_at,
        "summary": f"Repo work spec written to {spec_path.as_posix()}",
        "spec_path": spec_path.as_posix(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Create or update a repo-level AI Brain work spec.")
    parser.add_argument("--title", required=True)
    parser.add_argument("--prompt", default="")
    parser.add_argument("--requirement", action="append", default=[])
    parser.add_argument("--changed-file", action="append", default=[])
    parser.add_argument("--doc", action="append", default=[])
    parser.add_argument("--command", action="append", default=[])
    parser.add_argument("--status", default="in_progress")
    parser.add_argument("--path")
    parser.add_argument("--state", default=str(DEFAULT_STATE))
    parser.add_argument("--profile", default=str(DEFAULT_PROFILE))
    parser.add_argument("--root")
    args = parser.parse_args()

    result = create_or_update_spec(
        title=args.title,
        prompt=args.prompt,
        requirements=args.requirement,
        changed_files=args.changed_file,
        docs=args.doc,
        commands=args.command,
        status=args.status,
        path=Path(args.path) if args.path else None,
        state_path=Path(args.state),
        profile_path=Path(args.profile),
        root=Path(args.root).expanduser() if args.root else None,
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
