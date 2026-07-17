from pathlib import Path

import yaml

from tools.check_implementation_drift import validate
from tools.select_agent_route import load_source_catalogs, route_prompt


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


def test_dropin_adoption_avoids_nested_git_checkouts() -> None:
    expected = (ROOT / "contracts/expected_behavior.md").read_text()
    readme = (ROOT / "README.md").read_text()
    plumbing = (ROOT / "docs/agent_plumbing.md").read_text()
    framework_map = yaml.safe_load((ROOT / "contracts/agentic_framework_map.yaml").read_text())

    assert "Git subtree" in plumbing
    assert "git subtree add --prefix=ai-brain" in readme
    assert "git subtree pull --prefix=ai-brain" in readme
    assert "make dropin-bundle" in readme
    assert "make -C ai-brain manual-copy-clean" in readme
    assert readme.index("target repo's `.gitignore`") < readme.index("## What It Does")
    assert readme.index("root `AGENTS.md`") < readme.index("## What It Does")
    assert "start a new Codex session" in readme
    assert "INSTALL_ROOT_AGENTS=0" in readme
    assert "nested `.git`" in readme
    assert "make -C ai-brain init-repo TARGET_ROOT=.." in expected
    assert "manual-copy-clean" in expected
    assert "root `AGENTS.md`" in expected
    assert "root_agents_bridge" in framework_map["local_unique_capabilities"]
    assert "plain nested `.git`\ndirectory is not a supported committed state" in expected
    assert "dropin_vendoring" in framework_map["local_unique_capabilities"]


def test_prompt_spec_template_and_current_spec_are_actionable() -> None:
    template = (ROOT / "specs/prompt_spec_template.md").read_text()
    gitignore = (ROOT / ".gitignore").read_text()
    orchestrator = (ROOT / ".codex/agents/sdlc_orchestrator.toml").read_text()
    planner = (ROOT / ".codex/agents/delivery_planner.toml").read_text()

    for marker in {
        "Requirements Checklist",
        "Prompt-To-Agent Routing",
        "Delegation Decision",
        "Agent Ownership",
        "Implementation Chunks",
        "Expected Evidence",
        "Completion Audit",
    }:
        assert marker in template

    spec_names = sorted(path.name for path in (ROOT / "specs").glob("*.md"))
    local_specs = [name for name in spec_names if name != "prompt_spec_template.md"]

    assert "prompt_spec_template.md" in spec_names
    assert all(name[:4].isdigit() and name.endswith(".md") for name in local_specs)
    assert "specs/*.md" in gitignore
    assert "!specs/prompt_spec_template.md" in gitignore
    assert "specs/prompt_spec_template.md" in planner
    assert "/goal Clarification" in template
    assert "tools/select_agent_route.py" in template
    assert "Selected source skills" in template
    assert "Deferred source skills" in template
    assert "Qualifying independent workstreams" in template
    assert "If staying single-agent, allowed exception and reason" in template
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


