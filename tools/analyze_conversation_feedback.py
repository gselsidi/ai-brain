from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SESSION_DIR = Path.home() / ".codex" / "sessions"
DEFAULT_OUTPUT = ROOT / "state" / "reports" / "conversation-feedback_report.json"
DEFAULT_PATCH_BRIEF = ROOT / "state" / "reports" / "conversation-feedback_patch_brief.md"
DEFAULT_STATE = ROOT / "state" / "conversation_feedback_state.local.json"

BOILERPLATE_MARKERS = {
    "# AGENTS.md instructions",
    "<INSTRUCTIONS>",
    "</INSTRUCTIONS>",
    "<environment_context>",
    "<collaboration_mode>",
    "<permissions instructions>",
    "<apps_instructions>",
    "<skills_instructions>",
    "<plugins_instructions>",
    "# Project Agent Instructions",
    "Mandatory Start-Of-Turn Protocol",
    "Knowledge cutoff:",
    "You are Codex",
}
BLOCK_START_MARKERS = {
    "# AGENTS.md instructions",
    "<INSTRUCTIONS>",
    "<environment_context>",
    "<permissions instructions>",
    "<apps_instructions>",
    "<skills_instructions>",
    "<plugins_instructions>",
    "<developer_context",
}
BLOCK_END_MARKERS = {
    "</INSTRUCTIONS>",
    "</environment_context>",
    "</permissions instructions>",
    "</apps_instructions>",
    "</skills_instructions>",
    "</plugins_instructions>",
}
NOISE_PATTERNS = [
    re.compile(r"^process exited with code:? \d+", re.IGNORECASE),
    re.compile(r"^wall time:?", re.IGNORECASE),
    re.compile(r"^original token count:?", re.IGNORECASE),
    re.compile(r"^sandbox permissions:?", re.IGNORECASE),
    re.compile(r"^\[\d+\] (tool|function|custom_tool|web_search)[_ ]", re.IGNORECASE),
    re.compile(r'^"mode": ', re.IGNORECASE),
    re.compile(r"^the codex agent has requested ", re.IGNORECASE),
    re.compile(r"^assess the exact planned action below", re.IGNORECASE),
    re.compile(r"^the following is the codex agent history", re.IGNORECASE),
    re.compile(r"^\d+ history$", re.IGNORECASE),
    re.compile(r"^\d+ (container|toolbar|button|checkbox|link) ", re.IGNORECASE),
    re.compile(r"\b(settable|inactive tab|memory usage|omitted_approx_tokens)\b", re.IGNORECASE),
    re.compile(r"\breviewed codex session id\b", re.IGNORECASE),
    re.compile(r"\b(app com\.google\.chrome|yarn run v|lint-staged)\b", re.IGNORECASE),
    re.compile(r"^(computer use state|window cloudflare dashboard)", re.IGNORECASE),
    re.compile(r"^-rw[-rwx@ ]+\s+\d+\s+", re.IGNORECASE),
    re.compile(r"^[\w./ -]+\.(md|py|ts|tsx|js|json|yaml|yml|toml)$", re.IGNORECASE),
    re.compile(r"^success updated the following files", re.IGNORECASE),
    re.compile(r"^warning package\.json no license field", re.IGNORECASE),
]
SECRET_PATTERNS = [
    re.compile(r"github_pat_[A-Za-z0-9_]+"),
    re.compile(r"ghp_[A-Za-z0-9]+"),
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"ASIA[0-9A-Z]{16}"),
    re.compile(r"AIza[0-9A-Za-z_-]{35}"),
    re.compile(r"xox[baprs]-[A-Za-z0-9-]+"),
    re.compile(
        r"\b([A-Z0-9_]*(?:SECRET|TOKEN|PASSWORD|API_KEY|PRIVATE_KEY)[A-Z0-9_]*)\s*=\s*([^\s]+)",
        re.IGNORECASE,
    ),
]
WORD_RE = re.compile(r"[a-z0-9][a-z0-9'/-]*")
CODE_FENCE_RE = re.compile(r"```.*?```", re.DOTALL)


@dataclass(frozen=True)
class FrictionFinding:
    id: str
    category: str
    severity: int
    count: int
    summary: str
    evidence: list[str]
    suggested_patch: str
    owner: str


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def stable_id(category: str, summary: str) -> str:
    digest = hashlib.sha1(f"{category}:{summary}".encode()).hexdigest()[:12]
    return f"{category}:{digest}"


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def should_run_for_cadence(state_path: Path, cadence_days: int, *, now: datetime) -> bool:
    if cadence_days <= 0:
        return True
    state = load_json(state_path)
    if not isinstance(state, dict):
        return True
    last_run = state.get("last_run_at")
    if not isinstance(last_run, str):
        return True
    try:
        last_run_at = datetime.fromisoformat(last_run)
    except ValueError:
        return True
    if last_run_at.tzinfo is None:
        last_run_at = last_run_at.replace(tzinfo=UTC)
    return now - last_run_at >= timedelta(days=cadence_days)


