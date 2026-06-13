import json
import subprocess
from pathlib import Path

from tools import run_release_gate


ROOT = Path(__file__).resolve().parents[1]


def test_memory_and_state_templates_describe_generic_team_framework() -> None:
    memory = (ROOT / "memory/PROJECT_MEMORY.template.md").read_text()
    state = json.loads((ROOT / "state/sdlc_state.template.json").read_text())
    gitignore = (ROOT / ".gitignore").read_text()

    assert "Autonomous SDLC Team Framework" in memory
    assert "no default product runtime" in memory
    assert "Project Memory Template" in memory
    assert "`/goal` workflow" in memory
    assert "provider-native" in memory
    assert "memory/PROJECT_MEMORY.md" in gitignore
    assert "state/sdlc_state.json" in gitignore
    assert "dist/" in gitignore
    assert state["project"] == "autonomous-sdlc-team"
    assert state["status"] == "template"
    assert "team_reliability" in state["last_reports"]


def test_state_definition_of_done_tracks_framework_gates() -> None:
    state = json.loads((ROOT / "state/sdlc_state.template.json").read_text())
    dod = state["definition_of_done"]

    for key in {
        "role_prompts_generic",
        "framework_map_passes",
        "framework_drift_passes",
        "harness_quality_passes",
        "goal_command_documented",
        "provider_native_goal_adapter_documented",
        "prompt_specs_required",
        "team_reliability_tracked",
        "release_gate_pass",
    }:
        assert key in dod


def test_release_gate_accepts_state_template_without_local_state(
    tmp_path: Path,
    monkeypatch,
) -> None:
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    (state_dir / "sdlc_state.template.json").write_text(
        (ROOT / "state/sdlc_state.template.json").read_text(),
        encoding="utf-8",
    )

    monkeypatch.setattr(run_release_gate, "ROOT", tmp_path)

    check = run_release_gate.state_definition_of_done_check()

    assert check["status"] == "PASS"
    assert check["mode"] == "template_only"
    assert check["path"] == "state/sdlc_state.template.json"


def test_release_gate_accepts_initialized_repo_profile_state(
    tmp_path: Path,
    monkeypatch,
) -> None:
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    (state_dir / "sdlc_state.json").write_text(
        json.dumps(
            {
                "project": "sample-product",
                "status": "initialized",
                "repo_profile": {
                    "profile_path": "state/ai_brain_repo_profile.local.json",
                    "detected_commands": [{"purpose": "test", "command": "npm run test"}],
                },
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(run_release_gate, "ROOT", tmp_path)

    check = run_release_gate.state_definition_of_done_check()

    assert check["status"] == "PASS"
    assert check["mode"] == "local_state_initialized"


def test_tracked_source_does_not_publish_workspace_identifiers() -> None:
    tracked_files = subprocess.check_output(
        ["git", "ls-files"],
        cwd=ROOT,
        text=True,
    ).splitlines()
    forbidden = {
        "gsel" + "sidi",
        "github.com/" + "gsel" + "sidi",
        "/" + "Users/",
        "Desktop/" + "AI Brain",
        "logged" + " into " + "github",
        "logged" + " into " + "chro" + "me",
        "history " + "rewrite plus " + "force " + "push",
        "Create public " + "GitHub repo",
    }

    failures: list[str] = []
    for relative_path in tracked_files:
        path = ROOT / relative_path
        if not path.exists():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        lowered = text.casefold()
        for marker in forbidden:
            if marker.casefold() in lowered:
                failures.append(f"{relative_path}: {marker}")

    assert failures == []
