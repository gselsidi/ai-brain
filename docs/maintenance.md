# Maintenance And Heartbeats

Scheduled maintenance should run the same checks a careful framework maintainer
would run.

## Daily

- lint
- framework map validation
- source-backed regression tests
- framework drift check across role prompts, contracts, docs, memory, reports,
  and tests
- prompt spec workflow checks through framework drift and harness quality
- improvement queue scan with strict score and ranked next items
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
make lint
make framework-check
make framework-drift
make improvement-queue
make harness-check
make test
make team-reliability
make release-gate
make report-html
```
