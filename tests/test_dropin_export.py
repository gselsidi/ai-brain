from pathlib import Path

from tools.export_dropin_bundle import export_bundle


def write(path: Path, text: str = "x") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_dropin_export_excludes_git_and_local_artifacts(tmp_path: Path) -> None:
    source = tmp_path / "ai-brain-source"
    output = tmp_path / "ai-brain-dropin"

    write(source / ".git" / "config", "private git metadata")
    write(source / ".venv" / "pyvenv.cfg", "local venv")
    try:
        (source / ".venv" / "python").symlink_to(Path("/usr/bin/python3"))
    except OSError:
        write(source / ".venv" / "python", "local python")
    write(source / "README.md", "# AI Brain")
    write(source / "AGENTS.md", "# Agents")
    write(source / ".codex" / "agents" / "sdlc_orchestrator.toml", "name = 'sdlc_orchestrator'")
    write(source / "tools" / "init_repo_profile.py", "print('init')")
    write(source / "specs" / "prompt_spec_template.md", "# Template")
    write(source / "specs" / "2026-06-13_local_work.md", "# Local Spec")
    write(source / "specs" / "work" / "2026-06-13_target.md", "# Target Work")
    write(source / "memory" / "PROJECT_MEMORY.template.md", "# Template")
    write(source / "memory" / "PROJECT_MEMORY.md", "# Local Memory")
    write(source / "state" / "sdlc_state.template.json", "{}")
    write(source / "state" / "sdlc_state.json", "{}")
    write(source / "state" / "ai_brain_repo_profile.local.json", "{}")
    write(source / "state" / "reports" / ".gitkeep", "")
    write(source / "state" / "reports" / "test_report.json", "{}")

    report = export_bundle(source, output, clean=False)

    assert report["status"] == "PASS"
    assert (output / "README.md").exists()
    assert (output / "AGENTS.md").exists()
    assert (output / ".codex" / "agents" / "sdlc_orchestrator.toml").exists()
    assert (output / "tools" / "init_repo_profile.py").exists()
    assert (output / "specs" / "prompt_spec_template.md").exists()
    assert (output / "memory" / "PROJECT_MEMORY.template.md").exists()
    assert (output / "state" / "sdlc_state.template.json").exists()
    assert (output / "state" / "reports" / ".gitkeep").exists()

    assert not (output / ".git").exists()
    assert not (output / ".venv").exists()
    assert not (output / "specs" / "2026-06-13_local_work.md").exists()
    assert not (output / "specs" / "work").exists()
    assert not (output / "memory" / "PROJECT_MEMORY.md").exists()
    assert not (output / "state" / "sdlc_state.json").exists()
    assert not (output / "state" / "ai_brain_repo_profile.local.json").exists()
    assert not (output / "state" / "reports" / "test_report.json").exists()


def test_dropin_export_requires_clean_for_existing_output(tmp_path: Path) -> None:
    source = tmp_path / "source"
    output = tmp_path / "output"
    write(source / "README.md", "# AI Brain")
    write(output / "old.txt", "old")

    try:
        export_bundle(source, output, clean=False)
    except FileExistsError as error:
        assert "pass --clean" in str(error)
    else:
        raise AssertionError("export_bundle should refuse to overwrite without clean=True")

    report = export_bundle(source, output, clean=True)

    assert report["status"] == "PASS"
    assert (output / "README.md").exists()
    assert not (output / "old.txt").exists()