def test_prompt_to_agent_routing_is_division_first_and_token_thrifty() -> None:
    agents = (ROOT / "AGENTS.md").read_text()
    orchestrator = (ROOT / ".codex/agents/sdlc_orchestrator.toml").read_text()
    agent_plumbing = (ROOT / "docs/agent_plumbing.md").read_text()
    expected = (ROOT / "contracts/expected_behavior.md").read_text()
    routing_contract = yaml.safe_load((ROOT / "contracts/domain_agent_routing.yaml").read_text())
    framework_map = yaml.safe_load((ROOT / "contracts/agentic_framework_map.yaml").read_text())

    seo_route = route_prompt(
        "Improve SEO for service pages with keyword research and metadata.",
        contract=routing_contract,
    )
    programming_route = route_prompt(
        "Fix the React checkout state bug and add regression tests.",
        contract=routing_contract,
    )

    seo_selected = {item["name"] for item in seo_route["selected_specialists"]}
    seo_deferred = {item["name"] for item in seo_route["deferred_specialists"]}
    programming_selected = {item["name"] for item in programming_route["selected_specialists"]}
    programming_deferred = {item["name"] for item in programming_route["deferred_specialists"]}

    assert "prompt-to-agent routing" in orchestrator
    assert "division-first" in orchestrator
    assert "engineering/programming" in orchestrator
    assert "deferred specialists" in orchestrator
    assert "selected source skills" in orchestrator
    assert "Prompt-To-Agent Routing" in agent_plumbing
    assert "SEO is only an example" in agent_plumbing
    assert "source skills" in agent_plumbing
    assert "Prompt specs record division-first prompt-to-agent routing" in expected
    assert "selected source skills" in expected
    assert "prompt_agent_routing" in framework_map["local_unique_capabilities"]
    assert "rampstack_skill_catalog" in framework_map["local_unique_capabilities"]
    assert "marketing_skill_catalog" in framework_map["local_unique_capabilities"]
    assert "Spawn at least one bounded child for substantial work" in agents
    assert "Use at most four bounded children" in agents
    assert "Record the applicable\n  reason" in agents
    assert '`fork_turns="none"`' in agents
    assert "A child must not spawn another child" in agents
    assert "spawn at least one bounded child" in orchestrator
    assert "Use at most\nfour children" in orchestrator
    assert '`fork_turns="none"`' in orchestrator
    assert routing_contract["subagent_policy"]["default_budget"] == 4
    assert routing_contract["subagent_policy"]["delegation_mode"] == "required_when_qualified"
    assert routing_contract["subagent_policy"]["minimum_children_when_qualified"] == 1
    assert routing_contract["subagent_policy"]["single_agent_exception_requires_reason"] is True
    assert routing_contract["subagent_policy"]["required_fork_turns"] == "none"
    assert routing_contract["subagent_policy"]["recursive_fanout"] == "prohibited"

    assert seo_route["primary_division"] == "marketing"
    assert seo_route["adjacent_divisions"] == []
    assert "seo_specialist" in seo_selected
    assert "content_copywriter" in seo_selected
    assert "funnel_lead_gen_strategist" in seo_deferred
    assert "selected_source_skills" in seo_route
    assert "deferred_source_skills" in seo_route
    assert seo_route["subagent_budget"] == 4
    assert seo_route["subagent_policy"] == {
        "routed_roles_are": "review_lenses",
        "delegation_mode": "required_when_qualified",
        "delegation_decision_required": True,
        "assessment_required_for_execution_tiers": ["focused", "controlled", "release"],
        "required_for_substantial_work": True,
        "required_for_execution_tiers": ["controlled", "release"],
        "minimum_children_when_qualified": 1,
        "max_without_explicit_user_request": 4,
        "max_with_explicit_user_request": 4,
        "required_fork_turns": "none",
        "child_bootstrap_mode": "task_packet_only",
        "recursive_fanout": "prohibited",
        "automatic_spawn_from_routing": False,
        "single_agent_exception_requires_reason": True,
        "qualifying_workstreams": [
            "independent_research",
            "independent_audit",
            "disjoint_implementation",
            "test_matrix_execution",
            "adversarial_review",
            "independent_verification",
        ],
        "allowed_single_agent_exceptions": [
            "no_safe_independent_workstream",
            "runtime_delegation_unavailable",
            "user_disabled_subagents",
            "shared_state_conflict",
        ],
    }
    assert any(
        "review lenses, not automatic subagent spawns" in note
        for note in seo_route["routing_notes"]
    )
    assert len(seo_route["selected_specialists"]) <= (
        routing_contract["routing_defaults"]["max_primary_specialists"]
        + routing_contract["routing_defaults"]["max_adjacent_specialists"]
    )

    assert programming_route["primary_division"] == "engineering"
    assert "dev_builder" in programming_route["selected_framework_agents"]
    assert "dev_test_writer" in programming_route["selected_framework_agents"]
    assert "frontend_developer" in programming_selected
    assert "test_engineer" in programming_selected
    assert "content_copywriter" not in programming_selected
    assert "content_copywriter" not in programming_deferred
    assert programming_route["selected_source_skills"] == []


