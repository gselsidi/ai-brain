# Automation Prompt Templates

These are templates for Codex thread automations or scheduled CI tasks.

For a GitHub Actions placeholder that demonstrates how CI could invoke a real
Codex agent, see [Codex In GitHub Actions](codex_github_actions.md).

## Codex App Automation Models

Codex app automations have their own top-level model setting for the scheduled
worker. Specialist role files under `.codex/agents/*.toml` declare their own
intended models when the runtime supports delegation.

Make targets remain deterministic either way. Running `make maintenance-daily`
from an automation does not make tests or release gates conversational; commands
still write evidence for Codex to inspect.

## Daily Maintenance

```text
Use maintenance_heartbeat. Run lint, tests, framework drift, harness quality,
repo-scoped conversation feedback when due, combined report generation, team
reliability scoring, and release gate. If anything fails, update local
state/sdlc_state.json when present and ask self_healer to repair. Set
AI_BRAIN_FEEDBACK_CADENCE_DAYS to choose the feedback interval.
```

## Weekly Review

```text
Use security_reviewer, docs_drift_guard, and pr_reviewer. Review the repo for
security risk, stale docs, TODOs that affect correctness, and missing framework
evidence. Produce reports under state/reports/.
```

## Post-Change Gate

```text
Use release_gate. Review tests, framework drift report, harness quality report,
team reliability report, security review, docs drift, requirements audit, and
combined report. Return PASS or FAIL with blocking reasons.
```
