from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from tools.install_root_agents import install_root_agents, should_install_from_env


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROFILE = ROOT / "state" / "ai_brain_repo_profile.local.json"
DEFAULT_MEMORY = ROOT / "memory" / "PROJECT_MEMORY.md"
DEFAULT_STATE = ROOT / "state" / "sdlc_state.json"
GENERATED_START = "<!-- AI_BRAIN_REPO_PROFILE_START -->"
GENERATED_END = "<!-- AI_BRAIN_REPO_PROFILE_END -->"


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


def build_profile(root: Path = ROOT, *, generated_at: str | None = None) -> dict[str, Any]:
    generated_at = generated_at or utc_now()
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
        "local_files": {
            "profile": "state/ai_brain_repo_profile.local.json",
            "memory": "memory/PROJECT_MEMORY.md",
            "state": "state/sdlc_state.json",
        },
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
    parser.add_argument("--profile", default=str(DEFAULT_PROFILE))
    parser.add_argument("--memory", default=str(DEFAULT_MEMORY))
    parser.add_argument("--state", default=str(DEFAULT_STATE))
    parser.add_argument(
        "--skip-root-agents",
        action="store_true",
        help="Do not install or update the target repo root AGENTS.md AI Brain bridge.",
    )
    args = parser.parse_args()

    root = Path(args.root).expanduser().resolve()
    profile = build_profile(root)
    bridge_report: dict[str, Any] | None = None
    if not args.skip_root_agents and should_install_from_env(os.environ.get("INSTALL_ROOT_AGENTS")):
        bridge_report = install_root_agents(target_root=root, ai_brain_root=ROOT)
    profile["root_agents_bridge"] = bridge_report or {
        "status": "SKIP",
        "summary": "Root AGENTS bridge installation was disabled.",
    }
    write_local_files(
        profile,
        profile_path=Path(args.profile),
        memory_path=Path(args.memory),
        state_path=Path(args.state),
    )
    print(json.dumps(profile, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
