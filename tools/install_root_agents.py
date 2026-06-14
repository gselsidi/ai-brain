from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BRIDGE_START = "<!-- AI_BRAIN_ROOT_BRIDGE_START -->"
BRIDGE_END = "<!-- AI_BRAIN_ROOT_BRIDGE_END -->"


def display_path(path: Path, base: Path) -> str:
    try:
        return path.relative_to(base).as_posix()
    except ValueError:
        return path.as_posix()


def target_data_root_for(target_root: Path, ai_brain_root: Path, data_root: Path | None = None) -> Path:
    target_root = target_root.resolve()
    ai_brain_root = ai_brain_root.resolve()
    if data_root is not None:
        return data_root.expanduser().resolve()
    return target_root


def render_bridge(*, target_root: Path, ai_brain_root: Path, data_root: Path | None = None) -> str:
    ai_brain_path = display_path(ai_brain_root.resolve(), target_root.resolve())
    data_root_path = display_path(
        target_data_root_for(target_root, ai_brain_root, data_root),
        target_root.resolve(),
    )
    agents_path = f"{ai_brain_path}/AGENTS.md"
    data_prefix = "" if data_root_path == "." else f"{data_root_path}/"
    memory_path = f"{data_prefix}memory/PROJECT_MEMORY.md"
    state_path = f"{data_prefix}state/ai_brain_repo_profile.local.json"
    route_tool = f"{ai_brain_path}/tools/select_agent_route.py"

    return "\n".join(
        [
            BRIDGE_START,
            "## AI Brain Workflow Bridge",
            "",
            "This repository uses AI Brain as its agent orchestration layer.",
            "",
            "Mandatory start-of-turn rule for every new user prompt in this",
            "repository:",
            "",
            f"1. Read and follow `{agents_path}` first.",
            f"2. Read `{memory_path}` if it exists.",
            f"3. Read `{state_path}` if it exists.",
            "4. Treat the user's prompt as an AI Brain routing signal before",
            "   answering or editing files.",
            f"5. Run or consult `{route_tool}` and the AI Brain routing contracts",
            "   to identify the primary division, selected framework agents,",
            "   selected specialists, deferred specialists, selected source",
            "   skills, deferred source skills, routing assumptions, and",
            "   verification gates.",
            "6. For project-work prompts, create/update the required AI Brain",
            "   spec before implementation and follow the AI Brain evidence loop.",
            "7. Do not bypass AI Brain for repo work unless the user explicitly",
            "   says not to use it.",
            "8. Treat AI Brain as the primary workflow layer unless the user",
            "   explicitly says not to use it.",
            "",
            "If AI Brain is present only as a private local helper, remove this",
            "bridge or run init with `INSTALL_ROOT_AGENTS=0`.",
            BRIDGE_END,
            "",
        ]
    )


def merge_bridge(existing: str, bridge: str) -> str:
    if BRIDGE_START in existing and BRIDGE_END in existing:
        before, rest = existing.split(BRIDGE_START, 1)
        _, after = rest.split(BRIDGE_END, 1)
        return before.rstrip() + "\n\n" + bridge.rstrip() + "\n" + after.lstrip()
    if existing.strip():
        return existing.rstrip() + "\n\n" + bridge
    return "# Repository Agent Instructions\n\n" + bridge


def install_root_agents(
    *,
    target_root: Path,
    ai_brain_root: Path = ROOT,
    data_root: Path | None = None,
    agents_path: Path | None = None,
) -> dict[str, Any]:
    target_root = target_root.resolve()
    ai_brain_root = ai_brain_root.resolve()
    agents_path = agents_path or target_root / "AGENTS.md"
    agents_path = agents_path.resolve()

    if target_root == ai_brain_root:
        return {
            "status": "SKIP",
            "mode": "root-agents-bridge",
            "summary": "Target root is the AI Brain root; existing AGENTS.md is already authoritative.",
            "path": agents_path.as_posix(),
        }

    resolved_data_root = target_data_root_for(target_root, ai_brain_root, data_root)
    bridge = render_bridge(
        target_root=target_root,
        ai_brain_root=ai_brain_root,
        data_root=resolved_data_root,
    )
    existing = agents_path.read_text(encoding="utf-8") if agents_path.exists() else ""
    next_text = merge_bridge(existing, bridge)
    agents_path.parent.mkdir(parents=True, exist_ok=True)
    agents_path.write_text(next_text, encoding="utf-8")

    return {
        "status": "PASS",
        "mode": "root-agents-bridge",
        "path": agents_path.as_posix(),
        "ai_brain_root": ai_brain_root.as_posix(),
        "data_root": resolved_data_root.as_posix(),
        "target_root": target_root.as_posix(),
        "summary": "Installed or updated the target repo root AGENTS.md AI Brain bridge.",
    }


def should_install_from_env(value: str | None) -> bool:
    if value is None:
        return True
    return value.strip().lower() not in {"0", "false", "no", "off"}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Install a target repo root AGENTS.md bridge to nested AI Brain."
    )
    parser.add_argument("--target-root", default=".")
    parser.add_argument("--ai-brain-root", default=str(ROOT))
    parser.add_argument("--data-root", default=None)
    parser.add_argument("--agents-path", default=None)
    args = parser.parse_args()

    if not should_install_from_env(os.environ.get("INSTALL_ROOT_AGENTS")):
        print(
            json.dumps(
                {
                    "status": "SKIP",
                    "mode": "root-agents-bridge",
                    "summary": "INSTALL_ROOT_AGENTS disables root AGENTS bridge installation.",
                },
                indent=2,
                sort_keys=True,
            )
        )
        return

    report = install_root_agents(
        target_root=Path(args.target_root).expanduser(),
        ai_brain_root=Path(args.ai_brain_root).expanduser(),
        data_root=Path(args.data_root).expanduser() if args.data_root else None,
        agents_path=Path(args.agents_path).expanduser() if args.agents_path else None,
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
