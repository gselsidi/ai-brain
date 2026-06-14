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

Best default: add AI Brain to a target codebase as a Git subtree so the
framework is committed as normal files and can still pull upstream updates:

```bash
git subtree add --prefix=ai-brain https://github.com/YOUR_ORG/ai-brain.git main --squash
git subtree pull --prefix=ai-brain https://github.com/YOUR_ORG/ai-brain.git main --squash
```

Use a submodule only when you intentionally want the target repo to store a
pointer to a separate AI Brain checkout. Avoid committing a plain nested `.git`
directory; normal clones and deploys will not get the contents as ordinary
files. For one-off vendoring, `make dropin-bundle` creates
`dist/ai-brain-dropin/` without Git internals or local generated artifacts.
If someone manually copied the live folder anyway, run
`make -C ai-brain manual-copy-clean` before staging it. The command is guarded:
it removes nested AI Brain Git metadata only when `ai-brain/` is inside another
Git repo, and it moves non-conflicting local AI Brain memory, state, reports,
and dated specs to the target repo root before cleanup.

After adding AI Brain to the target codebase, run:

```bash
make init-repo
```

If AI Brain is in an `ai-brain/` subfolder, run:

```bash
make -C ai-brain init-repo TARGET_ROOT=..
```

That creates ignored target-local memory, lifecycle state, repo profile, work
specs, and reports at the target repo root for subfolder installs, and updates
target `.gitignore` so those files stay local. It also creates or updates root
`AGENTS.md` with an AI Brain bridge so future Codex sessions read
`ai-brain/AGENTS.md` automatically for repo work. Use `INSTALL_ROOT_AGENTS=0`
for a private local-only helper that should not add an AI Brain bridge. Then
keep the evidence loop: test report, framework drift, harness quality,
reliability scoring, requirements audit, and release gate.

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
