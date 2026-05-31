from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "state" / "reports" / "improvement-queue_report.json"

SCAN_SUFFIXES = {".md", ".py", ".sh", ".toml", ".yaml", ".yml"}
EXCLUDED_DIRS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "autonomous_sdlc_team.egg-info",
    "site",
}
EXCLUDED_PREFIXES = {
    "state/agent_runs",
    "state/reports",
}
CONFIDENCE_WEIGHT = {"high": 1.0, "medium": 0.7, "low": 0.4}
STATUS_WEIGHT_STRICT = {
    "open": 1.0,
    "deferred": 1.0,
    "wontfix": 1.0,
    "suppressed": 1.0,
    "fixed": 0.0,
    "false_positive": 0.0,
}
STATUS_WEIGHT_LENIENT = {
    "open": 1.0,
    "deferred": 0.5,
    "wontfix": 0.25,
    "suppressed": 0.25,
    "fixed": 0.0,
    "false_positive": 0.0,
}
DIMENSION_WEIGHT = {
    "maintainability": 1.0,
    "prompt_spec_hygiene": 1.1,
    "release_evidence": 1.2,
    "security_hygiene": 1.4,
    "test_health": 1.2,
}
TODO_RE = re.compile(r"\b(TODO|FIXME|HACK)\b\s*[:(]", re.IGNORECASE)


