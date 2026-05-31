from pathlib import Path

import yaml

from team_framework.roles import LIFECYCLE_PHASES, ROLE_NAMES


ROOT = Path(__file__).resolve().parents[1]


def test_role_registry_matches_team_framework_contract() -> None:
    contract = yaml.safe_load((ROOT / "contracts/team_framework.yaml").read_text())
    contract_roles = [
        Path(path).stem
        for path in contract["role_files"]
    ]

    assert contract_roles == ROLE_NAMES
    assert "release_gate" in ROLE_NAMES
    assert "self_healer" in ROLE_NAMES


def test_lifecycle_phase_registry_has_release_and_maintenance() -> None:
    assert LIFECYCLE_PHASES[0] == "requirements_intake"
    assert "implementation_hardening" in LIFECYCLE_PHASES
    assert "release_gate" in LIFECYCLE_PHASES
    assert LIFECYCLE_PHASES[-1] == "scheduled_maintenance"
