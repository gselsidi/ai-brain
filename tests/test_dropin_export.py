import subprocess
from pathlib import Path

from tools.clean_manual_copy import clean_manual_copy
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


def test_manual_copy_clean_removes_nested_git_only_inside_parent_repo(tmp_path: Path) -> None:
    target = tmp_path / "target-repo"
    copied = target / "ai-brain"
    target.mkdir()
    subprocess.check_call(["git", "init"], cwd=target, stdout=subprocess.DEVNULL)

    write(copied / ".git" / "config", "private git metadata")
    write(copied / ".venv" / "pyvenv.cfg", "local venv")
    write(copied / "README.md", "# AI Brain")
    write(copied / "AGENTS.md", "# Agents")
    write(copied / "specs" / "prompt_spec_template.md", "# Template")
    write(copied / "specs" / "2026-06-13_local_work.md", "# Local Spec")
    write(copied / "memory" / "PROJECT_MEMORY.md", "# Local Memory")
    write(copied / "state" / "sdlc_state.json", "{}")
    write(copied / "state" / "reports" / "test_report.json", "{}")

    report = clean_manual_copy(copied)
    status = subprocess.check_output(["git", "status", "--short"], cwd=target, text=True)

    assert report["status"] == "PASS"
    assert report["parent_repo"] == target.as_posix()
    assert ".git" in report["removed"]
    assert not (copied / ".git").exists()
    assert not (copied / ".venv").exists()
    assert not (copied / "specs" / "2026-06-13_local_work.md").exists()
    assert not (copied / "memory" / "PROJECT_MEMORY.md").exists()
    assert not (copied / "state" / "sdlc_state.json").exists()
    assert not (copied / "state" / "reports" / "test_report.json").exists()
    assert (copied / "README.md").exists()
    assert (copied / "AGENTS.md").exists()
    assert (copied / "specs" / "prompt_spec_template.md").exists()
    assert "?? ai-brain/" in status


def test_manual_copy_clean_refuses_source_checkout_without_parent_repo(tmp_path: Path) -> None:
    source = tmp_path / "ai-brain-source"
    write(source / ".git" / "config", "source git metadata")
    write(source / "README.md", "# AI Brain")

    try:
        clean_manual_copy(source)
    except RuntimeError as error:
        assert "no parent target repo was detected" in str(error)
    else:
        raise AssertionError("clean_manual_copy should refuse to clean a standalone checkout")

    assert (source / ".git").exists()
