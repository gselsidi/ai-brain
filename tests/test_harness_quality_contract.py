import yaml

from tools.validate_harness_quality import (
    CONTRACT_PATH,
    artifact_check,
    artifact_marker_check,
)


def test_harness_quality_contract_references_existing_artifacts_and_markers() -> None:
    contract = yaml.safe_load(CONTRACT_PATH.read_text(encoding="utf-8"))

    artifacts = artifact_check(contract)
    markers = artifact_marker_check(contract)

    assert artifacts["status"] == "PASS", artifacts
    assert markers["status"] == "PASS", markers