def iter_session_files(session_dir: Path) -> list[Path]:
    if not session_dir.exists():
        return []
    return sorted(
        path
        for path in session_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in {".jsonl", ".json", ".log", ".txt", ".md"}
    )


def file_mentions_project(path: Path, project_root: Path, project_token: str | None) -> bool:
    needle = project_root.resolve().as_posix()
    token = project_token.strip() if project_token else ""
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return False
    return needle in text or bool(token and token in text)


METADATA_KEYS = {
    "id",
    "uuid",
    "session_id",
    "conversation_id",
    "parent_id",
    "timestamp",
    "created_at",
    "updated_at",
    "model",
}


def extract_strings(value: Any, *, parent_key: str = "") -> list[str]:
    if isinstance(value, str):
        if parent_key in METADATA_KEYS:
            return []
        return [value]
    if isinstance(value, list):
        strings: list[str] = []
        for item in value:
            strings.extend(extract_strings(item, parent_key=parent_key))
        return strings
    if isinstance(value, dict):
        strings = []
        for key, item in value.items():
            strings.extend(extract_strings(item, parent_key=str(key)))
        return strings
    return []


def extract_user_strings_from_record(record: dict[str, Any]) -> list[str]:
    payload = record.get("payload")
    if not isinstance(payload, dict):
        return []
    if record.get("type") == "response_item":
        if payload.get("type") == "message" and payload.get("role") == "user":
            return extract_strings(payload.get("content"))
        return []
    if record.get("type") == "event_msg" and payload.get("type") == "user_message":
        return extract_strings(payload.get("message"))
    return []


def load_session_text(path: Path) -> list[str]:
    raw = path.read_text(encoding="utf-8", errors="ignore")
    strings: list[str] = []
    if path.suffix.lower() == ".jsonl":
        for line in raw.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                parsed = json.loads(line)
            except json.JSONDecodeError:
                strings.append(line)
                continue
            if isinstance(parsed, dict):
                strings.extend(extract_user_strings_from_record(parsed))
        return strings
    if path.suffix.lower() == ".json":
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return [raw]
        if isinstance(parsed, list):
            for item in parsed:
                if isinstance(item, dict):
                    strings.extend(extract_user_strings_from_record(item))
            return strings
        if isinstance(parsed, dict):
            return extract_user_strings_from_record(parsed)
        return []
    return [raw]


def redact(text: str) -> str:
    redacted = text
    for pattern in SECRET_PATTERNS:
        if pattern.groups >= 2:
            redacted = pattern.sub(r"\1=[REDACTED_SECRET]", redacted)
        else:
            redacted = pattern.sub("[REDACTED_SECRET]", redacted)
    return redacted


def clean_text(text: str, project_root: Path) -> list[str]:
    redacted = redact(text).replace(project_root.resolve().as_posix(), "[PROJECT_ROOT]")
    redacted = CODE_FENCE_RE.sub(" ", redacted)
    cleaned: list[str] = []
    in_boilerplate_block = False
    for raw_line in redacted.splitlines():
        line = " ".join(raw_line.strip().split())
        if not line:
            continue
        if any(marker in line for marker in BLOCK_START_MARKERS):
            in_boilerplate_block = True
            continue
        if in_boilerplate_block:
            if any(marker in line for marker in BLOCK_END_MARKERS):
                in_boilerplate_block = False
            continue
        if any(marker in line for marker in BOILERPLATE_MARKERS):
            continue
        if any(pattern.search(line) for pattern in NOISE_PATTERNS):
            continue
        if len(line) > 800:
            continue
        cleaned.append(line)
    return cleaned


def normalized_phrase(line: str) -> str | None:
    words = WORD_RE.findall(line.lower())
    if not (4 <= len(words) <= 18):
        return None
    phrase = " ".join(words)
    if phrase.startswith(("you are ", "current date ", "knowledge cutoff ")):
        return None
    return phrase


def collect_project_lines(
    *,
    session_dir: Path,
    project_root: Path,
    project_token: str | None,
) -> tuple[list[str], list[str]]:
    session_files = [
        path
        for path in iter_session_files(session_dir)
        if file_mentions_project(path, project_root, project_token)
    ]
    lines: list[str] = []
    for path in session_files:
        for text in load_session_text(path):
            lines.extend(clean_text(text, project_root))
    return lines, [str(path) for path in session_files]