@dataclass(frozen=True)
class Finding:
    id: str
    detector: str
    dimension: str
    path: str
    line: int
    severity: int
    confidence: str
    status: str
    summary: str
    evidence: str
    remediation: str
    first_seen_at: str
    last_seen_at: str

    @property
    def priority(self) -> float:
        confidence = CONFIDENCE_WEIGHT.get(self.confidence, 0.4)
        dimension = DIMENSION_WEIGHT.get(self.dimension, 1.0)
        status = STATUS_WEIGHT_STRICT.get(self.status, 1.0)
        return round(self.severity * confidence * dimension * status, 3)

    @property
    def resolve_command(self) -> str:
        return "make improvement-queue"


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def relative(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def should_scan(path: Path, root: Path) -> bool:
    rel = relative(path, root)
    if any(part in EXCLUDED_DIRS for part in path.parts):
        return False
    if any(rel == prefix or rel.startswith(f"{prefix}/") for prefix in EXCLUDED_PREFIXES):
        return False
    return path.suffix in SCAN_SUFFIXES


def iter_scan_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*") if path.is_file() and should_scan(path, root))


def stable_id(detector: str, path: str, line: int, summary: str) -> str:
    digest = hashlib.sha1(f"{detector}:{path}:{line}:{summary}".encode()).hexdigest()[:12]
    return f"{detector}:{path}:{line}:{digest}"


def make_finding(
    *,
    detector: str,
    dimension: str,
    path: str,
    line: int,
    severity: int,
    confidence: str,
    summary: str,
    evidence: str,
    remediation: str,
    generated_at: str,
    previous: dict[str, dict[str, Any]],
) -> Finding:
    finding_id = stable_id(detector, path, line, summary)
    prior = previous.get(finding_id, {})
    status = str(prior.get("status") or "open")
    first_seen = str(prior.get("first_seen_at") or generated_at)
    return Finding(
        id=finding_id,
        detector=detector,
        dimension=dimension,
        path=path,
        line=line,
        severity=severity,
        confidence=confidence,
        status=status,
        summary=summary,
        evidence=evidence.strip(),
        remediation=remediation,
        first_seen_at=first_seen,
        last_seen_at=generated_at,
    )


def load_previous_findings(output: Path) -> dict[str, dict[str, Any]]:
    if not output.exists():
        return {}
    try:
        payload = json.loads(output.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    findings = payload.get("findings", [])
    if not isinstance(findings, list):
        return {}
    return {
        str(item.get("id")): item
        for item in findings
        if isinstance(item, dict) and item.get("id")
    }


def text_findings(
    path: Path,
    *,
    root: Path,
    generated_at: str,
    previous: dict[str, dict[str, Any]],
) -> list[Finding]:
    rel = relative(path, root)
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        return []

    findings: list[Finding] = []
    for index, line in enumerate(lines, start=1):
        if TODO_RE.search(line):
            findings.append(
                make_finding(
                    detector="explicit_todo_marker",
                    dimension="maintainability",
                    path=rel,
                    line=index,
                    severity=3,
                    confidence="medium",
                    summary="Explicit TODO/FIXME/HACK marker remains in harness source.",
                    evidence=line,
                    remediation="Either complete the work, move it into a prompt spec, or document why it is intentionally deferred.",
                    generated_at=generated_at,
                    previous=previous,
                )
            )
    if len(lines) > 350 and rel.startswith(("tools/", "team_framework/", "tests/")):
        findings.append(
            make_finding(
                detector="large_harness_file",
                dimension="maintainability",
                path=rel,
                line=351,
                severity=3,
                confidence="high",
                summary="Harness file is large enough to deserve periodic simplification review.",
                evidence=f"{len(lines)} lines",
                remediation="During a hardening pass, split cohesive helpers or document why the file should remain consolidated.",
                generated_at=generated_at,
                previous=previous,
            )
        )
    return findings


def python_ast_findings(
    path: Path,
    *,
    root: Path,
    generated_at: str,
    previous: dict[str, dict[str, Any]],
) -> list[Finding]:
    if path.suffix != ".py":
        return []
    rel = relative(path, root)
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=rel)
    except (SyntaxError, UnicodeDecodeError):
        return []

    findings: list[Finding] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and is_debug_call(node):
            line = int(getattr(node, "lineno", 1))
            findings.append(
                make_finding(
                    detector="debug_breakpoint",
                    dimension="release_evidence",
                    path=rel,
                    line=line,
                    severity=10,
                    confidence="high",
                    summary="Interactive debugger call would block automated harness runs.",
                    evidence=ast.unparse(node),
                    remediation="Remove the debugger call and add deterministic regression evidence.",
                    generated_at=generated_at,
                    previous=previous,
                )
            )
        if not isinstance(node, ast.ExceptHandler):
            continue
        line = int(getattr(node, "lineno", 1))
        if node.type is None:
            findings.append(
                make_finding(
                    detector="bare_except",
                    dimension="security_hygiene",
                    path=rel,
                    line=line,
                    severity=10,
                    confidence="high",
                    summary="Bare except hides failures from deterministic harness checks.",
                    evidence="except:",
                    remediation="Catch the narrow exception type and preserve actionable failure evidence.",
                    generated_at=generated_at,
                    previous=previous,
                )
            )
            continue
        if isinstance(node.type, ast.Name) and node.type.id == "Exception":
            findings.append(
                make_finding(
                    detector="broad_exception",
                    dimension="maintainability",
                    path=rel,
                    line=line,
                    severity=5,
                    confidence="medium",
                    summary="Broad Exception handler may mask useful release-gate diagnostics.",
                    evidence="except Exception",
                    remediation="Catch the narrow expected exception or record why broad recovery is required.",
                    generated_at=generated_at,
                    previous=previous,
                )
            )
    return findings


def is_debug_call(node: ast.Call) -> bool:
    func = node.func
    if isinstance(func, ast.Name):
        return func.id == "breakpoint"
    if not isinstance(func, ast.Attribute):
        return False
    return (
        func.attr == "set_trace"
        and isinstance(func.value, ast.Name)
        and func.value.id == "pdb"
    )


def prompt_spec_findings(
    *,
    root: Path,
    generated_at: str,
    previous: dict[str, dict[str, Any]],
) -> list[Finding]:
    findings: list[Finding] = []
    for path in sorted((root / "specs").glob("*.md")):
        if path.name == "prompt_spec_template.md":
            continue
        rel = relative(path, root)
        text = path.read_text(encoding="utf-8")
        if "Completion Audit" not in text:
            findings.append(
                make_finding(
                    detector="missing_completion_audit",
                    dimension="prompt_spec_hygiene",
                    path=rel,
                    line=1,
                    severity=6,
                    confidence="high",
                    summary="Prompt spec is missing a completion audit section.",
                    evidence="Completion Audit section not found",
                    remediation="Add a completion audit so requirements can be mapped to evidence.",
                    generated_at=generated_at,
                    previous=previous,
                )
            )
    return findings


def score_findings(findings: list[Finding], *, scanned_files: int, mode: str) -> float:
    status_weights = STATUS_WEIGHT_STRICT if mode == "strict" else STATUS_WEIGHT_LENIENT
    divisor = max(1.0, scanned_files / 15.0)
    penalty = 0.0
    for finding in findings:
        confidence = CONFIDENCE_WEIGHT.get(finding.confidence, 0.4)
        status = status_weights.get(finding.status, 1.0)
        dimension = DIMENSION_WEIGHT.get(finding.dimension, 1.0)
        penalty += finding.severity * confidence * dimension * status / divisor
    return round(max(0.0, 100.0 - penalty), 2)


def dimension_summary(findings: list[Finding]) -> dict[str, dict[str, Any]]:
    summary: dict[str, dict[str, Any]] = {}
    for finding in findings:
        entry = summary.setdefault(
            finding.dimension,
            {"open_count": 0, "max_severity": 0, "priority": 0.0},
        )
        if finding.status in STATUS_WEIGHT_STRICT:
            entry["open_count"] += 1
        entry["max_severity"] = max(int(entry["max_severity"]), finding.severity)
        entry["priority"] = round(float(entry["priority"]) + finding.priority, 3)
    return dict(sorted(summary.items()))


def build_report(
    *,
    root: Path = ROOT,
    output: Path = DEFAULT_OUTPUT,
    generated_at: str | None = None,
) -> dict[str, Any]:
    generated_at = generated_at or utc_now()
    previous = load_previous_findings(output)
    scan_files = iter_scan_files(root)

    findings: list[Finding] = []
    for path in scan_files:
        findings.extend(
            text_findings(path, root=root, generated_at=generated_at, previous=previous)
        )
        findings.extend(
            python_ast_findings(path, root=root, generated_at=generated_at, previous=previous)
        )
    findings.extend(prompt_spec_findings(root=root, generated_at=generated_at, previous=previous))

    findings = sorted(
        findings,
        key=lambda item: (-item.priority, -item.severity, item.path, item.line, item.id),
    )
    strict_score = score_findings(findings, scanned_files=len(scan_files), mode="strict")
    lenient_score = score_findings(findings, scanned_files=len(scan_files), mode="lenient")
    blockers = [
        finding
        for finding in findings
        if finding.status in STATUS_WEIGHT_STRICT and finding.severity >= 9
    ]
    status = "PASS" if not blockers and strict_score >= 75 else "FAIL"

    payload = {
        "mode": "improvement-queue",
        "status": status,
        "generated_at": generated_at,
        "summary": (
            "Improvement queue passed: no release-blocking harness quality debt was found."
            if status == "PASS"
            else "Improvement queue failed; resolve release-blocking harness quality debt."
        ),
        "source_inspiration": {
            "repository": "https://github.com/peteromallet/desloppify",
            "inspected_commit": "3a7735d531a96b6a226bfbdc9fd662b14195f857",
            "adopted_ideas": [
                "scan-score-queue-rescan loop",
                "strict score that still counts deferred or suppressed work",
                "ranked next-item execution queue",
                "generated/local-state exclusions",
            ],
            "copied_code": False,
        },
        "scores": {
            "strict": strict_score,
            "lenient": lenient_score,
            "threshold": 75,
        },
        "scanned_files": len(scan_files),
        "finding_count": len(findings),
        "blocker_count": len(blockers),
        "dimensions": dimension_summary(findings),
        "next_items": [
            asdict(finding) | {"priority": finding.priority, "resolve_command": finding.resolve_command}
            for finding in findings[:8]
        ],
        "findings": [
            asdict(finding) | {"priority": finding.priority, "resolve_command": finding.resolve_command}
            for finding in findings
        ],
    }
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the AI Brain improvement queue gate.")
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()

    output = Path(args.output)
    result = build_report(root=Path(args.root), output=output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
