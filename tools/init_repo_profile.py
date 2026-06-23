from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from tools.install_root_agents import install_root_agents, should_install_from_env


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROFILE = ROOT / "state" / "ai_brain_repo_profile.local.json"
DEFAULT_MEMORY = ROOT / "memory" / "PROJECT_MEMORY.md"
DEFAULT_STATE = ROOT / "state" / "sdlc_state.json"
LEGACY_TARGET_DATA_DIR = ".ai-brain"
GENERATED_START = "<!-- AI_BRAIN_REPO_PROFILE_START -->"
GENERATED_END = "<!-- AI_BRAIN_REPO_PROFILE_END -->"
GITIGNORE_START = "# AI_BRAIN_LOCAL_DATA_START"
GITIGNORE_END = "# AI_BRAIN_LOCAL_DATA_END"
PROMPT_SPEC_TEMPLATE = "prompt_spec_template.md"


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def merge_block(existing: str, start: str, end: str, block: str) -> str:
    if start in existing and end in existing:
        before, rest = existing.split(start, 1)
        _, after = rest.split(end, 1)
        return before.rstrip() + "\n\n" + block.rstrip() + "\n" + after.lstrip()
    if existing.strip():
        return existing.rstrip() + "\n\n" + block
    return block


def display_path(path: Path, base: Path) -> str:
    try:
        return path.resolve().relative_to(base.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def target_data_root_for(target_root: Path, *, data_root: Path | None = None) -> Path:
    target_root = target_root.resolve()
    if data_root is not None:
        resolved = data_root.expanduser().resolve()
        if resolved == target_root / LEGACY_TARGET_DATA_DIR:
            return target_root
        return resolved
    return target_root


def local_artifact_paths(
    target_root: Path,
    *,
    data_root: Path | None = None,
) -> dict[str, Path]:
    root = target_data_root_for(target_root, data_root=data_root)
    return {
        "data_root": root,
        "profile": root / "state" / "ai_brain_repo_profile.local.json",
        "memory": root / "memory" / "PROJECT_MEMORY.md",
        "state": root / "state" / "sdlc_state.json",
        "reports": root / "state" / "reports",
        "work_specs": root / "specs" / "work",
    }


def local_file_refs(target_root: Path, *, data_root: Path | None = None) -> dict[str, str]:
    paths = local_artifact_paths(target_root, data_root=data_root)
    return {
        "data_root": display_path(paths["data_root"], target_root),
        "profile": display_path(paths["profile"], target_root),
        "memory": display_path(paths["memory"], target_root),
        "state": display_path(paths["state"], target_root),
        "reports": display_path(paths["reports"], target_root),
        "work_specs": display_path(paths["work_specs"], target_root),
    }


def run_git(root: Path, args: list[str]) -> str:
    try:
        return subprocess.check_output(
            ["git", *args],
            cwd=root,
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return ""


def detect_project_name(root: Path) -> str:
    package = read_json(root / "package.json")
    if isinstance(package.get("name"), str) and package["name"].strip():
        return str(package["name"]).strip()

    pyproject = root / "pyproject.toml"
    if pyproject.exists():
        match = re.search(r'(?m)^\s*name\s*=\s*["\']([^"\']+)["\']', pyproject.read_text(encoding="utf-8"))
        if match:
            return match.group(1).strip()

    git_root = run_git(root, ["rev-parse", "--show-toplevel"])
    if git_root:
        return Path(git_root).name
    return root.name


def package_manager(root: Path) -> str:
    if (root / "pnpm-lock.yaml").exists():
        return "pnpm"
    if (root / "yarn.lock").exists():
        return "yarn"
    if (root / "bun.lockb").exists() or (root / "bun.lock").exists():
        return "bun"
    return "npm"


def script_command(manager: str, name: str) -> str:
    if manager == "npm":
        return f"npm run {name}"
    return f"{manager} {name}"


def detect_node_commands(root: Path) -> tuple[list[str], dict[str, str]]:
    package = read_json(root / "package.json")
    scripts = package.get("scripts", {})
    if not isinstance(scripts, dict):
        return [], {}
    manager = package_manager(root)
    commands = {
        purpose: script_command(manager, purpose)
        for purpose in ["lint", "test", "build", "typecheck", "check", "dev", "start", "deploy"]
        if purpose in scripts
    }
    frameworks = []
    dependencies = {}
    for key in ["dependencies", "devDependencies"]:
        value = package.get(key, {})
        if isinstance(value, dict):
            dependencies.update(value)
    for marker, label in {
        "next": "Next.js",
        "react": "React",
        "vue": "Vue",
        "svelte": "Svelte",
        "astro": "Astro",
        "vite": "Vite",
        "express": "Express",
    }.items():
        if marker in dependencies:
            frameworks.append(label)
    return frameworks, commands


def detect_python_commands(root: Path) -> tuple[list[str], dict[str, str]]:
    if not any((root / name).exists() for name in ["pyproject.toml", "requirements.txt", "setup.py"]):
        return [], {}
    frameworks = ["Python"]
    commands: dict[str, str] = {}
    if (root / "pytest.ini").exists() or (root / "tests").exists():
        commands["test"] = "python -m pytest"
    if (root / "ruff.toml").exists() or (root / "pyproject.toml").exists():
        commands.setdefault("lint", "ruff check .")
    if (root / "mypy.ini").exists():
        commands["typecheck"] = "mypy ."
    return frameworks, commands


def detect_other_commands(root: Path) -> tuple[list[str], dict[str, str]]:
    frameworks: list[str] = []
    commands: dict[str, str] = {}
    if (root / "Cargo.toml").exists():
        frameworks.append("Rust")
        commands.update({"test": "cargo test", "build": "cargo build"})
    if (root / "go.mod").exists():
        frameworks.append("Go")
        commands.update({"test": "go test ./...", "build": "go build ./..."})
    return frameworks, commands


def detect_make_targets(root: Path) -> list[str]:
    makefile = root / "Makefile"
    if not makefile.exists():
        return []
    targets = []
    for line in makefile.read_text(encoding="utf-8").splitlines():
        match = re.match(r"^([A-Za-z0-9_.-]+):(?:\s|$)", line)
        if match and not match.group(1).startswith("."):
            targets.append(match.group(1))
    return sorted(set(targets))


def command_list(commands: dict[str, str]) -> list[dict[str, str]]:
    return [{"purpose": key, "command": value} for key, value in sorted(commands.items())]


def build_profile(
    root: Path = ROOT,
    *,
    generated_at: str | None = None,
    data_root: Path | None = None,
) -> dict[str, Any]:
    generated_at = generated_at or utc_now()
    root = root.resolve()
    node_frameworks, node_commands = detect_node_commands(root)
    python_frameworks, python_commands = detect_python_commands(root)
    other_frameworks, other_commands = detect_other_commands(root)
    commands = {**python_commands, **other_commands, **node_commands}
    git_remote = run_git(root, ["remote", "get-url", "origin"])
    git_branch = run_git(root, ["branch", "--show-current"])

    source_markers = [
        marker
        for marker in [
            "package.json",
            "pyproject.toml",
            "Cargo.toml",
            "go.mod",
            "Makefile",
            "src",
            "app",
            "pages",
            "tests",
        ]
        if (root / marker).exists()
    ]

    return {
        "mode": "ai-brain-repo-init",
        "generated_at": generated_at,
        "project_root": root.resolve().as_posix(),
        "project_name": detect_project_name(root),
        "git": {
            "branch": git_branch,
            "remote": git_remote,
        },
        "detected_stack": sorted(set(node_frameworks + python_frameworks + other_frameworks)),
        "detected_commands": command_list(commands),
        "make_targets": detect_make_targets(root),
        "source_markers": source_markers,
        "local_files": local_file_refs(root, data_root=data_root),
        "privacy": {
            "local_only": True,
            "ignored_by_git": True,
            "secrets_not_scanned_or_stored": True,
        },
    }


def render_commands(commands: list[dict[str, str]]) -> str:
    if not commands:
        return "- No standard product commands were detected yet."
    return "\n".join(
        f"- {item['purpose']}: `{item['command']}`" for item in commands
    )


def render_generated_memory_section(profile: dict[str, Any]) -> str:
    stack = ", ".join(profile["detected_stack"]) or "not detected yet"
    markers = ", ".join(profile["source_markers"]) or "not detected yet"
    return "\n".join(
        [
            GENERATED_START,
            "## AI Brain Repo Profile",
            "",
            f"- Project: {profile['project_name']}",
            f"- Generated: {profile['generated_at']}",
            f"- Root: `{profile['project_root']}`",
            f"- Detected stack: {stack}",
            f"- Source markers: {markers}",
            "- Product commands:",
            render_commands(profile["detected_commands"]),
            "",
            "This section is generated by `make init-repo`. Keep private notes",
            "outside this block; rerunning init preserves text outside the markers.",
            GENERATED_END,
            "",
        ]
    )


def merge_generated_section(existing: str, generated: str) -> str:
    if GENERATED_START in existing and GENERATED_END in existing:
        before, rest = existing.split(GENERATED_START, 1)
        _, after = rest.split(GENERATED_END, 1)
        return before.rstrip() + "\n\n" + generated.rstrip() + "\n" + after.lstrip()
    if existing.strip():
        return existing.rstrip() + "\n\n" + generated
    return "# Project Memory\n\n" + generated


def write_memory(path: Path, profile: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    path.write_text(
        merge_generated_section(existing, render_generated_memory_section(profile)),
        encoding="utf-8",
    )


def write_state(path: Path, profile: dict[str, Any]) -> None:
    state = read_json(path)
    state.update(
        {
            "project": profile["project_name"],
            "status": "initialized",
            "current_phase": state.get("current_phase", "context-recovery"),
            "repo_profile": {
                "generated_at": profile["generated_at"],
                "profile_path": profile["local_files"]["profile"],
                "detected_commands": profile["detected_commands"],
            },
        }
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    write_json(path, state)


def target_gitignore_entries(target_root: Path, data_root: Path) -> list[str]:
    target_root = target_root.resolve()
    data_root = data_root.resolve()
    if data_root == target_root:
        return [
            "memory/PROJECT_MEMORY.md",
            "memory/*.local.md",
            "state/sdlc_state.json",
            "state/ai_brain_repo_profile.local.json",
            "state/*.local.json",
            "state/reports/*.json",
            "state/reports/*.jsonl",
            "state/reports/*.html",
            "state/reports/*.log",
            "state/reports/*.md",
            "specs/*.md",
            "specs/work/*.md",
            "!specs/prompt_spec_template.md",
        ]
    return [f"{display_path(data_root, target_root)}/"]


def install_target_gitignore(target_root: Path, data_root: Path) -> dict[str, Any]:
    target_root = target_root.resolve()
    data_root = target_data_root_for(target_root, data_root=data_root)
    if target_root == ROOT or data_root == ROOT:
        return {
            "status": "SKIP",
            "mode": "target-local-data-gitignore",
            "summary": "AI Brain is the repo root; existing framework ignores apply.",
        }

    entries = target_gitignore_entries(target_root, data_root)
    block = "\n".join(
        [
            GITIGNORE_START,
            "# AI Brain target-local memory, specs, state, and reports.",
            *entries,
            GITIGNORE_END,
            "",
        ]
    )
    path = target_root / ".gitignore"
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    path.write_text(merge_block(existing, GITIGNORE_START, GITIGNORE_END, block), encoding="utf-8")
    return {
        "status": "PASS",
        "mode": "target-local-data-gitignore",
        "path": path.as_posix(),
        "entries": entries,
        "summary": "Installed or updated target repo .gitignore for AI Brain local data.",
    }


def prune_empty_dirs(start: Path, stop: Path) -> None:
    current = start
    stop = stop.resolve()
    while current.exists() and current.resolve() != stop:
        try:
            current.rmdir()
        except OSError:
            return
        current = current.parent


def move_file_if_safe(
    source: Path,
    destination: Path,
    *,
    root: Path,
    stop_root: Path,
) -> dict[str, str]:
    if not source.exists():
        return {
            "status": "SKIP",
            "source": display_path(source, root),
            "destination": display_path(destination, root),
            "summary": "Source does not exist.",
        }
    if destination.exists():
        return {
            "status": "CONFLICT",
            "source": display_path(source, root),
            "destination": display_path(destination, root),
            "summary": "Destination exists; source was left in place.",
        }
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(source.as_posix(), destination.as_posix())
    prune_empty_dirs(source.parent, stop_root)
    return {
        "status": "MOVED",
        "source": display_path(source, root),
        "destination": display_path(destination, root),
        "summary": "Moved local AI Brain data to target data home.",
    }


def migrate_dir_files(
    source_dir: Path,
    destination_dir: Path,
    *,
    root: Path,
    stop_root: Path,
) -> list[dict[str, str]]:
    if not source_dir.exists():
        return [
            {
                "status": "SKIP",
                "source": display_path(source_dir, root),
                "destination": display_path(destination_dir, root),
                "summary": "Source directory does not exist.",
            }
        ]

    results = []
    for source in sorted(path for path in source_dir.rglob("*") if path.is_file()):
        if source.name == ".gitkeep":
            continue
        destination = destination_dir / source.relative_to(source_dir)
        results.append(move_file_if_safe(source, destination, root=root, stop_root=stop_root))
    prune_empty_dirs(source_dir, stop_root)
    return results or [
        {
            "status": "SKIP",
            "source": display_path(source_dir, root),
            "destination": display_path(destination_dir, root),
            "summary": "No movable files found.",
        }
    ]


def migrate_prompt_specs(
    source_dir: Path,
    destination_spec_dir: Path,
    *,
    root: Path,
    stop_root: Path,
) -> list[dict[str, str]]:
    if not source_dir.exists():
        return [
            {
                "status": "SKIP",
                "source": display_path(source_dir, root),
                "destination": display_path(destination_spec_dir, root),
                "summary": "Source directory does not exist.",
            }
        ]

    results = []
    for source in sorted(source_dir.glob("*.md")):
        if source.name == PROMPT_SPEC_TEMPLATE:
            continue
        results.append(
            move_file_if_safe(
                source,
                destination_spec_dir / source.name,
                root=root,
                stop_root=stop_root,
            )
        )
    return results or [
        {
            "status": "SKIP",
            "source": display_path(source_dir, root),
            "destination": display_path(destination_spec_dir, root),
            "summary": "No dated local prompt specs found.",
        }
    ]


def migration_groups_for_source(
    *,
    source_root: Path,
    data_root: Path,
    target_root: Path,
    name_prefix: str,
) -> list[dict[str, Any]]:
    return [
        {
            "name": f"{name_prefix}_memory",
            "items": [
                move_file_if_safe(
                    source_root / "memory" / "PROJECT_MEMORY.md",
                    data_root / "memory" / "PROJECT_MEMORY.md",
                    root=target_root,
                    stop_root=source_root,
                )
            ],
        },
        {
            "name": f"{name_prefix}_state",
            "items": [
                move_file_if_safe(
                    source_root / "state" / "sdlc_state.json",
                    data_root / "state" / "sdlc_state.json",
                    root=target_root,
                    stop_root=source_root,
                ),
                move_file_if_safe(
                    source_root / "state" / "ai_brain_repo_profile.local.json",
                    data_root / "state" / "ai_brain_repo_profile.local.json",
                    root=target_root,
                    stop_root=source_root,
                ),
            ],
        },
        {
            "name": f"{name_prefix}_prompt_specs",
            "items": migrate_prompt_specs(
                source_root / "specs",
                data_root / "specs",
                root=target_root,
                stop_root=source_root,
            ),
        },
        {
            "name": f"{name_prefix}_work_specs",
            "items": migrate_dir_files(
                source_root / "specs" / "work",
                data_root / "specs" / "work",
                root=target_root,
                stop_root=source_root,
            ),
        },
        {
            "name": f"{name_prefix}_reports",
            "items": migrate_dir_files(
                source_root / "state" / "reports",
                data_root / "state" / "reports",
                root=target_root,
                stop_root=source_root,
            ),
        },
    ]


def migrate_nested_local_data(target_root: Path, data_root: Path) -> dict[str, Any]:
    target_root = target_root.resolve()
    data_root = target_data_root_for(target_root, data_root=data_root)
    if target_root == ROOT or data_root == ROOT:
        return {
            "status": "SKIP",
            "mode": "target-local-data-migration",
            "summary": "AI Brain is the repo root; no nested local data migration needed.",
            "items": [],
        }
    if ROOT.parent.resolve() != target_root:
        return {
            "status": "SKIP",
            "mode": "target-local-data-migration",
            "summary": "AI Brain is not directly inside the target root; no nested local data migration attempted.",
            "items": [],
        }

    item_groups = migration_groups_for_source(
        source_root=ROOT,
        data_root=data_root,
        target_root=target_root,
        name_prefix="nested_ai_brain",
    )
    legacy_data_root = target_root / LEGACY_TARGET_DATA_DIR
    if legacy_data_root.exists() and legacy_data_root.resolve() != data_root:
        item_groups.extend(
            migration_groups_for_source(
                source_root=legacy_data_root,
                data_root=data_root,
                target_root=target_root,
                name_prefix="legacy_dot_ai_brain",
            )
        )
    item_statuses = [
        item["status"]
        for group in item_groups
        for item in group["items"]
    ]
    moved_count = item_statuses.count("MOVED")
    conflict_count = item_statuses.count("CONFLICT")
    return {
        "status": "CONFLICT" if conflict_count else "PASS",
        "mode": "target-local-data-migration",
        "moved_count": moved_count,
        "conflict_count": conflict_count,
        "source_root": ROOT.as_posix(),
        "target_data_root": data_root.as_posix(),
        "summary": (
            f"Moved {moved_count} nested local AI Brain artifact(s) to target data home."
            if moved_count
            else "No nested local AI Brain artifacts needed migration."
        ),
        "items": item_groups,
    }


def write_local_files(
    profile: dict[str, Any],
    *,
    profile_path: Path = DEFAULT_PROFILE,
    memory_path: Path = DEFAULT_MEMORY,
    state_path: Path = DEFAULT_STATE,
) -> None:
    write_json(profile_path, profile)
    write_memory(memory_path, profile)
    write_state(state_path, profile)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Initialize AI Brain local repo profile, memory, and state."
    )
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--data-root", default=None)
    parser.add_argument("--profile", default=None)
    parser.add_argument("--memory", default=None)
    parser.add_argument("--state", default=None)
    parser.add_argument(
        "--skip-root-agents",
        action="store_true",
        help="Do not install or update the target repo root AGENTS.md AI Brain bridge.",
    )
    args = parser.parse_args()

    root = Path(args.root).expanduser().resolve()
    data_root = Path(args.data_root).expanduser().resolve() if args.data_root else None
    local_paths = local_artifact_paths(root, data_root=data_root)
    migration_report = migrate_nested_local_data(root, local_paths["data_root"])
    profile = build_profile(root, data_root=local_paths["data_root"])
    profile["target_data_migration"] = migration_report
    bridge_report: dict[str, Any] | None = None
    if not args.skip_root_agents and should_install_from_env(os.environ.get("INSTALL_ROOT_AGENTS")):
        bridge_report = install_root_agents(
            target_root=root,
            ai_brain_root=ROOT,
            data_root=local_paths["data_root"],
        )
    profile["root_agents_bridge"] = bridge_report or {
        "status": "SKIP",
        "summary": "Root AGENTS bridge installation was disabled.",
    }
    profile["target_gitignore"] = install_target_gitignore(root, local_paths["data_root"])
    write_local_files(
        profile,
        profile_path=Path(args.profile) if args.profile else local_paths["profile"],
        memory_path=Path(args.memory) if args.memory else local_paths["memory"],
        state_path=Path(args.state) if args.state else local_paths["state"],
    )
    print(json.dumps(profile, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