def test_execution_discipline_is_compact_and_preserves_final_evidence() -> None:
    agents = (ROOT / "AGENTS.md").read_text()
    orchestrator = (ROOT / ".codex/agents/sdlc_orchestrator.toml").read_text()
    expected = (ROOT / "contracts/expected_behavior.md").read_text()
    plumbing = (ROOT / "docs/agent_plumbing.md").read_text()

    assert "## Execution Discipline" in agents
    assert "Assess → act → verify" in agents
    assert "Work in terse architect-engineer mode" in agents
    assert "native format of the task or tool" in agents
    assert "child handoffs compact" in agents
    assert "native format of the task or tool" in orchestrator
    assert "Work in terse architect-engineer mode" in orchestrator
    assert "## Execution Discipline" in expected
    assert "native format of the task or tool" in expected
    assert "## Execution Discipline" in plumbing


def test_release_windows_defer_full_release_work_until_explicit_close() -> None:
    agents = (ROOT / "AGENTS.md").read_text()
    orchestrator = (ROOT / ".codex/agents/sdlc_orchestrator.toml").read_text()
    expected = (ROOT / "contracts/expected_behavior.md").read_text()

    assert "## Release Windows" in agents
    assert "related follow-up corrections as one active release window" in agents
    assert "asks to finish, commit, push, deploy, release" in agents
    assert "Use release windows for related follow-up corrections" in orchestrator
    assert "explicitly asks to finish, commit, push, deploy, release" in orchestrator
    assert "## Release Window Discipline" in expected
    assert "commit/push, and deployment run once" in expected


def test_rampstack_skill_catalog_maps_all_source_skills_and_router_defers_extra_lenses() -> None:
    routing_contract = yaml.safe_load((ROOT / "contracts/domain_agent_routing.yaml").read_text())
    source_catalog = yaml.safe_load((ROOT / "contracts/rampstack_skill_integration.yaml").read_text())

    category_mappings = source_catalog["category_mappings"]
    mapped_skills = [
        skill
        for mapping in category_mappings.values()
        for skill in mapping["skills"]
    ]
    skill_by_slug = {skill["slug"]: skill for skill in mapped_skills}
    integration_actions = {skill["integration_action"] for skill in mapped_skills}

    assert source_catalog["source"]["inspected_skill_count"] == 103
    assert len(mapped_skills) == 103
    assert len(skill_by_slug) == 103
    assert integration_actions == {
        "add_catalog_lens",
        "merge_existing",
        "tool_dependent_lens",
    }
    assert skill_by_slug["code-review-web"]["integration_action"] == "merge_existing"
    assert skill_by_slug["landing-page-copy"]["integration_action"] == "add_catalog_lens"
    assert skill_by_slug["seo-audit-orchestration"]["integration_action"] == (
        "tool_dependent_lens"
    )

    frontend_route = route_prompt(
        "Build a frontend component and audit accessibility.",
        contract=routing_contract,
        source_catalog=source_catalog,
    )
    frontend_source_slugs = {
        skill["slug"] for skill in frontend_route["selected_source_skills"]
    }

    assert "frontend-component-build" in frontend_source_slugs
    assert "accessibility-audit" in frontend_source_slugs
    assert len(frontend_route["selected_source_skills"]) <= (
        routing_contract["routing_defaults"]["max_source_skills"]
    )

    seo_route = route_prompt(
        "Run a full SEO audit and backlink gap review.",
        contract=routing_contract,
        source_catalog=source_catalog,
    )
    selected_seo_slugs = {skill["slug"] for skill in seo_route["selected_source_skills"]}
    deferred_seo_slugs = {skill["slug"] for skill in seo_route["deferred_source_skills"]}

    assert "seo-audit-orchestration" in selected_seo_slugs
    assert "seo-backlink-audit" in selected_seo_slugs
    assert "seo-keyword" in deferred_seo_slugs
    assert any(
        skill["integration_action"] == "tool_dependent_lens"
        for skill in seo_route["selected_source_skills"]
    )
    assert any("Tool-dependent source skills" in note for note in seo_route["routing_notes"])
    assert len(seo_route["selected_source_skills"]) <= (
        routing_contract["routing_defaults"]["max_source_skills"]
    )
    assert len(seo_route["deferred_source_skills"]) <= (
        routing_contract["routing_defaults"]["max_deferred_source_skills"]
    )


