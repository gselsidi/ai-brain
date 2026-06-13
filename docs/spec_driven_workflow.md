# Spec-Driven Workflow

Every project-work prompt that changes artifacts starts with a durable local
prompt spec under `specs/`.

For broad, ambiguous, risky, or outcome-oriented prompts, run `/goal` before the
spec. If the active provider supports a native `/goal` or planning feature, AI
Brain can use it to clarify the work. That native step feeds the AI Brain SDLC
loop; it does not replace specs, memory, evidence, audits, or release gates. If
native `/goal` is unavailable, disabled, or incompatible, AI Brain performs the
same clarification step itself.

In either mode, `/goal` clarifies the outcome, success criteria, non-goals,
constraints, assumptions, and open questions. `/spec` then turns that clarified
goal into owned chunks and verification evidence.

Tiny direct questions can still be answered directly. Any prompt that changes
code, docs, tests, contracts, memory, state, reports, automation, or team
workflow needs a spec before implementation starts.

## Ownership

- `product_context_analyst` owns `/goal` clarification.
- `sdlc_orchestrator` chooses provider-native `/goal` or AI Brain clarification,
  then enforces the same SDLC loop either way.
- `delivery_planner` creates or updates the spec.
- `sdlc_orchestrator` refuses substantial implementation until the spec is
  actionable.
- `docs_drift_guard` keeps the spec workflow reflected in docs, memory,
  contracts, and role prompts.
- `requirements_auditor` maps final evidence back to the spec checklist.

## Spec Shape

Use `specs/prompt_spec_template.md` unless the adopting team has a stricter
template.

Each prompt spec should include:

- the user's concrete prompt
- clarified `/goal` outcome when applicable
- implementation goal
- explicit requirements checklist
- scope boundaries
- agent ownership
- small implementation chunks
- expected evidence
- completion audit

Recommended local path:

```text
specs/YYYY-MM-DD_short_slug.md
```

This public framework repo tracks only `specs/prompt_spec_template.md`.
Adopter-specific dated specs are ignored by git by default. That keeps the
framework clean when another team drops it into its own codebase, while still
letting agents use durable local planning files during real work.

## Repo Work Specs

When AI Brain is operating on a target repo, actual implementation evidence goes
under:

```text
.ai-brain/specs/work/YYYY-MM-DD_short_slug.md
```

For framework-root development, the same ledger lives under `specs/work/`.
Those repo work specs are the spec-driven development ledger for the target
repo. They record the prompt, goal, requirements, affected artifacts, target
tests and commands, documentation updates, reports, and completion audit.

AI Brain contracts and docs remain framework-level. Repo-specific facts stay in
target-local `.ai-brain/memory/PROJECT_MEMORY.md`,
`.ai-brain/state/sdlc_state.json`,
`.ai-brain/state/ai_brain_repo_profile.local.json`,
`.ai-brain/state/reports/target-command_report.json`,
`.ai-brain/state/reports/target-drift_report.json`, and the current repo work
spec for subfolder installs.

## Orchestration Rule

The spec is the handoff between planning and implementation. Once the spec
exists, the orchestrator implements the listed chunks, updates it or the
requirements audit if scope changes, and uses the final verification commands as
release evidence.

Do not treat the spec as static ceremony. If implementation reveals a better
small chunk, missing artifact, or blocked assumption, update the spec before
continuing.
