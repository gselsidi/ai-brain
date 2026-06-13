import json
import shlex
import sys
from pathlib import Path

from tools.check_target_drift import build_report as build_drift_report
from tools.manage_repo_work_spec import create_or_update_spec
from tools.run_target_commands import build_report as build_command_report
from tools import run_release_gate


PYTHON = shlex.quote(sys.executable)


def write_profile(path: Path, project: Path, commands: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "mode": "ai-brain-repo-init",
        "project_name": "sample-product",
        "project_root": project.as_posix(),
        "detected_commands": commands,
        "source_markers": ["package.json", "tests"],
        "local_files": {
            "profile": ".ai-brain/state/ai_brain_repo_profile.local.json",
            "memory": ".ai-brain/memory/PROJECT_MEMORY.md",
            "state": ".ai-brain/state/sdlc_state.json",
            "reports": ".ai-brain/state/reports",
            "work_specs": ".ai-brain/specs/work",
        },
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_target_commands_run_detected_repo_commands(tmp_path: Path) -> None:
    product = tmp_path / "product"
    product.mkdir()
    (product / "package.json").write_text('{"name":"sample"}', encoding="utf-8")
    (product / "tests").mkdir()
    (product / "check_cwd.py").write_text(
        "from pathlib import Path\nPath('cwd_marker.txt').write_text(Path.cwd().name)\n",
        encoding="utf-8",
    )
    (product / "deploy.py").write_text(
        "from pathlib import Path\nPath('deploy_marker.txt').write_text('deploy ran')\n",
        encoding="utf-8",
    )
    profile = tmp_path / "state" / "ai_brain_repo_profile.local.json"
    write_profile(
        profile,
        product,
        [
            {
                "purpose": "test",
                "command": f"{PYTHON} check_cwd.py",
            },
            {"purpose": "deploy", "command": f"{PYTHON} deploy.py"},
        ],
    )

    report = build_command_report(
        profile_path=profile,
        output=tmp_path / "state" / "reports" / "target-command_report.json",
        purposes={"test"},
        generated_at="2026-06-01T00:00:00+00:00",
    )

    assert report["status"] == "PASS"
    assert report["commands"][0]["purpose"] == "test"
    assert report["commands"][0]["status"] == "PASS"
    assert (product / "cwd_marker.txt").read_text(encoding="utf-8") == "product"
    assert not (product / "deploy_marker.txt").exists()


def test_target_commands_fail_when_profile_has_no_runnable_commands(tmp_path: Path) -> None:
    product = tmp_path / "product"
    product.mkdir()
    profile = tmp_path / "state" / "ai_brain_repo_profile.local.json"
    write_profile(profile, product, [{"purpose": "deploy", "command": "npm run deploy"}])

    report = build_command_report(
        profile_path=profile,
        output=tmp_path / "state" / "reports" / "target-command_report.json",
        generated_at="2026-06-01T00:00:00+00:00",
    )

    assert report["status"] == "FAIL"
    assert report["commands"] == []


def test_target_commands_fail_on_failing_repo_command(tmp_path: Path) -> None:
    product = tmp_path / "product"
    product.mkdir()
    profile = tmp_path / "state" / "ai_brain_repo_profile.local.json"
    write_profile(
        profile,
        product,
        [
            {
                "purpose": "test",
                "command": f'{PYTHON} -c "import sys; sys.exit(7)"',
            }
        ],
    )

    report = build_command_report(
        profile_path=profile,
        output=tmp_path / "state" / "reports" / "target-command_report.json",
        purposes={"test"},
        generated_at="2026-06-01T00:00:00+00:00",
    )

    assert report["status"] == "FAIL"
    assert report["commands"][0]["returncode"] == 7


def test_repo_work_spec_updates_state_and_target_drift(tmp_path: Path) -> None:
    spec = tmp_path / "specs" / "work" / "2026-06-01_add_feature.md"
    state = tmp_path / "state" / "sdlc_state.json"
    result = create_or_update_spec(
        title="add feature",
        prompt="Add the feature.",
        requirements=["Feature works"],
        changed_files=["src/app.ts"],
        docs=["README.md updated"],
        commands=["npm run test"],
        status="complete",
        path=spec,
        state_path=state,
        generated_at="2026-06-01T00:00:00+00:00",
    )

    assert result["status"] == "PASS"
    assert "Requirements Checklist" in spec.read_text(encoding="utf-8")
    state_payload = json.loads(state.read_text(encoding="utf-8"))
    assert state_payload["current_work_spec"]["path"] == spec.as_posix()

    drift = build_drift_report(
        profile_path=tmp_path / "missing-profile.json",
        state_path=state,
        output=tmp_path / "state" / "reports" / "target-drift_report.json",
        generated_at="2026-06-01T00:00:00+00:00",
    )

    assert drift["status"] == "PASS"
    assert drift["checks"]["work_spec"]["status"] == "PASS"


def test_target_drift_fails_when_detected_command_disappears(tmp_path: Path) -> None:
    product = tmp_path / "product"
    product.mkdir()
    (product / "package.json").write_text('{"name":"sample","scripts":{}}', encoding="utf-8")
    (product / "tests").mkdir()
    profile = tmp_path / "state" / "ai_brain_repo_profile.local.json"
    write_profile(profile, product, [{"purpose": "test", "command": "npm run test"}])

    report = build_drift_report(
        profile_path=profile,
        state_path=tmp_path / "state" / "sdlc_state.json",
        output=tmp_path / "state" / "reports" / "target-drift_report.json",
        generated_at="2026-06-01T00:00:00+00:00",
    )

    assert report["status"] == "FAIL"
    assert report["checks"]["profile"]["missing_commands"] == ["test"]


def test_repo_work_spec_defaults_to_target_repo_specs_work(tmp_path: Path) -> None:
    product = tmp_path / "product"
    product.mkdir()
    profile = tmp_path / "state" / "ai_brain_repo_profile.local.json"
    write_profile(profile, product, [])
    state = tmp_path / "state" / "sdlc_state.json"

    result = create_or_update_spec(
        title="repo scoped work",
        prompt="Do the work.",
        changed_files=["src/app.ts"],
        docs=["README.md reviewed"],
        commands=["npm run test"],
        profile_path=profile,
        state_path=state,
        generated_at="2026-06-01T00:00:00+00:00",
    )

    spec_path = Path(result["spec_path"])
    assert spec_path.parent == product / ".ai-brain" / "specs" / "work"
    assert spec_path.exists()


def test_release_gate_fails_when_target_commands_fail(monkeypatch, tmp_path: Path) -> None:
    def fake_command_check(name: str, command: list[str]) -> dict[str, object]:
        return {
            "name": name,
            "status": "FAIL" if name == "target_commands" else "PASS",
            "returncode": 1 if name == "target_commands" else 0,
            "command": command,
        }

    def fake_load_json(path: Path) -> dict[str, object]:
        if path.name == "team-reliability_report.json":
            return {
                "status": "PASS",
                "team_reliability_score": 100,
                "run_classification": "healthy",
            }
        return {}

    monkeypatch.setattr(run_release_gate, "command_check", fake_command_check)
    monkeypatch.setattr(run_release_gate, "load_json", fake_load_json)
    monkeypatch.setattr(run_release_gate, "text_has_status", lambda path: True)
    monkeypatch.setattr(run_release_gate, "state_definition_of_done_check", lambda path=None: {"status": "PASS"})
    monkeypatch.setattr(run_release_gate, "ROOT", tmp_path)

    report = run_release_gate.run_release_gate()

    assert report["status"] == "FAIL"
    assert report["checks"]["target_commands"] == "FAIL"
