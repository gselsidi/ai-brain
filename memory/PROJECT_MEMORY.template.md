# Project Memory Template

This file is the safe, tracked template for local project memory.

Copy it to `memory/PROJECT_MEMORY.md` in a working checkout when you want the
agent team to keep durable local context. The real `memory/PROJECT_MEMORY.md`
file is intentionally ignored by git so workspace notes, report summaries, and
local adoption details do not get published.

Keep local memory concise, factual, and high-signal. Do not store secrets,
credentials, private personal data, speculative scratch notes, or large logs.

## Current Project State

- Project: Autonomous SDLC Team Framework.
- Purpose: reusable autonomous full-stack SDLC team methodology for other teams
  and codebases.
- Runtime scope: no default product runtime is included. This repo contains
  role prompts, contracts, docs, deterministic tools, tests, templates, and
  report plumbing.
- `/goal` workflow: provider-native goal or planning input can clarify broad
  work when available, but it feeds the AI Brain SDLC loop. It does not replace
  prompt specs, checks, evidence, audits, or release gates.
- Generated evidence belongs under `state/reports/`; summarize only durable
  conclusions here.

## Stable Commands

```bash
./scripts/build_and_launch.sh
PATH=".venv/bin:$PATH" make lint
PATH=".venv/bin:$PATH" make test
PATH=".venv/bin:$PATH" make framework-check
PATH=".venv/bin:$PATH" make framework-drift
PATH=".venv/bin:$PATH" make improvement-queue
PATH=".venv/bin:$PATH" make harness-check
PATH=".venv/bin:$PATH" make team-reliability
PATH=".venv/bin:$PATH" make release-gate
PATH=".venv/bin:$PATH" make report-html
PATH=".venv/bin:$PATH" make maintenance-daily
```

## Important Files

- `AGENTS.md`: operating instructions and definition of done.
- `.codex/agents/*.toml`: specialist autonomous SDLC team role prompts.
- `specs/prompt_spec_template.md`: default template for per-prompt specs.
- `contracts/team_framework.yaml`: machine-readable role, artifact, docs, and
  report contract.
- `contracts/expected_behavior.md`: human-readable framework behavior.
- `contracts/agentic_framework_map.yaml`: lifecycle map.
- `memory/PROJECT_MEMORY.md`: local ignored durable context.
- `memory/PROJECT_MEMORY.template.md`: tracked safe memory template.
- `state/sdlc_state.json`: local ignored lifecycle state and report pointers.
- `state/sdlc_state.template.json`: tracked safe lifecycle-state template.
- `tools/run_tests_with_report.py`: pytest runner that records source-backed
  test evidence.
- `tools/run_release_gate.py`: final deterministic release gate.
- `docs/memory.md`: durable memory rules.

## Role Set

- `sdlc_orchestrator`
- `delivery_planner`
- `product_context_analyst`
- `interface_contract_architect`
- `dev_builder`
- `dev_test_writer`
- `quality_explorer`
- `adversarial_reviewer`
- `evidence_judge`
- `implementation_hardener`
- `security_reviewer`
- `docs_drift_guard`
- `requirements_auditor`
- `self_healer`
- `maintenance_heartbeat`
- `pr_reviewer`
- `release_gate`

## Known Scope Boundaries

- This repo supplies the autonomous SDLC team framework, not a target product.
- Adopting teams supply their own codebase, product contracts, product tests,
  domain checks, and deployment commands.
- Tiny direct answers may skip prompt specs, but artifact-changing project work
  should not begin until the current prompt spec is actionable.
- Broad or ambiguous work should document provider-native input or AI Brain
  clarification mode before moving to the durable prompt spec.
- Generated reports belong under `state/reports/`; memory stores only durable
  conclusions.
- Local memory and state files are ignored by git and should stay private to
  the checkout.

## Memory Maintenance Rules

- Update local `memory/PROJECT_MEMORY.md` when architecture, lifecycle status,
  commands, role names, adoption boundaries, or known limitations change.
- Prefer paths to detailed artifacts instead of copying large content.
- If local memory conflicts with source code, contracts, tests, or current
  reports, treat source artifacts as truth and update local memory.
