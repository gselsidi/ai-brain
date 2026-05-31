# Ready To Discuss

## What This Framework Is

It is a reusable autonomous full-stack SDLC team: orchestrator, planner,
builders, test writer, quality explorer, adversarial reviewer, evidence judge,
hardener, security reviewer, docs guard, requirements auditor, self-healer,
maintenance heartbeat, PR reviewer, and release gate.

## What It Is Not

It is not a default product implementation. Adopting teams bring the product,
surface contracts, tests, deployment commands, and domain checks.

## How To Adopt It

Start by copying the role prompts and `AGENTS.md` into a target codebase. Add the
target team's behavior contracts and Make targets, then keep the evidence loop:
test report, framework drift, harness quality, reliability scoring, requirements
audit, and release gate.

Keep `specs/prompt_spec_template.md` or replace it with the target team's
standard. Each project-work prompt should create a durable spec before
implementation so planning, ownership, and verification are auditable.
Use provider-native `/goal` before `/spec` when the active runtime supports it,
but treat it as clarification for the AI Brain SDLC loop, not a replacement for
the loop. When native `/goal` is unavailable, use AI Brain's own clarification
step so outcome, success criteria, non-goals, and constraints are still
explicit.

## Why It Works

The team is process plus proof:

- prompts define responsibilities
- `/goal` can use native provider planning, then still runs the AI Brain loop
- specs turn prompts into small implementation chunks
- memory preserves context
- tests and reports prove execution
- hardening improves thin first passes
- requirements audit catches missed asks
- self-healing routes failures
- release gate refuses unsupported completion claims
