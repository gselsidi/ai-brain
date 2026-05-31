from pathlib import Path

import yaml

from tools.check_implementation_drift import validate


ROOT = Path(__file__).resolve().parents[1]


def test_team_framework_contract_lists_existing_role_files() -> None:
    contract = yaml.safe_load((ROOT / "contracts/team_framework.yaml").read_text())

    missing = [path for path in contract["role_files"] if not (ROOT / path).exists()]

    assert missing == []
    assert ".codex/agents/sdlc_orchestrator.toml" in contract["role_files"]
    assert ".codex/agents/release_gate.toml" in contract["role_files"]


def test_team_framework_contract_has_no_default_product_runtime() -> None:
    expected = (ROOT / "contracts/expected_behavior.md").read_text()
    readme = (ROOT / "README.md").read_text()

    assert "no default product runtime" in expected
    assert "no default product runtime" in readme


def test_prompt_spec_template_and_current_spec_are_actionable() -> None:
    template = (ROOT / "specs/prompt_spec_template.md").read_text()
    gitignore = (ROOT / ".gitignore").read_text()
    orchestrator = (ROOT / ".codex/agents/sdlc_orchestrator.toml").read_text()
    planner = (ROOT / ".codex/agents/delivery_planner.toml").read_text()

    for marker in {
        "Requirements Checklist",
        "Agent Ownership",
        "Implementation Chunks",
        "Expected Evidence",
        "Completion Audit",
    }:
        assert marker in template

    assert sorted(path.name for path in (ROOT / "specs").glob("*.md")) == [
        "prompt_spec_template.md"
    ]
    assert "specs/*.md" in gitignore
    assert "!specs/prompt_spec_template.md" in gitignore
    assert "specs/prompt_spec_template.md" in planner
    assert "/goal Clarification" in template
    assert "small work chunks" in planner
    assert "current prompt spec" in orchestrator
    assert "not begin substantial implementation" in orchestrator


def test_goal_command_is_a_define_phase_before_local_specs() -> None:
    expected = (ROOT / "contracts/expected_behavior.md").read_text()
    workflow_doc = (ROOT / "docs/spec_driven_workflow.md").read_text()
    framework_map = yaml.safe_load((ROOT / "contracts/agentic_framework_map.yaml").read_text())
    product_context = (ROOT / ".codex/agents/product_context_analyst.toml").read_text()
    planner = (ROOT / ".codex/agents/delivery_planner.toml").read_text()
    orchestrator = (ROOT / ".codex/agents/sdlc_orchestrator.toml").read_text()

    assert "requirements intake -> /goal -> prompt spec" in expected
    assert "/goal" in workflow_doc
    assert "success criteria" in workflow_doc
    assert "non-goals" in workflow_doc
    assert "durable local\nprompt spec" in workflow_doc
    assert "/goal" in framework_map["lifecycle"]["define"]["upstream_commands"]
    assert "goal_clarification" in framework_map["lifecycle"]["define"]["local_phases"]
    assert "Own the `/goal` step" in product_context
    assert "any provider-native\n`/goal` objective" in planner
    assert "AI Brain `/goal` clarification" in planner
    assert "run `/goal`" in orchestrator


def test_provider_native_goal_adapter_feeds_required_sdlc_loop() -> None:
    expected = (ROOT / "contracts/expected_behavior.md").read_text()
    workflow_doc = (ROOT / "docs/spec_driven_workflow.md").read_text()
    orchestrator = (ROOT / ".codex/agents/sdlc_orchestrator.toml").read_text()
    planner = (ROOT / ".codex/agents/delivery_planner.toml").read_text()
    contract = yaml.safe_load((ROOT / "contracts/agentic_framework_map.yaml").read_text())

    assert "provider-native" in workflow_doc
    assert "AI Brain clarification" in workflow_doc
    assert "release gates" in workflow_doc
    assert "provider-native `/goal` or planning input" in expected
    assert "Provider-native `/goal` cannot bypass or replace" in expected
    assert "provider-native `/goal` as input to the SDLC loop" in orchestrator
    assert "clarify the goal inside AI Brain" in orchestrator
    assert "the `/goal` mode: provider-native input or AI Brain clarification" in planner
    assert "provider_goal_adapter" in contract["local_unique_capabilities"]


def test_framework_drift_validator_passes_for_current_contract() -> None:
    test_report = {
        "tests": [
            {
                "section": "Agent Skills Framework Tests",
                "status": "PASS",
                "source": "def test_agentic_framework(): assert True",
            },
            {
                "section": "Harness Quality Tests",
                "status": "PASS",
                "source": "def test_harness(): assert True",
            },
            {
                "section": "Memory And State Tests",
                "status": "PASS",
                "source": "def test_memory(): assert True",
            },
            {
                "section": "Report Rendering Tests",
                "status": "PASS",
                "source": "def test_report(): assert True",
            },
            {
                "section": "Team Framework Tests",
                "status": "PASS",
                "source": "def test_framework(): assert True",
            },
            {
                "section": "Team Reliability Tests",
                "status": "PASS",
                "source": "def test_reliability(): assert True",
            },
        ]
    }

    result = validate(test_report=test_report)

    assert result["status"] == "PASS", result


def test_framework_drift_validator_fails_for_missing_role_prompt(tmp_path: Path) -> None:
    contract = {
        "required_artifacts": [],
        "role_files": [".codex/agents/missing_role.toml"],
        "required_document_markers": [],
    }
    result = validate(contract=contract, test_report={"tests": []}, root=tmp_path)

    assert result["status"] == "FAIL"
    assert result["checks"]["role_prompts"]["missing_files"] == [
        ".codex/agents/missing_role.toml"
    ]
