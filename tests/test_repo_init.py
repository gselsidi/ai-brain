import json
from pathlib import Path

from tools.init_repo_profile import build_profile, write_local_files


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

    profile = build_profile(product, generated_at="2026-06-01T00:00:00+00:00")
    write_local_files(
        profile,
        profile_path=tmp_path / "state" / "ai_brain_repo_profile.local.json",
        memory_path=tmp_path / "memory" / "PROJECT_MEMORY.md",
        state_path=tmp_path / "state" / "sdlc_state.json",
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

    memory = (tmp_path / "memory" / "PROJECT_MEMORY.md").read_text(encoding="utf-8")
    state = json.loads((tmp_path / "state" / "sdlc_state.json").read_text())

    assert "AI Brain Repo Profile" in memory
    assert "npm run test" in memory
    assert state["status"] == "initialized"
    assert state["repo_profile"]["profile_path"] == "state/ai_brain_repo_profile.local.json"
    assert "behavior_contract" not in state["repo_profile"]


def test_public_docs_point_to_init_instead_of_manual_template_copying() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    memory_doc = (ROOT / "docs/memory.md").read_text(encoding="utf-8")
    ready_doc = (ROOT / "docs/ready_to_discuss.md").read_text(encoding="utf-8")

    assert "make init-repo" in readme
    assert "make init-repo" in memory_doc
    assert "make init-repo" in ready_doc
    assert "Copy `memory/PROJECT_MEMORY.template.md` to `memory/PROJECT_MEMORY.md`" not in readme
    assert "Contracts describe AI Brain itself" in readme
    assert "Replace `contracts/expected_behavior.md`" not in readme
    assert "Add your product's test, lint, build, and deploy commands" not in readme
