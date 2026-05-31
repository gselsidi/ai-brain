# How This Was Built

This project started as a working AI-assisted delivery harness and was shaped
into a reusable autonomous SDLC team framework.

The early work focused on the operating loop: durable instructions, specialist
role prompts, prompt specs, tests, evidence reports, hardening passes, release
gates, and maintenance checks. The goal was not to build another demo app. The
goal was to package a repeatable way for an agent team to plan, implement,
verify, review, repair, and ship work with evidence.

## Build Timeline

1. The framework was separated from any target product runtime. Product code,
   product routes, and domain-specific checks were treated as adoption inputs
   that another team supplies.
2. Specialist roles were organized around a full SDLC loop: orchestration,
   planning, product context, interface contracts, building, testing, quality
   exploration, adversarial review, evidence judging, hardening, security,
   docs drift, requirements audit, self-healing, maintenance, review, and
   release.
3. Prompt specs became the durable planning layer. Broad work starts with a
   clarified goal, then moves into a small checklist, ownership map, affected
   artifacts, and verification commands.
4. Provider-neutral behavior was clarified. Codex, Claude, or another runtime
   can use native planning features when available, but those features feed the
   AI Brain loop. They do not replace specs, tests, audits, or release gates.
5. The harness adopted a lightweight improvement queue inspired by external
   maintainability tooling: scan source, score risk, produce ranked next items,
   and require release evidence.
6. Local memory and lifecycle state were moved out of tracked source. The repo
   now ships safe templates while real workspace memory, generated reports, and
   run state stay local.
7. Public-source hygiene became a tested behavior. Tracked files are checked so
   workspace-specific account names, local paths, and internal publishing notes
   do not slip back into the repository.
8. The public `specs/` folder was reduced to only the reusable prompt-spec
   template. The build history moved here so adopters get a clean working
   directory while curious readers can still see the broad construction path.

## What Was Kept

- The reusable team operating model.
- The provider-neutral role prompts and SDLC contracts.
- The prompt-spec workflow.
- A clean `specs/prompt_spec_template.md` for adopters.
- Deterministic checks and report generation.
- Safe templates for local memory and state.
- The improvement queue and release gate.

## What Was Removed Or Kept Local

- Raw local memory and lifecycle state.
- Generated reports and generated documentation output.
- Internal publishing notes.
- Workspace-specific paths, account names, and setup details.
- Dated build specs from the public `specs/` folder.

## Why The History Is Short

The public history was intentionally cleaned after the framework was made
public. That keeps the repository focused on the reusable framework rather than
on private setup notes or intermediate local state.
