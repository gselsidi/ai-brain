from pathlib import Path

from tools import check_python


ROOT = Path(__file__).resolve().parents[1]


def test_python_version_checker_accepts_supported_versions() -> None:
    assert check_python.is_supported((3, 11))
    assert check_python.is_supported((3, 12))
    assert check_python.is_supported((3, 13))


def test_python_version_checker_explains_old_system_python() -> None:
    assert not check_python.is_supported((3, 9))

    message = check_python.unsupported_message("/usr/bin/python3", (3, 9))

    assert "AI Brain requires Python 3.11+" in message
    assert "/usr/bin/python3 is Python 3.9" in message
    assert "make -C ai-brain setup" in message
    assert "ai-brain/.venv/bin" in message


def test_makefile_prefers_existing_venv_and_checks_python_before_init() -> None:
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")

    assert 'if [ -x "$(VENV)/bin/python" ]' in makefile
    assert "python3.12" in makefile
    assert "python3.13" in makefile
    assert "python3.11" in makefile
    assert "check-python:" in makefile
    assert "init-repo: check-python" in makefile
    assert "tools/check_python.py" in makefile
    assert 'if [ -x "$(VENV)/bin/ruff" ]' in makefile
    assert 'if [ -x "$(VENV)/bin/mkdocs" ]' in makefile


def test_readme_top_guidance_mentions_python_bootstrap_before_overview() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    overview_index = readme.index("AI Brain is a reusable agent orchestration harness")

    assert readme.index("make -C ai-brain setup") < overview_index
    assert readme.index("AI Brain requires Python 3.11+") < overview_index
    assert readme.index("macOS") < overview_index
    assert readme.index("ai-brain/.venv/bin/python") < overview_index