def test_marketing_skill_catalog_maps_all_source_skills_and_routes_trigger_terms() -> None:
    routing_contract = yaml.safe_load((ROOT / "contracts/domain_agent_routing.yaml").read_text())
    marketing_catalog = yaml.safe_load(
        (ROOT / "contracts/marketing_skill_integration.yaml").read_text()
    )
    rampstack_catalog = yaml.safe_load(
        (ROOT / "contracts/rampstack_skill_integration.yaml").read_text()
    )

    configured_catalogs = load_source_catalogs(routing_contract)
    configured_catalog_names = {catalog["name"] for catalog in configured_catalogs}
    mapped_skills = [
        skill
        for mapping in marketing_catalog["category_mappings"].values()
        for skill in mapping["skills"]
    ]
    skill_by_slug = {skill["slug"]: skill for skill in mapped_skills}
    integration_actions = {skill["integration_action"] for skill in mapped_skills}

    assert configured_catalog_names == {
        "marketing-skill-integration",
        "rampstack-skill-integration",
    }
    assert marketing_catalog["source"]["inspected_skill_count"] == 44
    assert marketing_catalog["supplemental_skill_count"] == 1
    assert marketing_catalog["total_mapped_skill_count"] == 45
    assert len(mapped_skills) == 45
    assert len(skill_by_slug) == 45
    assert integration_actions == {
        "add_catalog_lens",
        "merge_existing",
        "tool_dependent_lens",
    }
    assert skill_by_slug["product-marketing"]["integration_action"] == "merge_existing"
    assert skill_by_slug["direct-response-copy"]["integration_action"] == "add_catalog_lens"
    assert skill_by_slug["direct-response-copy"]["source"] == "direct-response-copy"
    assert skill_by_slug["sms"]["integration_action"] == "add_catalog_lens"
    assert skill_by_slug["revops"]["integration_action"] == "tool_dependent_lens"

    measurement_route = route_prompt(
        "Set up GA4 tracking for paid ads and write cold outreach emails.",
        contract=routing_contract,
        source_catalog=[marketing_catalog, rampstack_catalog],
    )
    selected_slugs = {skill["slug"] for skill in measurement_route["selected_source_skills"]}
    selected_catalogs = {
        skill["catalog"] for skill in measurement_route["selected_source_skills"]
    }

    assert "analytics" in selected_slugs
    assert "ads" in selected_slugs
    assert "cold-email" in selected_slugs
    assert "marketing-skill-integration" in selected_catalogs
    assert any(
        skill["integration_action"] == "tool_dependent_lens"
        for skill in measurement_route["selected_source_skills"]
    )
    assert len(measurement_route["selected_source_skills"]) <= (
        routing_contract["routing_defaults"]["max_source_skills"]
    )

    duplicate_route = route_prompt(
        "Plan programmatic SEO pages at scale with schema markup.",
        contract=routing_contract,
        source_catalog=[marketing_catalog, rampstack_catalog],
    )
    all_duplicate_slugs = [
        skill["slug"]
        for skill in duplicate_route["selected_source_skills"]
        + duplicate_route["deferred_source_skills"]
    ]

    assert "programmatic-seo" in all_duplicate_slugs
    assert all_duplicate_slugs.count("programmatic-seo") == 1

    direct_response_route = route_prompt(
        "Write direct response sales copy for a landing page with headline variations, CTA copy, and curiosity gaps.",
        contract=routing_contract,
        source_catalog=[marketing_catalog, rampstack_catalog],
    )
    direct_response_slugs = {
        skill["slug"] for skill in direct_response_route["selected_source_skills"]
    }

    assert direct_response_route["primary_division"] == "marketing"
    assert "direct-response-copy" in direct_response_slugs


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
