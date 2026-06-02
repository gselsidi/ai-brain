from pathlib import Path

from tools.analyze_conversation_feedback import build_report


def write_session(path: Path, project_root: Path, messages: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    for message in messages:
        lines.append(
            '{"cwd": "'
            + project_root.as_posix()
            + '", "type": "response_item", "payload": {"type": "message", "role": "user", "content": "'
            + message.replace('"', '\\"')
            + '"}}'
        )
    path.write_text("\n".join(lines), encoding="utf-8")


def test_conversation_feedback_filters_to_project_and_suggests_patches(tmp_path: Path) -> None:
    project = tmp_path / "product"
    project.mkdir()
    sessions = tmp_path / "sessions"
    write_session(
        sessions / "project.jsonl",
        project,
        [
            "bro you still left specs in the repo, this should be ignored",
            "actually the README is still too salesly and docs need to be cleaner",
            "no i meant delete repo history and scrub secrets",
            "release gate failed again after make test",
        ],
    )
    (sessions / "nested.jsonl").write_text(
        '{"cwd": "'
        + project.as_posix()
        + '", "type": "response_item", "payload": {"type": "message", "role": "user", "content": [{"text": "still need README docs fixed"}]}}',
        encoding="utf-8",
    )
    other_project = tmp_path / "other"
    other_project.mkdir()
    write_session(
        sessions / "other.jsonl",
        other_project,
        ["secret unrelated repo chatter should not count"],
    )

    report = build_report(
        session_dir=sessions,
        project_root=project,
        output=tmp_path / "state" / "reports" / "conversation-feedback_report.json",
        patch_brief=tmp_path / "state" / "reports" / "conversation-feedback_patch_brief.md",
        state_path=tmp_path / "state" / "conversation_feedback_state.local.json",
        cadence_days=0,
        generated_at="2026-06-01T00:00:00+00:00",
    )

    categories = {finding["category"] for finding in report["findings"]}
    assert report["status"] == "PASS"
    assert report["scanned_session_count"] == 2
    assert "correction_loop" in categories
    assert "public_hygiene" in categories
    assert "docs_friction" in categories
    assert "Conversation Feedback Patch Brief" in Path(report["patch_brief"]).read_text()


def test_conversation_feedback_respects_cadence(tmp_path: Path) -> None:
    project = tmp_path / "product"
    project.mkdir()
    state = tmp_path / "state" / "conversation_feedback_state.local.json"
    state.parent.mkdir()
    state.write_text('{"last_run_at": "2026-06-01T00:00:00+00:00"}', encoding="utf-8")

    report = build_report(
        session_dir=tmp_path / "sessions",
        project_root=project,
        output=tmp_path / "state" / "reports" / "conversation-feedback_report.json",
        patch_brief=tmp_path / "state" / "reports" / "conversation-feedback_patch_brief.md",
        state_path=state,
        cadence_days=7,
        generated_at="2026-06-02T00:00:00+00:00",
    )

    assert report["status"] == "SKIP"
    assert "cadence is 7 day" in report["summary"]
