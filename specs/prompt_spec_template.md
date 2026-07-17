# Prompt Spec Template

Use this template for every project-work prompt before implementation starts.
Tiny direct questions may be answered without a spec, but any prompt that
changes code, docs, tests, contracts, memory, state, reports, automation, or
team workflow needs a durable spec file.

Recommended path:

```text
specs/YYYY-MM-DD_short_slug.md
```

## Prompt

Paste or summarize the user's concrete ask.

## Goal

State the implementation outcome in one short paragraph.

## /goal Clarification

Use this section for broad, ambiguous, risky, or outcome-oriented work.

- Success criteria:
- Non-goals:
- Constraints:
- Assumptions:
- Open questions that can be resolved from source:

## Prompt-To-Agent Routing

Use `contracts/domain_agent_routing.yaml` or `tools/select_agent_route.py` for
project-work prompts before assigning implementation chunks.

- Primary division:
- Adjacent divisions:
- Selected framework agents:
- Selected specialists:
- Deferred specialists:
- Selected source skills:
- Deferred source skills:
- Routing assumptions:
- Verification gates:

## Delegation Decision

- Qualifying independent workstreams:
- Child assignments (objective, scope, artifact, verification):
- If staying single-agent, allowed exception and reason:

## Requirements Checklist

- [ ] Requirement copied from the user's ask.
- [ ] Requirement copied from the user's ask.

## Scope Boundaries

- What this spec will not change.
- Any product, runtime, security, or adoption boundary.

## Agent Ownership

| Chunk | Owner | Purpose |
| --- | --- | --- |
| 1 | `delivery_planner` | Break the work into small verifiable tasks. |
| 2 | `sdlc_orchestrator` | Coordinate implementation and evidence. |

## Implementation Chunks

| Chunk | Work | Files Or Artifacts | Verification |
| --- | --- | --- | --- |
| 1 | Small task | Path or artifact | Command or report |

## Expected Evidence

- Tests:
- Docs:
- Contracts:
- Memory/state:
- Reports:

## Completion Audit

- [ ] Each requirement maps to changed artifacts or a documented boundary.
- [ ] Verification commands pass.
- [ ] Requirements audit and release evidence are current when release is
  claimed.
