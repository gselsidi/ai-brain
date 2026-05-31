from pathlib import Path

from tools.run_improvement_queue import build_report, iter_scan_files


def test_improvement_queue_detects_and_prioritizes_blockers(tmp_path: Path) -> None:
    tools_dir = tmp_path / "tools"
    tools_dir.mkdir()
    source = tools_dir / "danger.py"
    source.write_text(
        "def run():\n"
        "    try:\n"
        "        pass\n"
        "    except:\n"
        "        pass\n"
        "    breakpoint()\n",
        encoding="utf-8",
    )

    report = build_report(
        root=tmp_path,
        output=tmp_path / "state" / "reports" / "improvement-queue_report.json",
        generated_at="2026-05-31T00:00:00+00:00",
    )

    detectors = [item["detector"] for item in report["next_items"]]
    assert report["status"] == "FAIL"
    assert report["blocker_count"] == 2
    assert detectors[:2] == ["bare_except", "debug_breakpoint"]
    assert report["scores"]["strict"] < 75


def test_improvement_queue_excludes_generated_and_report_state(tmp_path: Path) -> None:
    generated = tmp_path / "site" / "bad.py"
    generated.parent.mkdir()
    generated.write_text("breakpoint()\n", encoding="utf-8")
    reports = tmp_path / "state" / "reports" / "bad.py"
    reports.parent.mkdir(parents=True)
    reports.write_text("breakpoint()\n", encoding="utf-8")
    source = tmp_path / "tools" / "ok.py"
    source.parent.mkdir()
    source.write_text("def ok():\n    return True\n", encoding="utf-8")

    scanned = [path.relative_to(tmp_path).as_posix() for path in iter_scan_files(tmp_path)]
    report = build_report(
        root=tmp_path,
        output=tmp_path / "state" / "reports" / "improvement-queue_report.json",
        generated_at="2026-05-31T00:00:00+00:00",
    )

    assert scanned == ["tools/ok.py"]
    assert report["status"] == "PASS"
    assert report["finding_count"] == 0


def test_improvement_queue_is_release_wired() -> None:
    root = Path(__file__).resolve().parents[1]
    makefile = (root / "Makefile").read_text(encoding="utf-8")
    release_gate = (root / "tools" / "run_release_gate.py").read_text(encoding="utf-8")
    combined_report = (
        root / "tools" / "generate_combined_report_html.py"
    ).read_text(encoding="utf-8")

    assert "improvement-queue:" in makefile
    assert "tools/run_improvement_queue.py" in makefile
    assert "improvement_queue" in release_gate
    assert "improvement-queue_report.json" in combined_report