def evidence_for(lines: list[str], pattern: re.Pattern[str], limit: int = 3) -> list[str]:
    matches = []
    for line in lines:
        if pattern.search(line):
            matches.append(line[:220])
        if len(matches) >= limit:
            break
    return matches


def make_finding(
    *,
    category: str,
    severity: int,
    count: int,
    summary: str,
    evidence: list[str],
    suggested_patch: str,
    owner: str,
) -> FrictionFinding:
    return FrictionFinding(
        id=stable_id(category, summary),
        category=category,
        severity=severity,
        count=count,
        summary=summary,
        evidence=evidence,
        suggested_patch=suggested_patch,
        owner=owner,
    )


def detect_findings(lines: list[str]) -> list[FrictionFinding]:
    joined = "\n".join(lines)
    patterns = {
        "correction_loop": re.compile(
            r"\b(no i meant|actually|still|wtf|bro|you left|not supposed|i mean)\b",
            re.IGNORECASE,
        ),
        "public_hygiene": re.compile(
            r"\b(secret|password|identifying|repo history|git history|history cleanup|force push|delete.*repo|scrub)\b",
            re.IGNORECASE,
        ),
        "docs_friction": re.compile(r"\b(readme|docs?|documentation|salesly|slop)\b", re.IGNORECASE),
        "gate_friction": re.compile(
            r"\b(test failed|release gate|framework-drift|harness-check|make test)\b",
            re.IGNORECASE,
        ),
        "memory_state_hygiene": re.compile(r"\b(memory|state|specs?/|gitignore)\b", re.IGNORECASE),
    }
    counts = {name: len(pattern.findall(joined)) for name, pattern in patterns.items()}
    findings: list[FrictionFinding] = []
    if counts["correction_loop"] >= 2:
        findings.append(
            make_finding(
                category="correction_loop",
                severity=7,
                count=counts["correction_loop"],
                summary="User correction language repeated; instructions may need a clearer default behavior.",
                evidence=evidence_for(lines, patterns["correction_loop"]),
                suggested_patch="Tighten AGENTS.md or README defaults around the repeated correction so future runs choose the expected behavior first.",
                owner="requirements_auditor",
            )
        )
    if counts["public_hygiene"] >= 2:
        findings.append(
            make_finding(
                category="public_hygiene",
                severity=8,
                count=counts["public_hygiene"],
                summary="Public-source hygiene came up repeatedly.",
                evidence=evidence_for(lines, patterns["public_hygiene"]),
                suggested_patch="Add or strengthen a pre-publish hygiene checklist covering ignored memory, generated reports, specs, identifiers, secrets, and history cleanup.",
                owner="security_reviewer",
            )
        )
    if counts["docs_friction"] >= 2:
        findings.append(
            make_finding(
                category="docs_friction",
                severity=5,
                count=counts["docs_friction"],
                summary="Documentation wording or positioning caused repeated friction.",
                evidence=evidence_for(lines, patterns["docs_friction"]),
                suggested_patch="Patch README/docs so the expected user-facing positioning appears at the top and stale maintainer detail moves lower or out.",
                owner="docs_drift_guard",
            )
        )
    if counts["gate_friction"] >= 2:
        findings.append(
            make_finding(
                category="gate_friction",
                severity=6,
                count=counts["gate_friction"],
                summary="Gate failures or repeated verification commands were part of the workflow friction.",
                evidence=evidence_for(lines, patterns["gate_friction"]),
                suggested_patch="Add a regression test or Make target that catches this class of failure before the final release gate.",
                owner="self_healer",
            )
        )
    if counts["memory_state_hygiene"] >= 3:
        findings.append(
            make_finding(
                category="memory_state_hygiene",
                severity=6,
                count=counts["memory_state_hygiene"],
                summary="Memory, state, or spec hygiene appeared often enough to deserve a guardrail.",
                evidence=evidence_for(lines, patterns["memory_state_hygiene"]),
                suggested_patch="Keep local memory/state/spec rules explicit in .gitignore, docs, tests, and role prompts.",
                owner="security_reviewer",
            )
        )
    return sorted(findings, key=lambda item: (-item.severity, -item.count, item.category))


def repeated_phrases(lines: list[str], limit: int = 10) -> list[dict[str, Any]]:
    counter: Counter[str] = Counter()
    for line in lines:
        phrase = normalized_phrase(line)
        if phrase:
            counter[phrase] += 1
    return [
        {"phrase": phrase, "count": count}
        for phrase, count in counter.most_common(limit)
        if count > 1
    ]


