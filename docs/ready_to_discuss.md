# Ready To Discuss

## What This Framework Is

It is a reusable autonomous full-stack SDLC team: orchestrator, planner,
builders, test writer, quality explorer, adversarial reviewer, evidence judge,
hardener, security reviewer, docs guard, requirements auditor, self-healer,
maintenance heartbeat, PR reviewer, and release gate.

## What It Is Not

It is not a default product implementation. Adopting teams bring the product.
AI Brain initializes local product context from the repo instead of asking the
team to rewrite framework files by hand.

## How To Adopt It

Start by dropping AI Brain into a target codebase and running:

```bash
make init-repo
```

That creates ignored local memory, lifecycle state, and a repo profile from the
checkout. Then keep the evidence loop: test report, framework drift, harness
quality, reliability scoring, requirements audit, and release gate.

Each project-work prompt should create a durable spec before implementation so
planning, ownership, and verification are auditable.
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
