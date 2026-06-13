from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "dist" / "ai-brain-dropin"

EXCLUDED_DIR_NAMES = {
    ".git",
    ".ai-brain",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "autonomous_sdlc_team.egg-info",
    "dist",
    "site",
}
EXCLUDED_FILE_NAMES = {".DS_Store"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo"}
EXCLUDED_LOCAL_FILES = {
    Path("memory/PROJECT_MEMORY.md"),
    Path("state/ai_brain_repo_profile.local.json"),
    Path("state/sdlc_state.json"),
}


def as_relative(path: Path, root: Path) -> Path:
    return path.relative_to(root)


def should_exclude(relative: Path, *, is_dir: bool) -> bool:
    parts = set(relative.parts)
    if parts & EXCLUDED_DIR_NAMES:
        return True
    if relative.name in EXCLUDED_FILE_NAMES:
        return True
    if relative.suffix in EXCLUDED_SUFFIXES:
        return True
    if relative in EXCLUDED_LOCAL_FILES:
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


def iter_export_files(root: Path) -> list[Path]:
    root = root.resolve()
    files: list[Path] = []
    for path in sorted(root.rglob("*")):
        relative = as_relative(path, root)
        if should_exclude(relative, is_dir=path.is_dir()):
            continue
        if path.is_file():
            files.append(relative)
    return files


def prepare_output(output: Path, *, clean: bool) -> None:
    output = output.resolve()
    if output == ROOT.resolve():
        raise ValueError("Refusing to export over the AI Brain source root.")
    if output.exists():
        if not clean:
            raise FileExistsError(f"{output} already exists; pass --clean to replace it.")
        shutil.rmtree(output)
    output.mkdir(parents=True, exist_ok=True)


def export_bundle(root: Path = ROOT, output: Path = DEFAULT_OUTPUT, *, clean: bool = False) -> dict[str, Any]:
    root = root.resolve()
    output = output.resolve()

    prepare_output(output, clean=clean)
    exported_files = iter_export_files(root)

    for relative in exported_files:
        source = root / relative
        destination = output / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)

    return {
        "status": "PASS",
        "source_root": root.as_posix(),
        "output": output.as_posix(),
        "file_count": len(exported_files),
        "excluded": {
            "git": ".git",
            "local_memory": "memory/PROJECT_MEMORY.md",
            "local_state": "state/sdlc_state.json",
            "local_repo_profile": "state/ai_brain_repo_profile.local.json",
            "generated_reports": "state/reports/* except .gitkeep",
            "local_specs": "specs/*.md except specs/prompt_spec_template.md",
        },
        "next_steps": [
            "Copy this exported folder into the target repository.",
            "From the copied folder, run make init-repo.",
            "Commit the copied files from the target repository.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export a clean AI Brain drop-in bundle without Git internals."
    )
    parser.add_argument("--root", default=str(ROOT), help="AI Brain source checkout.")
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT),
        help="Destination folder for the clean drop-in bundle.",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Remove an existing output folder before exporting.",
    )
    args = parser.parse_args()

    report = export_bundle(
        root=Path(args.root).expanduser(),
        output=Path(args.output).expanduser(),
        clean=args.clean,
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