def write_patch_brief(path: Path, report: dict[str, Any]) -> None:
    findings = report.get("findings", [])
    lines = [
        "# Conversation Feedback Patch Brief",
        "",
        f"Generated: {report.get('generated_at')}",
        f"Target root: `{report.get('project_root')}`",
        "",
        "Use this as input to the normal AI Brain SDLC loop. Do not paste raw",
        "private chat logs into public docs or commits.",
        "",
    ]
    if not findings:
        lines.append("No recurring repo-scoped friction patterns were found.")
    for finding in findings:
        lines.extend(
            [
                f"## {finding['category']}",
                "",
                f"- Owner: `{finding['owner']}`",
                f"- Severity: `{finding['severity']}`",
                f"- Count: `{finding['count']}`",
                f"- Summary: {finding['summary']}",
                f"- Suggested patch: {finding['suggested_patch']}",
                "",
            ]
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_report(
    *,
    session_dir: Path = DEFAULT_SESSION_DIR,
    project_root: Path = ROOT,
    output: Path = DEFAULT_OUTPUT,
    patch_brief: Path = DEFAULT_PATCH_BRIEF,
    state_path: Path = DEFAULT_STATE,
    cadence_days: int = 7,
    force: bool = False,
    project_token: str | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    now = (
        datetime.fromisoformat(generated_at)
        if generated_at
        else datetime.now(UTC)
    )
    if now.tzinfo is None:
        now = now.replace(tzinfo=UTC)
    generated_at = now.isoformat()

    if not force and not should_run_for_cadence(state_path, cadence_days, now=now):
        report = {
            "mode": "conversation-feedback",
            "status": "SKIP",
            "generated_at": generated_at,
            "summary": f"Conversation feedback skipped; cadence is {cadence_days} day(s).",
            "project_root": project_root.resolve().as_posix(),
            "session_dir": session_dir.as_posix(),
            "cadence_days": cadence_days,
            "scanned_session_count": 0,
            "cleaned_line_count": 0,
            "findings": [],
            "repeated_phrases": [],
            "patch_brief": patch_brief.as_posix(),
        }
        write_json(output, report)
        return report

    lines, session_files = collect_project_lines(
        session_dir=session_dir,
        project_root=project_root,
        project_token=project_token,
    )
    findings = [asdict(finding) for finding in detect_findings(lines)]
    status = "PASS"
    if not session_files:
        summary = "No repo-scoped Codex chat/session files were found; nothing to update."
    elif not findings:
        summary = "Conversation feedback passed: no recurring repo-scoped friction patterns were found."
    else:
        summary = "Conversation feedback found recurring repo-scoped friction patterns to review."
    report = {
        "mode": "conversation-feedback",
        "status": status,
        "generated_at": generated_at,
        "summary": summary,
        "project_root": project_root.resolve().as_posix(),
        "session_dir": session_dir.as_posix(),
        "cadence_days": cadence_days,
        "scanned_session_count": len(session_files),
        "cleaned_line_count": len(lines),
        "findings": findings,
        "repeated_phrases": repeated_phrases(lines),
        "patch_brief": patch_brief.as_posix(),
        "privacy": {
            "repo_scoped_only": True,
            "raw_chat_not_written": True,
            "boilerplate_filtered": True,
            "secret_patterns_redacted": True,
        },
    }
    write_json(output, report)
    write_patch_brief(patch_brief, report)
    write_json(state_path, {"last_run_at": generated_at, "last_status": status})
    return report


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analyze repo-scoped Codex conversations for repeated friction patterns."
    )
    parser.add_argument("--session-dir", default=os.environ.get("CODEX_SESSION_DIR", str(DEFAULT_SESSION_DIR)))
    parser.add_argument("--project-root", default=os.environ.get("AI_BRAIN_TARGET_ROOT", str(ROOT)))
    parser.add_argument("--project-token", default=os.environ.get("AI_BRAIN_PROJECT_TOKEN"))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--patch-brief", default=str(DEFAULT_PATCH_BRIEF))
    parser.add_argument("--state", default=str(DEFAULT_STATE))
    parser.add_argument(
        "--cadence-days",
        type=int,
        default=int(os.environ.get("AI_BRAIN_FEEDBACK_CADENCE_DAYS", "7")),
    )
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    result = build_report(
        session_dir=Path(args.session_dir).expanduser(),
        project_root=Path(args.project_root).expanduser(),
        output=Path(args.output),
        patch_brief=Path(args.patch_brief),
        state_path=Path(args.state),
        cadence_days=args.cadence_days,
        force=args.force,
        project_token=args.project_token,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["status"] in {"PASS", "SKIP"} else 1)


if __name__ == "__main__":
    main()
