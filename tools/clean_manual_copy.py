from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

CLEAN_DIR_NAMES = {
    ".git",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "autonomous_sdlc_team.egg-info",
    "dist",
    "site",
}
CLEAN_FILE_NAMES = {".DS_Store"}
CLEAN_LOCAL_FILES = {
    Path("memory/PROJECT_MEMORY.md"),
    Path("state/ai_brain_repo_profile.local.json"),
    Path("state/sdlc_state.json"),
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


def nearest_parent_git_root(root: Path) -> Path | None:
    root = root.resolve()
    for parent in root.parents:
        git_root = run_git(parent, ["rev-parse", "--show-toplevel"])
        if git_root:
            resolved = Path(git_root).resolve()
            if resolved != root:
                return resolved
    return None


def should_clean_relative(relative: Path) -> bool:
    if relative.name in CLEAN_FILE_NAMES:
        return True
    if relative in CLEAN_LOCAL_FILES:
        return True
    if len(relative.parts) == 2 and relative.parts[0] == "specs":
        return relative.name != "prompt_spec_template.md"
    if len(relative.parts) >= 2 and relative.parts[0] == "specs" and relative.parts[1] == "work":
        return True
    if len(relative.parts) == 2 and relative.parts[0] == "memory":
        return relative.name.endswith(".local.md")
    if len(relative.parts) == 2 and relative.parts[0] == "state":
        return relative.name.endswith(".local.json")
    if len(relative.parts) >= 2 and relative.parts[0] == "state" and relative.parts[1] == "reports":
        return relative.name != ".gitkeep"
    if len(relative.parts) >= 2 and relative.parts[0] == "state" and relative.parts[1] == "agent_runs":
        return relative.name != ".gitkeep"
    return False


def iter_cleanup_paths(root: Path) -> list[Path]:
    root = root.resolve()
    paths: list[Path] = []

    for name in sorted(CLEAN_DIR_NAMES):
        direct = root / name
        if direct.exists():
            paths.append(direct)

    for path in sorted(root.rglob("*"), key=lambda item: len(item.parts), reverse=True):
        try:
            relative = path.relative_to(root)
        except ValueError:
            continue
        if any(part in CLEAN_DIR_NAMES for part in relative.parts):
            continue
        if should_clean_relative(relative):
            paths.append(path)

    return sorted(set(paths), key=lambda item: len(item.parts), reverse=True)


def remove_path(path: Path) -> None:
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    else:
        path.unlink(missing_ok=True)


def clean_manual_copy(root: Path = ROOT, *, dry_run: bool = False) -> dict[str, Any]:
    root = root.resolve()
    nested_git = root / ".git"
    parent_repo = nearest_parent_git_root(root)

    if nested_git.exists() and parent_repo is None:
        raise RuntimeError(
            "Refusing to remove .git because no parent target repo was detected. "
            "Run this only from an AI Brain folder copied inside another Git repo."
        )

    cleanup_paths = iter_cleanup_paths(root)
    removed: list[str] = []
    for path in cleanup_paths:
        relative = path.relative_to(root).as_posix()
        removed.append(relative)
        if not dry_run:
            remove_path(path)

    return {
        "status": "PASS",
        "mode": "manual-copy-clean",
        "root": root.as_posix(),
        "parent_repo": parent_repo.as_posix() if parent_repo else None,
        "dry_run": dry_run,
        "removed": removed,
        "next_steps": [
            "Run git add ai-brain from the target repo root.",
            "Commit AI Brain as normal files in the target repo.",
            "Run make -C ai-brain init-repo TARGET_ROOT=.. when you want AI Brain to profile the target repo.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Clean a manually copied AI Brain folder so it can be committed as normal files."
    )
    parser.add_argument("--root", default=str(ROOT), help="Path to the copied AI Brain folder.")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be removed.")
    args = parser.parse_args()

    report = clean_manual_copy(Path(args.root).expanduser(), dry_run=args.dry_run)
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
