from tools.validate_agentic_framework import EXPECTED_UPSTREAM_SKILLS, validate


def test_combined_agentic_framework_map_is_complete() -> None:
    result = validate()

    assert result["status"] == "PASS", result["errors"]
    assert result["upstream_skill_count"] == len(EXPECTED_UPSTREAM_SKILLS)
    assert result["lifecycle_phase_count"] == 7
