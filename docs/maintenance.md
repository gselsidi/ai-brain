# Maintenance And Heartbeats

Scheduled maintenance should run the same checks a careful framework maintainer
would run.

## Daily

- lint
- repo initialization through `make init-repo`
- framework map validation
- source-backed regression tests
- target repo commands through `make target-check`
- target repo drift through `make target-drift`
- framework drift check across role prompts, contracts, docs, memory, reports,
  and tests
- prompt spec workflow checks through framework drift and harness quality
- improvement queue scan with strict score and ranked next items
- repo-scoped conversation feedback when the local cadence is due
- combined report generation
- harness quality validation
- team reliability scoring
- release gate

Run the full local heartbeat with:

```bash
PATH=".venv/bin:$PATH" make maintenance-daily
```

## Framework Drift

`make framework-drift` writes
`state/reports/implementation-drift_report.json`. It verifies:

- required artifacts exist
- role prompts listed in `contracts/team_framework.yaml` exist
- role prompts do not contain retired product-domain terms
- docs contain required adoption and evidence markers
- orchestrator prompts still require prompt specs, memory, hardening, audit, and
  release gates
- regression evidence is source-backed and layered

## Improvement Queue

`make improvement-queue` writes
`state/reports/improvement-queue_report.json`. It adapts the useful
Desloppify loop for this harness: scan deterministic source artifacts, compute a
strict score, rank the next maintainability items, fix or consciously defer
work, and rescan. The queue excludes generated/local state such as `site/`,
`.venv/`, caches, and `state/reports/` so the signal stays focused on source
artifacts.

The release gate fails if the queue finds blocker-severity debt or the strict
score drops below its threshold. Non-blocking findings remain visible in the
combined report so maintenance can chip away over time.

## Conversation Feedback

`make conversation-feedback` writes
`state/reports/conversation-feedback_report.json` and
`state/reports/conversation-feedback_patch_brief.md`.

This is the repo-scoped version of the "learn from repeated chats" idea. It does
not read every Codex chat on the computer. It only considers local session files
that mention the configured project root, strips repeated instruction
boilerplate such as `AGENTS.md`, redacts common secret/token patterns, and
summarizes recurring friction. The output is a patch brief for the normal SDLC
loop, not an automatic rewrite of public source from private chat data.

Run it for the current checkout:

```bash
PATH=".venv/bin:$PATH" make conversation-feedback
```

Run it for a deployed project:

```bash
AI_BRAIN_TARGET_ROOT=/path/to/project \
CODEX_SESSION_DIR="$HOME/.codex/sessions" \
AI_BRAIN_FEEDBACK_CADENCE_DAYS=7 \
PATH=".venv/bin:$PATH" make conversation-feedback-due
```

Use `AI_BRAIN_PROJECT_TOKEN` only when the session logs do not contain a stable
absolute project path. Keep that token repo-specific, never personal.

## Team Reliability

Maintenance writes `state/reports/team-reliability_report.json` and appends one
line per scored run to `state/reports/team-reliability_history.jsonl`.

The score separates product quality from team-process quality:

- A true regression caught by tests or review is a caught regression. It can
  fail release, but it is credited to the team process.
- A missing report, malformed evidence, failed harness-quality gate, or failed
  framework drift gate is a team reliability issue.
- Escaped regression feedback can be added to `state/team_feedback.jsonl`; those
  entries lower the score and should trigger regression coverage.

Feedback entries are newline-delimited JSON:

```json
{"id":"BUG-123","classification":"escaped_regression","severity":"high","summary":"A release gap was reported after completion."}
```

Supported classifications:

- `caught_regression`, `caught_by_review`, `caught_by_tests`
- `escaped_regression`, `missed_regression`, `process_miss`
- `false_positive`, `false_alarm`

## Weekly

- security review
- dependency review
- stale assumption review
- requirements-audit spot check against recent prompts and memory

## Failure Behavior

If maintenance fails:

1. preserve the failing report
2. update local `state/sdlc_state.json` when present
3. route the problem to `self_healer`
4. repair the smallest safe slice
5. rerun the failed checks
6. rerun release evidence

## Current Local Commands

```bash
./scripts/build_and_launch.sh
source .venv/bin/activate
make init-repo
make lint
make framework-check
make framework-drift
make target-check
make target-drift
make improvement-queue
make conversation-feedback
make harness-check
make test
make team-reliability
make release-gate
make report-html
```
