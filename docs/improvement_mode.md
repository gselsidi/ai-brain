# Improvement Mode

Improvement mode is the standalone form of the implementation hardening gate.
Use it when the goal is making the current framework or adopting project more
concrete, robust, readable, and verifiable.

## Trigger Prompt

```text
Review the project and make improvements.
```

or:

```text
Run improvement mode on this project.
```

## Loop

1. Read `AGENTS.md` and local `memory/PROJECT_MEMORY.md` when it exists.
2. Create a short improvement plan.
3. Run up to 3 hardening passes.
4. In each pass, look for thin logic, brittle assumptions, unclear prompts,
   weak docs, missing regression evidence, or confusing reports.
5. Run the improvement queue with `make improvement-queue`; use its strict score
   and ranked next items as deterministic guidance, not as a replacement for
   judgment.
6. Implement concrete improvements only when they materially help.
7. Stop early when the implementation is up to par.
8. After 3 passes, document remaining ideas as future work or overkill.
9. Run the relevant checks, preferably the full release gate.

## Guardrails

- Prefer small, high-leverage improvements over broad rewrites.
- Do not add a product runtime to this framework repo.
- Add regression coverage for behavior repairs.
- Update docs and local project memory when workflow changes.
- Treat release-blocking improvement queue findings as self-healing work before
  claiming completion.
- Leave the framework in a releasable state.
