import json
from pathlib import Path

from tools.install_root_agents import BRIDGE_START, install_root_agents
from tools.init_repo_profile import build_profile, install_target_gitignore, local_artifact_paths, write_local_files


ROOT = Path(__file__).resolve().parents[1]


def test_repo_init_detects_product_commands_and_writes_local_files(tmp_path: Path) -> None:
    product = tmp_path / "product"
    product.mkdir()
    (product / "package.json").write_text(
        json.dumps(
            {
                "name": "sample-product",
                "scripts": {
                    "lint": "eslint .",
                    "test": "vitest run",
                    "build": "vite build",
                    "deploy": "wrangler deploy",
                },
                "dependencies": {"react": "^19.0.0", "vite": "^6.0.0"},
            }
        ),
        encoding="utf-8",
    )
    (product / "src").mkdir()
    (product / "tests").mkdir()

    local_paths = local_artifact_paths(product)
    profile = build_profile(product, generated_at="2026-06-01T00:00:00+00:00")
    write_local_files(
        profile,
        profile_path=local_paths["profile"],
        memory_path=local_paths["memory"],
        state_path=local_paths["state"],
    )

    commands = {item["purpose"]: item["command"] for item in profile["detected_commands"]}
    assert profile["project_name"] == "sample-product"
    assert "React" in profile["detected_stack"]
    assert "Vite" in profile["detected_stack"]
    assert commands["test"] == "npm run test"
    assert commands["lint"] == "npm run lint"
    assert commands["build"] == "npm run build"
    assert commands["deploy"] == "npm run deploy"
    assert "src" in profile["source_markers"]
    assert "tests" in profile["source_markers"]

    memory = local_paths["memory"].read_text(encoding="utf-8")
    state = json.loads(local_paths["state"].read_text())

    assert "AI Brain Repo Profile" in memory
    assert "npm run test" in memory
    assert state["status"] == "initialized"
    assert state["repo_profile"]["profile_path"] == ".ai-brain/state/ai_brain_repo_profile.local.json"
    assert "behavior_contract" not in state["repo_profile"]
    assert profile["local_files"]["memory"] == ".ai-brain/memory/PROJECT_MEMORY.md"
    assert profile["local_files"]["work_specs"] == ".ai-brain/specs/work"


def test_public_docs_point_to_init_instead_of_manual_template_copying() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    memory_doc = (ROOT / "docs/memory.md").read_text(encoding="utf-8")
    ready_doc = (ROOT / "docs/ready_to_discuss.md").read_text(encoding="utf-8")

    assert "make init-repo" in readme
    assert "make init-repo" in memory_doc
    assert "make init-repo" in ready_doc
    assert "git subtree" in readme
    assert "make dropin-bundle" in readme
    assert "make -C ai-brain manual-copy-clean" in readme
    assert "ai-brain/" in readme
    assert "target repo's `.gitignore`" in readme
    assert "root `AGENTS.md`" in readme
    assert "INSTALL_ROOT_AGENTS=0" in readme
    assert "nested `.git`" in ready_doc
    assert "AI Brain bridge" in ready_doc
    assert "TARGET_ROOT=.." in readme
    assert "Copy `memory/PROJECT_MEMORY.template.md` to `memory/PROJECT_MEMORY.md`" not in readme
    assert "Contracts describe AI Brain itself" in readme
    assert "Replace `contracts/expected_behavior.md`" not in readme
    assert "Add your product's test, lint, build, and deploy commands" not in readme


def test_root_agents_bridge_installs_and_preserves_existing_instructions(tmp_path: Path) -> None:
    target = tmp_path / "target"
    brain = target / "ai-brain"
    target.mkdir()
    brain.mkdir()
    (brain / "AGENTS.md").write_text("# AI Brain instructions\n", encoding="utf-8")
    root_agents = target / "AGENTS.md"
    root_agents.write_text("# Existing Instructions\n\nKeep this repo-specific note.\n", encoding="utf-8")

    report = install_root_agents(target_root=target, ai_brain_root=brain)
    text = root_agents.read_text(encoding="utf-8")

    assert report["status"] == "PASS"
    assert "# Existing Instructions" in text
    assert "Keep this repo-specific note." in text
    assert BRIDGE_START in text
    assert "This repository uses AI Brain as its agent orchestration layer." in text
    assert "Mandatory start-of-turn rule for every new user prompt" in text
    assert "`ai-brain/AGENTS.md`" in text
    assert "`.ai-brain/memory/PROJECT_MEMORY.md`" in text
    assert "`.ai-brain/state/ai_brain_repo_profile.local.json`" in text
    assert "Treat the user's prompt as an AI Brain routing signal" in text
    assert "selected specialists, deferred specialists, selected source" in text
    assert "spec before implementation" in text
    assert "Treat AI Brain as the primary workflow layer" in text


def test_root_agents_bridge_replaces_only_managed_block(tmp_path: Path) -> None:
    target = tmp_path / "target"
    brain = target / "ai-brain"
    target.mkdir()
    brain.mkdir()
    root_agents = target / "AGENTS.md"

    install_root_agents(target_root=target, ai_brain_root=brain)
    first_text = root_agents.read_text(encoding="utf-8")
    root_agents.write_text(first_text + "\nOutside managed block.\n", encoding="utf-8")
    install_root_agents(target_root=target, ai_brain_root=brain)
    second_text = root_agents.read_text(encoding="utf-8")

    assert second_text.count(BRIDGE_START) == 1
    assert "Outside managed block." in second_text


def test_makefile_installs_root_agents_bridge_by_default_with_opt_out() -> None:
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")

    assert "INSTALL_ROOT_AGENTS ?= 1" in makefile
    assert "ROOT_AGENTS_FLAG" in makefile
    assert "--skip-root-agents" in makefile


def test_target_gitignore_ignores_sticky_ai_brain_data(tmp_path: Path) -> None:
    target = tmp_path / "target"
    target.mkdir()
    gitignore = target / ".gitignore"
    gitignore.write_text("node_modules/\n", encoding="utf-8")

    report = install_target_gitignore(target, target / ".ai-brain")
    text = gitignore.read_text(encoding="utf-8")

    assert report["status"] == "PASS"
    assert "node_modules/" in text
    assert "# AI_BRAIN_LOCAL_DATA_START" in text
    assert ".ai-brain/" in text
