from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml


ROOT_DIR = Path(__file__).resolve().parents[1]
MAP_PATH = ROOT_DIR / "contracts" / "agentic_framework_map.yaml"
REPORT_PATH = ROOT_DIR / "state" / "reports" / "agent-skills-framework_report.json"

EXPECTED_UPSTREAM_SKILLS = {
    "api-and-interface-design",
    "browser-testing-with-devtools",
    "ci-cd-and-automation",
    "code-review-and-quality",
    "code-simplification",
    "context-engineering",
    "debugging-and-error-recovery",
    "deprecation-and-migration",
    "documentation-and-adrs",
    "frontend-ui-engineering",
    "git-workflow-and-versioning",
    "idea-refine",
    "incremental-implementation",
    "performance-optimization",
    "planning-and-task-breakdown",
    "security-and-hardening",
    "shipping-and-launch",
    "source-driven-development",
    "spec-driven-development",
    "test-driven-development",
    "using-agent-skills",
}

EXPECTED_LIFECYCLE_PHASES = {
    "define",
    "plan",
    "build",
    "verify",
    "review",
    "ship",
    "maintain",
}


def load_map() -> dict[str, Any]:
    return yaml.safe_load(MAP_PATH.read_text(encoding="utf-8"))


def path_exists(path: str) -> bool:
    if path.startswith("http://") or path.startswith("https://"):
        return True
    if path.startswith("state/reports/"):
        return True
    return (ROOT_DIR / path).exists()


def validate() -> dict[str, Any]:
    mapping = load_map()
    errors: list[dict[str, Any]] = []

    upstream_skills = set(mapping.get("upstream_skills", []))
    if upstream_skills != EXPECTED_UPSTREAM_SKILLS:
        errors.append(
            {
                "rule": "upstream_skill_set",
                "missing": sorted(EXPECTED_UPSTREAM_SKILLS - upstream_skills),
                "unexpected": sorted(upstream_skills - EXPECTED_UPSTREAM_SKILLS),
            }
        )

    coverage = mapping.get("skill_coverage", {})
    uncovered = sorted(EXPECTED_UPSTREAM_SKILLS - set(coverage))
    extra_coverage = sorted(set(coverage) - EXPECTED_UPSTREAM_SKILLS)
    if uncovered or extra_coverage:
        errors.append(
            {
                "rule": "skill_coverage",
                "missing": uncovered,
                "unexpected": extra_coverage,
            }
        )

    lifecycle = mapping.get("lifecycle", {})
    lifecycle_phases = set(lifecycle)
    if lifecycle_phases != EXPECTED_LIFECYCLE_PHASES:
        errors.append(
            {
                "rule": "lifecycle_phases",
                "missing": sorted(EXPECTED_LIFECYCLE_PHASES - lifecycle_phases),
                "unexpected": sorted(lifecycle_phases - EXPECTED_LIFECYCLE_PHASES),
            }
        )

    for phase_name, phase in lifecycle.items():
        for skill in phase.get("upstream_skills", []):
            if skill not in EXPECTED_UPSTREAM_SKILLS:
                errors.append(
                    {"rule": "lifecycle_skill_reference", "phase": phase_name, "skill": skill}
                )
        if not phase.get("combined_rule"):
            errors.append({"rule": "missing_combined_rule", "phase": phase_name})

    missing_agents = []
    for agent in mapping.get("local_agents", []):
        path = ROOT_DIR / ".codex" / "agents" / f"{agent}.toml"
        if not path.exists():
            missing_agents.append(agent)
    if missing_agents:
        errors.append({"rule": "local_agent_files", "missing": sorted(missing_agents)})

    missing_artifacts = []
    for section in ("local_unique_capabilities", "skill_coverage", "lifecycle"):
        values = mapping.get(section, {})
        for name, item in values.items():
            artifacts = item.get("artifacts") or item.get("local_artifacts") or []
            for artifact in artifacts:
                if not path_exists(artifact):
                    missing_artifacts.append({"section": section, "name": name, "path": artifact})
    if missing_artifacts:
        errors.append({"rule": "artifact_paths", "missing": missing_artifacts})

    upstream_source = mapping.get("upstream_source", {})
    if upstream_source.get("license") != "MIT" or not upstream_source.get("repository"):
        errors.append({"rule": "upstream_provenance", "source": upstream_source})

    return {
        "status": "PASS" if not errors else "FAIL",
        "map": str(MAP_PATH.relative_to(ROOT_DIR)),
        "summary": (
            "Agent-skills framework map covers all upstream skills, local agents, and referenced artifacts."
            if not errors
            else "Agent-skills framework map has coverage or artifact drift."
        ),
        "upstream_skill_count": len(upstream_skills),
        "lifecycle_phase_count": len(lifecycle_phases),
        "local_agent_count": len(mapping.get("local_agents", [])),
        "errors": errors,
    }


def main() -> None:
    result = validate()
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
