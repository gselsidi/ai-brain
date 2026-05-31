# Agentic SDLC

The framework runs as a loop, not a one-pass build.

## Loop

```text
1. Requirements intake
2. `/goal`
3. Prompt spec
4. Planning checkpoint
5. Interface contract
6. Build
7. Developer tests
8. Quality exploration
9. Adversarial review
10. Implementation hardening
11. Evidence judge
12. Security review
13. Documentation drift check
14. Requirements audit
15. Self-healing repair
16. Regression
17. PR review
18. Release gate
19. Scheduled maintenance
```

## General Skill Overlay

The framework maps the general lifecycle from
`https://github.com/addyosmani/agent-skills` into the local role and evidence
model. The mapping lives in `contracts/agentic_framework_map.yaml`.

- DEFINE uses provider-native `/goal` or planning when available, or AI Brain's
  own clarification step when not, to clarify intent before `/spec` and
  implementation. Either way, the rest of the AI Brain SDLC loop still runs.
- BUILD and VERIFY require incremental implementation, tests, quality
  exploration, and recovery.
- REVIEW and SHIP add code quality, simplification, security, performance,
  docs, release, and rollback thinking.
- MAINTAIN keeps memory, state, and deprecation decisions current.

## Harness Quality Gates

- Role prompts must match the framework contract.
- Regression evidence includes framework map, role contract, memory/state,
  prompt specs, report rendering, reliability, and harness-quality tests.
- The evidence judge checks whether reports are source-backed and auditable.
- Maintenance tracks team reliability over time.
- Framework drift blocks stale roles, docs, memory, or reports.
- The combined report renders source-backed test evidence.
- The one-command launcher keeps checks and the knowledge base discoverable.

## Why This Matters

The framework is meant to make autonomous work operational:

- scope becomes agent-sized tasks
- `/goal` can use native provider planning when available, but it feeds the AI
  Brain SDLC loop instead of replacing it
- `/goal` makes success criteria and non-goals explicit before planning
- planning happens before substantial edits
- prompt specs preserve the user's ask, chunk plan, ownership, and verification
- contracts define handoffs
- tests and reports prove the work
- hardening catches thin first passes
- requirements audit maps prompts back to artifacts
- self-healing routes failures into repair
- release gate refuses incomplete claims
