from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from html import escape
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT_DIR = ROOT / "state" / "reports"
DEFAULT_OUTPUT = DEFAULT_REPORT_DIR / "combined_report.html"


REPORT_FILES = {
    "Regression Tests": "test_report.json",
    "Agent Skills Framework": "agent-skills-framework_report.json",
    "Framework Drift": "implementation-drift_report.json",
    "Harness Quality": "harness-quality_report.json",
    "Improvement Queue": "improvement-queue_report.json",
    "Conversation Feedback": "conversation-feedback_report.json",
    "Target Commands": "target-command_report.json",
    "Target Drift": "target-drift_report.json",
    "Team Reliability": "team-reliability_report.json",
    "Hardening": "improvement_hardening_report.json",
    "Requirements Audit": "requirements_audit_report.json",
    "Release Gate": "release-gate_report.json",
}


def load_report(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {
            "mode": path.stem,
            "status": "FAIL",
            "summary": f"Could not parse report JSON: {exc}",
        }


def status_class(status: Any) -> str:
    value = str(status or "UNKNOWN").upper()
    if value in {"PASS", "HEALTHY", "OK"}:
        return "pass"
    if value in {"WARN", "SKIP", "SKIPPED", "ADAPTED"}:
        return "warn"
    if value in {"FAIL", "ERROR"}:
        return "fail"
    return "neutral"


def tag(status: Any) -> str:
    value = escape(str(status or "UNKNOWN"))
    return f'<span class="tag {status_class(status)}">{value}</span>'


def section(title: str, body: str) -> str:
    return f"<section><h2>{escape(title)}</h2>{body}</section>"


def kv_table(items: dict[str, Any]) -> str:
    rows = []
    for key, value in items.items():
        rows.append(
            "<tr>"
            f"<th>{escape(str(key).replace('_', ' ').title())}</th>"
            f"<td>{escape(str(value))}</td>"
            "</tr>"
        )
    return f'<table class="kv"><tbody>{"".join(rows)}</tbody></table>'


def render_checks(checks: dict[str, Any]) -> str:
    rows = []
    for name, status in sorted(checks.items()):
        rows.append(
            "<tr>"
            f"<td>{escape(str(name).replace('_', ' '))}</td>"
            f"<td>{tag(status)}</td>"
            "</tr>"
        )
    if not rows:
        return '<p class="muted">No release checks recorded.</p>'
    return (
        "<table><thead><tr><th>Check</th><th>Status</th></tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table>"
    )


def render_improvement_queue(report: dict[str, Any] | None) -> str:
    if not report:
        return '<p class="muted">No improvement queue report found. Run <code>make improvement-queue</code>.</p>'

    scores = report.get("scores", {})
    summary = kv_table(
        {
            "status": report.get("status"),
            "strict_score": scores.get("strict"),
            "lenient_score": scores.get("lenient"),
            "finding_count": report.get("finding_count"),
            "blocker_count": report.get("blocker_count"),
        }
    )
    rows = []
    for item in report.get("next_items", [])[:8]:
        if not isinstance(item, dict):
            continue
        rows.append(
            "<tr>"
            f"<td>{escape(str(item.get('priority', '')))}</td>"
            f"<td><code>{escape(str(item.get('detector', '')))}</code></td>"
            f"<td><code>{escape(str(item.get('path', '')))}:{escape(str(item.get('line', '')))}</code></td>"
            f"<td>{escape(str(item.get('summary', '')))}</td>"
            "</tr>"
        )
    if not rows:
        queue_html = '<p class="muted">No active improvement queue items.</p>'
    else:
        queue_html = (
            "<table><thead><tr><th>Priority</th><th>Detector</th><th>Location</th><th>Summary</th></tr></thead><tbody>"
            + "".join(rows)
            + "</tbody></table>"
        )
    return summary + queue_html


def render_conversation_feedback(report: dict[str, Any] | None) -> str:
    if not report:
        return '<p class="muted">No conversation feedback report found. Run <code>make conversation-feedback</code>.</p>'

    rows = []
    for item in report.get("findings", [])[:8]:
        if not isinstance(item, dict):
            continue
        rows.append(
            "<tr>"
            f"<td><code>{escape(str(item.get('category', '')))}</code></td>"
            f"<td>{escape(str(item.get('severity', '')))}</td>"
            f"<td>{escape(str(item.get('count', '')))}</td>"
            f"<td>{escape(str(item.get('summary', '')))}</td>"
            "</tr>"
        )
    findings_html = (
        '<p class="muted">No recurring repo-scoped friction findings.</p>'
        if not rows
        else (
            "<table><thead><tr><th>Category</th><th>Severity</th><th>Count</th><th>Summary</th></tr></thead><tbody>"
            + "".join(rows)
            + "</tbody></table>"
        )
    )
    return (
        kv_table(
            {
                "status": report.get("status"),
                "summary": report.get("summary"),
                "scanned_sessions": report.get("scanned_session_count"),
                "patch_brief": report.get("patch_brief"),
            }
        )
        + findings_html
    )


def render_target_commands(report: dict[str, Any] | None) -> str:
    if not report:
        return '<p class="muted">No target command report found. Run <code>make target-check</code>.</p>'
    rows = []
    for item in report.get("commands", []):
        if not isinstance(item, dict):
            continue
        rows.append(
            "<tr>"
            f"<td><code>{escape(str(item.get('purpose', '')))}</code></td>"
            f"<td><code>{escape(str(item.get('command', '')))}</code></td>"
            f"<td>{tag(item.get('status'))}</td>"
            f"<td>{escape(str(item.get('returncode', '')))}</td>"
            "</tr>"
        )
    commands_html = (
        '<p class="muted">No target commands were selected.</p>'
        if not rows
        else (
            "<table><thead><tr><th>Purpose</th><th>Command</th><th>Status</th><th>Return Code</th></tr></thead><tbody>"
            + "".join(rows)
            + "</tbody></table>"
        )
    )
    return (
        kv_table(
            {
                "status": report.get("status"),
                "summary": report.get("summary"),
                "project_root": report.get("project_root"),
            }
        )
        + commands_html
    )


def render_target_drift(report: dict[str, Any] | None) -> str:
    if not report:
        return '<p class="muted">No target drift report found. Run <code>make target-drift</code>.</p>'
    checks = report.get("checks", {})
    rows = []
    if isinstance(checks, dict):
        for name, item in sorted(checks.items()):
            if not isinstance(item, dict):
                continue
            rows.append(
                "<tr>"
                f"<td><code>{escape(str(name))}</code></td>"
                f"<td>{tag(item.get('status'))}</td>"
                f"<td>{escape(str(item.get('summary', '')))}</td>"
                "</tr>"
            )
    checks_html = (
        '<p class="muted">No target drift checks were recorded.</p>'
        if not rows
        else (
            "<table><thead><tr><th>Check</th><th>Status</th><th>Summary</th></tr></thead><tbody>"
            + "".join(rows)
            + "</tbody></table>"
        )
    )
    return (
        kv_table(
            {
                "status": report.get("status"),
                "summary": report.get("summary"),
                "profile": report.get("profile"),
            }
        )
        + checks_html
    )


def test_counts(tests: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for test in tests:
        status = str(test.get("status", "UNKNOWN")).upper()
        counts[status] = counts.get(status, 0) + 1
    return dict(sorted(counts.items()))


def render_count_summary(counts: dict[str, int]) -> str:
    if not counts:
        return '<span class="muted">No tests</span>'
    return " ".join(
        f"{tag(status)} <span class=\"count\">{count}</span>"
        for status, count in counts.items()
    )


def render_test_case(test: dict[str, Any]) -> str:
    nodeid = str(test.get("nodeid", "unknown"))
    status = test.get("status", "UNKNOWN")
    file = str(test.get("file", ""))
    line = str(test.get("line", ""))
    duration = test.get("duration_seconds", "")
    parameters = test.get("parameters", {})
    source = str(test.get("source", ""))
    failure = test.get("failure")

    params_html = ""
    if isinstance(parameters, dict) and parameters:
        params_html = (
            '<div class="test-params"><strong>Parameters</strong><pre>'
            + escape(json.dumps(parameters, indent=2, sort_keys=True))
            + "</pre></div>"
        )

    failure_html = ""
    if failure:
        failure_html = '<div class="test-failure"><strong>Failure</strong><pre>'
        failure_html += escape(str(failure))
        failure_html += "</pre></div>"

    return (
        '<details class="test-case">'
        "<summary>"
        f"{tag(status)} "
        f"<code>{escape(nodeid)}</code>"
        "</summary>"
        '<div class="test-meta">'
        f"<code>{escape(file)}:{escape(line)}</code>"
        f"<span>{escape(str(duration))}s</span>"
        "</div>"
        f"{params_html}"
        '<pre class="source-code"><code>'
        f"{escape(source)}"
        "</code></pre>"
        f"{failure_html}"
        "</details>"
    )


def render_test_evidence(report: dict[str, Any] | None) -> str:
    if not report:
        return '<p class="muted">No pytest evidence report found. Run <code>make test</code>.</p>'

    tests = report.get("tests", [])
    if not isinstance(tests, list):
        return '<p class="muted">Pytest evidence report has no test list.</p>'

    grouped: dict[str, list[dict[str, Any]]] = {}
    for test in tests:
        if isinstance(test, dict):
            grouped.setdefault(str(test.get("section", "Uncategorized Tests")), []).append(test)

    group_html = []
    for section_name, section_tests in sorted(grouped.items()):
        counts = test_counts(section_tests)
        cases = "".join(render_test_case(test) for test in section_tests)
        group_html.append(
            '<details class="test-section">'
            "<summary>"
            f"<span>{escape(section_name)}</span>"
            f"<span>{render_count_summary(counts)}</span>"
            "</summary>"
            f"{cases}"
            "</details>"
        )

    collection_errors = report.get("collection_errors", [])
    errors_html = ""
    if collection_errors:
        errors_html = "<h3>Collection Errors</h3><pre>"
        errors_html += escape(json.dumps(collection_errors, indent=2, sort_keys=True))
        errors_html += "</pre>"

    return (
        "<p class=\"muted\">"
        "Expand a group to inspect each test and the exact source code behind the evidence."
        "</p>"
        + kv_table(
            {
                "status": report.get("status"),
                "summary": report.get("summary"),
                "generated_at": report.get("generated_at"),
            }
        )
        + "".join(group_html)
        + errors_html
    )


def render_report(report_dir: Path, output: Path) -> Path:
    reports = {label: load_report(report_dir / filename) for label, filename in REPORT_FILES.items()}
    generated_at = datetime.now(UTC).isoformat()

    cards = []
    for label, report in reports.items():
        status = report.get("status") if report else "MISSING"
        summary = report.get("summary") if report else "Report file was not found."
        cards.append(
            '<article class="card">'
            f"<h3>{escape(label)}</h3>"
            f"{tag(status)}"
            f"<p>{escape(str(summary or 'No summary.'))}</p>"
            "</article>"
        )

    release = reports["Release Gate"] or {}
    reliability = reports["Team Reliability"] or {}
    drift = reports["Framework Drift"] or {}
    improvement_queue = reports["Improvement Queue"]
    conversation_feedback = reports["Conversation Feedback"]
    target_commands = reports["Target Commands"]
    target_drift = reports["Target Drift"]
    hardening = reports["Hardening"] or {}
    audit = reports["Requirements Audit"] or {}
    test_run = reports["Regression Tests"]

    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Autonomous SDLC Team Report</title>
  <style>
    :root {{
      --ink: #1f2933;
      --muted: #5f6f7a;
      --line: #d7dee4;
      --soft: #f6f8fa;
      --green: #4d7c0f;
      --amber: #b7791f;
      --red: #b42318;
      --blue: #2563a6;
      --teal: #0f766e;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: var(--ink);
      background: #ffffff;
      line-height: 1.45;
    }}
    header {{
      padding: 42px 48px 28px;
      border-bottom: 1px solid var(--line);
      background: #fbfcfd;
    }}
    header .eyebrow {{
      color: var(--teal);
      font-size: 12px;
      font-weight: 700;
      letter-spacing: .08em;
      text-transform: uppercase;
    }}
    h1 {{ margin: 8px 0; font-size: 34px; line-height: 1.1; }}
    h2 {{ margin: 0 0 16px; font-size: 22px; }}
    h3 {{ margin: 0 0 10px; font-size: 16px; }}
    main {{ max-width: 1180px; margin: 0 auto; padding: 28px 24px 48px; }}
    section {{
      margin: 0 0 28px;
      padding: 24px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fff;
    }}
    .cards {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
      gap: 14px;
      margin-top: 20px;
    }}
    .card {{
      padding: 16px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--soft);
      min-height: 136px;
    }}
    .card p {{ margin: 12px 0 0; color: var(--muted); font-size: 14px; }}
    .tag {{
      display: inline-block;
      padding: 3px 9px;
      border-radius: 999px;
      color: white;
      font-size: 12px;
      font-weight: 700;
    }}
    .tag.pass {{ background: var(--green); }}
    .tag.warn {{ background: var(--amber); }}
    .tag.fail {{ background: var(--red); }}
    .tag.neutral {{ background: var(--blue); }}
    table {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
    th, td {{
      padding: 10px 12px;
      border-bottom: 1px solid var(--line);
      text-align: left;
      vertical-align: top;
    }}
    th {{ background: var(--soft); font-weight: 700; }}
    .kv th {{ width: 190px; }}
    code {{ font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 12px; }}
    pre {{
      overflow: auto;
      padding: 14px;
      border-radius: 8px;
      background: #111827;
      color: #f9fafb;
      font-size: 12px;
    }}
    .muted {{ color: var(--muted); }}
    details {{
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fff;
      margin: 10px 0;
    }}
    summary {{
      cursor: pointer;
      list-style-position: inside;
      padding: 12px 14px;
      font-weight: 700;
    }}
    .test-section > summary {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 14px;
      background: var(--soft);
    }}
    .test-case {{ margin: 10px 14px; background: #ffffff; }}
    .test-case > summary code {{ white-space: normal; overflow-wrap: anywhere; }}
    .test-meta {{
      display: flex;
      gap: 12px;
      padding: 0 14px 10px;
      color: var(--muted);
      font-size: 13px;
    }}
    .test-params, .test-failure {{ padding: 0 14px; }}
    .source-code {{ margin: 0 14px 14px; }}
    .count {{ margin: 0 8px 0 3px; color: var(--muted); font-size: 13px; font-weight: 700; }}
    .two-col {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
    @media (max-width: 800px) {{
      header {{ padding: 28px 22px 20px; }}
      main {{ padding: 20px 14px 36px; }}
      .two-col {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <header>
    <div class="eyebrow">Generated {escape(generated_at)}</div>
    <h1>Autonomous SDLC Team Report</h1>
    <div class="muted">Human-readable evidence for role prompts, lifecycle gates, memory, hardening, reliability, and release readiness.</div>
    <div class="cards">{''.join(cards)}</div>
  </header>
  <main>
    {section("Regression Test Evidence", render_test_evidence(test_run))}
    {section("Release Gate Checks", render_checks(release.get("checks", {})))}
    {section("Target Repo Commands", render_target_commands(target_commands))}
    {section("Target Repo Drift", render_target_drift(target_drift))}
    {section("Improvement Queue", render_improvement_queue(improvement_queue))}
    {section("Conversation Feedback", render_conversation_feedback(conversation_feedback))}
    <div class="two-col">
      {section("Framework Drift Summary", kv_table({"status": drift.get("status"), "summary": drift.get("summary"), "generated_at": drift.get("generated_at")}))}
      {section("Team Reliability Summary", kv_table({"status": reliability.get("status"), "score": reliability.get("team_reliability_score"), "classification": reliability.get("run_classification"), "summary": reliability.get("summary")}))}
      {section("Hardening Summary", kv_table({"status": hardening.get("status"), "summary": hardening.get("summary"), "generated_at": hardening.get("generated_at")}))}
      {section("Requirements Audit Summary", kv_table({"status": audit.get("status"), "summary": audit.get("summary"), "generated_at": audit.get("generated_at")}))}
    </div>
  </main>
</body>
</html>
"""
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html, encoding="utf-8")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a combined HTML report for SDLC team evidence.")
    parser.add_argument("--report-dir", default=str(DEFAULT_REPORT_DIR))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()
    path = render_report(Path(args.report_dir), Path(args.output))
    print(path)


if __name__ == "__main__":
    main()
